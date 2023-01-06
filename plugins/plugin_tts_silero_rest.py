# TTS plugin for silero engine (rest server from https://github.com/janvarev/silero_rest_service )
# author: Vladislav Janvarev

import os
import requests

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

### classes from https://github.com/Aculeasis/rhvoice-rest/blob/master/example/rhvoice-rest.py
class Error(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg


class TTS:
    TTS_URL = "{}/getwav"

    def __init__(self, text, url='http://127.0.0.1:5010', speaker='xenia', sample_rate=24000, put_yo=1, put_accent=1):
        self._url = self.TTS_URL.format(url)
        self.__params = {
            'text_to_speech': text,
            'speaker': speaker,
            'sample_rate': sample_rate,
            'put_accent': put_accent,
            'put_yo': put_yo,

        }
        self._data = None
        self._generate()

    def _generate(self):
        try:
            rq = requests.get(self._url, params=self.__params, stream=False)
        except (requests.exceptions.HTTPError, requests.exceptions.RequestException) as e:
            raise Error(code=1, msg=str(e))

        code = rq.status_code
        if code != 200:
            raise Error(code=code, msg='http code != 200')
        self._data = rq.iter_content()

    def save(self, file_path):
        if self._data is None:
            raise Exception('There\'s nothing to save')

        with open(file_path, 'wb') as f:
            for d in self._data:
                f.write(d)

        return file_path



# функция на старте
def start(core:VACore):
    manifest = {
        "name": "TTS silero (REST)",
        "version": "1.0",
        "require_online": False,

        "default_options": {
            "urlSileroRestServer": "http://127.0.0.1:5010",
            "speaker": "xenia",
            "sample_rate": 24000,
            "put_accent": True,
            "put_yo": True,
        },

        "tts": {
            "silero_rest": (init,None,towavfile) # первая функция инициализации, вторая - говорить, третья - в wav file
                                            # если вторая - None, то используется 3-я с проигрыванием файла
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def init(core:VACore):
    pass

def towavfile(core:VACore, text_to_speech:str, wavfile:str):
    # simple way
    speaker = core.plugin_options("plugin_tts_silero_rest")["speaker"]
    url = core.plugin_options("plugin_tts_silero_rest")["urlSileroRestServer"]
    sample_rate = core.plugin_options("plugin_tts_silero_rest")["sample_rate"]

    if core.plugin_options("plugin_tts_silero_rest")["put_yo"]:
        put_yo = 1
    else:
        put_yo = 0

    if core.plugin_options("plugin_tts_silero_rest")["put_accent"]:
        put_accent = 1
    else:
        put_accent = 0


    #format = core.plugin_options("plugin_tts_silero_rest")["format"]
    try:

        res = TTS(text=text_to_speech,url=url,speaker=speaker,sample_rate=sample_rate,put_yo=put_yo,put_accent=put_accent)

        res.save(wavfile)
    except Exception as e:
        print(e)




    return

if __name__ == '__main__':
    test = TTS(text='Привет мир! 1 2 3.',format_="wav")
    test.save('../temp/testrh.wav')
    print('test.mp3 generated!')