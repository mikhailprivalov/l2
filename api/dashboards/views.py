import json
import logging

from django.http import JsonResponse

from dashboards.models import Dashboard
from dashboards.views import exec_query, get_dashboard


logger = logging.getLogger(__name__)


def dashboard_list(request):
    result = get_dashboard()
    return JsonResponse({'rows': result})


def dashboard_charts(request):
    request_data = json.loads(request.body)
    dashboard_pk = request_data.get("dashboard", -1)

    try:
        result = exec_query(dashboard_pk)
    except Exception as e:
        logger.exception(e)
        return JsonResponse({"ok": False})

    dash = Dashboard.objects.get(pk=dashboard_pk)
    return JsonResponse({'rows': result, "ok": True, "intervalReloadSeconds": dash.interval_reload_seconds})
