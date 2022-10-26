from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def last_result_researches_years(client_id, years, researches):
    if not researches or not years:
        return []

    with connection.cursor() as cursor:
        cursor.execute(
            """
                WITH 
                t_iss AS (
                SELECT
                date_part('year', directions_issledovaniya.time_confirmation) as year_date,
                date_part('month', directions_issledovaniya.time_confirmation) as month_date,
                date_part('day', directions_issledovaniya.time_confirmation) as day_date, 
                directions_issledovaniya.id as iss_id, 
                directions_napravleniya.client_id as card_id, 
                directions_issledovaniya.napravleniye_id as dir_id,
                directions_issledovaniya.research_id as research_id,
                directions_issledovaniya.time_confirmation as confirm
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                    ON directions_issledovaniya.napravleniye_id =directions_napravleniya.id
                WHERE 
                directions_napravleniya.client_id = %(card_pk)s and 
                directions_issledovaniya.research_id = ANY(ARRAY[%(researches)s]) and
                date_part('year', directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s) = ANY(ARRAY[%(years)s])
                ORDER BY directions_issledovaniya.time_confirmation DESC)
                
                SELECT DISTINCT ON (t_iss.year_date, t_iss.research_id) 
                    t_iss.year_date, t_iss.month_date, t_iss.day_date, t_iss.iss_id, t_iss.card_id, t_iss.dir_id, t_iss.research_id, t_iss.confirm
                From t_iss
                ORDER BY t_iss.year_date DESC, t_iss.research_id DESC, t_iss.confirm DESC 
            """,
            params={'tz': TIME_ZONE, 'card_pk': client_id, 'researches': researches, 'years': years},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def last_results_researches_by_time_ago(client_id, researches, date_start, date_end):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                directions_issledovaniya.id as iss_id, 
                directions_napravleniya.client_id as card_id, 
                directions_issledovaniya.napravleniye_id as dir_id,
                directions_issledovaniya.research_id as research_id,
                directions_issledovaniya.time_confirmation,
                to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YY') as confirm,
                directions_result.fraction_id,
                directory_fractions.title,
                directions_result.value
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                    ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                LEFT JOIN directions_result
                    ON directions_result.issledovaniye_id=directions_issledovaniya.id
                LEFT JOIN directory_fractions
                    ON directory_fractions.id=directions_result.fraction_id
                WHERE 
                directions_napravleniya.client_id = %(card_pk)s and 
                directions_issledovaniya.research_id = ANY(ARRAY[%(researches)s]) and
                directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(date_start)s AND %(date_end)s
                ORDER BY directions_issledovaniya.time_confirmation DESC
            """,
            params={'tz': TIME_ZONE, 'card_pk': client_id, 'researches': researches, 'date_start': date_start, 'date_end': date_end},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_individual_age(date_target, individual_pk):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT distinct on (id)  clients_individual.id,
                date_part('year', age(timestamp %(date_target)s, clients_individual.birthday))::int as age_year,
                date_part('month', age(timestamp %(date_target)s, clients_individual.birthday))::int as age_month 
                from clients_individual
                WHERE
                clients_individual.id = %(individual_pk)s
            """,
            params={'individual_pk': individual_pk, 'date_target': date_target},
        )

        rows = namedtuplefetchall(cursor)
    return rows
