from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def get_plans_by_params_sql(d_s, d_e, doc_operate_id, doc_anesthetist_id, department):
    """
    парам: d_s - date-start, d_e - date-end, doc_operate, doc_anesthetist, deparment

    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """WITH 
        t_plans AS 
            (SELECT id as pk_plan, patient_card_id, direction,
            to_char(date AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_char, 
            type_operation, doc_operate_id, doc_anesthetist_id, canceled, date  FROM plans_planoperations
            WHERE 
            CASE when %(doc_operate_id)s > -1 THEN 
            doc_operate_id = %(doc_operate_id)s AND date AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
            when %(doc_anesthetist_id)s > -1  THEN
            doc_anesthetist_id = %(doc_anesthetist_id)s AND date AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
            when %(department_id)s > -1 THEN
            date AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s AND doc_operate_id in (SELECT id FROM users_doctorprofile where podrazdeleniye_id=%(department_id)s)
            ELSE date AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
            END
            ORDER BY date),
        
        t_patient AS
            (SELECT clients_card.id as card_id, clients_card.individual_id, clients_individual.family as ind_family,
             clients_individual.name AS ind_name, clients_individual.patronymic as ind_twoname, to_char(clients_individual.birthday, 'DD.MM.YYYY') as birthday
             FROM clients_individual 
             LEFT JOIN clients_card ON clients_individual.id = clients_card.individual_id
             WHERE clients_card.id in (SELECT patient_card_id FROM t_plans))
        
        
        SELECT pk_plan, patient_card_id, direction, date_char, type_operation, doc_operate_id, doc_anesthetist_id, canceled,
               ind_family, ind_name, ind_twoname, birthday, date FROM t_plans
        LEFT JOIN t_patient ON t_plans.patient_card_id = t_patient.card_id ORDER BY date
        """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'doc_operate_id': doc_operate_id, 'doc_anesthetist_id': doc_anesthetist_id, 'department_id': department},
        )

        row = cursor.fetchall()
    return row


def get_plans_by_pk(pks_plan):
    """
    парам: d_s - date-start, d_e - date-end, doc_operate, doc_anesthetist, deparment

    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """WITH 
        t_plans AS 
            (SELECT id as pk_plan, 
            patient_card_id, 
            direction,
            to_char(date AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_char, 
            type_operation, 
            doc_operate_id, 
            doc_anesthetist_id, 
            canceled,
            date 
            FROM plans_planoperations
            WHERE id = ANY(ARRAY[%(pks_plan)s]) 
            ORDER BY date),

        t_patient AS
            (SELECT clients_card.id as card_id, clients_card.individual_id, clients_individual.family as ind_family,
             clients_individual.name AS ind_name, clients_individual.patronymic as ind_twoname, to_char(clients_individual.birthday, 'DD.MM.YYYY') as birthday
             FROM clients_individual 
             LEFT JOIN clients_card ON clients_individual.id = clients_card.individual_id
             WHERE clients_card.id in (SELECT patient_card_id FROM t_plans)),
        
        t_podrazdeleniye AS (
          SELECT id as id, title as title_podr, short_title FROM podrazdeleniya_podrazdeleniya),
        
        t_users_doc AS (
          SELECT users_doctorprofile.id as doc_id, user_id, podrazdeleniye_id, fio, t_podrazdeleniye.title_podr as podr_title,
          t_podrazdeleniye.short_title as short_podr_title
          FROM users_doctorprofile
          LEFT JOIN t_podrazdeleniye ON users_doctorprofile.podrazdeleniye_id = t_podrazdeleniye.id
          ),
          
        t_users_anesthetist AS (
          SELECT users_doctorprofile.id as doc_id, user_id, podrazdeleniye_id, fio, t_podrazdeleniye.title_podr as podr_title, 
          t_podrazdeleniye.short_title as short_podr_title
          FROM users_doctorprofile
          LEFT JOIN t_podrazdeleniye ON users_doctorprofile.podrazdeleniye_id = t_podrazdeleniye.id
          )
        
        SELECT pk_plan, patient_card_id, direction, date_char, type_operation, doc_operate_id, t_users_doc.fio, t_users_doc.short_podr_title,
        doc_anesthetist_id, t_users_anesthetist.fio, canceled, ind_family, ind_name, ind_twoname, birthday, date, t_users_doc.podr_title  FROM t_plans
        LEFT JOIN t_patient ON t_plans.patient_card_id = t_patient.card_id
        LEFT JOIN t_users_doc ON t_users_doc.doc_id = t_plans.doc_operate_id
        LEFT JOIN t_users_anesthetist ON t_users_anesthetist.doc_id = t_plans.doc_anesthetist_id
        ORDER BY date
        """,
            params={'pks_plan': pks_plan, 'tz': TIME_ZONE},
        )

        row = cursor.fetchall()
    return row


def get_plans_hospitalization_sql(d_s, d_e, department):
    """
    парам: d_s - date-start, d_e - date-end, deparment

    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """WITH 
        t_plans AS 
            (SELECT id as pk_plan, client_id,
            to_char(exec_at AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS exec_at_char, 
            work_status, action, exec_at, hospital_department_id, phone, research_id, diagnos, comment FROM plans_planhospitalization
            WHERE 
            CASE
            WHEN %(department_id)s > -1 THEN
                exec_at AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s AND hospital_department_id=%(department_id)s and action=0
            ELSE exec_at AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s and action=0
            END
            ORDER BY hospital_department_id, exec_at),

        t_patient AS
            (SELECT clients_card.id as card_id, clients_card.individual_id, clients_individual.family as ind_family,
             clients_individual.name AS ind_name, clients_individual.patronymic as ind_twoname, to_char(clients_individual.birthday, 'DD.MM.YYYY') as born,
             clients_individual.birthday, clients_individual.sex
             FROM clients_individual 
             LEFT JOIN clients_card ON clients_individual.id = clients_card.individual_id
             WHERE clients_card.id in (SELECT client_id FROM t_plans))

        SELECT pk_plan, client_id, exec_at_char, work_status, action, hospital_department_id,
               concat_ws(' ', ind_family, ind_name, ind_twoname) as fio_patient, birthday, exec_at,
               to_char(EXTRACT(YEAR from age(t_plans.exec_at, t_patient.birthday)), '999') as ind_age,
               t_patient.born, podrazdeleniya_podrazdeleniya.title as depart_title, phone, directory_researches.title as research_title, diagnos, 
               t_patient.sex, comment
                FROM t_plans
        LEFT JOIN t_patient ON t_plans.client_id = t_patient.card_id 
        LEFT JOIN podrazdeleniya_podrazdeleniya ON podrazdeleniya_podrazdeleniya.id = hospital_department_id
        LEFT JOIN directory_researches ON t_plans.research_id = directory_researches.id 
        
        ORDER BY hospital_department_id, exec_at
        
        """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'department_id': department},
        )

        rows = namedtuplefetchall(cursor)
    return rows
