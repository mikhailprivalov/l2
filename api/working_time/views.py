import base64
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, FileResponse

from forms.forms300 import form_01
from laboratory.decorators import group_required
from employees.models import Department, EmployeeWorkingHoursSchedule, TimeTrackingDocument, WorkDayStatus


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
    result = WorkDayStatus.get_workday_statuses(short=True)
    return JsonResponse({"result": result})


@login_required()
@group_required('График рабочего времени')
def print_document(request):
    request_data = json.loads(request.body)
    employees_work_time = request_data.get("employeesWorkTime")
    result_bytes = form_01(request_data={"employeesWorkTime": employees_work_time})
    base64_encoded = base64.b64encode(result_bytes)
    base64_string = base64_encoded.decode('utf-8')
    return JsonResponse({"result": base64_string})
    # response = HttpResponse(content_type='application/pdf')
    # response['Content-Disposition'] = 'inline; filename="form-' + 'document' + '.pdf"'
    # response.write(form_01(request_data={"employeesWorkTime": employees_work_time}))

    # return response
    # result_bytes = form_01(request_data={"employeesWorkTime": employees_work_time})
