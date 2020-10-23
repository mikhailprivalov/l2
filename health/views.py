from datetime import datetime, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse

import clients.models as clients
import directory.models as directory
from appconf.manager import SettingManager
from rmis_integration.client import Client
from slog.models import Log as slog


CLEANUP_TYPES_LOG = (
    1, 2, 3, 4, 5, 6, 10, 16, 17, 18, 19, 20, 25, 27, 22, 23, 100, 998, 999, 1001, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 3000, 3001, 5000, 6000, 10000, 20000, 60001, 60003
)


@login_required
@staff_member_required
def log(request):
    response = {"cnt": slog.objects.all().count(), "store_days": SettingManager.get("max_log_store_days", "120", "i")}
    response["to_delete"] = slog.objects.filter(
        time__lt=datetime.today() - timedelta(days=response["store_days"]),
        type__in=CLEANUP_TYPES_LOG
    ).count()
    return JsonResponse(response)


@login_required
@staff_member_required
def log_cleanup(request):
    _, cnt = (
        slog.objects.filter(
            time__lt=datetime.today() - timedelta(days=SettingManager.get("max_log_store_days", "120", "i")),
            type__in=CLEANUP_TYPES_LOG
        ).delete()
    )
    return HttpResponse(str(cnt.get("slog.Log", 0)), content_type="text/plain")


@login_required
@staff_member_required
def db(request):
    response = []
    return JsonResponse(response, safe=False)


@login_required
@staff_member_required
def rmis_check(request):
    c = Client()
    return HttpResponse(c.search_organization_id(check=True) + " " + c.search_dep_id(check=True), content_type="text/plain")


@login_required
@staff_member_required
def archive_without_directions(request):
    objs = clients.Card.objects.filter(napravleniya__isnull=True, is_archive=True)
    cnt = objs.count()
    if request.GET.get("remove", "0") == "1":
        _, cnt = objs.delete()
        cnt = cnt.get("clients.Card", 0)
    return HttpResponse(str(cnt), content_type="text/plain")


@login_required
@staff_member_required
def patients_without_cards(request):
    objs = clients.Individual.objects.filter(card__isnull=True)
    cnt = objs.count()
    if request.GET.get("remove", "0") == "1":
        _, cnt = objs.delete()
        cnt = cnt.get("clients.Individual", 0)
    return HttpResponse(str(cnt), content_type="text/plain")


@login_required
@staff_member_required
def sync_departments(request):
    c = Client()
    return HttpResponse("Добавлено: %s. Обновлено: %s." % c.department.sync_departments(), content_type="text/plain")


@login_required
@staff_member_required
def sync_researches(request):
    r = directory.Researches.objects.filter(podrazdeleniye__isnull=True, subgroup__isnull=False)
    cnt = r.count()
    for research in r:
        research.podrazdeleniye = research.subgroup.podrazdeleniye
        research.save()
    return HttpResponse(str(cnt), content_type="text/plain")
