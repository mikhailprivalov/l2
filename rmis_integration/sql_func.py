from django.db import connection
from laboratory.settings import TIME_ZONE


def get_confirm_direction(d_s, d_e, limit):
    with connection.cursor() as cursor:
        cursor.execute(
            """WITH     
        t_all_direction AS (
            SELECT DISTINCT ON (napravleniye_id) napravleniye_id FROM public.directions_issledovaniya
            WHERE time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s),
        
         t_not_confirm_direction AS (
            SELECT DISTINCT ON (napravleniye_id) napravleniye_id FROM public.directions_issledovaniya
            WHERE napravleniye_id IN (SELECT napravleniye_id FROM t_all_direction) AND time_confirmation IS NULL),
        
        t_only_confirm_direction AS (
            SELECT napravleniye_id FROM t_all_direction
            WHERE napravleniye_id NOT IN (SELECT napravleniye_id FROM t_not_confirm_direction)),
        
        t_istochnik_f_rmis_auto_send AS (
            SELECT id FROM directions_istochnikifinansirovaniya
            WHERE rmis_auto_send = true) 
                
        SELECT id FROM directions_napravleniya
            WHERE id IN (SELECT napravleniye_id FROM t_only_confirm_direction)
            AND 
                rmis_number != ANY(ARRAY['NONERMIS', '', NULL]) 
            AND 
                result_rmis_send = false
            AND 
                NOT (imported_from_rmis = True and imported_directions_rmis_send = False)
            AND
                NOT (istochnik_f_id IN (SELECT id FROM t_istochnik_f_rmis_auto_send) and force_rmis_send = False)
            ORDER BY data_sozdaniya 
            LIMIT %(limit)s     
        """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'limit': limit},
        )
        row = cursor.fetchall()
    return row
