from vacore import VACore

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Открыть браузер по настраиваемой команде",
        "version": "1.0",
        "require_online": True,

        "commands": {

        },

        "default_options": {
            "cmds": {
                "ютуб|юту|ютюб": "https://www.youtube.com/results?search_query={}",
                "яндекс": "https://yandex.ru/search/?text={}",
                "главная яндекс|главное яндекс": "https://yandex.ru/",
            }
        }

    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    # модифицируем манифест, добавляя команды на основе options, сохраненных в файле
    cmds = {}
    cmdoptions = manifest["options"]["cmds"]
    print(cmdoptions)
    for cmd in cmdoptions.keys():
        cmds[cmd]  = (open_browser, cmdoptions[cmd])

    manifest["commands"] = cmds
    return manifest

def open_browser(core:VACore, phrase:str, param: str):
    core.play_voice_assistant_speech("Открываю браузер")

    import webbrowser
    url = ""
    try:
        url = param.format(phrase)
    except Exception:
        core.play_voice_assistant_speech("Ошибка при формировании ссылки")

    if url != "":
        webbrowser.get().open(url)


