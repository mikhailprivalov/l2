
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


def get_enrollees_by_id(connection_string: str, ids_str: str):
    with connect(connection_string).cursor() as cursor:
        cursor.execute(
            f"""
            SELECT [Фамилия], [Имя], [Отчество], [Дата_Рождения], [Пол] FROM [Абитуриенты].[dbo].[Все_Абитуриенты] 
            WHERE [Абитуриенты].[dbo].[Все_Абитуриенты].[ID] IN ({ids_str}) 
            """
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_changes(connection_string: str, last_date_time: str):
    with connect(connection_string).cursor() as cursor:
        cursor.execute(
            f"""
           SELECT [Код], [код_абитуриента], [дата]
           FROM [Абитуриенты].[dbo].[Логи]
           WHERE [Абитуриенты].[dbo].[Логи].[дата] > CAST('{last_date_time}' AS datetime2) and код_абитуриента <> 0
            """
        )
        rows = namedtuplefetchall(cursor)
    return rows
