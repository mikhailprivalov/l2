import psycopg2
from utils.db import namedtuplefetchall
from django.db import connection


def dashboards():
    with connection.cursor() as cursor:
        cursor.execute(
            """
              SELECT id, title, 'order' as ord_dash FROM public.dashboards_dashboard
              WHERE hide = False
              ORDER BY ord_dash DESC
        """
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_charts_dataset(dashboard_pk):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                dashboards_dashboardchartdata.chart_id, 
                dashboards_dashboardchartdata.data_set_id,
                dashboards_dashboarddataset.sql_query,
                dashboards_dashboarddataset.sql_columns_settings,
                dashboards_dashboarddataset.title as field_title,
                dashboards_dashboarddataset.connect_id,
                dashboards_databaseconnectsettings.login,
                dashboards_databaseconnectsettings.ip_address,
                dashboards_databaseconnectsettings.password,
                dashboards_databaseconnectsettings.port,
                dashboards_databaseconnectsettings.database,
                dashboards_dashboardcharts.title as chart_title,
                dashboards_dashboardcharts.default_type as chart_type,
                dashboards_dashboardcharts.order as chart_order
                FROM public.dashboards_dashboardchartdata
                LEFT JOIN dashboards_dashboarddataset ON
                dashboards_dashboarddataset.id = dashboards_dashboardchartdata.data_set_id
                LEFT JOIN dashboards_databaseconnectsettings ON
                dashboards_databaseconnectsettings.id = dashboards_dashboarddataset.connect_id
                LEFT JOIN dashboards_dashboardcharts ON
                dashboards_dashboardcharts.id = dashboards_dashboardchartdata.chart_id
                WHERE chart_id in (SELECT id from dashboards_dashboardcharts where dashboard_id = %(dashboard_pk)s and hide=False)
                order by dashboards_dashboardcharts.order
        """,
            params={'dashboard_pk': dashboard_pk},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def execute_select(database, user, password, address, port, query):
    connection = psycopg2.connect(
        database=database,
        user=user,
        password=password,
        host=address,
        port=port
    )
    cursor = connection.cursor()
    cursor.execute(query)
    rows = namedtuplefetchall(cursor)
    cursor.close()
    connection.close()
    return rows
