from utils.db import namedtuplefetchall
from django.db import connection


def get_district_limit_research(district_pk):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                 limit_count, 
                 type_period_limit,
                 users_districtresearchlimitassign_research.researches_id
                from users_districtresearchlimitassign
                LEFT JOIN users_districtresearchlimitassign_research
                ON users_districtresearchlimitassign.id = users_districtresearchlimitassign_research.districtresearchlimitassign_id
                WHERE district_group_id = %(district_pk)s
        """,
            params={'district_pk': district_pk},
        )

        rows = namedtuplefetchall(cursor)
    return rows
