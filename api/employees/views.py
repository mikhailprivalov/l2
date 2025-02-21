from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from laboratory.decorators import group_required


@login_required
@group_required("Конструктор: Настройка организации")
def get_ref_books(request):
    result = {"departments": [], "positions": [], "employmentForms": []}
    return JsonResponse({"result": result})
