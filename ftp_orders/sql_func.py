from utils.db import namedtuplefetchall
from django.db import connection


def get_tubesregistration_id_by_iss(iss_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT dt.number as tube_number
            FROM directions_issledovaniya_tubes
            LEFT JOIN directions_tubesregistration dt on directions_issledovaniya_tubes.tubesregistration_id = dt.id
            where issledovaniya_id = %(iss_id)s
            LIMIT 1
            """,
            params={'iss_id': iss_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows
