# TTS plugin for Luna Translator with enabled HTTP server
# Luna Translator provide fast access to such corporate TTS like: GoogleTTS, EdgeTTS etc. via single interface
# Now tested with Google TTS
# https://github.com/HIllya51/LunaTranslator
# https://docs.lunatranslator.org/ru/apiservice.html
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
    # TTS_URL = "{}/say"

    def __init__(self, text, url='http://127.0.0.1:8080', voice='anna', format_='mp3'):
        self._url = url
        self.__params = {
            'text': text,
            #'voice': voice,
            #'format': format_
        }
        self._data = None
        self._generate()

    def _generate(self):
        # print(self._url)
        try:
            rq = requests.get(self._url, params=self.__params, stream=False)
        except (requests.exceptions.HTTPError, requests.exceptions.RequestException) as e:
            raise Error(code=1, msg=str(e))

        code = rq.status_code
        if code != 200:
            raise Error(code=code, msg='http code != 200')
        # print(rq.status_code, rq.content)
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
        "name": "TTS Luna Translator (REST)",
        "version": "1.1",
        "require_online": False,

        "default_options": {
            "urlRHVoiceRestServer": "http://127.0.0.1:2333/api/tts",
        },

        "tts": {
            "lunatranslator_rest": (init,None,towavfile) # первая функция инициализации, вторая - говорить, третья - в wav file
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
    # voiceid = core.plugin_options(modname)["voiceId"]
    url = core.plugin_options(modname)["urlRHVoiceRestServer"]
    # format = core.plugin_options(modname)["format"]

    # print("lunatranslator call")
    try:

        res = TTS(text=text_to_speech,url=url)

        res.save(wavfile)
    except Exception as e:
        print(e)




    return

if __name__ == '__main__':
    test = TTS(text='Привет мир! 1 2 3.',format_="wav")
    test.save('../temp/testrh.wav')
    print('test.mp3 generated!')