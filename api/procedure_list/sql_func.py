from django.db import connection
from laboratory.settings import TIME_ZONE


def get_procedure_by_params(d_s, d_e, research_pk=-1):
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT 
            pharmacotherapy_procedurelist.id, 
            pharmacotherapy_drugs.mnn,
            to_char(pharmacotherapy_procedurelist.time_create AT TIME ZONE %(tz)s, 'DD.MM.YYYY-HH24:MI:SS') AS create_procedure,
            pharmacotherapy_formrelease.title,
            pharmacotherapy_methodsreception.title,
            pharmacotherapy_procedurelist.dosage,
            pharmacotherapy_procedurelist.units,
            clients_individual.id,
            concat_ws(' ', clients_individual.family, clients_individual.name, clients_individual.patronymic),
            pharmacotherapy_procedurelist.history_id,
            pharmacotherapy_procedurelist.card_id,
            to_char(pl.times_medication AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_execute,
            to_char(pl.times_medication AT TIME ZONE %(tz)s, 'HH24:MI') AS time_execute,
            pl.cancel,
            pl.executor_id,
            pl.prescription_id,
            pl.fio,
            pharmacotherapy_procedurelist.history_id
            FROM public.pharmacotherapy_procedurelist
                LEFT JOIN pharmacotherapy_drugs ON (pharmacotherapy_procedurelist.drug_id=pharmacotherapy_drugs.id)
                LEFT JOIN pharmacotherapy_formrelease ON (pharmacotherapy_procedurelist.form_release_id=pharmacotherapy_formrelease.id)
                LEFT JOIN pharmacotherapy_methodsreception ON (pharmacotherapy_procedurelist.method_id=pharmacotherapy_methodsreception.id)
                LEFT JOIN clients_card ON (pharmacotherapy_procedurelist.card_id=clients_card.id)
                LEFT JOIN clients_individual ON (clients_card.individual_id=clients_individual.id)
                RIGHT JOIN  
                    (SELECT 
                        pharmacotherapy_procedurelisttimes.times_medication, 
                        pharmacotherapy_procedurelisttimes.cancel, 
                        pharmacotherapy_procedurelisttimes.executor_id,
                        pharmacotherapy_procedurelisttimes.prescription_id,
                        users_doctorprofile.fio
                    FROM pharmacotherapy_procedurelisttimes
                    LEFT JOIN users_doctorprofile ON (pharmacotherapy_procedurelisttimes.executor_id=users_doctorprofile.id)
                        ) as pl
                            ON pl.prescription_id=pharmacotherapy_procedurelist.id
                    WHERE 
                        pl.times_medication AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                        AND
                            CASE
                                WHEN %(research_pk)s > -1 THEN 
                                    research_id = %(research_pk)s
                                 WHEN %(research_pk)s = -1 THEN 
                                     EXISTS (SELECT id from pharmacotherapy_formrelease)
                            END       
            ORDER BY clients_individual.family, clients_individual.id, pharmacotherapy_drugs.mnn, pl.times_medication   
        """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'research_pk': research_pk},
        )
        row = cursor.fetchall()
    return row


def get_procedure_all_times(d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """ SELECT 
            DISTINCT ON (times_medication) to_char(pharmacotherapy_procedurelisttimes.times_medication AT TIME ZONE %(tz)s, 'HH24:MI') as times_medication
            FROM pharmacotherapy_procedurelisttimes
            WHERE pharmacotherapy_procedurelisttimes.times_medication AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
            ORDER BY times_medication
        """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )
        row = cursor.fetchall()
    return row
