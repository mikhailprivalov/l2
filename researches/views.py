from django.core import serializers
from django.http import HttpResponse
from researches.models import Researches, Subgroups, Podrazdeleniya, Tubes
from directions.models import Issledovaniya
import simplejson as json
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import directory.models as directory
import slog.models as slog


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
    """Получение исследования (название, фракции, параметры)"""

    res_o = {"res_id": "", "title": "", "fractions": {}, "confirmed": True, "saved": True, "can_comment": False, "cached": False}
    from copy import deepcopy

    if request.method == "GET":
        multi = request.GET.get("multi", "false") == "true"
        id = request.GET["id"]
        if not multi:
            id = "[%s]" % id
        id = json.loads(id)
        isresearch = request.GET.get("isresearch", "false") == "true"
        a = []
        for i in id:
            res = deepcopy(res_o)
            res["cached"] = request.GET.get("cached", "false") != "false"
            iss = None
            if not isresearch:
                iss = Issledovaniya.objects.get(pk=i)
                res["res_id"] = i
                if not iss.doc_save:
                    res["saved"] = False
                if not iss.doc_confirmation:
                    res["confirmed"] = False

            if not res["cached"]:
                if not isresearch:
                    research = iss.research
                else:
                    research = directory.Researches.objects.get(pk=i)
                fractions = directory.Fractions.objects.filter(research=research).order_by("pk", "sort_weight")
                res["title"] = research.title
                res["i"] = i
                res["can_comment"] = research.can_lab_result_comment
                for val in fractions:
                    ref_m = val.ref_m
                    ref_f = val.ref_f
                    if isinstance(ref_m, str):
                        ref_m = json.loads(ref_m)
                    if isinstance(ref_f, str):
                        ref_f = json.loads(ref_f)
                    av = {}
                    for avref in directory.References.objects.filter(fraction=val):
                        av[avref.pk] = {
                            "title": avref.title,
                            "about": avref.about,
                            "m": json.loads(avref.ref_m) if isinstance(avref.ref_m, str) else avref.ref_m,
                            "f": json.loads(avref.ref_f) if isinstance(avref.ref_f, str) else avref.ref_f,

                        }

                    tmp = {"title": val.title,
                           "pk": val.pk,
                           "unit": val.units,
                           "hide": val.hide,
                           "render_type": val.render_type,
                           "options": val.options.split(","),
                           "type": val.type,
                           "references": {
                               "m": ref_m,
                               "f": ref_f,
                               "default": -1 if not val.default_ref else val.default_ref.pk,
                               "available": av,
                                          },
                           "num": val.sort_weight,
                           "formula": val.formula}
                    if val.sort_weight and val.sort_weight > 0:
                        res["fractions"][val.sort_weight] = tmp
                    else:
                        res["fractions"][val.pk] = tmp
            a.append(res)
        if multi:
            return HttpResponse(json.dumps(a))
        elif len(a) > 0:
            return HttpResponse(json.dumps(a[0]))

    return HttpResponse(json.dumps(res_o))  # Создание JSON


@login_required
def get_all_tubes(request):
    """Получение списка пробирок"""
    res = []
    tubes = Tubes.objects.all().order_by('title')
    for v in tubes:
        res.append({"id": v.id, "title": v.title, "color": v.color})
    return HttpResponse(json.dumps(res), content_type="application/json")  # Создание JSON


@csrf_exempt
@login_required
def tubes_control(request):
    """ Создание новых и настройка существующих пробирок """
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
        slog.Log(key=str(new_tube.pk), user=request.user.doctorprofile, type=1,
                 body=json.dumps({"data": {"title": request.POST["title"], "color": request.POST["color"]}})).save()
    if request.method == "POST":
        id = int(request.POST["id"])
        title = request.POST["title"]
        color = "#" + request.POST["color"]
        tube = Tubes.objects.get(id=id)
        tube.color = color
        tube.title = title
        tube.save()
        slog.Log(key=str(tube.pk), user=request.user.doctorprofile, type=2,
                 body=json.dumps({"data": {"title": request.POST["title"], "color": request.POST["color"]}})).save()
    return HttpResponse(json.dumps({}), content_type="application/json")  # Создание JSON


@csrf_exempt
@login_required
def tubes_relation(request):
    """ Создание связи пробирка-фракция """
    return_result = {}
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

        tube_id = request.PUT["id"]
        tube = Tubes.objects.get(id=tube_id)
        from directory.models import ReleationsFT

        relation = ReleationsFT(tube=tube)
        relation.save()
        return_result["id"] = relation.pk
        return_result["title"] = tube.title
        return_result["color"] = tube.color
        slog.Log(key=str(relation.pk), user=request.user.doctorprofile, type=20,
                 body=json.dumps({"data": {"id": tube_id}})).save()
    return HttpResponse(json.dumps(return_result), content_type="application/json")  # Создание JSON
