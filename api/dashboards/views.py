import json

from dashboards.views import exec_query
from laboratory.decorators import group_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


@login_required
@group_required("Просмотр мониторингов")
def get_dashboard(request):
    request_data = json.loads(request.body)
    dashboard_pk = request_data["dashboard"]

    date_start = request_data["date"]
    date_end = request_data.get("date_end", "")
    if not date_end:
        date_end = date_start

    result = exec_query(dashboard_pk)

    return JsonResponse({'rows': result})
