from django.db import connection
from laboratory.settings import TIME_ZONE

def get_history_dir(d_s, d_e, card_id, who_create_dir, services, is_serv):
    with connection.cursor() as cursor:
        cursor.execute("""WITH 
        t_iss AS (SELECT 
            directions_issledovaniya.id as iss_id, 
            directions_napravleniya.client_id, 
            directory_researches.title as res_title, 
            directory_researches.id as res_id, 
            directory_researches.code, 
            directory_researches.is_hospital,
            directory_researches.is_slave_hospital,
            directory_researches.podrazdeleniye_id,
            directions_napravleniya.data_sozdaniya,
            directions_napravleniya.doc_who_create_id,
            directions_issledovaniya.napravleniye_id,
            directions_napravleniya.cancel,
            directions_issledovaniya.doc_confirmation_id, 
            directions_issledovaniya.maybe_onco,
            to_char(directions_issledovaniya.time_save AT TIME ZONE %(tz)s, 'DD.MM.YYYY-HH24:MI:SS') as ch_time_save
        FROM directions_issledovaniya
        LEFT JOIN directory_researches
        ON directions_issledovaniya.research_id = directory_researches.Id
        LEFT JOIN directions_napravleniya
        ON directions_issledovaniya.napravleniye_id =directions_napravleniya.id
        WHERE directions_napravleniya.data_sozdaniya BETWEEN %(d_start)s AND %(d_end)s
        AND
        CASE when %(card_id)s > -1 THEN 
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
        doc_confirmation_id,
        to_char(time_recive AT TIME ZONE %(tz)s, 'DD.MM.YY HH24:MI:SS.US'), 
        ch_time_save, podr_title, is_hospital, maybe_onco, can_has_pacs, is_slave_hospital
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
        
        ORDER BY napravleniye_id DESC""", params={'d_start': d_s, 'd_end': d_e, 'card_id': card_id, 'who_create': who_create_dir,
                                                  'services_p': services, 'is_serv': is_serv, 'tz': TIME_ZONE, })

        row = cursor.fetchall()
    return row
