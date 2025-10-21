from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall
from laboratory.settings import RESEARCH_ID_CLOSE_CASE, RESEARCH_ID_FINAL_REPORT


def get_closed_case_by_company(companies_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
            dn.id as direction_num,
            directions_issledovaniya.id as case_issledovaniye_id,
            to_char(directions_issledovaniya.medical_examination AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_end,
            cnc.title as company_title,
            cnc.inn as company_inn
            FROM directions_issledovaniya
            LEFT JOIN directions_napravleniya dn on directions_issledovaniya.napravleniye_id = dn.id
            LEFT JOIN contracts_company cnc on cnc.id = dn.work_place_db_id
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


def directions_by_parent_cases_issledovaniye_only_research_id_final_report(cases_issledovaniye_ids):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
            directions_issledovaniya.id as iss_id,
            directions_issledovaniya.research_id,
            directions_issledovaniya.napravleniye_id,
            to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm,
            dn.parent_case_id as parent_case_iss_id,
            ci.family as patient_family,
            ci.name as patient_name,
            ci.patronymic as patient_patronymic,
            ci.sex,
            to_char(ci.birthday AT TIME ZONE %(tz)s, 'YYYY-MM-DD') as patient_birthday,
            dn.work_place_db_id
            FROM directions_issledovaniya
            LEFT JOIN directions_napravleniya dn on directions_issledovaniya.napravleniye_id = dn.id
            LEFT JOIN clients_card cc on cc.id=dn.client_id
            LEFT JOIN clients_individual ci on cc.individual_id = ci.id
            WHERE 
            directions_issledovaniya.napravleniye_id in (SELECT id from directions_napravleniya where directions_napravleniya.parent_case_id in %(cases_issledovaniye_ids)s)
            AND directions_issledovaniya.time_confirmation IS NOT NULL
            AND directions_issledovaniya.research_id in %(research_id_final_report)s
            ORDER BY dn.parent_case_id
            """,
            params={'cases_issledovaniye_ids': cases_issledovaniye_ids, 'tz': TIME_ZONE, 'research_id_final_report': RESEARCH_ID_FINAL_REPORT},
        )

        rows = namedtuplefetchall(cursor)
    return rows