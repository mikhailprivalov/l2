from django.db import connection
from utils.db import namedtuplefetchall


def get_patients_stationar(department_id):
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
                AND data_sozdaniya > now() - INTERVAL '2 months'
                AND NOT EXISTS (SELECT direction_id FROM podrazdeleniya_patienttobed WHERE date_out IS NULL AND napravleniye_id = direction_id)
                AND NOT EXISTS (SELECT direction_id FROM podrazdeleniya_patientstationarwithoutbeds WHERE napravleniye_id = direction_id)
                """,
            params={"department_id": department_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows
