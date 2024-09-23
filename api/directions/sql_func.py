from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def get_history_dir(d_s, d_e, card_id, who_create_dir, services, is_serv, iss_pk, is_parent, for_slave_hosp):
    with connection.cursor() as cursor:
        cursor.execute(
            """WITH 
        t_iss AS (SELECT 
            directions_issledovaniya.id as iss_id, 
            directions_napravleniya.client_id, 
            directory_researches.title as res_title, 
            directory_researches.id as res_id, 
            directory_researches.code, 
            directory_researches.is_hospital,
            directory_researches.is_slave_hospital,
            directory_researches.is_treatment,
            directory_researches.is_stom,
            directory_researches.is_doc_refferal,
            directory_researches.is_paraclinic,
            directory_researches.is_form,
            directory_researches.is_microbiology,
            directory_researches.is_case,
            directory_researches.podrazdeleniye_id,
            directions_napravleniya.parent_id as dir_parent_id,
            directions_napravleniya.data_sozdaniya as dir_data_sozdaniya,
            directions_napravleniya.doc_who_create_id,
            directions_issledovaniya.napravleniye_id,
            directions_napravleniya.cancel as dir_cancel,
            directions_issledovaniya.time_confirmation, 
            directions_issledovaniya.maybe_onco,
            to_char(directions_issledovaniya.time_save AT TIME ZONE %(tz)s, 'DD.MM.YYYY-HH24:MI:SS') as ch_time_save,
            directions_issledovaniya.study_instance_uid,
            directions_napravleniya.parent_slave_hosp_id as dir_parent_slave_hosp_id,
            directory_researches.is_application,
            directory_researches.is_expertise,
            person_contract.id as person_contract_id,
            person_contract.dir_list as contract_dirs,
            directions_napravleniya.hospital_id as dir_hosp,
            directions_napravleniya.rmis_number as rmis_number
        FROM directions_issledovaniya
        LEFT JOIN directory_researches
        ON directions_issledovaniya.research_id = directory_researches.Id
        LEFT JOIN directions_napravleniya
        ON directions_issledovaniya.napravleniye_id = directions_napravleniya.id
        LEFT JOIN directions_personcontract person_contract on directions_napravleniya.num_contract = person_contract.num_contract
        WHERE directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
        AND NOT directory_researches.is_expertise
        AND
        CASE
        WHEN %(is_parent)s = TRUE AND %(for_slave_hosp)s = FALSE THEN 
            directions_napravleniya.parent_id = %(iss_pk)s
        WHEN %(is_parent)s = TRUE AND %(for_slave_hosp)s = TRUE THEN
            directions_napravleniya.parent_slave_hosp_id = %(iss_pk)s
        when %(card_id)s > -1 THEN 
        directions_napravleniya.client_id = %(card_id)s
        when %(who_create)s > -1 THEN
        directions_napravleniya.doc_who_create_id = %(who_create)s
        END),
        
        t_tubes AS (SELECT tubesregistration_id, issledovaniya_id as tubes_iss_id
        FROM directions_issledovaniya_tubes
        WHERE issledovaniya_id IN (SELECT iss_id FROM t_iss)),
        
        t_iss_tubes AS (SELECT * from t_iss
        LEFT JOIN t_tubes
        ON t_iss.iss_id = t_tubes.tubes_iss_id),
        
        t_recive AS (SELECT time_recive, "number" as tube_number, id as id_t_recive FROM directions_tubesregistration
        WHERE directions_tubesregistration.id in (SELECT tubesregistration_id  FROM t_tubes)),
        
        t_podrazdeleniye AS (SELECT id AS podr_id, can_has_pacs, title AS podr_title FROM podrazdeleniya_podrazdeleniya)
        
        SELECT 
            napravleniye_id, 
            dir_cancel, 
            iss_id, 
            tube_number, 
            res_id, 
            res_title,
            to_char(dir_data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YY') as date_create,
            time_confirmation,
            to_char(time_recive AT TIME ZONE %(tz)s, 'DD.MM.YY HH24:MI:SS.US'),
            ch_time_save, 
            podr_title, 
            is_hospital, 
            maybe_onco, 
            can_has_pacs, 
            is_slave_hospital,
            is_treatment,
            is_stom,
            is_doc_refferal,
            is_paraclinic,
            is_microbiology,
            dir_parent_id,
            study_instance_uid,
            dir_parent_slave_hosp_id,
            is_form,
            is_application,
            is_expertise,
            person_contract_id,
            contract_dirs,
            dir_hosp,
            directions_napravleniya.additional_number as register_number,
            ud.family,
            ud.name,
            ud.patronymic,
            directions_napravleniya.visit_date,
            directions_napravleniya.time_microbiology_receive,
            directions_napravleniya.time_gistology_receive,
            is_case,
            directions_napravleniya.rmis_number
        FROM t_iss_tubes
        LEFT JOIN t_recive
        ON t_iss_tubes.tubesregistration_id = t_recive.id_t_recive
        LEFT JOIN t_podrazdeleniye
        ON t_iss_tubes.podrazdeleniye_id = t_podrazdeleniye.podr_id
        LEFT JOIN directions_napravleniya
        ON directions_napravleniya.id = napravleniye_id
        LEFT JOIN users_doctorprofile ud 
        ON directions_napravleniya.planed_doctor_executor_id = ud.id
        WHERE
        CASE
        WHEN %(is_serv)s = TRUE THEN 
            res_id = ANY(ARRAY[%(services_p)s])
        WHEN %(is_serv)s = FALSE THEN 
            EXISTS (SELECT res_id FROM t_iss)
        END
        
        ORDER BY napravleniye_id DESC""",
            params={
                'd_start': d_s,
                'd_end': d_e,
                'card_id': card_id,
                'who_create': who_create_dir,
                'services_p': services,
                'is_serv': is_serv,
                'tz': TIME_ZONE,
                'iss_pk': iss_pk,
                'is_parent': is_parent,
                'for_slave_hosp': for_slave_hosp,
            },
        )

        row = cursor.fetchall()
    return row


def get_directions_by_user(d_s, d_e, who_create_dir):
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT 
            directions_napravleniya.id as direction_id
        FROM directions_napravleniya
        WHERE directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
        and directions_napravleniya.doc_who_create_id in %(who_create)s
        ORDER BY directions_napravleniya.id DESC""",
            params={
                'd_start': d_s,
                'd_end': d_e,
                'who_create': who_create_dir,
                'tz': TIME_ZONE,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_patient_contract(
    d_s,
    d_e,
    card_pk,
):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT
        directions_napravleniya.num_contract,
        directions_personcontract.id,
        directions_personcontract.cancel,
        directions_personcontract.create_at,
        directions_personcontract.sum_contract,
        to_char(directions_personcontract.create_at AT TIME ZONE %(tz)s, 'DD.MM.YY') as date_create,
        directions_issledovaniya.napravleniye_id,
        directions_issledovaniya.coast,
        directions_issledovaniya.discount,
        directory_researches.title,
        directions_personcontract.dir_list
        FROM directions_issledovaniya
        LEFT JOIN directory_researches ON
        directory_researches.id=directions_issledovaniya.research_id
        LEFT JOIN directions_napravleniya ON
        directions_napravleniya.id=directions_issledovaniya.napravleniye_id
        LEFT JOIN directions_personcontract ON
        directions_personcontract.num_contract=directions_napravleniya.num_contract
        
        WHERE directions_issledovaniya.napravleniye_id::varchar in (
         select regexp_split_to_table(directions_personcontract.dir_list, ',') from directions_personcontract
            where directions_personcontract.patient_card_id=%(card_pk)s and directions_personcontract.create_at AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
        )
        order by directions_personcontract.create_at DESC
        """,
            params={
                'd_start': d_s,
                'd_end': d_e,
                'tz': TIME_ZONE,
                'card_pk': card_pk,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_lab_podr():
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT id FROM public.podrazdeleniya_podrazdeleniya
        WHERE p_type=2
        """
        )
        row = cursor.fetchall()
    return row


def get_confirm_direction(d_s, d_e, lab_podr, is_lab=False, is_paraclinic=False, is_doc_refferal=False):
    with connection.cursor() as cursor:
        cursor.execute(
            """     
        SELECT DISTINCT ON (napravleniye_id) napravleniye_id FROM public.directions_issledovaniya
        LEFT JOIN directions_napravleniya dn on directions_issledovaniya.napravleniye_id = dn.id
        WHERE time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
        AND research_id IN (SELECT id FROM directory_researches WHERE CASE
        
        WHEN  %(is_lab)s = FALSE AND %(is_paraclinic)s = TRUE AND %(is_doc_refferal)s = FALSE THEN
          is_paraclinic = TRUE
        WHEN %(is_lab)s = FALSE AND %(is_paraclinic)s = FALSE AND %(is_doc_refferal)s = TRUE THEN
          is_doc_refferal = TRUE or is_form = TRUE
        
        WHEN  %(is_lab)s = FALSE AND %(is_paraclinic)s = TRUE AND %(is_doc_refferal)s = TRUE  THEN 
          is_paraclinic = TRUE or is_doc_refferal = TRUE or is_form = TRUE
             
        WHEN %(is_lab)s = TRUE AND %(is_paraclinic)s = FALSE AND %(is_doc_refferal)s = FALSE THEN
            podrazdeleniye_id = ANY(ARRAY[%(lab_podr)s])
        
        WHEN %(is_lab)s = TRUE AND %(is_paraclinic)s = TRUE AND %(is_doc_refferal)s = FALSE THEN
          is_paraclinic = TRUE and is_doc_refferal = FALSE or podrazdeleniye_id = ANY(ARRAY[%(lab_podr)s])
        
        WHEN %(is_lab)s = TRUE AND %(is_paraclinic)s = FALSE AND %(is_doc_refferal)s = TRUE THEN
          is_paraclinic = FALSE and is_doc_refferal = TRUE or is_form = TRUE or podrazdeleniye_id = ANY(ARRAY[%(lab_podr)s])
        
        WHEN %(is_lab)s = TRUE AND %(is_paraclinic)s = TRUE AND %(is_doc_refferal)s = TRUE THEN
          is_paraclinic = TRUE or is_doc_refferal = TRUE or is_form = TRUE or podrazdeleniye_id = ANY(ARRAY[%(lab_podr)s])
        END
        )
        
        """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'is_lab': is_lab, 'is_paraclinic': is_paraclinic, 'is_doc_refferal': is_doc_refferal, 'lab_podr': lab_podr},
        )
        row = cursor.fetchall()
    return row


def filter_direction_department(list_dirs, podrazdeleniye_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT DISTINCT ON (id) id FROM public.directions_napravleniya
        WHERE id = ANY(ARRAY[%(num_dirs)s])
        AND doc_id IN (SELECT id from users_doctorprofile WHERE podrazdeleniye_id = %(podrazdeleniye_id)s)
        """,
            params={'num_dirs': list_dirs, 'podrazdeleniye_id': podrazdeleniye_id},
        )
        row = cursor.fetchall()
    return row


def filter_direction_doctor(list_dirs, doc_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT DISTINCT ON (id) id FROM public.directions_napravleniya
        WHERE id = ANY(ARRAY[%(num_dirs)s]) AND doc_id = %(doc_id)s
        """,
            params={'num_dirs': list_dirs, 'doc_id': doc_id},
        )
        row = cursor.fetchall()
    return row


def get_confirm_direction_pathology(d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """     
        SELECT DISTINCT ON (napravleniye_id) napravleniye_id FROM public.directions_issledovaniya
        WHERE time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
        AND research_id IN (SELECT id FROM public.directory_researches where title ILIKE '%%профпатолог%%')
        """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )
        row = cursor.fetchall()
    return row


def get_confirm_direction_patient_year(d_s, d_e, lab_podr, card_pk1, is_lab=False, is_paraclinic=False, is_doc_refferal=False, is_user_forms=False):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT 
            directions_napravleniya.id as direction,
            directions_issledovaniya.time_confirmation,
            to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as ch_time_confirmation,
            directions_issledovaniya.research_id,
            directory_researches.title as research_title,
            directions_issledovaniya.study_instance_uid,
            directions_issledovaniya.study_instance_uid_tag
            FROM directions_napravleniya
            INNER JOIN directions_issledovaniya ON (directions_napravleniya.id = directions_issledovaniya.napravleniye_id)
            AND directions_issledovaniya.research_id IN 
            (SELECT directory_researches.id FROM directory_researches WHERE CASE 
             WHEN %(is_lab)s = TRUE THEN directory_researches.podrazdeleniye_id = ANY(ARRAY[%(lab_podr)s])
             WHEN %(is_doc_refferal)s = TRUE THEN is_doc_refferal = TRUE or is_treatment = TRUE
             WHEN %(is_paraclinic)s = TRUE THEN is_paraclinic = TRUE
             WHEN %(is_user_forms)s = TRUE THEN can_created_patient = TRUE
             END
            )
            LEFT JOIN directory_researches ON
            directions_issledovaniya.research_id=directory_researches.id
            WHERE directions_issledovaniya.time_confirmation IS NOT NULL
            AND directions_issledovaniya.time_confirmation AT TIME ZONE 'ASIA/Irkutsk' BETWEEN %(d_start)s AND %(d_end)s
            AND NOT EXISTS (SELECT directions_issledovaniya.napravleniye_id FROM directions_issledovaniya 
                            WHERE time_confirmation IS NULL AND directions_issledovaniya.napravleniye_id = directions_napravleniya.id)
            AND client_id=%(card_pk)s
            ORDER BY directions_issledovaniya.time_confirmation DESC, directions_napravleniya.id
        """,
            params={
                'd_start': d_s,
                'd_end': d_e,
                'tz': TIME_ZONE,
                'is_lab': is_lab,
                'is_paraclinic': is_paraclinic,
                'is_doc_refferal': is_doc_refferal,
                'is_user_forms': is_user_forms,
                'lab_podr': lab_podr,
                'card_pk': card_pk1,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_confirm_direction_patient_year_is_extract(d_s, d_e, card_pk1, extract_research_pks):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT 
            directions_napravleniya.id as direction,
            directions_issledovaniya.time_confirmation,
            to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as ch_time_confirmation,
            directions_issledovaniya.research_id,
            directory_researches.title as research_title,
            directions_issledovaniya.study_instance_uid_tag
            FROM directions_napravleniya
            INNER JOIN directions_issledovaniya ON (directions_napravleniya.id = directions_issledovaniya.napravleniye_id)
            AND directions_issledovaniya.research_id IN %(extract_research_pks)s
            LEFT JOIN directory_researches ON
            directions_issledovaniya.research_id=directory_researches.id
            WHERE directions_issledovaniya.time_confirmation IS NOT NULL
            AND directions_issledovaniya.research_id in %(extract_research_pks)s
            AND directions_issledovaniya.time_confirmation AT TIME ZONE 'ASIA/Irkutsk' BETWEEN %(d_start)s AND %(d_end)s
            AND client_id=%(card_pk)s
            ORDER BY directions_issledovaniya.time_confirmation DESC, directions_napravleniya.id
        """,
            params={
                'd_start': d_s,
                'd_end': d_e,
                'tz': TIME_ZONE,
                'card_pk': card_pk1,
                'extract_research_pks': extract_research_pks,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def direction_by_card(d_s, d_e, card_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """ 
        SELECT 
            directions_issledovaniya.id as iss_id, 
            directions_issledovaniya.napravleniye_id,
            directions_issledovaniya.time_confirmation, 
            to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') date_confirm, 
            to_char(directions_issledovaniya.time_save AT TIME ZONE %(tz)s, 'DD.MM.YYYY-HH24:MI:SS') as ch_time_save,
            directions_issledovaniya.study_instance_uid,
            directory_researches.title as research_title, 
            directory_researches.id as research_id,  
            directory_researches.is_hospital,
            directory_researches.is_slave_hospital,
            directory_researches.is_treatment,
            directory_researches.is_stom,
            directory_researches.is_doc_refferal,
            directory_researches.is_paraclinic,
            directory_researches.is_form,
            directory_researches.is_microbiology,
            directory_researches.is_application,
            directory_researches.is_expertise,
            directory_researches.podrazdeleniye_id,
            directions_napravleniya.parent_slave_hosp_id,
            directions_napravleniya.client_id, 
            directions_napravleniya.parent_id,
            directions_napravleniya.data_sozdaniya,
            to_char(data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YY') as date_create,
            directions_napravleniya.cancel
        FROM directions_issledovaniya
        LEFT JOIN directory_researches
        ON directions_issledovaniya.research_id = directory_researches.id
        LEFT JOIN directions_napravleniya
        ON directions_issledovaniya.napravleniye_id = directions_napravleniya.id
        WHERE directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
        AND directions_napravleniya.client_id = %(card_id)s
        AND NOT directory_researches.is_expertise AND NOT directory_researches.is_hospital AND NOT
            directory_researches.is_slave_hospital AND NOT directory_researches.is_application

        ORDER BY directions_issledovaniya.napravleniye_id DESC""",
            params={
                'd_start': d_s,
                'd_end': d_e,
                'card_id': card_id,
                'tz': TIME_ZONE,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_type_confirm_direction(directions_tuple):
    if not directions_tuple:
        return []
    with connection.cursor() as cursor:
        cursor.execute(
            """ 
        SELECT 
            DISTINCT (directions_issledovaniya.napravleniye_id) as napravleniye_id,
            directory_researches.podrazdeleniye_id,
            directory_researches.is_stom,
            directory_researches.is_doc_refferal,
            directory_researches.is_paraclinic,
            directory_researches.is_form,
            directory_researches.is_microbiology,
            directory_researches.is_application
        FROM directions_issledovaniya
        LEFT JOIN directory_researches
        ON directions_issledovaniya.research_id = directory_researches.id
        WHERE directions_issledovaniya.napravleniye_id in %(directions_tuple)s
        ORDER BY directions_issledovaniya.napravleniye_id DESC""",
            params={
                'directions_tuple': directions_tuple,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_confirm_direction_by_hospital(hospitals, d_start, d_end, email_with_results_sent_is_false='-1'):
    with connection.cursor() as cursor:
        cursor.execute(
            """ 
        SELECT 
            DISTINCT (directions_napravleniya.id) as direction,
            directions_napravleniya.hospital_id as hospital,
            directions_napravleniya.email_with_results_sent,
            directions_napravleniya.last_confirmed_at
        FROM directions_napravleniya
        WHERE directions_napravleniya.hospital_id in %(hospitals)s and
        directions_napravleniya.last_confirmed_at AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
        AND 
            CASE WHEN %(email_with_results_sent_is_false)s != '-1' THEN
                directions_napravleniya.email_with_results_sent = false
                WHEN %(email_with_results_sent_is_false)s = '-1' THEN
                directions_napravleniya.id IS NOT NULL
            END
        ORDER BY directions_napravleniya.hospital_id
        """,
            params={'hospitals': hospitals, 'd_start': d_start, 'd_end': d_end, 'tz': TIME_ZONE, 'email_with_results_sent_is_false': email_with_results_sent_is_false},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_directions_meta_info(directions):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                    directions_issledovaniya.napravleniye_id,
                    directions_issledovaniya.research_id,
                    dr.title,
                    dr.podrazdeleniye_id,
                    dr.is_paraclinic,
                    dr.is_doc_refferal,
                    dr.is_stom,
                    dr.is_slave_hospital,
                    dr.is_microbiology,
                    dr.is_gistology,
                    dr.is_form,
                    dh.site_type,
                    to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as ch_time_confirm
                FROM directions_issledovaniya
                LEFT JOIN directory_researches dr on directions_issledovaniya.research_id = dr.id
                LEFT JOIN directory_hospitalservice dh on dr.id = dh.slave_research_id
                WHERE directions_issledovaniya.napravleniye_id in %(directions)s
                ORDER BY directions_issledovaniya.napravleniye_id
            """,
            params={'directions': directions, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_patient_open_case_data(card_pk, start_date, end_date):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                    directions_issledovaniya.id as iss_id,
                    directions_issledovaniya.napravleniye_id,
                    directions_issledovaniya.research_id,
                    dr.title,
                    dr.is_case,
                    to_char(dn.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_create
                FROM directions_issledovaniya
                LEFT JOIN directory_researches dr on directions_issledovaniya.research_id = dr.id
                LEFT JOIN directions_napravleniya dn on directions_issledovaniya.napravleniye_id = dn.id
                WHERE dn.client_id = %(card_pk)s and dr.is_case = true and directions_issledovaniya.time_confirmation is Null and
                dn.data_sozdaniya AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                ORDER BY directions_issledovaniya.napravleniye_id
            """,
            params={'card_pk': card_pk, 'tz': TIME_ZONE, 'd_start': start_date, 'd_end': end_date},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_direction_data_by_directions_id(directions):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                    directions_napravleniya.id as direction_id,
                    directions_napravleniya.client_id as client_id,
                    ci.family,
                    ci.name,
                    ci.patronymic,
                    directions_napravleniya.email_with_results_sent_to_person,
                    cc.email as patient_email
                FROM directions_napravleniya
                LEFT JOIN clients_card cc on cc.id = directions_napravleniya.client_id
                LEFT JOIN clients_individual ci on cc.individual_id = ci.id
                WHERE directions_napravleniya.id in %(directions)s
                ORDER BY directions_napravleniya.client_id
            """,
            params={
                'directions': directions,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_total_confirm_direction(d_s, d_e, lab_podr, is_lab=False, is_paraclinic=False, is_doc_refferal=False):
    with connection.cursor() as cursor:
        cursor.execute(
            """     
        SELECT DISTINCT ON (napravleniye_id) napravleniye_id FROM public.directions_issledovaniya
        LEFT JOIN directions_napravleniya dn on directions_issledovaniya.napravleniye_id = dn.id
        WHERE (time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s) AND dn.total_confirmed = true
        AND research_id IN (SELECT id FROM directory_researches WHERE CASE

        WHEN  %(is_lab)s = FALSE AND %(is_paraclinic)s = TRUE AND %(is_doc_refferal)s = FALSE THEN
          is_paraclinic = TRUE
        WHEN %(is_lab)s = FALSE AND %(is_paraclinic)s = FALSE AND %(is_doc_refferal)s = TRUE THEN
          is_doc_refferal = TRUE or is_form = TRUE

        WHEN  %(is_lab)s = FALSE AND %(is_paraclinic)s = TRUE AND %(is_doc_refferal)s = TRUE  THEN 
          is_paraclinic = TRUE or is_doc_refferal = TRUE or is_form = TRUE

        WHEN %(is_lab)s = TRUE AND %(is_paraclinic)s = FALSE AND %(is_doc_refferal)s = FALSE THEN
            podrazdeleniye_id = ANY(ARRAY[%(lab_podr)s])

        WHEN %(is_lab)s = TRUE AND %(is_paraclinic)s = TRUE AND %(is_doc_refferal)s = FALSE THEN
          is_paraclinic = TRUE and is_doc_refferal = FALSE or podrazdeleniye_id = ANY(ARRAY[%(lab_podr)s])

        WHEN %(is_lab)s = TRUE AND %(is_paraclinic)s = FALSE AND %(is_doc_refferal)s = TRUE THEN
          is_paraclinic = FALSE and is_doc_refferal = TRUE or is_form = TRUE or podrazdeleniye_id = ANY(ARRAY[%(lab_podr)s])

        WHEN %(is_lab)s = TRUE AND %(is_paraclinic)s = TRUE AND %(is_doc_refferal)s = TRUE THEN
          is_paraclinic = TRUE or is_doc_refferal = TRUE or is_form = TRUE or podrazdeleniye_id = ANY(ARRAY[%(lab_podr)s])
        END
        )

        """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'is_lab': is_lab, 'is_paraclinic': is_paraclinic, 'is_doc_refferal': is_doc_refferal, 'lab_podr': lab_podr},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_template_research_by_department(research_id, department_id, hide="true"):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT directory_paraclinictemplatename.id, directory_paraclinictemplatename.title, directory_paraclinictemplatename.hide
                FROM public.directory_paraclinictemplatenamedepartment
                INNER JOIN directory_paraclinictemplatename ON 
                directory_paraclinictemplatenamedepartment.template_name_id = directory_paraclinictemplatename.id
                WHERE
                directory_paraclinictemplatename.research_id = %(research_id)s AND
                directory_paraclinictemplatenamedepartment.department_id = %(department_id)s AND
                (directory_paraclinictemplatename.hide = %(hide)s or directory_paraclinictemplatename.hide = false)
                
                ORDER BY directory_paraclinictemplatename.id
                
                
            """,
            params={
                'research_id': research_id,
                'department_id': department_id,
                'hide': hide,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_template_field_by_department(research_id, department_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                directory_paraclinicfieldtemplatedepartment.paraclinic_field_id as field_id,
                directory_paraclinicfieldtemplatedepartment.value  
                FROM directory_paraclinicfieldtemplatedepartment
                WHERE
                directory_paraclinicfieldtemplatedepartment.department_id = %(department_id)s AND
                directory_paraclinicfieldtemplatedepartment.research_id = %(research_id)s

            """,
            params={
                'research_id': research_id,
                'department_id': department_id,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows
