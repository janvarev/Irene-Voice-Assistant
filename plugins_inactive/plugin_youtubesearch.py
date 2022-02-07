import os
import time

import pyautogui

# from voiceassmain import play_voice_assistant_speech
from vacore import VACore

# based on EnjiRouz realization https://github.com/EnjiRouz/Voice-Assistant-App/blob/master/app.py

# функция на старте
def start(core: VACore):
    manifest = {
        "name": "Ютуб (поиск)",
        "version": "1.0",
        "require_online": True,
        "commands": {
            "ютуб|юту": run_youtube,
        },
    }
    return manifest


def run_youtube(core: VACore, phrase: str):
    if core != None:
        core.play_voice_assistant_speech("Ищу на ютуб {}".format(phrase))

    import webbrowser

    url = "https://www.youtube.com/results?search_query=" + phrase
    webbrowser.get().open(url)
