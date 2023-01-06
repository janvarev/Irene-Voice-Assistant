# Playwav plugin for sounddevice engine
# author: Vladislav Janvarev

import os

from vacore import VACore
import sounddevice as sound_device
import soundfile as sound_file

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "PlayWav through sounddevice",
        "version": "1.0",
        "require_online": False,

        "playwav": {
            "sounddevice": (init,playwav) # первая функция инициализации, вторая - проиграть wav-файл
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def init(core:VACore):
    pass

def playwav(core:VACore, wavfile:str):
    #AudioPlayer(wavfile).play(block=True)
    filename = os.path.dirname(__file__)+"/../"+wavfile

    #filename = 'timer/Sounds/Loud beep.wav'
    # now, Extract the data and sampling rate from file
    data_set, fsample = sound_file.read(filename, dtype = 'float32')

    # Этот фикс позволяет убрать проглатывания из концов фраз
    # Просто добавляет 0 в конце проигрываемому файлу
    # https://github.com/spatialaudio/python-sounddevice/issues/283
    # zeros = []
    # for i in range(5000):
    #     zeros.append(0.0)
    import numpy
    zeros = numpy.zeros((5000,)) # fix by modos189
    data_set_new = numpy.concatenate((data_set,zeros))
    # end fix

    sound_device.play(data_set_new, fsample)
    # Wait until file is done playing
    status = sound_device.wait()
    return

