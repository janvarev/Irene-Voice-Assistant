# Webapi settings
# author: Vladislav Janvarev



import os

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Webapi options",
        "version": "1.0",
        "require_online": False,

        "default_options": {
            "host": "127.0.0.1",
            "port": 5003,
            "log_level": "info"
        },

    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

