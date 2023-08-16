from django.db import connection
from pyodbc import connect
from utils.db import namedtuplefetchall


def get_connection_params(settings_name):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                dashboards_databaseconnectsettings.login,
                dashboards_databaseconnectsettings.ip_address,
                dashboards_databaseconnectsettings.password,
                dashboards_databaseconnectsettings.port,
                dashboards_databaseconnectsettings.database,
                dashboards_databaseconnectsettings.driver,
                dashboards_databaseconnectsettings.encrypt
                FROM public.dashboards_databaseconnectsettings
                WHERE dashboards_databaseconnectsettings.title = %(name_settings)s
        """,
            params={"name_settings": settings_name},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_all_enrollee(connection_string):
    with connect(connection_string).cursor() as cursor:
        cursor.execute(
            """
            SELECT TOP(10) * FROM Абитуриенты.dbo.Все_Абитуриенты
            """,
        )
        rows = namedtuplefetchall(cursor)
    return rows
