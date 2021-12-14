import pyautogui
import time
import os

#from voiceassmain import play_voice_assistant_speech
from voiceasscore import VoiceAssCore
# based on EnjiRouz realization https://github.com/EnjiRouz/Voice-Assistant-App/blob/master/app.py

# функция на старте
def start(core:VoiceAssCore):
    manifest = {
        "name": "Ютуб (поиск)",
        "version": "1.0",
        "require_online": True,

        "commands": {
            "ютуб|юту": run_youtube,
        }
    }
    return manifest

def run_youtube(core:VoiceAssCore,phrase:str):
    if core != None:
        core.play_voice_assistant_speech("Ищу на ютуб {}".format(phrase))

    import webbrowser
    url = "https://www.youtube.com/results?search_query=" + phrase
    webbrowser.get().open(url)


