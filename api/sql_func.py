from django.db import connection

from laboratory.settings import TIME_ZONE


def dispensarization_research(sex, age, client_id, d_start, d_end):
    """
    на входе: пол, возраст,
    выход: pk - исследований, справочника "DispensaryRouteSheet"
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(""" WITH
    t_field AS (
        SELECT directory_dispensaryroutesheet.research_id, directory_dispensaryroutesheet.sort_weight
        FROM directory_dispensaryroutesheet WHERE
        directory_dispensaryroutesheet.age_client = %(age_p)s
        and directory_dispensaryroutesheet.sex_client = %(sex_p)s
        ORDER BY directory_dispensaryroutesheet.sort_weight
    ),
    t_iss AS
        (SELECT directions_napravleniya.client_id, directions_issledovaniya.napravleniye_id as napr,  
        directions_napravleniya.data_sozdaniya, 
        directions_issledovaniya.research_id, directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s as time_confirmation,
        to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm
        FROM directions_issledovaniya
        LEFT JOIN directions_napravleniya 
           ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id 
        WHERE directions_napravleniya.client_id = %(client_p)s
         and directions_issledovaniya.research_id in (SELECT research_id FROM t_field) 
         and directions_issledovaniya.time_confirmation BETWEEN  %(start_p)s AND %(end_p)s
         ORDER BY directions_issledovaniya.time_confirmation DESC),
     t_research AS (SELECT directory_researches.id, directory_researches.title, 
                    directory_researches.short_title FROM directory_researches),
     t_disp AS 
        (SELECT DISTINCT ON (t_field.research_id) t_field.research_id as res_id, t_field.sort_weight as sort,
        client_id, napr, data_sozdaniya, t_iss.research_id, time_confirmation, date_confirm FROM t_field
        LEFT JOIN t_iss ON t_field.research_id = t_iss.research_id)
    
    SELECT res_id, sort, napr, time_confirmation, date_confirm, title, short_title 
    FROM t_disp
    LEFT JOIN t_research ON t_disp.res_id = t_research.id
    ORDER by sort
        """, params={'sex_p': sex, 'age_p': age, 'client_p': client_id, 'start_p': d_start, 'end_p': d_end, 'tz': TIME_ZONE})

        row = cursor.fetchall()
    return row


def get_fraction_result(client_id, fraction_id, count=1):
    """
    на входе: id-фракции, id-карты,
    выход: последний результат исследования
    :return:
    """

    with connection.cursor() as cursor:
        cursor.execute("""
        SELECT directions_napravleniya.client_id, directions_issledovaniya.napravleniye_id,   
        directions_issledovaniya.research_id, directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s as time_confirmation,
        to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm,
        directions_result.value, directions_result.fraction_id
        FROM directions_issledovaniya
        LEFT JOIN directions_napravleniya 
           ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
        LEFT JOIN directions_result
           ON directions_issledovaniya.id=directions_result.issledovaniye_id
        WHERE directions_napravleniya.client_id = %(client_p)s
         and directions_result.fraction_id = %(fraction_p)s
         and directions_issledovaniya.time_confirmation is not NULL
         ORDER BY directions_issledovaniya.time_confirmation DESC LIMIT %(count_p)s 
        """, params={'client_p': client_id, 'fraction_p': fraction_id, 'count_p': count, 'tz': TIME_ZONE})

        row = cursor.fetchall()
    return row


def get_field_result(client_id, field_id, count=1):
    """
    на входе: id-поля, id-карты,
    выход: последний результат поля
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT directions_napravleniya.client_id, directions_issledovaniya.napravleniye_id,   
            directions_issledovaniya.research_id, directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s as time_confirmation,
            to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm,
            directions_paraclinicresult.value, directions_paraclinicresult.field_id
            FROM directions_issledovaniya
            LEFT JOIN directions_napravleniya 
            ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
            LEFT JOIN directions_paraclinicresult
            ON directions_issledovaniya.id=directions_paraclinicresult.issledovaniye_id
            WHERE directions_napravleniya.client_id = %(client_p)s
            and directions_paraclinicresult.field_id = %(field_id)s
            and directions_issledovaniya.time_confirmation is not NULL
            ORDER BY directions_issledovaniya.time_confirmation DESC LIMIT %(count_p)s
            """, params={'client_p': client_id, 'field_id': field_id, 'count_p': count, 'tz': TIME_ZONE})

        row = cursor.fetchall()
    return row


def users_by_group(title_groups):

    with connection.cursor() as cursor:
        cursor.execute("""
        WITH 
          t_group AS (
          SELECT id as group_id FROM auth_group
          WHERE name = ANY(ARRAY[%(title_groups)s])),
            
        t_users_id AS(
          SELECT user_id FROM auth_user_groups
          WHERE group_id in (SELECT group_id from t_group)),
            
        t_podrazdeleniye AS (
          SELECT id as id, title as title_podr, short_title FROM podrazdeleniya_podrazdeleniya),
            
        t_users AS (
          SELECT users_doctorprofile.id as doc_id, fio, user_id, podrazdeleniye_id, title_podr, short_title
          FROM users_doctorprofile
          LEFT JOIN
          t_podrazdeleniye ON users_doctorprofile.podrazdeleniye_id = t_podrazdeleniye.id
          WHERE user_id in (SELECT user_id FROM t_users_id))
            
        SELECT doc_id, fio, podrazdeleniye_id, title_podr, short_title FROM t_users
        ORDER BY podrazdeleniye_id                    
        """, params={'title_groups': title_groups})

        row = cursor.fetchall()
    return row
