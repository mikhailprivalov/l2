from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from laboratory.decorators import group_required
from employees.models import Department


@login_required
@group_required("Конструктор: Настройка организации")
def get_ref_books(request):
    user_hospital = request.user.hospital_id
    print(user_hospital)
    # departments = Department
    result = {"": [], "departments": [], "positions": [], "employmentForms": []}
    return JsonResponse({"result": result})
