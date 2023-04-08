# TTS plugin for Vosk engine
# author: Vladislav Janvarev

import os

from vacore import VACore
from vosk_tts.model import Model
from vosk_tts.synth import Synth

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "TTS vosk",
        "version": "1.1",
        "require_online": False,

        "default_options": {
            "voiceId": "vosk-model-tts-ru-0.1-natasha", # id голоса
        },

        "tts": {
            "vosk": (init,None,towavfile) # первая функция инициализации, вторая - говорить, третья - в wav file
                                         # если вторая - None, то используется 3-я с проигрыванием файла
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def init(core:VACore):
    options = core.plugin_options(modname)

    core.ttsModel = Model(model_name = options['voiceId'])
    core.ttsSynth = Synth(core.ttsModel)

def towavfile(core:VACore, text_to_speech:str,wavfile:str):
    """
    Проигрывание речи ответов голосового ассистента с сохранением в файл
    :param text_to_speech: текст, который нужно преобразовать в речь
    """
    core.ttsSynth.synth(text_to_speech,wavfile)
