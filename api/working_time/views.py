import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from laboratory.decorators import group_required
from employees.models import Department, EmployeeWorkingHoursSchedule, TimeTrackingDocument, WorkDayStatus, EmployeePosition, TabelDocument, FactTimeWork
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
    FactTimeWork.update_time(department_id, year, month, changed_employee_work_time)
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
