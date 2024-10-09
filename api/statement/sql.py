from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def get_tubes_without_statement(directions, user_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """ 
        SELECT
        DISTINCT dt.number as tube_number,
        dn.id as direction_id,
        ci.name as patient_name,
        ci.family as patient_family,
        ci.patronymic as patient_patronymic,
        to_char(ci.birthday, 'DD.MM.YYYY') AS patient_birthday,
        cc.number as card_number

        FROM directions_issledovaniya
        LEFT JOIN directions_issledovaniya_tubes dit on directions_issledovaniya.id = dit.issledovaniya_id
        LEFT JOIN directions_tubesregistration dt on dt.id = dit.tubesregistration_id
        LEFT JOIN directions_napravleniya dn on directions_issledovaniya.napravleniye_id = dn.id
        LEFT JOIN clients_card cc on dn.client_id=cc.id
        LEFT JOIN clients_individual ci on cc.individual_id = ci.id

        WHERE directions_issledovaniya.napravleniye_id in %(directions)s
        AND dn.doc_who_create_id = %(user_id)s
        AND dt.statement_document_id is Null
        AND dt.number is not Null
        ORDER BY dn.id, dt.number

        """,
            params={"directions": directions, "user_id": user_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_who_create_directions(directions):
    with connection.cursor() as cursor:
        cursor.execute(
            """ 
        SELECT
        DISTINCT ON (doc_who_create_id) doc_who_create_id
        FROM directions_napravleniya
        WHERE directions_napravleniya.id in %(directions)s
        """,
            params={"directions": directions},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_directions_by_tube_regitration_number(tube_numbers):
    with connection.cursor() as cursor:
        cursor.execute(
            """ 
        SELECT
        dn.id as direction_id,
        dt.number as tube_number
        FROM directions_issledovaniya
        LEFT JOIN directions_issledovaniya_tubes dit on directions_issledovaniya.id = dit.issledovaniya_id
        LEFT JOIN directions_tubesregistration dt on dt.id = dit.tubesregistration_id
        LEFT JOIN directions_napravleniya dn on directions_issledovaniya.napravleniye_id = dn.id

        WHERE dt.number in %(tube_numbers)s
        ORDER BY dn.id, dt.number

        """,
            params={"tube_numbers": tube_numbers},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_statement_document_data(statement_ids, start_date, end_date):
    with connection.cursor() as cursor:
        cursor.execute(
            """ 
        SELECT
        directions_tubesregistration.number as tube_number,
        ds.create_at,
        directions_tubesregistration.statement_document_id as statement_id
        FROM directions_tubesregistration
        LEFT JOIN directions_statementdocument ds on directions_tubesregistration.statement_document_id = ds.id
        WHERE directions_tubesregistration.statement_document_id in %(statement_ids)s
        AND ds.create_at AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
        ORDER BY ds.create_at DESC 
        """,
            params={"statement_ids": statement_ids, "d_start": start_date, "d_end": end_date, "tz": TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows
