from django.contrib.auth.decorators import login_required

from hospitals.models import Hospitals
from laboratory.decorators import group_required
from django.http import JsonResponse


@login_required
@group_required('Конструктор: настройка внешних исполнителей')
def external_performer(request):
    result = Hospitals.get_is_external_performing_organization()
    return JsonResponse({"data": result})
