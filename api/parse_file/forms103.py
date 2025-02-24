from typing import Union

from openpyxl.reader.excel import load_workbook

from hospitals.models import Hospitals


def check_need_col(cols: list, need_cols: set):
    other_need_cols = set(set(cols) - need_cols)
    if len(other_need_cols) + len(need_cols) != len(cols):
        return False
    return True


def normalize_employee_data(employment_form, snils, tabel_number, employee_fio, department_title, position_title, rate, date_employment, date_dismissal):
    return {}


def validate_employee_data(normalized_employee_data):
    return {}


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
            employment_form = cells[employment_form_idx].strip()
            snils = cells[snils_idx].strip()
            tabel_number = cells[tabel_number_idx].strip()
            employee_fio = cells[employee_fio_idx].strip()
            department_title = cells[department_title_idx].strip()
            position_title = cells[position_title_idx].strip()
            rate = cells[rate_idx].strip()
            date_employment = cells[date_employment_idx].strip()
            date_dismissal = cells[date_dismissal_idx].strip()

            normalized_employee_data = normalize_employee_data(employment_form, snils, tabel_number, employee_fio, department_title, position_title, rate, date_employment, date_dismissal)
            validation_result = validate_employee_data(normalized_employee_data)

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
