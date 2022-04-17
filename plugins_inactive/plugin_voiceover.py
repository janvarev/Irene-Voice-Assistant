# VoiceOver
# author: Vladislav Janvarev

import os

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Озвучивание текста",
        "version": "1.3",
        "require_online": False,

        "default_options": {
            "wavBeforeGeneration": True, # звук перед генерацией из буфера обмена, которая может быть долгой
            "wavPath": 'media/timer.wav', # путь к звуковому файлу
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
    import win32clipboard

    win32clipboard.OpenClipboard()
    data = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()

    text_to_speech = str(data)

    options = core.plugin_options(modname)

    if options["wavBeforeGeneration"]:
        core.play_wav(options["wavPath"])

    try:
        core.say2(text_to_speech)
    except Exception:
        import traceback
        traceback.print_exc()
        core.say("Ошибка при озвучке буфера")

    # sentences = text_to_speech.split(".")
    # for sentence in sentences:
    #     if sentence != "":
    #         core.say2(sentence+".")
