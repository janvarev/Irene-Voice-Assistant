# VOSK-remote based type of Irene
# Speech will be recognized on Server
# Run Docker server: docker run -d -p 2700:2700 alphacep/kaldi-ru:latest
# Details: https://alphacephei.com/vosk/server

import json
import asyncio
import websockets
import logging
import sounddevice as sd
import argparse

from vacore import VACore

mic_blocked = False

def block_mic():
    global mic_blocked
    #print("Blocking microphone...")
    mic_blocked = True

# ------------------- vosk ------------------
def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    loop.call_soon_threadsafe(audio_queue.put_nowait, bytes(indata))

async def run_test():

    # initing core
    core = VACore()
    core.init_with_plugins()

    with sd.RawInputStream(samplerate=args.samplerate, blocksize = 4000, device=args.device, dtype='int16',
                           channels=1, callback=callback) as device:

        async with websockets.connect(args.uri) as websocket:
            await websocket.send('{ "config" : { "sample_rate" : %d } }' % (device.samplerate))

            while True:
                data = await audio_queue.get()
                await websocket.send(data)
                #print (await websocket.recv())
                res = await websocket.recv()
                resj = json.loads(res)
                if "text" in resj:
                    voice_input_str = resj["text"]
                    #print(restext)

                    if voice_input_str != "":
                        core.run_input_str(voice_input_str,block_mic)
                        mic_blocked = False

            await websocket.send('{"eof" : 1}')
            print (await websocket.recv())

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
    parser = argparse.ArgumentParser(description="ASR Server",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     parents=[parser])
    parser.add_argument('-u', '--uri', type=str, metavar='URL',
                        help='Server URL', default='ws://localhost:2700')
    parser.add_argument('-d', '--device', type=int_or_str,
                        help='input device (numeric ID or substring)')
    parser.add_argument('-r', '--samplerate', type=int, help='sampling rate', default=16000)
    args = parser.parse_args(remaining)
    loop = asyncio.get_running_loop()
    audio_queue = asyncio.Queue()

    logging.basicConfig(level=logging.INFO)

    await run_test()

if __name__ == '__main__':
    asyncio.run(main())


