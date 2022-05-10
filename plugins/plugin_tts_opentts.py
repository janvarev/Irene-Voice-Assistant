# TTS plugin for OpenTTS server (rest server from https://github.com/synesthesiam/opentts )
# author: Vladislav Janvarev



import os
import requests
import json

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

### classes from https://github.com/Aculeasis/rhvoice-rest/blob/master/example/rhvoice-rest.py
class Error(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg


class TTS:
    TTS_URL = "{}/api/tts"

    def __init__(self, text, url='http://127.0.0.1:8080', voice='anna', format_='mp3'):
        self._url = self.TTS_URL.format(url)
        self.__params = {
            'text': text,
            'voice': voice,
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
        "name": "TTS OpenTTS server",
        "version": "1.0",
        "require_online": False,

        "default_options": {
            "voiceId": "marytts:ac-irina-hsmm", # id голоса
            "urlOpenTTS": "http://127.0.0.1:5500",
        },

        "tts": {
            "opentts": (init,None,towavfile) # первая функция инициализации, вторая - говорить, третья - в wav file
                                            # если вторая - None, то используется 3-я с проигрыванием файла
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def init(core:VACore):
    url = core.plugin_options(modname)["urlOpenTTS"]
    print("Open TTS web interface: {}".format(url))
    try:
        rq = requests.get(url+"/api/voices", params={}, stream=False)
    except (requests.exceptions.HTTPError, requests.exceptions.RequestException) as e:
        #raise Error(code=1, msg=str(e))
        print("--- Error: OpenTTS seems to be unavailable ----")
        return

    #print(rq.content)
    ar = json.loads(rq.content)
    print("Available voices OpenTTS:")
    for voiceId in ar.keys():
        print("  "+voiceId+": ",ar[voiceId])

def towavfile(core:VACore, text_to_speech:str, wavfile:str):
    # simple way
    voiceid = core.plugin_options(modname)["voiceId"]
    url = core.plugin_options(modname)["urlOpenTTS"]
    #format = core.plugin_options("plugin_tts_rhvoice_rest")["format"]
    try:

        res = TTS(text=text_to_speech,url=url,voice=voiceid)

        res.save(wavfile)
    except Exception as e:
        print(e)




    return

if __name__ == '__main__':
    test = TTS(text='Привет мир! 1 2 3.',format_="wav")
    test.save('../temp/testrh.wav')
    print('test.mp3 generated!')