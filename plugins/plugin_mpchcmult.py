# Проигрывание музыки/видео
# author: Vladislav Janvarev

import subprocess
import requests
#from voiceassmain import play_voice_assistant_speech
from vacore import VACore


multPath = ""
serialPath = ""
options = {}

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "MPC-HC проигрывание мультиков/сериалов",
        "version": "3.0",
        "require_online": False,

        "description": """
Проигрывание медиа через MPC-HC из определенной папки (оффлайн).

(В принципе, можно попробовать использовать вместо MPC-HC любой другой плеер, вероятно, будет работать)
 
### Пример "мультик <название_мультика>". 

Папка мультиков задается в конфиге (multPath). 

При вызове команды в папке ищется файл с соответствующим названием <название_мультика> и любым расширением. Если найден - запускается на проигрывание.
(Так что можно делать свою базу данных мультов, вместо ютуба с непонятными алгоритмами ранжирования). 

### Пример "сериал <название сериала> <номер серии>".

Папка сериалов задается в конфиге (serialPath).

При вызове команды ищется
   * папка с таким названием
   * или (если неудобно переназывать папку) ищется в папке файл `_irenename.txt` в кодировке UTF-8. В нем считываются все строки, и каждая из них - это указатель имени данной папки сериала для Ирины.
   
Например: папка "Babylon 5" содержит файл "_irenename.txt" со строкой "вавилон". Сериал может быть запущен по фразе "сериал вавилон два" (вторая серия)

Последним параметром команды является номер серии. Варианты:
  * номер серии - один, два и т.д.
  * "последняя" - для последней доступной серии
  
_Доп инфа:_

1. Предполагается, что медиафайлы ["mkv","avi","mp4","mpg"], будучи отсортированы в алфавитном порядке дают серии по порядку.

2. Серии с субтитрами поддерживаются; файлы субтитров не будут учтены при поисках серии, не беспокойтесь о них.
""",

        "options_label": {
            "multPath": "Путь до мультфильмов",
            "serialPath": 'Путь до сериалов',
            "player": "mpc-hc|dune MPC-HC локальный, Dune - по сети (поддерживается Dune HD Player)",
            "dune_ip": "Для DUNE - внутренний IP адрес",
            "dune_multPath": "Сетевой путь до мультфильмов (нужен Dune HD). Например: smb://192.168.1.4/mults/",
        },

        "default_options": {
            "multPath": '',
            "serialPath": '',
            "player": "mpc-hc",
            "dune_ip": "",
            "dune_multPath": "",
        },

        "commands": {
            "запусти плеер": run_player,
            "мультик": play_mult,
            "сериал": play_serial,
            "стоп мультик|останови мультик": stop_mult,
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    #print(manifest["options"])
    global multPath, serialPath, options
    options = manifest["options"]

    multPath = options["multPath"]
    serialPath = options["serialPath"]

    return manifest

def run_player(core:VACore, phrase: str):
    subprocess.Popen([core.mpcHcPath])

def play_mult(core:VACore, phrase: str):
    if multPath == "":
        core.say("Не установлена папка с мультиками")
        return

    if phrase == "":
        core.say("Пожалуйста, уточни какой именно мультик")
        core.context_set(play_mult)
        return

    #core.play_voice_assistant_speech("Ищу мультфильм "+find)
    mult_files= mult_list()
    name_dict = {}
    #f_list = []
    for f in mult_files:
        name = str(f)[:-4].lower().replace(".","").replace(",","")
        name_dict[name] = f
        # if name == phrase:
        #     print("Мульт ",f)
        #     #subprocess.Popen([core.mpcHcPath, multPath+"\\"+f])
        #     play_mult_direct(core, f)
        #     core.say("Запускаю!")
        #     return

    res = core.find_best_cmd_with_fuzzy(phrase,name_dict,False,0.7)
    if res is not None:
        print(res)
        f = name_dict[res[0]]
        print("Мульт ", f)
        #     #subprocess.Popen([core.mpcHcPath, multPath+"\\"+f])
        play_mult_direct(core, f)
        core.say("Запускаю!")
        return



    core.say("Не нашла. Пожалуйста, повтори только название.")
    core.context_set(play_mult)

def play_mult_direct(core:VACore, f:str):
    if options["player"] == "mpc-hc":
        subprocess.Popen([core.mpcHcPath, multPath + "\\" + f])
    elif options["player"] == "dune":
        res_str = requests.get(
            f"http://{options.get('dune_ip')}/cgi-bin/do?cmd=start_playlist_playback&media_url={options.get('dune_multPath')}{f}&loop_mode=0")

def stop_mult(core:VACore, phrase: str):
    if options["player"] == "mpc-hc":
        #subprocess.Popen([core.mpcHcPath, multPath + "\\" + f])
        pass
    elif options["player"] == "dune":
        res_str = requests.get(
            f"http://{options.get('dune_ip')}/cgi-bin/do?cmd=main_screen")


def play_serial(core:VACore, phrase: str):
    if serialPath == "":
        core.say("Не установлена папка с сериалами")
        return

    if phrase == "":
        core.say("Пожалуйста, уточни сериал")
        core.context_set(play_serial)
        return

    #core.play_voice_assistant_speech("Ищу мультфильм "+find)
    serials = serial_list()
    for serial_name in serials.keys():
        if phrase.startswith(serial_name):
            rest_phrase = phrase[(len(serial_name)+1):]
            serial_dir = serials[serial_name]
            #self.execute_next(rest_phrase,next_context)
            play_serial_number(core,rest_phrase,serial_dir)
            # parsing restphrase

            return

    core.say("Не нашла, повтори название.")
    core.context_set(play_serial)

def play_serial_number(core:VACore, phrase: str, serial_dir:str):
    from os import listdir
    from os.path import isfile, join
    #pluginpath = m #os.path.dirname(__file__)+"/plugins"
    serial_path = join(serialPath,serial_dir)
    series = [f for f in listdir(serial_path) if (isfile(join(serial_path, f)) and (str(f)[-3:].lower() in ["mkv","avi","mp4","mpg"]))]

    # for f in series:
    #     print(f,str(f)[:-3].lower())

    if len(series) == 0:
        core.say("Ошибка: серии в этом сериале не найдены")
        #core.context_set((play_serial_number,serial_dir))
        return

    print("Серии:",series)

    if phrase == "":
        core.say("Номер серии?")
        core.context_set((play_serial_number,serial_dir))
        return

    sum = None
    import utils.num_to_text_ru as num_to_text

    if sum == None:
        if phrase == "первая": sum = 1
        if phrase == "последняя": sum = len(series)

    if sum == None:
        for i in range(100000,0,-1):
            str_try = num_to_text.num2text(i)
            if phrase == str_try:
                sum = i
                break

    if sum == None:
        core.say("Номер серии?")
        core.context_set((play_serial_number,serial_dir))
        return

    if sum > len(series):
        core.say("Серии с таким номером нет. Другой номер?")
        core.context_set((play_serial_number,serial_dir))
        return

    core.say("Запускаю")
    print("Сериал",serial_dir,"серия",series[sum-1])
    subprocess.Popen([core.mpcHcPath, serial_path+"\\"+series[sum-1]])
    return

    # files = [str(f)[:-4].lower() for f in files]
    # files = [str(f).replace(".","").replace(",","") for f in files]
    #return files


def mult_list():
    from os import listdir
    from os.path import isfile, join
    #pluginpath = m #os.path.dirname(__file__)+"/plugins"
    files = [f for f in listdir(multPath) if isfile(join(multPath, f))]
    # files = [str(f)[:-4].lower() for f in files]
    # files = [str(f).replace(".","").replace(",","") for f in files]
    return files

def serial_list():
    from os import listdir
    from os.path import isfile, isdir, join
    import os
    #pluginpath = m #os.path.dirname(__file__)+"/plugins"
    dirs = [f for f in listdir(serialPath) if isdir(join(serialPath, f))]

    res = {}
    for dir in dirs:
        k1 = str(dir).lower().replace(".","").replace(",","")
        res[k1] = dir

        file_irene = join(serialPath, dir, "_irenename.txt")
        if os.path.exists(file_irene):
            with open(file_irene, encoding="utf-8") as file:
                lines = file.readlines()
                lines = [line.rstrip() for line in lines]

            for line in lines:
                res[line] = dir


    # files = [str(f)[:-4].lower() for f in files]
    # files = [str(f).replace(".","").replace(",","") for f in files]
    return res

if __name__ == "__main__":
    print(serial_list())
