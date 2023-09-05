import datetime

from django.db import connection
from laboratory.settings import MMIS_CONNECT_WITH_PYODBC
if MMIS_CONNECT_WITH_PYODBC:
    from pyodbc import connect
else:
    from pymssql import connect
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


def get_applications_by_card(card_pk: int):
    with connection.cursor() as cursor:
        cursor.execute(
            """
           SELECT education_applicationeducation.id as application_pk, date, users_speciality.title as spec_title, education_subjects.title as subject_title, grade FROM education_applicationeducation
           LEFT JOIN users_speciality on speciality_id = users_speciality.id
           LEFT JOIN education_entranceexam on education_applicationeducation.id = education_entranceexam.application_education_id
           LEFT JOIN education_subjects on education_entranceexam.subjects_id = education_subjects.id
           WHERE education_applicationeducation.card_id = %(card_pk)s
           ORDER BY application_pk
           """,
            params={"card_pk": card_pk},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def execute_sql_by_connect(query, connection_string):
    if MMIS_CONNECT_WITH_PYODBC:
        connect_as = connect(connection_string).cursor()
    else:
        connect_as = connect(connection_string["server"], connection_string["user"], connection_string["password"], connection_string["database"]).cursor()
    with connect_as as cursor:
        cursor.execute(query)
        rows = namedtuplefetchall(cursor)
    return rows


def get_enrollees_by_id(connection_string, ids_str: str):
    query = f"""
            SELECT 
              [ID], 
              [Фамилия], 
              [Имя], 
              [Отчество], 
              [СНИЛС], 
              [Дата_Рождения], 
              [Пол],
              [Телефон_ПП],
              [Мобильный],
              [E_Mail],
              [Тип_Удостоверения],
              [Номер_Паспорта],
              [ПаспортНомер],
              [ПаспортСерия],
              [Дата_Выдачи],
              [Кем_Выдан],
              [Страна_ПП],
              [Регион_ПП],
              [Город_ПП],
              [Индекс_ПП],
              [Улица_ПП],
              [Дом_Кв_ПП],
              [Тип_Образ_Документа],
              [Серия_Аттестата],
              [Номер_Аттестата],
              [Год_Набора],
              [ТипОбразования],
              [ДатаПодачиДокументов],
              [Гражданство],
              [GUID],
              [Иностранец],
              [РегНомерДиплома],
              [GuidEpgu]
            FROM [Абитуриенты].[dbo].[Все_Абитуриенты] 
            WHERE [Абитуриенты].[dbo].[Все_Абитуриенты].[ID] IN ({ids_str}) 
            """
    return execute_sql_by_connect(query, connection_string)


def get_changes(connection_string, last_date_time: str):
    query = f"""
           SELECT [Код], [код_абитуриента], [дата]
           FROM [Абитуриенты].[dbo].[Логи]
           WHERE [Абитуриенты].[dbo].[Логи].[дата] >= CAST('{last_date_time}' AS datetime2) and код_абитуриента <> 0
           ORDER BY [Абитуриенты].[dbo].[Логи].[дата]
            """
    return execute_sql_by_connect(query, connection_string)


def get_grade_entrance_exams(connection_string, id_enrollee: str):
    query = f"""
               SELECT 
                 [ID],
                 [Код],
                 [Код_Дисциплины], 
                 [Оценка], 
                 [Код_Испытания], 
                 [Код_Заявления]
               FROM [Абитуриенты].[dbo].[Все_Оценки]
               WHERE [Абитуриенты].[dbo].[Все_Оценки].[ID] IN ({id_enrollee}) 
               """
    return execute_sql_by_connect(query, connection_string)


def get_application_by_id(connection_string, id_enrollee: str):
    query = f"""
               SELECT 
                 [Код_Заявления],
                 [ID], 
                 [Основания], 
                 [Код_Специальности], 
                 [НомерЛД], 
                 [Номер],
                 [Шифр],
                 [Факультет],
                 [Оригинал],
                 [Дата_Подачи],
                 [Зачислен],
                 [ОтказалсяОтЗачисления], 
                 [Проверено],
                 [КодФормы]
               FROM [Абитуриенты].[dbo].[Все_Заявления]
               WHERE [Абитуриенты].[dbo].[Все_Заявления].[ID] IN ({id_enrollee}) AND
               [Абитуриенты].[dbo].[Все_Заявления].[Удалена] = 0 AND 
               [Абитуриенты].[dbo].[Все_Заявления].[ПричинаУдаления] = ''
               """
    return execute_sql_by_connect(query, connection_string)


def get_achievements_by_id(connection_string: str, id_enrollee: str):
    query = f"""
               SELECT 
                 [ID], 
                 [Код], 
                 [КодИД], 
                 [ДатаИД], 
                 [БаллИД],
                 [СерияИД],
                 [НомерИД],
                 [ОрганизацияИД],
                 [Код_Заявления]
               FROM [Абитуриенты].[dbo].[Достижения]
               WHERE [Абитуриенты].[dbo].[Достижения].[ID] IN ({id_enrollee}) 
               """
    return execute_sql_by_connect(query, connection_string)


def get_dashboard_data(application_year=datetime.datetime.now().year):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            education_entranceexam.card_id as card_id,
            ci.family as ind_family,
            ci.patronymic as ind_patronymic,
            ci.name as ind_name,
            education_applicationeducation.personal_number as personal_number,
            education_applicationeducation.is_enrolled as is_enrolled,
            education_applicationeducation.is_expelled as is_expelled,
            education_applicationeducation.original,
            education_applicationeducation.id as app_id,
            education_applicationeducation.date as app_data,
            exsubj.title as subj_title,
            education_entranceexam.grade,
            es.title as special_title,
            es.id as special_id,
            exsubj.title as subject_title
            FROM education_entranceexam
            LEFT JOIN clients_card cc ON
            cc.id = education_entranceexam.card_id
            LEFT JOIN clients_individual ci ON
            ci.id = cc.individual_id
            LEFT JOIN education_applicationeducation ON
            education_applicationeducation.id = education_entranceexam.application_education_id
            LEFT JOIN education_educationspeciality es ON 
            education_applicationeducation.speciality_id = es.id
            LEFT JOIN education_subjects exsubj ON 
            education_entranceexam.subjects_id = exsubj.id
            WHERE ci.mmis_id IS NOT NULL AND date_part('year', education_applicationeducation.date) = %(application_year)s
            ORDER BY education_entranceexam.card_id, education_applicationeducation.id
            """,
            params={"application_year": application_year},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_confirm_research_contract(card_id, researches):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            directions_issledovaniya.napravleniye_id
            FROM directions_issledovaniya
            LEFT JOIN directions_napravleniya dn ON
            dn.id = directions_issledovaniya.napravleniye_id
            WHERE directions_issledovaniya.research_id in %(researches)s and 
            dn.client_id = %(card_id)s and directions_issledovaniya.time_confirmation IS NOT NULL
            """,
            params={"researches": researches, 'card_id': card_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows
