from django.db import connection

from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def get_date_slots(date_start, date_end):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            to_char(datetime AT TIME ZONE %(tz)s, 'HH:MI') AS start_slot,
            to_char(datetime_end AT TIME ZONE %(tz)s, 'HH:MI') AS end_slot
            FROM public.doctor_schedule_slotplan
            WHERE datetime AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
            ORDER BY datetime
        """,
            params={'d_start': date_start, 'd_end': date_end, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows
