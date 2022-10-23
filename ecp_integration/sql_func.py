from utils.db import namedtuplefetchall
from django.db import connection


def get_doctors_rmis_location_by_research(research_pk, hosptal_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT users_doctorprofile.id,
            family, 
            name,
            patronymic,
            rmis_location,
            cd.title
            FROM users_doctorprofile
            LEFT JOIN clients_district cd ON users_doctorprofile.district_group_id = cd.id
            WHERE users_doctorprofile.id IN
            (SELECT doctorprofile_id FROM users_doctorprofile_users_services WHERE researches_id = %(research_pk)s)
            AND users_doctorprofile.rmis_location IS NOT NULL
            AND users_doctorprofile.hospital_id = %(hosptal_id)s
            """,
            params={'research_pk': research_pk, 'hosptal_id': hosptal_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows
