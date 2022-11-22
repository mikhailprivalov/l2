import json
from django.db import connection
from laboratory.settings import TIME_ZONE, DEATH_RESEARCH_PK
from utils.db import namedtuplefetchall


def find_death_by_dignoses(start_date, end_date, diagnoses, exclude_hospital_pk):
    result = get_death_data(start_date, end_date, exclude_hospital_pk)
    directions = set()
    for i in result:
        val = json.loads(i.value)
        if len(val["rows"]) > 0 and len(val["rows"][0]) > 2 and "code" in val["rows"][0][2]:
            code_data = json.loads(val["rows"][0][2])
            if code_data["code"] in diagnoses:
                directions.add(i.napravleniye_id)
    return directions


def get_death_data(date_start, date_end, exclude_hospital_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
              SELECT 
                  directions_paraclinicresult.issledovaniye_id, 
                  directions_paraclinicresult.value, 
                  directions_paraclinicresult.field_id, 
                  directions_paraclinicresult.field_type,
                  directions_paraclinicresult.value_json,
                  directions_issledovaniya.research_id,
                  directions_issledovaniya.napravleniye_id
              FROM public.directions_paraclinicresult
              LEFT JOIN directions_issledovaniya ON
                directions_issledovaniya.id = issledovaniye_id
              WHERE field_type=27 and directions_issledovaniya.research_id=%(research_id)s and 
                directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s 
              BETWEEN %(date_start)s AND %(date_end)s
              and directions_issledovaniya.doc_confirmation_id not in (SELECT id from users_doctorprofile where hospital_id=%(hospital_id)s)
            """,
            params={"research_id": DEATH_RESEARCH_PK, "date_start": date_start, "date_end": date_end, "hospital_id": exclude_hospital_id, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows
