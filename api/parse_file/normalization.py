import re
from fractions import Fraction
from django.utils.module_loading import import_string
from utils.dates import normalize_dots_date


def remove_double_spaces(text: str):
    """
    Удаление "лишних" пробелов
    """
    text = re.sub(" +", " ", text)
    return text


def string_not_empty(value) -> bool:
    result = value and value.strip() and value != "None"
    return result


def normalize_snils(value: str):
    snils = value.replace("-", "").replace(" ", "")
    return snils


def normalize_rate(value):
    """Нормализует значение ставки, на входе str "1/2" "1/4", "3/4" """
    try:
        rate_in_fraciton = Fraction(value)
        float_rate = float(rate_in_fraciton)
    except Exception:
        return value
    return float_rate


def normalize_date(value: str):
    """
    Нормализует дату, на входе str в %Y-%m-%d %HH:%MM, или %d.%m.%Y
    """
    value_within_spaces = remove_double_spaces(value)
    value_in_list = value_within_spaces.split(" ")
    normalized_value = normalize_dots_date(value_in_list[0])
    return normalized_value


def normalize_values(value: str, actions: list):
    """
    Перебирает действия по нормализации
    """
    if not string_not_empty(value):
        return None
    for action in actions:
        normalize_function = import_string(f"api.parse_file.normalization.{action}")
        value = normalize_function(value)
    return value
