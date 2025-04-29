# TTS plugin - just console output for debugging
# author: Vladislav Janvarev

import os

from vacore import VACore
# import pyttsx3

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "TTS console (for debug)",
        "version": "1.0",
        "require_online": False,

        "tts": {
            "console": (init,say) # первая функция инициализации, вторая - говорить
        }
    }
    return manifest

def init(core:VACore):
    pass

def say(core:VACore, text_to_speech:str):
    # просто выводим текст в консоль
    try:
        from termcolor import colored, cprint
        cprint("TTS: {}".format(text_to_speech),"blue")
    except Exception as e:
        print("TTS: {}".format(text_to_speech))