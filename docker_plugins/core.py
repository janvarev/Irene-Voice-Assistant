# Core plugin
# author: Vladislav Janvarev

from vacore import VACore

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Core plugin",
        "version": "3.0",

        "default_options": {
            "mpcIsUse": True,
            "mpcHcPath": "C:\Program Files (x86)\K-Lite Codec Pack\MPC-HC64\mpc-hc64_nvo.exe",
            "mpcIsUseHttpRemote": False,

            "isOnline": False,
            #"ttsIndex": 0,
            "useTTSCache": False,
            "ttsEngineId": "silero_v3",
            "ttsEngineId2": "", # двиг для прямой озвучки на сервере. Если пуст - используется ttsEngineId
            "playWavEngineId": "consolewav",
            "linguaFrancaLang": "ru", # язык для библиотеки lingua-franca конвертирования чисел
            "voiceAssNames": "ирина|ирины|ирину",
            "logPolicy": "cmd", # all | cmd | none

            "replyNoCommandFound": "Извини, я не поняла",
            "replyNoCommandFoundInContext": "Не поняла...",
            "replyOnlineRequired": "Для этой команды необходим онлайн",

            "contextDefaultDuration": 10,
            "contextRemoteWaitForCall": False,

            "tempDir": "temp",
            "fuzzyThreshold": 0.5,
        },

    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    #print(manifest["options"])
    options = manifest["options"]
    #core.setup_assistant_voice(options["ttsIndex"])

    core.mpcHcPath = options["mpcHcPath"]
    core.mpcIsUse = options["mpcIsUse"]
    core.mpcIsUseHttpRemote = options["mpcIsUseHttpRemote"]
    core.isOnline = options["isOnline"]

    core.voiceAssNames = options["voiceAssNames"].split("|")
    core.ttsEngineId = options["ttsEngineId"]
    core.ttsEngineId2 = options["ttsEngineId2"]
    core.playWavEngineId = options["playWavEngineId"]
    core.logPolicy = options["logPolicy"]

    core.contextDefaultDuration = options["contextDefaultDuration"]
    core.contextRemoteWaitForCall = options["contextRemoteWaitForCall"]

    core.tmpdir = options["tempDir"]
    import os
    if not os.path.exists(core.tmpdir):
        os.mkdir(core.tmpdir)

    core.useTTSCache = options["useTTSCache"]
    core.tts_cache_dir = "tts_cache"
    if not os.path.exists(core.tts_cache_dir):
        os.mkdir(core.tts_cache_dir)
    if not os.path.exists(core.tts_cache_dir+"/"+core.ttsEngineId):
        os.mkdir(core.tts_cache_dir+"/"+core.ttsEngineId)



    import lingua_franca
    lingua_franca.load_language(options["linguaFrancaLang"])


    return manifest
