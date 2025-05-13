from django.db import connection
from laboratory.settings import TIME_ZONE, RESEARCH_ID_CLOSE_CASE
from utils.db import namedtuplefetchall


def closed_company_cases_by_date(d_start, d_end, company_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
            dn.id as direction_num,
            directions_issledovaniya.id as issledovaniye_id,
            ci.family as patient_family,
            ci.name as patient_name,
            ci.patronymic as patient_patronymic,
            ci.sex,
            to_char(ci.birthday AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as patient_birthday,
            cph.harmful_factor_id as factor_id
            
            FROM directions_issledovaniya 
            LEFT JOIN directions_napravleniya dn on directions_issledovaniya.napravleniye_id = dn.id
            LEFT JOIN clients_card cc on cc.id=dn.client_id
            LEFT JOIN clients_individual ci on cc.individual_id = ci.id
            RIGHT JOIN clients_patientharmfullfactor cph on cc.id = cph.card_id
            WHERE
            dn.work_place_db_id = %(company_id)s
            AND directions_issledovaniya.medical_examination AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
            AND directions_issledovaniya.research_id in %(research_id_case)s
            ORDER BY directions_issledovaniya.medical_examination
            """,
            params={'d_start': d_start, 'd_end': d_end, 'tz': TIME_ZONE, 'company_id': company_id, 'research_id_case': RESEARCH_ID_CLOSE_CASE},
        )

        rows = namedtuplefetchall(cursor)
    return rows
