from vacore import VACore

import os

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Акции на Московской бирже",
        "version": "1.2",
        "require_online": True,

        "commands": {

        },

        "default_options": {
            "tickers": {
                "": [ # "ирина акции"
                    ["sber", "Сбер"],
                    ["gazp", "Газпром"]
                ],
                "сбер": [ # "ирина акции сбер"
                    ["sber", "Сбер"],
                ],
            },
            "portfolios": { # разные портфели акций
                "тест": { # команда "ирина портфель тест"
                    "portfolio": [ # портфель акций
                        ["sberp", 100],
                        ["sber", 100]
                    ],
                    "start_inv": 40000, # стартовая цена портфеля
                }
            }
        }

    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    # модифицируем манифест, добавляя команды на основе options, сохраненных в файле
    cmds = {}
    cmdoptions = manifest["options"]["portfolios"]
    for cmd in cmdoptions.keys():
        cmds[cmd]  = (run_portfolio, cmdoptions[cmd])
    manifest["commands"]["портфель"] = cmds

    cmds2 = {}
    cmdoptions = manifest["options"]["tickers"]
    for cmd in cmdoptions.keys():
        cmds2[cmd]  = (run_stocks, cmdoptions[cmd])
    manifest["commands"]["акции|акция"] = cmds2


    return manifest

data_stocks = {}

def update_stocks():
    try:
        import requests
        res = requests.get("https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json?iss.meta=off&iss.only=marketdata&marketdata.columns=SECID,LAST")
        data = res.json()
        global data_stocks
        data_stocks = {}
        for st in data["marketdata"]["data"]:

            data_stocks[st[0]] = st[1]

        return True

    except:
        import traceback
        traceback.print_exc()
        return False

def run_stocks(core:VACore, phrase:str, param):
    isUpdated = update_stocks()
    if isUpdated:
        #print(data_stocks["SBERP"])
        #options = core.plugin_options(modname)
        #from utils.num_to_text_ru import num2text
        txt = ""
        for t in param:
            price = data_stocks[str(t[0]).upper()]
            pricetxt = str(price)
            if price > 1000: # спецкейс для дорогих акций, иначе тупо
                from utils.num_to_text_ru import num2text
                pricetxt = num2text(int(price))
            txt += t[1]+" "+pricetxt+" . "

        core.say(txt)

    else:
        core.say("Проблемы с соединением с биржей")

def run_portfolio(core:VACore, phrase:str, param: dict):
    isUpdated = update_stocks()
    if isUpdated:
        #print(data_stocks["SBERP"])

        from utils.num_to_text_ru import num2text

        sum = 0
        for t in param["portfolio"]:
            cur = data_stocks[str(t[0]).upper()]
            value = cur*t[1]
            print("{0}: {1} шт по цене {2} - всего {3}".format(str(t[0]).upper(),t[1],cur,value))
            sum += value
        print("Всего: {0}".format(sum))

        # округляем до удобного
        sum = int(sum/1000)*1000

        txt = "Стоимость портфеля {0} . ".format(num2text(sum))
        if sum > param["start_inv"]:
            txt += "Текущая прибыль {0} . ".format(num2text(sum-param["start_inv"]))
        else:
            txt += "Текущий убыток {0} . ".format(num2text(param["start_inv"]-sum))

        core.say(txt)

    else:
        core.say("Проблемы с соединением с биржей")


