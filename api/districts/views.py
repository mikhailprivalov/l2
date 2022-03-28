import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from api.districts.sql_func import get_district_limit_research
from clients.models import District


@login_required
def district_create(request):
    pass


@login_required
def districts_load(request):
    districts = District.objects.all().order_by("sort_weight")
    result = [{"pk": i.pk, "title": i.title, "is_ginekolog": i.is_ginekolog} for i in districts]
    return JsonResponse({"result": result})


@login_required
def district_edit(request):
    request_data = json.loads(request.body)
    district_pk = int(request_data.get("pk", -1))
    district_limit = get_district_limit_research(district_pk)
    result = [{"limit_count": i.limit_count, "type_period_limit": i.type_period_limit, "researches_id": i.researches_id} for i in district_limit]

    return JsonResponse({"result": result})
