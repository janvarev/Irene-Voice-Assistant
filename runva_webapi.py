# ----------

from fastapi import FastAPI, HTTPException
import uvicorn



#from pydantic import BaseModel


from vacore import VACore
#import time

# ------------------- main loop ------------------

core = VACore()
core.init_with_plugins()
core.init_plugin("webapi")
webapi_options = core.plugin_options("webapi")
print("WEB api for VoiceAssistantCore (remote control)")
# здесь двойная инициализация - на импорте, и на запуске сервера
# не очень хорошо, но это нужно, чтобы получить webapi_options = core.plugin_options("webapi")

"""
returnFormat Варианты:
- "none" (TTS реакции будут на сервере) (звук на сервере)
- "saytxt" (сервер вернет текст, TTS будет на клиенте) (звук на клиенте)
- "saywav" (TTS на сервере, сервер отрендерит WAV и вернет клиенту, клиент его проиграет) (звук на клиенте) **наиболее универсальный для клиента**
"""
def runCmd(cmd:str,returnFormat:str):
    if core.logPolicy == "cmd" or core.logPolicy == "all":
        print("Running cmd: ",cmd)

    tmpformat = core.remoteTTS
    core.remoteTTS = returnFormat
    core.remoteTTSResult = ""
    core.lastSay = ""
    core.execute_next(cmd,None)
    core.remoteTTS = tmpformat

app = FastAPI()


# рендерит текст в wav
@app.get("/ttsWav")
async def ttsWav(text:str):
    #runCmd(cmd,returnFormat)
    tmpformat = core.remoteTTS
    core.remoteTTS = "saywav"
    core.play_voice_assistant_speech(text)
    core.remoteTTS = tmpformat
    return core.remoteTTSResult


# выполняет команду Ирины
# Например: привет, погода.
@app.get("/sendTxtCmd")
async def sendSimpleTxtCmd(cmd:str,returnFormat:str = "none"):
    runCmd(cmd,returnFormat)
    return core.remoteTTSResult

# Посылает распознанный текстовый ввод. Если в нем есть имя помощника, выполняется команда.
# Пример: ирина погода, раз два
@app.get("/sendRawTxt")
async def sendRawTxt(rawtxt:str,returnFormat:str = "none"):
    voice_input = rawtxt.split(" ")

    isFound = False
    for ind in range(len(voice_input)):
        callname = voice_input[ind]
        if callname in core.voiceAssNames: # найдено имя ассистента
            isFound = True
            if core.logPolicy == "cmd":
                print("Input (cmd): ",rawtxt)

            command_options = " ".join([str(input_part) for input_part in voice_input[(ind+1):len(voice_input)]])
            runCmd(command_options, returnFormat)
            break

    if isFound:
        return core.remoteTTSResult
    else:
        return "NO_VA_NAME"


# simple threading for timer
from threading import Thread, Event

class MyThread(Thread):
    def __init__(self, event):
        Thread.__init__(self)
        self.stopped = event

    def run(self):
        while not self.stopped.wait(0.5):
            core._update_timers()

if __name__ != "__main__": # must run only in web
    stopFlag = Event()
    thread = MyThread(stopFlag)
    thread.start()
    # this will stop the timer
    #stopFlag.set()

if __name__ == "__main__":
    uvicorn.run("runva_webapi:app", host=webapi_options["host"], port=webapi_options["port"],
                log_level=webapi_options["log_level"])