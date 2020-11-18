from typing import Union, Dict, Iterable, Any


def one_of_includes(check_value: Union[str, Iterable[str], Dict[str, Any]], values_to_check: Iterable[str]):
    return any(x in check_value for x in values_to_check)


def select_key_by_one_of_values_includes(value: str, values_to_check: Dict[str, Iterable]):
    for key in values_to_check:
        if one_of_includes(value, values_to_check[key]):
            return key
    return None


def replace_values_by_keys(value: str, to_replace: Dict[str, str]):
    for key in to_replace:
        value = value.replace(f"{{{{{key}}}}}", to_replace[key])
    return value
