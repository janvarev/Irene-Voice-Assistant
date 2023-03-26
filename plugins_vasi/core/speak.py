# realization for https://github.com/Oknolaz/vasisualy/blob/master/vasisualy/core/speak.py

import vacore

core:vacore.VACore = None

def speak(message, widget):
    core.say(message)
    return