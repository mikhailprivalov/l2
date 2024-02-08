from django.db import connection
from utils.db import namedtuplefetchall


def search_hospitals(hospital_title="-1", limit=400):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT id, title FROM hospitals_hospitals
            WHERE title ~* %(hospital_title)s
        LIMIT %(limit)s
        """,
            params={"hospital_title": hospital_title, "limit": limit},
        )
        rows = namedtuplefetchall(cursor)
    return rows
