# Команды управления мультимедиа
# author: Vladislav Janvarev

try:
    import pyautogui
except:
    raise ValueError("Не могу загрузить pyautogui в plugin_mediacmds.\nЭто повлияет только на то, что не будут работать команды управления звуком через эмуляцию клавиш.\nЕсли это не критично, пропустите эту ошибку")
import time
import os

#from voiceassmain import play_voice_assistant_speech
from vacore import VACore

# опции
useYandexMusicShortcuts = False
useMPCHCRemote = False
mpchc = None

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Команды управления мультимедия",
        "version": "1.2",
        "require_online": False,

        "description": """
Команды управления медиа (оффлайн). 
Примеры: пауза|паузу, дальше|вперед, назад, стоп, без звука|выключи звук|со звуком, тише, громче, чуть тише, чуть громче, сильно тише, сильно громче, выключи плеер|закрой плеер, пробел
Если установлено mpcIsUseHttpRemote, то сначала делается попытка вызвать команду MPC HC плейера, если не удается - используется эмуляция мультимедийных клавиш
        """,

        "default_options": {
            "useYandexMusicShortcuts": False,
                # использовать специальные клавиши l и k для след/пред трека в Яндекс.Музыке онлайн
        },

        "commands": {
            "пауза|паузу": play_pause,
            "дальше|вперед|вперёд": play_next,
            "назад": play_prev,
            "стоп": play_stop,
            "без звука|выключи звук|со звуком|без мука": toggle_mute,
            "тише": (volume_downX, 3),
            "громче": (volume_upX, 3),
            "чуть тише": (volume_downX, 1),
            "чуть громче": (volume_upX, 1),
            "сильно тише": (volume_downX, 9),
            "сильно громче": (volume_upX, 9),
            "выключи плеер|закрой плеер": close,
            "пробел": space,
        }
    }

    global useMPCHCRemote,mpchc
    useMPCHCRemote = core.mpcIsUseHttpRemote
    mpchc = core.mpchc

    return manifest

def start_with_options(core:VACore, manifest:dict):
    #print(manifest["options"])
    global useYandexMusicShortcuts
    options = manifest["options"]

    useYandexMusicShortcuts = options["useYandexMusicShortcuts"]

def play_pause(core:VACore, phrase: str):
    print("Команда пауза")
    #pyautogui.keyDown("space")
    if useMPCHCRemote:
        try:
            mpchc.play_pause()
            return # если команда отработала, то дальше ничего не нужно
        except Exception as e:
            pass

    pyautogui.press("playpause") # универсально для всех

def space(core:VACore, phrase: str):
    print("Команда пробел")

    pyautogui.press("space") # универсально для всех

def play_stop(core:VACore, phrase: str):
    print("Команда стоп")

    if useMPCHCRemote:
        try:
            mpchc.stop()
            return # если команда отработала, то дальше ничего не нужно
        except Exception as e:
            pass

    pyautogui.press("stop")



def play_next(core:VACore, phrase: str):
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

def play_prev(core:VACore, phrase: str):
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

def toggle_mute(core:VACore, phrase: str):
    if useMPCHCRemote:
        try:
            mpchc.volume_mute()
            return # если команда отработала, то дальше ничего не нужно
        except Exception as e:
            pass

    pyautogui.press("volumemute")

def volume_upX(core:VACore, phrase: str, param:int):
    for i in range(param):
        volume_up1(core,phrase)

def volume_downX(core:VACore, phrase: str, param:int):
    for i in range(param):
        volume_down1(core,phrase)



def volume_up1(core:VACore, phrase: str):
    if useMPCHCRemote:
        try:
            mpchc.volume_up()
            return # если команда отработала, то дальше ничего не нужно
        except Exception as e:
            pass

    pyautogui.press("volumeup")

def volume_down1(core:VACore, phrase: str):
    if useMPCHCRemote:
        try:
            mpchc.volume_down()
            return # если команда отработала, то дальше ничего не нужно
        except Exception as e:
            pass

    pyautogui.press("volumedown")

def close(core:VACore, phrase: str):
    if useMPCHCRemote:
        try:
            mpchc.exit()
            return # если команда отработала, то дальше ничего не нужно
        except Exception as e:
            pass

if __name__ == "__main__":
    play_pause(None,"")
