from django.db import connection
from utils.db import namedtuplefetchall


def get_users_by_role(groups_title):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            id
            FROM users_doctorprofile
            WHERE users_doctorprofile.user_id IN (
            SELECT
              auth_user_groups.user_id as user_id
            FROM auth_user_groups
            WHERE
            auth_user_groups.group_id in (SELECT id from auth_group where name in %(groups_title)s))
            """,
            params={'groups_title': groups_title},
        )
        rows = namedtuplefetchall(cursor)
    return rows
