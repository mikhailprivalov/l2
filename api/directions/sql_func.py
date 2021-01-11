from django.db import connection
from laboratory.settings import TIME_ZONE


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
            directory_researches.is_microbiology,
            directory_researches.podrazdeleniye_id,
            directions_napravleniya.parent_id,
            directions_napravleniya.data_sozdaniya,
            directions_napravleniya.doc_who_create_id,
            directions_issledovaniya.napravleniye_id,
            directions_napravleniya.cancel,
            directions_issledovaniya.time_confirmation, 
            directions_issledovaniya.maybe_onco,
            to_char(directions_issledovaniya.time_save AT TIME ZONE %(tz)s, 'DD.MM.YYYY-HH24:MI:SS') as ch_time_save,
            directions_issledovaniya.study_instance_uid,
            directions_napravleniya.parent_slave_hosp_id
        FROM directions_issledovaniya
        LEFT JOIN directory_researches
        ON directions_issledovaniya.research_id = directory_researches.Id
        LEFT JOIN directions_napravleniya
        ON directions_issledovaniya.napravleniye_id =directions_napravleniya.id
        WHERE directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
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
        
        t_recive AS (SELECT time_recive, id as id_t_recive FROM directions_tubesregistration
        WHERE directions_tubesregistration.id in (SELECT tubesregistration_id  FROM t_tubes)),
        
        t_podrazdeleniye AS (SELECT id AS podr_id, can_has_pacs, title AS podr_title FROM podrazdeleniya_podrazdeleniya)
        
        SELECT napravleniye_id, cancel, iss_id, tubesregistration_id, res_id, res_title,
        to_char(data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YY') as date_create,
        time_confirmation,
        to_char(time_recive AT TIME ZONE %(tz)s, 'DD.MM.YY HH24:MI:SS.US'), 
        ch_time_save, podr_title, is_hospital, maybe_onco, can_has_pacs, is_slave_hospital,
        is_treatment, is_stom, is_doc_refferal, is_paraclinic, is_microbiology, parent_id, study_instance_uid, parent_slave_hosp_id
        FROM t_iss_tubes
        LEFT JOIN t_recive
        ON t_iss_tubes.tubesregistration_id = t_recive.id_t_recive
        LEFT JOIN t_podrazdeleniye
        ON t_iss_tubes.podrazdeleniye_id = t_podrazdeleniye.podr_id
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
        WHERE time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
        AND research_id IN (SELECT id FROM directory_researches WHERE CASE
        
        WHEN  %(is_lab)s = FALSE AND %(is_paraclinic)s = TRUE AND %(is_doc_refferal)s = FALSE THEN
          is_paraclinic = TRUE
        WHEN %(is_lab)s = FALSE AND %(is_paraclinic)s = FALSE AND %(is_doc_refferal)s = TRUE THEN
          is_doc_refferal = TRUE
        
        WHEN  %(is_lab)s = FALSE AND %(is_paraclinic)s = TRUE AND %(is_doc_refferal)s = TRUE  THEN 
          is_paraclinic = TRUE or is_doc_refferal = TRUE
             
        WHEN %(is_lab)s = TRUE AND %(is_paraclinic)s = FALSE AND %(is_doc_refferal)s = FALSE THEN
            podrazdeleniye_id = ANY(ARRAY[%(lab_podr)s])
        
        WHEN %(is_lab)s = TRUE AND %(is_paraclinic)s = TRUE AND %(is_doc_refferal)s = FALSE THEN
          is_paraclinic = TRUE and is_doc_refferal = FALSE or podrazdeleniye_id = ANY(ARRAY[%(lab_podr)s])
        
        WHEN %(is_lab)s = TRUE AND %(is_paraclinic)s = FALSE AND %(is_doc_refferal)s = TRUE THEN
          is_paraclinic = FALSE and is_doc_refferal = TRUE or podrazdeleniye_id = ANY(ARRAY[%(lab_podr)s])
        
        WHEN %(is_lab)s = TRUE AND %(is_paraclinic)s = TRUE AND %(is_doc_refferal)s = TRUE THEN
          is_paraclinic = TRUE or is_doc_refferal = TRUE or podrazdeleniye_id = ANY(ARRAY[%(lab_podr)s])
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
