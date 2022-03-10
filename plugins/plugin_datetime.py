# Дата и время
# author: Vladislav Janvarev

from datetime import datetime

from vacore import VACore

# функция на старте
def start(core:VACore):
    manifest = { # возвращаем настройки плагина - словарь
        "name": "Дата и время", # имя
        "version": "1.0", # версия
        "require_online": False, # требует ли онлайн?

        "commands": { # набор скиллов. Фразы скилла разделены | . Если найдены - вызывается функция
            "дата": play_date,
            "время": play_time,
        }
    }
    return manifest

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
                'двадацать четвёртое', 'двадцать пятое', 'двадцать шестое',
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
    from utils.num_to_text_ru import num2text
    now = datetime.now()
    hours = int(now.strftime("%H"))
    mins = int(now.strftime("%M"))
    core.play_voice_assistant_speech("сейчас "+num2text(hours)+" "+num2text(mins))
