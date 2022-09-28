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
