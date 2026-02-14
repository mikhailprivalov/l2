import calendar
import datetime
import openpyxl
from openpyxl import Workbook

from employees.models import Employee, EmployeePosition, TabelDocument, TimeTrackingDocument
from employees.sql_func import get_employee_work_time
from users.models import DoctorProfile


def get_or_create_tabel_service(year: int, month: int, department_id: int, user):
    result_validate_user = validate_user(department_id, user)
    if not result_validate_user.get("ok"):
        return create_xlsx_tabel(error_data=result_validate_user)
    first_date_month = datetime.date(year, month, 1)
    length_month = calendar.monthrange(year, month)[1]
    last_date_month = datetime.date(year, month, length_month)

    time_tracking_document = TimeTrackingDocument.get_document(first_date_month, last_date_month, department_id)
    work_time_employee = get_employee_work_time(department_id, time_tracking_document.id, str(first_date_month))
    convert_to_tabel_data(work_time_employee)

    tabel_document = TabelDocument.get_tabel(first_date_month, last_date_month, department_id)

    if tabel_document:
        #  TODO сравниваем данные графика и табеля, если есть отличия, то создаем новую версию tabelDocument, FactTimeWork-s, TabelData
        pass
    else:
        #  TODO Создаем новые TabelDocument, FactTimeWork-s, TabelData
        pass

    xlsx_tabel: Workbook = create_xlsx_tabel()
    return xlsx_tabel


def validate_user(department_id, user):
    user_is_admin = user.is_superuser
    user_has_group = user.groups.filter(name="График рабочего времени: все табели").exists()
    doctor_profile: DoctorProfile = user.doctorprofile
    employee: Employee = Employee.objects.filter(snils=doctor_profile.snils).first()
    if not employee:
        return {"ok": False, "message": "Работник не найден"}
    employee_position: EmployeePosition = EmployeePosition.objects.filter(employee_id=employee.pk).first()
    if not employee_position:
        return {"ok": False, "message": "Трудовой договор (табельный номер) не найден"}
    if not user_is_admin and not user_has_group and employee_position.department_id != department_id:
        return {"ok": False, "message": "Нет доступа"}
    return {"ok": True, "message": ""}


def convert_to_tabel_data(work_time_employee):
    employee_positions_data = {}
    for work_time in work_time_employee:
        if not employee_positions_data.get(work_time.employee_position_id):
            employee_positions_data[work_time.employee_position_id] = {
                "snils": work_time.snils,
                "person_family": work_time.family,
                "person_name": work_time.name,
                "person_patronymic": work_time.patronymic,
                "work_hours": {
                    "position_name": work_time.position_name,
                    "bid_name": work_time.bid_name,
                    "department_name": work_time.department_name,
                    "tabel_number": work_time.tabel_number,
                    "days": {},
                },
            }
        if work_time.day:
            # TODO Надо конвертировать диапозон часов (start, end time) в кол-во часов (night_hours, common_hours)
            employee_positions_data[work_time.employee_position_id]["work_hours"]["days"][work_time.day] = {
                "status": work_time.work_day_status_id,  # TODO здесь из таблицы в БД, в табеле ожидается из Choices, надо превращать
                "night_hours": "",
                "common_hours": "",
            }

    person_data_grouped_by_snils = {}
    for employee_position in employee_positions_data.values():
        snils = employee_position["snils"]
        if not person_data_grouped_by_snils.get(snils):
            person_data_grouped_by_snils[snils] = {
                "snils": snils,
                "person_family": employee_position["person_family"],
                "person_name": employee_position["person_name"],
                "person_patronymic": employee_position["person_patronymic"],
                "work_hours": [],
            }
        person_data_grouped_by_snils[snils]["work_hours"].append(employee_position["work_hours"])

    person_data = [value for value in person_data_grouped_by_snils.values()]

    return person_data


def create_xlsx_tabel(error_data=None):
    work_book: Workbook = openpyxl.Workbook()
    work_book.remove(work_book.get_sheet_by_name("Sheet"))
    work_sheet = work_book.create_sheet("Табель")
    if error_data:
        work_sheet.append(["Ошибка", error_data.get("message")])
        return work_book
    work_sheet.append(["Привет, мир!"])
    return work_book
