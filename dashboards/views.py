import json
from dateutil.relativedelta import relativedelta

from appconf.manager import SettingManager
from dashboards.models import Dashboard
from dashboards.sql_func import get_charts_dataset, execute_select
from laboratory.utils import current_time, str_date
from utils.dates import normalize_date


def get_dashboard():
    return [{"label": dashboard.title, "id": dashboard.pk} for dashboard in Dashboard.objects.filter(hide=False).order_by('-order')]


def exec_query(dashboard_pk, dates_param):
    show_dates_param = False
    # data_chart = {"chart_id": [{"chart_title": "", "chart_type": "", "database": "", "user": "", "password": "", "address": "", "port": "", "query": "", sql_param: ""}]}
    result = []
    data_chart = {}
    metadata_charts = get_charts_dataset(dashboard_pk)
    # обход по графикам датасетов
    for md in metadata_charts:
        if not data_chart.get(md.chart_id):
            data_chart[md.chart_id] = [
                {
                    "chart_title": md.chart_title,
                    "chart_type": md.chart_type,
                    "database": md.database,
                    "user": md.login,
                    "password": md.password,
                    "address": md.ip_address,
                    "port": md.port,
                    "query": md.sql_query,
                    "sql_param": md.sql_columns_settings,
                    "chart_order": md.chart_order,
                    "field_title": md.field_title,
                }
            ]
        else:
            temp_data_chart = data_chart.get(md.chart_id, None)
            temp_data_chart.append(
                {
                    "chart_title": md.chart_title,
                    "chart_type": md.chart_type,
                    "database": md.database,
                    "user": md.login,
                    "password": md.password,
                    "address": md.ip_address,
                    "port": md.port,
                    "query": md.sql_query,
                    "sql_param": md.sql_columns_settings,
                    "chart_order": md.chart_order,
                    "field_title": md.field_title,
                }
            )
            data_chart[md.chart_id] = temp_data_chart.copy()

    tmp_chart = {
        "title": "",
        "type": "",
        "pk": "",
        "chart_order": -1,
        "availableTypes": ["BAR", "COLUMN", "PIE", "LINE", "TABLE"],
        "isFullWidth": False,
        "dates": [],
        "fields": [],
        "columnTotal": [],
    }
    # обход по графикам в дашборде
    for k, v in data_chart.items():
        global_dates = set()
        step = 0
        # обход датасетов в графике
        for datachart in v:
            if step == 0:
                tmp_chart["title"] = datachart['chart_title']
                tmp_chart["pk"] = k
                tmp_chart["chart_order"] = datachart['chart_order']
                tmp_chart["type"] = datachart['chart_type']
                tmp_chart["data"] = []
                tmp_chart["fields"] = [datachart["field_title"]]
            sql_param = json.loads(datachart['sql_param'])
            tmp_data = {}
            # возвращаемые параметры в sql - запросе по типу value, date
            for param, attr in sql_param.items():
                for key, val in attr.items():
                    if key == "value":
                        tmp_data[param] = "value"
                    elif key == "date":
                        tmp_data[param] = "date"
            dash_with_param = SettingManager.get("dash_with_param", default='False', default_type='b')
            if not dash_with_param:
                r = execute_select(datachart['database'], datachart['user'], datachart['password'], datachart['address'], datachart['port'], datachart['query'])
            else:
                dates_server = sql_param.get("between", {})
                if "@date_start" in datachart['query']:
                    show_dates_param = True
                query_result = cast_dates(dates_server, dates_param, datachart['query'])
                r = execute_select(datachart['database'], datachart['user'], datachart['password'], datachart['address'], datachart['port'], query_result)
            values = []
            dates = []
            for tmp_dict in r:
                for current_key in tmp_data.keys():
                    if tmp_data[current_key] == 'value':
                        values.append(tmp_dict[current_key])
                    else:
                        dates.append(tmp_dict[current_key])
                        global_dates.add(tmp_dict[current_key])
            tmp_data = tmp_chart.get("data", [])
            tmp_data.append({"tmp_values": values.copy(), "dates": dates.copy()})
            tmp_chart["data"] = tmp_data.copy()

            tmp_fields = tmp_chart.get("fields", [])
            if datachart["field_title"] not in tmp_fields:
                tmp_fields.append(datachart["field_title"])
            tmp_chart["fields"] = tmp_fields.copy()
            step += 1
        tmp_chart["dates"] = sorted(global_dates.copy())
        result.append(tmp_chart.copy())
    for row in result:
        dates = row.get("dates", "")
        row_data = row.get("data", "")
        for i in row_data:
            values = ['' for k in dates]
            for d in i["dates"]:
                index_el = dates.index(d)
                tmp_index = i["dates"].index(d)
                current_result_el = i['tmp_values'][tmp_index]
                values[index_el] = current_result_el
            i["values"] = values.copy()

    for row in result:
        if row["type"] == "PIE":
            row_data = row.get("data", [])
            if len(row_data) > 1:
                dates = row.get("dates", "")
                fields = row.get("fields", "")
                title = row.get("title", "")
                final_row_data = row_data[0]
                step = 0
                for i in row_data:
                    step += 1
                    if step == 1:
                        continue
                    final_row_data['values'].append(i['values'][0])
                row["data"] = [final_row_data]
                row["dates"] = fields
                row["title"] = f"{title} за {dates[0]}"

    return {"result": result, "show_dates_param": show_dates_param}


def cast_dates(default_dates, dates_param, query_data):
    date_start, date_end = None, None
    if dates_param.get("date_start", None) and dates_param.get("date_end", None):
        date_start = dates_param["date_start"].strftime("%Y-%m-%d %H:%M:%S")
        date_end = dates_param["date_end"].strftime("%Y-%m-%d %H:%M:%S")
    elif default_dates.get("date_start", None) and default_dates.get("date_end", None):
        date_start = cast_sql_syntax_dates(default_dates["date_start"], "min")
        date_end = cast_sql_syntax_dates(default_dates["date_end"], "max")
    if date_start and date_end:
        query_data = query_data.replace("@date_start", f"'{date_start}'")
        query_data = query_data.replace("@date_end", f"'{date_end}'")
    return query_data


def cast_sql_syntax_dates(params, indicator):
    date = None
    if "current_date" in params.lower():
        current_date = current_time()
        if "interval" in params.lower():
            interval = params.split("interval")
            period = interval[1].replace("'", "")
            period = period.strip().split(" ")
            period_duration = int(period[0])
            period_type = int(period[1])
            years, months, weeks, days = 0, 0, 0, 0
            if period_type == "years":
                years = period_duration
            elif period_type == "months":
                months = period_duration
            elif period_type == "days":
                days = period_duration
            elif period_type == "weeks":
                weeks = period_duration
            if "+" in params:
                date = current_date + relativedelta(years=years, months=months, weeks=weeks, days=days)
            if "-" in params:
                date = current_date + relativedelta(years=-years, months=-months, weeks=-weeks, days=-days)
    else:
        try:
            if "-" in params:
                params = normalize_date(params)
            date = str_date(params, indicator=indicator).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            date = None
    return date
