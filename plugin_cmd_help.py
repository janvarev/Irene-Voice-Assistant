# Игра больше меньше (альтернативная реализация на меню)
# author: Vladislav Janvarev

from datetime import datetime

from vacore import VACore
import random

# функция на старте
def start(core:VACore):
    manifest = { # возвращаем настройки плагина - словарь
        "name": "Подсказка по всем актуальным командам и их описаниям", # имя
        "version": "1.0", # версия
        "require_online": False, # требует ли онлайн?

        "commands": { # набор скиллов. Фразы скилла разделены | . Если найдены - вызывается функция
            "что|что умеешь|что можешь": help_start,
        }
    }
    return manifest

def help_start(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла, если юзер сказал больше
    core.say("Расказать кратко, подробно или отмена")
    core.context_set(menu_main) # меню - набор фраз и правил, в конце файла

def help_cancel(core:VACore, phrase: str):
    core.say("хорошо")
    return

def help_short(core:VACore, phrase: str):
    #core.play_voice_assistant_speech("выполняю команды")
    help_cmd(core,phrase,"short")
    #core.context_set(menu_main) # - снова включить текущий контекст
    #core._context_clear_timer # - сбросить таймер
    return

def help_desc(core:VACore, phrase: str):
    #core.play_voice_assistant_speech("подробно о командах")
    help_cmd(core,phrase,"desc")
    #core.context_set(menu_main)
    return

menu_main = {"кратко|коротко":help_short,"подробно":help_desc,"отмена":help_cancel}

def help_cmd(core:VACore, phrase: str, mode_help: str):
    #import inspect; print(inspect.getmembers(core.plugin_manifests))
    #import json;    print(json.dumps(core.commands))
    for manifs in core.plugin_manifests.keys():
        commands=core.plugin_manifests[manifs].get('commands')
        name=core.plugin_manifests[manifs].get('name')
        if commands!=None:
            for keyall in commands.keys():
                keys = keyall.split("|")
                msg=keys[0]
                if msg=="что умеешь":
                    continue
    
                if mode_help=='desc':
                    msg=msg + ' - '+name
                
                print(msg)
                core.say(msg)
                #if __name__ == "__main__":
                #core.play_voice_assistant_speech(msg)
    return
