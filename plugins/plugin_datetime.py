# Дата и время
# author: Vladislav Janvarev

from datetime import datetime
from utils.num_to_text_ru import num2text
from vacore import VACore
import os

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = { # возвращаем настройки плагина - словарь
        "name": "Дата и время", # имя
        "version": "1.2", # версия
        "require_online": False, # требует ли онлайн?

        "description": "Демонстрационный плагин\n"
                       "Голосовая команда: дата, подбрось время",

        "options_label": {
            "sayNoon": 'говорить "полдень" и "полночь" вместо 12 и 0 часов',
            "skipUnits": 'не произносить единицы времени ("час", "минуты")',
            "unitsSeparator": 'сепаратор при озвучивании 10 часов <sep> 10 минут. Вариант: " и "',
            "skipMinutesWhenZero": 'не озвучивать минуты, если равны 0',
        },

        "default_options": {
            "sayNoon": False, # говорить "полдень" и "полночь" вместо 12 и 0 часов
            "skipUnits": False,  # не произносить единицы времени ("час", "минуты")
            "unitsSeparator": ", ",  # сепаратор при озвучивании 10 часов <sep> 10 минут. Варианты: " и "
            "skipMinutesWhenZero": True, # не озвучивать минуты, если равны 0
        },

        "commands": { # набор скиллов. Фразы скилла разделены | . Если найдены - вызывается функция
            "дата": play_date,
            "время": play_time,
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def play_date(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла,
                                              # если юзер сказал больше
                                              # в этом плагине не используется
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    weekday = ["понедельник","вторник","среда","четверг","пятница","суббота","воскресенье"][datetime.weekday(now)]
    core.play_voice_assistant_speech("сегодня "+weekday+", "+get_date(date))

def get_date(date):
    day_list = ['первое', 'второе', 'третье', 'четвёртое',
                'пятое', 'шестое', 'седьмое', 'восьмое',
                'девятое', 'десятое', 'одиннадцатое', 'двенадцатое',
                'тринадцатое', 'четырнадцатое', 'пятнадцатое', 'шестнадцатое',
                'семнадцатое', 'восемнадцатое', 'девятнадцатое', 'двадцатое',
                'двадцать первое', 'двадцать второе', 'двадцать третье',
                'двадцать четвёртое', 'двадцать пятое', 'двадцать шестое',
                'двадцать седьмое', 'двадцать восьмое', 'двадцать девятое',
                'тридцатое', 'тридцать первое']
    month_list = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    date_list = date.split('-')
    return (day_list[int(date_list[2]) - 1] + ' ' +
            month_list[int(date_list[1]) - 1] + ' '
            #date_list[0] + ' года'
            )

def play_time(core:VACore, phrase: str): # в phrase находится остаток фразы после названия скилла,
    # если юзер сказал больше
    # в этом плагине не используется

    options = core.plugin_options(modname)

    if options["skipUnits"]:
        units_minutes = (('', '', ''), 'f')
        units_hours = (('', '', ''), 'm')
    else:
        units_minutes = ((u'минута', u'минуты', u'минут'), 'f')
        units_hours = ((u'час', u'часа', u'часов'), 'm')

    now = datetime.now()
    hours = int(now.strftime("%H"))
    minutes = int(now.strftime("%M"))

    if options["sayNoon"]:
        if hours == 0 and minutes == 0:
            core.say("Сейчас ровно полночь")
            return
        elif hours == 12 and minutes == 0:
            core.say("Сейчас ровно полдень")
            return

    txt = num2text(hours, units_hours)
    if minutes > 0 or options["skipMinutesWhenZero"] is not True:
        txt = "Сейчас " + txt
        if not options["skipUnits"]:
            txt += options["unitsSeparator"]
        txt += num2text(minutes, units_minutes)
    else:
        txt = "Сейчас ровно " + txt

    core.say(txt)
