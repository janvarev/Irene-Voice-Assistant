# ----------

from fastapi import FastAPI, HTTPException
import uvicorn
from multiprocessing import Process
from termcolor import cprint
import json

#from pydantic import BaseModel


from vacore import VACore
import time

# ------------------- main loop ------------------

webapi_options = None

core = None

try:
    with open('options/webapi.json', 'r', encoding="utf-8") as f:
        s = f.read(1000000)
        f.close()
    webapi_options = json.loads(s)
except Exception as e:
    core = VACore()
    core.init_with_plugins()
    core.init_plugin("webapi")
    cprint("Настройки созданы; пожалуйста, перезапустите этот файл", "red")
    exit(-1)




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
    core.execute_next(cmd,core.context)
    core.remoteTTS = tmpformat

app = FastAPI()
is_running = True

@app.on_event("startup")
async def startup_event():
    global core
    core = VACore()
    core.init_with_plugins()
    core.init_plugin("webapi")
    print("WEB api for VoiceAssistantCore (remote control)")


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
    tmpformat = core.remoteTTS
    core.remoteTTS = returnFormat
    core.remoteTTSResult = ""
    core.lastSay = ""
    isFound = core.run_input_str(rawtxt)
    core.remoteTTS = tmpformat

    if isFound:
        return core.remoteTTSResult
    else:
        return "NO_VA_NAME"

# Обновляет контекст на то же самое время
@app.get("/reinitContext")
async def reinitContext():
    if core.contextTimer != None:
        core.context_set(core.context,core.contextTimerLastDuration)
    return ""

# Запускает внутреннюю процедуру проверки таймеров. Должна запускаться периодически
@app.get("/updTimers")
async def updTimers():
    #core.say("аа")
    #print("upd timers")
    core._update_timers()
    return ""

# Сообщает серверу, что клиент воспроизвёл ответ и можно начать отсчёт таймера контекста
@app.get("/replyWasGiven")
async def replyWasGiven():
    if core.contextRemoteWaitForCall:
        if core.contextTimer != None:
            core.contextTimer.start()
            #print("debug - run context after webapi call")

def core_update_timers_http(runReq=True):
    if not is_running:
        return

    if runReq:
        try:
            import requests
            reqstr = "http://{0}:{1}/updTimers".format(webapi_options["host"],webapi_options["port"])
            #print(reqstr)
            r = requests.get(reqstr)
        except Exception:
            pass
    try:
        time.sleep(2)
    except:
        return
    core_update_timers_http()

@app.on_event("shutdown")
def app_shutdown():
    global is_running
    cprint("Ctrl-C pressed, exiting Irene.", "yellow")
    is_running = False



if __name__ == "__main__":



    p = Process(target=core_update_timers_http, args=(False,))
    p.start()
    uvicorn.run("runva_webapi:app", host=webapi_options["host"], port=webapi_options["port"],
                log_level=webapi_options["log_level"])