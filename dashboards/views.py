from dashboards.sql_func import get_charts_dataset, execute_select


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

    tmp_chart = {
        "title": "",
        "type": "",
        "pk": "",
        "chart_order": -1,
        "data": [
            {
                "title": "",
                "fields": [],
                "values": [],
                "stringTotal": [],
            }
        ],
        "availableTypes": ["BAR", "COLUMN", "PIE", "LINE", "TABLE"],
        "isFullWidth": False,
        "dates": [],
        "fields": [],
        "columnTotal": [],
    }

    for k, v in data_chart.items():
        step = 0
        for datachart in v:
            if step == 0:
                tmp_chart["title"] = datachart['chart_title']
                tmp_chart["pk"] = datachart[k]
                tmp_chart["chart_order"] = datachart['chart_order']
                tmp_chart["type"] = datachart['default_type']
            r = execute_select(datachart['database'], datachart['user'], datachart['password'], datachart['address'], datachart['port'], datachart['query'])



            step += 1
