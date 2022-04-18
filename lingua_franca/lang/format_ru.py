# -*- coding: utf-8 -*-
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

from lingua_franca.lang.format_common import convert_to_mixed_fraction
from lingua_franca.lang.common_data_ru import _NUM_STRING_RU, \
    _FRACTION_STRING_RU, _LONG_SCALE_RU, _SHORT_SCALE_RU, _SHORT_ORDINAL_RU, _LONG_ORDINAL_RU
from lingua_franca.internal import FunctionNotLocalizedError


def nice_number_ru(number, speech=True, denominators=range(1, 21)):
    """ English helper for nice_number

    This function formats a float to human understandable functions. Like
    4.5 becomes "4 and a half" for speech and "4 1/2" for text

    Args:
        number (int or float): the float to format
        speech (bool): format for speech (True) or display (False)
        denominators (iter of ints): denominators to use, default [1 .. 20]
    Returns:
        (str): The formatted string.
    """

    result = convert_to_mixed_fraction(number, denominators)
    if not result:
        # Give up, just represent as a 3 decimal number
        return str(round(number, 3))

    whole, num, den = result

    if not speech:
        if num == 0:
            # TODO: Number grouping?  E.g. "1,000,000"
            return str(whole)
        else:
            return '{} {}/{}'.format(whole, num, den)

    if num == 0:
        return str(whole)
    den_str = _FRACTION_STRING_RU[den]
    if whole == 0:
        if num == 1 and den <= 4:
            return_string = '{}'.format(den_str)
        else:
            return_string = '{} {}'.format(num, den_str)
    elif num == 1 and den == 2:
        return_string = '{} с половиной'.format(whole)
    else:
        return_string = '{} и {} {}'.format(whole, num, den_str)
    if 2 <= den <= 4:
        if 2 <= num <= 4:
            return_string = return_string[:-1] + 'и'
        elif num > 4:
            return_string = return_string[:-1] + 'ей'
    elif den >= 5:
        if 2 <= num <= 4:
            return_string = return_string[:-2] + 'ые'
        elif num > 4:
            return_string = return_string[:-2] + 'ых'

    return return_string


def pronounce_number_ru(number, places=2, short_scale=True, scientific=False,
                        ordinals=False):
    """
    Convert a number to it's spoken equivalent

    For example, '5.2' would return 'five point two'

    Args:
        number(float or int): the number to pronounce (under 100)
        places(int): maximum decimal places to speak
        short_scale (bool) : use short (True) or long scale (False)
            https://en.wikipedia.org/wiki/Names_of_large_numbers
        scientific (bool): pronounce in scientific notation
        ordinals (bool): pronounce in ordinal form "first" instead of "one"
    Returns:
        (str): The pronounced number
    """
    num = number
    # deal with infinity
    if num == float("inf"):
        return "бесконечность"
    elif num == float("-inf"):
        return "минус бесконечность"
    if scientific:
        number = '%E' % num
        n, power = number.replace("+", "").split("E")
        power = int(power)
        if power != 0:
            if ordinals:
                # This handles negative powers separately from the normal
                # handling since each call disables the scientific flag
                return '{}{} на десять в {}{} степени'.format(
                    'минус ' if float(n) < 0 else '',
                    pronounce_number_ru(
                        abs(float(n)), places, short_scale, False, ordinals=True),
                    'минус ' if power < 0 else '',
                    pronounce_number_ru(abs(power), places, short_scale, False, ordinals=True))
            else:
                # This handles negative powers separately from the normal
                # handling since each call disables the scientific flag
                return '{}{} на десять в степени {}{}'.format(
                    'минус ' if float(n) < 0 else '',
                    pronounce_number_ru(
                        abs(float(n)), places, short_scale, False, ordinals=False),
                    'минус ' if power < 0 else '',
                    pronounce_number_ru(abs(power), places, short_scale, False, ordinals=False))

    if short_scale:
        number_names = _NUM_STRING_RU.copy()
        number_names.update(_SHORT_SCALE_RU)
    else:
        number_names = _NUM_STRING_RU.copy()
        number_names.update(_LONG_SCALE_RU)

    digits = [number_names[n] for n in range(0, 20)]

    tens = [number_names[n] for n in range(10, 100, 10)]

    if short_scale:
        hundreds = [_SHORT_SCALE_RU[n] for n in _SHORT_SCALE_RU.keys()]
    else:
        hundreds = [_LONG_SCALE_RU[n] for n in _LONG_SCALE_RU.keys()]

    # deal with negative numbers
    result = ""
    if num < 0:
        result = "минус "
    num = abs(num)

    # check for a direct match
    if num in number_names and not ordinals:
        result += number_names[num]
    else:
        def _sub_thousand(n, ordinals=False):
            assert 0 <= n <= 999
            if n in _SHORT_ORDINAL_RU and ordinals:
                return _SHORT_ORDINAL_RU[n]
            if n <= 19:
                return digits[n]
            elif n <= 99:
                q, r = divmod(n, 10)
                return tens[q - 1] + (" " + _sub_thousand(r, ordinals) if r
                                      else "")
            else:
                q, r = divmod(n, 100)
                return _NUM_STRING_RU[q * 100] + (" " + _sub_thousand(r, ordinals) if r else "")

        def _short_scale(n):
            if n > max(_SHORT_SCALE_RU.keys()):
                return "бесконечность"
            ordi = ordinals

            if int(n) != n:
                ordi = False
            n = int(n)
            assert 0 <= n
            res = []
            for i, z in enumerate(_split_by(n, 1000)):
                if not z:
                    continue
                number = _sub_thousand(z, not i and ordi)

                if i:
                    if i >= len(hundreds):
                        return ""
                    if ordi:
                        if i * 1000 in _SHORT_ORDINAL_RU:
                            if z == 1:
                                number = _SHORT_ORDINAL_RU[i * 1000]
                            else:
                                if z > 5:
                                    number = number[:-1] + "и"
                                number += _SHORT_ORDINAL_RU[i * 1000]
                        else:
                            if n not in _SHORT_SCALE_RU:
                                num = int("1" + "0" * (len(str(n)) // 3 * 3))

                                if number[-3:] == "два":
                                    number = number[:-1] + "ух"
                                elif number[-2:] == "ри" or number[-2:] == "ре":
                                    number = number[:-1] + "ёх"
                                elif number[-1:] == "ь":
                                    number = number[:-1] + "и"

                                number += _SHORT_SCALE_RU[num] + "ный"
                            else:
                                number = _SHORT_SCALE_RU[n] + "ный"
                    elif z == 1:
                        number = hundreds[i - 1]
                    else:
                        if i == 1:
                            if z % 10 == 1 and z % 100 // 10 != 1:
                                number = number[:-2] + "на"
                            elif z % 10 == 2 and z % 100 // 10 != 1:
                                number = number[:-1] + "е"
                            number += " " + plural_ru(z, "тысяча", "тысячи", "тысяч")
                        elif 1 <= z % 10 <= 4 and z % 100 // 10 != 1:
                            number += " " + hundreds[i - 1] + "а"
                        else:
                            number += " " + hundreds[i - 1] + "ов"

                res.append(number)
                ordi = False

            return " ".join(reversed(res))

        def _split_by(n, split=1000):
            assert 0 <= n
            res = []
            while n:
                n, r = divmod(n, split)
                res.append(r)
            return res

        def _long_scale(n):
            if n >= max(_LONG_SCALE_RU.keys()):
                return "бесконечность"
            ordi = ordinals
            if int(n) != n:
                ordi = False
            n = int(n)
            assert 0 <= n
            res = []
            for i, z in enumerate(_split_by(n, 1000000)):
                if not z:
                    continue
                number = pronounce_number_ru(z, places, True, scientific,
                                             ordinals=ordi and not i)
                # strip off the comma after the thousand
                if i:
                    if i >= len(hundreds):
                        return ""
                    # plus one as we skip 'thousand'
                    # (and 'hundred', but this is excluded by index value)
                    number = number.replace(',', '')

                    if ordi:
                        if (i + 1) * 1000000 in _LONG_ORDINAL_RU:
                            if z == 1:
                                number = _LONG_ORDINAL_RU[
                                    (i + 1) * 1000000]
                            else:
                                number += _LONG_ORDINAL_RU[
                                    (i + 1) * 1000000]
                        else:
                            if n not in _LONG_SCALE_RU:
                                num = int("1" + "0" * (len(str(n)) // 3 * 3))

                                if number[-3:] == "два":
                                    number = number[:-1] + "ух"
                                elif number[-2:] == "ри" or number[-2:] == "ре":
                                    number = number[:-1] + "ёх"
                                elif number[-1:] == "ь":
                                    number = number[:-1] + "и"

                                number += _LONG_SCALE_RU[num] + "ный"
                            else:
                                number = " " + _LONG_SCALE_RU[n] + "ный"
                    elif z == 1:
                        number = hundreds[i]
                    elif z <= 4:
                        number += " " + hundreds[i] + "а"
                    else:
                        number += " " + hundreds[i] + "ов"

                res.append(number)
            return " ".join(reversed(res))

        if short_scale:
            result += _short_scale(num)
        else:
            result += _long_scale(num)

    # deal with scientific notation unpronounceable as number
    if not result and "e" in str(num):
        return pronounce_number_ru(num, places, short_scale, scientific=True)
    # Deal with fractional part
    elif not num == int(num) and places > 0:
        if abs(num) < 1.0 and (result == "минус " or not result):
            result += "ноль"
        result += " точка"
        _num_str = str(num)
        _num_str = _num_str.split(".")[1][0:places]
        for char in _num_str:
            result += " " + number_names[int(char)]
    return result


def nice_time_ru(dt, speech=True, use_24hour=True, use_ampm=False):
    """
    Format a time to a comfortable human format
    For example, generate 'five thirty' for speech or '5:30' for
    text display.
    Args:
        dt (datetime): date to format (assumes already in local timezone)
        speech (bool): format for speech (default/True) or display (False)=Fal
        use_24hour (bool): output in 24-hour/military or 12-hour format
        use_ampm (bool): include the am/pm for 12-hour format
    Returns:
        (str): The formatted time string
    """
    if use_24hour:
        # e.g. "03:01" or "14:22"
        string = dt.strftime("%H:%M")
    else:
        if use_ampm:
            # e.g. "3:01 AM" or "2:22 PM"
            string = dt.strftime("%I:%M")
            if dt.hour < 4:
                string += " ночи"
            elif dt.hour < 12:
                string += " утра"
            elif dt.hour < 18:
                string += " дня"
            else:
                string += " вечера"
        else:
            # e.g. "3:01" or "2:22"
            string = dt.strftime("%I:%M")
        if string[0] == '0':
            string = string[1:]  # strip leading zeros

    if not speech:
        return string

    # Generate a speakable version of the time
    if use_24hour:
        speak = ""

        # Either "0 8 hundred" or "13 hundred"
        if string[0] == '0':
            speak += pronounce_hour_ru(int(string[0])) + " "
            speak += pronounce_number_ru(int(string[1]))
        else:
            speak = pronounce_hour_ru(int(string[0:2]))

        speak += " "
        if string[3:5] == '00':
            speak += "ровно"
        else:
            if string[3] == '0':
                speak += pronounce_number_ru(0) + " "
                speak += pronounce_number_ru(int(string[4]))
            else:
                speak += pronounce_number_ru(int(string[3:5]))
        return speak
    else:
        if dt.hour == 0 and dt.minute == 0:
            return "полночь"
        elif dt.hour == 12 and dt.minute == 0:
            return "полдень"

        hour = dt.hour % 12 or 12  # 12 hour clock and 0 is spoken as 12
        if dt.minute == 15:
            speak = pronounce_hour_ru(hour) + " с четвертью"
        elif dt.minute == 30:
            speak = pronounce_hour_ru(hour) + " с половиной"
        elif dt.minute == 45:
            next_hour = (dt.hour + 1) % 12 or 12
            speak = "без четверти " + pronounce_hour_ru(next_hour)
        else:
            speak = pronounce_hour_ru(hour)

            if dt.minute == 0:
                if not use_ampm:
                    if dt.hour % 12 == 1:
                        return speak
                    return speak + " " + plural_ru(dt.hour % 12, "час", "часа", "часов")
            else:
                if dt.minute < 10:
                    speak += " ноль"
                speak += " " + pronounce_number_ru(dt.minute)

        if use_ampm:
            if dt.hour < 4:
                speak += " ночи"
            elif dt.hour < 12:
                speak += " утра"
            elif dt.hour < 18:
                speak += " дня"
            else:
                speak += " вечера"

        return speak


def nice_duration_ru(duration, speech=True):
    """ Convert duration to a nice spoken timespan

    Args:
        seconds: number of seconds
        minutes: number of minutes
        hours: number of hours
        days: number of days
    Returns:
        str: timespan as a string
    """

    if not speech:
        raise FunctionNotLocalizedError

    days = int(duration // 86400)
    hours = int(duration // 3600 % 24)
    minutes = int(duration // 60 % 60)
    seconds = int(duration % 60)

    out = ''

    if days > 0:
        out += pronounce_number_ru(days)
        out += " " + plural_ru(days, "день", "дня", "дней")
    if hours > 0:
        if out:
            out += " "
        out += pronounce_number_ru(hours)
        out += " " + plural_ru(hours, "час", "часа", "часов")
    if minutes > 0:
        if out:
            out += " "
        out += pronounce_number_feminine_ru(minutes)
        out += " " + plural_ru(minutes, "минута", "минуты", "минут")
    if seconds > 0:
        if out:
            out += " "
        out += pronounce_number_feminine_ru(seconds)
        out += " " + plural_ru(seconds, "секунда", "секунды", "секунд")

    return out


def pronounce_hour_ru(num):
    if num == 1:
        return "час"
    return pronounce_number_ru(num)


def pronounce_number_feminine_ru(num):
    pronounced = pronounce_number_ru(num)

    num %= 100
    if num % 10 == 1 and num // 10 != 1:
        return pronounced[:-2] + "на"
    elif num % 10 == 2 and num // 10 != 1:
        return pronounced[:-1] + "е"

    return pronounced


def plural_ru(num: int, one: str, few: str, many: str):
    num %= 100
    if num // 10 == 1:
        return many
    if num % 10 == 1:
        return one
    if 2 <= num % 10 <= 4:
        return few
    return many
