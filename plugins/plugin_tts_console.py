# TTS plugin - just console output for debugging
# author: Vladislav Janvarev

import os

import pyttsx3

from vacore import VACore

modname = os.path.basename(__file__)[:-3]  # calculating modname

# функция на старте
def start(core: VACore):
    manifest = {
        "name": "TTS console (for debug)",
        "version": "1.0",
        "require_online": False,
        "tts": {
            "console": (init, say)  # первая функция инициализации, вторая - говорить
        },
    }
    return manifest


def init(core: VACore):
    pass


def say(core: VACore, text_to_speech: str):
    # просто выводим текст в консоль
    print("TTS: {}".format(text_to_speech))
