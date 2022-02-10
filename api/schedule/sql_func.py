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


def limit_plan_hosp_get(date_start, date_end, research_pk):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT date, max_count, to_char(date AT TIME ZONE %(tz)s, 'YYYY-MM-DD') AS date_char
            FROM public.plans_limitdateplanhospitalization
            WHERE date AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s and research_id=%(research_pk)s
            ORDER BY date
        """,
            params={'d_start': date_start, 'd_end': date_end, 'tz': TIME_ZONE, 'research_pk': research_pk},
        )
        rows = namedtuplefetchall(cursor)
    return rows
