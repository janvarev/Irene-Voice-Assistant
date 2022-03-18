# Игра больше меньше
# author: Vladislav Janvarev

from datetime import datetime

from vacore import VACore
import random

# функция на старте
def start(core:VACore):
    manifest = { # возвращаем настройки плагина - словарь
        "name": "Игра больше меньше", # имя
        "version": "1.0", # версия
        "require_online": False, # требует ли онлайн?

        "commands": { # набор скиллов. Фразы скилла разделены | . Если найдены - вызывается функция
            "игра больше меньше": play_game_start,
        }
    }
    return manifest

questNumber = -1
tries = 0

def play_game_start(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла,
                                              # если юзер сказал больше
                                              # в этом плагине не используется
    core.play_voice_assistant_speech("Скажи правила или начать")
    core.context_set(play_1)

def play_1(core:VACore, phrase: str):
    if phrase == "правила":
        core.play_voice_assistant_speech("Правила игры. Я загадываю число от одного до тридцати. "
                                         "Ты называешь число, а я говорю, загаданное число больше названного, или меньше. "
                                         "Твоя задача - отгадать число за пять попыток. Скажи начать для начала игры.")
        core.context_set(play_1)
        return
    if phrase == "начать" or phrase == "скачать" or phrase == "повторить":
        global questNumber, tries
        questNumber = random.randint(1,30)
        #print(questNumber)
        tries = 0
        core.play_voice_assistant_speech("Число от одного до тридцати загадано. Начинаем!")
        #play_game_start(core,"")
        core.context_set(play_2)
        return

    if phrase == "отмена":
        core.say("Поняла, играть не будем")
        return

    core.play_voice_assistant_speech("Не поняла...")
    core.context_set(play_1)

def play_2(core:VACore, phrase: str):
    from utils.num_to_text_ru import num2text
    for i in range(1,31):
        if phrase == num2text(i):
            global tries
            tries += 1
            if i == questNumber:
                core.say("Да, ты угадал. Поздравляю с победой! Скажи повторить, если хочешь сыграть еще раз.")
                core.context_set(play_1)
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
                    core.context_set(play_1)
                    return
                else:
                    core.say(txtsay)
                    core.context_set(play_2)
                    return

    core.play_voice_assistant_speech("Не поняла число, скажи еще раз!")
    core.context_set(play_2)