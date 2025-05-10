# Normalizer plugin RUNorm (require pip install runorm), https://github.com/Den4ikAI/runorm
# author: Vladislav Janvarev

import os

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Normalizer through RUNorm",
        "version": "1.0",
        "require_online": False,

        "normalizer": {
            "runorm": (init, normalize) # первая функция инициализации, вторая - реализация нормализации
        },

        "default_options": {
            "modelSize": "small",  # модель
            "device": "cpu"  # cuda, если хотите на GPU
        },
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def init(core:VACore):
    options = core.plugin_options(modname)

    from runorm import RUNorm

    # Используйте load(workdir="./local_cache") для кэширования моделей в указанной папке.
    # Доступные модели: small, medium, big
    # Выбирайте устройство используемое pytorch с помощью переменной device
    normalizer = RUNorm()
    normalizer.load(model_size=options["modelSize"], device=options["device"])

    core.normalizerRUNorm = normalizer



def normalize(core:VACore, text:str):
    return core.normalizerRUNorm.norm(text)
