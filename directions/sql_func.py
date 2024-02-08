from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def check_limit_assign_researches(
    district_group_id,
):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT users_districtresearchlimitassign.id, 
                users_districtresearchlimitassign.limit_count, 
                users_districtresearchlimitassign.type_period_limit,
                users_districtresearchlimitassign.research_id,
                users_districtresearchlimitassign.district_group_id
                from users_districtresearchlimitassign
                where
                district_group_id = %(district_group_id)s
            """,
            params={'district_group_id': district_group_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_count_researches_by_doc(doctor_pks, d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                directions_issledovaniya.research_id,
                count(directions_napravleniya.id) as count
                FROM directions_napravleniya
                LEFT JOIN directions_issledovaniya
                ON directions_napravleniya.id=directions_issledovaniya.napravleniye_id
                WHERE doc_who_create_id in %(doctor_pks)s and data_sozdaniya AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                group by directions_issledovaniya.research_id
            """,
            params={'doctor_pks': doctor_pks, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def check_confirm_patient_research(client_id, researches, months_ago):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
              DISTINCT ON (directions_issledovaniya.research_id) directions_issledovaniya.research_id as research_id
            FROM directions_issledovaniya
            LEFT JOIN directions_napravleniya 
            ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id 
            WHERE directions_napravleniya.client_id = %(client_id)s
            AND directions_issledovaniya.research_id in %(researches)s 
            AND directions_issledovaniya.time_confirmation BETWEEN (NOW() - interval '%(months_ago)s month')  AND (NOW())
            ORDER BY directions_issledovaniya.research_id, directions_issledovaniya.time_confirmation DESC
            """,
            params={'client_id': client_id, 'researches': researches, 'months_ago': months_ago, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def check_create_direction_patient_by_research(client_id, researches, months_ago):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
              DISTINCT ON (directions_issledovaniya.research_id) directions_issledovaniya.research_id as research_id,
              directions_issledovaniya.napravleniye_id as direction_id
            FROM directions_issledovaniya
            LEFT JOIN directions_napravleniya 
            ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id 
            WHERE directions_napravleniya.client_id = %(client_id)s
            AND directions_issledovaniya.research_id in %(researches)s 
            AND directions_napravleniya.data_sozdaniya BETWEEN (NOW() - interval '%(months_ago)s month')  AND (NOW())
            ORDER BY directions_issledovaniya.research_id, directions_napravleniya.data_sozdaniya DESC
            """,
            params={'client_id': client_id, 'researches': researches, 'months_ago': months_ago, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_researches_by_number_directions(direction_numbers):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
              directions_issledovaniya.research_id
            FROM directions_issledovaniya
            WHERE directions_issledovaniya.napravleniye_id in %(direction_numbers)s 
            """,
            params={'direction_numbers': direction_numbers},
        )
        rows = namedtuplefetchall(cursor)
    return rows