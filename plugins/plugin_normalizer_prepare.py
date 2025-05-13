# Latin text and some specsymbols normalizer plugin for russian TTS
# required library: eng_to_ipa (`pip install eng_to_ipa`)
# author: Sergey Savin aka Grayen
"""
    Подготовка текста к озвучиванию на русских моделях TTS.
Т.к. многие модели либо пропускают некоторые символы (в лучшем случае),
либо останавливаются с генерацией исключения. Производится замена слов
на латинице в транскрипцию кириллицей и замена символов словами.
    Автор не ставил цели добиться идеального произношения :)
"""
import os
import logging
import re

from vacore import VACore

modname = os.path.basename(__file__)[:-3]  # calculating modname
logger = logging.getLogger(__name__)


# функция на старте
def start(core: VACore):
    manifest = {
        "name": "Normalizer latin text and some specsymbols",
        "version": "0.2",
        "require_online": False,

        "normalizer": {
            "prepare": (init, normalize)  # первая функция инициализации, вторая - реализация нормализации
        },

        "description": "Подготовка текста к озвучиванию на русских моделях TTS.\n"
                       "Замена символов и слов на латинице в транскрипцию кириллицей\n",

        "default_options": {
            "changeNumbers": "process",
            # Заменять числа словами: "process" - заменять, "delete" - удалять, "no_process" - оставлять как есть
            "changeLatin": "process",
            # Заменять латиницу на кириллицу: "process" - заменять, "delete" - удалять, "no_process" - оставлять как есть
            "changeSymbols": r"#$%&*+-/<=>@~[\]_`{|}№",  # Символы, заменяемые словами.
            "keepSymbols": r",.?!;:() ",  # Символы, оставляемые в тексте без изменений
            "deleteUnknownSymbols": True,  # Удалять все остальные символы
        },

    }
    return manifest


def start_with_options(core: VACore, manifest: dict):
    pass


def init(core: VACore):
    pass


def normalize(core: VACore, text: str):
    """
    Подготовка текста к озвучиванию
    """
    options = core.plugin_options(modname)
    logger.debug(f'Текст до преобразований: {text}')

    # Если в строке только кириллица и пунктуация - оставляем как есть
    if not bool(re.search(r'[^,.?!;:"() ЁА-Яа-яё]', text)):
        return text

    def replace_characters(input_string, replacement_dict):
        """
        Замена символов в строке по словарю подстановки
        Ключи в словаре - только одиночные символы!
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

        symbols_to_change = options['changeSymbols']
        filtered_symbol_dict = {key: value for key, value in symbol_dict.items() if key in symbols_to_change}
        logger.debug(f'Словарь замены символов: {filtered_symbol_dict}')

        symbols_to_keep = options['keepSymbols']
        filtered_symbol_dict.update({key: key for key in symbols_to_keep})
        logger.debug(f'Словарь с сохраняемыми символами: {filtered_symbol_dict}')

        if filtered_symbol_dict:
            text = replace_characters(text, filtered_symbol_dict)
            logger.debug(f'Текст после замены символов: {text}')

        if options['deleteUnknownSymbols']:
            text = re.sub(f'[^{symbols_to_change}{symbols_to_keep}A-Za-zЁА-Яа-яё ]', '',
                          text)  # убрать все остальные символы
            logger.debug(f'Текст после удаления символов: {text}')

        text = re.sub(r'[\s]+', ' ', text)  # убрать лишние пробелы

    if bool(re.search(r'[0-9]', text)):
        if options['changeNumbers'].lower() == 'process':  # Заменяем числа словами
            text = core.all_num_to_text(text)
        elif options['changeNumbers'].lower() == 'delete':  # Удаляем числа
            text = re.sub(r'[0-9]', '', text)
        # 'no_process' оставляем как есть
        logger.debug(f'Текст после замены чисел: {text}')

    change_latin = options['changeLatin'].lower() == 'no_process'
    if (not bool(re.search('[a-zA-Z]', text)) or  # Если нет латинских букв
            change_latin):  # или не обрабатываем латиницу
        return text  # оставляем как есть
    elif change_latin == 'delete':  # Удаляем латиницу
        text = re.sub('[a-zA-Z]', '', text)
        logger.debug(f'Текст после удаления латиницы: {text}')
    else:  # 'process' Заменяем латиницу на русский текст
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

        if ipa is None:
            logger.error("Текст содержит латинские буквы, возможны ошибки в библиотеках TTS")
            logger.error("Установите eng_to_ipa: `pip install eng_to_ipa`")
            return text
        else:
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
            try:
                logger.debug(f"Символы: {[f'{ch}: {ord(ch)}' for ch in text]}")
            except Exception as e:
                logger.exception(e)
            return text
