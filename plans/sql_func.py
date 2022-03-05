from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def get_messages_by_plan_hospitalization(plan_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT 
            message, 
            created_at, 
            plan_id,
            to_char(created_at AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_create,
            to_char(created_at AT TIME ZONE %(tz)s, 'HH24:MI') AS time_create,
            concat(ud.family, ' ', ud.name,  ' ', ud.patronymic) as fio_create             
        FROM plans_messages
        LEFT JOIN users_doctorprofile ud ON plans_messages.doc_who_create_id = ud.id
        WHERE plan_id = %(plan_id)s
        ORDER BY created_at DESC """,
            params={'plan_id': plan_id, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_messages_by_card_id(card_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT 
            message, 
            created_at, 
            plan_id,
            client_id,
            to_char(created_at AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_create,
            to_char(created_at AT TIME ZONE %(tz)s, 'HH24:MI') AS time_create
        FROM plans_messages
        WHERE client_id = %(card_id)s
        ORDER BY created_at DESC """,
            params={'card_id': card_id, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows
