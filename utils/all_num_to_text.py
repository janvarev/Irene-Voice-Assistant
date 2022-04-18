# MIT License
# Janvarev Vladislav
#
# library for translate all digits in text to pronounce

import re

#from utils.num_to_text_ru import num2text
from lingua_franca.format import pronounce_number

def load_language(lang:str):
    import lingua_franca
    lingua_franca.load_language(lang)

def convert_one_num_float(match_obj):
    if match_obj.group() is not None:
        text = str(match_obj.group())
        return pronounce_number(float(match_obj.group()))

def convert_diapazon(match_obj):
    if match_obj.group() is not None:
        text = str(match_obj.group())
        text = text.replace("-"," тире ")
        return all_num_to_text(text)


def all_num_to_text(text:str) -> str:
    text = re.sub(r'[\d]*[.][\d]+-[\d]*[.][\d]+', convert_diapazon, text)
    text = re.sub(r'-[\d]*[.][\d]+', convert_one_num_float, text)
    text = re.sub(r'[\d]*[.][\d]+', convert_one_num_float, text)
    text = re.sub(r'[\d]-[\d]+', convert_diapazon, text)
    text = re.sub(r'-[\d]+', convert_one_num_float, text)
    text = re.sub(r'[\d]+', convert_one_num_float, text)
    text = text.replace("%", " процентов")
    return text

if __name__ == "__main__":
    load_language("ru")
    print(all_num_to_text("Ба ва 120.1-120.8, Да -30.1, Ка 44.05, Га 225. Рынок -10%. Тест"))