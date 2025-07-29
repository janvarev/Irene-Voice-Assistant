# Болталка с vsegpt.
# Ключ можно получить на https://vsegpt.ru
# author: Vladislav Janvarev

from vacore import VACore

import json
import os
import openai

# ---------- from https://github.com/stancsz/chatgpt ----------
class ChatApp:
    def __init__(self, model="gpt-3.5-turbo", load_file='', system=''):
        # Setting the API key to use the OpenAI API
        self.model = model
        self.messages = []
        if system != '':
            self.messages.append({"role": "system", "content" : system})
        if load_file != '':
            self.load(load_file)

    def chat(self, message):
        if message == "exit":
            self.save()
            os._exit(1)
        elif message == "save":
            self.save()
            return "(saved)"
        self.messages.append({"role": "user", "content": message})

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=self.messages,
            temperature=0.8,
            n=1,
            max_tokens=200,
        )
        self.messages.append({"role": "assistant", "content": response["choices"][0]["message"].content})
        return response["choices"][0]["message"]
    def save(self):
        try:
            import time
            import re
            import json
            ts = time.time()
            json_object = json.dumps(self.messages, indent=4)
            filename_prefix=self.messages[0]['content'][0:30]
            filename_prefix = re.sub('[^0-9a-zA-Z]+', '-', f"{filename_prefix}_{ts}")
            with open(f"models/chat_model_{filename_prefix}.json", "w") as outfile:
                outfile.write(json_object)
        except:
            os._exit(1)

    def load(self, load_file):
        with open(load_file) as f:
            data = json.load(f)
            self.messages = data

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Болталка с ChatGPT с сохранением контекста через Vsegpt.ru или другой OpenAI сервер",
        "version": "3.2",
        "require_online": True,
        "description": "После указания apiKey позволяет вести диалог с ChatGPT.\n"
                       "Голосовая команда: поболтаем|поговорим (для обычной модели с чатом), справка (для точных фактов)",

        "options_label": {
            "apiKey": "API-ключ VseGPT для доступа к ChatGPT", #
            "apiBaseUrl": "URL для OpenAI (нужен, если вы связываетесь с другим сервером, эмулирующим OpenAI)",  #
            "system": "Вводная строка, задающая характер ответов помощника.",
            "model": "ID нейросетевой модели с сайта Vsegpt",
            "model_spravka": "ID нейросетевой модели с сайта Vsegpt для справок (точных фактов)",
            "tts_model": "TTS модель с VseGPT",
            "tts_voice": "Голос для модели",

        },

        "default_options": {
            "apiKey": "", #
            "apiBaseUrl": "https://api.vsegpt.ru/v1",  #
            "system": "Ты - Ирина, голосовой помощник, помогающий человеку. Давай ответы кратко и по существу.",
            "model": "openai/gpt-4o-mini",
            "model_spravka": "perplexity/latest-large-online",
            "tts_model": "tts-openai/tts-1",
            "tts_voice": "nova",
            "tts_response_format": "mp3",
            "prompt_tpl_spravka": "Вопрос: {0}. Ответь на русском языке максимально кратко - только запрошенные данные. ",
        },

        "commands": {
            "поболтаем|поговорим": run_start,
            "справка": run_start_spravka,
        },

        "tts": {
            "vsegpt": (init, None, towavfile)  # первая функция инициализации, вторая - говорить, третья - в wav file
            # если вторая - None, то используется 3-я с проигрыванием файла
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def run_start(core:VACore, phrase:str):

    options = core.plugin_options(modname)

    if options["apiKey"] == "":
        core.play_voice_assistant_speech("Нужен ключ апи для доступа к всегепете точка ру")
        return

    openai.api_key = options["apiKey"]
    openai.api_base = options["apiBaseUrl"]

    new_chat(core)

    if phrase == "":
        core.play_voice_assistant_speech("Да, давай!")
        core.context_set(boltalka, 20)
    else:
        boltalka(core,phrase)

def new_chat(core:VACore):
    options = core.plugin_options(modname)
    core.chatapp = ChatApp(model=options["model"], system=options["system"])  # создаем новый чат

def new_chat_spravka(core:VACore):
    options = core.plugin_options(modname)
    core.chatapp = ChatApp(model=options["model_spravka"])  # создаем новый чат для perplexity


def boltalka(core:VACore, phrase:str):
    if phrase == "отмена" or phrase == "пока":
        core.play_voice_assistant_speech("Пока!")
        return

    if phrase == "новый диалог" or phrase == "новые диалог":
        new_chat(core)
        core.play_voice_assistant_speech("Начинаю новый диалог")
        core.context_set(boltalka, 20)
        return

    try:
        # print("-", phrase)
        response = core.chatapp.chat(phrase) #generate_response(phrase)
        # print(response)
        # decoded_value = response["content"].encode().decode('utf-8')
        # print("-", decoded_value)
        core.say(response["content"])
        core.context_set(boltalka, 20)

    except:
        import traceback
        traceback.print_exc()
        core.play_voice_assistant_speech("Проблемы с доступом к апи. Посмотрите логи")

        return

def run_start_spravka(core:VACore, phrase:str):

    options = core.plugin_options(modname)

    if options["apiKey"] == "":
        core.play_voice_assistant_speech("Нужен ключ апи для доступа к всегепете точка ру")
        return

    openai.api_key = options["apiKey"]
    openai.api_base = options["apiBaseUrl"]

    new_chat_spravka(core)

    if phrase == "":
        core.play_voice_assistant_speech("Задайте вопрос")
        core.context_set(boltalka_spravka, 20)
    else:
        boltalka_spravka(core,phrase)

def boltalka_spravka(core:VACore, phrase:str):
    options = core.plugin_options(modname)
    if phrase == "отмена" or phrase == "пока":
        core.play_voice_assistant_speech("Пока!")
        return

    try:
        # print("-", phrase)
        prompt = str(options.get("prompt_tpl_spravka")).format(phrase);
        print('Запрос:',prompt)
        response = core.chatapp.chat(prompt) #generate_response(phrase)
        # print(response)
        # decoded_value = response["content"].encode().decode('utf-8')
        # print("-", decoded_value)
        core.say(response["content"])
        # core.context_set(boltalka, 20)

    except:
        import traceback
        traceback.print_exc()
        core.play_voice_assistant_speech("Проблемы с доступом к апи. Посмотрите логи")

        return

# TTS
def init(core:VACore):
    pass

def towavfile(core:VACore, text_to_speech:str,wavfile:str):
    """
    Проигрывание речи ответов голосового ассистента (без сохранения аудио)
    :param text_to_speech: текст, который нужно преобразовать в речь
    """
    options = core.plugin_options(modname)

    if options["apiKey"] == "":
        core.play_voice_assistant_speech("Нужен ключ апи для доступа к всегепете точка ру")
        return


    import requests
    import json

    headers = {
            "Authorization": f"Bearer {options['apiKey']}",
            "Content-Type": "application/json",
        }

    # adding header for VseGPT
    if str(options["apiBaseUrl"]).startswith("https://api.vsegpt.ru"):
        headers["X-Title"] = "Irene VA"

    response = requests.post(
        url=options["apiBaseUrl"]+"/audio/speech",
        headers=headers,
        data=json.dumps({
            "model": options['tts_model'],
            "voice": options['tts_voice'],
            "input": text_to_speech,
            "response_format": options['tts_response_format'],
        }, ensure_ascii=True)
    )

    if response.status_code == 200:
        with open(wavfile, "wb") as wavfile:
            wavfile.write(response.content)
    else:
        print("Не могу связаться с сервером", response.status_code, response.text)