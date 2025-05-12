# VoiceOver
# author: Vladislav Janvarev

import os
import logging

from vacore import VACore


modname = os.path.basename(__file__)[:-3] # calculating modname
logger = logging.getLogger(__name__)


# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Озвучивание текста",
        "version": "1.3",
        "require_online": False,

        "default_options": {
            "wavBeforeGeneration": True, # звук перед генерацией из буфера обмена, которая может быть долгой
            "wavPath": 'media/timer.wav', # путь к звуковому файлу
            "useTtsEngineId2": True,  # использовать движок 2
        },

        "commands": {
            "озвучь|скажи": say,
            "буфер": say_clipboard, # озвучка буфера обмена
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def say(core:VACore, phrase:str):
    if phrase == "":
        core.say2("Нечего сказать")
        return
    core.say2(phrase)

def say_clipboard(core:VACore, phrase:str):
    # На Linux нужно установить в системе xclip, xsel, or wl-clipboard
    # Например в Debian
    #     sudo apt-get install xclip
    # На Windows и Mac в систему устанавливать ничего не требуется
    # На всех системах: pip install pyperclip

    try:
        import pyperclip
    except ImportError:
        logger.error("Установите pyperclip: `pip install pyperclip`")
        from sys import platform
        if platform == 'win32':
            try:
                import win32clipboard
            except ImportError:
                logger.error("... или pywin32: `pip install pywin32`")
                return
            else:
                win32clipboard.OpenClipboard()
                data = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()

                text_to_speech = str(data)
    else:
        try:
            text_to_speech = pyperclip.paste()  # получение текста из буфера обмена
        except Exception as e:
            logger.exception("Ошибка при получении текста из буфера обмена: %s", e)
            return

    options = core.plugin_options(modname)

    if options["wavBeforeGeneration"]:
        core.play_wav(options["wavPath"])

    try:
        if options["useTtsEngineId2"]:
            core.say2(text_to_speech)
        else:
            core.say(text_to_speech)
    except Exception as e:
        logger.exception("Ошибка при озвучке буфера: %s", e)

    # sentences = text_to_speech.split(".")
    # for sentence in sentences:
    #     if sentence != "":
    #         core.say2(sentence+".")

