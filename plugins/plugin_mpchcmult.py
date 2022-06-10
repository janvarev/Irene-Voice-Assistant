# Проигрывание музыки/видео
# author: Vladislav Janvarev

import subprocess

#from voiceassmain import play_voice_assistant_speech
from vacore import VACore


multPath = ""
serialPath = ""

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "MPC-HC проигрывание мультиков/сериалов",
        "version": "2.0",
        "require_online": False,

        "default_options": {
            "multPath": '',
            "serialPath": '',
        },

        "commands": {
            "запусти плеер": run_player,
            "мультик": play_mult,
            "сериал": play_serial,
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    #print(manifest["options"])
    global multPath, serialPath
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
    for f in mult_files:
        name = str(f)[:-4].lower().replace(".","").replace(",","")
        if name == phrase:
            print("Мульт ",f)
            subprocess.Popen([core.mpcHcPath, multPath+"\\"+f])
            return

    core.say("Не нашла. Пожалуйста, повтори только название.")
    core.context_set(play_mult)

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
