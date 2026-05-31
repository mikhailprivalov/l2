from django.db import connection

from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def load_patients_stationar_unallocated_sql(department_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                family,
                name,
                patronymic,
                sex,
                napravleniye_id,
                directory_researches.title as service_title,
                directions_issledovaniya.id as issledovanie_id,
                birthday,
                date_part('year', age(birthday))::int AS age
                FROM directions_issledovaniya
                INNER JOIN directory_researches ON directions_issledovaniya.research_id = directory_researches.id
                INNER JOIN directions_napravleniya ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                INNER JOIN clients_card ON directions_napravleniya.client_id=clients_card.id
                INNER JOIN public.clients_individual ON clients_card.individual_id = public.clients_individual.id
                WHERE directions_napravleniya.cancel = false
                AND hospital_department_override_id = %(department_id)s
                AND data_sozdaniya > now() - INTERVAL '2 months'
                AND NOT EXISTS (
                    SELECT 1
                    FROM podrazdeleniya_patienttobed ptb
                    INNER JOIN podrazdeleniya_bed bed ON ptb.bed_id = bed.id
                    INNER JOIN podrazdeleniya_chamber ch ON bed.chamber_id = ch.id
                    WHERE ptb.direction_id = directions_napravleniya.id
                    AND ch.podrazdelenie_id = %(department_id)s
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM podrazdeleniya_patientstationarwithoutbeds pswb
                    WHERE pswb.direction_id = directions_napravleniya.id
                    AND pswb.department_id = %(department_id)s
                )
                
                ORDER BY family
                """,
            params={"department_id": department_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_closing_protocols(issledovaniye_ids, titles):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                directions_napravleniya.parent_id
                
                FROM directions_napravleniya
                LEFT JOIN directions_issledovaniya ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN directory_researches ON directions_issledovaniya.research_id = directory_researches.id
                LEFT JOIN directory_hospitalservice ON directory_researches.id = directory_hospitalservice.slave_research_id
                WHERE directions_napravleniya.parent_id IN %(issledovaniye_ids)s
                AND 
                (directory_hospitalservice.site_type = 7 OR (directory_hospitalservice.site_type = 6 AND title IN %(titles)s))

                AND total_confirmed = true
                
                """,
            params={"issledovaniye_ids": issledovaniye_ids, "titles": titles},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def load_patient_without_bed_by_department(department_id, start_date=None, end_date=None):
    period_filter = ""
    params = {"department_id": department_id}
    if start_date is not None and end_date is not None:
        period_filter = """
            AND COALESCE(
                podrazdeleniya_patientstationarwithoutbeds.plan_date_in,
                podrazdeleniya_patientstationarwithoutbeds.date_in,
                %(start_date)s
            ) <= %(end_date)s
            AND (
                CASE
                    WHEN podrazdeleniya_patientstationarwithoutbeds.plan_date_in IS NOT NULL
                      OR podrazdeleniya_patientstationarwithoutbeds.plan_date_out IS NOT NULL
                    THEN COALESCE(
                        podrazdeleniya_patientstationarwithoutbeds.plan_date_out,
                        podrazdeleniya_patientstationarwithoutbeds.date_out,
                        DATE '2200-01-01'
                    )
                    ELSE COALESCE(
                        podrazdeleniya_patientstationarwithoutbeds.date_out,
                        DATE '2200-01-01'
                    )
                END
            ) >= %(start_date)s
        """
        params["start_date"] = start_date
        params["end_date"] = end_date

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
            clients_individual.family as patient_family,
            clients_individual.name as patient_name,
            clients_individual.patronymic as patient_patronymic,
            date_part('year', age(clients_individual.birthday))::int AS patient_age,
            clients_individual.sex as patient_sex,
            direction_id,
            podrazdeleniya_patientstationarwithoutbeds.date_in,
            podrazdeleniya_patientstationarwithoutbeds.date_out,
            podrazdeleniya_patientstationarwithoutbeds.plan_date_in,
            podrazdeleniya_patientstationarwithoutbeds.plan_date_out,
            users_doctorprofile.id as doctor_id,
            is_extract
            
            FROM podrazdeleniya_patientstationarwithoutbeds
            LEFT JOIN directions_napravleniya ON podrazdeleniya_patientstationarwithoutbeds.direction_id = directions_napravleniya.id
            LEFT JOIN clients_card ON directions_napravleniya.client_id = clients_card.id
            LEFT JOIN clients_individual ON clients_card.individual_id = clients_individual.id
            LEFT JOIN users_doctorprofile ON podrazdeleniya_patientstationarwithoutbeds.doctor_id = users_doctorprofile.id
            
            WHERE
            podrazdeleniya_patientstationarwithoutbeds.department_id = %(department_id)s
            {period_filter}
            
            ORDER BY clients_individual.family
            """,
            params=params,
        )

        rows = namedtuplefetchall(cursor)
    return rows


def load_directions_hosp_meta_bulk(direction_pks, cda_discharge_title, fallback_discharge_title):
    if not direction_pks:
        return []
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH direction_ids AS (
                SELECT unnest(%(direction_pks)s::int[]) AS direction_pk
            ),
            pswb_latest AS (
                SELECT DISTINCT ON (pswb.direction_id)
                    pswb.direction_id,
                    pswb.plan_date_in,
                    pswb.plan_date_out,
                    pswb.date_in,
                    pswb.date_out,
                    pswb.is_extract
                FROM podrazdeleniya_patientstationarwithoutbeds pswb
                WHERE pswb.direction_id = ANY(%(direction_pks)s)
                ORDER BY pswb.direction_id, pswb.id DESC
            ),
            ptb_latest AS (
                SELECT DISTINCT ON (ptb.direction_id)
                    ptb.direction_id,
                    ptb.plan_date_in,
                    ptb.plan_date_out,
                    ptb.date_in,
                    ptb.date_out,
                    ptb.is_extract
                FROM podrazdeleniya_patienttobed ptb
                WHERE ptb.direction_id = ANY(%(direction_pks)s)
                ORDER BY ptb.direction_id, ptb.id DESC
            ),
            discharge_by_direction AS (
                SELECT DISTINCT ON (d.direction_pk)
                    d.direction_pk,
                    COALESCE(cda_val.value, fb_val.value) AS discharge_value_raw
                FROM direction_ids d
                INNER JOIN directions_issledovaniya d_iss ON d_iss.time_confirmation IS NOT NULL
                INNER JOIN directions_napravleniya dn ON d_iss.napravleniye_id = dn.id
                INNER JOIN directory_researches dr ON d_iss.research_id = dr.id
                LEFT JOIN LATERAL (
                    SELECT pr.value
                    FROM directions_paraclinicresult pr
                    INNER JOIN directory_paraclinicinputfield pf ON pr.field_id = pf.id
                    INNER JOIN external_system_cdafields cda ON pf.cda_option_id = cda.id
                    WHERE pr.issledovaniye_id = d_iss.id
                      AND cda.title = %(cda_discharge_title)s
                      AND pr.value IS NOT NULL
                      AND pr.value <> ''
                    ORDER BY pf."order"
                    LIMIT 1
                ) cda_val ON TRUE
                LEFT JOIN LATERAL (
                    SELECT pr.value
                    FROM directions_paraclinicresult pr
                    INNER JOIN directory_paraclinicinputfield pf ON pr.field_id = pf.id
                    WHERE pr.issledovaniye_id = d_iss.id
                      AND pf.title = %(fallback_discharge_title)s
                      AND pr.value IS NOT NULL
                      AND pr.value <> ''
                    ORDER BY pf."order"
                    LIMIT 1
                ) fb_val ON TRUE
                WHERE (d_iss.napravleniye_id = d.direction_pk OR dn.parent_id = d.direction_pk)
                  AND (dr.desc IS NULL OR dr.desc = '')
                  AND (
                    dr.title ILIKE '%%выписка%%'
                    OR dr.title ILIKE '%%выписной%%'
                    OR dr.title ILIKE '%%посмертный%%'
                  )
                  AND COALESCE(cda_val.value, fb_val.value) IS NOT NULL
                  AND COALESCE(cda_val.value, fb_val.value) <> ''
                ORDER BY d.direction_pk, d_iss.time_confirmation DESC NULLS LAST
            )
            SELECT
                d.direction_pk,
                (pswb.direction_id IS NOT NULL) AS has_pswb,
                pswb.plan_date_in AS pswb_plan_date_in,
                pswb.plan_date_out AS pswb_plan_date_out,
                pswb.date_in AS pswb_date_in,
                pswb.date_out AS pswb_date_out,
                pswb.is_extract AS pswb_is_extract,
                (ptb.direction_id IS NOT NULL) AS has_ptb,
                ptb.plan_date_in AS ptb_plan_date_in,
                ptb.plan_date_out AS ptb_plan_date_out,
                ptb.date_in AS ptb_date_in,
                ptb.date_out AS ptb_date_out,
                ptb.is_extract AS ptb_is_extract,
                dd.discharge_value_raw
            FROM direction_ids d
            LEFT JOIN pswb_latest pswb ON pswb.direction_id = d.direction_pk
            LEFT JOIN ptb_latest ptb ON ptb.direction_id = d.direction_pk
            LEFT JOIN discharge_by_direction dd ON dd.direction_pk = d.direction_pk
            ORDER BY d.direction_pk
            """,
            params={
                "direction_pks": direction_pks,
                "cda_discharge_title": cda_discharge_title,
                "fallback_discharge_title": fallback_discharge_title,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def load_attending_doctor_by_department(department_id, group_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            users_doctorprofile.id,
            users_doctorprofile.family,
            users_doctorprofile.name,
            users_doctorprofile.patronymic
            
            FROM users_doctorprofile
            LEFT JOIN auth_user ON users_doctorprofile.user_id = auth_user.id
            LEFT JOIN auth_user_groups ON auth_user.id = auth_user_groups.user_id
            LEFT JOIN auth_group ON auth_user_groups.group_id = auth_group.id
            WHERE 
            auth_group.id = %(group_id)s
            AND users_doctorprofile.podrazdeleniye_id = %(department_id)s
            AND users_doctorprofile.dismissed = false
            
            ORDER BY family
            """,
            params={"department_id": department_id, "group_id": group_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def load_attending_doctor_by_department_and_group_title(department_id, group_title):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            users_doctorprofile.id,
            users_doctorprofile.family,
            users_doctorprofile.name,
            users_doctorprofile.patronymic

            FROM users_doctorprofile
            LEFT JOIN auth_user ON users_doctorprofile.user_id = auth_user.id
            LEFT JOIN auth_user_groups ON auth_user.id = auth_user_groups.user_id
            LEFT JOIN auth_group ON auth_user_groups.group_id = auth_group.id
            WHERE
            auth_group.name = %(group_title)s
            AND users_doctorprofile.podrazdeleniye_id = %(department_id)s
            AND users_doctorprofile.dismissed = false

            ORDER BY family
            """,
            params={"department_id": department_id, "group_title": group_title},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def load_chambers_and_beds_by_department(department_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
             SELECT 
             podrazdeleniya_chamber.id as chamber_id,
             podrazdeleniya_chamber.title as chamber_title,
             
             podrazdeleniya_bed.id as bed_id,
             podrazdeleniya_bed.bed_number,
             
             clients_individual.family as patient_family,
             clients_individual.name as patient_name,
             clients_individual.patronymic as patient_patronymic,
             date_part('year', age(clients_individual.birthday))::int AS patient_age,
             clients_individual.sex as patient_sex,
             
             patient_table.direction_id,
             
             users_doctorprofile.id as doctor_id,
             users_doctorprofile.family as doctor_family,
             users_doctorprofile.name as doctor_name,
             users_doctorprofile.patronymic as doctor_patronymic

             FROM podrazdeleniya_chamber
             LEFT JOIN podrazdeleniya_bed ON podrazdeleniya_chamber.id = podrazdeleniya_bed.chamber_id
             LEFT JOIN 
             (SELECT * FROM podrazdeleniya_patienttobed WHERE date_out is NULL) as patient_table ON bed_id = podrazdeleniya_bed.id
             LEFT JOIN directions_napravleniya ON patient_table.direction_id = directions_napravleniya.id
             LEFT JOIN clients_card ON directions_napravleniya.client_id = clients_card.id
             LEFT JOIN clients_individual ON clients_card.individual_id = clients_individual.id
             LEFT JOIN users_doctorprofile ON patient_table.doctor_id = users_doctorprofile.id
             
             WHERE
             podrazdeleniya_chamber.podrazdelenie_id = %(department_id)s
             
             ORDER BY podrazdeleniya_chamber.id, bed_number

                """,
            params={"department_id": department_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def load_plan_operations_next_day(start_time, end_time):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            direction
            FROM plans_planoperations
            WHERE date AT TIME ZONE %(tz)s BETWEEN %(start_time)s AND %(end_time)s
            """,
            params={"tz": TIME_ZONE, "start_time": start_time, "end_time": end_time},
        )

        rows = namedtuplefetchall(cursor)
    return rows
