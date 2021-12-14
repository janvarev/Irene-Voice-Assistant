# Команды управления мультимедия
# author: Vladislav Janvarev

import pyautogui
import time
import os

#from voiceassmain import play_voice_assistant_speech
from voiceasscore import VoiceAssCore

# опции
useYandexMusicShortcuts = False
useMPCHCRemote = False
mpchc = None

# функция на старте
def start(core:VoiceAssCore):
    manifest = {
        "name": "Команды управления мультимедия",
        "version": "1.1",
        "require_online": False,

        "default_options": {
            "useYandexMusicShortcuts": False,
                # использовать специальные клавиши l и k для след/пред трека в Яндекс.Музыке онлайн
        },

        "commands": {
            "пауза|паузу": play_pause,
            "дальше|вперед": play_next,
            "назад": play_prev,
            "без звука|выключи звук|со звуком|без мука": toggle_mute,
            "тише": (volume_downX, 3),
            "громче": (volume_upX, 3),
            "чуть тише": (volume_downX, 1),
            "чуть громче": (volume_upX, 1),
            "сильно тише": (volume_downX, 9),
            "сильно громче": (volume_upX, 9),
            "выключи плеер|закрой плеер": close,
        }
    }

    global useMPCHCRemote,mpchc
    useMPCHCRemote = core.mpcIsUseHttpRemote
    mpchc = core.mpchc

    return manifest

def start_with_options(core:VoiceAssCore,manifest:dict):
    #print(manifest["options"])
    global useYandexMusicShortcuts
    options = manifest["options"]

    useYandexMusicShortcuts = options["useYandexMusicShortcuts"]

def play_pause(core:VoiceAssCore, phrase: str):
    print("Команда пауза")
    #pyautogui.keyDown("space")
    if useMPCHCRemote:
        try:
            mpchc.play_pause()
            return # если команда отработала, то дальше ничего не нужно
        except Exception as e:
            pass

    pyautogui.press("space") # универсально для всех


def play_next(core:VoiceAssCore, phrase: str):
    print("Команда дальше")

    if useMPCHCRemote:
        try:
            mpchc.next()
            return # если команда отработала, то дальше ничего не нужно
        except Exception as e:
            pass

    pyautogui.press("nexttrack")

    if useYandexMusicShortcuts:
        pyautogui.press("l")

def play_prev(core:VoiceAssCore, phrase: str):
    print("Команда назад")

    if useMPCHCRemote:
        try:
            mpchc.previous()
            return # если команда отработала, то дальше ничего не нужно
        except Exception as e:
            pass

    pyautogui.press("prevtrack")
    if useYandexMusicShortcuts:
        pyautogui.press("k")

def toggle_mute(core:VoiceAssCore, phrase: str):
    if useMPCHCRemote:
        try:
            mpchc.volume_mute()
            return # если команда отработала, то дальше ничего не нужно
        except Exception as e:
            pass

    pyautogui.press("volumemute")

def volume_upX(core:VoiceAssCore, phrase: str, param:int):
    for i in range(param):
        volume_up1(core,phrase)

def volume_downX(core:VoiceAssCore, phrase: str, param:int):
    for i in range(param):
        volume_down1(core,phrase)



def volume_up1(core:VoiceAssCore, phrase: str):
    if useMPCHCRemote:
        try:
            mpchc.volume_up()
            return # если команда отработала, то дальше ничего не нужно
        except Exception as e:
            pass

    pyautogui.press("volumeup")

def volume_down1(core:VoiceAssCore, phrase: str):
    if useMPCHCRemote:
        try:
            mpchc.volume_down()
            return # если команда отработала, то дальше ничего не нужно
        except Exception as e:
            pass

    pyautogui.press("volumedown")

def close(core:VoiceAssCore, phrase: str):
    if useMPCHCRemote:
        try:
            mpchc.exit()
            return # если команда отработала, то дальше ничего не нужно
        except Exception as e:
            pass

if __name__ == "__main__":
    play_pause(None,"")
