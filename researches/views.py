from django.core import serializers
from django.http import HttpResponse
from researches.models import Researches, Subgroups, Podrazdeleniya
from directions.models import Issledovaniya
import simplejson as json
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required

@cache_page(60 * 15)
@login_required
def ajax_search_res(request):
    """Получение исследований в лаборатории"""
    res = []
    if request.method == 'GET':
        id = int(request.GET['lab_id'])  # Идентификатор лаборатории
        if id and id >= 0:  # Проверка корректности id
            groups = Subgroups.objects.filter(
                podrazdeleniye=Podrazdeleniya.objects.get(pk=id))  # Получение всех групп для этой лаборатории
            for v in groups:  # Перебор групп
                tmp = Researches.objects.filter(subgroup_lab=v.pk, hide=0)  # Выборка исследований по id лаборатории
                for val in tmp:
                    res.append({"pk": val.pk, "fields": {"id_lab_fk": id,
                                                         "ref_title": val.ref_title}})  # Добавление исследований к ответу сервера
    return HttpResponse(json.dumps(res), content_type="application/json")  # Создание JSON


@login_required
def researches_get_one(request):
    res = {"res_id": "", "title": "", "fractions": []}
    if request.method == "GET":
        id = request.GET["id"]
        iss = Issledovaniya.objects.get(pk=id).issledovaniye
        fractions = iss.ref_fractions
        res["res_id"] = id
        res["title"] = iss.ref_title
        for key, val in enumerate(fractions):
            res["fractions"].append(
                {"title": val, "unit": iss.ref_units[key], "references": {"m": iss.ref_m[key], "f": iss.ref_f[key]}})

    return HttpResponse(json.dumps(res), content_type="application/json")  # Создание JSON
