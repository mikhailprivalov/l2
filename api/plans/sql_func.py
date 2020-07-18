from django.db import connection
from laboratory.settings import TIME_ZONE

def get_plans_by_params_sql(d_s, d_e, doc_operate_id, doc_anesthetist_id, department):
    """
    парам: d_s - date-start, d_e - date-end, doc_operate, doc_anesthetist, deparment

    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute("""WITH 
        t_plans AS 
            (SELECT id as pk_plan, patient_card_id, direction,
            to_char(date AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date, 
            type_operation, doc_operate_id, doc_anesthetist_id, canceled FROM plans_planoperations
            WHERE 
            CASE when %(doc_operate_id)s > -1 THEN 
            doc_operate_id = %(doc_operate_id)s AND date BETWEEN %(d_start)s AND %(d_end)s
            when %(doc_anesthetist_id)s > -1  THEN
            doc_anesthetist_id = %(doc_anesthetist_id)s AND date BETWEEN %(d_start)s AND %(d_end)s
            when %(department_id)s > -1 THEN
            date BETWEEN %(d_start)s AND %(d_end)s AND doc_operate_id in (SELECT id FROM users_doctorprofile where podrazdeleniye_id=%(department_id)s)
            ELSE date BETWEEN %(d_start)s AND %(d_end)s
            END
            ORDER BY date),
        
        t_patient AS
            (SELECT clients_card.id as card_id, clients_card.individual_id, clients_individual.family as ind_family,
             clients_individual.name AS ind_name, clients_individual.patronymic as ind_twoname, to_char(clients_individual.birthday, 'DD.MM.YYYY') as birthday
             FROM clients_individual 
             LEFT JOIN clients_card ON clients_individual.id = clients_card.individual_id
             WHERE clients_card.id in (SELECT patient_card_id FROM t_plans))
        
        
        SELECT pk_plan, patient_card_id, direction, date, type_operation, doc_operate_id, doc_anesthetist_id, canceled,
               ind_family, ind_name, ind_twoname, birthday FROM t_plans
        LEFT JOIN t_patient ON t_plans.patient_card_id = t_patient.card_id

        """, params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'doc_operate_id': doc_operate_id,
                                       'doc_anesthetist_id': doc_anesthetist_id, 'department_id': department})

        row = cursor.fetchall()
    return row
