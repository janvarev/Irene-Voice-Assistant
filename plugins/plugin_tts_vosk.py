# TTS plugin for Vosk engine
# author: Vladislav Janvarev

import os

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "TTS vosk",
        "version": "1.3",
        "require_online": False,

        "description": "TTS через VOSK\n"
                       "ID для указания: vosk\n"
                       "Список голосов доступен здесь: https://giters.com/alphacep/vosk-tts",

        "default_options": {
            "modelId": "vosk-model-tts-ru-0.4-multi", # модель
            "speakerId": 0, # id голоса irina (доступно 0,1,2,3,4)
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

    options = core.plugin_options(modname)

    core.ttsModel = Model(model_name = options['modelId'])
    if options['useGPU']:
        try:
            import torch
            import onnxruntime
            import pkg_resources
            installed = {pkg.key for pkg in pkg_resources.working_set if pkg.key.startswith('onnxruntime-gpu')}
            if not installed:
                raise ImportError
        except ImportError:
            print("Please install torch and onnxruntime-gpu")
        else:
            if torch.cuda.is_available():
                providers = [("CUDAExecutionProvider", {"device_id": torch.cuda.current_device(),
                                                        "user_compute_stream": str(torch.cuda.current_stream().cuda_stream)})]
                so = onnxruntime.SessionOptions()
                # so.log_severity_level = 1  # раскомментируйте, если хотите увидеть логи
                session = onnxruntime.InferenceSession(core.ttsModel.onnx._model_path, providers=providers, sess_options=so)
                core.ttsModel.onnx = session
            else:
                print("CUDA is not available")
            # print(onnxruntime.get_available_providers())  # раскомментируйте, если хотите увидеть список доступных провайдеров
    # print(core.ttsModel.onnx._providers)  # раскомментируйте, если хотите увидеть список используемых провайдеров

    core.ttsSynth = Synth(core.ttsModel)

def towavfile(core:VACore, text_to_speech:str,wavfile:str):
    """
    Проигрывание речи ответов голосового ассистента с сохранением в файл
    :param text_to_speech: текст, который нужно преобразовать в речь
    """
    options = core.plugin_options(modname)
    core.ttsSynth.synth(core.all_num_to_text(text_to_speech),wavfile,speaker_id=options['speakerId'])
