import datetime

from django.utils.module_loading import import_string


def check_not_empty(data):
    value = data["value"]
    if not value:
        return {"ok": False, "message": "не указано"}
    return {"ok": True, "message": ""}


def check_max_len(data):
    value = data["value"]
    max_len = data["max_len"]
    if value and max_len:
        if len(value) > max_len:
            return {"ok": False, "message": f"превышает максимальную длину ({max_len})"}
    return {"ok": True, "message": ""}


def check_rate(data):
    value = data["value"]
    if value:
        if not isinstance(value, float):
            return {"ok": False, "message": "не корректно"}
        elif isinstance(value, float) and value > 1:
            return {"ok": False, "message": "больше единицы"}
    return {"ok": True, "message": ""}


def check_date(data):
    value = data["value"]
    if value:
        try:
            datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return {"ok": False, "message": "неверная/несуществующая дата"}
    return {"ok": True, "message": ""}


def check_values(value: str, checks: list, value_len: int, return_key: str):
    """
    Перебирает проверки
    not_empty - обязательно значение
    """
    for check in checks:
        check_function = import_string(f"api.parse_file.validation.check_{check}")
        result = check_function({"value": value, "max_len": value_len})
        if not result["ok"]:
            return {"ok": result["ok"], "message": f"{return_key}: {result['message']}"}
    return {"ok": True, "message": ""}
