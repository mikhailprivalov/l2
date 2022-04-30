import simplejson as json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import slog.models as slog
from researches.models import Tubes


@login_required
def get_all_tubes(request):
    """Получение списка пробирок"""
    res = []
    tubes = Tubes.objects.all().order_by('title')
    for v in tubes:
        res.append({"id": v.id, "title": v.title, "short_title": v.short_title, "color": v.color})
    return JsonResponse(res, safe=False)


@csrf_exempt
@login_required
def tubes_control(request):
    """Создание новых и настройка существующих пробирок"""
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
        new_tube = Tubes(title=title, color=color, short_title=request.PUT.get("short_title", ""))
        new_tube.save()
        slog.Log(
            key=str(new_tube.pk),
            user=request.user.doctorprofile,
            type=1,
            body=json.dumps({"data": {"title": request.POST["title"], "color": request.POST["color"], "code": request.POST.get("code", "")}}),
        ).save()
    if request.method == "POST":
        id = int(request.POST["id"])
        title = request.POST["title"]
        color = "#" + request.POST["color"]
        tube = Tubes.objects.get(id=id)
        tube.color = color
        tube.title = title
        tube.short_title = request.POST.get("code", "")
        tube.save()
        slog.Log(
            key=str(tube.pk),
            user=request.user.doctorprofile,
            type=2,
            body=json.dumps({"data": {"title": request.POST["title"], "color": request.POST["color"], "code": request.POST.get("code", "")}}),
        ).save()
    return JsonResponse({})


@csrf_exempt
@login_required
def tubes_relation(request):
    """Создание связи пробирка-фракция"""
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
        slog.Log(key=str(relation.pk), user=request.user.doctorprofile, type=20, body=json.dumps({"data": {"id": tube_id}})).save()
    return JsonResponse(return_result)
