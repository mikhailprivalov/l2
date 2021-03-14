from django.db import connection

from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def get_confirm_direction(list_dirs):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT DISTINCT ON (napravleniye_id) napravleniye_id FROM public.directions_issledovaniya
        WHERE napravleniye_id = ANY(ARRAY[%(num_dirs)s])
        AND time_confirmation IS NOT NULL
        """,
            params={'num_dirs': list_dirs},
        )
        row = cursor.fetchall()
    return row


def get_not_confirm_direction(list_dirs):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT DISTINCT ON (napravleniye_id) napravleniye_id FROM public.directions_issledovaniya
        WHERE napravleniye_id = ANY(ARRAY[%(num_dirs)s])
        AND time_confirmation IS NULL
        """,
            params={'num_dirs': list_dirs},
        )
        row = cursor.fetchall()
    return row


def get_direction_by_client(list_dirs):
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT id as dir_id, client_id  FROM public.directions_napravleniya WHERE id = ANY(ARRAY[%(num_dirs)s]) order by client_id""",
            params={'num_dirs': list_dirs},
        )
        row = cursor.fetchall()
    return row


def get_laboratory_results_by_directions(list_dirs):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT 
                directions_issledovaniya.id,
                directions_issledovaniya.napravleniye_id as direction,
                directions_issledovaniya.research_id,
                directory_researches.title as research_title,
                directions_result.value as value,
                directions_result.fraction_id,
                directions_result.id as result_is,
                directory_fractions.title as fraction_title,
                directions_result.units as units,
                users_doctorprofile.fio as fio,
                to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm
                from directions_issledovaniya
                INNER JOIN directions_result ON (directions_result.issledovaniye_id = directions_issledovaniya.id)
                LEFT JOIN directory_researches ON
                directions_issledovaniya.research_id=directory_researches.id
                LEFT JOIN directory_fractions ON
                directions_result.fraction_id=directory_fractions.id
                LEFT JOIN users_doctorprofile ON
                users_doctorprofile.id=directions_issledovaniya.doc_confirmation_id
                WHERE directions_issledovaniya.napravleniye_id = ANY(ARRAY[%(num_dirs)s])
                ORDER BY directions_issledovaniya.napravleniye_id

        """,
            params={'num_dirs': list_dirs, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows
