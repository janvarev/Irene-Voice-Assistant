#
# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from lingua_franca.lang.parse_common import is_numeric, look_for_fractions, \
    invert_dict, ReplaceableNumber, partition_list, tokenize, Token, Normalizer
from lingua_franca.lang.common_data_ru import _NUM_STRING_RU, \
    _LONG_ORDINAL_RU, _LONG_SCALE_RU, _SHORT_SCALE_RU, _SHORT_ORDINAL_RU, \
    _FRACTION_STRING_RU, _MONTHS_CONVERSION, _MONTHS_RU, _TIME_UNITS_CONVERSION, \
    _ORDINAL_BASE_RU

import re
import json
from lingua_franca import resolve_resource_file
from lingua_franca.time import now_local


def generate_plurals_ru(originals):
    """
    Return a new set or dict containing the plural form of the original values,

    In English this means all with 's' appended to them.

    Args:
        originals set(str) or dict(str, any): values to pluralize

    Returns:
        set(str) or dict(str, any)

    """
    suffixes = ["а", "ах", "ам", "ами", "ные", "ный", "ов", "ом", "ы"]
    if isinstance(originals, dict):
        return {key + suffix: value for key, value in originals.items() for suffix in suffixes}
    return {value + suffix for value in originals for suffix in suffixes}


# negate next number (-2 = 0 - 2)
_NEGATIVES = {"минус"}

# sum the next number (twenty two = 20 + 2)
_SUMS = {'двадцать', '20', 'тридцать', '30', 'сорок', '40', 'пятьдесят', '50',
         'шестьдесят', '60', 'семьдесят', '70', 'восемьдесят', '80', 'девяносто', '90',
         'сто', '100', 'двести', '200', 'триста', '300', 'четыреста', '400',
         'пятьсот', '500', 'шестьсот', '600', 'семьсот', '700', 'восемьсот', '800',
         'девятьсот', '900'}

_MULTIPLIES_LONG_SCALE_RU = set(_LONG_SCALE_RU.values()) | \
                            generate_plurals_ru(_LONG_SCALE_RU.values())

_MULTIPLIES_SHORT_SCALE_RU = set(_SHORT_SCALE_RU.values()) | \
                             generate_plurals_ru(_SHORT_SCALE_RU.values())

# split sentence parse separately and sum ( 2 and a half = 2 + 0.5 )
_FRACTION_MARKER = {"и", "с", " "}

# decimal marker ( 1 point 5 = 1 + 0.5)
_DECIMAL_MARKER = {"целая", "целых", "точка", "запятая"}

_STRING_NUM_RU = invert_dict(_NUM_STRING_RU)
_STRING_NUM_RU.update({
    "тысяч": 1e3,
})
_STRING_NUM_RU.update(generate_plurals_ru(_STRING_NUM_RU))
_STRING_NUM_RU.update({
    "четверти": 0.25,
    "четвёртая": 0.25,
    "четвёртых": 0.25,
    "третья": 1 / 3,
    "третяя": 1 / 3,
    "вторая": 0.5,
    "вторых": 0.5,
    "половина": 0.5,
    "половиной": 0.5,
    "пол": 0.5,
    "одна": 1,
    "двойка": 2,
    "двое": 2,
    "пара": 2,
    "сот": 100,
    "сотен": 100,
    "сотни": 100,
    "сотня": 100,
})

_WORDS_NEXT_RU = [
    "будущая", "будущее", "будущей", "будущий", "будущим", "будущую",
    "новая", "новое", "новой", "новый", "новым",
    "следующая", "следующее", "следующей", "следующем", "следующий", "следующую",
]
_WORDS_PREV_RU = [
    "предыдущая", "предыдущем", "предыдущей", "предыдущий", "предыдущим", "предыдущую",
    "прошедшая", "прошедшем", "прошедшей", "прошедший", "прошедшим", "прошедшую",
    "прошлая", "прошлой", "прошлом", "прошлую", "прошлый", "прошлым",
    "том", "тот",
]
_WORDS_CURRENT_RU = [
    "данная", "данное", "данном", "данный",
    "настойщая", "настоящее", "настойщем", "настойщем", "настойщий",
    "нынешняя", "нынешнее", "нынешней", "нынешнем", "нынешний",
    "текущая", "текущее", "текущей", "текущем", "текущий",
    "это", "этим", "этой", "этом", "этот", "эту",
]
_WORDS_NOW_RU = [
    "теперь",
    "сейчас",
]
_WORDS_MORNING_RU = ["утро", "утром"]
_WORDS_DAY_RU = ["днём"]
_WORDS_EVENING_RU = ["вечер", "вечером"]
_WORDS_NIGHT_RU = ["ночь", "ночью"]

_STRING_SHORT_ORDINAL_RU = invert_dict(_SHORT_ORDINAL_RU)
_STRING_LONG_ORDINAL_RU = invert_dict(_LONG_ORDINAL_RU)


def _convert_words_to_numbers_ru(text, short_scale=True, ordinals=False):
    """
    Convert words in a string into their equivalent numbers.
    Args:
        text str:
        short_scale boolean: True if short scale numbers should be used.
        ordinals boolean: True if ordinals (e.g. first, second, third) should
                          be parsed to their number values (1, 2, 3...)

    Returns:
        str
        The original text, with numbers subbed in where appropriate.

    """
    text = text.lower()
    tokens = tokenize(text)
    numbers_to_replace = \
        _extract_numbers_with_text_ru(tokens, short_scale, ordinals)
    numbers_to_replace.sort(key=lambda number: number.start_index)

    results = []
    for token in tokens:
        if not numbers_to_replace or \
                token.index < numbers_to_replace[0].start_index:
            results.append(token.word)
        else:
            if numbers_to_replace and \
                    token.index == numbers_to_replace[0].start_index:
                results.append(str(numbers_to_replace[0].value))
            if numbers_to_replace and \
                    token.index == numbers_to_replace[0].end_index:
                numbers_to_replace.pop(0)

    return ' '.join(results)


def _extract_numbers_with_text_ru(tokens, short_scale=True,
                                  ordinals=False, fractional_numbers=True):
    """
    Extract all numbers from a list of Tokens, with the words that
    represent them.

    Args:
        [Token]: The tokens to parse.
        short_scale bool: True if short scale numbers should be used, False for
                          long scale. True by default.
        ordinals bool: True if ordinal words (first, second, third, etc) should
                       be parsed.
        fractional_numbers bool: True if we should look for fractions and
                                 decimals.

    Returns:
        [ReplaceableNumber]: A list of tuples, each containing a number and a
                         string.

    """
    placeholder = "<placeholder>"  # inserted to maintain correct indices
    results = []
    while True:
        to_replace = \
            _extract_number_with_text_ru(tokens, short_scale,
                                         ordinals, fractional_numbers)

        if not to_replace:
            break

        results.append(to_replace)

        tokens = [
            t if not
            to_replace.start_index <= t.index <= to_replace.end_index
            else
            Token(placeholder, t.index) for t in tokens
        ]
    results.sort(key=lambda n: n.start_index)
    return results


def _extract_number_with_text_ru(tokens, short_scale=True,
                                 ordinals=False, fractional_numbers=True):
    """
    This function extracts a number from a list of Tokens.

    Args:
        tokens str: the string to normalize
        short_scale (bool): use short scale if True, long scale if False
        ordinals (bool): consider ordinal numbers, third=3 instead of 1/3
        fractional_numbers (bool): True if we should look for fractions and
                                   decimals.
    Returns:
        ReplaceableNumber

    """
    number, tokens = \
        _extract_number_with_text_ru_helper(tokens, short_scale,
                                            ordinals, fractional_numbers)
    return ReplaceableNumber(number, tokens)


def _extract_number_with_text_ru_helper(tokens,
                                        short_scale=True, ordinals=False,
                                        fractional_numbers=True):
    """
    Helper for _extract_number_with_text_en.

    This contains the real logic for parsing, but produces
    a result that needs a little cleaning (specific, it may
    contain leading articles that can be trimmed off).

    Args:
        tokens [Token]:
        short_scale boolean:
        ordinals boolean:
        fractional_numbers boolean:

    Returns:
        int or float, [Tokens]

    """
    if fractional_numbers:
        fraction, fraction_text = \
            _extract_fraction_with_text_ru(tokens, short_scale, ordinals)
        if fraction:
            return fraction, fraction_text

        decimal, decimal_text = \
            _extract_decimal_with_text_ru(tokens, short_scale, ordinals)
        if decimal:
            return decimal, decimal_text

    return _extract_whole_number_with_text_ru(tokens, short_scale, ordinals)


def _extract_fraction_with_text_ru(tokens, short_scale, ordinals):
    """
    Extract fraction numbers from a string.

    This function handles text such as '2 and 3/4'. Note that "one half" or
    similar will be parsed by the whole number function.

    Args:
        tokens [Token]: words and their indexes in the original string.
        short_scale boolean:
        ordinals boolean:

    Returns:
        (int or float, [Token])
        The value found, and the list of relevant tokens.
        (None, None) if no fraction value is found.

    """
    for c in _FRACTION_MARKER:
        partitions = partition_list(tokens, lambda t: t.word == c)

        if len(partitions) == 3:
            numbers1 = \
                _extract_numbers_with_text_ru(partitions[0], short_scale,
                                              ordinals, fractional_numbers=False)
            numbers2 = \
                _extract_numbers_with_text_ru(partitions[2], short_scale,
                                              ordinals, fractional_numbers=True)

            if not numbers1 or not numbers2:
                return None, None

            # ensure first is not a fraction and second is a fraction
            num1 = numbers1[-1]
            num2 = numbers2[0]
            if num1.value >= 1 and 0 < num2.value < 1:
                return num1.value + num2.value, \
                       num1.tokens + partitions[1] + num2.tokens

    return None, None


def _extract_decimal_with_text_ru(tokens, short_scale, ordinals):
    """
    Extract decimal numbers from a string.

    This function handles text such as '2 point 5'.

    Notes:
        While this is a helper for extract_number_xx, it also depends on
        extract_number_xx, to parse out the components of the decimal.

        This does not currently handle things like:
            number dot number number number

    Args:
        tokens [Token]: The text to parse.
        short_scale boolean:
        ordinals boolean:

    Returns:
        (float, [Token])
        The value found and relevant tokens.
        (None, None) if no decimal value is found.

    """
    for c in _DECIMAL_MARKER:
        partitions = partition_list(tokens, lambda t: t.word == c)

        if len(partitions) == 3:
            numbers1 = \
                _extract_numbers_with_text_ru(partitions[0], short_scale,
                                              ordinals, fractional_numbers=False)
            numbers2 = \
                _extract_numbers_with_text_ru(partitions[2], short_scale,
                                              ordinals, fractional_numbers=False)

            if not numbers1 or not numbers2:
                return None, None

            number = numbers1[-1]
            decimal = numbers2[0]

            # TODO handle number dot number number number
            if "." not in str(decimal.text):
                return number.value + float('0.' + str(decimal.value)), \
                       number.tokens + partitions[1] + decimal.tokens
    return None, None


def _extract_whole_number_with_text_ru(tokens, short_scale, ordinals):
    """
    Handle numbers not handled by the decimal or fraction functions. This is
    generally whole numbers. Note that phrases such as "one half" will be
    handled by this function, while "one and a half" are handled by the
    fraction function.

    Args:
        tokens [Token]:
        short_scale boolean:
        ordinals boolean:

    Returns:
        int or float, [Tokens]
        The value parsed, and tokens that it corresponds to.

    """
    multiplies, string_num_ordinal, string_num_scale = \
        _initialize_number_data(short_scale)

    number_words = []  # type: [Token]
    val = False
    prev_val = None
    next_val = None
    to_sum = []
    for idx, token in enumerate(tokens):
        current_val = None
        if next_val:
            next_val = None
            continue

        word = token.word
        if word in word in _NEGATIVES:
            number_words.append(token)
            continue

        prev_word = tokens[idx - 1].word if idx > 0 else ""
        next_word = tokens[idx + 1].word if idx + 1 < len(tokens) else ""

        # In Russian (?) we do no use suffix (1st,2nd,..) but use point instead (1.,2.,..)
        if is_numeric(word[:-1]) and \
                (word.endswith(".")):
            # explicit ordinals, 1st, 2nd, 3rd, 4th.... Nth
            word = word[:-1]

            # handle nth one
        #    if next_word == "one":
            # would return 1 instead otherwise
        #        tokens[idx + 1] = Token("", idx)
        #        next_word = ""

        # Normalize Russian inflection of numbers (один, одна, одно,...)
        if not ordinals:
            word = _text_ru_inflection_normalize(word, 1)

        if word not in string_num_scale and \
                word not in _STRING_NUM_RU and \
                word not in _SUMS and \
                word not in multiplies and \
                not (ordinals and word in string_num_ordinal) and \
                not is_numeric(word) and \
                not is_fractional_ru(word, short_scale=short_scale) and \
                not look_for_fractions(word.split('/')):
            words_only = [token.word for token in number_words]
            if number_words and not all([w in _NEGATIVES for w in words_only]):
                break
            else:
                number_words = []
                continue
        elif word not in multiplies \
                and prev_word not in multiplies \
                and prev_word not in _SUMS \
                and not (ordinals and prev_word in string_num_ordinal) \
                and prev_word not in _NEGATIVES:
            number_words = [token]
        elif prev_word in _SUMS and word in _SUMS:
            number_words = [token]
        else:
            number_words.append(token)

        # is this word already a number ?
        if is_numeric(word):
            if word.isdigit():  # doesn't work with decimals
                val = int(word)
            else:
                val = float(word)
            current_val = val

        # is this word the name of a number ?
        if word in _STRING_NUM_RU:
            val = _STRING_NUM_RU.get(word)
            current_val = val
        elif word in string_num_scale:
            val = string_num_scale.get(word)
            current_val = val
        elif ordinals and word in string_num_ordinal:
            val = string_num_ordinal[word]
            current_val = val

        # is the prev word an ordinal number and current word is one?
        # second one, third one
        if ordinals and prev_word in string_num_ordinal and val == 1:
            val = prev_val

        # is the prev word a number and should we sum it?
        # twenty two, fifty six
        if (prev_word in _SUMS and val and val < 10) \
                or (prev_word in _SUMS and val and val < 100 and prev_val >= 100) \
                or all([prev_word in multiplies, val < prev_val if prev_val else False]):
            val = prev_val + val

        # is the prev word a number and should we multiply it?
        # twenty hundred, six hundred
        if word in multiplies:
            if not prev_val:
                prev_val = 1
            val = prev_val * val

        # is this a spoken fraction?
        # half cup
        if val is False:
            val = is_fractional_ru(word, short_scale=short_scale)
            current_val = val

        # 2 fifths
        if not ordinals:
            next_val = is_fractional_ru(next_word, short_scale=short_scale)
            if next_val:
                if not val:
                    val = 1
                val = val * next_val
                number_words.append(tokens[idx + 1])

        # is this a negative number?
        if val and prev_word and prev_word in _NEGATIVES:
            val = 0 - val

        # let's make sure it isn't a fraction
        if not val:
            # look for fractions like "2/3"
            a_pieces = word.split('/')
            if look_for_fractions(a_pieces):
                val = float(a_pieces[0]) / float(a_pieces[1])
        else:
            if all([
                prev_word in _SUMS,
                word not in _SUMS,
                word not in multiplies,
                current_val >= 10
            ]):
                # Backtrack - we've got numbers we can't sum.
                number_words.pop()
                val = prev_val
                break
            prev_val = val

            if word in multiplies and next_word not in multiplies:
                # handle long numbers
                # six hundred sixty six
                # two million five hundred thousand
                #
                # This logic is somewhat complex, and warrants
                # extensive documentation for the next coder's sake.
                #
                # The current word is a power of ten. `current_val` is
                # its integer value. `val` is our working sum
                # (above, when `current_val` is 1 million, `val` is
                # 2 million.)
                #
                # We have a dict `string_num_scale` containing [value, word]
                # pairs for "all" powers of ten: string_num_scale[10] == "ten.
                #
                # We need go over the rest of the tokens, looking for other
                # powers of ten. If we find one, we compare it with the current
                # value, to see if it's smaller than the current power of ten.
                #
                # Numbers which are not powers of ten will be passed over.
                #
                # If all the remaining powers of ten are smaller than our
                # current value, we can set the current value aside for later,
                # and begin extracting another portion of our final result.
                # For example, suppose we have the following string.
                # The current word is "million".`val` is 9000000.
                # `current_val` is 1000000.
                #
                #    "nine **million** nine *hundred* seven **thousand**
                #     six *hundred* fifty seven"
                #
                # Iterating over the rest of the string, the current
                # value is larger than all remaining powers of ten.
                #
                # The if statement passes, and nine million (9000000)
                # is appended to `to_sum`.
                #
                # The main variables are reset, and the main loop begins
                # assembling another number, which will also be appended
                # under the same conditions.
                #
                # By the end of the main loop, to_sum will be a list of each
                # "place" from 100 up: [9000000, 907000, 600]
                #
                # The final three digits will be added to the sum of that list
                # at the end of the main loop, to produce the extracted number:
                #
                #    sum([9000000, 907000, 600]) + 57
                # == 9,000,000 + 907,000 + 600 + 57
                # == 9,907,657
                #
                # >>> foo = "nine million nine hundred seven thousand six
                #            hundred fifty seven"
                # >>> extract_number(foo)
                # 9907657

                time_to_sum = True
                for other_token in tokens[idx + 1:]:
                    if other_token.word in multiplies:
                        if string_num_scale[other_token.word] >= current_val:
                            time_to_sum = False
                        else:
                            continue
                    if not time_to_sum:
                        break
                if time_to_sum:
                    to_sum.append(val)
                    val = 0
                    prev_val = 0

    if val is not None and to_sum:
        val += sum(to_sum)

    return val, number_words


def _initialize_number_data(short_scale):
    """
    Generate dictionaries of words to numbers, based on scale.

    This is a helper function for _extract_whole_number.

    Args:
        short_scale boolean:

    Returns:
        (set(str), dict(str, number), dict(str, number))
        multiplies, string_num_ordinal, string_num_scale

    """
    multiplies = _MULTIPLIES_SHORT_SCALE_RU if short_scale \
        else _MULTIPLIES_LONG_SCALE_RU

    string_num_ordinal_ru = _STRING_SHORT_ORDINAL_RU if short_scale \
        else _STRING_LONG_ORDINAL_RU

    string_num_scale_ru = _SHORT_SCALE_RU if short_scale else _LONG_SCALE_RU
    string_num_scale_ru = invert_dict(string_num_scale_ru)
    string_num_scale_ru.update(generate_plurals_ru(string_num_scale_ru))
    return multiplies, string_num_ordinal_ru, string_num_scale_ru


def extract_number_ru(text, short_scale=True, ordinals=False):
    """
    This function extracts a number from a text string,
    handles pronunciations in long scale and short scale

    https://en.wikipedia.org/wiki/Names_of_large_numbers

    Args:
        text (str): the string to normalize
        short_scale (bool): use short scale if True, long scale if False
        ordinals (bool): consider ordinal numbers, third=3 instead of 1/3
    Returns:
        (int) or (float) or False: The extracted number or False if no number
                                   was found

    """
    return _extract_number_with_text_ru(tokenize(text.lower()),
                                        short_scale, ordinals).value


def extract_duration_ru(text):
    """
    Convert an english phrase into a number of seconds

    Convert things like:
        "10 minute"
        "2 and a half hours"
        "3 days 8 hours 10 minutes and 49 seconds"
    into an int, representing the total number of seconds.

    The words used in the duration will be consumed, and
    the remainder returned.

    As an example, "set a timer for 5 minutes" would return
    (300, "set a timer for").

    Args:
        text (str): string containing a duration

    Returns:
        (timedelta, str):
                    A tuple containing the duration and the remaining text
                    not consumed in the parsing. The first value will
                    be None if no duration is found. The text returned
                    will have whitespace stripped from the ends.
    """
    if not text:
        return None

    # Russian inflection for time: минута, минуты, минут - safe to use минута as pattern
    # For day: день, дня, дней - short pattern not applicable, list all

    time_units = {
        'microseconds': 0,
        'milliseconds': 0,
        'seconds': 0,
        'minutes': 0,
        'hours': 0,
        'days': 0,
        'weeks': 0
    }

    pattern = r"(?P<value>\d+(?:\.?\d+)?)(?:\s+|\-){unit}(?:а|ов|у|ут|уту)?"
    text = _convert_words_to_numbers_ru(text)

    for (unit_ru, unit_en) in _TIME_UNITS_CONVERSION.items():
        unit_pattern = pattern.format(unit=unit_ru)

        def repl(match):
            time_units[unit_en] += float(match.group(1))
            return ''

        text = re.sub(unit_pattern, repl, text)

    text = text.strip()
    duration = timedelta(**time_units) if any(time_units.values()) else None

    return duration, text


def extract_datetime_ru(text, anchor_date=None, default_time=None):
    """ Convert a human date reference into an exact datetime

    Convert things like
        "today"
        "tomorrow afternoon"
        "next Tuesday at 4pm"
        "August 3rd"
    into a datetime.  If a reference date is not provided, the current
    local time is used.  Also consumes the words used to define the date
    returning the remaining string.  For example, the string
       "what is Tuesday's weather forecast"
    returns the date for the forthcoming Tuesday relative to the reference
    date and the remainder string
       "what is weather forecast".

    The "next" instance of a day or weekend is considered to be no earlier than
    48 hours in the future. On Friday, "next Monday" would be in 3 days.
    On Saturday, "next Monday" would be in 9 days.

    Args:
        text (str): string containing date words
        anchor_date (datetime): A reference date/time for "tommorrow", etc
        default_time (time): Time to set if no time was found in the string

    Returns:
        [datetime, str]: An array containing the datetime and the remaining
                         text not consumed in the parsing, or None if no
                         date or time related text was found.
    """

    def clean_string(s):
        # clean unneeded punctuation and capitalization among other things.
        # Normalize Russian inflection
        s = s.lower().replace('?', '').replace('.', '').replace(',', '') \
            .replace("сегодня вечером", "вечером") \
            .replace("сегодня ночью", "ночью")
        word_list = s.split()

        for idx, word in enumerate(word_list):
            # word = word.replace("'s", "")
            ##########
            # Russian Day Ordinals - we do not use 1st,2nd format
            #    instead we use full ordinal number names with specific format(suffix)
            #   Example: тридцать первого > 31
            count_ordinals = 0
            if word == "первого":
                count_ordinals = 1  # These two have different format
            elif word == "третьего":
                count_ordinals = 3
            elif word.endswith("ого"):
                tmp = word[:-3]
                tmp += "ый"
                for nr, name in _ORDINAL_BASE_RU.items():
                    if name == tmp:
                        count_ordinals = nr

            # If number is bigger than 19 check if next word is also ordinal
            #  and count them together
            if count_ordinals > 19:
                if word_list[idx + 1] == "первого":
                    count_ordinals += 1  # These two have different format
                elif word_list[idx + 1] == "третьего":
                    count_ordinals += 3
                elif word_list[idx + 1].endswith("ого"):
                    tmp = word_list[idx + 1][:-3]
                    tmp += "ый"
                    for nr, name in _ORDINAL_BASE_RU.items():
                        if name == tmp and nr < 10:
                            # write only if sum makes acceptable count of days in month
                            if (count_ordinals + nr) <= 31:
                                count_ordinals += nr

            if count_ordinals > 0:
                word = str(count_ordinals)  # Write normalized value into word
            if count_ordinals > 20:
                # If counted number is greater than 20, clear next word so it is not used again
                word_list[idx + 1] = ""
            ##########
            # Remove inflection from Russian months

            word_list[idx] = word

        return word_list

    def date_found():
        return found or \
               (
                       date_string != "" or
                       year_offset != 0 or month_offset != 0 or
                       day_offset is True or hr_offset != 0 or
                       hr_abs or min_offset != 0 or
                       min_abs or sec_offset != 0
               )

    if text == "":
        return None

    anchor_date = anchor_date or now_local()
    found = False
    day_specified = False
    day_offset = False
    month_offset = 0
    year_offset = 0
    today = anchor_date.strftime("%w")
    current_year = anchor_date.strftime("%Y")
    from_flag = False
    date_string = ""
    has_year = False
    time_qualifier = ""

    time_qualifiers_am = _WORDS_MORNING_RU
    time_qualifiers_pm = ['дня', 'вечера']
    time_qualifiers_pm.extend(_WORDS_DAY_RU)
    time_qualifiers_pm.extend(_WORDS_EVENING_RU)
    time_qualifiers_pm.extend(_WORDS_NIGHT_RU)
    time_qualifiers_list = set(time_qualifiers_am + time_qualifiers_pm)
    markers = ['на', 'в', 'во', 'до', 'на', 'это',
               'около', 'этот', 'через', 'спустя', 'за', 'тот']
    days = ['понедельник', 'вторник', 'среда',
            'четверг', 'пятница', 'суббота', 'воскресенье']
    months = _MONTHS_RU
    recur_markers = days + ['выходные', 'викенд']
    months_short = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг',
                    'сен', 'окт', 'ноя', 'дек']
    year_multiples = ["десятилетие", "век", "тысячелетие"]

    words = clean_string(text)
    preposition = ""

    for idx, word in enumerate(words):
        if word == "":
            continue

        if word in markers:
            preposition = word

        word = _text_ru_inflection_normalize(word, 2)
        word_prev_prev = _text_ru_inflection_normalize(
            words[idx - 2], 2) if idx > 1 else ""
        word_prev = _text_ru_inflection_normalize(
            words[idx - 1], 2) if idx > 0 else ""
        word_next = _text_ru_inflection_normalize(
            words[idx + 1], 2) if idx + 1 < len(words) else ""
        word_next_next = _text_ru_inflection_normalize(
            words[idx + 2], 2) if idx + 2 < len(words) else ""

        # this isn't in clean string because I don't want to save back to words
        start = idx
        used = 0
        if word in _WORDS_NOW_RU and not date_string:
            result_str = " ".join(words[idx + 1:])
            result_str = ' '.join(result_str.split())
            extracted_date = anchor_date.replace(microsecond=0)
            return [extracted_date, result_str]
        elif word_next in year_multiples:
            multiplier = None
            if is_numeric(word):
                multiplier = extract_number_ru(word)
            multiplier = multiplier or 1
            multiplier = int(multiplier)
            used += 2
            if word_next == "десятилетие":
                year_offset = multiplier * 10
            elif word_next == "век":
                year_offset = multiplier * 100
            elif word_next == "тысячелетие":
                year_offset = multiplier * 1000
        elif word in time_qualifiers_list and preposition != "через" and word_next != "назад":
            time_qualifier = word
        # parse today, tomorrow, day after tomorrow
        elif word == "сегодня" and not from_flag:
            day_offset = 0
            used += 1
        elif word == "завтра" and not from_flag:
            day_offset = 1
            used += 1
        elif word == "послезавтра" and not from_flag:
            day_offset = 2
            used += 1
        elif word == "после" and word_next == "завтра" and not from_flag:
            day_offset = 2
            used += 2
        elif word == "позавчера" and not from_flag:
            day_offset = -2
            used += 1
        elif word == "вчера" and not from_flag:
            day_offset = -1
            used += 1
        elif (word in ["день", "дня"] and
              word_next == "после" and
              word_next_next == "завтра" and
              not from_flag and
              (not word_prev or not word_prev[0].isdigit())):
            day_offset = 2
            used = 2
        elif word in ["день", "дня"] and is_numeric(word_prev) and preposition == "через":
            if word_prev and word_prev[0].isdigit():
                day_offset += int(word_prev)
                start -= 1
                used = 2
        elif word in ["день", "дня"] and is_numeric(word_prev) and word_next == "назад":
            if word_prev and word_prev[0].isdigit():
                day_offset += -int(word_prev)
                start -= 1
                used = 3
        elif word == "сегодня" and not from_flag and word_prev:
            if word_prev[0].isdigit():
                day_offset += int(word_prev) * 7
                start -= 1
                used = 2
            elif word_prev in _WORDS_NEXT_RU:
                day_offset = 7
                start -= 1
                used = 2
            elif word_prev in _WORDS_PREV_RU:
                day_offset = -7
                start -= 1
                used = 2
                # parse 10 months, next month, last month
        elif word == "неделя" and not from_flag and preposition in ["через", "на"]:
            if word_prev[0].isdigit():
                day_offset = int(word_prev) * 7
                start -= 1
                used = 2
            elif word_prev in _WORDS_NEXT_RU:
                day_offset = 7
                start -= 1
                used = 2
            elif word_prev in _WORDS_PREV_RU:
                day_offset = -7
                start -= 1
                used = 2
        elif word == "месяц" and not from_flag and preposition in ["через", "на"]:
            if word_prev[0].isdigit():
                month_offset = int(word_prev)
                start -= 1
                used = 2
            elif word_prev in _WORDS_NEXT_RU:
                month_offset = 1
                start -= 1
                used = 2
            elif word_prev in _WORDS_PREV_RU:
                month_offset = -1
                start -= 1
                used = 2
        # parse 5 years, next year, last year
        elif word == "год" and not from_flag and preposition in ["через", "на"]:
            if word_prev[0].isdigit():
                year_offset = int(word_prev)
                start -= 1
                used = 2
            elif word_prev in _WORDS_NEXT_RU:
                year_offset = 1
                start -= 1
                used = 2
            elif word_prev in _WORDS_PREV_RU:
                year_offset = -1
                start -= 1
                used = 2
            elif word_prev == "через":
                year_offset = 1
                used = 1
        # parse Monday, Tuesday, etc., and next Monday,
        # last Tuesday, etc.
        elif word in days and not from_flag:
            d = days.index(word)
            day_offset = (d + 1) - int(today)
            used = 1
            if day_offset < 0:
                day_offset += 7
            if word_prev in _WORDS_NEXT_RU:
                if day_offset <= 2:
                    day_offset += 7
                used += 1
                start -= 1
            elif word_prev in _WORDS_PREV_RU:
                day_offset -= 7
                used += 1
                start -= 1
        elif word in months or word in months_short and not from_flag:
            try:
                m = months.index(word)
            except ValueError:
                m = months_short.index(word)
            used += 1
            # Convert Russian months to english
            date_string = _MONTHS_CONVERSION.get(m)
            if word_prev and (word_prev[0].isdigit() or
                              (word_prev == " " and word_prev_prev[0].isdigit())):
                if word_prev == " " and word_prev_prev[0].isdigit():
                    date_string += " " + words[idx - 2]
                    used += 1
                    start -= 1
                else:
                    date_string += " " + word_prev
                start -= 1
                used += 1
                if word_next and word_next[0].isdigit():
                    date_string += " " + word_next
                    used += 1
                    has_year = True
                else:
                    has_year = False

            elif word_next and word_next[0].isdigit():
                date_string += " " + word_next
                used += 1
                if word_next_next and word_next_next[0].isdigit():
                    date_string += " " + word_next_next
                    used += 1
                    has_year = True
                else:
                    has_year = False

        # parse 5 days from tomorrow, 10 weeks from next thursday,
        # 2 months from July
        valid_followups = days + months + months_short
        valid_followups.append("сегодня")
        valid_followups.append("завтра")
        valid_followups.append("послезавтра")
        valid_followups.append("вчера")
        valid_followups.append("позавчера")
        for followup in _WORDS_NEXT_RU:
            valid_followups.append(followup)
        for followup in _WORDS_PREV_RU:
            valid_followups.append(followup)
        for followup in _WORDS_CURRENT_RU:
            valid_followups.append(followup)
        for followup in _WORDS_NOW_RU:
            valid_followups.append(followup)
        if (word in ["до", "по", "от", "с", "со"]) and word_next in valid_followups:
            used = 2
            from_flag = True
            if word_next == "завтра":
                day_offset += 1
            elif word_next == "послезавтра":
                day_offset += 2
            elif word_next == "вчера":
                day_offset -= 1
            elif word_next == "позавчера":
                day_offset -= 2
            elif word_next in days:
                d = days.index(word_next)
                tmp_offset = (d + 1) - int(today)
                used = 2
                if tmp_offset < 0:
                    tmp_offset += 7
                day_offset += tmp_offset
            elif word_next_next and word_next_next in days:
                d = days.index(word_next_next)
                tmp_offset = (d + 1) - int(today)
                used = 3
                if word_next in _WORDS_NEXT_RU:
                    if day_offset <= 2:
                        tmp_offset += 7
                    used += 1
                    start -= 1
                elif word_next in _WORDS_PREV_RU:
                    tmp_offset -= 7
                    used += 1
                    start -= 1
                day_offset += tmp_offset
        if used > 0:
            if start - 1 > 0 and (words[start - 1] in _WORDS_CURRENT_RU):
                start -= 1
                used += 1

            for i in range(0, used):
                words[i + start] = ""

            if start - 1 >= 0 and words[start - 1] in markers:
                words[start - 1] = ""
            found = True
            day_specified = True

    # parse time
    hr_offset = 0
    min_offset = 0
    sec_offset = 0
    hr_abs = None
    min_abs = None
    military = False
    preposition = ""

    for idx, word in enumerate(words):
        if word == "":
            continue

        if word in markers:
            preposition = word

        word = _text_ru_inflection_normalize(word, 2)
        word_prev_prev = _text_ru_inflection_normalize(
            words[idx - 2], 2) if idx > 1 else ""
        word_prev = _text_ru_inflection_normalize(
            words[idx - 1], 2) if idx > 0 else ""
        word_next = _text_ru_inflection_normalize(
            words[idx + 1], 2) if idx + 1 < len(words) else ""
        word_next_next = _text_ru_inflection_normalize(
            words[idx + 2], 2) if idx + 2 < len(words) else ""

        # parse noon, midnight, morning, afternoon, evening
        used = 0
        if word == "полдень":
            hr_abs = 12
            used += 1
        elif word == "полночь":
            hr_abs = 0
            used += 1
        elif word in _WORDS_MORNING_RU:
            if hr_abs is None:
                hr_abs = 8
            used += 1
        elif word in _WORDS_DAY_RU:
            if hr_abs is None:
                hr_abs = 15
            used += 1
        elif word in _WORDS_EVENING_RU:
            if hr_abs is None:
                hr_abs = 19
            used += 1
            if word_next != "" and word_next[0].isdigit() and ":" in word_next:
                used -= 1
        elif word in _WORDS_NIGHT_RU:
            if hr_abs is None:
                hr_abs = 22
        # parse half an hour, quarter hour
        elif word == "час" and \
                (word_prev in markers or word_prev_prev in markers):
            if word_prev in ["пол", "половина"]:
                min_offset = 30
            elif word_prev == "четверть":
                min_offset = 15
            elif word_prev == "через":
                hr_offset = 1
            else:
                hr_offset = 1
            if word_prev_prev in markers:
                words[idx - 2] = ""
                if word_prev_prev in _WORDS_CURRENT_RU:
                    day_specified = True
            words[idx - 1] = ""
            used += 1
            hr_abs = -1
            min_abs = -1
            # parse 5:00 am, 12:00 p.m., etc
        # parse in a minute
        elif word == "минута" and word_prev == "через":
            min_offset = 1
            words[idx - 1] = ""
            used += 1
        # parse in a second
        elif word == "секунда" and word_prev == "через":
            sec_offset = 1
            words[idx - 1] = ""
            used += 1
        elif word[0].isdigit():
            is_time = True
            str_hh = ""
            str_mm = ""
            remainder = ""
            word_next_next_next = words[idx + 3] \
                if idx + 3 < len(words) else ""
            if word_next in _WORDS_EVENING_RU or word_next in _WORDS_NIGHT_RU or word_next_next in _WORDS_EVENING_RU \
                    or word_next_next in _WORDS_NIGHT_RU or word_prev in _WORDS_EVENING_RU \
                    or word_prev in _WORDS_NIGHT_RU or word_prev_prev in _WORDS_EVENING_RU \
                    or word_prev_prev in _WORDS_NIGHT_RU or word_next_next_next in _WORDS_EVENING_RU \
                    or word_next_next_next in _WORDS_NIGHT_RU:
                remainder = "pm"
                used += 1
                if word_prev in _WORDS_EVENING_RU or word_prev in _WORDS_NIGHT_RU:
                    words[idx - 1] = ""
                if word_prev_prev in _WORDS_EVENING_RU or word_prev_prev in _WORDS_NIGHT_RU:
                    words[idx - 2] = ""
                if word_next_next in _WORDS_EVENING_RU or word_next_next in _WORDS_NIGHT_RU:
                    used += 1
                if word_next_next_next in _WORDS_EVENING_RU or word_next_next_next in _WORDS_NIGHT_RU:
                    used += 1

            if ':' in word:
                # parse colons
                # "3:00 in the morning"
                stage = 0
                length = len(word)
                for i in range(length):
                    if stage == 0:
                        if word[i].isdigit():
                            str_hh += word[i]
                        elif word[i] == ":":
                            stage = 1
                        else:
                            stage = 2
                            i -= 1
                    elif stage == 1:
                        if word[i].isdigit():
                            str_mm += word[i]
                        else:
                            stage = 2
                            i -= 1
                    elif stage == 2:
                        remainder = word[i:].replace(".", "")
                        break
                if remainder == "":
                    next_word = word_next.replace(".", "")
                    if next_word in ["am", "pm", "ночи", "утра", "дня", "вечера"]:
                        remainder = next_word
                        used += 1
                    elif next_word == "часа" and word_next_next in ["am", "pm", "ночи", "утра", "дня", "вечера"]:
                        remainder = word_next_next
                        used += 2
                    elif word_next in _WORDS_MORNING_RU:
                        remainder = "am"
                        used += 2
                    elif word_next in _WORDS_DAY_RU:
                        remainder = "pm"
                        used += 2
                    elif word_next in _WORDS_EVENING_RU:
                        remainder = "pm"
                        used += 2
                    elif word_next == "этого" and word_next_next in _WORDS_MORNING_RU:
                        remainder = "am"
                        used = 2
                        day_specified = True
                    elif word_next == "на" and word_next_next in _WORDS_DAY_RU:
                        remainder = "pm"
                        used = 2
                        day_specified = True
                    elif word_next == "на" and word_next_next in _WORDS_EVENING_RU:
                        remainder = "pm"
                        used = 2
                        day_specified = True
                    elif word_next == "в" and word_next_next in _WORDS_NIGHT_RU:
                        if str_hh and int(str_hh) > 5:
                            remainder = "pm"
                        else:
                            remainder = "am"
                        used += 2
                    elif hr_abs and hr_abs != -1:
                        if hr_abs >= 12:
                            remainder = "pm"
                        else:
                            remainder = "am"
                        used += 1
                    else:
                        if time_qualifier != "":
                            military = True
                            if str_hh and int(str_hh) <= 12 and \
                                    (time_qualifier in time_qualifiers_pm):
                                str_hh += str(int(str_hh) + 12)

            else:
                # try to parse numbers without colons
                # 5 hours, 10 minutes etc.
                length = len(word)
                str_num = ""
                remainder = ""
                for i in range(length):
                    if word[i].isdigit():
                        str_num += word[i]
                    else:
                        remainder += word[i]

                if remainder == "":
                    remainder = word_next.replace(".", "").lstrip().rstrip()
                if (
                        remainder == "pm" or
                        word_next == "pm" or
                        remainder == "p.m." or
                        word_next == "p.m." or
                        (remainder == "дня" and preposition != 'через') or
                        (word_next == "дня" and preposition != 'через') or
                        remainder == "вечера" or
                        word_next == "вечера"):
                    str_hh = str_num
                    remainder = "pm"
                    used = 1
                    if (
                            remainder == "pm" or
                            word_next == "pm" or
                            remainder == "p.m." or
                            word_next == "p.m." or
                            (remainder == "дня" and preposition != 'через') or
                            (word_next == "дня" and preposition != 'через') or
                            remainder == "вечера" or
                            word_next == "вечера"):
                        str_hh = str_num
                        remainder = "pm"
                        used = 1
                elif (
                        remainder == "am" or
                        word_next == "am" or
                        remainder == "a.m." or
                        word_next == "a.m." or
                        remainder == "ночи" or
                        word_next == "ночи" or
                        remainder == "утра" or
                        word_next == "утра"):
                    str_hh = str_num
                    remainder = "am"
                    used = 1
                elif (
                        remainder in recur_markers or
                        word_next in recur_markers or
                        word_next_next in recur_markers):
                    # Ex: "7 on mondays" or "3 this friday"
                    # Set str_hh so that is_time == True
                    # when am or pm is not specified
                    str_hh = str_num
                    used = 1
                else:
                    if int(str_num) > 100:
                        str_hh = str(int(str_num) // 100)
                        str_mm = str(int(str_num) % 100)
                        military = True
                        if word_next == "час":
                            used += 1
                    elif (
                            (word_next == "час" or
                             remainder == "час") and
                            word[0] != '0' and
                            # (wordPrev != "в" and wordPrev != "на")
                            word_prev == "через"
                            and
                            (
                                    int(str_num) < 100 or
                                    int(str_num) > 2400
                            )):
                        # ignores military time
                        # "in 3 hours"
                        hr_offset = int(str_num)
                        used = 2
                        is_time = False
                        hr_abs = -1
                        min_abs = -1
                    elif word_next == "минута" or \
                            remainder == "минута":
                        # "in 10 minutes"
                        min_offset = int(str_num)
                        used = 2
                        is_time = False
                        hr_abs = -1
                        min_abs = -1
                    elif word_next == "секунда" \
                            or remainder == "секунда":
                        # in 5 seconds
                        sec_offset = int(str_num)
                        used = 2
                        is_time = False
                        hr_abs = -1
                        min_abs = -1
                    elif int(str_num) > 100:
                        # military time, eg. "3300 hours"
                        str_hh = str(int(str_num) // 100)
                        str_mm = str(int(str_num) % 100)
                        military = True
                        if word_next == "час" or \
                                remainder == "час":
                            used += 1
                    elif word_next and word_next[0].isdigit():
                        # military time, e.g. "04 38 hours"
                        str_hh = str_num
                        str_mm = word_next
                        military = True
                        used += 1
                        if (word_next_next == "час" or
                                remainder == "час"):
                            used += 1
                    elif (
                            word_next == "" or word_next == "час" or
                            (
                                    (word_next == "в" or word_next == "на") and
                                    (
                                            word_next_next == time_qualifier
                                    )
                            ) or word_next in _WORDS_EVENING_RU or
                            word_next_next in _WORDS_EVENING_RU):

                        str_hh = str_num
                        str_mm = "00"
                        if word_next == "час":
                            used += 1
                        if (word_next == "в" or word_next == "на"
                                or word_next_next == "в" or word_next_next == "на"):
                            used += (1 if (word_next ==
                                           "в" or word_next == "на") else 2)
                            word_next_next_next = words[idx + 3] \
                                if idx + 3 < len(words) else ""

                            if (word_next_next and
                                    (word_next_next in time_qualifier or
                                     word_next_next_next in time_qualifier)):
                                if (word_next_next in time_qualifiers_pm or
                                        word_next_next_next in time_qualifiers_pm):
                                    remainder = "pm"
                                    used += 1
                                if (word_next_next in time_qualifiers_am or
                                        word_next_next_next in time_qualifiers_am):
                                    remainder = "am"
                                    used += 1

                        if time_qualifier != "":
                            if time_qualifier in time_qualifiers_pm:
                                remainder = "pm"
                                used += 1

                            elif time_qualifier in time_qualifiers_am:
                                remainder = "am"
                                used += 1
                            else:
                                # TODO: Unsure if this is 100% accurate
                                used += 1
                                military = True
                        elif remainder == "час":
                            if word_next_next in ["ночи", "утра"]:
                                remainder = "am"
                                used += 1
                            elif word_next_next in ["дня", "вечера"]:
                                remainder = "pm"
                                used += 1
                            else:
                                remainder = ""

                    else:
                        is_time = False
            hh = int(str_hh) if str_hh else 0
            mm = int(str_mm) if str_mm else 0
            hh = hh + 12 if remainder == "pm" and hh < 12 else hh
            hh = hh - 12 if remainder == "am" and hh >= 12 else hh
            if (not military and
                    remainder not in ['am', 'pm', 'час', 'минута', 'секунда'] and
                    ((not day_specified) or 0 <= day_offset < 1)):

                # ambiguous time, detect whether they mean this evening or
                # the next morning based on whether it has already passed
                if anchor_date.hour < hh or (anchor_date.hour == hh and
                                             anchor_date.minute < mm):
                    pass  # No modification needed
                elif anchor_date.hour < hh + 12:
                    hh += 12
                else:
                    # has passed, assume the next morning
                    day_offset += 1
            if time_qualifier in time_qualifiers_pm and hh < 12:
                hh += 12

            if hh > 24 or mm > 59:
                is_time = False
                used = 0
            if is_time:
                hr_abs = hh
                min_abs = mm
                used += 1

        if used > 0:
            # removed parsed words from the sentence
            for i in range(used):
                if idx + i >= len(words):
                    break
                words[idx + i] = ""

            # if wordPrev == "o" or wordPrev == "oh":
            #    words[words.index(wordPrev)] = ""

            if word_prev == "скоро":
                hr_offset = -1
                words[idx - 1] = ""
                idx -= 1
            elif word_prev == "позже":
                hr_offset = 1
                words[idx - 1] = ""
                idx -= 1
            if idx > 0 and word_prev in markers:
                words[idx - 1] = ""
                if word_prev in _WORDS_CURRENT_RU:
                    day_specified = True
            if idx > 1 and word_prev_prev in markers:
                words[idx - 2] = ""
                if word_prev_prev in _WORDS_CURRENT_RU:
                    day_specified = True

            idx += used - 1
            found = True
    # check that we found a date
    if not date_found():
        return None

    if day_offset is False:
        day_offset = 0

    # perform date manipulation

    extracted_date = anchor_date.replace(microsecond=0)
    if date_string != "":
        # date included an explicit date, e.g. "june 5" or "june 2, 2017"
        try:
            temp = datetime.strptime(date_string, "%B %d")
        except ValueError:
            # Try again, allowing the year
            temp = datetime.strptime(date_string, "%B %d %Y")
        extracted_date = extracted_date.replace(hour=0, minute=0, second=0)
        if not has_year:
            temp = temp.replace(year=extracted_date.year,
                                tzinfo=extracted_date.tzinfo)
            if extracted_date < temp:
                extracted_date = extracted_date.replace(
                    year=int(current_year),
                    month=int(temp.strftime("%m")),
                    day=int(temp.strftime("%d")),
                    tzinfo=extracted_date.tzinfo)
            else:
                extracted_date = extracted_date.replace(
                    year=int(current_year) + 1,
                    month=int(temp.strftime("%m")),
                    day=int(temp.strftime("%d")),
                    tzinfo=extracted_date.tzinfo)
        else:
            extracted_date = extracted_date.replace(
                year=int(temp.strftime("%Y")),
                month=int(temp.strftime("%m")),
                day=int(temp.strftime("%d")),
                tzinfo=extracted_date.tzinfo)
    else:
        # ignore the current HH:MM:SS if relative using days or greater
        if hr_offset == 0 and min_offset == 0 and sec_offset == 0:
            extracted_date = extracted_date.replace(hour=0, minute=0, second=0)

    if year_offset != 0:
        extracted_date = extracted_date + relativedelta(years=year_offset)
    if month_offset != 0:
        extracted_date = extracted_date + relativedelta(months=month_offset)
    if day_offset != 0:
        extracted_date = extracted_date + relativedelta(days=day_offset)
    if hr_abs != -1 and min_abs != -1:
        # If no time was supplied in the string set the time to default
        # time if it's available
        if hr_abs is None and min_abs is None and default_time is not None:
            hr_abs, min_abs = default_time.hour, default_time.minute
        else:
            hr_abs = hr_abs or 0
            min_abs = min_abs or 0

        extracted_date = extracted_date + relativedelta(hours=hr_abs,
                                                        minutes=min_abs)
        if (hr_abs != 0 or min_abs != 0) and date_string == "":
            if not day_specified and anchor_date > extracted_date:
                extracted_date = extracted_date + relativedelta(days=1)
    if hr_offset != 0:
        extracted_date = extracted_date + relativedelta(hours=hr_offset)
    if min_offset != 0:
        extracted_date = extracted_date + relativedelta(minutes=min_offset)
    if sec_offset != 0:
        extracted_date = extracted_date + relativedelta(seconds=sec_offset)
    for idx, word in enumerate(words):
        if words[idx] == "и" and \
                words[idx - 1] == "" and words[idx + 1] == "":
            words[idx] = ""

    result_str = " ".join(words)
    result_str = ' '.join(result_str.split())
    return [extracted_date, result_str]


def is_fractional_ru(input_str, short_scale=True):
    """
    This function takes the given text and checks if it is a fraction.

    Args:
        input_str (str): the string to check if fractional
        short_scale (bool): use short scale if True, long scale if False
    Returns:
        (bool) or (float): False if not a fraction, otherwise the fraction

    """
    if input_str[-3:] in ["тые", "тых"]:  # leading number is bigger than one (две четвёртые, три пятых)
        input_str = input_str[-3:] + "тая"
    fractions = {"целая": 1}  # first four numbers have little different format

    for num in _FRACTION_STRING_RU:  # Numbers from 2 to 1 hundred, more is not usually used in common speech
        if num > 1:
            fractions[_FRACTION_STRING_RU[num]] = num

    if input_str.lower() in fractions:
        return 1.0 / fractions[input_str.lower()]
    return False


def extract_numbers_ru(text, short_scale=True, ordinals=False):
    """
        Takes in a string and extracts a list of numbers.

    Args:
        text (str): the string to extract a number from
        short_scale (bool): Use "short scale" or "long scale" for large
            numbers -- over a million.  The default is short scale, which
            is now common in most English speaking countries.
            See https://en.wikipedia.org/wiki/Names_of_large_numbers
        ordinals (bool): consider ordinal numbers, e.g. third=3 instead of 1/3
    Returns:
        list: list of extracted numbers as floats
    """
    results = _extract_numbers_with_text_ru(tokenize(text),
                                            short_scale, ordinals)
    return [float(result.value) for result in results]


class RussianNormalizer(Normalizer):
    with open(resolve_resource_file("text/ru-ru/normalize.json"), encoding='utf8') as f:
        _default_config = json.load(f)


def normalize_ru(text, remove_articles=True):
    """ Russian string normalization """
    return RussianNormalizer().normalize(text, remove_articles)


def _text_ru_inflection_normalize(word, arg):
    """
    Russian Inflection normalizer.

    This try to normalize known inflection. This function is called
    from multiple places, each one is defined with arg.

    Args:
        word [Word]
        arg [Int]

    Returns:
        word [Word]

    """
    if word in ["тысяч", "тысячи"]:
        return "тысяча"

    if arg == 1:  # _extract_whole_number_with_text_ru
        if word in ["одна", "одним", "одно", "одной"]:
            return "один"
        if word == "две":
            return "два"
        if word == "пару":
            return "пара"

    elif arg == 2:  # extract_datetime_ru
        if word in ["часа", "часам", "часами", "часов", "часу"]:
            return "час"
        if word in ["минут", "минутам", "минутами", "минуту", "минуты"]:
            return "минута"
        if word in ["секунд", "секундам", "секундами", "секунду", "секунды"]:
            return "секунда"
        if word in ["дней", "дни"]:
            return "день"
        if word in ["неделе", "недели", "недель"]:
            return "неделя"
        if word in ["месяца", "месяцев"]:
            return "месяц"
        if word in ["года", "лет"]:
            return "год"
        if word in _WORDS_MORNING_RU:
            return "утром"
        if word in ["полудне", "полудня"]:
            return "полдень"
        if word in _WORDS_EVENING_RU:
            return "вечером"
        if word in _WORDS_NIGHT_RU:
            return "ночь"
        if word in ["викенд", "выходным", "выходных"]:
            return "выходные"
        if word in ["столетие", "столетий", "столетия"]:
            return "век"

        # Week days
        if word in ["среду", "среды"]:
            return "среда"
        if word in ["пятницу", "пятницы"]:
            return "пятница"
        if word in ["субботу", "субботы"]:
            return "суббота"

        # Months
        if word in ["марта", "марте"]:
            return "март"
        if word in ["мае", "мая"]:
            return "май"
        if word in ["августа", "августе"]:
            return "август"

        if word[-2:] in ["ле", "ля", "не", "ня", "ре", "ря"]:
            tmp = word[:-1] + "ь"
            for name in _MONTHS_RU:
                if name == tmp:
                    return name

    return word
