from django.db import connection

from utils.db import namedtuplefetchall


def get_cash_registers():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM cash_registers_cashregister
            """,
        )
        rows = namedtuplefetchall(cursor)
    return rows
