from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall
from django.db import connection


def get_pharmacotherapy_exec_by_directions(directions_tuple):

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                pharmacotherapy_procedurelist.history_id,
                pharmacotherapy_procedurelisttimes.prescription_id,
                pharmacotherapy_procedurelist.drug_id,
                pharmacotherapy_drugs.mnn,
                pharmacotherapy_drugs.trade_name,
                pharmacotherapy_methodsreception.title as method_title,
                pharmacotherapy_formrelease.title as form_title,
                pharmacotherapy_procedurelist.dosage,
                pharmacotherapy_procedurelist.units,
                pharmacotherapy_procedurelist.comment,
                to_char(pharmacotherapy_procedurelisttimes.times_medication, 'DD.MM.YYYY') as date_char,
                to_char(pharmacotherapy_procedurelisttimes.times_medication, 'HH:MI') as time_char,
                pharmacotherapy_procedurelisttimes.times_medication,
                pharmacotherapy_procedurelisttimes.executor_id
                FROM pharmacotherapy_procedurelisttimes
                LEFT JOIN pharmacotherapy_procedurelist
                ON pharmacotherapy_procedurelist.id = pharmacotherapy_procedurelisttimes.prescription_id
                LEFT JOIN pharmacotherapy_drugs
                ON pharmacotherapy_procedurelist.drug_id = pharmacotherapy_drugs.id
                LEFT JOIN pharmacotherapy_formrelease
                ON pharmacotherapy_procedurelist.form_release_id = pharmacotherapy_formrelease.id
                LEFT JOIN pharmacotherapy_methodsreception
                ON pharmacotherapy_procedurelist.method_id = pharmacotherapy_methodsreception.id
                where pharmacotherapy_procedurelist.history_id in %(directions_tuple)s and
                pharmacotherapy_procedurelisttimes.executor_id is not null
                ORDER BY pharmacotherapy_procedurelist.history_id, drug_id, pharmacotherapy_procedurelisttimes.prescription_id, times_medication
            """,
            params={'directions_tuple': directions_tuple, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows
