from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def indicator_sql(fields_ids, date_start, date_end, filter_by_date, has_start, has_end):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                    directions_issledovaniya.napravleniye_id as direction_id,
                    directions_issledovaniya.document_id as document_id,
                    directions_issledovaniya.id as issledovaniye_id,
                    to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as d_confirm,
                    COALESCE(direction_hospital.title, creator_hospital.title) as hospital_title,
                    dp.field_id,
                    dp.value as result_value,
                    dpf.title as field_title,
                    dpgr.title as group_title
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                LEFT JOIN hospitals_hospitals direction_hospital
                ON direction_hospital.id=directions_napravleniya.hospital_id
                LEFT JOIN document_management_documents doc
                ON doc.id=directions_issledovaniya.document_id
                LEFT JOIN users_doctorprofile creator
                ON creator.id=doc.who_create_id
                LEFT JOIN hospitals_hospitals creator_hospital
                ON creator_hospital.id=creator.hospital_id
                LEFT JOIN directions_paraclinicresult dp on directions_issledovaniya.id = dp.issledovaniye_id
                LEFT JOIN directory_paraclinicinputfield dpf on dpf.id = dp.field_id
                LEFT JOIN directory_paraclinicinputgroups dpgr on dpgr.id = dpf.group_id
                WHERE dp.field_id in %(fields_ids)s
                  AND directions_issledovaniya.time_confirmation IS NOT NULL
                  AND (
                    %(filter_by_date)s IS FALSE
                    OR (
                      (%(has_start)s IS FALSE OR directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s >= %(d_start)s)
                      AND (%(has_end)s IS FALSE OR directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s <= %(d_end)s)
                    )
                  )
                ORDER BY directions_issledovaniya.document_id, directions_issledovaniya.napravleniye_id, dpgr.title, dpf.title
            """,
            params={
                'tz': TIME_ZONE,
                'fields_ids': fields_ids,
                'd_start': date_start,
                'd_end': date_end,
                'filter_by_date': filter_by_date,
                'has_start': has_start,
                'has_end': has_end,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def approval_journal_sql(date_start, date_end, filter_by_date, hospital_id, filter_hospital, document_id, document_ids, use_document_ids):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT DISTINCT ON (iss.document_id, iss.id, dpgr.id)
                    iss.document_id AS document_id,
                    iss.id AS iss_id,
                    iss.time_confirmation AS time_confirmation,
                    COALESCE(direction_hospital.id, creator_hospital.id) AS hospital_id,
                    COALESCE(direction_hospital.title, creator_hospital.title, '') AS hospital_title,
                    dpgr.id AS group_id,
                    curator_field.field_id AS curator_field_id,
                    COALESCE(ind.approved, FALSE) AS approved
                FROM directions_paraclinicresult dp
                JOIN directory_paraclinicinputfield dpf ON dpf.id = dp.field_id
                JOIN directory_paraclinicinputgroups dpgr ON dpgr.id = dpf.group_id
                JOIN directions_issledovaniya iss ON iss.id = dp.issledovaniye_id
                LEFT JOIN directions_napravleniya nap ON nap.id = iss.napravleniye_id
                LEFT JOIN hospitals_hospitals direction_hospital ON direction_hospital.id = nap.hospital_id
                LEFT JOIN document_management_documents doc ON doc.id = iss.document_id
                LEFT JOIN users_doctorprofile creator ON creator.id = doc.who_create_id
                LEFT JOIN hospitals_hospitals creator_hospital ON creator_hospital.id = creator.hospital_id
                LEFT JOIN (
                    SELECT DISTINCT ON (group_id) group_id, id AS field_id
                    FROM directory_paraclinicinputfield
                    WHERE field_type IN (10, 18)
                    ORDER BY group_id, id
                ) curator_field ON curator_field.group_id = dpgr.id
                LEFT JOIN directions_paraclinicresultindicator ind
                    ON ind.issledovaniye_id = iss.id AND ind.field_id = curator_field.field_id
                WHERE iss.document_id IS NOT NULL
                  AND iss.time_confirmation IS NOT NULL
                  AND dpgr.cda_option_id IN (
                    SELECT indicator_id
                    FROM external_system_curatorcdafields
                    WHERE indicator_id IS NOT NULL
                  )
                  AND (%(document_id)s IS NULL OR iss.document_id = %(document_id)s)
                  AND (%(use_document_ids)s IS FALSE OR iss.document_id = ANY(%(document_ids)s))
                  AND (%(filter_hospital)s IS FALSE OR COALESCE(direction_hospital.id, creator_hospital.id) = %(hospital_id)s)
                  AND (
                    %(filter_by_date)s IS FALSE
                    OR (
                      iss.time_confirmation AT TIME ZONE %(tz)s >= %(d_start)s
                      AND iss.time_confirmation AT TIME ZONE %(tz)s <= %(d_end)s
                    )
                  )
                ORDER BY iss.document_id, iss.id, dpgr.id, dpf.id
            """,
            params={
                "tz": TIME_ZONE,
                "d_start": date_start,
                "d_end": date_end,
                "filter_by_date": filter_by_date,
                "hospital_id": hospital_id,
                "filter_hospital": filter_hospital,
                "document_id": document_id,
                "document_ids": document_ids,
                "use_document_ids": use_document_ids,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows
