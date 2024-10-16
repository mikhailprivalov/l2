from django.db import connection

from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def dispensarization_research(sex, age, client_id, d_start, d_end):
    """
    На входе: пол, возраст,
    выход: pk - исследований, справочника "DispensaryRouteSheet"
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """ WITH
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
        """,
            params={'sex_p': sex, 'age_p': age, 'client_p': client_id, 'start_p': d_start, 'end_p': d_end, 'tz': TIME_ZONE},
        )

        row = cursor.fetchall()
    return row


def get_fraction_result(client_id, fraction_id, count=1):
    """
    на входе: id-фракции, id-карты,
    выход: последний результат исследования
    :return:
    """

    with connection.cursor() as cursor:
        cursor.execute(
            """
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
        """,
            params={'client_p': client_id, 'fraction_p': fraction_id, 'count_p': count, 'tz': TIME_ZONE},
        )

        row = cursor.fetchall()
    return row


def get_field_result(client_id, field_id, count=1, current_year='1900-01-01 00:00:00', months_ago='-1', parent_iss=-1, use_parent_iss='-1'):
    """
    на входе: id-поля, id-карты,
    выход: последний результат поля
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
            directions_napravleniya.client_id, 
            directions_issledovaniya.napravleniye_id,   
            directions_issledovaniya.research_id, 
            directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s as time_confirmation,
            to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm,
            directions_paraclinicresult.value, 
            directions_paraclinicresult.field_id,
            directions_napravleniya.parent_id
            FROM directions_issledovaniya
            LEFT JOIN directions_napravleniya 
            ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
            LEFT JOIN directions_paraclinicresult
            ON directions_issledovaniya.id=directions_paraclinicresult.issledovaniye_id
            WHERE directions_napravleniya.client_id = %(client_p)s
            and directions_paraclinicresult.field_id = %(field_id)s
            and directions_issledovaniya.time_confirmation is not NULL
            AND CASE WHEN %(current_year)s != '1900-01-01 00:00:00' THEN 
                     directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s > %(current_year)s
                     WHEN %(months_ago)s != '-1' THEN 
                     directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s > (current_date AT TIME ZONE 'ASIA/IRKUTSK' - interval %(months_ago)s)
                     WHEN %(current_year)s = '1900-01-01 00:00:00' THEN directions_issledovaniya.time_confirmation is not Null
                END
            AND CASE WHEN %(use_parent_iss)s != '-1' THEN 
                     directions_napravleniya.parent_id in %(parent_iss)s
                     WHEN %(use_parent_iss)s = '-1' THEN 
                     directions_issledovaniya.time_confirmation is not Null
                END
            ORDER BY directions_issledovaniya.time_confirmation DESC LIMIT %(count_p)s
            """,
            params={
                'client_p': client_id,
                'field_id': field_id,
                'count_p': count,
                'tz': TIME_ZONE,
                'current_year': current_year,
                'months_ago': months_ago,
                'parent_iss': parent_iss,
                'use_parent_iss': use_parent_iss,
            },
        )

        row = cursor.fetchall()
    return row


def users_by_group(title_groups, hosp_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
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
          SELECT users_doctorprofile.id as doc_id, fio, user_id, podrazdeleniye_id, title_podr, short_title, hospital_id, position_id
          FROM users_doctorprofile
          LEFT JOIN
          t_podrazdeleniye ON users_doctorprofile.podrazdeleniye_id = t_podrazdeleniye.id
          WHERE user_id in (SELECT user_id FROM t_users_id) and hospital_id = %(hosp_id)s) 
    
        SELECT doc_id, fio, podrazdeleniye_id, title_podr, short_title, position_id FROM t_users
        ORDER BY podrazdeleniye_id, fio DESC              
        """,
            params={'title_groups': title_groups, "hosp_id": hosp_id},
        )

        row = cursor.fetchall()
    return row


def users_all(hosp_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        WITH
        t_users_id AS (
          SELECT user_id FROM auth_user_groups),
            
        t_podrazdeleniye AS (
          SELECT id as id, title as title_podr, short_title FROM podrazdeleniya_podrazdeleniya),
            
        t_users AS (
          SELECT users_doctorprofile.id as doc_id, fio, user_id, podrazdeleniye_id, title_podr, short_title, hospital_id, position_id
          FROM users_doctorprofile
          LEFT JOIN
          t_podrazdeleniye ON users_doctorprofile.podrazdeleniye_id = t_podrazdeleniye.id
          WHERE user_id in (SELECT user_id FROM t_users_id) and hospital_id = %(hosp_id)s)            
        SELECT doc_id, fio, podrazdeleniye_id, title_podr, short_title FROM t_users
        ORDER BY podrazdeleniye_id                    
        """,
            params={"hosp_id": hosp_id},
        )

        row = cursor.fetchall()
    return row


def get_diagnoses(d_type="mkb10.4", diag_title="-1", diag_mkb="-1", limit=100):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT * FROM public.directions_diagnoses
            WHERE d_type=%(d_type)s 
            AND CASE
                WHEN %(diag_title)s != '-1' AND %(diag_mkb)s != '-1' THEN 
                  code ~* %(diag_mkb)s and title ~* %(diag_title)s
                WHEN %(diag_title)s != '-1' AND %(diag_mkb)s = '-1' THEN 
                  title ~* %(diag_title)s
                WHEN %(diag_title)s = '-1' AND %(diag_mkb)s != '-1' THEN 
                  code ~* %(diag_mkb)s 
              END
            AND 
            nsi_id IS NOT NULL
            AND nsi_id != '' and hide=false
        LIMIT %(limit)s
        """,
            params={"d_type": d_type, "diag_title": diag_title, "diag_mkb": diag_mkb, "limit": limit},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_resource_researches(resource_pks):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT scheduleresource_id, researches_id FROM doctor_schedule_scheduleresource_service
        WHERE scheduleresource_id in %(resource_pks)s 
        ORDER BY scheduleresource_id
        """,
            params={"resource_pks": resource_pks},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def search_data_by_param(
    date_create_start,
    date_create_end,
    research_id,
    case_number,
    hospital_id,
    date_registred_start,
    date_registred_end,
    date_examination_start,
    date_examination_end,
    doc_confirm,
    date_recieve_start,
    date_recieve_end,
    date_get,
    final_text,
    direction_number,
):
    """
    на входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                distinct on (directions_issledovaniya.napravleniye_id) directions_issledovaniya.napravleniye_id as direction_number,
                directions_issledovaniya.medical_examination as date_service,
                users_doctorprofile.fio as doc_fio,

                directions_napravleniya.client_id,
                directions_napravleniya.additional_number,
                concat(clients_individual.family, ' ', clients_individual.name, ' ', clients_individual.patronymic) as patient_fio,

                hospitals_hospitals.title as hosp_title,
                hospitals_hospitals.short_title as hosp_short_title,
                hospitals_hospitals.okpo as hosp_okpo,
                hospitals_hospitals.okato as hosp_okato,

                to_char(clients_individual.birthday, 'DD.MM.YYYY') as patient_birthday,
                date_part('year', age(directions_issledovaniya.medical_examination, clients_individual.birthday))::int as patient_age,
                clients_individual.sex as patient_sex,
                directions_issledovaniya.napravleniye_id,
                directions_issledovaniya.research_id,
                directions_paraclinicresult.value as field_value,
                directions_paraclinicresult.field_id,
                directory_paraclinicinputfield.title,
                to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm,
                to_char(directions_issledovaniya.medical_examination AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as medical_examination,
                to_char(directions_napravleniya.visit_date AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as registered_date,
                to_char(directions_napravleniya.time_gistology_receive AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as time_gistology_receive,
                doc_plan.fio as doc_plan_fio
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN clients_card ON clients_card.id=directions_napravleniya.client_id
                LEFT JOIN clients_individual ON clients_individual.id=clients_card.individual_id
                LEFT JOIN hospitals_hospitals on directions_napravleniya.hospital_id = hospitals_hospitals.id
                LEFT JOIN users_doctorprofile ON directions_issledovaniya.doc_confirmation_id=users_doctorprofile.id
                LEFT JOIN users_doctorprofile doc_plan ON directions_napravleniya.planed_doctor_executor_id=doc_plan.id
                LEFT JOIN directions_paraclinicresult on directions_paraclinicresult.issledovaniye_id=directions_issledovaniya.id
                LEFT JOIN directory_paraclinicinputfield on directions_paraclinicresult.field_id=directory_paraclinicinputfield.id
                
                WHERE 
                    directions_issledovaniya.research_id in %(research_id)s 
                    and (directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s BETWEEN %(date_create_start)s AND %(date_create_end)s)
                AND CASE WHEN %(case_number)s != '-1' THEN directions_napravleniya.additional_number = %(case_number)s 
                         WHEN %(case_number)s = '-1' THEN directions_napravleniya.cancel is not Null 
                END
                AND CASE WHEN %(direction_number)s != '-1' THEN directions_napravleniya.id = %(direction_number)s 
                         WHEN %(direction_number)s = '-1' THEN directions_napravleniya.cancel is not Null 
                END
                AND CASE WHEN (%(hospital_id)s)::int > -1 THEN directions_napravleniya.hospital_id = %(hospital_id)s
                         WHEN (%(hospital_id)s)::int = -1 THEN directions_napravleniya.cancel is not Null 
                END
                AND CASE WHEN %(date_examination_start)s != '1900-01-01' THEN 
                     (directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(date_examination_start)s AND %(date_examination_end)s)
                     and directions_issledovaniya.time_confirmation is NOT NULL
                     WHEN %(date_examination_start)s = '1900-01-01' THEN directions_napravleniya.cancel is not Null
                END
                AND CASE WHEN %(doc_confirm)s > -1 THEN directions_issledovaniya.doc_confirmation_id = %(doc_confirm)s or directions_napravleniya.planed_doctor_executor_id = %(doc_confirm)s
                         WHEN %(doc_confirm)s = -1 THEN directions_napravleniya.cancel is not Null 
                END
                AND CASE WHEN %(date_registred_start)s != '1900-01-01 00:00:00' THEN
                         directions_napravleniya.visit_date AT TIME ZONE %(tz)s BETWEEN %(date_registred_start)s AND %(date_registred_end)s
                         WHEN %(date_registred_start)s = '1900-01-01 00:00:00' THEN directions_napravleniya.cancel is not Null 
                END
                AND CASE WHEN %(date_recieve_start)s != '1900-01-01 00:00:00' THEN
                         directions_napravleniya.time_gistology_receive AT TIME ZONE %(tz)s BETWEEN %(date_recieve_start)s AND %(date_recieve_end)s
                         WHEN %(date_recieve_start)s = '1900-01-01 00:00:00' THEN directions_napravleniya.cancel is not Null
                END
                AND CASE WHEN %(date_get)s != '1900-01-01' THEN directory_paraclinicinputfield.title = 'Дата забора' and directions_paraclinicresult.value = %(date_get)s
                         WHEN %(date_get)s = '1900-01-01' THEN directions_napravleniya.cancel is not Null
                END
                AND CASE WHEN %(final_text)s != '' THEN directions_paraclinicresult.value ~* %(final_text)s
                         WHEN %(final_text)s = '' THEN directions_napravleniya.cancel is not Null 
                END
                order by directions_issledovaniya.napravleniye_id
            """,
            params={
                'date_create_start': date_create_start,
                'date_create_end': date_create_end,
                'research_id': research_id,
                'case_number': case_number,
                'hospital_id': hospital_id,
                'date_examination_start': date_examination_start,
                'date_examination_end': date_examination_end,
                'date_registred_start': date_registred_start,
                'date_registred_end': date_registred_end,
                'doc_confirm': doc_confirm,
                'date_recieve_start': date_recieve_start,
                'date_recieve_end': date_recieve_end,
                'date_get': date_get,
                'final_text': final_text,
                'tz': TIME_ZONE,
                'direction_number': direction_number,
            },
        )

        rows = namedtuplefetchall(cursor)
    return rows


def search_text_stationar(date_create_start, date_create_end, final_text):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                distinct on (history_num ) dp.napravleniye_id as history_num,
                directions_issledovaniya.napravleniye_id as direction_number,
                users_doctorprofile.fio as doc_fio,
                directions_issledovaniya.medical_examination as date_service,
                directions_napravleniya.client_id,
                concat(clients_individual.family, ' ', clients_individual.name, ' ', clients_individual.patronymic) as patient_fio,
                to_char(clients_individual.birthday, 'DD.MM.YYYY') as patient_birthday,
                date_part('year', age(directions_issledovaniya.medical_examination, clients_individual.birthday))::int as patient_age,
                clients_individual.sex as patient_sex,
                directions_issledovaniya.napravleniye_id,
                directions_issledovaniya.research_id,
                directions_paraclinicresult.value as field_value,
                directions_paraclinicresult.field_id,
                directory_paraclinicinputfield.title,
                directory_researches.title as research_title,
                to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN directory_researches ON directions_issledovaniya.research_id = directory_researches.id
                LEFT JOIN users_doctorprofile ON directions_issledovaniya.doc_confirmation_id=users_doctorprofile.id
                LEFT JOIN clients_card ON clients_card.id=directions_napravleniya.client_id
                LEFT JOIN clients_individual ON clients_individual.id=clients_card.individual_id                
                LEFT JOIN directions_paraclinicresult on directions_paraclinicresult.issledovaniye_id=directions_issledovaniya.id
                LEFT JOIN directory_paraclinicinputfield on directions_paraclinicresult.field_id=directory_paraclinicinputfield.id
                LEFT JOIN directions_issledovaniya dp on directions_napravleniya.parent_id=dp.id
                WHERE 
                    directory_researches.is_slave_hospital = true
                    and directions_issledovaniya.time_confirmation IS NOT NULL 
                    and (directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s BETWEEN %(date_create_start)s AND %(date_create_end)s) 
                    and directions_paraclinicresult.value ~* %(final_text)s
                order by dp.napravleniye_id
            """,
            params={
                'date_create_start': date_create_start,
                'date_create_end': date_create_end,
                'final_text': final_text,
                'tz': TIME_ZONE,
            },
        )

        rows = namedtuplefetchall(cursor)
    return rows


def search_case_by_card_date(card_id, plan_date_start_case, research_case_id, limit):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                directions_napravleniya.id as case_direction_number,
                directions_issledovaniya.id as case_issledovaniye_number
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                WHERE 
                    directions_issledovaniya.research_id = %(research_case_id)s
                    and directions_issledovaniya.plan_start_date AT TIME ZONE %(tz)s = %(plan_date_start_case)s
                    and directions_napravleniya.client_id = %(card_id)s 
                LIMIT %(limit)s
            """,
            params={'card_id': card_id, 'plan_date_start_case': plan_date_start_case, 'research_case_id': research_case_id, 'tz': TIME_ZONE, 'limit': limit},
        )

        rows = namedtuplefetchall(cursor)
    return rows
