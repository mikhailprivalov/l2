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
                 [Код_Заявления], 
                 [Номер_Документа],
                 [Серия_Документа],
                 [Абитуриенты].[dbo].[АбитДисциплины].[Дисциплина]
               FROM [Абитуриенты].[dbo].[Все_Оценки]
               LEFT JOIN [Абитуриенты].[dbo].[АбитДисциплины] ON
               [Абитуриенты].[dbo].[АбитДисциплины].[Код] = [Абитуриенты].[dbo].[Все_Оценки].[Код_Дисциплины]
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
                 [Дата_Подачи],
                 [Проверено],
                 [Проверено]
               FROM [Абитуриенты].[dbo].[Все_Заявления]
               WHERE [Абитуриенты].[dbo].[Все_Заявления].[ID] IN ({id_enrollee}) 
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
                 [БаллИД]
               FROM [Абитуриенты].[dbo].[Достижения]
               WHERE [Абитуриенты].[dbo].[Достижения].[ID] IN ({id_enrollee}) 
               """
        )
        rows = namedtuplefetchall(cursor)
    return rows
