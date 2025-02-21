import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from hospitals.models import Hospitals
from laboratory.decorators import group_required
from employees.models import Department, Position, TypeWorkTimeEmployee


@login_required
@group_required("Конструктор: Настройка организации")
def get_organizations(request):
    user = request.user
    user_is_admin = user.is_superuser
    user_hospital_id = user.doctorprofile.hospital_id
    groups_user = [str(x) for x in request.user.groups.all()]
    if "Конструктор: Настройка всех организаций" in groups_user or user_is_admin:
        organizations = Hospitals.get_hospitals()
    else:
        organizations = Hospitals.get_hospitals(user_hospital_id)
    return JsonResponse({"result": organizations})


@login_required
@group_required("Конструктор: Настройка организации")
def get_ref_books(request):
    request_data = json.loads(request.body)
    organization_id = request_data["organizationId"]
    departments = Department.get_active(organization_id)
    positions = Position.get_active(organization_id)
    employment_forms = TypeWorkTimeEmployee.get_active()
    result = {"departments": departments, "positions": positions, "employmentForms": employment_forms}
    return JsonResponse({"result": result})


@login_required
@group_required("Конструктор: Настройка организации")
def get_employees(request):
    request_data = json.loads(request.body)
    print(request_data)
    result = []
    return JsonResponse({"result": result})
