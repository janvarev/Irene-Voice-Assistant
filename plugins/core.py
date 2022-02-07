# Core plugin
# author: Vladislav Janvarev

from vacore import VACore


# функция на старте
def start(core: VACore):
    manifest = {
        "name": "Core plugin",
        "version": "1.9",
        "default_options": {
            "mpcIsUse": True,
            "mpcHcPath": "C:\Program Files (x86)\K-Lite Codec Pack\MPC-HC64\mpc-hc64_nvo.exe",
            "mpcIsUseHttpRemote": False,
            "isOnline": False,
            # "ttsIndex": 0,
            "ttsEngineId": "pyttsx",
            "voiceAssNames": "ирина|ирины|ирину",
            "logPolicy": "cmd",  # all | cmd | none
            "replyNoCommandFound": "Извини, я не поняла",
            "replyOnlineRequired": "Для этой команды необходим онлайн",
            "tempDir": "temp",
        },
    }
    return manifest


def start_with_options(core: VACore, manifest: dict):
    # print(manifest["options"])
    options = manifest["options"]
    # core.setup_assistant_voice(options["ttsIndex"])

    core.mpcHcPath = options["mpcHcPath"]
    core.mpcIsUse = options["mpcIsUse"]
    core.mpcIsUseHttpRemote = options["mpcIsUseHttpRemote"]
    core.isOnline = options["isOnline"]

    core.voiceAssNames = options["voiceAssNames"].split("|")
    core.ttsEngineId = options["ttsEngineId"]
    core.logPolicy = options["logPolicy"]

    core.tmpdir = options["tempDir"]
    import os

    if not os.path.exists(core.tmpdir):
        os.mkdir(core.tmpdir)

    return manifest
