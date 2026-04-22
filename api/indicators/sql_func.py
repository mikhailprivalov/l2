from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def indicator_sql(fields_ids, date_start, date_end):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                    directions_issledovaniya.napravleniye_id as direction_id,
                    directions_issledovaniya.id as issledovaniye_id,
                    to_char(directions_issledovaniya.time_save AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as d_confirm,
                    hospitals_hospitals.title as hospital_title,
                    dp.field_id,
                    dp.value as result_value,
                    dpf.title as field_title,
                    dpgr.title as group_title
                    
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                LEFT JOIN hospitals_hospitals
                ON hospitals_hospitals.id=directions_napravleniya.hospital_id
                LEFT JOIN directions_paraclinicresult dp on directions_issledovaniya.id = dp.issledovaniye_id
                LEFT JOIN directory_paraclinicinputfield dpf on dpf.id = dp.field_id
                LEFT JOIN directory_paraclinicinputgroups dpgr on dpgr.id = dpf.group_id 
                WHERE dp.field_id in %(fields_ids)s and directions_issledovaniya.time_confirmation is not Null
                ORDER BY directions_issledovaniya.napravleniye_id, dpgr.title, dpf.title
            """,
            params={
                'tz': TIME_ZONE,
                'fields_ids': fields_ids,
                'd_start': date_start,
                'd_end': date_end,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows
