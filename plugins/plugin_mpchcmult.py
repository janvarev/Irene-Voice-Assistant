# Проигрывание музыки/видео
# author: Vladislav Janvarev

import subprocess

# from voiceassmain import play_voice_assistant_speech
from vacore import VACore

multPath = ""

# функция на старте
def start(core: VACore):
    manifest = {
        "name": "MPC-HC проигрывание мультиков",
        "version": "1.2",
        "require_online": False,
        "default_options": {
            "multPath": "",
        },
        "commands": {
            "запусти плеер": run_player,
            "мультик": play_mult,
        },
    }
    return manifest


def start_with_options(core: VACore, manifest: dict):
    # print(manifest["options"])
    global multPath
    options = manifest["options"]

    multPath = options["multPath"]

    return manifest


def run_player(core: VACore, phrase: str):
    subprocess.Popen([core.mpcHcPath])


def play_mult(core: VACore, phrase: str):
    if phrase == "":
        core.play_voice_assistant_speech("Пожалуйста, уточни какой именно мультик")
        # здесь надо вернуть контекст, чтобы не добавлять Ирина. но это позже
        return

    # core.play_voice_assistant_speech("Ищу мультфильм "+find)
    mult_files = mult_list()
    for f in mult_files:
        name = str(f)[:-4].lower().replace(".", "").replace(",", "")
        if name == phrase:
            print("Мульт ", f)
            subprocess.Popen([core.mpcHcPath, multPath + "\\" + f])
            return

    core.play_voice_assistant_speech("Не нашла такого мультика")


def mult_list():
    from os import listdir
    from os.path import isfile, join

    # pluginpath = m #os.path.dirname(__file__)+"/plugins"
    files = [f for f in listdir(multPath) if isfile(join(multPath, f))]
    # files = [str(f)[:-4].lower() for f in files]
    # files = [str(f).replace(".","").replace(",","") for f in files]
    return files


if __name__ == "__main__":
    print(mult_list())
