# Игра больше меньше (альтернативная реализация на меню)
# author: Vladislav Janvarev

from datetime import datetime

from vacore import VACore
import random

# функция на старте
def start(core:VACore):
    manifest = { # возвращаем настройки плагина - словарь
        "name": "Игра больше меньше (альтернативная реализация)", # имя
        "version": "1.0", # версия
        "require_online": False, # требует ли онлайн?

        "commands": { # набор скиллов. Фразы скилла разделены | . Если найдены - вызывается функция
            "игра меньше больше": play_game_start,
        }
    }
    return manifest

questNumber = -1
tries = 0



def play_game_start(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла,
                                              # если юзер сказал больше
                                              # в этом плагине не используется
    core.play_voice_assistant_speech("Скажи правила или начать")
    core.context_set(menu_main) # меню - набор фраз и правил, в конце файла

def play_cancel(core:VACore, phrase: str):
    core.say("Поняла, играть не будем")
    return

def play_rules(core:VACore, phrase: str):
    core.play_voice_assistant_speech("Правила игры. Я загадываю число от одного до тридцати. "
                                     "Ты называешь число, а я говорю, загаданное число больше названного, или меньше. "
                                     "Твоя задача - отгадать число за пять попыток. Скажи начать для начала игры.")
    core.context_set(menu_main)


def play_start(core:VACore, phrase: str):
    global questNumber, tries
    questNumber = random.randint(1,30)
    #print(questNumber)
    tries = 0
    core.play_voice_assistant_speech("Число от одного до тридцати загадано. Начинаем!")
    core.context_set(menu_in_game)
    return

def play_game(core:VACore, phrase: str, i: int):
    if phrase != "":
        # что-то не распозналось или было добавлено. Просим повторить еще раз
        core.say("Извини, не поняла число")
        core.context_set(menu_in_game)
        return

    global tries
    tries += 1
    if i == questNumber:
        core.say("Да, ты угадал. Поздравляю с победой! Скажи повторить, если хочешь сыграть еще раз.")
        core.context_set(menu_main)
        return
    else:
        txtsay = ""
        if i < questNumber:
            txtsay += "Больше. "
        else:
            txtsay += "Меньше. "

        if tries >= 5:
            txtsay += "Пять попыток прошло, к сожалению, ты проиграл. А я загадала число "+num2text(questNumber)
            txtsay += ". Скажи повторить, если хочешь сыграть еще раз."
            core.say(txtsay)
            core.context_set(menu_main)
            return
        else:
            core.say(txtsay)
            core.context_set(menu_in_game)
            return


# game menus
menu_main = {"правила":play_rules,"начать|скачать|повторить":play_start,"отмена":play_cancel}

menu_in_game = {}
from utils.num_to_text_ru import num2text
for i in range(1,31):
    menu_in_game[num2text(i)] = (play_game, i)