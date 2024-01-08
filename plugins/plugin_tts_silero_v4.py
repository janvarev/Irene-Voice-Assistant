# TTS plugin for silero engine v4
# author: Vladislav Janvarev

# require torch 2.0+

# поддерживает несколько языков
# поменяйте modelurl на нужный вам
# список здесь: https://github.com/snakers4/silero-models#text-to-speech
# или здесь: https://models.silero.ai/models/tts/

modelurl = 'https://models.silero.ai/models/tts/ru/v4_ru.pt'

import os

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "TTS silero V4",
        "version": "2.0",
        "require_online": False,

        "default_options": {
            "speaker": "xenia",
            "threads": 1,
            "sample_rate": 24000,
            "put_accent": True,
            "put_yo": True,
            "speaker_by_assname": {
                "николай|николаю": "aidar"
            }
        },

        "tts": {
            "silero_v4": (init,None,towavfile) # первая функция инициализации, вторая - говорить
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
    torch.set_num_threads(options["threads"])
    local_file = 'silero_model_v4.pt'

    if not os.path.isfile(local_file):
        print("Downloading Silero model...")
        torch.hub.download_url_to_file(modelurl,
                                       local_file)


    core.model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
    core.model.to(device)


    #core.model.


def towavfile(core:VACore, text_to_speech:str, wavfile:str):
    text_to_speech = text_to_speech.replace("…","...")
    text_to_speech = core.all_num_to_text(text_to_speech)
    #print(text_to_speech)


    options = core.plugin_options(modname)
    speaker = options["speaker"]

    # дополнительный резолвинг по имени обращения, если нужно
    if core.cur_callname != "":
        for k in options["speaker_by_assname"].keys():
            ar_k = str(k).split("|")
            if core.cur_callname in ar_k:
                speaker = options["speaker_by_assname"][k]

    # рендерим wav
    path = core.model.save_wav(text=text_to_speech,
                               speaker=speaker,
                               put_accent=options["put_accent"],
                               put_yo=options["put_yo"],
                               sample_rate=options["sample_rate"])

    # перемещаем wav на новое место
    if os.path.exists(wavfile):
        os.unlink(wavfile)
    os.rename(path,wavfile)