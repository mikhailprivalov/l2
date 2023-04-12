from django.db import connection
from utils.db import namedtuplefetchall


def getting_patient_issledovaniya(hosp_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                family, 
                name, 
                patronymic, 
                sex, 
                napravleniye_id,
                birthday 
                FROM directions_issledovaniya 
                INNER JOIN directions_napravleniya ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                INNER JOIN clients_card ON directions_napravleniya.client_id=clients_card.id
                INNER JOIN public.clients_individual ON clients_card.individual_id = public.clients_individual.id
                WHERE hospital_department_override_id = %(department_id)s
            """,
            params={"department_id": hosp_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows
