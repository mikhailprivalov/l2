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
           ORDER BY [Абитуриенты].[dbo].[Логи].[дата]
            """
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_grade_entrance_exams(connection_string: str, id_enrollee: str):
    with connect(connection_string).cursor() as cursor:
        cursor.execute(
            f"""
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
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_application_by_id(connection_string: str, id_enrollee: str):
    with connect(connection_string).cursor() as cursor:
        cursor.execute(
            f"""
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
                 [КодФормы],
               FROM [Абитуриенты].[dbo].[Все_Заявления]
               WHERE [Абитуриенты].[dbo].[Все_Заявления].[ID] IN ({id_enrollee}) AND
               [Абитуриенты].[dbo].[Все_Заявления].[Удалена] = 0 AND 
               [Абитуриенты].[dbo].[Все_Заявления].[ПричинаУдаления] = ''
               """
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_achievements_by_id(connection_string: str, id_enrollee: str):
    with connect(connection_string).cursor() as cursor:
        cursor.execute(
            f"""
               SELECT 
                 [ID], 
                 [Код], 
                 [КодИД], 
                 [ДатаИД], 
                 [БаллИД],
                 [СерияИД],
                 [НомерИД],
                 [ОрганизацияИД]
               FROM [Абитуриенты].[dbo].[Достижения]
               WHERE [Абитуриенты].[dbo].[Достижения].[ID] IN ({id_enrollee}) 
               """
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_dashboard_data():
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
            education_applicationeducation.id as app_id,
            education_applicationeducation.date as app_data,
            exsubj.title as subj_title,
            education_entranceexam.grade,
            es.title as special_title,
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
            WHERE ci.mmis_id IS NOT NULL
            ORDER BY education_entranceexam.card_id, education_applicationeducation.id
            """,
            params={},
        )
        rows = namedtuplefetchall(cursor)
    return rows
