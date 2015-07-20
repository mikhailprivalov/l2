from django.core import serializers
from django.http import HttpResponse
from researches.models import Researches, Subgroups, Podrazdeleniya, Tubes
from directions.models import Issledovaniya
import simplejson as json
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt


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


@login_required
def get_all_tubes(request):
    res = []
    tubes = Tubes.objects.all().order_by('title')
    for v in tubes:
        res.append({"id": v.id, "title": v.title, "color": v.color})
    return HttpResponse(json.dumps(res), content_type="application/json")  # Создание JSON


@csrf_exempt
@login_required
def tubes_control(request):
    if request.method == "PUT":
        if hasattr(request, '_post'):
            del request._post
            del request._files

        try:
            request.method = "POST"
            request._load_post_and_files()
            request.method = "PUT"
        except AttributeError:
            request.META['REQUEST_METHOD'] = 'POST'
            request._load_post_and_files()
            request.META['REQUEST_METHOD'] = 'PUT'

        request.PUT = request.POST

        title = request.PUT["title"]
        color = "#" + request.PUT["color"]
        new_tube = Tubes(title=title, color=color)
        new_tube.save()

    if request.method == "POST":
        id = int(request.POST["id"])
        title = request.POST["title"]
        color = "#" + request.POST["color"]
        tube = Tubes.objects.get(id=id)
        tube.color = color
        tube.title = title
        tube.save()
    return HttpResponse(json.dumps({}), content_type="application/json")  # Создание JSON
