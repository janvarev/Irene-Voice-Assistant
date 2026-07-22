# GigaSTT-based type of Irene
# Speech is recognized by a gigastt server: https://github.com/ekhodzitsky/gigastt
# Run a server first: gigastt serve

import json
import asyncio
import sys
import websockets
import logging
import sounddevice as sd
import argparse
from urllib.parse import urlparse

from vacore import VACore

mic_blocked = False

def block_mic():
    global mic_blocked
    #print("Blocking microphone...")
    mic_blocked = True

# ------------------- gigastt ------------------

BACKOFF_MAX_SECS = 30  # cap for the reconnect backoff
ROTATE_AT = 0.9        # rotate the session at 90% of the server-side cap

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def normalize_uri(uri):
    """Accept host:port with or without scheme/path, return a full ws://.../v1/ws URL."""
    if "://" not in uri:
        uri = "ws://" + uri
    if urlparse(uri).path in ("", "/"):
        uri = uri.rstrip("/") + "/v1/ws"
    return uri

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    if not mic_blocked:
        def enqueue():
            try:
                audio_queue.put_nowait(bytes(indata))
            except asyncio.QueueFull:
                # queue is full: drop the oldest block, fresh audio wins
                try:
                    audio_queue.get_nowait()
                    audio_queue.put_nowait(bytes(indata))
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    pass
        loop.call_soon_threadsafe(enqueue)

async def send_audio(websocket):
    while True:
        data = await audio_queue.get()
        await websocket.send(data)

async def receive_results(websocket, core):
    """Handles server messages until the connection closes.
    Returns retry_after_ms when the server asked to back off, -1 on a fatal
    server error, None when the connection just closed."""
    global mic_blocked
    async for res in websocket:
        try:
            msg = json.loads(res)
        except ValueError:
            print("Skipping an unparsable server message:", res)
            continue
        msg_type = msg.get("type")
        if msg_type == "partial":
            if args.debug:
                print("Partial:", msg.get("text"))
        elif msg_type == "final":
            voice_input_str = (msg.get("text") or "").strip()
            if voice_input_str != "":
                # command execution (incl. TTS) may take minutes - run it in a
                # thread so the loop keeps answering server keepalive pings
                try:
                    await asyncio.to_thread(core.run_input_str, voice_input_str, block_mic)
                except Exception as e:
                    print("Command failed:", e)
                finally:
                    mic_blocked = False
        elif msg_type == "error":
            print("Server error: {0} (code: {1})".format(msg.get("message"), msg.get("code")))
            retry_after_ms = msg.get("retry_after_ms")
            if retry_after_ms:
                print("Server is busy, retry after {0} ms".format(retry_after_ms))
                return retry_after_ms
            return -1
    return None

async def graceful_stop(websocket):
    """Finalize the session: flush trailing words, read the last final, close."""
    try:
        await websocket.send('{"type":"stop"}')
        # partials may still arrive before the final
        while True:
            res = await asyncio.wait_for(websocket.recv(), timeout=5)
            msg = json.loads(res)
            if msg.get("type") == "final":
                if args.debug:
                    print("Final on stop:", msg.get("text"))
                break
    except Exception:
        pass

async def run_session(core, websocket, ready):
    """Streams audio until the session ends (server close, error, or planned
    rotation at 90% of max_session_secs). Returns the pause in seconds the
    server asked for before reconnecting, 0 for an immediate reconnect."""
    supported_rates = ready.get("supported_rates") or [8000, 16000, 24000, 44100, 48000]
    try:
        samplerate = args.samplerate
        if samplerate is None:
            device_info = sd.query_devices(args.device, 'input')
            # sounddevice provides a float, the server expects an int:
            samplerate = int(device_info['default_samplerate'])
        if samplerate not in supported_rates:
            print("Sample rate {0} is not supported by the server {1}, trying 16000 Hz".format(
                samplerate, supported_rates))
            samplerate = 16000

        # configure must be sent before the first audio frame
        await websocket.send(json.dumps({"type": "configure", "sample_rate": samplerate}))

        # drop audio captured while there was no live session
        while not audio_queue.empty():
            audio_queue.get_nowait()

        with sd.RawInputStream(samplerate=samplerate, blocksize = 4000, device=args.device, dtype='int16',
                               channels=1, callback=callback):
            print('#' * 80)
            print('Press Ctrl+C to stop the recording')
            print('#' * 80)

            sender = asyncio.ensure_future(send_audio(websocket))
            receiver = asyncio.ensure_future(receive_results(websocket, core))
            tasks = [sender, receiver]
            max_session_secs = ready.get("max_session_secs") or 0
            if max_session_secs > 0:
                # planned rotation just before the server-side cap
                tasks.append(asyncio.ensure_future(asyncio.sleep(max_session_secs * ROTATE_AT)))
            retry_after_ms = None
            try:
                done, _pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for t in done:
                    if t.cancelled():
                        continue
                    exc = t.exception()
                    if exc is not None:
                        print("Connection to gigastt lost: {0}".format(exc))
                    elif t is receiver:
                        retry_after_ms = t.result()
                    # a finished rotation timer just means: rotate now
            finally:
                # stop both tasks before graceful_stop, otherwise its recv
                # races the receiver and the trailing final gets swallowed
                for t in tasks:
                    t.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                await graceful_stop(websocket)
            if retry_after_ms is not None and retry_after_ms < 0:
                sys.exit(1)  # fatal server error, no point reconnecting
            return (retry_after_ms or 0) / 1000
    except sd.PortAudioError as e:
        print("Cannot open the microphone: {0}".format(e))
        print("Pass a valid input device via -d and one of the server supported rates via -r: {0}".format(
            supported_rates))
        sys.exit(1)

async def run_connection(core):
    """One connection lifecycle: connect, wait for ready, stream.
    Raises OSError / InvalidHandshake / TimeoutError when the server cannot
    be reached yet - the caller retries with backoff."""
    try:
        websocket = await websockets.connect(args.uri)
    except websockets.exceptions.InvalidURI:
        print("Bad server URI: {0} (example: ws://127.0.0.1:9876/v1/ws)".format(args.uri))
        sys.exit(1)

    async with websocket:
        res = await asyncio.wait_for(websocket.recv(), timeout=15)
        try:
            ready = json.loads(res)
        except ValueError:
            ready = {}
        if ready.get("type") == "error":
            # a busy server (pool saturation) refuses before sending ready
            print("Server error: {0} (code: {1})".format(ready.get("message"), ready.get("code")))
            retry_after_ms = ready.get("retry_after_ms")
            if retry_after_ms:
                print("Server is busy, retry after {0} ms".format(retry_after_ms))
                return retry_after_ms / 1000
            sys.exit(1)
        if ready.get("type") != "ready":
            print("Unexpected first message from server:", res)
            sys.exit(1)

        print("Connected to gigastt: model={0}, protocol={1}".format(
            ready.get("model"), ready.get("version")))
        if ready.get("max_session_secs"):
            print("Session limit: {0} s".format(ready.get("max_session_secs")))
        if ready.get("idle_timeout_secs"):
            print("Idle timeout: {0} s".format(ready.get("idle_timeout_secs")))

        return await run_session(core, websocket, ready)

async def run_test():

    # initing core
    core = VACore()
    core.init_with_plugins()

    backoff = 1
    while True:
        try:
            delay = await run_connection(core)
            backoff = 1  # a full session ran - reset the backoff
            if delay > 0:
                await asyncio.sleep(delay)  # server asked for a pause
            else:
                print("Session ended, reconnecting...")
        except (OSError, asyncio.TimeoutError, websockets.exceptions.InvalidHandshake,
                websockets.exceptions.ConnectionClosed) as e:
            print("Cannot connect to gigastt server at {0}: {1}".format(args.uri, e))
            print("Retrying in {0} s (run a server first: gigastt serve)".format(backoff))
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, BACKOFF_MAX_SECS)

async def main():

    global args
    global loop
    global audio_queue

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-l', '--list-devices', action='store_true',
                        help='show list of audio devices and exit')
    args, remaining = parser.parse_known_args()
    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)
    parser = argparse.ArgumentParser(description="GigaSTT ASR client",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     parents=[parser])
    parser.add_argument('-u', '--uri', type=str, metavar='URL',
                        help='Server URL', default='ws://127.0.0.1:9876/v1/ws')
    parser.add_argument('-d', '--device', type=int_or_str,
                        help='input device (numeric ID or substring)')
    parser.add_argument('-r', '--samplerate', type=int, help='sampling rate')
    parser.add_argument('--debug', action='store_true',
                        help='print partial recognition results')
    args = parser.parse_args(remaining)
    args.uri = normalize_uri(args.uri)
    loop = asyncio.get_running_loop()
    audio_queue = asyncio.Queue(maxsize=100)

    logging.basicConfig(level=logging.INFO)

    await run_test()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nDone')
