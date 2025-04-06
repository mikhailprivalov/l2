import json
import time

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from laboratory.decorators import group_required
from employees.models import Department, EmployeeWorkingHoursSchedule, TimeTrackingDocument


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
    start_work = request_data["startWork"]
    end_work = request_data["endWork"]
    type_work = request_data["type"]
    employee_position_id = request_data["employeePositionId"]
    date = request_data["date"]
    result = EmployeeWorkingHoursSchedule.update_time(start_work, end_work, type_work, employee_position_id, date)
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
    result = {"ok": True, "message": ""}
    return JsonResponse(result)

