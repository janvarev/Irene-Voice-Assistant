# Рандом
# author: Vladislav Janvarev

import random
from vacore import VACore

# функция на старте
def start(core:VACore):
    manifest = { # возвращаем настройки плагина - словарь
        "name": "Рандом", # имя
        "version": "1.0", # версия
        "require_online": False, # требует ли онлайн?

        "commands": { # набор скиллов. Фразы скилла разделены | . Если найдены - вызывается функция
            "подбрось|брось": { # если нашли - парсим дальше
                "монету|монетку": play_coin,
                "кубик|кость": play_dice,
            }
        }
    }
    return manifest

def play_coin(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла,
                                              # если юзер сказал больше
                                              # в этом плагине не используется
    arrR = [
        "Выпал орел",
        "Выпала решка",
    ]
    core.play_voice_assistant_speech(arrR[random.randint(0, len(arrR) - 1)])

def play_dice(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла,
    # если юзер сказал больше
    # в этом плагине не используется
    arrR = [
        "Выпала единица",
        "Выпало два",
        "Выпало три",
        "Выпало четыре",
        "Выпало пять",
        "Выпало шесть",
    ]
    core.play_voice_assistant_speech(arrR[random.randint(0, len(arrR) - 1)])
