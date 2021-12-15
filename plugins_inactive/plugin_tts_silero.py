# TTS plugin for silero engine
# author: Vladislav Janvarev

# require torch 1.8+

import os

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "TTS silero",
        "version": "1.0",
        "require_online": False,

        "default_options": {
            "sileroId": "v2_kseniya", # id файла голоса с https://models.silero.ai/models/tts/ru/
        },

        "tts": {
            "silero": (init,say) # первая функция инициализации, вторая - говорить
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def init(core:VACore):
    options = core.plugin_options(modname)

    import os
    import torch

    device = torch.device('cpu')
    torch.set_num_threads(8)
    local_file = 'silero_{}.pt'.format(options["sileroId"])

    if not os.path.isfile(local_file):
        torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/{}.pt'.format(options["sileroId"]),
                                       local_file)


    core.model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
    core.model.to(device)


    #core.model.


def say(core:VACore, text_to_speech:str):
    # simple way
    paths = core.model.save_wav(texts=[text_to_speech],
                                sample_rate=16000)
    #print(text_to_speech)
    #print(paths)
    for file in paths:
        core.play_wav(file)
    return

    # other way - splitting by small phrases to speed up generation

    sentences = text_to_speech.split(".")
    for sentence in sentences:
        if sentence != "":
            paths = core.model.save_wav(texts=[sentence+"."],
                           sample_rate=16000)
            #print(text_to_speech)
            #print(paths)
            for file in paths:
                core.play_wav(file)