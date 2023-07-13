from utils.db import namedtuplefetchall
from django.db import connection


def get_tubesregistration_id_by_iss(iss_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT tubesregistration_id
            FROM directions_issledovaniya_tubes
            where issledovaniya_id = %(iss_id)s
            LIMIT 1
            """,
            params={'iss_id': iss_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows