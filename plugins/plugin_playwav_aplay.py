# Playwav plugin for aplay program
# source: https://github.com/mobez/Irene-Voice-Assistant/blob/master/plugins/plugin_playwav_aplay.py

import os

from vacore import VACore
#from aplay import Aplay
import subprocess

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "PlayWav through aplay",
        "version": "1.0",
        "require_online": False,

        "playwav": {
            "aplay": (init,playwav) # первая функция инициализации, вторая - проиграть wav-файл
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def init(core:VACore):
    pass

def playwav(core:VACore, wavfile:str):
    subprocess.call("aplay "+wavfile, shell=True)
    #AudioPlayer(wavfile).play(block=True)
    return

