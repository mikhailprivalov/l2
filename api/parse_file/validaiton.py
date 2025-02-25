import datetime
from fractions import Fraction


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
        try:
            value_in_fraction = Fraction(value)
            value_in_float = float(value_in_fraction)
            if value_in_float > 1:
                return {"ok": False, "message": "больше единицы"}
        except Exception:
            return {"ok": False, "message": "не корректно"}
    return {"ok": True, "message": ""}


def check_date(data):
    value = data["value"]
    if value:
        try:
            datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return {"ok": False, "message": "неверная/несуществующая дата"}
    return {"ok": True, "message": ""}


def check_value(value: str, checks: list, value_len: int, return_key: str):
    """
    Перебирает проверки
    not_empty - обязательно значение
    """
    checks_func = {
        "not_empty": check_not_empty,
        "max_len": check_max_len,
        "rate": check_rate,
        "date": check_date,
    }

    for check in checks:
        check_func = checks_func.get(check, None)
        if check_func:
            try:
                result = check_func({"value": value, "max_len": value_len})
                if not result["ok"]:
                    return {"ok": result["ok"], "message": f"{return_key}: {result['message']}"}
            except Exception as e:
                return {"ok": False, "message": f"Ошибка проверки, {e}"}
    return {"ok": True, "message": ""}
