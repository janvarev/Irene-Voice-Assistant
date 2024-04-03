# Погода через OpenWeatherMap (https://openweathermap.org/)
# author: Vladislav Janvarev

# работает без пакета pyowm! на прямых запросах

import os

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Погода (open weather map)",
        "version": "1.1",
        "require_online": True,

        "description": """
Погода (онлайн). 
Голосовые команды: "погода, погода завтра, погода послезавтра, прогноз погоды". 
Требует установки в конфиге бесплатного API-ключа с https://openweathermap.org/ , а также местоположения
(Рекомендуется вручную заполнить геокординаты lon и lat)
""",

        "default_options": {
            "apiKey": "", # get at https://openweathermap.org/

            "city": "Moscow",
            "country": "RU",
            "lon": 0, # will be auto-calculated base on city. Or you can fill it manual
            "lat": 0,
            "is_active": False,
        },

        "commands": {
            "погода": (run_weather, ""), # погода завтра, погода послезавтра
            "прогноз погоды|прогноз погода": (run_weather, "prognoz"),
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

    weather_api_key = options["apiKey"]
    if weather_api_key == "":
        print("OWM: нужен api_key для получения погоды! пока отключено")
        #manifest["commands"] = {}
        return manifest

    if options["lat"] == 0 and options["lon"] == 0: # если не указаны координаты - получаем их
        print("OWM: try to locate city...")
        # не установлено место
        try:
            import requests
            res_str = requests.get("http://api.openweathermap.org/geo/1.0/direct",
                               params={'q': options["city"]+","+options["country"], 'APPID': options["apiKey"]})
            res = res_str.json()
            print(res)
            lat = res[0]["lat"]
            lon = res[0]["lon"]

            options["lat"] = lat
            options["lon"] = lon


            core.save_plugin_options(modname,options)
            print("OWM: city {0} located at lat={1}, lon={2}".format(options["city"],lat,lon))
        except:
            import traceback
            traceback.print_exc()
            print("Проблемы с получением локации погоды. Посмотрите логи")

            return

def run_weather(core:VACore, phrase:str, addparam:str):

    options = core.plugin_options(modname)

    if options["apiKey"] == "":
        core.play_voice_assistant_speech("Нужен ключ апи для получения погоды")
        return

    try:
        #one_call = mgr.one_call(options["lat"], options["lon"], lang="ru")
        #try:
        import requests
        res = requests.get("https://api.openweathermap.org/data/2.5/onecall",
                           params={'lon': options["lon"], 'lat': options["lat"], 'units': 'metric', 'lang': 'ru', 'APPID': options["apiKey"]})
        data_one_call = res.json()
        print(data_one_call)

        from utils.num_to_text_ru import num2text

        if addparam == "" and (phrase == "" or phrase == "сейчас"):
            #print(one_call.current.status)

            # temp = one_call.current.temperature("celsius")
            # humid = one_call.current.humidity
            # veter = one_call.current.wind("meters_sec")
            # veter_int = int(veter["speed"])
            current = data_one_call["current"]
            temp = current["temp"]
            desc = current["weather"][0]["description"]
            feels_like = current["feels_like"]
            humid = int(current["humidity"])
            veter_int = int(current["wind_speed"])

            #desc = one_call.


            veter_str = num2text(veter_int,((u'метр', u'метра', u'метров'), 'm'))
            vl_str = num2text(humid,((u'процента', u'процента', u'процентов'), 'm'))

            text = "Сейчас {0}"
            if temp != feels_like:
                text = text + ", ощущается как {1}"

            text = (text + ". Влажность {2}, ветер {3} в секунду. {4}").format(
                    num2text(int(temp)),num2text(int(feels_like)),vl_str,veter_str,data_one_call["daily"][0]["weather"][0]["description"])
            print(text)
            core.play_voice_assistant_speech(text)

        if phrase == "завтра":
            #print(one_call.current.temperature("celsius"))
            forecast_data = data_one_call["daily"][0]
            #print(temp)
            # humid = one_call.forecast_daily[0].humidity
            #one_call.forecast_daily[0]
            text = "Завтра {0}, будет ощущаться как {1}. {3}. Ночью {2}.".format(
                num2text(int(forecast_data["temp"]["day"])),num2text(int(forecast_data["feels_like"]["day"])),int(forecast_data["temp"]["night"]),forecast_data["weather"][0]["description"])
            print(text)
            core.play_voice_assistant_speech(text)

        if phrase == "послезавтра":
            #print(one_call.current.temperature("celsius"))
            forecast_data = data_one_call["daily"][1]
            #print(temp)
            # humid = one_call.forecast_daily[0].humidity
            text = "Послезавтра {0}, будет ощущаться как {1}. {3}. Ночью {2}.".format(
                int(forecast_data["temp"]["day"]),int(forecast_data["feels_like"]["day"]),int(forecast_data["temp"]["night"]),forecast_data["weather"][0]["description"])
            print(text)
            core.play_voice_assistant_speech(text)

        if addparam =="prognoz" or (addparam == "" and phrase=="прогноз"):
            current = data_one_call["current"]
            temp = num2text(int(current["temp"]))
            desc = current["weather"][0]["description"]
            #text = "Сейчас {1}, {0}. ".format(temp, desc)
            text = "Сейчас {0}. ".format(temp, desc)

            forecast_data = data_one_call["daily"][0]
            text += "Завтра {3}, {0}. ".format(
                num2text(int(forecast_data["temp"]["day"])),num2text(int(forecast_data["feels_like"]["day"])),
                num2text(int(forecast_data["temp"]["night"])),forecast_data["weather"][0]["description"])

            forecast_data = data_one_call["daily"][1]
            text += "Послезавтра {3}, {0}. ".format(
                num2text(int(forecast_data["temp"]["day"])),num2text(int(forecast_data["feels_like"]["day"])),
                num2text(int(forecast_data["temp"]["night"])),forecast_data["weather"][0]["description"])

            forecast_data = data_one_call["daily"][2]
            text += "Дальше {3}, {0}. ".format(
                num2text(int(forecast_data["temp"]["day"])),num2text(int(forecast_data["feels_like"]["day"])),
                num2text(int(forecast_data["temp"]["night"])),forecast_data["weather"][0]["description"])

            print(text)
            core.play_voice_assistant_speech(text)

    except:
        import traceback
        traceback.print_exc()
        core.play_voice_assistant_speech("Проблемы с погодой. Посмотрите логи")

        return



