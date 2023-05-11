# Плагин, позволяющий загружать core плагины голосового помощника vasisualy
# https://github.com/Oknolaz/vasisualy

# 1. Плагины надо кидать в plugins_vasi/skills
# 2. от каждого плагина ожидается, что в модуле будет прописан triggers, на основании которого
# формируется список команд. Если нет - плагин надо доработать.

# author: Vladislav Janvarev

import os

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "vasisualy plugins loader",
        "version": "1.0",
        "description": "Технический плагин для загрузки плагинов голосового помощника vasisualy (https://github.com/Oknolaz/vasisualy)\n"
                        "1. Плагины надо кидать в plugins_vasi/skills"
                        "2. От каждого плагина ожидается, что в модуле будет прописан triggers, на основании которого"
                        "формируется список команд. Если нет - плагин надо доработать.",
        "require_online": True,

        "default_options": {

        },

        "commands": {

        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):

    #options = manifest["options"]
    #print(options)

    # set interface
    import plugins_vasi.core.speak
    plugins_vasi.core.speak.core = core

    # 2. run all plugins from plugins folder
    from os import listdir
    from os.path import isfile, join
    pluginpath = core.jaaRootFolder + "/plugins_vasi/skills"
    files = [f for f in listdir(pluginpath) if isfile(join(pluginpath, f))]

    for fil in files:
        # print fil[:-3]
        if fil.endswith(".py"):
            modfile = fil[:-3]
            init_vasi_plugin(core, modfile, manifest)

    return manifest

def import_plugin(module_name):
    import sys

    __import__(module_name)

    if module_name in sys.modules:
        return sys.modules[module_name]
    return None

def run_vasi_plugin(core:VACore, phrase:str, param):
    param.main(core.input_cmd_full,None)

def init_vasi_plugin(core:VACore,modname,manifest:dict):
    print(manifest)

    # import
    try:
        mod = import_plugin("plugins_vasi.skills."+modname)
    except Exception as e:
        print("VASI PLUGIN ERROR: {0} error on load: {1}".format(modname, str(e)))
        return False

    # run start function
    try:
        res = list(mod.trigger)
    except Exception as e:
        print("VASI PLUGIN ERROR: {0} error on get triggers: {1}".format(modname, str(e)))
        return False

    cmds_str = "|".join(res)

    manifest["commands"][cmds_str] = (run_vasi_plugin, mod)