# TTS plugin for Elevenlabs.io
# author: Vladislav Janvarev


import os

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "TTS Elevenlabs",
        "version": "1.0",
        "require_online": True,

        "default_options": {
            "speaker": "Bella",
            "model": "eleven_multilingual_v2",
            "api_key": "", # not required
        },

        "tts": {
            "elevenlabs": (init,None,towavfile) # первая функция инициализации, вторая - говорить
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def init(core:VACore):
    options = core.plugin_options(modname)
    import elevenlabs


def towavfile(core:VACore, text_to_speech:str, wavfile:str):


    options = core.plugin_options(modname)
    speaker = options["speaker"]
    model = options["model"]
    api_key = options["api_key"]

    from elevenlabs.client import ElevenLabs
    from elevenlabs import save


    el_client:ElevenLabs = None
    if api_key == "":
        el_client = ElevenLabs()
    else:
        el_client = ElevenLabs(
            api_key=api_key
        )

    audio = el_client.generate(
        text=text_to_speech,
        voice=speaker,
        model=model,
    )
    # рендерим wav (здесь это будет MP3)
    save(audio,wavfile)
