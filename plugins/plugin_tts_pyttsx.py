# TTS plugin for pyttsx3 engine
# author: Vladislav Janvarev

import os

from voiceasscore import VoiceAssCore
import pyttsx3

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VoiceAssCore):
    manifest = {
        "name": "TTS pyttsx",
        "version": "1.0",
        "require_online": False,

        "default_options": {
            "sysId": 0, # id голоса в системе, может варьироваться
        },

        "tts": {
            "pyttsx": (init,say) # первая функция инициализации, вторая - говорить
        }
    }
    return manifest

def start_with_options(core:VoiceAssCore,manifest:dict):
    pass

def init(core:VoiceAssCore):
    options = core.plugin_options(modname)

    core.ttsEngine = pyttsx3.init()

    """
    Установка голоса по умолчанию (индекс может меняться в зависимости от настроек операционной системы)
    """


    voices = core.ttsEngine.getProperty("voices")
    #print(voices[0].id)

    # if assistant.speech_language == "en":
    #     assistant.recognition_language = "en-US"
    #     if assistant.sex == "female":
    #         # Microsoft Zira Desktop - English (United States)
    #         ttsEngine.setProperty("voice", voices[1].id)
    #     else:
    #         # Microsoft David Desktop - English (United States)
    #         ttsEngine.setProperty("voice", voices[2].id)
    # else:
    #     assistant.recognition_language = "ru-RU"

    # Microsoft Irina Desktop - Russian
    core.ttsEngine.setProperty("voice", voices[options["sysId"]].id)
    core.ttsEngine.setProperty("volume", 1.0)

def say(core:VoiceAssCore,text_to_speech:str):
    """
    Проигрывание речи ответов голосового ассистента (без сохранения аудио)
    :param text_to_speech: текст, который нужно преобразовать в речь
    """
    core.ttsEngine.say(str(text_to_speech))
    core.ttsEngine.runAndWait()