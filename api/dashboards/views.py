import json
import logging

from dashboards.views import exec_query, get_dashboard
from laboratory.decorators import group_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


logger = logging.getLogger(__name__)


@login_required
@group_required("Просмотр графиков статистики")
def dashboard_list(request):
    result = get_dashboard()
    return JsonResponse({'rows': result})


@login_required
@group_required("Просмотр графиков статистики")
def dashboard_charts(request):
    request_data = json.loads(request.body)
    dashboard_pk = request_data["dashboard"]

    try:
        result = exec_query(dashboard_pk)
    except Exception as e:
        logger.exception(e)
        return JsonResponse({"ok": False})

    return JsonResponse({'rows': result, "ok": True})
