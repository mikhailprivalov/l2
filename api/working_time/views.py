import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from employees.models import Department
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
    work_time = []
    return JsonResponse({"result": work_time})


@login_required()
@group_required('График рабочего времени')
def get_document(request):
    document = []
    return JsonResponse({"result": document})


@login_required()
@group_required('График рабочего времени')
def create_document(request):
    document = []
    if document:
        return status_response(True)
    return status_response(False)
