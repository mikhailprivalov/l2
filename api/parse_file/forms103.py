from typing import Union
from openpyxl.reader.excel import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from api.parse_file.normalization import normalize_values
from api.parse_file.validaiton import check_values
from employees.models import Department, Position, Employee, EmployeePosition, TypeWorkTimeEmployee
from hospitals.models import Hospitals


def check_request_data(organization_id, user=None):
    """
    Проверяет есть ли переданная организация и проверяет права пользователя (если он передан)
    """
    result = {"ok": True, "message": ""}
    organization: Union[Hospitals, None] = Hospitals.objects.filter(pk=organization_id).first()
    if not organization:
        result = {"ok": False, "result": {}, "message": "Такой организации нет"}
    elif user:
        user_organization: Union[Hospitals, None] = user.doctorprofile.get_hospital()
        user_is_admin = user.is_superuser
        if user_organization.pk != organization.pk and user_is_admin is False:
            result = {"ok": False, "result": {}, "message": "Запрещено передавать не свою организацию"}
    return result


def check_need_col(cols: list, need_cols: set):
    """
    Проверяет что все необходимые колонки есть
    """
    other_need_cols = set(set(cols) - need_cols)
    if len(other_need_cols) + len(need_cols) != len(cols):
        return False
    return True


def parse_work_sheet(ws: Worksheet):
    """
    Разбор xlsx листа из файла
    """
    result = {"ok": True, "message": "", "result": {}}
    need_col_name = {"Вид занятости", "СНИЛС", "Табельный номер", "Сотрудник", "Подразделение", "Должность", "Количество ставок", "Дата приема", "Дата увольнения"}
    starts = False
    employment_form_idx, snils_idx, tabel_number_idx, employee_fio_idx, department_title_idx, position_title_idx, rate_idx, date_employment_idx, date_dismissal_idx = (
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
    )
    employees = []
    incorrect_employees = []
    departments_titles = set()
    positions_titles = set()
    for row in ws.rows:
        cells = [str(x.value) for x in row]
        if not starts:
            if "Табельный номер" in cells:
                if not check_need_col(cells, need_col_name):
                    return {"ok": False, "message": "Нет обязательных полей", "result": {}}
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
            normalized_employee_data = normalize_employee_data(
                employment_form=cells[employment_form_idx],
                snils=cells[snils_idx],
                tabel_number=cells[tabel_number_idx],
                fio=cells[employee_fio_idx],
                department_title=cells[department_title_idx],
                position_title=cells[position_title_idx],
                rate=cells[rate_idx],
                date_employment=cells[date_employment_idx],
                date_dismissal=cells[date_dismissal_idx],
            )
            validation_result = validate_employee_data(normalized_employee_data)
            if not validation_result["ok"] and validation_result.get("empty"):
                continue
            if not validation_result["ok"]:
                incorrect_employees.append(validation_result["data"])
                continue
            departments_titles.add(normalized_employee_data["department_title"])
            positions_titles.add(normalized_employee_data["position_title"])
            employees.append(normalized_employee_data)
    if not starts:
        return {"ok": False, "result": {}, "message": "Не найдены колонка 'Табельный номер'"}
    result["result"] = {"employees": employees, "incorrect_employees": incorrect_employees, "departments_titles": departments_titles, "positions_titles": positions_titles}
    return result


def normalize_employee_data(**kwargs):
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
    actions = {
        "employment_form": ["remove_double_spaces"],
        "snils": ["normalize_snils"],
        "tabel_number": ["remove_double_spaces"],
        "fio": ["remove_double_spaces"],
        "department_title": ["remove_double_spaces"],
        "position_title": ["remove_double_spaces"],
        "rate": ["remove_double_spaces", "normalize_rate"],
        "date_employment": ["normalize_date"],
        "date_dismissal": ["normalize_date"],
    }

    for key in kwargs.keys():
        action = actions.get(key, None)
        if action:
            action_result = normalize_values(kwargs[key], action)
            result[key] = action_result

    if result["fio"]:
        fio_data = result["fio"].split(" ")
        result["family"] = fio_data[0]
        result["name"] = fio_data[1]
        if len(fio_data) > 2:
            result["patronymic"] = " ".join(fio_data[2:])
    return result


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
    }
    check_lists = {
        "employment_form": ["not_empty", "max_len"],
        "snils": ["not_empty", "max_len"],
        "tabel_number": ["not_empty", "max_len"],
        "fio": ["not_empty", "max_len"],
        "department_title": ["not_empty", "max_len"],
        "position_title": ["not_empty", "max_len"],
        "rate": ["not_empty", "rate"],
        "date_employment": ["not_empty", "date"],
        "date_dismissal": ["date"],
    }
    result = {"ok": True, "data": {}}
    fio = normalized_data["fio"]
    snils = normalized_data["snils"]
    name_local = fio if fio else snils
    errors = []
    if not name_local:
        result = {"ok": False, "data": {}, "empty": True}
        return result
    for key in normalized_data.keys():
        checks = check_lists.get(key, [])
        value_len = values_lens.get(key, None)
        ru_key = russian_keys.get(key, None)
        check_result = check_values(normalized_data[key], checks, value_len, ru_key)
        if not check_result["ok"]:
            errors.append(check_result["message"])
    if errors:
        result = {"ok": False, "data": {"fio": name_local, "reason": ", ".join(errors)}, "empty": False}
    return result


def update_organization_departments(organization_id: int, new_departments_titles: Union[list, set]):
    """
    Добавляет подразделения в организации если их не было
    """
    all_current_departments_titles = Department.get_active_titles(organization_id)
    for department_title in new_departments_titles:
        if department_title not in all_current_departments_titles:
            Department.create_department(department_title, organization_id)


def update_organization_positions(organization_id: int, new_positions_titles: Union[list, set]):
    """
    Добавляет должности в организации если их не было
    """
    all_current_positions_titles = Position.get_active_titles(organization_id)
    for position_title in new_positions_titles:
        if position_title not in all_current_positions_titles:
            Position.create_position(position_title, organization_id)


def update_employee_position(employee_position, employee_data):
    """
    Обновляет данные трудового договора (EmployeePosition)
    """
    if employee_data["date_dismissal"]:
        employee_position.date_dismissal = employee_data["date_dismissal"]
        employee_position.is_active = False
        employee_position.save()


def create_employee_position(employee_data, employee, department, position, employment_form):
    """
        Создает новый трудовой договор (EmployeePosition)
        """
    active = False if employee_data["date_dismissal"] else True
    new_employee_position = EmployeePosition(is_active=active, employee_id=employee.pk, position_id=position.pk, department_id=department.pk, tabel_number=employee_data["tabel_number"],
                                             rate=employee_data["rate"], type_work_time_id=employment_form.pk, date_employment=employee_data["date_employment"],
                                             date_dismissal=employee_data["date_dismissal"])
    new_employee_position.save()


def update_organization_employee_positions(organization_id: int, employees):
    """
    Обновление и создание трудовых договоров (EmployeePosition)
    Ищет активный трудовой договор - обновляет, если нет, ищет архивный, если нет - создает архивный
    Если не нашло ничего - создает новый трудовой договор
    """
    departments = Department.get_active_departments(organization_id)
    positions = Position.get_active_positions(organization_id)
    employment_forms = TypeWorkTimeEmployee.objects.all()
    incorrent_employees = []
    for employee in employees:
        current_employee = Employee.find_by_snils(employee["snils"], organization_id)
        if not current_employee:
            current_employee = Employee.create_employee(employee["family"], employee["name"], employee["patronymic"], employee["snils"], organization_id, True)
        current_department = departments.get(name=employee["department_title"])
        current_position = positions.get(name=employee["position_title"])
        current_employment_form = employment_forms.filter(title=employee["employment_form"]).first()
        if not current_employment_form:
            incorrent_employees.append({"fio": employee["fio"], "reason": f"Нет такого вид занятости в справочнике ({employee['employment_form']})"})
            continue
        current_active_employee_position = EmployeePosition.find_employee_position(True, current_employee, current_position, current_department, employee["tabel_number"])
        if current_active_employee_position:
            update_employee_position(current_active_employee_position, employee)
        elif not current_active_employee_position and employee["date_dismissal"]:
            current_non_active_employee_position = EmployeePosition.find_employee_position(False, current_employee, current_position, current_department, employee["tabel_number"])
            if not current_non_active_employee_position:
                create_employee_position(employee, current_employee, current_department, current_position, current_employment_form)
        else:
            create_employee_position(employee, current_employee, current_department, current_position, current_employment_form)
    return {"ok": True, "message": "", "data": incorrent_employees}


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
    result_request_check = check_request_data(organization_id, user)
    if not result_request_check["ok"]:
        return result_request_check
    wb = load_workbook(filename=file)
    ws = wb[wb.sheetnames[0]]
    result_parse_file = parse_work_sheet(ws)
    if not result_parse_file["ok"]:
        return result_parse_file
    employees: list = result_parse_file["result"]["employees"]
    incorrect_employees: list = result_parse_file["result"]["incorrect_employees"]
    departments_titles: set = result_parse_file["result"]["departments_titles"]
    positions_titles: set = result_parse_file["result"]["positions_titles"]
    update_organization_departments(organization_id, departments_titles)
    update_organization_positions(organization_id, positions_titles)
    result_update = update_organization_employee_positions(organization_id, employees)
    incorrect_employees.extend(result_update["data"])
    columns = [{"field": "fio", "key": "fio", "title": "Сотрудник", "align": "left", "width": 250}, {"field": "reason", "key": "reason", "title": 'Причины ошибки'}]
    result = {
        "colData": columns,
        "data": incorrect_employees,
    }
    return {"ok": True, "result": result, "message": ""}
