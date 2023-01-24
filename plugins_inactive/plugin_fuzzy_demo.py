# Demo plugin for fuzzy input processing
# author: Vladislav Janvarev

import os

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Fuzzy input processing (demo)",
        "version": "1.0",
        "require_online": False,

        "fuzzy_processor": {
            "demo_timer": (init,predict) # первая функция инициализации, вторая - обработка
        }
    }
    return manifest

def init(core:VACore):
    pass

def predict(core:VACore, command:str, context:dict): # на входе - команда + текущий контекст в формате Ирины
    # пользователь хочет что-то сказать?
    # наверняка это про таймер!
    for k in context.keys():
        if str(k).find("таймер") != -1:
            return (k, 1, "абвгд")
            # возвращаем тройку: ключ команды, уверенность (от 0 до 1), остаток фразы.
            # Тут возвращаем остаток фразы, чтобы Ирина переспросила про таймер

    # не нашли ничего со словом таймер - не знаем, что это
    return None


