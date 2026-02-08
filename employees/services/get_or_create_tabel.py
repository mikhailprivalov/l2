import datetime

import openpyxl
from openpyxl import Workbook

from employees.models import Employee, EmployeePosition, TabelDocument, EmployeeWorkingHoursSchedule
from users.models import DoctorProfile


def get_or_create_tabel_service(year, month, department_id, user):
    result_validate_user = validate_user(department_id, user)
    if not result_validate_user.get("ok"):
        return create_xlsx_tabel(error_data=result_validate_user)
    tabel_document = TabelDocument.get_tabel(int(year), int(month), department_id)
    # work_time_employee = EmployeeWorkingHoursSchedule.get_work_time_employee(year, month, department_id)
    # work_time_employee_data = work_time_employee.get("data") or []
    # first_date_month = datetime.date(year, month, 1)
    if tabel_document:
        # TODO сравниваем данные графика и табеля, если есть отличия, то создаем новую версию tabelDocument, FactTimeWork-s, TabelData
        pass
    else:
        # TODO Создаем новые TabelDocument, FactTimeWork-s, TabelData
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


def create_xlsx_tabel(error_data = None):
    work_book: Workbook = openpyxl.Workbook()
    work_book.remove(work_book.get_sheet_by_name("Sheet"))
    work_sheet = work_book.create_sheet("Табель")
    if error_data:
        work_sheet.append(["Ошибка", error_data.get("message")])
        return work_book
    work_sheet.append(["Привет, мир!"])
    return work_book
