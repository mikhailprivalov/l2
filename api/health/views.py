from datetime import datetime, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from appconf.manager import SettingManager
from clients.models import Card, Individual
from slog.models import Log


@login_required
@staff_member_required
def log_stats(request):
    store_days = SettingManager.get("max_log_store_days", "120", "i")
    return JsonResponse(
        {
            "total": Log.objects.all().count(),
            "storeDays": store_days,
            "toDelete": Log.objects.filter(time__lt=datetime.today() - timedelta(days=store_days), type__in=Log.CLEANUP_TYPES_LOG).count(),
        }
    )


@login_required
@staff_member_required
def archive_cards_stats(request):
    objs = Card.objects.filter(napravleniya__isnull=True, is_archive=True)
    cnt = objs.count()
    return JsonResponse({"total": cnt})


@login_required
@staff_member_required
def patients_stats(request):
    objs = Individual.objects.filter(card__isnull=True)
    cnt = objs.count()
    return JsonResponse({"total": cnt})


@login_required
@staff_member_required
def log_cleanup(request):
    _, deleted = Log.objects.filter(time__lt=datetime.today() - timedelta(days=SettingManager.get("max_log_store_days", "120", "i")), type__in=Log.CLEANUP_TYPES_LOG).delete()
    return JsonResponse({"deleted": deleted.get("slog.Log", 0)})


@login_required
@staff_member_required
def archive_cards_cleanup(request):
    _, deleted = Card.objects.filter(napravleniya__isnull=True, is_archive=True).delete()
    return JsonResponse({"deleted": deleted.get("clients.Card", 0)})


@login_required
@staff_member_required
def patients_cleanup(request):
    _, deleted = Individual.objects.filter(card__isnull=True).delete()
    return JsonResponse({"deleted": deleted.get("clients.Individual", 0)})
