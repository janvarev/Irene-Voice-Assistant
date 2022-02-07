# TTS plugin for rhvoice engine
# author: Vladislav Janvarev



import os

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "TTS rhvoice",
        "version": "1.1",
        "require_online": False,

        "default_options": {
            "voiceId": "anna", # id голоса
        },

        "tts": {
            "rhvoice": (init,None,towavfile) # первая функция инициализации, вторая - говорить, третья - в wav file
                                            # если вторая - None, то используется 3-я с проигрыванием файла
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def init(core:VACore):
    from rhvoice_wrapper import TTS

    core.ttsrhvoice = TTS(threads=1)
    print("RHVoices available voices:",core.ttsrhvoice.voices)
    for voiceId in core.ttsrhvoice.voices_info.keys():
        print('  ',voiceId,': ',core.ttsrhvoice.voices_info[voiceId])

def towavfile(core:VACore, text_to_speech:str, wavfile:str):
    # simple way
    voiceid = core.plugin_options("plugin_tts_rhvoice")["voiceId"]
    core.ttsrhvoice.to_file(filename=wavfile, text=text_to_speech, voice=voiceid, format_='wav', sets=None)
    return

