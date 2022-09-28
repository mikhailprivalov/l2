from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def report_buh_gistology(directions):
    with connection.cursor() as cursor:
        cursor.execute(
            """ 
        SELECT
        dn.id as direction_id,
        dn.hospital_id,
        dn.istochnik_f_id,
        to_char(dn.visit_date AT TIME ZONE %(tz)s, 'DD.MM.YYYY HH24:MI') AS char_visit_date,
        dn.visit_date,
        di.title as iss_finsource_title,
        cp.title as iss_price_category,
        
        hh.title as hosp_title,
        hh.id as hosp_id,
        
        dp.value, 
        dp.field_id as field_id,
        dpif.title as field_title    
        
        FROM directions_issledovaniya
        LEFT JOIN directions_napravleniya dn on directions_issledovaniya.napravleniye_id = dn.id
        LEFT JOIN hospitals_hospitals hh on dn.hospital_id = hh.id
        LEFT JOIN directions_istochnikifinansirovaniya di on directions_issledovaniya.fin_source_id = di.id
        LEFT JOIN contracts_pricecategory cp on directions_issledovaniya.price_category_id = cp.id 
        LEFT JOIN directions_paraclinicresult dp on directions_issledovaniya.id = dp.issledovaniye_id
        LEFT JOIN directory_paraclinicinputfield dpif on dp.field_id = dpif.id
        
        WHERE directions_issledovaniya.napravleniye_id in %(directions)s
        ORDER BY hh.title, dn.visit_date, dn.id

        """,
            params={'directions': directions, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows
