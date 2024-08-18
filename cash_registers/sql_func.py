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


def check_shift(cash_register_id, doctor_profile_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            operator_id,
            cash_register_id,
            close_status
            FROM cash_registers_shift
            WHERE
            (operator_id=%(doctor_profile_id)s or cash_register_id=%(cash_register_id)s)
            and
            close_status = False
            """,
            params={"cash_register_id": cash_register_id, "doctor_profile_id": doctor_profile_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_service_coasts(services_ids):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT directory_researches.id as research_id, directory_researches.title, contracts_pricecoast.coast FROM directions_istochnikifinansirovaniya
            INNER JOIN clients_cardbase ON directions_istochnikifinansirovaniya.base_id = clients_cardbase.id
            INNER JOIN contracts_contract ON directions_istochnikifinansirovaniya.contracts_id = contracts_contract.id
            INNER JOIN contracts_pricecoast ON contracts_contract.price_id = contracts_pricecoast.price_name_id
            INNER JOIN directory_researches ON contracts_pricecoast.research_id = directory_researches.id
            WHERE LOWER(directions_istochnikifinansirovaniya.title) = 'платно' and clients_cardbase.internal_type = true
            AND contracts_pricecoast.research_id in %(services_ids)s
            """,
            params={"services_ids": services_ids},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_services(services_ids):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT directory_researches.id, directory_researches.title FROM directory_researches
            WHERE directory_researches.id in %(services_ids)s
            """,
            params={"services_ids": services_ids},
        )
        rows = namedtuplefetchall(cursor)
    return rows
