import json
from dashboards.models import DashboardCharts
from laboratory.decorators import group_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from laboratory.utils import current_time, strfdatetime


@login_required
@group_required("Просмотр мониторингов")
def get_dashboard(request):
    request_data = json.loads(request.body)
    dashboard_pk = request_data["dashboard"]

    date_start = request_data["date"]
    date_end = request_data.get("date_end", "")
    if not date_end:
        date_end = date_start
    charts_objs = DashboardCharts.objects.filter(dashboard__pk=dashboard_pk, hide=False)

    default_charts = []

    return JsonResponse({'rows': ''})
