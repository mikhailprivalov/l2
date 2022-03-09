import json

from dashboards.sql_func import get_charts_dataset, execute_select
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


    return JsonResponse({'rows': ''})


def exec_query(dashboard_pk):
    # data_chart = {"chart_id": [{"chart_title": "", "chart_type": "", "database": "", "user": "", "password": "", "address": "", "port": "", "query": "", sql_param: ""}]}
    data_chart = {}
    metadata_charts = get_charts_dataset(dashboard_pk)
    for md in metadata_charts:
        if not data_chart.get(md.chart_id):
            data_chart[md.chart_id] = [
                {"chart_title": md.chart_title, "chart_type": md.chart_type, "database": md.database, "user": md.login, "password": md.password, "address": md.ip_address,
                 "port": md.port, "query": md.sql_query, "sql_param": md.sql_columns_settings}]
        else:
            temp_data_chart = data_chart.get(md.chart_id, None)
            temp_data_chart.append({"chart_title": md.chart_title, "chart_type": md.chart_type, "database": md.database, "user": md.login, "password": md.password, "address": md.ip_address,
                 "port": md.port, "query": md.sql_query, "sql_param": md.sql_columns_settings})
            data_chart[md.chart_id] = temp_data_chart.copy()

    for k, v in data_chart.items():
        for ds in v:
            r = execute_select(ds['database'], ds['user'], ds['password'], ds['address'], ds['port'], ds['query'])
