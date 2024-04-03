# Погода через wttr.in  
# author: Oleg Bakharev, Ivan-Firefly, Vlad Janvarev

import os
from datetime import datetime
import requests

from vacore import VACore

# местоположение

modname = os.path.basename(__file__)[:-3] # calculating modname

# информация о плагине и начальные настройки
def start(core: VACore):
    manifest = {
        'name': 'Погода (wttr.in)',
        'version': '1.1',
        'require_online': True,
        'location':'Moscow',
        "default_options": {
            "location": "Moscow",
            "is_active": False,
        },
        'commands': {
            'погода|погода за окном|погода сейчас|погода сегодня|погода сейчас': get_weather_short,
			'погода подробно|погода полный прогноз': get_weather,
            'прогноз погоды': get_weather_forecast,
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):

    options = manifest["options"]

    if options["is_active"]:
        pass
    else:
        manifest["commands"] = {}
        return manifest



# вычисляет вариант текста для конкретного числительного из набора вариантов
def compute_suffix(value: str, variants: list):
    n = int(value.strip()[-1])
    if (n == 0) or (n >= 5):
        suffix = variants[0]
    elif (n == 1):
        suffix = variants[1]
        if len(value) >= 2:
            if value.strip()[-2] == '1':
                suffix = variants[2]
    else:
        suffix = variants[2]
    return suffix


# текст прогноза погоды на основании переданных данныхъ о температуре, влажности, давлении и скорости ветра
def forecast_text(temp: str, temp_feel: str, humidity: str, pressure: str, wind_speed: str):
    text = 'Температура {0} {1}, Влажность {2} {3}, Давление - {4} {5} ртутного столба, Ветер {6} {7} в час.'.format(
        temp, compute_suffix(temp, ['градусов', 'градус', 'градуса']),
		temp_feel, compute_suffix(temp_feel, ['градусов', 'градус', 'градуса']),
        humidity, compute_suffix(humidity, ['процентов', 'процент', 'процента']),
        pressure, compute_suffix(pressure, ['миллиметров', 'миллиметр', 'миллиметра']),
        wind_speed, compute_suffix(wind_speed, ['километров', 'километр', 'километра'])
    )
    return text

def forecast_text_short(temp: str, temp_feel: str, wind_speed: str):
    text = 'Температура {0} {1}, Ощущается как {2} {3}, Ветер {4} {5} в секунду.'.format(
        temp, compute_suffix(temp, ['градусов', 'градус', 'градуса']),
		temp_feel, compute_suffix(temp_feel, ['градусов', 'градус', 'градуса']),
        wind_speed, compute_suffix(wind_speed, ['метров', 'метр', 'метра'])
    )
    return text


# запросить погоду для данного местоположения
def request_weather(core:VACore):
    options = core.plugin_options(modname)
    dd=options["location"]
    url = 'https://wttr.in/{0}?Q?m&format=j1&lang=ru'.format(dd)
    req = requests.get(url)
    return req.json()


# сформировать описание погоды, на основании словаря JSON
def get_weather_text(data: dict):
    descr = data['lang_ru'][0]['value']

    humidity = data['humidity']
    pressure = round(int(data['pressure']) / 1.333)

    if 'temp_C' in data:
        temp = data['temp_C']
    else:
        temp = data['tempC']

    wind_speed = data['windspeedKmph']

    return descr + '. ' + forecast_text(temp, humidity, str(pressure), wind_speed)

def get_weather_text_short(data: dict):
    descr = 'Сегодня '+data['lang_ru'][0]['value']

    if 'temp_C' in data:
        temp = data['temp_C']
    else:
        temp = data['tempC']

    temp_feel = data['FeelsLikeC']
    wind_speed = str(round(float(data['windspeedKmph']) * 1000 / 3600))

    return descr + '. ' + forecast_text_short(temp, temp_feel, wind_speed)


# получить текст для описания даты прогноза
def get_date(data: str):
    day_list = (
    'первое', 'второе', 'третье', 'четвёртое', 'пятое', 'шестое', 'седьмое', 'восьмое', 'девятое', 'десятое',
    'одиннадцатое', 'двенадцатое', 'тринадцатое', 'четырнадцатое', 'пятнадцатое', 'шестнадцатое', 'семнадцатое',
    'восемнадцатое', 'девятнадцатое', 'двадцатое', 'двадцать первое', 'двадцать второе', 'двадцать третье',
    'двадцать четвёртое', 'двадцать пятое', 'двадцать шестое', 'двадцать седьмое', 'двадцать восьмое',
    'двадцать девятое', 'тридцатое', 'тридцать первое')
    weekday_list = ('понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу', 'воскресенье')
    month_list = (
    'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября',
    'декабря')

    d = datetime.strptime(data, '%Y-%m-%d')
    day = day_list[d.day - 1]
    weekday = weekday_list[d.weekday()]
    month = month_list[d.month - 1]
    # year = d.year

    # text = 'Прогноз на ' + weekday + ' с датой' +  day + ' ' + month + ' ' + str(year) + ' года.'
    text = 'Прогноз на ' + weekday + ' с датой' + day + ' ' + month + ' '
    return text


# текущая погода
def get_weather(core: VACore, phrase: str):
    try:
        # core.play_voice_assistant_speech('Текущая погодная сводка')

        weathers = request_weather(core)
        text = get_weather_text(weathers['current_condition'][0])
        core.play_voice_assistant_speech(text)
        return
    except Exception as e:
        pass

def get_weather_short(core: VACore,phrase: str):
    try:
        # core.play_voice_assistant_speech('Текущая погодная сводка')

        weathers = request_weather(core)
        text = get_weather_text_short(weathers['current_condition'][0])
        core.play_voice_assistant_speech(text)
        return
    except Exception as e:
        pass

# прогноз погоды на три дня
def get_weather_forecast(core: VACore, phrase: str):
    # произнести прогноз на определенное время суток
    def say_hourly_weather(daytime: str, hourly: dict):
        core.play_voice_assistant_speech(daytime);
        text = get_weather_text(hourly)
        core.play_voice_assistant_speech(text)

    try:
        core.play_voice_assistant_speech('Прогноз на три дня')

        weathers = request_weather(core)['weather']  # город или координаты

        for weather in weathers:
            # дата на которую прогноз
            d = weather['date']

            # произнести дату
            core.play_voice_assistant_speech(get_date(d))

            # произнести утренний прогноз
            say_hourly_weather("Утро", weather['hourly'][2])

            # произнести дневной прогноз
            say_hourly_weather("День", weather['hourly'][4])

            # произнести вечернний прогноз
            say_hourly_weather("Вечер", weather['hourly'][6])

        return
    except Exception as e:
        pass
