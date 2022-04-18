# Playwav plugin for audioplayer engine
# author: Vladislav Janvarev

import os

from vacore import VACore
from audioplayer import AudioPlayer

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "PlayWav through audioplayer",
        "version": "1.0",
        "require_online": False,

        "playwav": {
            "audioplayer": (init,playwav) # первая функция инициализации, вторая - проиграть wav-файл
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def init(core:VACore):
    pass

def playwav(core:VACore, wavfile:str):
    AudioPlayer(wavfile).play(block=True)
    return

