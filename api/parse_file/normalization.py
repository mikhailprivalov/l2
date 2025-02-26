from fractions import Fraction

from utils.dates import normalize_dots_date


def remove_double_spaces(text: str, return_list: bool = False, no_join: bool = False):
    """
    Удаление двойных пробелов и пробелов в начале и конце строки
    """
    text_list = text.split(" ")
    text_list_normalized = [word for word in text_list if word.strip()]
    if return_list:
        result = text_list_normalized
    else:
        result = " ".join(text_list_normalized)
    return result


def string_not_empty(value) -> bool:
    result = value and value.strip() and value != "None"
    return result


def normalize_snils(value: str):
    snils = value.replace("-", "").replace(" ", "")
    return snils


def normalize_rate(value):
    """ Нормализует значение ставки, на входе str "1/2" "1/4", "3/4" """
    try:
        rate_in_fraciton = Fraction(value)
        float_rate = float(rate_in_fraciton)
    except Exception:
        return None
    return float_rate


def normalize_date(value: str):
    """
    Нормализует дату, на входе str в %Y-%m-%d %HH:%MM, или %d.%m.%Y
    """
    value_in_list = remove_double_spaces(value, True)
    normalized_value = normalize_dots_date(value_in_list[0])
    return normalized_value


def normalize_values(value: str, actions: list):
    """
    Перебирает действия по нормализации
    """
    normalize_funcs = {
        "remove_double_spaces": remove_double_spaces,
        "normalize_snils": normalize_snils,
        "normalize_rate": normalize_rate,
        "normalize_date": normalize_date,
    }

    if string_not_empty(value):
        tmp_value = value
        for action in actions:
            normalize_func = normalize_funcs.get(action)
            if normalize_func:
                try:
                    tmp_value = normalize_func(tmp_value)
                    if not tmp_value:
                        return None
                except Exception as e:
                    return None
    else:
        return None
    return tmp_value
