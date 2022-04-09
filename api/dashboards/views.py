import json
import logging

from dateutil.relativedelta import relativedelta
from django.http import JsonResponse

from dashboards.models import Dashboard
from dashboards.views import exec_query, get_dashboard
from laboratory.utils import current_time, str_date

logger = logging.getLogger(__name__)


def dashboard_list(request):
    result = get_dashboard()
    return JsonResponse({'rows': result})


def dashboard_charts(request):
    request_data = json.loads(request.body)
    dashboard_pk = request_data.get("dashboard", -1)

    period_type = request_data.get("period_type", None)
    period_duration = request_data.get("period_duration", 0)

    date_end = request_data.get("date_end", None)
    date_start = request_data.get("date_start", None)
    if date_end and date_end:
        try:
            date_end = str_date(date_end)
        except Exception as e:
            logger.exception(e)
            date_end = None
        try:
            date_start = str_date(date_start, indicator="min")
        except Exception as e:
            logger.exception(e)
            date_start = None

    elif period_type:
        years, months, weeks, days = 0, 0, 0, 0
        if period_type == "y" and period_duration > 0 and period_duration < 2:
            years = -period_duration
        elif period_type == "m" and period_duration > 0 and period_duration < 13:
            months = -period_duration
        elif period_type == "w" and period_duration > 0 and period_duration < 50:
            weeks = -period_duration
        elif period_type == "d" and period_duration > 0 and period_duration < 65:
            days = -period_duration

        date_end = current_time()
        date_start = date_end + relativedelta(years=years, months=months, weeks=weeks, days=days)
    if date_end and date_start:
        d = date_end - date_start
        if d.days > 380:
            date_end = None
            date_start = None
    try:
        result = exec_query(dashboard_pk, {"date_start": date_start, "date_end": date_end})
    except Exception as e:
        logger.exception(e)
        return JsonResponse({"ok": False})

    dash = Dashboard.objects.get(pk=dashboard_pk)
    return JsonResponse({'rows': result, "ok": True, "intervalReloadSeconds": dash.interval_reload_seconds})
