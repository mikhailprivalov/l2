from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def get_confirm_research(research_id, date_start, date_end):
    with connection.cursor() as cursor:
        cursor.execute(
            """
             SELECT research_id, doc_confirmation_id,
             hh.title as title_mo,
             hh.oid as oid_mo
            FROM directions_issledovaniya
            INNER JOIN users_doctorprofile doctor
              ON directions_issledovaniya.doc_confirmation_id = doctor.id
            LEFT JOIN hospitals_hospitals hh on doctor.hospital_id = hh.id

            WHERE time_confirmation AT TIME ZONE %(tz)s BETWEEN %(date_start)s and %(date_end)s and research_id=%(research_id)s
                  """,
            params={"research_id": research_id, "date_start": date_start, "date_end": date_end, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows
