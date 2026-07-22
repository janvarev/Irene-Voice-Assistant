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
        loop.call_soon_threadsafe(audio_queue.put_nowait, bytes(indata))

async def send_audio(websocket):
    while True:
        data = await audio_queue.get()
        await websocket.send(data)

async def receive_results(websocket, core):
    global mic_blocked
    async for res in websocket:
        msg = json.loads(res)
        msg_type = msg.get("type")
        if msg_type == "partial":
            if args.debug:
                print("Partial:", msg.get("text"))
        elif msg_type == "final":
            voice_input_str = msg.get("text", "").strip()
            if voice_input_str != "":
                core.run_input_str(voice_input_str, block_mic)
                mic_blocked = False
        elif msg_type == "error":
            print("Server error: {0} (code: {1})".format(msg.get("message"), msg.get("code")))
            if msg.get("retry_after_ms"):
                print("Server is busy, retry after {0} ms".format(msg.get("retry_after_ms")))
            sys.exit(1)

async def graceful_stop(websocket):
    """Finalize the session: flush trailing words, read the last final, close."""
    try:
        await websocket.send('{"type":"stop"}')
        res = await asyncio.wait_for(websocket.recv(), timeout=5)
        msg = json.loads(res)
        if args.debug and msg.get("type") == "final":
            print("Final on stop:", msg.get("text"))
    except Exception:
        pass

async def run_test():

    # initing core
    core = VACore()
    core.init_with_plugins()

    try:
        websocket = await websockets.connect(args.uri)
    except websockets.exceptions.InvalidURI:
        print("Bad server URI: {0} (example: ws://127.0.0.1:9876/v1/ws)".format(args.uri))
        sys.exit(1)
    except websockets.exceptions.InvalidHandshake as e:
        print("gigastt server at {0} refused the connection: {1}".format(args.uri, e))
        print("The model may still be loading - try again in a few seconds.")
        sys.exit(1)
    except OSError:
        print("Cannot connect to gigastt server at {0}".format(args.uri))
        print("Run a server first: gigastt serve")
        sys.exit(1)

    async with websocket:
        res = await websocket.recv()
        ready = json.loads(res)
        if ready.get("type") != "ready":
            print("Unexpected first message from server:", res)
            sys.exit(1)

        supported_rates = ready.get("supported_rates") or [8000, 16000, 24000, 44100, 48000]
        print("Connected to gigastt: model={0}, protocol={1}".format(
            ready.get("model"), ready.get("version")))
        if ready.get("max_session_secs"):
            print("Session limit: {0} s".format(ready.get("max_session_secs")))

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

        try:
            with sd.RawInputStream(samplerate=samplerate, blocksize = 4000, device=args.device, dtype='int16',
                                   channels=1, callback=callback):
                print('#' * 80)
                print('Press Ctrl+C to stop the recording')
                print('#' * 80)
                try:
                    await asyncio.gather(send_audio(websocket), receive_results(websocket, core))
                finally:
                    await graceful_stop(websocket)
        except sd.PortAudioError as e:
            print("Cannot open the microphone at {0} Hz: {1}".format(samplerate, e))
            print("Pass one of the server supported rates via -r: {0}".format(supported_rates))
            sys.exit(1)

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
    audio_queue = asyncio.Queue()

    logging.basicConfig(level=logging.INFO)

    await run_test()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nDone')
