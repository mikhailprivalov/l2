import datetime
from django.db import connection

from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def search_companies(company_title="-1", limit=400):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT id, title FROM public.contracts_company
            WHERE active_status=true AND title ~* %(company_title)s
        LIMIT %(limit)s
        """,
            params={"company_title": company_title, "limit": limit},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_examination_data(company_id, date_start, date_end, current_year_last_date):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT public.clients_card.id as card_id, family, name, patronymic, date as examination_date,
            public.clients_harmfulfactor.title as harmful_factor,
            public.directory_researches.id as research_id, 
            public.directory_researches.title as research_title,
            date_part('year', age(timestamp %(current_year_last_date)s, clients_individual.birthday)) as age_year,
            public.clients_individual.sex as sex
        FROM public.contracts_medicalexamination
            INNER JOIN public.clients_card
              ON public.contracts_medicalexamination.card_id = public.clients_card.id
            INNER JOIN public.clients_individual
              ON public.clients_card.individual_id = public.clients_individual.id
            INNER JOIN clients_patientharmfullfactor 
              ON public.contracts_medicalexamination.card_id = public.clients_patientharmfullfactor.card_id
            INNER JOIN public.clients_harmfulfactor
              ON public.clients_patientharmfullfactor.harmful_factor_id = public.clients_harmfulfactor.id
            INNER JOIN public.users_assignmentresearches
              ON public.clients_harmfulfactor.template_id = users_assignmentresearches.template_id
            INNER JOIN public.directory_researches
              ON public.users_assignmentresearches.research_id = public.directory_researches.id
        WHERE date BETWEEN %(date_start)s AND %(date_end)s and contracts_medicalexamination.company_id = %(company_id)s
        ORDER BY contracts_medicalexamination.card_id
        """,
            params={"date_start": date_start, "date_end": date_end, "company_id": company_id, "current_year_last_date": current_year_last_date},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_research_coast_by_prce(price_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT price_name_id, research_id, coast
        FROM contracts_pricecoast
        WHERE contracts_pricecoast.price_name_id in %(price_id)s
        
        """,
            params={"price_id": price_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_data_for_confirm_billing(billing_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                    directions_issledovaniya.napravleniye_id as dir_id,
                    directions_issledovaniya.id as iss_id,
                    directions_issledovaniya.research_id,
                    directory_researches.title as research_title,
                    directory_researches.internal_code as internal_code,
                    directory_researches.code as code_nmu,
                    to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_confirm,
                    directions_issledovaniya.time_confirmation,
                    directions_napravleniya.client_id,
                    cc.number as patient_card_num,
                    ci.family as patient_family,
                    ci.name as patient_name,
                    ci.patronymic as patient_patronymic,
                    to_char(ci.birthday,'DD.MM.YYYY') as ru_date_born,
                    date_part('year', age(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, ci.birthday))::int as patient_age,
                    dtr.number as tube_number
                FROM directions_issledovaniya
                LEFT JOIN directions_issledovaniya_tubes dit
                ON directions_issledovaniya.id = dit.issledovaniya_id

                LEFT JOIN directions_tubesregistration dtr
                ON dit.tubesregistration_id = dtr.id

                LEFT JOIN directory_researches 
                ON directory_researches.id=directions_issledovaniya.research_id
                LEFT JOIN directions_napravleniya
                ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN clients_card cc
                ON directions_napravleniya.client_id = cc.id
                LEFT JOIN clients_individual ci 
                ON ci.id = cc.individual_id

                WHERE 
                    directions_issledovaniya.billing_id = %(billing_id)s
                ORDER BY 
                    directions_napravleniya.client_id, 
                    directions_issledovaniya.time_confirmation
                            """,
            params={'billing_id': billing_id, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows



