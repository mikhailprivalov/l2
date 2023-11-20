from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from employees.models import Department
from laboratory.decorators import group_required


@login_required()
@group_required('График рабочего времени')
def get_departments(request):
    departments = Department.get_active_labels()
    return JsonResponse({"result": departments})


