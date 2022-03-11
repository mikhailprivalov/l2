import json

from dashboards.views import exec_query, get_dashboard
from laboratory.decorators import group_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


@login_required
@group_required("Просмотр мониторингов")
def dashboard(request):
    result = get_dashboard()
    return JsonResponse({'rows': result})


@login_required
@group_required("Просмотр мониторингов")
def dashboard_charts(request):
    request_data = json.loads(request.body)
    dashboard_pk = request_data["dashboard"]
    result = exec_query(dashboard_pk)

    return JsonResponse({'rows': result})

