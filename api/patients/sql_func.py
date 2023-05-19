from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def get_patient_control_params(start_date, end_date, control_params, card_pk):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                dp.patient_control_param_id, 
                di.time_confirmation, 
                value, 
                dn.id as direction,
                to_char(di.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS confirm,
                to_char(di.time_confirmation AT TIME ZONE %(tz)s, 'YYYY-MM') AS yearmonth_confirm
            FROM directions_paraclinicresult
            LEFT JOIN directory_paraclinicinputfield dp on directions_paraclinicresult.field_id = dp.id
            LEFT JOIN directions_issledovaniya di on directions_paraclinicresult.issledovaniye_id=di.id
            LEFT JOIN directions_napravleniya dn on dn.id=di.napravleniye_id
            WHERE
                dn.client_id = %(card_pk)s AND 
                dp.patient_control_param_id in %(control_params)s AND
                di.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(start_date)s AND %(end_date)s
            UNION
            SELECT
                df.patient_control_param_id, 
                di.time_confirmation, 
                value, 
                dn.id,
                to_char(di.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS confirm,
                to_char(di.time_confirmation AT TIME ZONE %(tz)s, 'YYYY-MM') AS yearmonth_confirm
            FROM directions_result
            LEFT JOIN directory_fractions df on directions_result.fraction_id = df.id
            LEFT JOIN directions_issledovaniya di on directions_result.issledovaniye_id = di.id
            LEFT JOIN directions_napravleniya dn on dn.id=di.napravleniye_id
            WHERE
                dn.client_id = %(card_pk)s AND 
                df.patient_control_param_id in %(control_params)s AND
                di.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(start_date)s AND %(end_date)s
            ORDER BY patient_control_param_id, time_confirmation
            """,
            params={'start_date': start_date, 'end_date': end_date, 'control_params': control_params, 'card_pk': card_pk, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_laboratory_patient_control_params(start_date, end_date, control_params, card_pk):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                dp.patient_control_param_id, di.time_confirmation, value, dn.id as direction,
                to_char(di.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS confirm,
                to_char(di.time_confirmation AT TIME ZONE %(tz)s, 'YYYY-MM') AS yearmonth_confirm
            FROM directions_result
            LEFT JOIN directory_fractions dp on directions_result.fraction_id = dp.id = dp.id
            LEFT JOIN directions_issledovaniya di on directions_result.issledovaniye_id = di.id
            LEFT JOIN directions_napravleniya dn on dn.id=di.napravleniye_id
            WHERE
                dn.client_id = %(card_pk)s AND 
                dp.patient_control_param_id in %(control_params)s AND
                di.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(start_date)s AND %(end_date)s
            ORDER BY dp.patient_control_param_id, di.time_confirmation
            """,
            params={'start_date': start_date, 'end_date': end_date, 'control_params': control_params, 'card_pk': card_pk, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_patient_control_params_to_hosp(control_params, card_pk, parent_iss, limit=1):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                dp.patient_control_param_id, 
                di.time_confirmation, 
                value, 
                dn.id as direction,
                to_char(di.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS confirm
            FROM directions_paraclinicresult
            LEFT JOIN directory_paraclinicinputfield dp on directions_paraclinicresult.field_id = dp.id
            LEFT JOIN directions_issledovaniya di on directions_paraclinicresult.issledovaniye_id=di.id
            LEFT JOIN directions_napravleniya dn on dn.id=di.napravleniye_id
            WHERE
                dn.client_id = %(card_pk)s AND 
                dp.patient_control_param_id in %(control_params)s AND
                di.time_confirmation is not NULL AND
                dn.parent_id in %(parent_iss)s
            UNION
            SELECT
                df.patient_control_param_id, 
                di.time_confirmation, 
                value, 
                dn.id,
                to_char(di.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS confirm
            FROM directions_result
            LEFT JOIN directory_fractions df on directions_result.fraction_id = df.id
            LEFT JOIN directions_issledovaniya di on directions_result.issledovaniye_id = di.id
            LEFT JOIN directions_napravleniya dn on dn.id=di.napravleniye_id
            WHERE
                dn.client_id = %(card_pk)s AND 
                df.patient_control_param_id in %(control_params)s AND
                di.time_confirmation is not NULL AND
                dn.parent_id in %(parent_iss)s
            ORDER BY patient_control_param_id, time_confirmation DESC LIMIT %(limit)s
            """,
            params={'control_params': control_params, 'card_pk': card_pk, 'tz': TIME_ZONE, 'parent_iss': parent_iss, 'limit': limit},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def search_cards_by_numbers(numbers, document_types):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                clients_document.individual_id as ind_id,
                cc.id as card_id,
                cc.number as card_number,
                clients_document.number as document_number,
                clients_individual.family,
                clients_individual.name,
                clients_individual.patronymic,
                cd.title as district_title
            FROM clients_document
            LEFT JOIN clients_card cc on clients_document.individual_id = cc.individual_id
            LEFT JOIN clients_individual on clients_document.individual_id = clients_individual.id
            LEFT JOIN clients_cardbase cb on cc.base_id = cb.id
            LEFT JOIN clients_district cd on cc.district_id = cd.id
            WHERE
            clients_document.number in %(numbers)s AND
            clients_document.document_type_id = %(document_types)s AND 
            cb.internal_type=true
            ORDER BY cc.id
            """,
            params={'numbers': numbers, 'document_types': document_types},
        )

        rows = namedtuplefetchall(cursor)
    return rows
