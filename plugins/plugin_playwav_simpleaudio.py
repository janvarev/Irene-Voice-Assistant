# Playwav plugin for simpleaudio engine
# author: Alexander Danilov

import os

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "PlayWav through simpleaudio",
        "version": "1.0",
        "require_online": False,

        "playwav": {
            "simpleaudio": (init,playwav) # первая функция инициализации, вторая - проиграть wav-файл
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def init(core:VACore):
    import simpleaudio as sa
    pass

def playwav(core:VACore, wavfile:str):
    import simpleaudio as sa
    wave_obj = sa.WaveObject.from_wave_file(wavfile)
    play_obj = wave_obj.play()
    play_obj.wait_done()

    return
