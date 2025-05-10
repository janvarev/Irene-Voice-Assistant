# VoiceOver
# author: Vladislav Janvarev

import os
import logging
import re

from vacore import VACore


modname = os.path.basename(__file__)[:-3] # calculating modname
logger = logging.getLogger(__name__)


# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Озвучивание текста",
        "version": "1.3",
        "require_online": False,

        "default_options": {
            "wavBeforeGeneration": True, # звук перед генерацией из буфера обмена, которая может быть долгой
            "wavPath": 'media/timer.wav', # путь к звуковому файлу
            "useTtsEngineId2": True,  # использовать движок 2
        },

        "commands": {
            "озвучь|скажи": say,
            "буфер": say_clipboard, # озвучка буфера обмена
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def say(core:VACore, phrase:str):
    if phrase == "":
        core.say2("Нечего сказать")
        return
    phrase = prepare(phrase)
    core.say2(phrase)

def say_clipboard(core:VACore, phrase:str):
    # На Linux нужно установить в системе xclip, xsel, or wl-clipboard
    # Например в Debian
    #     sudo apt-get install xclip
    # На Windows и Mac в систему устанавливать ничего не требуется
    # На всех системах: pip install pyperclip

    try:
        import pyperclip
    except ImportError:
        logger.error("Установите pyperclip: `pip install pyperclip`")
        from sys import platform
        if platform == 'win32':
            try:
                import win32clipboard
            except ImportError:
                logger.error("... или pywin32: `pip install pywin32`")
                return
            else:
                win32clipboard.OpenClipboard()
                data = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()

                text_to_speech = str(data)
    try:
        text_to_speech = pyperclip.paste()  # получение текста из буфера обмена
    except Exception as e:
        logger.exception("Ошибка при получении текста из буфера обмена: %s", e)
        return

    options = core.plugin_options(modname)

    if options["wavBeforeGeneration"]:
        core.play_wav(options["wavPath"])

    text_to_speech = prepare(text_to_speech)
    try:
        if options["useTtsEngineId2"]:
            core.say2(text_to_speech)
        else:
            core.say(text_to_speech)
    except Exception as e:
        logger.exception("Ошибка при озвучке буфера: %s", e)

    # sentences = text_to_speech.split(".")
    # for sentence in sentences:
    #     if sentence != "":
    #         core.say2(sentence+".")


def prepare(text: str):
    """
    Подготовка текста к озвучиванию
    """
    logger.debug(f'Текст до преобразований: {text}')

    # Если в строке только кириллица и пунктуация - оставляем как есть
    if not bool(re.search(r'[^,.?!;:"() ЁА-Яа-яё]', text)):
        return text

    def replace_characters(input_string, replacement_dict):
        """
        Замена символов в строке по словарю подстановки
        """
        translation_table = str.maketrans(replacement_dict)
        return input_string.translate(translation_table)

    # Замена символов текстом
    if bool(re.search(r'["-+\-/<->@{-}№]', text)):
        # Словарь замены символов
        # 'символ': 'замена'
        # 'замена' - заменяемый текст, символ или '' для удаления символа из текста
        # Если символ в словаре отсутствует - он остаётся в тексте без изменений
        symbol_dict = {
            # ASCII
            # '!': '!' - оставлены, чтобы ничего не пропустить, можно убрать потом
            '!': '!', '"': ' двойная кавычка ', '#': ' решётка ', '$': ' доллар ', '%': ' процент ',
            '&': ' амперсанд ', "'": ' кавычка ', '(': ' левая скобка ', ')': ' правая скобка ',
            '*': ' звёздочка ', '+': ' плюс ', ',': ',', '-': ' минус ', '.': '.', '/': ' косая черта ',
            ':': ':', ';': ';', '<': 'меньше', '=': ' равно ', '>': 'больше', '?': '?', '@': ' эт ',
            '~': ' тильда ', '[': ' левая квадратная скобка ', '\\': ' обратная косая черта ',
            ']': ' правая квадратная скобка ', '^': ' циркумфлекс ', '_': ' нижнее подчеркивание ',
            '`': ' обратная кавычка ', '{': ' левая фигурная скобка ', '|': ' вертикальная черта ',
            '}': ' правая фигурная скобка ',
            # Unicode
            '№': ' номер ',
        }
        text = replace_characters(text, symbol_dict)
        text = re.sub(r'[\s]+', ' ', text)  # убрать лишние пробелы
        logger.debug(f'Текст после подстановки символов: {text}')

    if bool(re.search('a-zA-Z', text)):
        return text
    else:
        # Использовано:
        # "https://ru.stackoverflow.com/questions/1602040/Англо-русская-практическая-транскрипция-на-python"

        # Словари замены транскрипции IPA к русскоязычному фонетическому представлению.
        ipa2ru_map = {
            "p": "п", "b": "б", "t": "т", "d": "д", "k": "к", "g": "г", "m": "м", "n": "н", "ŋ": "нг", "ʧ": "ч",
            "ʤ": "дж", "f": "ф", "v": "в", "θ": "т", "ð": "з", "s": "с", "z": "з", "ʃ": "ш", "ʒ": "ж", "h": "х",
            "w": "в", "j": "й", "r": "р", "l": "л",
            # гласные
            "i": "и", "ɪ": "и", "e": "э", "ɛ": "э", "æ": "э", "ʌ": "а", "ə": "е", "u": "у", "ʊ": "у", "oʊ": "оу",
            "ɔ": "о", "ɑ": "а", "aɪ": "ай", "aʊ": "ау", "ɔɪ": "ой", "ɛr": "ё", "ər": "ё", "ɚ": "а", "ju": "ю",
            "əv": "ов", "o": "о",
            # ударения
            "ˈ": "", "ˌ": "",
            "*": "",
        }
        try:
            import eng_to_ipa as ipa
        except ImportError as e:
            logger.exception(e)
            ipa = None

        if ipa is not None:
            text = ipa.convert(text)
            logger.debug(f'Текст после преобразования латиницы в транскрипцию: {text}')

            def ipa2ru_at_pos(ipa_text: str, pos: int) -> tuple[str, int]:
                """
                Переводит символ или пару символов из строки IPA в соответствующий русский символ(ы) в данной позиции.

                Аргументы:
                    ipa_text (str): Входная строка, содержащая символы IPA.
                    pos (int): Положение в строке.

                Возвращаемое значение:
                    tuple[str, int]: Кортеж, содержащий русскую озвучку и новую позицию после перевода.
                                     Если символ(ы) в данной позиции не найден(ы) в таблице соответствий,
                                     то возвращается строка, в которой неизвестные символ(ы) обрамлены восклицательными знаками.
                                    Второй элемент кортежа содержит позицию следующего необработанного символа.
                """
                ch = ipa_text[pos]
                ch2 = ipa_text[pos: pos + 2]
                # дифтонги или сочетания фонем
                if ch2 in ipa2ru_map:
                    return ipa2ru_map[ch2], pos + 2
                # одиночные фонемы
                if ch in ipa2ru_map:
                    return ipa2ru_map[ch], pos + 1
                # ascii символы - цифры, пунктуация и т.д.
                if ord(ch) < 128:
                    return ch, pos + 1
                return f"{ch}", pos + 1

            def ipa2ru(ipa_text: str) -> str:
                """
                Преобразует транскрипцию, заданную символами IPA (международный фонетический алфавит),
                в русское фонетическое представление.

                Args:
                    ipa_text (str): Входная строка, содержащая символы IPA.

                Returns:
                    str: Полученная строка с русским фонетическим представлением.
                """
                result = ""
                pos = 0
                while pos < len(ipa_text):
                    ru_ch, pos = ipa2ru_at_pos(ipa_text, pos)
                    result += ru_ch
                return result

            text = ipa2ru(text)
            logger.info(f'Текст после всех преобразований: {text}')
            # logger.debug(f'Символы: {[f'{ch}: {ord(ch)}' for ch in text]}')
            return text
        else:
            logger.warning("Текст содержит латинские буквы, возможны ошибки в библиотеках TTS")
            logger.warning("Установите eng_to_ipa: `pip install eng_to_ipa`")
            return text
