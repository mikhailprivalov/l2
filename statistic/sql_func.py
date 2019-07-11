from django.db import connection

def direct_job_sql(d_conf, d_s, d_e, fin):
    with connection.cursor() as cursor:
        cursor.execute("""with 
        t_iss AS 
            (SELECT directions_napravleniya.client_id, directory_researches.title, directory_researches.code,
            directory_researches.is_first_reception, 
            directions_napravleniya.polis_n, directions_napravleniya.polis_who_give,
            directions_issledovaniya.first_time, directions_issledovaniya.napravleniye_id, 
            directions_issledovaniya.doc_confirmation_id, directions_issledovaniya.def_uet,
            directions_issledovaniya.co_executor_id, directions_issledovaniya.co_executor_uet, 
            directions_issledovaniya.co_executor2_id, directions_issledovaniya.co_executor2_uet,
            directions_issledovaniya.time_confirmation,
            directions_issledovaniya.maybe_onco, statistics_tickets_visitpurpose.title as purpose,
            directions_issledovaniya.diagnos, statistics_tickets_resultoftreatment.title as result,
            statistics_tickets_outcomes.title as outcome
            FROM directions_issledovaniya 
            LEFT JOIN directory_researches
            ON directions_issledovaniya.research_id = directory_researches.Id
            LEFT JOIN directions_napravleniya 
            ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
            LEFT JOIN statistics_tickets_visitpurpose
            ON directions_issledovaniya.purpose_id=statistics_tickets_visitpurpose.id 
            LEFT JOIN statistics_tickets_resultoftreatment
            ON directions_issledovaniya.result_reception_id=statistics_tickets_resultoftreatment.id
            LEFT JOIN statistics_tickets_outcomes
            ON directions_issledovaniya.outcome_illness_id=statistics_tickets_outcomes.id
            where (%(d_confirms)s in (directions_issledovaniya.doc_confirmation_id, directions_issledovaniya.co_executor_id,
            directions_issledovaniya.co_executor2_id))
            and time_confirmation between %(d_start)s and %(d_end)s
            and directions_napravleniya.istochnik_f_id=%(ist_fin)s
            order by time_confirmation),
        t_card AS 
            (SELECT DISTINCT ON (clients_card.id) clients_card.id, clients_card.number, clients_individual.family,clients_individual.name,
            clients_individual.patronymic,clients_individual.birthday, 
            clients_document.number, clients_document.serial, clients_document.who_give  
            FROM clients_individual
            LEFT JOIN clients_card ON clients_individual.id = clients_card.individual_id
            LEFT JOIN clients_document ON clients_card.individual_id = clients_document.individual_id
            where clients_document.document_type_id=3
            order by clients_card.id
            )
        Select * from t_iss
        left join t_card ON t_iss.client_id=t_card.id
        order by time_confirmation""",params={'d_confirms':d_conf, 'd_start':d_s, 'd_end':d_e, 'ist_fin':fin})
        row = cursor.fetchall()
    return row


def indirect_job_sql(d_conf, d_s, d_e):
    """
    Вернуть косвенные работы:
    дата, вид работы, всего(УЕТ за дату)
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute("""with t_j as (SELECT ej.type_job_id, ej.count, ej.date_job, tj.value, tj.title, 
        (ej.count*tj.value) as total
        FROM public.directions_employeejob ej
        left join public.directions_typejob tj on ej.type_job_id=tj.id
        where ej.doc_execute_id=%(d_confirms)s and ej.date_job between %(d_start)s and %(d_end)s
        Order by ej.date_job, ej.type_job_id)

        select t_j.date_job, t_j.title, sum(t_j.total) from t_j
        group by t_j.title, t_j.date_job
        order by date_job 
        """, params={'d_confirms': d_conf, 'd_start': d_s, 'd_end': d_e})
        row = cursor.fetchall()
    return row


def total_report_sql(d_conf, d_s, d_e, fin):
    """
    Возврат (нагрузку) в порядке:
    research_id, date_confirm, doc_confirmation_id, def_uet, co_executor_id, co_executor_uet,
    co_executor2_id, co_executor2_uet, research_id, research_title, research-co_executor_2_title
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute("""with iss_doc as
               (SELECT directions_napravleniya.id, d_iss.id as iss_id, d_iss.research_id, EXTRACT(DAY FROM d_iss.time_confirmation) as date_confirm, d_iss.doc_confirmation_id, d_iss.def_uet,
               d_iss.co_executor_id, d_iss.co_executor_uet, d_iss.co_executor2_id, d_iss.co_executor2_uet, d_iss.napravleniye_id
               FROM public.directions_issledovaniya d_iss
               LEFT JOIN directions_napravleniya 
               ON d_iss.napravleniye_id=directions_napravleniya.id
               where 
               (%(d_confirms)s in (d_iss.doc_confirmation_id, d_iss.co_executor_id, d_iss.co_executor2_id)) 
               and d_iss.time_confirmation between  %(d_start)s and %(d_end)s and directions_napravleniya.istochnik_f_id=%(ist_fin)s
               Order by date_confirm),  
               t_res as (SELECT d_res.id, d_res.title, co_executor_2_title
               FROM public.directory_researches d_res)

               select iss_doc.iss_id, iss_doc.research_id, iss_doc.date_confirm, iss_doc.doc_confirmation_id, iss_doc.def_uet,
               iss_doc.co_executor_id, iss_doc.co_executor_uet, iss_doc.co_executor2_id, iss_doc.co_executor2_uet,
               t_res.id, t_res.title, t_res.co_executor_2_title
               from iss_doc
               left join t_res ON iss_doc.research_id = t_res.id
               order by iss_doc.date_confirm""", params={'d_confirms': d_conf, 'd_start': d_s, 'd_end': d_e, 'ist_fin':fin})
        row = cursor.fetchall()
    return row
