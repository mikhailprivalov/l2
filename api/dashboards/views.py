import json
import logging

import pickle
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from laboratory import VERSION
from laboratory.settings import DASHBOARD_CHARTS_CACHE_TIME_SEC
from laboratory.decorators import group_required
from dashboards.views import exec_query, get_dashboard


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
        key = f'dashboard-charts:{dashboard_pk}:{VERSION}'
        result = cache.get(key)
        if not result:
            result = exec_query(dashboard_pk)
            if DASHBOARD_CHARTS_CACHE_TIME_SEC > 0:
                cache.set(key, pickle.dumps(result, protocol=4), DASHBOARD_CHARTS_CACHE_TIME_SEC)
        else:
            result = pickle.loads(result, encoding="utf8")
    except Exception as e:
        logger.exception(e)
        return JsonResponse({"ok": False})

    return JsonResponse({'rows': result, "ok": True})
