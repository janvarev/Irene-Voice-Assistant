# Яндекс.Расписания - работает точно для электричек
# author: Vladislav Janvarev

import os

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Яндекс Расписания",
        "version": "1.0",
        "require_online": True,

        "description": """
Расписание ближайших электричек через Яндекс.Расписания. 
Голосовая команда: электричка, электрички.
Требует установки в конфиге бесплатного API-ключа для личных нужд (до 500 запросов в сутки) с https://yandex.ru/dev/rasp/raspapi/ , а также станций отправления и назначения
ID станций отправления и назначения можно подсмотреть в URL-строке браузера при поиске расписания по нужным вам станциям.            
""",

        "options_label": {
            "apiKey": "API-ключ",

            "from": "ID станции отправления",
            "to1": "ID станции назначения",

        },

        "default_options": {
            "apiKey": "", # get at https://yandex.ru/dev/rasp/raspapi/

            "from": "s9600681",
            "to1": "s2000002",

        },

        "commands": {
            "ближайший поезд|электричка|электрички": run_poezd,
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def run_poezd(core:VACore, phrase:str):

    options = core.plugin_options(modname)

    if options["apiKey"] == "":
        core.play_voice_assistant_speech("Нужен ключ апи для получения расписания")
        return

    try:
        # datetime
        import datetime
        now = datetime.datetime.now().__str__()
        print(now)

        from datetime import date
        current_date = date.today().__str__()

        import requests
        res = requests.get("https://api.rasp.yandex.net/v3.0/search/",
                           params={'from': options["from"], 'to': options["to1"], 'format':'json',
                                   'date': current_date,
                                   'apikey': options["apiKey"]})
        data = res.json()
        print(data)


        cnt = 1
        txt = ""
        for segment in data["segments"]:
            dep = str(segment["departure"]).replace("T"," ")
            if dep > now:
                hours = dep[11:13]
                min = dep[14:16]
                if cnt == 1:
                    txt += "Ближайшая электричка в {0} {1}. ".format(hours,min)
                    #print(txt)
                    cnt += 1
                elif cnt == 2:
                    txt += "Следующая в {0} {1}. ".format(hours,min)
                    #print(txt)
                    cnt += 1

                elif cnt == 3:
                    txt += "Дальше в {0} {1}. ".format(hours,min)
                    #print(txt)
                    cnt += 1
                    break
            #print(dep)
        print(txt)
        core.play_voice_assistant_speech(txt)


    except:
        import traceback
        traceback.print_exc()
        core.play_voice_assistant_speech("Проблемы с расписанием. Посмотрите логи")

        return

