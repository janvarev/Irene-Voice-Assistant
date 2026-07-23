# GigaSTT-based type of Irene
# Speech is recognized by a gigastt server: https://github.com/ekhodzitsky/gigastt
# Run a server first: gigastt serve

import json
import asyncio
import sys
import time
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

BACKOFF_MAX_SECS = 30      # cap for the reconnect backoff
ROTATE_AT = 0.9            # rotate the session at 90% of the server-side cap
READY_WAIT_SECS = 45       # the server pool checkout alone may take 30 s
HEALTHY_SESSION_SECS = 30  # a session this long resets the reconnect backoff
COMMAND_WAIT_SECS = 120    # session teardown waits this long for a command thread
POOL_CLOSED_RETRY_MS = 5000  # pool_closed carries no retry hint - wait this much

command_thread = None  # asyncio.Task of the command currently running in a thread

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
        # PortAudio reuses indata once the callback returns - copy it here,
        # on the caller thread, not later on the event loop
        data = bytes(indata)
        def enqueue():
            try:
                audio_queue.put_nowait(data)
            except asyncio.QueueFull:
                # queue is full: drop the oldest block, fresh audio wins
                try:
                    audio_queue.get_nowait()
                    audio_queue.put_nowait(data)
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    pass
        loop.call_soon_threadsafe(enqueue)

async def send_audio(websocket):
    while True:
        data = await audio_queue.get()
        await websocket.send(data)

async def run_command(core, text):
    """Runs a recognized command in a worker thread: command handling (incl.
    TTS) may take minutes and the loop must keep answering server pings. The
    thread cannot be cancelled, so it is tracked in command_thread and session
    teardown waits for it instead of orphaning it."""
    global mic_blocked, command_thread
    try:
        command_thread = asyncio.ensure_future(
            asyncio.to_thread(core.run_input_str, text, block_mic))
        await command_thread
    except Exception as e:
        print("Command failed:", e)
    finally:
        command_thread = None
        mic_blocked = False

async def receive_results(websocket, core):
    """Handles server messages until the connection closes.
    Returns the pause in ms the server asked for before reconnecting
    (0 = reconnect at once), -1 on a fatal server error, None when the
    connection just closed."""
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
                await run_command(core, voice_input_str)
        elif msg_type == "error":
            code = msg.get("code")
            print("Server error: {0} (code: {1})".format(msg.get("message"), code))
            retry_after_ms = msg.get("retry_after_ms")
            # a 0 ms hint is still a hint - test for None, not falsiness
            if retry_after_ms is not None:
                print("Server is busy, retry after {0} ms".format(retry_after_ms))
                return retry_after_ms
            if code in ("max_session_duration_exceeded", "idle_timeout"):
                # the session is over but the server is healthy - reconnect at once
                return 0
            if code == "pool_closed":
                # the server is draining and sent no hint - give it a moment
                return POOL_CLOSED_RETRY_MS
            if code in ("inference_error", "inference_panic"):
                # the server keeps the session open after these - carry on
                continue
            return -1  # any other server error is fatal
    return None

async def graceful_stop(websocket, core):
    """Finalize the session: flush trailing words, run the last final, close."""
    try:
        await websocket.send('{"type":"stop"}')
        # partials may still arrive before the final
        while True:
            res = await asyncio.wait_for(websocket.recv(), timeout=5)
            msg = json.loads(res)
            if msg.get("type") == "final":
                text = (msg.get("text") or "").strip()
                if text != "":
                    # trailing words are a command too - run it like any final
                    await run_command(core, text)
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
        await websocket.send(json.dumps({"type": "configure", "sample_rate": samplerate, "punctuation": False, "itn": False}))

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
                # 1. stop feeding audio at once
                sender.cancel()
                await asyncio.gather(sender, return_exceptions=True)
                # 2. a command runs in a thread and cannot be cancelled - wait
                # for it (bounded), so its finally unblocks the mic and two
                # commands never run at once; the receiver may still pick one
                # more command from an already-buffered final, so re-check
                while command_thread is not None:
                    try:
                        await asyncio.wait_for(asyncio.shield(command_thread),
                                               timeout=COMMAND_WAIT_SECS)
                    except asyncio.TimeoutError:
                        print("Command thread still runs after {0} s, leaving it behind".format(
                            COMMAND_WAIT_SECS))
                        break
                    except Exception:
                        pass  # the command already printed its own failure
                # 3. only now cancel the receiver: it is never killed mid-command
                for t in tasks:
                    t.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                await graceful_stop(websocket, core)
            if retry_after_ms is not None and retry_after_ms < 0:
                sys.exit(1)  # fatal server error, no point reconnecting
            return (retry_after_ms or 0) / 1000
    except (sd.PortAudioError, ValueError) as e:
        # a dead device raises PortAudioError, an unmatched -d substring ValueError
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
        res = await asyncio.wait_for(websocket.recv(), timeout=READY_WAIT_SECS)
        try:
            ready = json.loads(res)
        except ValueError:
            ready = {}
        if ready.get("type") == "error":
            # a busy server (pool saturation) refuses before sending ready
            print("Server error: {0} (code: {1})".format(ready.get("message"), ready.get("code")))
            retry_after_ms = ready.get("retry_after_ms")
            if retry_after_ms is not None:
                print("Server is busy, retry after {0} ms".format(retry_after_ms))
                return retry_after_ms / 1000
            if ready.get("code") == "pool_closed":
                # a draining server sends no hint - retry in a few seconds
                return POOL_CLOSED_RETRY_MS / 1000
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
            started = time.monotonic()
            delay = await run_connection(core)
            if time.monotonic() - started >= HEALTHY_SESSION_SECS:
                backoff = 1  # a long healthy session resets the backoff
            if delay > 0:
                await asyncio.sleep(delay)  # server asked for a pause
            else:
                # never reconnect in a hot loop: a fast-dying session doubles
                # the pause until a session proves healthy again
                print("Session ended, reconnecting in {0} s...".format(backoff))
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, BACKOFF_MAX_SECS)
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
