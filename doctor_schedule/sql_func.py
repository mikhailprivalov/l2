from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall
from django.db import connection


def get_resource_by_research_hospital():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT scheduleresource_id, researches_id, dr.title, dr.short_title
            FROM public.doctor_schedule_scheduleresource_service
            LEFT JOIN directory_researches dr on dr.id = doctor_schedule_scheduleresource_service.researches_id
            where researches_id in 
                (SELECT id from directory_researches WHERE is_hospital=True and hide=False)
            """
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_slot_plan_by_hosp_research(date_start, date_end, resource_tuple):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
            datetime, 
            to_char(datetime AT TIME ZONE %(tz)s, 'YYYY-MM-DD') AS date_char,
            to_char(datetime AT TIME ZONE %(tz)s, 'HH-MI') AS hhmm_char,
            resource_id
            FROM public.doctor_schedule_slotplan
            WHERE datetime AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s and resource_id in %(resource_tuple)s
            ORDER BY datetime
        """,
            params={'d_start': date_start, 'd_end': date_end, 'tz': TIME_ZONE, 'resource_tuple': resource_tuple},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_date_slots(date_start, date_end, resource_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            to_char(datetime AT TIME ZONE %(tz)s, 'HH:MI') AS start_slot,
            to_char(datetime_end AT TIME ZONE %(tz)s, 'HH:MI') AS end_slot
            FROM public.doctor_schedule_slotplan
            WHERE datetime AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s and resource_id = %(resource_id)s 
            ORDER BY datetime
        """,
            params={'d_start': date_start, 'd_end': date_end, 'tz': TIME_ZONE, 'resource_id': resource_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows
