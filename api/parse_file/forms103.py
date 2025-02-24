import datetime
from fractions import Fraction
from typing import Union

from openpyxl.reader.excel import load_workbook

from hospitals.models import Hospitals


def check_need_col(cols: list, need_cols: set):
    other_need_cols = set(set(cols) - need_cols)
    if len(other_need_cols) + len(need_cols) != len(cols):
        return False
    return True


def remove_spaces(text: str, return_list: bool = False) -> Union[str, list]:
    text_list = text.split(" ")
    text_list_normalized = [word for word in text_list if word.strip()]
    if return_list:
        result = text_list_normalized
    else:
        result = " ".join(text_list_normalized)
    return result


def not_empty(value) -> bool:
    result = value and value.strip() and value != "None"
    return result


def check_date(date):
    if not date:
        return False
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return False
    return True

def normalize_employee_data(employment_form, snils, tabel_number, fio, department_title, position_title, rate, date_employment, date_dismissal):
    result = {
        "employment_form": None,
        "snils": None,
        "tabel_number": None,
        "fio": None,
        "family": None,
        "name": None,
        "patronymic": None,
        "department_title": None,
        "position_title": None,
        "rate": None,
        "date_employment": None,
        "date_dismissal": None,
    }

    if not_empty(employment_form):
        result["employment_form"] = remove_spaces(employment_form)
    if not_empty(snils):
        result["snils"] = snils.replace("-", "").replace(" ", "")
    if not_empty(tabel_number):
        result["tabel_number"] = remove_spaces(tabel_number)
    if not_empty(fio):
        fio_data: list = remove_spaces(fio, True)
        result["fio"] = " ".join(fio_data)
        result["family"] = fio_data[0]
        result["name"] = fio_data[1]
        if len(fio_data) > 2:
            result["patronymic"] = fio_data[2:]
    if not_empty(department_title):
        result["department_title"] = remove_spaces(department_title)
    if not_empty(position_title):
        result["position_title"] = remove_spaces(position_title)
    if not_empty(rate):
        result["rate"] = remove_spaces(rate)
    if not_empty(date_employment):
        result["date_employment"] = remove_spaces(date_employment)[0]
    if not_empty(date_dismissal):
        result["date_dismissal"] = remove_spaces(date_dismissal)[0]
    return result


def check_len(data):
    value = data["value"]
    max_len = data["max_len"]
    if len(value) > max_len:
        return {"ok": False, "message": "Слишком длинный (ое)"}
    return {"ok": True, "message": ""}


def check_value(value: str, checks: list, value_len: int, return_key: str):

    checks_func = {
        "len": check_len,
    }

    for check in checks:
        check_func = checks_func.get(check, None)
        if check_func:
            result = check_func({"value": value, "max_len": value_len})
            if not result["ok"]:
                return {"ok": result["ok"], "message": f"{return_key}: {result['message']}"}
    return {"ok": True, "message": ""}


def validate_employee_data(normalized_data):

    russian_keys = {
        "employment_form": "Вид занятости",
        "snils": "СНИЛС",
        "tabel_number": "Табельный номер",
        "fio": "ФИО",
        "department_title": "Подразделение",
        "position_title": "Должность",
        "rate": "Количество ставок",
        "date_employment": "Дата приема",
        "date_dismissal": "Дата увольнения",
    }
    values_lens = {
        "employment_form": 255,
        "snils": 11,
        "tabel_number": 255,
        "fio": 192,
        "department_title": 128,
        "position_title": 128,
        "date_employment": "Дата приема",
        "date_dismissal": "Дата увольнения",
    }
    check_lists = {
        "employment_form": ["len"],
        "snils": ["empty", "len"],
        "tabel_number": ["empty", "len"],
        "fio": ["empty", "len"],
        "department_title": ["empty", "len"],
        "position_title": ["empty", "len"],
        "rate": ["is_float"],
        "date_employment": ["is_date"],
        "date_dismissal": ["is_date"],
    }

    result = {"ok": True, "data": {}}
    fio = normalized_data["fio"]
    snils = normalized_data["snils"]
    name_local = fio if fio else snils
    errors = []
    if not name_local:
        result = {"ok": False, "data": {}, "empty": True}
        return result
    if normalized_data["employment_form"] and len(normalized_data["employment_form"]) > 255:
        errors.append("Вид занятости слишком длинный")

    for key in normalized_data.keys():
        checks = check_lists.get(key, [])
        value_len = values_lens.get(key, None)
        ru_key = russian_keys.get(key, None)
        check_result = check_value(normalized_data[key], checks, value_len, ru_key)
        if not check_result["ok"]:
            errors.append(check_result["message"])

    if not snils:
        errors.append("Нет СНИЛС")
    elif len(snils) > 11:
        errors.append("Не корректный СНИЛС")
    if not normalized_data["tabel_number"]:
        errors.append("Нет табельного номера")
    elif len(normalized_data["tabel_number"]) > 255:
        errors.append("Табельный номер слишком длинный")
    if not normalized_data["fio"]:
        errors.append("Нет ФИО")
    if not normalized_data["department_title"]:
        errors.append("Нет подразделения")
    elif len(normalized_data["department_title"]) > 128:
        errors.append("Подразделение слишком длинное")
    if not normalized_data["position_title"]:
        errors.append("Нет должности")
    if not normalized_data["rate"]:
        errors.append("Нет ставки")
    if not normalized_data["date_employment"]:
        errors.append("Нет даты приема")
    elif not check_date(normalized_data["date_employment"]):
        errors.append("Дата приема: неверная/несуществующая дата")

    if errors:
        result = {"ok": False, "data": {"fio": name_local, "reason": ", ".join(errors)}, "empty": False}

    return result


def form_01(request_data):
    """
    Загрузка сотрудников организации

    На входе:
    "file" - Файл XLSX со столбцами (указаны в need_col_name)
    "entity_id" - ID организации куда загружать данные с файла
    "user" (опционально) - user объект из request-а с фронта, может не быть при вызове из django management commands
    """

    file = request_data.get("file")
    organization_id = request_data.get("entity_id")
    user = request_data.get("user")
    organization: Union[Hospitals, None] = Hospitals.objects.filter(pk=organization_id).first()
    if not organization:
        return {"ok": False, "result": {}, "message": "Такой организации нет"}
    if user:
        user_organization: Union[Hospitals, None] = user.doctorprofile.get_hospital()
        user_is_admin = user.is_superuser
        if user_organization.pk != organization.pk and user_is_admin is False:
            return {"ok": False, "result": {}, "message": "Запрещено передавать не свою организацию"}

    wb = load_workbook(filename=file)
    ws = wb[wb.sheetnames[0]]
    columns = [{"field": "title", "key": "title", "title": "Сотрудник", "align": "left", "width": 250}, {"field": "reason", "key": "reason", "title": 'Причина ошибки'}]
    incorrect_employees = []
    employment_form_idx, snils_idx, tabel_number_idx, employee_fio_idx, department_title_idx, position_title_idx, rate_idx, date_employment_idx, date_dismissal_idx = ('', '', '', '', '',
                                                                                                                                                                       '', '', '', '')
    need_col_name = {"Вид занятости", "СНИЛС", "Табельный номер", "Сотрудник", "Подразделение", "Должность", "Количество ставок", "Дата приема", "Дата увольнения"}
    starts = False
    for row in ws.rows:
        cells = [str(x.value) for x in row]
        if not starts:
            if "Табельный номер" in cells:
                if not check_need_col(cells, need_col_name):
                    return {"ok": False, "result": {}, "message": "Нет обязательных полей"}
                employment_form_idx = cells.index("Вид занятости")
                snils_idx = cells.index("СНИЛС")
                tabel_number_idx = cells.index("Табельный номер")
                employee_fio_idx = cells.index("Сотрудник")
                department_title_idx = cells.index("Подразделение")
                position_title_idx = cells.index("Должность")
                rate_idx = cells.index("Количество ставок")
                date_employment_idx = cells.index("Дата приема")
                date_dismissal_idx = cells.index("Дата увольнения")
                starts = True
        else:
            employment_form = cells[employment_form_idx]
            snils = cells[snils_idx]
            tabel_number = cells[tabel_number_idx]
            employee_fio = cells[employee_fio_idx]
            department_title = cells[department_title_idx]
            position_title = cells[position_title_idx]
            rate = cells[rate_idx]
            date_employment = cells[date_employment_idx]
            date_dismissal = cells[date_dismissal_idx]

            normalized_employee_data = normalize_employee_data(employment_form, snils, tabel_number, employee_fio, department_title, position_title, rate, date_employment, date_dismissal)
            validation_result = validate_employee_data(normalized_employee_data)

            if not validation_result["ok"] and validation_result.get("empty"):
                continue
            if not validation_result["ok"]:
                incorrect_employees.append(validation_result["data"])
                continue

            # if not valid:
            #     incorrect_employees.append({"title": title, "reason": "Валидация не пройдена"})
            #     continue
    result = {
        "colData": columns,
        "data": incorrect_employees,
    }

    if not starts:
        return {"ok": False, "result": [], "message": "Не найдены колонка 'Табельный номер'"}
    return {"ok": True, "result": result, "message": ""}
