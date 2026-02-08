import argparse
import time
import queue
import sys
import json

import sounddevice as sd
import vosk


def int_or_str(text):
    try:
        return int(text)
    except ValueError:
        return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--device', type=int_or_str, help='input device id or substring')
    parser.add_argument('-m', '--model', type=str, default='model', help='path to vosk model')
    parser.add_argument('-r', '--samplerate', type=int, help='samplerate')
    parser.add_argument('-t', '--time', type=int, default=8, help='seconds to record')
    args = parser.parse_args()

    if not vosk:
        print('vosk not available')
        sys.exit(1)

    if not sd:
        print('sounddevice not available')
        sys.exit(1)

    if not args.samplerate:
        device_info = sd.query_devices(args.device, 'input')
        args.samplerate = int(device_info['default_samplerate'])

    try:
        model = vosk.Model(args.model)
    except Exception as e:
        print('Model load error:', e)
        sys.exit(1)

    q = queue.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            print('status', status, file=sys.stderr)
        q.put(bytes(indata))

    rec = vosk.KaldiRecognizer(model, args.samplerate)

    print('Recording for', args.time, 'seconds...')
    start = time.time()
    try:
        with sd.RawInputStream(samplerate=args.samplerate, blocksize=8000, device=args.device,
                               dtype='int16', channels=1, callback=callback):
            while time.time() - start < args.time:
                try:
                    data = q.get(timeout=1)
                except queue.Empty:
                    continue
                if rec.AcceptWaveform(data):
                    res = rec.Result()
                    try:
                        j = json.loads(res)
                        print('RESULT:', j.get('text',''))
                    except Exception:
                        print('RAW RESULT:', res)
                else:
                    pass
    except Exception as e:
        print('Runtime error:', type(e).__name__, e)
        sys.exit(2)

    final = rec.FinalResult()
    try:
        j = json.loads(final)
        print('FINAL:', j.get('text',''))
    except Exception:
        print('FINAL RAW:', final)


if __name__ == '__main__':
    main()
