from django.db import connection
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


def get_examination_data(date, company_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT public.clients_card.id as card_id, family, name, patronymic, date as examination_date,
            public.clients_harmfulfactor.title as harmful_factor,
            public.directory_researches.id as research_id, 
            public.directory_researches.title as research_title
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
        WHERE date = %(date)s and contracts_medicalexamination.company_id = %(company_id)s
            """,
            params={"date": date, "company_id": company_id}
        )
        rows = namedtuplefetchall(cursor)
    return rows
