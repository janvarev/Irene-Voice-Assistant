# import pyautogui
import time
import os

#from voiceassmain import play_voice_assistant_speech
from vacore import VACore
# based on EnjiRouz realization https://github.com/EnjiRouz/Voice-Assistant-App/blob/master/app.py

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Википедия (поиск)",
        "version": "1.0",
        "require_online": True,

        "commands": {
            "википедия|вики": run_wiki,
        }
    }
    return manifest

def run_wiki(core:VACore, phrase:str):
    # if core != None:
    #     core.play_voice_assistant_speech("Ищу на вики {}".format(phrase))

    import wikipediaapi
    wiki = wikipediaapi.Wikipedia("ru")

    # поиск страницы по запросу, чтение summary, открытие ссылки на страницу для получения подробной информации
    wiki_page = wiki.page(phrase)
    try:
        if wiki_page.exists():
            core.play_voice_assistant_speech("Вот что я нашла для {} в википедии".format(phrase))

            #webbrowser.get().open(wiki_page.fullurl)

            # чтение ассистентом первых двух предложений summary со страницы Wikipedia
            # (могут быть проблемы с мультиязычностью)
            core.play_voice_assistant_speech(" ".join(wiki_page.summary.split(".")[:2]))
        else:
            # открытие ссылки на поисковик в браузере в случае, если на Wikipedia не удалось найти ничего по запросу
            # play_voice_assistant_speech(translator.get(
            #     "Can't find {} on Wikipedia. But here is what I found on google").format(search_term))
            # url = "https://google.com/search?q=" + search_term
            # webbrowser.get().open(url)
            core.play_voice_assistant_speech("Не нашла {} в википедии".format(phrase))

    # поскольку все ошибки предсказать сложно, то будет произведен отлов с последующим выводом без остановки программы
    except:
        import traceback
        core.play_voice_assistant_speech("Проблемы с поиском в Википедии")

        traceback.print_exc()
        return


