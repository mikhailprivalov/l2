import json

from dashboards.models import Dashboard
from dashboards.sql_func import get_charts_dataset, execute_select


def get_dashboard():
    return [{"label": dashboard.title, "id": dashboard.pk} for dashboard in Dashboard.objects.filter(hide=False).order_by('-order')]


def exec_query(dashboard_pk):
    # data_chart = {"chart_id": [{"chart_title": "", "chart_type": "", "database": "", "user": "", "password": "", "address": "", "port": "", "query": "", sql_param: ""}]}
    result = []
    data_chart = {}
    metadata_charts = get_charts_dataset(dashboard_pk)
    # обход по графикам датасетов
    for md in metadata_charts:
        if not data_chart.get(md.chart_id):
            data_chart[md.chart_id] = [
                {"chart_title": md.chart_title, "chart_type": md.chart_type, "database": md.database, "user": md.login, "password": md.password, "address": md.ip_address,
                 "port": md.port, "query": md.sql_query, "sql_param": md.sql_columns_settings, "chart_order": md.chart_order, "field_title": md.field_title}]
        else:
            temp_data_chart = data_chart.get(md.chart_id, None)
            temp_data_chart.append({"chart_title": md.chart_title, "chart_type": md.chart_type, "database": md.database, "user": md.login, "password": md.password, "address": md.ip_address,
                                    "port": md.port, "query": md.sql_query, "sql_param": md.sql_columns_settings, "chart_order": md.chart_order, "field_title": md.field_title})
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
            r = execute_select(datachart['database'], datachart['user'], datachart['password'], datachart['address'], datachart['port'], datachart['query'])
            values = []
            dates = []
            for i in r:
                tmp_dict = i._asdict()
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

    return result
