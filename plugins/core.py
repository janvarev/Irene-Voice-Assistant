# Core plugin
# author: Vladislav Janvarev
from logging import WARNING

from vacore import VACore

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Core plugin",
        "version": "4.3",
        "description": "Плагин с основными настройками Ирины.\nПосмотрите другие плагины, чтобы понять, какие команды можно использовать.",

        "options_label": {
            "mpcIsUse": "Можно ли использовать плеер MPC-HС",
            "mpcHcPath": "Путь до плеера MPC-HС",
            "mpcIsUseHttpRemote": "Можно ли использовать управление плеером MPC-HС через веб-доступ (включается в настройках плеера)",

            "isOnline": "Будут ли выполняться команды плагинов, требующие онлайн",
            # "ttsIndex": 0,
            "useTTSCache": "Кешировать озвучку текста (требует больше места на диске, может сбоить при переключении голосов)",
            "ttsEngineId": "ID основного движка озвучки. Если что-то не работает - попробуйте сменить на pyttsx, elevenlabs, vosk, vsegpt (если используете) или silero_v3 (последний требует полной установки из install - т.е. c torch)",
            "ttsEngineId2": "ID дополнительного движка озвучки. Всегда озвучивает результат на той машине, где запущена Ирина (без веб-интерфейса)",  # двиг для прямой озвучки на сервере. Если пуст - используется ttsEngineId
            "playWavEngineId": "ID движка воспроизведения аудио. Если есть проблемы - попробуйте сменить на audioplayer или sounddevice",
            "linguaFrancaLang": "Язык для библиотеки lingua-franca конвертирования чисел",  # язык для библиотеки lingua-franca конвертирования чисел
            "voiceAssNames": "Имена, по которому обращаются к помощнику через |. (Если это появится в звуковом потоке, то считается, что дальше будет голосовая команда.)",
            "logPolicy": "all|cmd|none . Когда распознается речь с микрофона - выводить в консоль всегда | только, если является командой | никогда",  # all | cmd | none

            "replyNoCommandFound": "ответ при непонимании",
            "replyNoCommandFoundInContext": "ответ при непонимании в состоянии контекста",
            "replyOnlineRequired": "ответ при вызове в оффлайн функции плагина, требующего онлайн",

            "contextDefaultDuration": "Время в секундах, пока Ирина находится в контексте (контекст используется в непрерывном чате, играх и пр.; в контексте не надо использовать слово Ирина)",
            "contextRemoteWaitForCall": "(ПРО) При использовании WEB-API - ждать ли команды от клиента, что звук уже проигрался?",

            "tempDir": "адрес директории для временных файлов",
            "fuzzyThreshold": "(ПРО) Порог уверенности при использовании нечеткого распознавания команд",

            "voiceAssNameRunCmd": "Словарь сопоставлений. При нахождении имени помощника, добавляет префикс к распознанной фразе",

            "console_logging": "Выводить ли в консоль логи",
            "console_logging_level": "Уровень логирования консоли",
            "file_logging": "Выводить ли в лог-файл логи",
            "file_logging_level": "Уровень логирования лог-файла",
            "log_file_name": "Имя лог-файла",
        },

        "default_options": {
            "mpcIsUse": True,
            "mpcHcPath": r"C:\Program Files (x86)\K-Lite Codec Pack\MPC-HC64\mpc-hc64_nvo.exe",
            "mpcIsUseHttpRemote": False,

            "isOnline": True,
            #"ttsIndex": 0,
            "useTTSCache": False,
            "ttsEngineId": "pyttsx",
            "ttsEngineId2": "", # двиг для прямой озвучки на сервере. Если пуст - используется ttsEngineId
            "playWavEngineId": "audioplayer",
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

            "voiceAssNameRunCmd": {
                "альбина": "чатгпт"
            },

            "console_logging": False,  # Вывод логов в консоль
            "console_logging_level": "WARNING",  # Записываются в лог сообщения с уровнем равным или выше этого уровня: NOTSET | DEBUG | INFO | WARNING | ERROR | CRITICAL
            "file_logging": False,  # Вывод в лог-файл
            "file_logging_level": "DEBUG",  # NOTSET | DEBUG | INFO | WARNING | ERROR | CRITICAL
            "log_file_name": "log.txt",  # имя лог-файла
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
    core.voiceAssNameRunCmd = options["voiceAssNameRunCmd"]
    print(core.voiceAssNameRunCmd)
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

    # Логирование
    core.console_logging = options["console_logging"]
    core.console_logging_level = options["console_logging_level"]
    core.file_logging = options["file_logging"]
    core.file_logging_level = options["file_logging_level"]
    core.log_file_name = options["log_file_name"]
    if core.console_logging or core.file_logging:
        import logging  # Если не создать логгер здесь, то он всё равно будет создан при первом вызове из библиотек или подмодулей
        root_logger = logging.getLogger()  # Получить объект логгера, если он уже создан или создать новый корневой...
        for handler in root_logger.handlers[:]:  # ... т.к. запуск не из самого верхнего модуля
            root_logger.removeHandler(handler)  # Удалить созданные обработчики, если они есть
        root_logger.setLevel(min(core.console_logging_level, core.file_logging_level))  # Установить минимальный уровень, ниже которого события не обрабатываются
        if core.console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(core.console_logging_level)
            console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        if core.file_logging:
            file_handler = logging.FileHandler(core.log_file_name)
            file_handler.setLevel(core.file_logging_level)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        logger = logging.getLogger(__name__)  # Создать логгер для этого модуля
        if core.console_logging:
            logger.info("Console logging enabled")
        if core.file_logging:
            logger.info("File logging enabled")


    return manifest
