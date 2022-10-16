from utils.db import namedtuplefetchall
from django.db import connection


def get_doctors_rmis_location_by_research(research_pk):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id,
            family, 
            name,
            patronymic,
            rmis_location
            FROM users_doctorprofile 
            WHERE users_doctorprofile.id IN
            (SELECT doctorprofile_id FROM users_doctorprofile_users_services WHERE researches_id = %(research_pk)s)
            and users_doctorprofile.rmis_location IS NOT NULL
            """,
            params={'research_pk': research_pk},
        )
        rows = namedtuplefetchall(cursor)
    return rows
