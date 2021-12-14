# Yandex Music

import pyautogui
import time
import os

from voiceasscore import VoiceAssCore

# функция на старте
def start(core:VoiceAssCore):
    manifest = {
        "name": "Яндекс Музыка",
        "version": "1.0",
        "require_online": True,

        "commands": {
            "запусти радио|запусти музыку": run_yamus,
        }
    }
    return manifest

def run_yamus(core:VoiceAssCore,phrase:str):
    if core != None:
        core.play_voice_assistant_speech("Запускаю музыку")

    # open web page
    import webbrowser
    webbrowser.open("https://music.yandex.ru/home", 1)
    time.sleep(3)

    # focus on browser
    pyautogui.click(10,200)
    time.sleep(0.5)

    # play
    pyautogui.press("space")

if __name__ == "__main__":
    run_yamus(None,"")
