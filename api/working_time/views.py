import json
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, FileResponse
from openpyxl.workbook import Workbook

from employees.services.get_or_create_tabel import get_or_create_tabel_service
from forms.forms300 import form_01
from laboratory.decorators import group_required
from employees.models import Department, EmployeeWorkingHoursSchedule, TimeTrackingDocument, WorkDayStatus, EmployeePosition
from laboratory.settings import SHIFTS_VARIANTS


@login_required()
@group_required('График рабочего времени')
def get_departments(request):
    departments = Department.get_active()
    return JsonResponse({"result": departments})


@login_required()
@group_required('График рабочего времени')
def get_work_time(request):
    request_data = json.loads(request.body)
    result = EmployeeWorkingHoursSchedule.get_work_time_employee(request_data["year"], request_data["month"], request_data["departmentId"])
    return JsonResponse({"result": result})


@login_required()
@group_required('График рабочего времени')
def update_time(request):
    request_data = json.loads(request.body)
    department_id = request_data.get("departmentId")
    year = request_data.get("year")
    month = request_data.get("month")
    changed_employee_work_time = request_data.get("changedEmployeesWorkTime")
    result = EmployeeWorkingHoursSchedule.update_time(department_id, year, month, changed_employee_work_time)
    return JsonResponse(result)


@login_required()
@group_required('График рабочего времени')
def create_document(request):
    request_data = json.loads(request.body)
    doctor_profile = request.user.doctorprofile
    year = request_data.get("year")
    month = request_data.get("month")
    department_id = request_data.get("departmentId")
    TimeTrackingDocument.create_document(year, month, department_id, doctor_profile)
    return JsonResponse({"ok": True, "message": ""})


@login_required()
@group_required('График рабочего времени')
def get_ref_books(request):
    work_day_statuses = WorkDayStatus.get_workday_statuses(short=True)
    shifts_variants = SHIFTS_VARIANTS
    return JsonResponse({"workDayStatuses": work_day_statuses, "shiftsVariants": shifts_variants})


@login_required()
@group_required('График рабочего времени')
def employee_transfer(request):
    request_data = json.loads(request.body)
    employee_position_id = request_data.get("employeePositionId")
    date_transfer = request_data.get("date")
    result = EmployeePosition.employee_transfer(employee_position_id, date_transfer)
    return JsonResponse(result)


@login_required()
@group_required('График рабочего времени')
def get_work_time_filling_by_employee_template(request):
    request_data = json.loads(request.body)
    year = request_data.get("year")
    month = request_data.get("month")
    department_id = request_data.get("departmentId")
    action = request_data.get("action")
    result = EmployeeWorkingHoursSchedule.get_work_time_filling_by_employee_template(year, month, department_id, action)
    return JsonResponse({"result": result})


@login_required()
@group_required('График рабочего времени')
def edit_lunch(request):
    request_data = json.loads(request.body)
    employee_position_id = request_data.get("employeePositionId")
    lunch_duration_in_minutes = request_data.get("lunchDurationInMinutes")
    EmployeePosition.edit_lunch(employee_position_id, lunch_duration_in_minutes)
    return JsonResponse({"ok": True, "message": ""})

@login_required()
@group_required('График рабочего времени')
def get_or_create_tabel(request):
    request_data = request.GET
    year = int(request_data.get("year") or -1)
    month = int(request_data.get("month") or -1)
    department_id = int(request_data.get("departmentId") or -1)
    user = request.user
    result: Workbook = get_or_create_tabel_service(year, month, department_id, user)
    buffer = BytesIO()
    result.save(buffer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="Tabel.xlsx")
