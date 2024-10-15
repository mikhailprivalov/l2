from django.db import connection

from laboratory.settings import TIME_ZONE
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
                directory_researches.title as service_title,
                directions_issledovaniya.id as issledovanie_id,
                birthday,
                date_part('year', age(birthday))::int AS age
                FROM directions_issledovaniya
                INNER JOIN directory_researches ON directions_issledovaniya.research_id = directory_researches.id
                INNER JOIN directions_napravleniya ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                INNER JOIN clients_card ON directions_napravleniya.client_id=clients_card.id
                INNER JOIN public.clients_individual ON clients_card.individual_id = public.clients_individual.id
                WHERE directions_napravleniya.cancel = false
                AND hospital_department_override_id = %(department_id)s
                AND data_sozdaniya > now() - INTERVAL '2 months'
                AND NOT EXISTS (SELECT direction_id FROM podrazdeleniya_patienttobed WHERE date_out IS NULL AND napravleniye_id = direction_id)
                AND NOT EXISTS (SELECT direction_id FROM podrazdeleniya_patientstationarwithoutbeds WHERE napravleniye_id = direction_id)
                
                ORDER BY family
                """,
            params={"department_id": department_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_closing_protocols(issledovaniye_ids, titles):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                directions_napravleniya.parent_id
                
                FROM directions_napravleniya
                LEFT JOIN directions_issledovaniya ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN directory_researches ON directions_issledovaniya.research_id = directory_researches.id
                LEFT JOIN directory_hospitalservice ON directory_researches.id = directory_hospitalservice.slave_research_id
                WHERE directions_napravleniya.parent_id IN %(issledovaniye_ids)s
                AND 
                (directory_hospitalservice.site_type = 7 OR (directory_hospitalservice.site_type = 6 AND title IN %(titles)s))

                AND total_confirmed = true
                
                """,
            params={"issledovaniye_ids": issledovaniye_ids, "titles": titles},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def load_patient_without_bed_by_department(department_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            clients_individual.family as patient_family,
            clients_individual.name as patient_name,
            clients_individual.patronymic as patient_patronymic,
            date_part('year', age(clients_individual.birthday))::int AS patient_age,
            clients_individual.sex as patient_sex,
            direction_id,
            
            users_doctorprofile.id as doctor_id
            
            FROM podrazdeleniya_patientstationarwithoutbeds
            LEFT JOIN directions_napravleniya ON podrazdeleniya_patientstationarwithoutbeds.direction_id = directions_napravleniya.id
            LEFT JOIN clients_card ON directions_napravleniya.client_id = clients_card.id
            LEFT JOIN clients_individual ON clients_card.individual_id = clients_individual.id
            LEFT JOIN users_doctorprofile ON podrazdeleniya_patientstationarwithoutbeds.doctor_id = users_doctorprofile.id
            
            WHERE
            podrazdeleniya_patientstationarwithoutbeds.department_id = %(department_id)s
            
            ORDER BY clients_individual.family
            """,
            params={"department_id": department_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def load_attending_doctor_by_department(department_id, group_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            users_doctorprofile.id,
            users_doctorprofile.family,
            users_doctorprofile.name,
            users_doctorprofile.patronymic
            
            FROM users_doctorprofile
            LEFT JOIN auth_user ON users_doctorprofile.user_id = auth_user.id
            LEFT JOIN auth_user_groups ON auth_user.id = auth_user_groups.user_id
            LEFT JOIN auth_group ON auth_user_groups.group_id = auth_group.id
            WHERE 
            auth_group.id = %(group_id)s
            AND users_doctorprofile.podrazdeleniye_id = %(department_id)s
            AND users_doctorprofile.dismissed = false
            
            ORDER BY family
            """,
            params={"department_id": department_id, "group_id": group_id},
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
             
             ORDER BY podrazdeleniya_chamber.id, bed_number

                """,
            params={"department_id": department_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def load_plan_operations_next_day(start_time, end_time):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            direction
            FROM plans_planoperations
            WHERE date AT TIME ZONE %(tz)s BETWEEN %(start_time)s AND %(end_time)s
            """,
            params={"tz": TIME_ZONE, "start_time": start_time, "end_time": end_time},
        )

        rows = namedtuplefetchall(cursor)
    return rows

