# ----------

from fastapi import FastAPI, HTTPException
import uvicorn
from multiprocessing import Process
from termcolor import cprint
import json
from starlette.websockets import WebSocket

try:
    from fastapi_utils.tasks import repeat_every
except Exception as e:
    cprint("Пожалуйста, установите fastapi-utils: pip install fastapi-utils","red")
    exit(-1)
#from pydantic import BaseModel


from vacore import VACore
import time

# ------------------- main loop ------------------

webapi_options = None

core = None
model = None # vosk model
#rec = None # vosk recognizer

# --------------- loading options ----------

# move options from old file
import os
if not os.path.exists('runva_webapi.json'):
    if os.path.exists('options/webapi.json'):
        os.rename('options/webapi.json','runva_webapi.json')

# loading options
from jaa import load_options

default_options={
    "host": "127.0.0.1",
    "port": 5003,
    "log_level": "info",
    "use_ssl": False
}
webapi_options = load_options(py_file=__file__,default_options=default_options)
use_ssl = webapi_options["use_ssl"]

# try:
#     with open('options/webapi.json', 'r', encoding="utf-8") as f:
#         s = f.read(1000000)
#         f.close()
#     webapi_options = json.loads(s)
#     use_ssl = webapi_options["use_ssl"]
# except Exception as e:
#     core = VACore()
#     core.init_with_plugins()
#     core.init_plugin("webapi")
#     cprint("Настройки созданы; пожалуйста, перезапустите этот файл", "red")
#     exit(-1)




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

from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

app.mount("/webapi_client", StaticFiles(directory="webapi_client", html = True), name="webapi_client")

app.mount("/mic_client", StaticFiles(directory="mic_client", html = True), name="mic_client")

@app.websocket("/wsmic")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    if model != None:
        from vosk import KaldiRecognizer
        rec = KaldiRecognizer(model, 48000)
        print("New WebSocket microphone recognition")
        while True:
            data = await websocket.receive_bytes()
            r = process_chunk(rec,data)
            await websocket.send_text(r)
    else:
        print("Can't accept WebSocket microphone recognition - no Model (seems to be no VOSK at startup)")

def process_chunk(rec,message):
    # with open('temp/asr_server_test.wav', 'wb') as the_file:
    #     the_file.write(message)

    if message == '{"eof" : 1}':
        return rec.FinalResult()
    elif rec.AcceptWaveform(message):
        res2 = "{}"
        res = rec.Result()
        #print("Result:",res)
        resj = json.loads(res)
        if "text" in resj:
            voice_input_str = resj["text"]
            #print(restext)
            import requests

            if voice_input_str != "" and voice_input_str != None:
                print(voice_input_str)
                #ttsFormatList = ["saytxt"]
                #res2 = sendRawTxtOrig(voice_input_str,"none,saytxt")
                res2 = sendRawTxtOrig(voice_input_str, "saytxt,saywav")
                # saywav not supported due to bytes serialization???


                if res2 != "NO_VA_NAME":
                    res3:dict = res2
                    if res3.get("wav_base64") is not None: # converting bytes to str
                        res3["wav_base64"] = res2["wav_base64"].decode("utf-8")
                    res2 = json.dumps(res3)
                else:
                    res2 = "{}"

        else:
            #print("2",rec.PartialResult())
            pass

        return res2
    else:
        res = rec.PartialResult()
        #print("Part Result:",res)
        return rec.PartialResult()

@app.on_event("startup")
async def startup_event():
    global core
    core = VACore()
    core.init_with_plugins()
    print("WEB api for VoiceAssistantCore (remote control)")

    url = ""
    if webapi_options["use_ssl"]:
        url = "https://{0}:{1}/".format("localhost",webapi_options["port"])
    else:
        url = "http://{0}:{1}/".format("localhost",webapi_options["port"])

    print("Web client URL (VOSK in browser): ", url+"webapi_client/")
    print("Mic client URL (experimental, sends WAV bytes to server): ", url+"mic_client/")

    try:
        import vosk
        from vosk import Model, SpkModel, KaldiRecognizer
        global model
        model = Model("model")
    except Exception as e:
        print("Can't init VOSK - no websocket speech recognition in WEBAPI. Can be skipped")
        import traceback
        traceback.print_exc()





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
    return sendRawTxtOrig(rawtxt,returnFormat)

def sendRawTxtOrig(rawtxt:str,returnFormat:str = "none"):
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
    return
    time.sleep(5) # small sleep before start
    while is_running:
        try:
            import requests
            if webapi_options["use_ssl"]:
                reqstr = "https://{0}:{1}/updTimers".format(webapi_options["host"],webapi_options["port"])
            else:
                reqstr = "http://{0}:{1}/updTimers".format(webapi_options["host"],webapi_options["port"])
            #print(reqstr)
            r = requests.get(reqstr,verify=False)
        except Exception:
            pass

        try:
            time.sleep(2)
        except:
            return

    return


@app.on_event("shutdown")
def app_shutdown():
    global is_running
    cprint("Ctrl-C pressed, exiting Irene.", "yellow")
    is_running = False

@app.on_event("startup")
@repeat_every(seconds=2)
async def app_timers():
    if core != None:
        #print("update timers")
        core._update_timers()

if __name__ == "__main__":



    # p = Process(target=core_update_timers_http, args=(False,))
    # p.start()
    if webapi_options["use_ssl"]:
        uvicorn.run("runva_webapi:app",
                    host=webapi_options["host"], port=webapi_options["port"],
                    ssl_keyfile="localhost.key",
                    ssl_certfile="localhost.crt",
                    log_level=webapi_options["log_level"])
    else:
        uvicorn.run("runva_webapi:app",
                    host=webapi_options["host"], port=webapi_options["port"],
                    log_level=webapi_options["log_level"])