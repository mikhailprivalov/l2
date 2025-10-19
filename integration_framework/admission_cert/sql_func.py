from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall
from laboratory.settings import RESEARCH_ID_CLOSE_CASE, CDA_ID_FOR_TYPE_MEDICAL_INSPECTION


def get_closed_case_by_company(companies_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
            dn.id as direction_num,
            directions_issledovaniya.id as case_issledovaniye_id,
            ci.family as patient_family,
            ci.name as patient_name,
            ci.patronymic as patient_patronymic,
            ci.sex,
            
            to_char(ci.birthday AT TIME ZONE %(tz)s, 'YYYY-MM-DD') as patient_birthday,
            cph.harmful_factor_id as factor_id,
            to_char(directions_issledovaniya.medical_examination AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_end,
            cc.title as company_title,
            cc.inn as company_inn
            
            FROM directions_issledovaniya
            LEFT JOIN directions_napravleniya dn on directions_issledovaniya.napravleniye_id = dn.id
            LEFT JOIN clients_card cc on cc.id=dn.client_id
            LEFT JOIN clients_individual ci on cc.individual_id = ci.id
            LEFT JOIN contracts_company cc on cc.id = dn.work_place_db_id
            RIGHT JOIN clients_patientharmfullfactor cph on cc.id = cph.card_id
            WHERE
            dn.work_place_db_id in %(companies_id)s
            AND directions_issledovaniya.medical_examination is not Null
            AND directions_issledovaniya.time_confirmation is not Null
            AND directions_issledovaniya.research_id = %(research_id_case)s
            AND dn.is_sent_to_work_place = false
            ORDER BY directions_issledovaniya.medical_examination
            """,
            params={'tz': TIME_ZONE, 'companies_id': companies_id, 'research_id_case': RESEARCH_ID_CLOSE_CASE},
        )

        rows = namedtuplefetchall(cursor)
    return rows