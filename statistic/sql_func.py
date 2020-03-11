from django.db import connection
from laboratory.settings import TIME_ZONE


def direct_job_sql(d_conf, d_s, d_e, fin, can_null):
    """
    парам: d_conf - doctor_confirm, d_s - date-start,  d_e - date-end,  fin - источник финансирвоания

    Вернуть:
    Услуги оказанные врачом за периодн с доп параметрами

    в SQL:
    t_iss - это временная таблица запроса для исследований
    t_card - это временная таблица запроса для карт
    """

    with connection.cursor() as cursor:
        cursor.execute("""WITH
        t_iss AS 
            (SELECT directions_napravleniya.client_id, directory_researches.title, directory_researches.code,
            directory_researches.is_first_reception, 
            directions_napravleniya.polis_n, directions_napravleniya.polis_who_give,
            directions_issledovaniya.first_time, directions_issledovaniya.napravleniye_id, 
            directions_issledovaniya.doc_confirmation_id, directions_issledovaniya.def_uet,
            directions_issledovaniya.co_executor_id, directions_issledovaniya.co_executor_uet, 
            directions_issledovaniya.co_executor2_id, directions_issledovaniya.co_executor2_uet,
            directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s AS datetime_confirm,
            to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm,
            to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'HH24:MI:SS') as time_confirm,
            
            directions_issledovaniya.maybe_onco, statistics_tickets_visitpurpose.title AS purpose,
            directions_issledovaniya.diagnos, statistics_tickets_resultoftreatment.title AS iss_result,
            statistics_tickets_outcomes.title AS outcome
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
            WHERE (%(d_confirms)s in (directions_issledovaniya.doc_confirmation_id, directions_issledovaniya.co_executor_id,
            directions_issledovaniya.co_executor2_id)) 
            AND time_confirmation BETWEEN %(d_start)s AND %(d_end)s
            AND 
            CASE when %(can_null)s = 1 THEN 
            directions_napravleniya.istochnik_f_id = %(ist_fin)s or directions_napravleniya.istochnik_f_id is NULL
            when %(can_null)s = 0 THEN
            directions_napravleniya.istochnik_f_id = %(ist_fin)s
            END 
            
            ORDER BY datetime_confirm),
        t_card AS 
            (SELECT DISTINCT ON (clients_card.id) clients_card.id, clients_card.number AS card_number, 
            clients_individual.family AS client_family, clients_individual.name AS client_name,
            clients_individual.patronymic AS client_patronymic, to_char(clients_individual.birthday, 'DD.MM.YYYY') as birthday, 
            clients_document.number, clients_document.serial, clients_document.who_give 
            FROM clients_individual
            LEFT JOIN clients_card ON clients_individual.id = clients_card.individual_id
            LEFT JOIN clients_document ON clients_card.individual_id = clients_document.individual_id          
            WHERE clients_document.document_type_id=(SELECT id AS polis_id FROM clients_documenttype  WHERE title = 'Полис ОМС')
            ORDER BY clients_card.id)
        
        SELECT title, code, is_first_reception, polis_n, polis_who_give, first_time, napravleniye_id, doc_confirmation_id, 
        def_uet, co_executor_id, co_executor_uet, co_executor2_id, co_executor2_uet, datetime_confirm, date_confirm, time_confirm,
        maybe_onco, purpose, diagnos, iss_result, outcome, card_number, client_family, client_name, client_patronymic, birthday FROM t_iss
        LEFT JOIN t_card ON t_iss.client_id=t_card.id
        ORDER BY datetime_confirm""", params={'d_confirms': d_conf, 'd_start': d_s, 'd_end': d_e, 'ist_fin': fin, 'can_null': can_null, 'tz': TIME_ZONE})

        row = cursor.fetchall()
    return row


def indirect_job_sql(d_conf, d_s, d_e):
    """
    парам:  d_conf - doctor_confirm, d_s - date-start, d_e - date-end

    Вернуть косвенные работы:
    дата, вид работы, всего(УЕТ за дату)

    В SQL:
    t_j - это временная таблица запроса для исследований
    ej - сокращенное наименование от employeejob
    tj - сокращенное наименование от directions_typejob
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute("""WITH 
        t_j AS 
            (SELECT ej.type_job_id, ej.count, ej.date_job AT TIME ZONE %(tz)s as date_job , tj.value, tj.title as title, 
            (ej.count*tj.value) as total
            FROM public.directions_employeejob ej
            LEFT JOIN public.directions_typejob tj ON ej.type_job_id=tj.id
            WHERE ej.doc_execute_id=%(d_confirms)s AND ej.date_job BETWEEN %(d_start)s AND %(d_end)s
            ORDER BY ej.date_job, ej.type_job_id)

        SELECT date_job, title, SUM(total) FROM t_j
        GROUP BY title, date_job
        ORDER BY date_job """, params={'d_confirms': d_conf, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE})

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
        cursor.execute("""WITH 
        iss_doc AS
           (SELECT directions_napravleniya.id, d_iss.id as iss_id, d_iss.research_id, EXTRACT(DAY FROM d_iss.time_confirmation) AS date_confirm, d_iss.doc_confirmation_id, d_iss.def_uet,
           d_iss.co_executor_id, d_iss.co_executor_uet, d_iss.co_executor2_id, d_iss.co_executor2_uet, d_iss.napravleniye_id
           FROM public.directions_issledovaniya d_iss
           LEFT JOIN directions_napravleniya 
           ON d_iss.napravleniye_id=directions_napravleniya.id
           WHERE 
           (%(d_confirms)s IN (d_iss.doc_confirmation_id, d_iss.co_executor_id, d_iss.co_executor2_id)) 
           AND d_iss.time_confirmation BETWEEN  %(d_start)s AND %(d_end)s AND directions_napravleniya.istochnik_f_id=%(ist_fin)s
           ORDER BY date_confirm),  
        t_res AS 
           (SELECT d_res.id, d_res.title, co_executor_2_title
           FROM public.directory_researches d_res)

        SELECT iss_doc.iss_id, iss_doc.research_id, iss_doc.date_confirm, iss_doc.doc_confirmation_id, iss_doc.def_uet,
        iss_doc.co_executor_id, iss_doc.co_executor_uet, iss_doc.co_executor2_id, iss_doc.co_executor2_uet,
        t_res.id, t_res.title, t_res.co_executor_2_title
        FROM iss_doc
        LEFT JOIN t_res ON iss_doc.research_id = t_res.id
        ORDER BY iss_doc.date_confirm""", params={'d_confirms': d_conf, 'd_start': d_s, 'd_end': d_e, 'ist_fin': fin})

        row = cursor.fetchall()
    return row


def passed_research(d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(""" WITH
        t_iss AS
            (SELECT directions_napravleniya.client_id, directory_researches.title,
            directions_napravleniya.polis_n, directions_napravleniya.polis_who_give,
            directions_issledovaniya.napravleniye_id, 
            to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY-HH24:MI:SS') AS t_confirm,
            to_char(directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY-HH24:MI:SS') AS create_napr,
            to_char(directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI:SS') AS time_napr,
            directions_issledovaniya.diagnos, statistics_tickets_resultoftreatment.title as result, 
            directions_issledovaniya.id AS iss_id, directions_napravleniya.data_sozdaniya
            FROM directions_issledovaniya
            LEFT JOIN directory_researches 
                ON directions_issledovaniya.research_id = directory_researches.Id
            LEFT JOIN directions_napravleniya 
                ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
            LEFT JOIN statistics_tickets_resultoftreatment 
                ON directions_issledovaniya.result_reception_id=statistics_tickets_resultoftreatment.id
            WHERE directions_napravleniya.data_sozdaniya BETWEEN %(d_start)s AND %(d_end)s 
            AND directions_issledovaniya.time_confirmation IS NOT NULL
            AND TRUE IN (directory_researches.is_paraclinic, directory_researches.is_doc_refferal, 
            directory_researches.is_stom, directory_researches.is_hospital)
            ),
        t_card AS
            (SELECT DISTINCT ON (clients_card.id) clients_card.id, clients_card.number as num_card, clients_individual.family,
            clients_individual.name AS ind_name, clients_individual.patronymic, to_char(clients_individual.birthday, 'DD.MM.YYYY') as birthday,
            clients_document.number, clients_document.serial, clients_document.who_give, clients_card.main_address,
            clients_card.fact_address, clients_card.work_place
            FROM clients_individual
            LEFT JOIN clients_card ON clients_individual.id = clients_card.individual_id
            LEFT JOIN clients_document ON clients_card.individual_id = clients_document.individual_id
            WHERE clients_document.document_type_id = (SELECT id AS polis_id FROM clients_documenttype WHERE title = 'Полис ОМС')
            ORDER BY clients_card.id),
            t_field AS
            (SELECT id AS f_is FROM directory_paraclinicinputfield
            WHERE directory_paraclinicinputfield.title='Кем направлен')

        SELECT client_id, title, polis_n, polis_who_give, napravleniye_id, t_confirm, create_napr, diagnos, result, 
        data_sozdaniya, num_card, family, ind_name, patronymic, birthday, main_address, fact_address, work_place, 
        directions_paraclinicresult.value, time_napr FROM t_iss
        LEFT JOIN t_card ON t_iss.client_id = t_card.id
        LEFT JOIN directions_paraclinicresult ON t_iss.iss_id = directions_paraclinicresult.issledovaniye_id
        AND (directions_paraclinicresult.field_id IN (SELECT * FROM t_field))
        ORDER BY client_id, data_sozdaniya""", params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE})

        row = cursor.fetchall()
    return row


def statistics_research(research_id, d_s, d_e):
    """
    на входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон, fin - источник финансирования
    выход: Физлицо, Дата рождения, Возраст, Карта, Исследование, Источник финансирования, Стоимость, Исполнитель,
        Направление, создано направление(дата), Дата подтверждения услуги, Время подтверждения.
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(""" WITH
    t_iss AS
        (SELECT directions_napravleniya.client_id, directions_issledovaniya.napravleniye_id as napr, 
        to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_confirm,
        to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'HH24:MI:SS') AS time_confirm,
        to_char(directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS create_date_napr,
        to_char(directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI:SS') AS create_time_napr, 
        directions_issledovaniya.doc_confirmation_id as doc, users_doctorprofile.fio as doc_fio,
        directions_issledovaniya.coast, directions_issledovaniya.discount,
        directions_issledovaniya.how_many, directions_napravleniya.data_sozdaniya, directions_napravleniya.istochnik_f_id,
        directions_istochnikifinansirovaniya.title as ist_f,
        directions_issledovaniya.research_id, directions_issledovaniya.time_confirmation
        FROM directions_issledovaniya
        LEFT JOIN directions_napravleniya 
           ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
        LEFT JOIN users_doctorprofile
           ON directions_issledovaniya.doc_confirmation_id=users_doctorprofile.id
        LEFT JOIN directions_istochnikifinansirovaniya
        ON directions_napravleniya.istochnik_f_id=directions_istochnikifinansirovaniya.id 
        WHERE directions_issledovaniya.time_confirmation BETWEEN %(d_start)s AND %(d_end)s
        AND directions_issledovaniya.research_id=%(research_id)s),
    t_card AS
       (SELECT DISTINCT ON (clients_card.id) clients_card.id, clients_card.number AS num_card, 
        clients_individual.family as ind_family,
        clients_individual.name AS ind_name, clients_individual.patronymic, 
        to_char(clients_individual.birthday, 'DD.MM.YYYY') as birthday,
        clients_individual.birthday as date_born
        FROM clients_individual
        LEFT JOIN clients_card ON clients_individual.id = clients_card.individual_id)

        SELECT napr, date_confirm, time_confirm, create_date_napr, create_time_napr, doc_fio, coast, discount, 
        how_many, ((coast + (coast/100 * discount)) * how_many)::NUMERIC(10,2) AS sum_money, ist_f, time_confirmation, num_card, 
        ind_family, ind_name, patronymic, birthday, date_born,
        to_char(EXTRACT(YEAR from age(time_confirmation, date_born)), '999') as ind_age FROM t_iss
        LEFT JOIN t_card ON t_iss.client_id = t_card.id
        ORDER BY time_confirmation""", params={'research_id': research_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE})

        row = cursor.fetchall()
    return row
