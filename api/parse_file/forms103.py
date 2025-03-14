from typing import Union
from openpyxl.reader.excel import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from api.parse_file.normalization import normalize_values
from api.parse_file.validation import check_values
from employees.models import Department, Position, Employee, EmployeePosition, TypeWorkTimeEmployee
from hospitals.models import Hospitals


def check_request_data(organization_id, user=None):
    """
    Проверяет есть ли переданная организация и проверяет права пользователя (если он передан)
    """
    result = {"ok": True, "message": ""}
    organization: Union[Hospitals, None] = Hospitals.objects.filter(pk=organization_id).first()
    if not organization:
        result = {"ok": False, "message": "Такой организации нет"}
    elif user:
        user_organization: Union[Hospitals, None] = user.doctorprofile.get_hospital()
        user_is_admin = user.is_superuser
        if user_organization.pk != organization.pk and user_is_admin is False:
            result = {"ok": False, "message": "Запрещено передавать не свою организацию"}
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
    result = {"ok": True, "message": ""}
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
            employee_data = {
                "employment_form": cells[employment_form_idx],
                "snils": cells[snils_idx],
                "tabel_number": cells[tabel_number_idx],
                "fio": cells[employee_fio_idx],
                "department_title": cells[department_title_idx],
                "position_title": cells[position_title_idx],
                "rate": cells[rate_idx],
                "date_employment": cells[date_employment_idx],
                "date_dismissal": cells[date_dismissal_idx],
            }
            normalized_employee_data = normalize_employee_data(employee_data)
            validation_result = validate_employee_data(normalized_employee_data)
            if not validation_result.get("ok") and validation_result.get("empty"):
                continue
            if not validation_result.get("ok"):
                incorrect_employees.append(validation_result["data"])
                continue
            departments_titles.add(normalized_employee_data["department_title"])
            positions_titles.add(normalized_employee_data["position_title"])
            employees.append(normalized_employee_data)
    if not starts:
        return {"ok": False, "message": "Не найдена колонка 'Табельный номер'", "result": {}}
    result["result"] = {"employees": employees, "incorrect_employees": incorrect_employees, "departments_titles": departments_titles, "positions_titles": positions_titles}
    return result


def normalize_employee_data(employee_data: dict):
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

    actions_lists = [
        {
            "fields": {"employment_form", "tabel_number", "fio", "department_title", "position_title", "rate"}, "normalize_funcs": {"remove_double_spaces"},
        },
        {
            "fields": {"snils"}, "normalize_funcs": {"normalize_snils"}
        },
        {
            "fields": {"rate"}, "normalize_funcs": {"normalize_rate"}
        },
        {
            "fields": {"date_employment", "date_dismissal"}, "normalize_funcs": {"normalize_date"}
        },
    ]

    for action in actions_lists:
        fields = action.get("fields", set())
        normalize_funcs = action.get("normalize_funcs", set())
        for field in fields:
            value = employee_data.get(field)
            normalized_value = normalize_values(value, normalize_funcs)
            result[field] = normalized_value

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
        "department_title": 255,
        "position_title": 128,
    }

    checks_lists = [
        {
            "fields": {"employment_form", "snils", "tabel_number", "fio", "department_title", "position_title"}, "check_funcs": {"check_not_empty", "check_max_len"},
        },
        {
            "fields": {"snils"}, "check_funcs": {"check_snils"}
        },
        {
            "fields": {"rate"}, "check_funcs": {"check_not_empty", "check_rate"}
        },
        {
            "fields": {"date_employment"}, "check_funcs": {"check_not_empty"}
        },
        {
            "fields": {"date_employment", "date_dismissal"}, "check_funcs": {"check_date"}
        },
    ]
    result = {"ok": True, "data": {}}
    fio = normalized_data.get("fio")
    snils = normalized_data.get("snils")
    name_local = fio if fio else snils
    errors = []
    if not name_local:
        result = {"ok": False, "data": {}, "empty": True}
        return result

    value_invalid = set()

    for check in checks_lists:
        fields = check.get("fields", set())
        check_funcs = check.get("check_funcs", set())
        for field in fields:
            if field not in value_invalid:
                value = normalized_data.get(field)
                value_len = values_lens.get(field)
                ru_key = russian_keys.get(field)
                check_result = check_values(value, check_funcs, value_len, ru_key)
                if not check_result.get("ok"):
                    value_invalid.add(field)
                    errors.append(check_result.get("message"))
    if errors:
        result = {"ok": False, "data": {"fio": name_local, "reason": ", ".join(errors)}}
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
    if employee_data.get("date_dismissal"):
        employee_position.date_dismissal = employee_data.get("date_dismissal")
        employee_position.is_active = False
        employee_position.save()


def create_employee_position(employee_data, employee, department, position, employment_form):
    """
    Создает новый трудовой договор (EmployeePosition)
    """
    active = False if employee_data.get("date_dismissal") else True
    new_employee_position = EmployeePosition(
        is_active=active,
        employee_id=employee.pk,
        position_id=position.pk,
        department_id=department.pk,
        tabel_number=employee_data.get("tabel_number"),
        rate=employee_data.get("rate"),
        type_work_time_id=employment_form.pk,
        date_employment=employee_data.get("date_employment"),
        date_dismissal=employee_data.get("date_dismissal"),
    )
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
        snils = employee.get("snils")
        employment_form = employee.get("employment_form")
        tabel_number = employee.get("tabel_number")
        current_employee = Employee.find_by_snils(snils, organization_id)
        if not current_employee:
            current_employee = Employee.create_employee(employee.get("family"), employee.get("name"), employee.get("patronymic"), snils, organization_id, True)
        current_department = departments.get(name=employee.get("department_title"))
        current_position = positions.get(name=employee.get("position_title"))
        current_employment_form = employment_forms.filter(title=employment_form).first()
        if not current_employment_form:
            incorrent_employees.append({"fio": employee["fio"], "reason": f"Нет такого вида занятости в справочнике ({employment_form})"})
            continue
        current_active_employee_position = EmployeePosition.find_employee_position(True, current_employee, current_position, current_department, tabel_number)
        if current_active_employee_position:
            update_employee_position(current_active_employee_position, employee)
        elif not current_active_employee_position and employee.get("date_dismissal"):
            current_non_active_employee_position = EmployeePosition.find_employee_position(False, current_employee, current_position, current_department, tabel_number)
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
    if not result_request_check.get("ok"):
        return result_request_check
    wb = load_workbook(filename=file)
    ws = wb[wb.sheetnames[0]]
    result_parse_file = parse_work_sheet(ws)
    if not result_parse_file.get("ok"):
        return result_parse_file
    data_result_parse = result_parse_file.get("result")
    employees: list = data_result_parse.get("employees")
    incorrect_employees: list = data_result_parse.get("incorrect_employees")
    departments_titles: set = data_result_parse.get("departments_titles")
    positions_titles: set = data_result_parse.get("positions_titles")
    update_organization_departments(organization_id, departments_titles)
    update_organization_positions(organization_id, positions_titles)
    result_update = update_organization_employee_positions(organization_id, employees)
    incorrect_employees.extend(result_update.get("data", []))
    columns = [{"field": "fio", "key": "fio", "title": "Работник", "align": "left", "width": 250}, {"field": "reason", "key": "reason", "title": 'Причины ошибки'}]
    result = {
        "colData": columns,
        "data": incorrect_employees,
    }
    return {"ok": True, "result": result, "message": ""}
