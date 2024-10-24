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
        dpif.title as field_title,
        udpf.family as doctor_family,
        udpf.name as doctor_name,
        udpf.patronymic as doctor_patronymic,
        to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_confirm
        FROM directions_issledovaniya
        LEFT JOIN directions_napravleniya dn on directions_issledovaniya.napravleniye_id = dn.id
        LEFT JOIN hospitals_hospitals hh on dn.hospital_id = hh.id
        LEFT JOIN directions_istochnikifinansirovaniya di on directions_issledovaniya.fin_source_id = di.id
        LEFT JOIN contracts_pricecategory cp on directions_issledovaniya.price_category_id = cp.id 
        LEFT JOIN directions_paraclinicresult dp on directions_issledovaniya.id = dp.issledovaniye_id
        LEFT JOIN directory_paraclinicinputfield dpif on dp.field_id = dpif.id
        LEFT JOIN users_doctorprofile udpf on directions_issledovaniya.doc_confirmation_id = udpf.id
        
        WHERE directions_issledovaniya.napravleniye_id in %(directions)s
        ORDER BY hh.title, dn.visit_date, dn.id

        """,
            params={'directions': directions, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_pair_direction_iss(directions):
    with connection.cursor() as cursor:
        cursor.execute(
            """ 
        SELECT
        directions_issledovaniya.napravleniye_id as direction_id,
        directions_issledovaniya.id as iss_id

        FROM directions_issledovaniya
        WHERE directions_issledovaniya.napravleniye_id in %(directions)s
        ORDER BY directions_issledovaniya.napravleniye_id
        """,
            params={'directions': directions},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_simple_directions_for_hosp_stationar(iss_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """ 
        SELECT
        directions_napravleniya.id as direction_id
        FROM directions_napravleniya
        WHERE directions_napravleniya.parent_id in %(iss_id)s
        """,
            params={'iss_id': iss_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_field_results(directions, input_field, fraction_field):
    with connection.cursor() as cursor:
        cursor.execute(
            """ 
        SELECT
        dn.id as direction_id,
        to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY HH24:MI') AS time_confirm,
        dp.value as input_value, 
        dpif.title as field_title,
        dpif.statistic_pattern_param_id as input_static_param,
        dr.value as fraction_value,
        df.statistic_pattern_param_id as fraction_static_param,
        dn.parent_id as parrent_iss,
        pd.napravleniye_id as hosp_direction,
        ci.family,
        ci.name,
        ci.patronymic,
        to_char(ci.birthday, 'DD.MM.YYYY') as born,
        to_char(EXTRACT(YEAR from age(directions_issledovaniya.time_confirmation, ci.birthday)), '999') as ind_age
        
        FROM directions_issledovaniya
        LEFT JOIN directions_napravleniya dn on directions_issledovaniya.napravleniye_id = dn.id 
        LEFT JOIN directions_paraclinicresult dp on directions_issledovaniya.id = dp.issledovaniye_id
        LEFT JOIN clients_card cc on dn.client_id = cc.id
        LEFT JOIN clients_individual ci on cc.individual_id = ci.id
        LEFT JOIN directory_paraclinicinputfield dpif on dp.field_id = dpif.id
        LEFT JOIN directions_result dr on directions_issledovaniya.id = dr.issledovaniye_id
        LEFT JOIN directory_fractions df on dr.fraction_id = df.id
        LEFT JOIN directions_issledovaniya pd on pd.id = dn.parent_id
        
        
        WHERE directions_issledovaniya.napravleniye_id in %(directions)s 
        AND directions_issledovaniya.time_confirmation is not Null
        AND ( dpif.id in %(input_field)s OR df.id in %(fraction_field)s)
        ORDER BY pd.napravleniye_id
        """,
            params={'directions': directions, 'input_field': input_field, 'fraction_field': fraction_field, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows
