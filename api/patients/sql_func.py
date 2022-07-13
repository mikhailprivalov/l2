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
