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


def check_shift(cash_register_id, doctor_profile_id, close_status):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            operator_id,
            cash_register_id,
            close_status
            FROM cash_registers_shift
            WHERE
            (operator_id=$(doctor_profile_id)s or cash_register_id=$(cash_register_id)s)
            and
            close_status = False
            """,
            params={"cash_register_id": cash_register_id, "doctor_profile_id": doctor_profile_id}
        )
        rows = namedtuplefetchall(cursor)
    return rows
