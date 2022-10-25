from utils.db import namedtuplefetchall
from django.db import connection


def get_doctors_infomat_has_rmis_location(hosptal_id, speciality_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT users_doctorprofile.id,
            family, 
            name,
            patronymic,
            rmis_location,
            cd.title as distric_title
            FROM users_doctorprofile
            LEFT JOIN clients_district cd ON users_doctorprofile.district_group_id = cd.id
            LEFT JOIN users_speciality spec ON users_doctorprofile.specialities_id = spec.id
            WHERE
            users_doctorprofile.show_infomat = true
            AND users_doctorprofile.rmis_location IS NOT NULL
            AND users_doctorprofile.hospital_id = %(hosptal_id)s
            AND users_doctorprofile.specialities_id = %(speciality_id)s
            """,
            params={'hosptal_id': hosptal_id, 'speciality_id': speciality_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows
