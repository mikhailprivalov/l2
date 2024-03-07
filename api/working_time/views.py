from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from laboratory.decorators import group_required
from employees.models import Department


@login_required()
@group_required('График рабочего времени')
def get_departments(request):
    departments = Department.get_active()
    return JsonResponse({"result": departments})
