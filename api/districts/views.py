import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from api.districts.sql_func import get_district_limit_research
from clients.models import District
from laboratory.decorators import group_required
from users.models import DistrictResearchLimitAssign


@login_required
@group_required("Конструктор: Настройка организации")
def district_create(request):
    request_data = json.loads(request.body)
    district_title = request_data.get("district", "")
    if District.objects.filter(title__iexact=district_title).exists():
        return JsonResponse({'ok': False, 'message': 'Название уже существует'})
    d = District(title=district_title)
    d.save()
    return JsonResponse({'ok': True, 'message': f'Создан {district_title}'})


@login_required
@group_required("Конструктор: Настройка организации")
def districts_load(request):
    districts = District.objects.all().order_by("sort_weight")
    result = [{"pk": i.pk, "title": i.title, "is_ginekolog": i.is_ginekolog} for i in districts]
    return JsonResponse({"result": result})


@login_required
@group_required("Конструктор: Настройка организации")
def district_edit(request):
    request_data = json.loads(request.body)
    district_pk = int(request_data.get("pk", -1))
    district_limit = get_district_limit_research(district_pk)
    result = [{"count": i.limit_count, "type": 'День' if i.type_period_limit == 0 else 'Месяц', "current_researches": i.research_id} for i in district_limit]

    return JsonResponse({"result": result})


@login_required
@group_required("Конструктор: Настройка организации")
def district_save_limit(request):
    request_data = json.loads(request.body)
    tb_data = request_data.get('tb_data', '')
    district_pk = request_data.get('district', -1)
    for t_b in tb_data:
        if int(t_b.get('count', 0)) < 1:
            return JsonResponse({'message': 'Ошибка в количестве'})
    DistrictResearchLimitAssign.save_limit_assign(district_pk, tb_data)

    return JsonResponse({'ok': True, 'message': 'Сохранено'})
