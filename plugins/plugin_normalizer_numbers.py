# Normalizer plugin (just numbers, demo)
# author: Vladislav Janvarev

import os

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Normalizer through Numbers",
        "version": "1.0",
        "require_online": False,

        "normalizer": {
            "numbers": (init, normalize) # первая функция инициализации, вторая - реализация нормализации
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def init(core:VACore):
    pass

def normalize(core:VACore, text:str):
    return core.all_num_to_text(text)
