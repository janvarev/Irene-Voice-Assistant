# ----------

from fastapi import FastAPI, HTTPException
import uvicorn



#from pydantic import BaseModel


from vacore import VACore
#import time

# ------------------- main loop ------------------

core = VACore()
core.init_with_plugins()
print("WEB api for VoiceAssistantCore (remote control)")

def runCmd(cmd:str,returnFormat:str):
    tmpformat = core.remoteTTS
    core.remoteTTS = returnFormat
    core.execute_next(cmd,None)
    core.remoteTTS = tmpformat

app = FastAPI()

"""
returnFormat Варианты:
- "none" (TTS реакции будут на сервере) (звук на сервере)
- "saytxt" (сервер вернет текст, TTS будет на клиенте) (звук на клиенте)
- "saywav" (TTS на сервере, сервер отрендерит WAV и вернет клиенту, клиент его проиграет) (звук на клиенте) **наиболее универсальный для клиента**
"""

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



if __name__ == "__main__":
    uvicorn.run("runva_webapi:app", host="127.0.0.1", port=5003, log_level="info")