from django.db import connection

from laboratory.settings import TIME_ZONE


def get_confirm_direction(d_s, d_e, limit):
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT DISTINCT ON (directions_napravleniya.id) directions_napravleniya.id
        FROM directions_napravleniya
        INNER JOIN directions_issledovaniya ON (directions_napravleniya.id = directions_issledovaniya.napravleniye_id)
        INNER JOIN directions_istochnikifinansirovaniya ON (directions_napravleniya.istochnik_f_id = directions_istochnikifinansirovaniya.id)
        WHERE directions_issledovaniya.time_confirmation IS NOT NULL
          AND directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s <= %(d_end)s
          AND directions_istochnikifinansirovaniya.rmis_auto_send = TRUE
          AND NOT EXISTS (SELECT napravleniye_id
             FROM directions_issledovaniya
             WHERE time_confirmation IS NULL AND napravleniye_id = directions_napravleniya.id)
          AND directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s >= %(d_start)s
          AND directions_napravleniya.rmis_number <> 'NONERMIS'
          AND directions_napravleniya.rmis_number <> ''
          AND directions_napravleniya.rmis_number IS NOT NULL
          AND directions_napravleniya.result_rmis_send = FALSE
          AND (directions_napravleniya.imported_from_rmis = FALSE OR directions_napravleniya.imported_directions_rmis_send = TRUE)
          AND directions_napravleniya.force_rmis_send = FALSE
        ORDER BY directions_napravleniya.id, data_sozdaniya
        LIMIT %(limit)s
        """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'limit': limit},
        )
        row = cursor.fetchall()
    return row
