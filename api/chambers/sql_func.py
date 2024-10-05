from django.db import connection
from utils.db import namedtuplefetchall


def load_patients_stationar_unallocated_sql(department_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                family, 
                name, 
                patronymic, 
                sex, 
                napravleniye_id,
                birthday,
                date_part('year', age(birthday))::int AS age
                FROM directions_issledovaniya 
                INNER JOIN directions_napravleniya ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                INNER JOIN clients_card ON directions_napravleniya.client_id=clients_card.id
                INNER JOIN public.clients_individual ON clients_card.individual_id = public.clients_individual.id
                WHERE hospital_department_override_id = %(department_id)s
                AND data_sozdaniya > now() - INTERVAL '2 months'
                AND NOT EXISTS (SELECT direction_id FROM podrazdeleniya_patienttobed WHERE date_out IS NULL AND napravleniye_id = direction_id)
                AND NOT EXISTS (SELECT direction_id FROM podrazdeleniya_patientstationarwithoutbeds WHERE napravleniye_id = direction_id)
                
                ORDER BY family
                """,
            params={"department_id": department_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def load_patient_without_bed_by_department(department_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            family,
            name,
            patronymic,
            date_part('year', age(birthday))::int AS age,
            sex,
            direction_id
            FROM podrazdeleniya_patientstationarwithoutbeds
            LEFT JOIN directions_napravleniya ON podrazdeleniya_patientstationarwithoutbeds.direction_id = directions_napravleniya.id
            LEFT JOIN clients_card ON directions_napravleniya.client_id = clients_card.id
            LEFT JOIN clients_individual ON clients_card.individual_id = clients_individual.id
            
            WHERE
            podrazdeleniya_patientstationarwithoutbeds.department_id = %(department_id)s
            
            ORDER BY family
            """,
            params={"department_id": department_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def load_attending_doctor_by_department(department_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            id,
            family,
            name,
            patronymic
            
            FROM users_doctorprofile
            WHERE
            users_doctorprofile.podrazdeleniye_id = %(department_id)s
            AND users_doctorprofile.dismissed = false
            
            ORDER BY family
            """,
            params={"department_id": department_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def load_chambers_and_beds_by_department(department_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
             SELECT 
             podrazdeleniya_chamber.id as chamber_id,
             podrazdeleniya_chamber.title as chamber_title,
             
             podrazdeleniya_bed.id as bed_id,
             podrazdeleniya_bed.bed_number,
             
             clients_individual.family as patient_family,
             clients_individual.name as patient_name,
             clients_individual.patronymic as patient_patronymic,
             date_part('year', age(clients_individual.birthday))::int AS patient_age,
             clients_individual.sex as patient_sex,
             
             patient_table.direction_id,
             
             users_doctorprofile.id as doctor_id,
             users_doctorprofile.family as doctor_family,
             users_doctorprofile.name as doctor_name,
             users_doctorprofile.patronymic as doctor_patronymic

             FROM podrazdeleniya_chamber
             LEFT JOIN podrazdeleniya_bed ON podrazdeleniya_chamber.id = podrazdeleniya_bed.chamber_id
             LEFT JOIN 
             (SELECT * FROM podrazdeleniya_patienttobed WHERE date_out is NULL) as patient_table ON bed_id = podrazdeleniya_bed.id
             LEFT JOIN directions_napravleniya ON patient_table.direction_id = directions_napravleniya.id
             LEFT JOIN clients_card ON directions_napravleniya.client_id = clients_card.id
             LEFT JOIN clients_individual ON clients_card.individual_id = clients_individual.id
             LEFT JOIN users_doctorprofile ON patient_table.doctor_id = users_doctorprofile.id
             
             WHERE
             podrazdeleniya_chamber.podrazdelenie_id = %(department_id)s

                """,
            params={"department_id": department_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows
