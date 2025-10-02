from django.db import connection
from laboratory.settings import RESEARCH_ID_CLOSE_CASE, CDA_ID_FOR_WHERE_SERVICE_DONE, CDA_ID_FOR_TYPE_MEDICAL_INSPECTION
from utils.db import namedtuplefetchall
from laboratory.settings import TIME_ZONE


def closed_company_cases_by_date(d_start, d_end, company_id, current_year_last_date):
    print('RESEARCH_ID_CLOSE_CASE', RESEARCH_ID_CLOSE_CASE)
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
            to_char(ci.birthday AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as patient_birthday,
            date_part('year', age(timestamp %(current_year_last_date)s, ci.birthday)) as age_year,
            cph.harmful_factor_id as factor_id,
            to_char(directions_issledovaniya.medical_examination AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_end,
            date_part('year', age(directions_issledovaniya.medical_examination AT TIME ZONE %(tz)s, ci.birthday)) as fact_year
            FROM directions_issledovaniya
            LEFT JOIN directions_napravleniya dn on directions_issledovaniya.napravleniye_id = dn.id
            LEFT JOIN clients_card cc on cc.id=dn.client_id
            LEFT JOIN clients_individual ci on cc.individual_id = ci.id
            RIGHT JOIN clients_patientharmfullfactor cph on cc.id = cph.card_id
            WHERE
            dn.work_place_db_id = %(company_id)s
            AND directions_issledovaniya.medical_examination AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
            AND directions_issledovaniya.time_confirmation is not Null
            AND directions_issledovaniya.research_id = %(research_id_case)s
            ORDER BY directions_issledovaniya.medical_examination
            """,
            params={'d_start': d_start, 'd_end': d_end, 'tz': TIME_ZONE, 'company_id': company_id, 'research_id_case': RESEARCH_ID_CLOSE_CASE,
                    'current_year_last_date': current_year_last_date},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def directions_by_parent_cases_issledovaniye(cases_issledovaniye_ids):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
            directions_issledovaniya.id as iss_id,
            directions_issledovaniya.research_id,
            to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm,
            dn.parent_case_id as parent_case_iss_id
            FROM directions_issledovaniya
            LEFT JOIN directions_napravleniya dn on directions_issledovaniya.napravleniye_id = dn.id
            WHERE 
            directions_issledovaniya.napravleniye_id in (SELECT id from directions_napravleniya where directions_napravleniya.parent_case_id in %(cases_issledovaniye_ids)s)
            AND directions_issledovaniya.time_confirmation IS NOT NULL
            ORDER BY dn.parent_case_id
            """,
            params={'cases_issledovaniye_ids': cases_issledovaniye_ids, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def search_value_where_done_custom_research(research_issledovaniye_ids, research_ids):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
            directions_paraclinicresult.issledovaniye_id,
            di.research_id as research_id,
            directions_paraclinicresult.value as result_value
            FROM directions_paraclinicresult
            LEFT JOIN directory_paraclinicinputfield dp on directions_paraclinicresult.field_id = dp.id
            LEFT JOIN directions_issledovaniya di on directions_paraclinicresult.issledovaniye_id = di.id
            WHERE
            directions_paraclinicresult.issledovaniye_id in %(research_issledovaniye_ids)s
            AND
            dp.cda_option_id = %(CDA_ID_FOR_WHERE_SERVICE_DONE)s
            AND di.research_id in %(research_ids)s
            
            """,
            params={'research_issledovaniye_ids': research_issledovaniye_ids, 'CDA_ID_FOR_WHERE_SERVICE_DONE': CDA_ID_FOR_WHERE_SERVICE_DONE, 'research_ids': research_ids},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def search_value_type_medical_inspection(research_issledovaniye_ids):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
            directions_paraclinicresult.issledovaniye_id,
            di.research_id as research_id,
            directions_paraclinicresult.value as result_value
            FROM directions_paraclinicresult
            LEFT JOIN directory_paraclinicinputfield dp on directions_paraclinicresult.field_id = dp.id
            LEFT JOIN directions_issledovaniya di on directions_paraclinicresult.issledovaniye_id = di.id
            WHERE
            directions_paraclinicresult.issledovaniye_id in %(research_issledovaniye_ids)s
            AND
            dp.cda_option_id = %(CDA_ID_FOR_TYPE_MEDICAL_INSPECTION)s
            """,
            params={'research_issledovaniye_ids': research_issledovaniye_ids, 'CDA_ID_FOR_TYPE_MEDICAL_INSPECTION': CDA_ID_FOR_TYPE_MEDICAL_INSPECTION},
        )

        rows = namedtuplefetchall(cursor)
    return rows
