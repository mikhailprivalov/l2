from django.db import connection

from utils.db import namedtuplefetchall

CYRILLIC_UPPER = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
CYRILLIC_LOWER = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"


def participant_plans(doctor_id, date_from, date_to, tz):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                p.id AS plan_id,
                COALESCE(NULLIF(BTRIM(p.title), ''), 'План ' || p.id::text) AS plan_title,
                d.id AS document_id,
                d.time_confirm,
                BOOL_OR(roles.role = 'executor') AS is_executor,
                BOOL_OR(roles.role = 'curator') AS is_curator
            FROM (
                SELECT cp.document_id, cp.plan_id, 'executor' AS role
                FROM control_plan cp
                JOIN control_plan_executor e ON e.control_plan_id = cp.id
                WHERE e.doctor_id = %(doctor_id)s

                UNION

                SELECT cp.document_id, cp.plan_id, 'curator' AS role
                FROM control_plan cp
                JOIN control_plan_curator c ON c.control_plan_id = cp.id
                WHERE c.doctor_id = %(doctor_id)s
            ) roles
            JOIN document_management_documents d ON d.id = roles.document_id
            JOIN document_management_plans p ON p.id = roles.plan_id
            WHERE d.is_hidden = FALSE
              AND d.time_confirm IS NOT NULL
              AND (%(date_from)s IS NULL OR (d.time_confirm AT TIME ZONE %(tz)s)::date >= %(date_from)s)
              AND (%(date_to)s IS NULL OR (d.time_confirm AT TIME ZONE %(tz)s)::date <= %(date_to)s)
            GROUP BY p.id, p.title, d.id, d.time_confirm
            ORDER BY d.time_confirm DESC, d.id DESC, p.id
            """,
            params={
                "doctor_id": doctor_id,
                "date_from": date_from,
                "date_to": date_to,
                "tz": tz,
            },
        )
        return namedtuplefetchall(cursor)


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
