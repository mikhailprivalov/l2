from django.db import connection
from laboratory.settings import TIME_ZONE, CDA_ID_FOR_DATE_CLOSE_CASE
from utils.db import namedtuplefetchall


def closed_company_cases_by_date(d_start, d_end, company_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
            dn.id as direction_num,
            di.id as issledovaniye_id,
            dpif.cda_option_id
            FROM directions_paraclinicresult dp
            LEFT JOIN directory_paraclinicinputfield dpif on dp.field_id = dpif.id
            LEFT JOIN  dpif on dp.field_id = dpif.id
            
            LEFT JOIN directions_issledovaniya di on di.id = dp.issledovaniye_id 
            LEFT JOIN directions_napravleniya dn on di.napravleniye_id = dn.id
            
            WHERE
            dn.work_place_db = %(company_id)s
            AND dpif.cda_option_id = %(cda_date_close_case)s
            ORDER BY dn.id
            """,
            params={'d_start': d_start, 'd_end': d_end, 'tz': TIME_ZONE, 'company_id': company_id, 'cda_date_close_case': CDA_ID_FOR_DATE_CLOSE_CASE},
        )

        rows = namedtuplefetchall(cursor)
    return rows
