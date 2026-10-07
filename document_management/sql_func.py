from django.db import connection

from utils.db import namedtuplefetchall

CYRILLIC_UPPER = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
CYRILLIC_LOWER = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"


def search_cases_by_topic(topic, limit=50):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id
            FROM document_management_documentcase
            WHERE translate(topic, %(cyr_upper)s, %(cyr_lower)s) ~* translate(%(topic)s, %(cyr_upper)s, %(cyr_lower)s)
            ORDER BY id DESC
            LIMIT %(limit)s
            """,
            params={
                "topic": topic,
                "limit": limit,
                "cyr_upper": CYRILLIC_UPPER,
                "cyr_lower": CYRILLIC_LOWER,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows
