# Ai Timer
# author: Vladislav Janvarev

import time
import os

from vacore import VACore
import utils.num_to_text_ru as num_to_text

male_units_hour = ((u'час', u'часа', u'часов'), 'm')
female_units_min2 = ((u'минуту', u'минуты', u'минут'), 'f')
female_units_min = ((u'минута', u'минуты', u'минут'), 'f')
female_units_sec2 = ((u'секунду', u'секунды', u'секунд'), 'f')
female_units_sec = ((u'секунда', u'секунды', u'секунд'), 'f')
#female_units_uni = ((u'', u'', u''), 'f')

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Таймер AI",
        "version": "1.0",
        "require_online": False,

        "description": "Плагин таймера\n"
                       "Голосовая команда: таймер, таймер десять минут, таймер двадцать секунд\n"
                        "Просто 'таймер' ставит таймер на 5 минут",

        "options_label": {
            "wavRepeatTimes": "число повторений WAV-файла сигнала таймера",
            "wavPath": "путь к звуковому файлу",
        },

        "default_options": {
            "wavRepeatTimes": 1, # число повторений WAV-файла таймера
            "wavPath": 'media/timer.wav', # путь к звуковому файлу
        },

        "ai_tools": {
            "set_timer": {
                "v": "1", # версия описания AI Tool.
                # В зависимости от неё будет по-разному обрабатываться доп параметры
                "function": set_timer,
                "manifest": {
                    "type": "function",
                    "function": {
                        # "name": "set_timer",
                        # name будет автоматически присвоено на основании базового ключа словаря
                        "description": "Set timer for specific time. "
                                       "You must specify hours, minutes and seconds for it. All must be integers."
                                       "If no specifications, set timer for 5 minutes, 0 hours, 0 seconds."
                                       "Если указывается, например, на \"полминуты\", сконвертируй их в integer величины."
                                       "Например, полминуты будет 30 секунд, полчаса - 30 минут.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "hours": {
                                    "type": "integer",
                                    "description": "Количество часов, на которое ставится таймер",
                                },
                                "minutes": {
                                    "type": "integer",
                                    "description": "Количество минут, на которое ставится таймер",
                                },
                                "seconds": {
                                    "type": "integer",
                                    "description": "Количество секунд, на которое ставится таймер",
                                },

                            },
                            "required": ["hours", "minutes", "seconds"],
                        },
                    },
                }
            }
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def set_timer(core:VACore, hours:int, minutes:int, seconds:int):
    txt = ""
    if hours > 0:
        txt += num_to_text.num2text(hours, male_units_hour)+" "
    if minutes > 0:
        txt += num_to_text.num2text(minutes, female_units_min)+" "
    if seconds > 0:
        txt += num_to_text.num2text(seconds, female_units_sec)+" "

    set_timer_real(core, hours*3600+minutes*60+seconds, txt)

def set_timer_real(core:VACore, num:int, txt:str):
    core.set_timer(num,(after_timer, txt))
    core.play_voice_assistant_speech("Ставлю таймер на "+txt)

def after_timer(core:VACore, txt:str):
    options = core.plugin_options(modname)

    for i in range(options["wavRepeatTimes"]):
        core.play_wav(options["wavPath"])
        time.sleep(0.2)

    core.play_voice_assistant_speech(txt+" прошло")
    #core.play_voice_assistant_speech("БИП! БИП! БИП! "+txt+" прошло")

if __name__ == "__main__":
    set_timer(None,"")
