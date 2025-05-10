# TTS plugin for Vosk engine
# author: Vladislav Janvarev

import os

from vacore import VACore
import logging
import re


modname = os.path.basename(__file__)[:-3] # calculating modname
logger = logging.getLogger(__name__)


# функция на старте
def start(core:VACore):
    manifest = {
        "name": "TTS vosk",
        "version": "1.4",
        "require_online": False,

        "description": "TTS через VOSK\n"
                       "ID для указания: vosk\n"
                       "Список голосов доступен здесь: https://giters.com/alphacep/vosk-tts",

        "default_options": {
            "modelId": "vosk-model-tts-ru-0.7-multi", # модель
            "speakerId": 2, # id голоса irina (доступно 0,1,2,3,4)
            "useGPU": False # не использовать GPU
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
    from vosk_tts.model import Model
    from vosk_tts.synth import Synth
    from time import time

    model_init_start_time = time()
    logger.info("Init model starting...")
    options = core.plugin_options(modname)

    if options['useGPU']:
        try:
            import torch
            import onnxruntime
            from importlib.metadata import distributions
            installed = {dist.metadata['Name'].lower() for dist in distributions() if
                         dist.metadata['Name'].lower().startswith('onnxruntime-gpu')}
            if not installed:
                raise ImportError
        except ImportError:
            logger.warning("Please install torch and onnxruntime-gpu")
        else:
            if torch.cuda.is_available():
                logger.info("CUDA is available")
            else:
                logger.info("CUDA is not available")
            logger.debug(
                f'Available providers: {onnxruntime.get_available_providers()}')  # список доступных провайдеров

    core.ttsModel = Model(model_name=options['modelId'])
    logger.debug(f'Used providers: {core.ttsModel.onnx._providers}')  # список используемых провайдеров
    core.ttsSynth = Synth(core.ttsModel)
    model_init_end_time = time()
    logger.info(f"Init done in {model_init_end_time - model_init_start_time:.1f} sec")


def towavfile(core:VACore, text_to_speech:str,wavfile:str):
    """
    Проигрывание речи ответов голосового ассистента с сохранением в файл
    :param text_to_speech: текст, который нужно преобразовать в речь
    """
    options = core.plugin_options(modname)
    core.ttsSynth.synth(core.normalize(text_to_speech),wavfile,speaker_id=options['speakerId'])
