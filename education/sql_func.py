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


def get_enrollee_by_year(connection_string: str, year):
    with connect(connection_string).cursor() as cursor:
        cursor.execute(
            f""" 
            SELECT top(1) * FROM Абитуриенты.dbo.Все_Абитуриенты 
            WHERE Абитуриенты.dbo.Все_Абитуриенты.Год_Набора = {year} 
            """
        )
        rows = namedtuplefetchall(cursor)
    return rows
