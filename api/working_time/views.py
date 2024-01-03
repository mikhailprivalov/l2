import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from employees.models import Department, EmployeeWorkTime, WorkTimeDocument
from laboratory.decorators import group_required
from utils.response import status_response


@login_required()
@group_required('График рабочего времени')
def get_departments(request):
    departments = Department.get_active_labels()
    return JsonResponse({"result": departments})


@login_required()
@group_required('График рабочего времени')
def get_work_time(request):
    request_data = json.loads(request.body)
    work_time = EmployeeWorkTime.get_work_time(request_data["year"], request_data["month"], request_data["department"])
    return JsonResponse({"result": work_time})


@login_required()
@group_required('График рабочего времени')
def get_document(request):
    request_data = json.loads(request.body)
    document = WorkTimeDocument.get_document(request_data["year"], request_data["month"], request_data["department"])
    return status_response(document)

@login_required()
@group_required('График рабочего времени')
def create_document(request):
    request_data = json.loads(request.body)
    document = WorkTimeDocument.create_document(request_data["year"], request_data["month"], request_data["department"])
    if document:
        return status_response(True)
    return status_response(False)
