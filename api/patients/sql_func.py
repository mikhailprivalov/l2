from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def get_patient_control_params_by_years(start_date, end_date, control_params, card_pk):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                value, dp.patient_control_param_id, di.time_confirmation
            FROM directions_paraclinicresult
            LEFT JOIN directory_paraclinicinputfield dp on directions_paraclinicresult.field_id = dp.id
            LEFT JOIN directions_issledovaniya di on directions_paraclinicresult.issledovaniye_id=di.id
            
            WHERE 
                client_id = %(card_pk)s AND 
                dp.patient_control_param_id in %(control_params)s AND
                di.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
            ORDER BY dp.patient_control_param_id, di.time_confirmation
            """,
            params={'start_date': start_date, 'end_date': end_date, 'control_params': control_params, 'card_pk': card_pk, 'TZ': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows
