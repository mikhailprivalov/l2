from django.db import connection

from laboratory.settings import TIME_ZONE, DEATH_RESEARCH_PK
from statistics_tickets.models import VisitPurpose
from utils.db import namedtuplefetchall
from directory.models import Researches


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
        cursor.execute(
            """WITH
        t_iss AS 
            (SELECT directions_napravleniya.client_id, directory_researches.title, directory_researches.code,
            directory_researches.is_first_reception, 
            directions_napravleniya.polis_n, directions_napravleniya.polis_who_give,
            directions_issledovaniya.first_time, directions_issledovaniya.napravleniye_id, 
            directions_issledovaniya.doc_confirmation_id, directions_issledovaniya.def_uet,
            directions_issledovaniya.co_executor_id, directions_issledovaniya.co_executor_uet, 
            directions_issledovaniya.co_executor2_id, directions_issledovaniya.co_executor2_uet,
            directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s as datetime_confirm,
            to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm,
            to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'HH24:MI:SS') as time_confirm,
            directions_issledovaniya.maybe_onco, statistics_tickets_visitpurpose.title AS purpose,
            directions_issledovaniya.diagnos, statistics_tickets_resultoftreatment.title AS iss_result,
            statistics_tickets_outcomes.title AS outcome,
            direction_fin.title as direction_finsource_title,
            iss_fin.title as iss_finsource_title,
            directions_issledovaniya.parent_id as parent_iss_id,
            dirprice.title as dir_category_price,
            issprice.title as iss_category_price
            FROM directions_issledovaniya 
            LEFT JOIN directory_researches
            ON directions_issledovaniya.research_id = directory_researches.id
            LEFT JOIN directions_napravleniya 
            ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
            LEFT JOIN statistics_tickets_visitpurpose
            ON directions_issledovaniya.purpose_id=statistics_tickets_visitpurpose.id 
            LEFT JOIN statistics_tickets_resultoftreatment
            ON directions_issledovaniya.result_reception_id=statistics_tickets_resultoftreatment.id
            LEFT JOIN statistics_tickets_outcomes
            ON directions_issledovaniya.outcome_illness_id=statistics_tickets_outcomes.id
            LEFT JOIN directions_istochnikifinansirovaniya direction_fin
            ON directions_napravleniya.istochnik_f_id = direction_fin.id
            LEFT JOIN directions_istochnikifinansirovaniya iss_fin
            ON directions_issledovaniya.fin_source_id = iss_fin.id
            
            LEFT JOIN contracts_pricecategory issprice
            ON directions_issledovaniya.price_category_id = issprice.id
            
            LEFT JOIN contracts_pricecategory dirprice
            ON directions_napravleniya.price_category_id = dirprice.id
            
            WHERE (%(d_confirms)s in (directions_issledovaniya.doc_confirmation_id, directions_issledovaniya.co_executor_id,
            directions_issledovaniya.co_executor2_id)) 
            AND time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
            AND directory_researches.is_slave_hospital=FALSE AND directory_researches.is_hospital=FALSE
            AND 
            CASE when %(can_null)s = 1 THEN 
            directions_napravleniya.istochnik_f_id = %(ist_fin)s or directions_issledovaniya.fin_source_id = %(ist_fin)s or directions_napravleniya.istochnik_f_id is NULL
            when %(can_null)s = 0 THEN
            directions_napravleniya.istochnik_f_id = %(ist_fin)s or directions_issledovaniya.fin_source_id = %(ist_fin)s
            END 
            
            ORDER BY datetime_confirm),
        t_card AS 
            (SELECT DISTINCT ON (clients_card.id) clients_card.id, clients_card.number AS card_number, 
            clients_individual.family AS client_family, clients_individual.name AS client_name,
            clients_individual.patronymic AS client_patronymic, to_char(clients_individual.birthday, 'DD.MM.YYYY') as birthday 
            FROM clients_individual
            LEFT JOIN clients_card ON clients_individual.id = clients_card.individual_id
            ORDER BY clients_card.id)
        
        SELECT 
        title, 
        code, 
        is_first_reception, 
        polis_n, 
        polis_who_give, 
        first_time, 
        t_iss.napravleniye_id, 
        doc_confirmation_id, 
        def_uet, 
        co_executor_id, 
        co_executor_uet, 
        co_executor2_id, 
        co_executor2_uet, 
        datetime_confirm, 
        date_confirm, 
        time_confirm,
        maybe_onco, 
        purpose, 
        diagnos, 
        iss_result, 
        outcome, 
        card_number, 
        client_family, 
        client_name, 
        client_patronymic, 
        birthday, 
        direction_finsource_title, 
        iss_finsource_title,
        parent_iss_id,
        dir_category_price,
        iss_category_price
        FROM t_iss
        LEFT JOIN t_card ON t_iss.client_id=t_card.id
        ORDER BY datetime_confirm""",
            params={'d_confirms': d_conf, 'd_start': d_s, 'd_end': d_e, 'ist_fin': fin, 'can_null': can_null, 'tz': TIME_ZONE},
        )

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
        cursor.execute(
            """WITH 
        t_j AS 
            (SELECT ej.type_job_id, ej.count, ej.date_job AT TIME ZONE %(tz)s as date_job , tj.value, tj.title as title, 
            (ej.count*tj.value) as total
            FROM public.directions_employeejob ej
            LEFT JOIN public.directions_typejob tj ON ej.type_job_id=tj.id
            WHERE ej.doc_execute_id=%(d_confirms)s AND ej.date_job AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
            ORDER BY ej.date_job, ej.type_job_id)

        SELECT date_job, title, SUM(total) FROM t_j
        GROUP BY title, date_job
        ORDER BY date_job """,
            params={'d_confirms': d_conf, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

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
        cursor.execute(
            """WITH 
        iss_doc AS
           (SELECT directions_napravleniya.id, d_iss.id as iss_id, d_iss.research_id, EXTRACT(DAY FROM d_iss.time_confirmation) AS date_confirm, d_iss.doc_confirmation_id, d_iss.def_uet,
           d_iss.co_executor_id, d_iss.co_executor_uet, d_iss.co_executor2_id, d_iss.co_executor2_uet, d_iss.napravleniye_id
           FROM public.directions_issledovaniya d_iss
           LEFT JOIN directions_napravleniya 
           ON d_iss.napravleniye_id=directions_napravleniya.id
           WHERE 
           (%(d_confirms)s IN (d_iss.doc_confirmation_id, d_iss.co_executor_id, d_iss.co_executor2_id)) 
           AND d_iss.time_confirmation AT TIME ZONE %(tz)s BETWEEN  %(d_start)s AND %(d_end)s AND directions_napravleniya.istochnik_f_id=%(ist_fin)s
           ORDER BY date_confirm),  
        t_res AS 
           (SELECT d_res.id, d_res.title, co_executor_2_title
           FROM public.directory_researches d_res)

        SELECT iss_doc.iss_id, iss_doc.research_id, iss_doc.date_confirm, iss_doc.doc_confirmation_id, iss_doc.def_uet,
        iss_doc.co_executor_id, iss_doc.co_executor_uet, iss_doc.co_executor2_id, iss_doc.co_executor2_uet,
        t_res.id, t_res.title, t_res.co_executor_2_title
        FROM iss_doc
        LEFT JOIN t_res ON iss_doc.research_id = t_res.id
        ORDER BY iss_doc.date_confirm""",
            params={'d_confirms': d_conf, 'd_start': d_s, 'd_end': d_e, 'ist_fin': fin, 'tz': TIME_ZONE},
        )

        row = cursor.fetchall()
    return row


def passed_research(d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """ WITH
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
            WHERE directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s 
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
        ORDER BY client_id, data_sozdaniya""",
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        row = cursor.fetchall()
    return row


def statistics_research(research_id, d_s, d_e, hospital_id_filter, is_purpose=0, purposes=None):
    """
    На входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон, fin - источник финансирования
    выход: Физлицо, Дата рождения, Возраст, Карта, Исследование, Источник финансирования, Стоимость, Исполнитель,
        Направление, создано направление(дата), Дата подтверждения услуги, Время подтверждения.
    :return:
    """
    if not purposes:
        purposes = tuple(VisitPurpose.objects.values_list('pk').all())

    with connection.cursor() as cursor:
        cursor.execute(
            """ WITH
    t_hosp AS 
        (SELECT id, title FROM hospitals_hospitals),
    t_iss AS
        (SELECT directions_napravleniya.client_id, directions_issledovaniya.napravleniye_id as napr, directions_napravleniya.hospital_id as hospital_id,
        directions_napravleniya.vich_code as vich_code, 
        to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_confirm,
        to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'HH24:MI:SS') AS time_confirm,
        to_char(directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS create_date_napr,
        to_char(directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI:SS') AS create_time_napr, 
        directions_issledovaniya.doc_confirmation_id as doc, users_doctorprofile.fio as doc_fio,
        directions_issledovaniya.coast, directions_issledovaniya.discount,
        directions_issledovaniya.how_many, directions_napravleniya.data_sozdaniya, directions_napravleniya.istochnik_f_id,
        directions_istochnikifinansirovaniya.title as ist_f,
        directions_issledovaniya.research_id, directions_issledovaniya.time_confirmation,
        statistics_tickets_visitpurpose.title as purpose_title,
        directions_issledovaniya.purpose_id,
        dir_price_category.title as dir_category,
        iss_price_category.title as iss_category
        FROM directions_issledovaniya
        LEFT JOIN directions_napravleniya 
           ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
        LEFT JOIN users_doctorprofile
           ON directions_issledovaniya.doc_confirmation_id=users_doctorprofile.id
        LEFT JOIN directions_istochnikifinansirovaniya
        ON directions_napravleniya.istochnik_f_id=directions_istochnikifinansirovaniya.id
        LEFT JOIN statistics_tickets_visitpurpose
        ON statistics_tickets_visitpurpose.id=directions_issledovaniya.purpose_id
        LEFT JOIN contracts_pricecategory dir_price_category
        ON directions_napravleniya.price_category_id=dir_price_category.id
        LEFT JOIN contracts_pricecategory iss_price_category
        ON directions_issledovaniya.price_category_id=iss_price_category.id
        WHERE directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
        AND directions_issledovaniya.research_id=%(research_id)s 
        AND 
            CASE WHEN %(hospital_id_filter)s > 0 THEN
                directions_napravleniya.hospital_id = %(hospital_id_filter)s
                WHEN %(hospital_id_filter)s = -1 THEN
                directions_issledovaniya.napravleniye_id IS NOT NULL
            END
        AND
            CASE WHEN %(is_purpose)s = 0 THEN
                directions_issledovaniya.purpose_id in (SELECT id FROM statistics_tickets_visitpurpose) or directions_issledovaniya.purpose_id is NULL
            WHEN %(is_purpose)s = 1 THEN
                directions_issledovaniya.purpose_id in %(purposes)s
            END
           ),
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
        to_char(EXTRACT(YEAR from age(time_confirmation, date_born)), '999') as ind_age, t_hosp.title, t_iss.purpose_title, t_iss.vich_code, dir_category, iss_category FROM t_iss
        LEFT JOIN t_card ON t_iss.client_id = t_card.id
        LEFT JOIN t_hosp ON t_iss.hospital_id = t_hosp.id

        ORDER BY time_confirmation""",
            params={'research_id': research_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'hospital_id_filter': hospital_id_filter, 'purposes': purposes, 'is_purpose': is_purpose},
        )

        row = cursor.fetchall()
    return row


def statistics_research_create_directions(research_id, d_s, d_e, users_docprofile_id):
    """
    На входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон, fin - источник финансирования
    выход: Физлицо, Дата рождения, Возраст, Карта, Исследование, Источник финансирования, Стоимость, Исполнитель,
        Направление, создано направление(дата), Дата подтверждения услуги, Время подтверждения.
    :return:
    """

    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT directions_issledovaniya.napravleniye_id as napr,
        to_char(directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS create_date_napr,
        to_char(directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI:SS') AS create_time_napr, 
        directions_napravleniya.data_sozdaniya,
        directions_issledovaniya.research_id as research_id,
        d_doc.id as doctor_id,
        d_doc.family as doctor_family,
        d_doc.name as doctor_name,
        d_doc.patronymic as doctor_patronymic,
        d_from_doc.id as d_from_doc_id,
        d_from_doc.family as d_from_doc_family,
        d_from_doc.name as d_from_doc_name,
        d_from_doc.patronymic as d_from_doc_patronymic
        FROM directions_issledovaniya
        LEFT JOIN directions_napravleniya
           ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
        LEFT JOIN users_doctorprofile d_doc
        ON directions_napravleniya.doc_id = d_doc.id
        LEFT JOIN users_doctorprofile d_from_doc
        ON directions_napravleniya.doc_who_create_id = d_from_doc.id
        WHERE directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
        AND directions_issledovaniya.research_id in %(research_id)s    
        AND (d_doc.id in %(users_docprofile_id)s or d_from_doc.id in %(users_docprofile_id)s)
        ORDER BY d_from_doc_id, doctor_id
        """,
            params={'research_id': research_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'users_docprofile_id': users_docprofile_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def custom_statistics_research(research_id, d_s, d_e, filter_hospital_id, medical_exam):
    """
    на входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон
    :return:
    """
    res = Researches.objects.get(pk=research_id)
    is_form = -1
    if res.is_form:
        is_form = 1
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                directions_paraclinicresult.issledovaniye_id,
                directions_paraclinicresult.field_id,
                directions_paraclinicresult.value as field_value,
                directions_paraclinicresult.field_type as field_type,
                
                directory_paraclinicinputfield.title as field_title,
                directory_paraclinicinputfield.for_talon as field_for_talon,
                
                to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS confirm_time,
                directions_issledovaniya.napravleniye_id as direction_number,
                directions_issledovaniya.medical_examination as date_service,
                users_doctorprofile.fio as doc_fio,
                users_doctorprofile.personal_code as personal_code,
                directions_napravleniya.client_id,
                concat(clients_individual.family, ' ', clients_individual.name, ' ', clients_individual.patronymic) as patient_fio,
                
                hospitals_hospitals.title as hosp_title,
                hospitals_hospitals.okpo as hosp_okpo,
                hospitals_hospitals.okato as hosp_okato,
                
                to_char(clients_individual.birthday, 'DD.MM.YYYY') as patient_birthday,
                date_part('year', age(directions_issledovaniya.medical_examination, clients_individual.birthday))::int as patient_age,
                clients_individual.sex as patient_sex,
                clients_card.main_address as patient_main_address,
                directions_napravleniya.parent_id as parent,
                
                directions_istochnikifinansirovaniya.title as fin_source
                
                FROM public.directions_paraclinicresult
                LEFT JOIN directions_issledovaniya ON directions_issledovaniya.id = directions_paraclinicresult.issledovaniye_id
                LEFT JOIN directory_paraclinicinputfield ON directory_paraclinicinputfield.id = directions_paraclinicresult.field_id
                LEFT JOIN directions_napravleniya ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN clients_card ON clients_card.id=directions_napravleniya.client_id
                LEFT JOIN clients_individual ON clients_individual.id=clients_card.individual_id
                LEFT JOIN hospitals_hospitals on directions_napravleniya.hospital_id = hospitals_hospitals.id
                LEFT JOIN users_doctorprofile ON directions_issledovaniya.doc_confirmation_id=users_doctorprofile.id
                LEFT JOIN directions_istochnikifinansirovaniya ON directions_napravleniya.istochnik_f_id=directions_istochnikifinansirovaniya.id
                WHERE 
                  directions_issledovaniya.research_id=%(research_id)s
                  and directory_paraclinicinputfield.for_talon = true
                  and directions_issledovaniya.time_confirmation IS NOT NULL
                AND
                CASE WHEN %(filter_hospital_id)s > 0 THEN
                  directions_napravleniya.hospital_id = %(filter_hospital_id)s
                  WHEN %(filter_hospital_id)s = -1 THEN
                    directions_issledovaniya.napravleniye_id IS NOT NULL
                  END
                AND                
                CASE WHEN %(is_form)s > 0 THEN
                    directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                WHEN %(is_form)s = -1 and %(medical_exam)s = 'true' THEN
                    directions_issledovaniya.medical_examination AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s     
                WHEN %(is_form)s = -1 and %(medical_exam)s = 'false' THEN
                    directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s 
                END                
                order by directions_issledovaniya.napravleniye_id
            """,
            params={'research_id': research_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'filter_hospital_id': filter_hospital_id, 'is_form': is_form, 'medical_exam': medical_exam},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def lab_result_statistics_research(research_id, d_s, d_e, filter_hospital_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS confirm_time,
                directions_issledovaniya.napravleniye_id as direction_number,
                users_doctorprofile.family as doc_family,
                users_doctorprofile.name as doc_name,
                users_doctorprofile.patronymic as doc_patronymic,
                directions_napravleniya.client_id,
                clients_individual.family as client_family,
                clients_individual.name as client_name,
                clients_individual.patronymic as client_patronymic,
                to_char(clients_individual.birthday, 'DD.MM.YYYY') as patient_birthday,
                date_part('year', age(directions_issledovaniya.time_confirmation, clients_individual.birthday))::int as patient_age,
                clients_individual.sex as patient_sex,
                clients_card.main_address as patient_main_address,
                directions_napravleniya.parent_id as parent,
                directions_istochnikifinansirovaniya.title as fin_source,
                df.title as field_title,
                directions_result.value as field_value
                FROM directions_result
                LEFT JOIN directions_issledovaniya ON directions_issledovaniya.id = directions_result.issledovaniye_id
                LEFT JOIN directions_napravleniya ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN clients_card ON clients_card.id=directions_napravleniya.client_id
                LEFT JOIN clients_individual ON clients_individual.id=clients_card.individual_id
                LEFT JOIN hospitals_hospitals on directions_napravleniya.hospital_id = hospitals_hospitals.id
                LEFT JOIN users_doctorprofile ON directions_napravleniya.doc_id=users_doctorprofile.id
                LEFT JOIN directions_istochnikifinansirovaniya ON directions_napravleniya.istochnik_f_id=directions_istochnikifinansirovaniya.id
                LEFT JOIN directory_fractions df on directions_result.fraction_id = df.id 
                WHERE 
                  directions_issledovaniya.research_id=%(research_id)s
                AND                
                     directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s 
                order by directions_issledovaniya.napravleniye_id
            """,
            params={'research_id': research_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'filter_hospital_id': filter_hospital_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def statistics_death_research(research_id: object, d_s: object, d_e: object, filter_hospital_id) -> object:
    """
    на входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                directions_paraclinicresult.issledovaniye_id,
                directions_paraclinicresult.field_id,
                directory_paraclinicinputfield.title,
                directions_paraclinicresult.value,
                to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS confirm_time,
                directions_paraclinicresult.value_json::json as json_value,
                value_json::jsonb #>> '{rows, 0, 2}' as diag,
                concat(value_json::jsonb #>> '{title}', value_json::jsonb #>> '{rows, 0, 2}') as result,
                directions_issledovaniya.napravleniye_id,
                directions_napravleniya.client_id,
                concat(clients_individual.family, ' ', clients_individual.name, ' ', clients_individual.patronymic) as fio_patient,
                clients_individual.sex,
                hospitals_hospitals.title as hosp_title,
                hospitals_hospitals.okpo as hosp_okpo,
                hospitals_hospitals.okato as hosp_okato,
                directions_napravleniya.hospital_id
                FROM public.directions_paraclinicresult
                LEFT JOIN directions_issledovaniya
                ON directions_issledovaniya.id = directions_paraclinicresult.issledovaniye_id
                LEFT JOIN directory_paraclinicinputfield
                ON directory_paraclinicinputfield.id = directions_paraclinicresult.field_id
                LEFT JOIN directions_napravleniya
                ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN clients_card ON clients_card.id=directions_napravleniya.client_id
                LEFT JOIN clients_individual ON clients_individual.id=clients_card.individual_id
                LEFT JOIN hospitals_hospitals on directions_napravleniya.hospital_id = hospitals_hospitals.id
                WHERE
                CASE
                WHEN %(filter_hospital_id)s > 0 THEN
                    issledovaniye_id in (
                        SELECT id FROM public.directions_issledovaniya
                        WHERE research_id = %(research_id)s and (time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s)
                        )
                    AND
                    directions_napravleniya.hospital_id = %(filter_hospital_id)s
                WHEN %(filter_hospital_id)s = -1 THEN
                    issledovaniye_id in (
                        SELECT id FROM public.directions_issledovaniya
                        WHERE research_id = %(research_id)s and (time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s)
                        )
                END
                order by issledovaniye_id
            """,
            params={'research_id': research_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'death_research_id': DEATH_RESEARCH_PK, 'filter_hospital_id': filter_hospital_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def temp_statistics_covid_call_patient(research_id, d_s, d_e, field_title, search_date):
    """
    на входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                directions_paraclinicresult.issledovaniye_id
                FROM public.directions_paraclinicresult
                LEFT JOIN directions_issledovaniya
                ON directions_issledovaniya.id = directions_paraclinicresult.issledovaniye_id
                LEFT JOIN directory_paraclinicinputfield
                ON directory_paraclinicinputfield.id = directions_paraclinicresult.field_id
                WHERE
                issledovaniye_id in (
                        SELECT id FROM public.directions_issledovaniya
                        WHERE research_id = %(research_id)s and (time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s)
                        )
                AND 
                directory_paraclinicinputfield.title=%(field_title)s AND directions_paraclinicresult.value = %(search_date)s 
                order by issledovaniye_id
            """,
            params={'research_id': research_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'field_title': field_title, 'search_date': search_date},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def statistics_covid_call_patient(research_id, d_s, d_e, field_title, iss_tuple):
    """
    на входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                directions_paraclinicresult.issledovaniye_id,
                directions_paraclinicresult.field_id,
                directory_paraclinicinputfield.title,
                directions_paraclinicresult.value,
                to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS confirm_time,
                directions_issledovaniya.napravleniye_id,
                directions_napravleniya.client_id,
                concat(clients_individual.family, ' ', clients_individual.name, ' ', clients_individual.patronymic) as fio_patient,
                clients_card.number
                FROM public.directions_paraclinicresult
                LEFT JOIN directions_issledovaniya
                ON directions_issledovaniya.id = directions_paraclinicresult.issledovaniye_id
                LEFT JOIN directory_paraclinicinputfield
                ON directory_paraclinicinputfield.id = directions_paraclinicresult.field_id
                LEFT JOIN directions_napravleniya
                ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN clients_card ON clients_card.id=directions_napravleniya.client_id
                LEFT JOIN clients_individual ON clients_individual.id=clients_card.individual_id
                WHERE
                issledovaniye_id in %(iss_tuple)s AND directory_paraclinicinputfield.title in %(field_title)s
                order by issledovaniye_id
            """,
            params={'research_id': research_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'field_title': field_title, 'iss_tuple': iss_tuple},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def statistics_reserved_number_death_research(research_id: object, d_s: object, d_e: object, filter_hospital_id) -> object:
    """
    на входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                directions_paraclinicresult.issledovaniye_id,
                directions_paraclinicresult.field_id,
                directory_paraclinicinputfield.title,
                directions_paraclinicresult.value,
                directions_issledovaniya.napravleniye_id,
                directions_napravleniya.client_id,
                to_char(directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_create,
                concat(clients_individual.family, ' ', clients_individual.name, ' ', clients_individual.patronymic) as fio_patient,
                clients_individual.sex,
                hospitals_hospitals.title as hosp_title,
                hospitals_hospitals.okpo as hosp_okpo,
                hospitals_hospitals.okato as hosp_okato,
                directions_napravleniya.hospital_id
                FROM public.directions_paraclinicresult
                LEFT JOIN directions_issledovaniya
                ON directions_issledovaniya.id = directions_paraclinicresult.issledovaniye_id
                LEFT JOIN directory_paraclinicinputfield
                ON directory_paraclinicinputfield.id = directions_paraclinicresult.field_id
                LEFT JOIN directions_napravleniya
                ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN clients_card ON clients_card.id=directions_napravleniya.client_id
                LEFT JOIN clients_individual ON clients_individual.id=clients_card.individual_id
                LEFT JOIN hospitals_hospitals on directions_napravleniya.hospital_id = hospitals_hospitals.id
                where
                CASE
                WHEN %(filter_hospital_id)s > 0 THEN
                    issledovaniye_id in (
                        SELECT id FROM public.directions_issledovaniya
                        WHERE research_id = %(death_research_id)s and (time_confirmation is Null) and directory_paraclinicinputfield.title='Номер' and
                directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                        )
                    AND
                    directions_napravleniya.hospital_id = %(filter_hospital_id)s
                WHEN %(filter_hospital_id)s = -1 THEN
                    issledovaniye_id in (
                SELECT id FROM public.directions_issledovaniya
                where research_id = %(death_research_id)s and time_confirmation is Null) and directory_paraclinicinputfield.title='Номер' and
                directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                END                                
                order by hospitals_hospitals.title, directions_napravleniya.data_sozdaniya
            """,
            params={'research_id': research_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'death_research_id': DEATH_RESEARCH_PK, 'filter_hospital_id': filter_hospital_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def statistics_sum_research_by_lab(podrazdeleniye: tuple, d_s: object, d_e: object) -> object:
    """
    на входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                    podrazdeleniya_podrazdeleniya.title as lab_title,
                    directory_researches.title as research_title, 
                    COUNT(research_id) as sum_research_id 
                FROM public.directions_issledovaniya
                LEFT JOIN directory_researches
                ON directory_researches.id = directions_issledovaniya.research_id
                LEFT JOIN podrazdeleniya_podrazdeleniya
                ON podrazdeleniya_podrazdeleniya.id = directory_researches.podrazdeleniye_id
                where research_id in (select id from directory_researches WHERE podrazdeleniye_id in %(podrazdeleniye)s) and 
                    time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                GROUP BY directory_researches.title, directory_researches.podrazdeleniye_id, podrazdeleniya_podrazdeleniya.title
                ORDER BY podrazdeleniya_podrazdeleniya.title, directory_researches.title
                            """,
            params={'podrazdeleniye': podrazdeleniye, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def statistics_details_research_by_lab(podrazdeleniye: tuple, d_s: object, d_e: object) -> object:
    """
    на входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                    directions_issledovaniya.napravleniye_id,
                    podrazdeleniya_podrazdeleniya.title as lab_title,
                    directory_researches.title as research_title,
                    to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_confirm,
                    to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'HH24:MI') AS time_confirm,
                    api_application.name,
                    directions_issledovaniya.time_confirmation,
                    directions_issledovaniya.id,
                    tubes.date_tubes,
                    tubes.time_tubes
                FROM public.directions_issledovaniya
                LEFT JOIN directory_researches
                ON directory_researches.id = directions_issledovaniya.research_id
                LEFT JOIN api_application
                ON api_application.id = directions_issledovaniya.api_app_id
                LEFT JOIN podrazdeleniya_podrazdeleniya
                ON podrazdeleniya_podrazdeleniya.id = directory_researches.podrazdeleniye_id
                LEFT JOIN (
                    SELECT issledovaniya_id,
                    tubesregistration_id,
                    to_char(directions_tubesregistration.time_get AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_tubes,
                    to_char(directions_tubesregistration.time_get AT TIME ZONE %(tz)s, 'HH24:MI') AS time_tubes,
                    "number" as tube_number
                    FROM directions_issledovaniya_tubes
                    LEFT JOIN directions_tubesregistration
                    ON directions_tubesregistration.id = directions_issledovaniya_tubes.tubesregistration_id
                ) as tubes
                ON tubes.issledovaniya_id = directions_issledovaniya.id
                where research_id in (select id from directory_researches  WHERE podrazdeleniye_id in %(podrazdeleniye)s) and 
                time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                ORDER BY podrazdeleniya_podrazdeleniya.title, directory_researches.title
                            """,
            params={'podrazdeleniye': podrazdeleniye, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def statistics_consolidate_research(d_s, d_e, fin_source_pk, is_research_set=-1, researches_id=None):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                    directions_issledovaniya.napravleniye_id as dir_id,
                    directory_researches.title as research_title,
                    to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_confirm,
                    directions_issledovaniya.time_confirmation,
                    users_doctorprofile.family as doc_f,
                    users_doctorprofile.name as doc_n,
                    users_doctorprofile.patronymic as doc_p,
                    users_speciality.title as doc_speciality,
                    directions_napravleniya.client_id,
                    directions_napravleniya.workplace as patient_workplace,
                    directions_napravleniya.harmful_factor as dir_harmful_factor,
                    cc.harmful_factor as patient_card_harmful_factor,
                    cc.number as patient_card_num,
                    ci.family as patient_family,
                    ci.name as patient_name,
                    ci.patronymic as patient_patronymic,
                    ci.birthday as patient_born,
                    date_part('year', age(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, ci.birthday))::int as patient_age,
                    directions_issledovaniya.parent_id as parent_iss,
                    directions_issledovaniya.id as id_iss,
                    directions_napravleniya.purpose,
                    contracts_pricecategory.title as category_title,
                    directions_napravleniya.doc_who_create_id,
                    directions_napravleniya.doc_id,
                    user_doc.family as user_doc_f,
                    user_doc.name as user_doc_n,
                    user_doc.patronymic as user_doc_p,
                    doc_who_create.family as doc_who_create_f,
                    doc_who_create.name as doc_who_create_n,
                    doc_who_create.patronymic as doc_who_create_p
                FROM public.directions_issledovaniya
                LEFT JOIN directory_researches
                ON directory_researches.id = directions_issledovaniya.research_id
                LEFT JOIN directions_napravleniya
                ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN users_doctorprofile
                ON users_doctorprofile.id = directions_issledovaniya.doc_confirmation_id
                LEFT JOIN users_doctorprofile doc_who_create
                ON doc_who_create.id = directions_napravleniya.doc_who_create_id
                LEFT JOIN users_doctorprofile user_doc
                ON user_doc.id = directions_napravleniya.doc_id
                LEFT JOIN users_speciality
                ON users_doctorprofile.specialities_id = users_speciality.id
                LEFT JOIN clients_card cc 
                ON directions_napravleniya.client_id = cc.id
                LEFT JOIN clients_individual ci 
                ON ci.id = cc.individual_id
                LEFT JOIN contracts_pricecategory
                ON contracts_pricecategory.id = directions_issledovaniya.price_category_id
                where time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s AND (
                            directions_issledovaniya.fin_source_id=%(fin_source_pk)s or 
                            directions_napravleniya.istochnik_f_id=%(fin_source_pk)s or 
                            directions_napravleniya.istochnik_f_id is NULL
                        )
                      AND  
                      CASE WHEN %(is_research_set)s > 0 THEN
                          directory_researches.id in %(researches_id)s
                      WHEN %(is_research_set)s = -1 THEN
                        directions_issledovaniya.napravleniye_id IS NOT NULL
                      END
                ORDER BY directions_napravleniya.client_id, directions_issledovaniya.time_confirmation, directions_issledovaniya.id 
                            """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'fin_source_pk': fin_source_pk, 'is_research_set': is_research_set, 'researches_id': researches_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def statistics_by_research_sets_company(d_s, d_e, fin_source_pk, researches, company_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                    directions_issledovaniya.napravleniye_id as dir_id,
                    directions_issledovaniya.research_id,
                    to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_confirm,
                    directions_issledovaniya.time_confirmation,
                    directions_napravleniya.client_id,
                    cc.number as patient_card_num,
                    ci.family as patient_family,
                    ci.name as patient_name,
                    ci.patronymic as patient_patronymic,
                    ci.birthday as patient_born,
                    date_part('year', age(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, ci.birthday))::int as patient_age,
                    contracts_companydepartment.title as department_title,
                    contracts_companydepartment.id as department_id,
                    contracts_company.title as company_title,
                    directions_issledovaniya.coast
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN clients_card cc
                ON directions_napravleniya.client_id = cc.id
                LEFT JOIN clients_individual ci 
                ON ci.id = cc.individual_id
                LEFT JOIN contracts_company
                ON cc.work_place_db_id = contracts_company.id
                LEFT JOIN contracts_companydepartment
                ON cc.work_department_db_id = contracts_companydepartment.id
                WHERE time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s 
                        AND (
                            directions_issledovaniya.fin_source_id=%(fin_source_pk)s or 
                            directions_napravleniya.istochnik_f_id=%(fin_source_pk)s or 
                            directions_napravleniya.istochnik_f_id is NULL
                        ) 
                        AND cc.work_place_db_id = %(company_id)s
                        AND directions_issledovaniya.research_id in %(researches)s
                ORDER BY 
                    contracts_companydepartment.id, 
                    directions_napravleniya.client_id, 
                    directions_issledovaniya.time_confirmation
                            """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'fin_source_pk': fin_source_pk, 'researches': researches, 'company_id': company_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def statistics_research_by_hospital_for_external_orders(d_s, d_e, hospital_id, fin_source_pk):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                    directions_issledovaniya.napravleniye_id as dir_id,
                    directions_issledovaniya.research_id,
                    directory_researches.title as research_title,
                    to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_confirm,
                    directions_issledovaniya.time_confirmation,
                    directions_napravleniya.client_id,
                    cc.number as patient_card_num,
                    ci.family as patient_family,
                    ci.name as patient_name,
                    ci.patronymic as patient_patronymic,
                    to_char(ci.birthday,'DD.MM.YYYY') as ru_date_born,
                    date_part('year', age(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, ci.birthday))::int as patient_age,
                    dtr.number as tube_number
                FROM directions_issledovaniya
                LEFT JOIN directions_issledovaniya_tubes dit
                ON directions_issledovaniya.id = dit.issledovaniya_id
                
                LEFT JOIN directions_tubesregistration dtr
                ON dit.tubesregistration_id = dtr.id
                
                LEFT JOIN directory_researches 
                ON directory_researches.id=directions_issledovaniya.research_id
                LEFT JOIN directions_napravleniya
                ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN clients_card cc
                ON directions_napravleniya.client_id = cc.id
                LEFT JOIN clients_individual ci 
                ON ci.id = cc.individual_id
                
                WHERE time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s 
                        AND (
                            directions_issledovaniya.fin_source_id=%(fin_source_pk)s or 
                            directions_napravleniya.istochnik_f_id=%(fin_source_pk)s
                        ) 
                        AND
                        directions_napravleniya.hospital_id = %(hospital_id)s
                ORDER BY 
                    directions_napravleniya.client_id, 
                    directions_issledovaniya.time_confirmation
                            """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'fin_source_pk': fin_source_pk, 'hospital_id': hospital_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def statistics_registry_profit(d_s, d_e, fin_source_pk):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                    directions_issledovaniya.research_id,
                    dr.title as research_title,
                    contracts_company.title as company_title,
                    contracts_company.id as company_id, 
                    directions_issledovaniya.doc_confirmation_string,
                    directions_issledovaniya.doc_confirmation_id,
                    positions.title as position_title,
                    dp.family as doc_family,
                    dp.name as doc_name,
                    dp.patronymic as doc_patronymic
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN directory_researches dr on directions_issledovaniya.research_id = dr.id
                LEFT JOIN clients_card cc
                ON directions_napravleniya.client_id = cc.id
                LEFT JOIN contracts_company
                ON cc.work_place_db_id = contracts_company.id
                LEFT JOIN users_doctorprofile dp
                ON dp.id = directions_issledovaniya.doc_confirmation_id
                LEFT JOIN users_position positions
                ON positions.id = dp.position_id
                WHERE time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s 
                        AND (
                            directions_issledovaniya.fin_source_id=%(fin_source_pk)s or 
                            directions_napravleniya.istochnik_f_id=%(fin_source_pk)s
                        ) 
                ORDER BY
                    directions_issledovaniya.doc_confirmation_id,
                    directions_issledovaniya.research_id
                                        
                            """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'fin_source_pk': fin_source_pk},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def consolidate_doctors_by_type_department(d_s, d_e, fin_source_pk, doctors_pk):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                    directions_issledovaniya.napravleniye_id as dir_id,
                    directions_issledovaniya.research_id,
                    directory_researches.title as research_title,
                    directory_researches.uet_refferal_doc,
                    to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_confirm,
                    directions_issledovaniya.time_confirmation,
                    directions_napravleniya.client_id,
                    cc.number as patient_card_num,
                    ci.family as patient_family,
                    ci.name as patient_name,
                    ci.patronymic as patient_patronymic,
                    ci.birthday as patient_born,
                    directions_issledovaniya.doc_confirmation_id,
                    ud.family,
                    ud.name,
                    ud.patronymic,
                    pp.title as department_title,
                    ud.id as doctor_id,
                    pp.id as department_id,
                    directions_napravleniya.istochnik_f_id
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN clients_card cc
                ON directions_napravleniya.client_id = cc.id
                LEFT JOIN clients_individual ci 
                ON ci.id = cc.individual_id
                LEFT JOIN users_doctorprofile ud on 
                directions_issledovaniya.doc_confirmation_id = ud.id
                LEFT JOIN podrazdeleniya_podrazdeleniya pp on 
                ud.podrazdeleniye_id = pp.id
                LEFT JOIN directory_researches on
                directory_researches.id=directions_issledovaniya.research_id
                WHERE time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s 
                        AND (
                            directions_issledovaniya.fin_source_id in %(fin_source_pk)s or 
                            directions_napravleniya.istochnik_f_id in %(fin_source_pk)s
                        ) 
                        AND directions_issledovaniya.doc_confirmation_id in %(doctors_pk)s
                ORDER BY 
                    pp.id, ud.id, directions_issledovaniya.research_id, directions_issledovaniya.time_confirmation
            """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'fin_source_pk': fin_source_pk, 'doctors_pk': doctors_pk},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def consolidate_middle_staff_by_type_department(d_s, d_e, fin_source_pk, middle_staf):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                    directions_issledovaniya.napravleniye_id as dir_id,
                    directions_issledovaniya.research_id,
                    directory_researches.title as research_title,
                    directory_researches.uet_refferal_co_executor_1,
                    to_char(directions_napravleniya.visit_date AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS visit_date,
                    directions_napravleniya.visit_date,
                    directions_napravleniya.client_id,
                    cc.number as patient_card_num,
                    ci.family as patient_family,
                    ci.name as patient_name,
                    ci.patronymic as patient_patronymic,
                    ci.birthday as patient_born,
                    directions_napravleniya.visit_who_mark_id,
                    ud.family,
                    ud.name,
                    ud.patronymic,
                    pp.title,
                    ud.id as doctor_id,
                    pp.id as department_id,
                    directions_napravleniya.istochnik_f_id
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN clients_card cc
                ON directions_napravleniya.client_id = cc.id
                LEFT JOIN clients_individual ci 
                ON ci.id = cc.individual_id
                LEFT JOIN users_doctorprofile ud on 
                directions_napravleniya.visit_who_mark_id = ud.id
                LEFT JOIN podrazdeleniya_podrazdeleniya pp on 
                ud.podrazdeleniye_id = pp.id
                LEFT JOIN directory_researches on
                directory_researches.id=directions_issledovaniya.research_id
                WHERE directions_napravleniya.visit_date AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s 
                        AND (
                            directions_issledovaniya.fin_source_id in %(fin_source_pk)s or 
                            directions_napravleniya.istochnik_f_id in %(fin_source_pk)s
                        ) 
                        AND directions_napravleniya.visit_who_mark_id in %(middle_staf)s
                ORDER BY 
                    pp.id, ud.id, directions_issledovaniya.research_id, directions_napravleniya.visit_date
            """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'fin_source_pk': fin_source_pk, 'middle_staf': middle_staf},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def disp_diagnos(diagnos, d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """WITH
            t_iss AS (
            SELECT id, diagnos, illnes, date_start, date_end, why_stop, card_id, 
                        doc_end_reg_id, doc_start_reg_id, spec_reg_id 
            FROM public.clients_dispensaryreg
            WHERE diagnos = 'U999' and (date_start AT TIME ZONE %(tz)s
            BETWEEN %(d_start)s AND %(d_end)s OR date_end AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s)
            ORDER BY date_start DESC),
            t_card AS (SELECT id as card_id, individual_id, number as num_card from clients_card WHERE id in (SELECT card_id from t_iss)),
            
            t_ind AS (SELECT family as p_family, name as p_name, patronymic as p_patr, birthday, t_card.card_id, t_card.num_card 
                  FROM clients_individual
            LEFT JOIN t_card ON t_card.individual_id = id 
            where id in (SELECT individual_id from t_card)),
            
            t_doc_start AS (SELECT id as docstart_id, fio from users_doctorprofile where id in (SELECT doc_start_reg_id from t_iss) ),
            t_doc_end AS (SELECT id as docend_id, fio from users_doctorprofile where id in (SELECT doc_end_reg_id from t_iss) )
            
            SELECT concat(p_family, ' ', p_name, ' ', p_patr) as patient, 
            to_char(t_ind.birthday, 'DD.MM.YYYY') as birthday,
            t_ind.num_card, 
            t_doc_start.fio as doc_start, 
            to_char(date_start, 'DD.MM.YYYY') as date_start,
            t_doc_end.fio as doc_stop, 
            to_char(date_end, 'DD.MM.YYYY') as date_end
            FROM t_iss
            LEFT JOIN t_ind ON t_iss.card_id = t_ind.card_id
            LEFT JOIN t_doc_start ON t_iss.doc_start_reg_id = t_doc_start.docstart_id
            LEFT JOIN t_doc_end ON t_iss.doc_end_reg_id = t_doc_end.docend_id
            ORDER by patient
            """,
            params={'diagnos': diagnos, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )
        row = cursor.fetchall()
    return row


def message_ticket(hospitals_id, d_s, d_e):
    """
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """ 
            SELECT 
                doctor_call_doctorcall.id as num,
                doctor_call_doctorcall.external_num,
                to_char(doctor_call_doctorcall.create_at AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_create,
                doctor_call_doctorcall.comment,
                doctor_call_doctorcall.phone,
                doctor_call_doctorcall.address,
                doctor_call_doctorcall.email,	  
                doc_call_hospital.title as hospital_title,
                doc_call_hospital.short_title as hospital_short_title,
                doctor_call_doctorcall.purpose,
                doctor_call_doctorcall.status,
                clients_individual.name,
                clients_individual.family,
                clients_individual.patronymic,
                to_char(clients_individual.birthday, 'DD.MM.YYYY') as birthday,
                doctor_call_doctorcall.hospital_id as hospital_id,
                doctor_call_doctorcall.is_external,
                users_doctorprofile.fio,
                who_create_hospital.short_title
                FROM doctor_call_doctorcall
                LEFT JOIN hospitals_hospitals as doc_call_hospital ON (doc_call_hospital.id=doctor_call_doctorcall.hospital_id)
                LEFT JOIN clients_card ON clients_card.id=doctor_call_doctorcall.client_id
                LEFT JOIN clients_individual ON clients_individual.id=clients_card.individual_id
                LEFT JOIN users_doctorprofile ON users_doctorprofile.id=doctor_call_doctorcall.doc_who_create_id
                LEFT JOIN hospitals_hospitals as who_create_hospital ON (who_create_hospital.id=users_doctorprofile.hospital_id)
                WHERE doctor_call_doctorcall.create_at AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s 
                AND doctor_call_doctorcall.hospital_id = ANY(%(hospitals_id)s)
                ORDER BY doctor_call_doctorcall.hospital_id, doctor_call_doctorcall.create_at 
 
            """,
            params={'hospitals_id': hospitals_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def message_ticket_purpose_total(hospitals_id, d_s, d_e):
    """
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """ 
            WITH 
                total_doc_call AS (
                  SELECT
                  purpose as total_purpose, 
                  COUNT(purpose) as sum_total_purpose
                  FROM doctor_call_doctorcall as total_dc
                  WHERE create_at AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s AND total_dc.hospital_id = ANY(%(hospitals_id)s)
                  GROUP BY purpose
                ),
                
                execut_doc_call AS (
                  SELECT purpose as execute_purpose, 
                  COUNT(purpose) as sum_execute_purpose
                  FROM doctor_call_doctorcall as exec_dc
                  WHERE create_at AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s AND STATUS=3 AND exec_dc.hospital_id = ANY(%(hospitals_id)s)
                  GROUP BY purpose)
                
                SELECT total_purpose, sum_total_purpose, execute_purpose, sum_execute_purpose
                    FROM total_doc_call
                    LEFT JOIN execut_doc_call ON execut_doc_call.execute_purpose = total_doc_call.total_purpose
            """,
            params={'hospitals_id': hospitals_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def attached_female_on_month(last_day_month_for_age, min_age, max_age):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(id) FROM clients_card
            WHERE clients_card.individual_id IN 
              (SELECT id FROM clients_individual WHERE (date_part('year', age(%(last_day_month_for_age)s, birthday))::int BETWEEN %(min_age)s and %(max_age)s) and sex='ж')
            """,
            params={
                'last_day_month_for_age': last_day_month_for_age,
                'min_age': min_age,
                'max_age': max_age,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def screening_plan_for_month_all_count(date_plan_year, date_plan_month):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(DISTINCT card_id) FROM public.clients_screeningregplan
            WHERE date_part('year', clients_screeningregplan.date)::int = %(date_plan_year)s AND
            date_part('month', clients_screeningregplan.date)::int = %(date_plan_month)s
            """,
            params={
                'date_plan_year': date_plan_year,
                'date_plan_month': date_plan_month,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def screening_plan_for_month_all_patient(date_plan_year, date_plan_month):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT ON (card_id) card_id FROM public.clients_screeningregplan
            WHERE date_part('year', clients_screeningregplan.date)::int = %(date_plan_year)s AND
            date_part('month', clients_screeningregplan.date)::int = %(date_plan_month)s
            """,
            params={
                'date_plan_year': date_plan_year,
                'date_plan_month': date_plan_month,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def must_dispensarization_from_screening_plan_for_month(year, month, date_dispansarization):
    with connection.cursor() as cursor:
        cursor.execute(
            """
          SELECT count(distinct dispensarisation.card_id) FROM 
            (SELECT 
                  clients_screeningregplan.card_id, 
                  directory_dispensaryroutesheet.research_id as dispensarisation_research
                FROM clients_screeningregplan
                LEFT JOIN clients_card
                ON clients_card.id=clients_screeningregplan.card_id
            
                LEFT JOIN clients_individual
                ON clients_individual.id=clients_card.individual_id
                LEFT JOIN directory_dispensaryroutesheet
                ON 
                  clients_screeningregplan.research_id=directory_dispensaryroutesheet.research_id AND
                  directory_dispensaryroutesheet.age_client = date_part('year', age(%(date_dispansarization)s, clients_individual.birthday))::int AND
                  clients_individual.sex = directory_dispensaryroutesheet.sex_client
                WHERE date_part('year', clients_screeningregplan.date)::int = %(screening_date_plan_year)s AND
                date_part('month', clients_screeningregplan.date)::int = %(screening_date_plan_month)s
                ORDER BY clients_screeningregplan.card_id) dispensarisation
                WHERE dispensarisation.dispensarisation_research is NOT NULL
            """,
            params={
                'screening_date_plan_year': year,
                'screening_date_plan_month': month,
                'date_dispansarization': date_dispansarization,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def sql_pass_screening(year, month, start_time_confirm, end_time_confirm, list_card):
    if not list_card:
        return []

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(distinct client_result.client_id) FROM 
                (SELECT
                    distinct on (directions_napravleniya.client_id, directions_issledovaniya.research_id)
                    date_part('year', directions_issledovaniya.time_confirmation) as year_date,
                    date_part('month', directions_issledovaniya.time_confirmation) as month_date,
                    date_part('day', directions_issledovaniya.time_confirmation) as day_date, 
                    directions_issledovaniya.id as iss_id, 
                    directions_napravleniya.client_id as client_id, 
                    directions_issledovaniya.napravleniye_id as dir_id,
                    directions_issledovaniya.research_id as research_id,
                    directions_issledovaniya.time_confirmation as confirm
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                WHERE 
                    directions_napravleniya.client_id in %(list_card)s
                AND
                    directions_issledovaniya.research_id in (SELECT 
                        distinct on (clients_screeningregplan.research_id) clients_screeningregplan.research_id 
                        FROM clients_screeningregplan WHERE date_part('year', clients_screeningregplan.date)::int = %(screening_date_plan_year)s AND
                        date_part('month', clients_screeningregplan.date)::int = %(screening_date_plan_month)s) 
                AND
                    (directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(start_time_confirm)s AND %(end_time_confirm)s)
                ORDER BY 
                    directions_napravleniya.client_id, 
                    directions_issledovaniya.research_id, 
                    directions_issledovaniya.time_confirmation DESC) client_result
            """,
            params={
                'screening_date_plan_year': year,
                'screening_date_plan_month': month,
                'start_time_confirm': start_time_confirm,
                'end_time_confirm': end_time_confirm,
                'list_card': list_card,
                'tz': TIME_ZONE,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def sql_pass_screening_in_dispensarization(year, month, start_time_confirm, end_time_confirm, date_dispansarization):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT count(distinct client_result.client_id) FROM 
                    (SELECT
                        distinct on (directions_napravleniya.client_id, directions_issledovaniya.research_id)
                        directions_napravleniya.client_id as client_id, 
                        directions_issledovaniya.napravleniye_id as dir_id,
                        directions_issledovaniya.research_id as research_id,
                        directions_issledovaniya.time_confirmation as confirm
                    FROM directions_issledovaniya
                    LEFT JOIN directions_napravleniya
                    ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                    WHERE 
                        directions_napravleniya.client_id in 
                        (
                            SELECT distinct ON (dispensarisation_card.card_id) dispensarisation_card.card_id FROM 
                                (
                                    SELECT clients_screeningregplan.card_id, directory_dispensaryroutesheet.research_id as dispensarisation_research
                                        FROM clients_screeningregplan
                                        LEFT JOIN clients_card
                                        ON clients_card.id=clients_screeningregplan.card_id
                                        
                                        LEFT JOIN clients_individual
                                        ON clients_individual.id=clients_card.individual_id
                                        LEFT JOIN directory_dispensaryroutesheet
                                        ON 
                                        clients_screeningregplan.research_id=directory_dispensaryroutesheet.research_id AND
                                        directory_dispensaryroutesheet.age_client = date_part('year', age(%(date_dispansarization)s, clients_individual.birthday))::int AND
                                        clients_individual.sex = directory_dispensaryroutesheet.sex_client
                                    WHERE date_part('year', clients_screeningregplan.date)::int = %(screening_date_plan_year)s AND
                                          date_part('month', clients_screeningregplan.date)::int = %(screening_date_plan_month)s
                                    ORDER BY clients_screeningregplan.card_id
                                ) dispensarisation_card
                            WHERE dispensarisation_card.dispensarisation_research is NOT NULL
                        )
                    AND
                        directions_issledovaniya.research_id in 
                        (
                            SELECT distinct on (dispensarisation.research_id) dispensarisation.research_id FROM
                                (
                                    SELECT  directory_dispensaryroutesheet.research_id, directory_dispensaryroutesheet.research_id as dispensarisation_research
                                        FROM clients_screeningregplan
                                        LEFT JOIN clients_card
                                        ON clients_card.id=clients_screeningregplan.card_id
                                        
                                        LEFT JOIN clients_individual
                                        ON clients_individual.id=clients_card.individual_id
                                        LEFT JOIN directory_dispensaryroutesheet
                                        ON 
                                        clients_screeningregplan.research_id=directory_dispensaryroutesheet.research_id AND
                                        directory_dispensaryroutesheet.age_client = date_part('year', age(%(date_dispansarization)s, clients_individual.birthday))::int AND
                                        clients_individual.sex = directory_dispensaryroutesheet.sex_client
                                    WHERE date_part('year', clients_screeningregplan.date)::int = %(screening_date_plan_year)s AND
                                          date_part('month', clients_screeningregplan.date)::int = %(screening_date_plan_month)s
                                    ORDER BY clients_screeningregplan.card_id
                                ) dispensarisation
                                WHERE dispensarisation.dispensarisation_research is NOT NULL
                        ) 
                    AND
                    (directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(start_time_confirm)s AND %(end_time_confirm)s)  
                    ORDER BY directions_napravleniya.client_id, directions_issledovaniya.research_id, directions_issledovaniya.time_confirmation DESC) client_result
            """,
            params={
                'screening_date_plan_year': year,
                'screening_date_plan_month': month,
                'start_time_confirm': start_time_confirm,
                'end_time_confirm': end_time_confirm,
                'date_dispansarization': date_dispansarization,
                'tz': TIME_ZONE,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def sql_pass_pap_analysis_count(start_time_confirm, end_time_confirm, list_card, pap_id_analysis):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(distinct result_papa.client_id) FROM
                (SELECT
                    distinct on (directions_napravleniya.client_id, directions_issledovaniya.research_id)
                    directions_napravleniya.client_id as client_id, 
                    directions_issledovaniya.napravleniye_id as dir_id,
                    directions_issledovaniya.research_id as research_id,
                    directions_issledovaniya.time_confirmation as confirm
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                WHERE 
                directions_napravleniya.client_id in %(list_card)s
                AND
                directions_issledovaniya.research_id in %(pap_id_analysis)s
                AND
                (directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(start_time_confirm)s AND %(end_time_confirm)s)  
                ORDER BY directions_napravleniya.client_id, directions_issledovaniya.research_id, directions_issledovaniya.time_confirmation DESC)
            result_papa  
            """,
            params={'start_time_confirm': start_time_confirm, 'end_time_confirm': end_time_confirm, 'list_card': list_card, 'pap_id_analysis': pap_id_analysis, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def sql_pass_pap_fraction_result_value(start_time_confirm, end_time_confirm, list_card, pap_id_analysis, fraction_id, value_result1, value_result2="", count_param=1):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(distinct client_result.client_id) FROM 
                (SELECT
                distinct on (directions_napravleniya.client_id, directions_issledovaniya.research_id)
                directions_napravleniya.client_id as client_id, 
                directions_issledovaniya.napravleniye_id as dir_id,
                directions_issledovaniya.research_id as research_id,
                directions_issledovaniya.time_confirmation as confirm,
                directions_result.value,
                directions_result.fraction_id
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                LEFT JOIN directions_result
                ON directions_result.issledovaniye_id=directions_issledovaniya.id 
                WHERE 
                directions_napravleniya.client_id in %(list_card)s
                AND
                directions_issledovaniya.research_id in %(pap_id_analysis)s
                AND
                (directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(start_time_confirm)s AND %(end_time_confirm)s)
                AND
                directions_result.fraction_id in %(fraction_id)s
                AND 
                    CASE WHEN %(count_param)s > 1 THEN
                      directions_result.value ~ %(value_result1)s or directions_result.value ~ %(value_result2)s
                    ELSE
                      directions_result.value ~ %(value_result1)s
                    END
                ORDER BY directions_napravleniya.client_id, 
                directions_issledovaniya.research_id, 
                directions_issledovaniya.time_confirmation DESC) 
            client_result
            """,
            params={
                'start_time_confirm': start_time_confirm,
                'end_time_confirm': end_time_confirm,
                'list_card': list_card,
                'pap_id_analysis': pap_id_analysis,
                'fraction_id': fraction_id,
                'tz': TIME_ZONE,
                'count_param': count_param,
                'value_result1': value_result1,
                'value_result2': value_result2,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def sql_card_dublicate_pass_pap_fraction_not_not_enough_adequate_result_value(
    start_time_confirm, end_time_confirm, list_card, pap_id_analysis, fraction_id, value_result1, value_result2="", count_param=1
):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT client_result.client_id FROM
             (SELECT
                directions_napravleniya.client_id as client_id
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                LEFT JOIN directions_result
                ON directions_result.issledovaniye_id=directions_issledovaniya.id 
                WHERE 
                directions_napravleniya.client_id in %(list_card)s
                AND
                directions_issledovaniya.research_id in %(pap_id_analysis)s
                AND
                (directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(start_time_confirm)s AND %(end_time_confirm)s)
                AND
                directions_result.fraction_id in %(fraction_id)s
                AND 
                    CASE WHEN %(count_param)s > 1 THEN
                      directions_result.value ILIKE %(value_result1)s or  directions_result.value ILIKE %(value_result2)s
                    ELSE
                      directions_result.value ILIKE %(value_result1)s
                    END
                ORDER BY directions_napravleniya.client_id, 
                directions_issledovaniya.research_id, 
                directions_issledovaniya.time_confirmation) client_result
                group by client_result.client_id having count(client_result.client_id)>1
            """,
            params={
                'start_time_confirm': start_time_confirm,
                'end_time_confirm': end_time_confirm,
                'list_card': list_card,
                'pap_id_analysis': pap_id_analysis,
                'fraction_id': fraction_id,
                'tz': TIME_ZONE,
                'count_param': count_param,
                'value_result1': value_result1,
                'value_result2': value_result2,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def sql_get_result_by_direction(pk, d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT
                    directions_napravleniya.client_id as client_id, 
                    to_char(directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s, 'YYYY-MM-DD') as date_create,
                    directions_issledovaniya.napravleniye_id as dir_id,
                    directions_issledovaniya.research_id as research_id,
                    to_char((directions_issledovaniya.time_confirmation - interval '1 day') AT TIME ZONE %(tz)s, 'YYYY-MM-DD') as date_reciev,
                    to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'YYYY-MM-DD') as date_confirm,
                    clients_individual.family,
                    clients_individual.name,
                    clients_individual.patronymic,
                    clients_individual.birthday,
                    to_char(clients_individual.birthday AT TIME ZONE %(tz)s, 'YYYY-MM-DD') as born,
                    clients_individual.sex,
                    directions_result.id,
                    directions_result.value,
                    directions_result.fraction_id,
                    hospitals_hospitals.title as hosp_title,
                    hospitals_hospitals.ogrn as hosp_ogrn,
                    dr.title as research_title,
                    dr.code as research_code,
                    dm.title as method_title
                    FROM directions_issledovaniya
                    LEFT JOIN directions_napravleniya
                    ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                    LEFT JOIN directions_result
                    ON directions_result.issledovaniye_id=directions_issledovaniya.id
                    LEFT JOIN clients_card ON clients_card.id=directions_napravleniya.client_id
                    LEFT JOIN clients_individual ON clients_individual.id=clients_card.individual_id
                    LEFT JOIN hospitals_hospitals on directions_napravleniya.hospital_id = hospitals_hospitals.id
                    LEFT JOIN directory_researches dr on directions_issledovaniya.research_id = dr.id
                    LEFT JOIN directory_methodlaboratoryanalisis dm on dr.method_lab_default_id = dm.id
                    WHERE
                        directions_issledovaniya.research_id = %(pk)s
                    AND
                    (directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s)
                            """,
            params={'pk': pk, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def sql_get_documents_by_card_id(card_tuple):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                clients_carddocusage.document_id,
                clients_carddocusage.card_id,
                clients_document.id,
                clients_document.serial,
                clients_document.number,
                clients_document.is_active,
                clients_document.document_type_id
            FROM clients_carddocusage 
            LEFT JOIN  clients_document on clients_document.id=clients_carddocusage.document_id
            WHERE clients_carddocusage.card_id in %(cards)s
            """,
            params={
                'cards': card_tuple,
            },
        )

        rows = namedtuplefetchall(cursor)
    return rows


def sql_get_date_death(pk_research, d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                    DISTINCT ON (directions_napravleniya.client_id) directions_napravleniya.client_id,
                    directions_issledovaniya.napravleniye_id as dir_id,
                    directions_issledovaniya.research_id as research_id,
                    directions_issledovaniya.time_confirmation as confirm,
                    directions_paraclinicresult.id,
                    directions_paraclinicresult.value,
                    directions_paraclinicresult.field_id,
                    directory_paraclinicinputfield.title
                    FROM directions_issledovaniya
                    LEFT JOIN directions_napravleniya
                    ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                    LEFT JOIN directions_paraclinicresult
                    ON directions_paraclinicresult.issledovaniye_id=directions_issledovaniya.id
                    LEFT JOIN clients_card ON clients_card.id=directions_napravleniya.client_id
                    LEFT JOIN clients_individual ON clients_individual.id=clients_card.individual_id
                    LEFT JOIN hospitals_hospitals on directions_napravleniya.hospital_id = hospitals_hospitals.id
                    LEFT JOIN directory_paraclinicinputfield on directions_paraclinicresult.field_id = directory_paraclinicinputfield.id
                    WHERE
                        directions_issledovaniya.research_id = %(pk)s AND directory_paraclinicinputfield.title = 'Дата смерти'
                    AND
                        (directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s)
                    ORDER BY 
                        directions_napravleniya.client_id, directions_issledovaniya.time_confirmation DESC
                            
            """,
            params={'pk': pk_research, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def card_has_death_date(research_id: object, d_s: object, d_e: object) -> object:
    """
    на входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                clients_card.id,
                clients_card.death_date
                FROM clients_card 
                where clients_card.death_date BETWEEN %(d_start)s AND %(d_end)s
            """,
            params={'research_id': research_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'death_research_id': DEATH_RESEARCH_PK},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def statistics_death_research_by_card(research_id, card_tuple, hospital_id_filter):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                directions_issledovaniya.napravleniye_id,
                directions_paraclinicresult.issledovaniye_id,
                directions_paraclinicresult.field_id,
                directory_paraclinicinputfield.title,
                directions_paraclinicresult.value,
                to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS confirm_time,
                directions_paraclinicresult.value_json::json as json_value,
                value_json::jsonb #>> '{rows, 0, 2}' as diag,
                concat(value_json::jsonb #>> '{title}', value_json::jsonb #>> '{rows, 0, 2}') as result,
                directions_napravleniya.client_id,
                concat(clients_individual.family, ' ', clients_individual.name, ' ', clients_individual.patronymic) as fio_patient,
                clients_individual.sex,
                hospitals_hospitals.title as hosp_title,
                hospitals_hospitals.okpo as hosp_okpo,
                hospitals_hospitals.okato as hosp_okato,
                directions_napravleniya.hospital_id
                FROM public.directions_paraclinicresult
                LEFT JOIN directions_issledovaniya
                ON directions_issledovaniya.id = directions_paraclinicresult.issledovaniye_id
                LEFT JOIN directory_paraclinicinputfield
                ON directory_paraclinicinputfield.id = directions_paraclinicresult.field_id
                LEFT JOIN directions_napravleniya
                ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN clients_card ON clients_card.id=directions_napravleniya.client_id
                LEFT JOIN clients_individual ON clients_individual.id=clients_card.individual_id
                LEFT JOIN hospitals_hospitals on directions_napravleniya.hospital_id = hospitals_hospitals.id
                where 
                CASE 
                WHEN %(hospital_id_filter)s = -1 THEN
                    directions_napravleniya.client_id in %(cards)s and (directions_issledovaniya.time_confirmation NOTNULL) and 
                    directions_issledovaniya.research_id=%(death_research_id)s
                WHEN %(hospital_id_filter)s > 0 THEN
                    directions_napravleniya.client_id in %(cards)s and (directions_issledovaniya.time_confirmation NOTNULL) and 
                    directions_issledovaniya.research_id=%(death_research_id)s AND
                    directions_napravleniya.hospital_id = %(hospital_id_filter)s 
                END
                order by directions_napravleniya.client_id, directions_issledovaniya.time_confirmation DESC
            """,
            params={'cards': card_tuple, 'research_id': research_id, 'tz': TIME_ZONE, 'death_research_id': DEATH_RESEARCH_PK, 'hospital_id_filter': hospital_id_filter},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def statistics_dispanserization(researches_tuple, d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                directions_issledovaniya.napravleniye_id,
                to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS confirm_time,
                directions_issledovaniya.time_confirmation,
                directions_issledovaniya.research_id,
                directions_issledovaniya.doc_confirmation_id,
                directions_issledovaniya.result_reception_id,
                directions_issledovaniya.purpose_id,
                concat(ud.family, ' ', ud.name, ' ', ud.patronymic) as fio_doctor
                FROM directions_issledovaniya
                LEFT JOIN users_doctorprofile ud on directions_issledovaniya.doc_confirmation_id = ud.id
                WHERE directions_issledovaniya.research_id in %(researches_tuple)s
                AND directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                ORDER BY directions_issledovaniya.doc_confirmation_id
            """,
            params={'researches_tuple': researches_tuple, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def dispansery_plan(d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT  
                distinct on (month, cc.id)
                to_char(date, 'MM-YYYY') as month,
                cc.number,
                ci.family, ci.name, ci.patronymic, 
                to_char(ci.birthday, 'DD.MM.YYYY') as born,
                cc.id as card_id
                FROM public.clients_dispensaryregplans
                LEFT JOIN clients_card cc on clients_dispensaryregplans.card_id=cc.id
                LEFT JOIN clients_individual ci on cc.individual_id=ci.id
                WHERE date AT TIME ZONE %(tz)s BETWEEN %(d_start)s and %(d_end)s
                order by month desc, card_id

            """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def dispansery_card_diagnos(cards):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT distinct on (diagnos, card_id) diagnos, card_id
            FROM clients_dispensaryreg
            WHERE card_id in %(cards)s and date_end is NULL
            ORDER BY card_id
            """,
            params={'cards': cards},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def dispansery_registered_by_year_age(age_param, date_param, junior=1):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT distinct on (card_id) 
                card_id
                from clients_dispensaryreg
                LEFT JOIN clients_card cc on clients_dispensaryreg.card_id=cc.id
                LEFT JOIN clients_individual ci on cc.individual_id=ci.id
                WHERE 
                CASE 
                WHEN %(junior)s=1 then
                    date_end is NULL and date_part('year', age(timestamp %(date_param)s, ci.birthday))::int < %(age_param)s
                WHEN %(junior)s=0 then
                    date_end is NULL and date_part('year', age(timestamp %(date_param)s, ci.birthday))::int >= %(age_param)s
                END
            """,
            params={'age_param': age_param, 'date_param': date_param, 'junior': junior},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def doctors_pass_count_patient_by_date(doctors_tuple, d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                 SELECT
                        directions_issledovaniya.doc_confirmation_id,
                        to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS confirm_time,
                        to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'YYYY.MM.DD') AS confirm_time_sort,
                        count(dn.client_id)
                    FROM directions_issledovaniya
                    LEFT JOIN directions_napravleniya dn on directions_issledovaniya.napravleniye_id = dn.id
                    WHERE directions_issledovaniya.doc_confirmation_id in %(doctors_tuple)s
                    AND directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                    GROUP by 
                        directions_issledovaniya.doc_confirmation_id, 
                        confirm_time,
                        confirm_time_sort
                    ORDER BY 
                        directions_issledovaniya.doc_confirmation_id,
                        confirm_time_sort
            """,
            params={'doctors_tuple': doctors_tuple, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_pair_iss_direction(iss_tuple):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                 SELECT
                    directions_issledovaniya.id as iss_pk,
                    directions_issledovaniya.napravleniye_id as direction_pk   
                FROM directions_issledovaniya
                WHERE directions_issledovaniya.id in %(iss_tuple)s
                    
            """,
            params={'iss_tuple': iss_tuple},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_all_harmful_factors_templates():
    with connection.cursor() as cursor:
        cursor.execute(
            """
                 SELECT
                    clients_harmfulfactor.id as harmfulfactor_id,
                    clients_harmfulfactor.title as harmfulfactor_title,
                    clients_harmfulfactor.description,
                    ut.title as template_title,
                    ut.id as template_id
                FROM clients_harmfulfactor
                LEFT JOIN users_assignmenttemplates ut on 
                clients_harmfulfactor.template_id = ut.id
                ORDER BY harmfulfactor_title
            """
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_researches_by_templates(template_ids):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                 SELECT
                    users_assignmentresearches.template_id,
                    users_assignmentresearches.research_id, 
                    dr.title
                FROM users_assignmentresearches
                LEFT JOIN directory_researches dr on dr.id = users_assignmentresearches.research_id
                WHERE users_assignmentresearches.template_id in %(template_ids)s
            """,
            params={'template_ids': template_ids},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_confirm_protocol_by_date_extract(field_ids, d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                directions_napravleniya.id as direction_protocol_extract, 
                directions_napravleniya.parent_id, 
                dd.napravleniye_id as direction_main_extract_dir,
                rd.title as main_extract_research,
                pd.id as iss_protocol_extract
                FROM
                directions_napravleniya
                LEFT JOIN directions_issledovaniya dd on directions_napravleniya.parent_id = dd.id
                LEFT JOIN directions_issledovaniya pd on directions_napravleniya.id = pd.napravleniye_id
                LEFT JOIN directory_researches rd on rd.id = dd.research_id
                
                WHERE directions_napravleniya.id in 
                (SELECT 
                napravleniye_id
                from directions_issledovaniya
                where id in (select issledovaniye_id
                FROM public.directions_paraclinicresult
                where field_id in %(field_ids)s and
                value BETWEEN %(d_start)s AND %(d_end)s) and 
                directions_issledovaniya.time_confirmation is NOT NULL)
            """,
            params={
                'field_ids': field_ids,
                'd_start': d_s,
                'd_end': d_e,
            },
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_expertise_grade(parent_ids):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
              grade_data.grade_iss as grade_expertise_iss, 
              level_data.level_iss as level_data_iss, 
              directions_issledovaniya.doc_confirmation_id as doc_id,
              directions_napravleniya.parent_id,
              grade_data.grade_value,
              level_data.level_value
            FROM directions_issledovaniya
            LEFT JOIN directions_napravleniya
            ON directions_napravleniya.id=directions_issledovaniya.napravleniye_id
            LEFT JOIN (
                SELECT
                  issledovaniye_id as level_iss, 
                  value as level_value
                FROM directions_paraclinicresult
                LEFT JOIN directory_paraclinicinputfield
                ON directions_paraclinicresult.field_id = directory_paraclinicinputfield.id
                WHERE 
                directory_paraclinicinputfield.title = 'Уровень экспертизы'
                ) as level_data
            ON directions_issledovaniya.id=level_data.level_iss
            
            LEFT JOIN (
                SELECT 
                  issledovaniye_id as grade_iss, 
                  value as grade_value
                FROM directions_paraclinicresult
                LEFT JOIN directory_paraclinicinputfield
                ON directions_paraclinicresult.field_id = directory_paraclinicinputfield.id
                WHERE 
                directory_paraclinicinputfield.title = 'Общее количество баллов'
                ) as grade_data
            ON directions_issledovaniya.id=grade_data.grade_iss
            
            WHERE 
            directions_issledovaniya.time_confirmation is not null
            AND
            directions_issledovaniya.napravleniye_id in
            (SELECT id FROM directions_napravleniya WHERE
            parent_id in %(parent_ids)s)
            """,
            params={'parent_ids': parent_ids},
        )

        rows = namedtuplefetchall(cursor)
    return rows
