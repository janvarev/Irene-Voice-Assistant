# Болталка с vsegpt.
# Ключ можно получить на https://vsegpt.ru
# author: Vladislav Janvarev

import os
import openai

from vacore import VACore

import json
import os
import openai

## ------------- special code to disable SSL verify (bypass SSL errors) -------------------

import warnings
import contextlib

import requests
from urllib3.exceptions import InsecureRequestWarning

old_merge_environment_settings = requests.Session.merge_environment_settings

@contextlib.contextmanager
def no_ssl_verification():
    opened_adapters = set()

    def merge_environment_settings(self, url, proxies, stream, verify, cert):
        # Verification happens only once per connection so we need to close
        # all the opened adapters once we're done. Otherwise, the effects of
        # verify=False persist beyond the end of this context manager.
        opened_adapters.add(self.get_adapter(url))

        settings = old_merge_environment_settings(self, url, proxies, stream, verify, cert)
        settings['verify'] = False

        return settings

    requests.Session.merge_environment_settings = merge_environment_settings

    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', InsecureRequestWarning)
            yield
    finally:
        requests.Session.merge_environment_settings = old_merge_environment_settings

        for adapter in opened_adapters:
            try:
                adapter.close()
            except:
                pass

## ------------- end special code to disable SSL verify (bypass SSL errors) -------------------


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
        with no_ssl_verification():
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=self.messages,
                temperature=0.8,
                n=1,
                max_tokens=100,
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
        "name": "Болталка с ChatGPT с сохранением контекста через Vsegpt.ru",
        "version": "1.0",
        "require_online": True,
        "description": "После указания apiKey позволяет вести диалог с ChatGPT.\n"
                       "Голосовая команда: поболтаем|поговорим",

        "options_label": {
            "apiKey": "API-ключ VseGPT для доступа к ChatGPT", #
            "system": "Вводная строка, задающая характер ответов помощника.",
            "model": "ID нейросетевой модели с сайта Vsegpt",

        },

        "default_options": {
            "apiKey": "", #
            "system": "Ты - Ирина, голосовой помощник, помогающий человеку. Давай ответы кратко и по существу.",
            "model": "openai/gpt-3.5-turbo"
        },

        "commands": {
            "поболтаем|поговорим": run_start,
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
    openai.api_base = "https://api.vsegpt.ru:6070/v1"

    new_chat(core)

    if phrase == "":
        core.play_voice_assistant_speech("Да, давай!")
        core.context_set(boltalka, 20)
    else:
        boltalka(core,phrase)

def new_chat(core:VACore):
    options = core.plugin_options(modname)
    core.chatapp = ChatApp(model=options["model"], system=options["system"])  # создаем новый чат

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
