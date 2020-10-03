from django.db import connection


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
            """
        SELECT id as dir_id, client_id  FROM public.directions_napravleniya
        WHERE id = ANY(ARRAY[%(num_dirs)s])
	    order by client_id
        """,
            params={'num_dirs': list_dirs},
        )
        row = cursor.fetchall()
    return row
