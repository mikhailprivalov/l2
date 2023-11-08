from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from laboratory.decorators import group_required


@login_required()
@group_required('График рабочего времени')
def get_columns(request):
    print('ура!')
    return JsonResponse({"result": []})
