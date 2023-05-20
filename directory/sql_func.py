from django.db import connection
from utils.db import namedtuplefetchall


def is_paraclinic_filter_research(reserches_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                  directory_researches.id as research_id
                FROM directory_researches
                WHERE directory_researches.id in %(reserches_id)s AND
                directory_researches.is_paraclinic = true
                order by directory_researches.id
        """,
            params={'reserches_id': reserches_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows



def is_lab_filter_research(reserches_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                directory_researches.id as research_id
                FROM directory_researches
                LEFT JOIN podrazdeleniya_podrazdeleniya pp on directory_researches.podrazdeleniye_id = pp.id
                WHERE directory_researches.id in %(reserches_id)s AND
                pp.p_type = 2
                order by directory_researches.id
        """,
            params={'reserches_id': reserches_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows
