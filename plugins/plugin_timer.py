# Timer
# author: Vladislav Janvarev

import os
import time

import utils.num_to_text_ru as num_to_text
from vacore import VACore

female_units_min2 = ((u"минуту", u"минуты", u"минут"), "f")
female_units_min = ((u"минута", u"минуты", u"минут"), "f")
female_units_sec2 = ((u"секунду", u"секунды", u"секунд"), "f")
female_units_sec = ((u"секунда", u"секунды", u"секунд"), "f")
# female_units_uni = ((u'', u'', u''), 'f')

modname = os.path.basename(__file__)[:-3]  # calculating modname

# функция на старте
def start(core: VACore):
    manifest = {
        "name": "Таймер",
        "version": "1.2",
        "require_online": False,
        "default_options": {
            "wavRepeatTimes": 1,  # число повторений WAV-файла таймера
            "wavPath": "media/timer.wav",  # путь к звуковому файлу
        },
        "commands": {
            "таймер|тайгер": set_timer,
        },
    }
    return manifest


def start_with_options(core: VACore, manifest: dict):
    pass


def set_timer(core: VACore, phrase: str):
    if phrase == "":
        # таймер по умолчанию - на 5 минут
        txt = num_to_text.num2text(5, female_units_min)
        set_timer_real(core, 5 * 60, txt)
        return

    phrase += " "

    if phrase.startswith("на "):  # вырезаем "на " (из фразы "на Х минут")
        phrase = phrase[3:]

    # ставим секунды?
    for i in range(1, 100):
        txt = num_to_text.num2text(i, female_units_sec) + " "
        if phrase.startswith(txt):
            # print(txt)
            set_timer_real(core, i, txt)
            return

        txt2 = num_to_text.num2text(i, female_units_sec2) + " "
        if phrase.startswith(txt2):
            # print(txt,txt2)
            set_timer_real(core, i, txt)
            return

        txt3 = str(i) + " секунд "
        if phrase.startswith(txt3):
            # print(txt,txt2)
            set_timer_real(core, i, txt)
            return

    # ставим минуты?
    for i in range(1, 100):
        txt = num_to_text.num2text(i, female_units_min) + " "
        if phrase.startswith(txt):
            set_timer_real(core, i * 60, txt)
            return

        txt2 = num_to_text.num2text(i, female_units_min2) + " "
        if phrase.startswith(txt2):
            set_timer_real(core, i * 60, txt)
            return

        txt3 = str(i) + " минут "
        if phrase.startswith(txt3):
            # print(txt,txt2)
            set_timer_real(core, i * 60, txt)
            return

    # без указания единиц измерения - ставим минуты
    for i in range(1, 100):
        txt = num_to_text.num2text(i, female_units_min) + " "
        txt2 = num_to_text.num2text(i) + " "
        if phrase.startswith(txt2):
            set_timer_real(core, i * 60, txt)
            return

        txt3 = str(i) + " "
        if phrase.startswith(txt3):
            # print(txt,txt2)
            set_timer_real(core, i * 60, txt)
            return

    # спецкейс под одну минуту
    if (
        phrase.startswith("один ")
        or phrase.startswith("одна ")
        or phrase.startswith("одну ")
    ):
        txt = num_to_text.num2text(1, female_units_min)
        set_timer_real(core, 1 * 60, txt)
        return


def set_timer_real(core: VACore, num: int, txt: str):
    core.set_timer(num, (after_timer, txt))
    core.play_voice_assistant_speech("Ставлю таймер на " + txt)


def after_timer(core: VACore, txt: str):
    options = core.plugin_options(modname)

    for i in range(options["wavRepeatTimes"]):
        core.play_wav(options["wavPath"])
        time.sleep(0.2)

    core.play_voice_assistant_speech(txt + " прошло")
    # core.play_voice_assistant_speech("БИП! БИП! БИП! "+txt+" прошло")


if __name__ == "__main__":
    set_timer(None, "")
