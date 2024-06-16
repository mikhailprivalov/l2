from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def check_limit_assign_researches(
    district_group_id,
):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT users_districtresearchlimitassign.id, 
                users_districtresearchlimitassign.limit_count, 
                users_districtresearchlimitassign.type_period_limit,
                users_districtresearchlimitassign.research_id,
                users_districtresearchlimitassign.district_group_id
                from users_districtresearchlimitassign
                where
                district_group_id = %(district_group_id)s
            """,
            params={'district_group_id': district_group_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_count_researches_by_doc(doctor_pks, d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                directions_issledovaniya.research_id,
                count(directions_napravleniya.id) as count
                FROM directions_napravleniya
                LEFT JOIN directions_issledovaniya
                ON directions_napravleniya.id=directions_issledovaniya.napravleniye_id
                WHERE doc_who_create_id in %(doctor_pks)s and data_sozdaniya AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                group by directions_issledovaniya.research_id
            """,
            params={'doctor_pks': doctor_pks, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def check_confirm_patient_research(client_id, researches, months_ago):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
              DISTINCT ON (directions_issledovaniya.research_id) directions_issledovaniya.research_id as research_id
            FROM directions_issledovaniya
            LEFT JOIN directions_napravleniya 
            ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id 
            WHERE directions_napravleniya.client_id = %(client_id)s
            AND directions_issledovaniya.research_id in %(researches)s 
            AND directions_issledovaniya.time_confirmation BETWEEN (NOW() - interval '%(months_ago)s month')  AND (NOW())
            ORDER BY directions_issledovaniya.research_id, directions_issledovaniya.time_confirmation DESC
            """,
            params={'client_id': client_id, 'researches': researches, 'months_ago': months_ago, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def check_create_direction_patient_by_research(client_id, researches, months_ago):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
              DISTINCT ON (directions_issledovaniya.research_id) directions_issledovaniya.research_id as research_id,
              directions_issledovaniya.napravleniye_id as direction_id
            FROM directions_issledovaniya
            LEFT JOIN directions_napravleniya 
            ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id 
            WHERE directions_napravleniya.client_id = %(client_id)s
            AND directions_issledovaniya.research_id in %(researches)s 
            AND directions_napravleniya.data_sozdaniya BETWEEN (NOW() - interval '%(months_ago)s month')  AND (NOW())
            ORDER BY directions_issledovaniya.research_id, directions_napravleniya.data_sozdaniya DESC
            """,
            params={'client_id': client_id, 'researches': researches, 'months_ago': months_ago, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_researches_by_number_directions(direction_numbers):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
              directions_issledovaniya.research_id
            FROM directions_issledovaniya
            WHERE directions_issledovaniya.napravleniye_id in %(direction_numbers)s 
            """,
            params={'direction_numbers': direction_numbers},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_tube_registration(d_start, d_end, doctorprofile_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            directions_tubesregistration.id as tube_id,
            directions_tubesregistration.number as tube_number,
            directions_tubesregistration.daynum as tube_daynum,
            directions_tubesregistration.defect_text as tube_defect_text,
            directions_tubesregistration.is_defect as tube_is_defect,
            di.napravleniye_id as direction_number,
            dn.external_executor_hospital_id,
            dn.external_order_id,
            dr.title as research_title,
            pp.title as department_title,
            plan_org.title as plan_external_perform_org,
            externalordre_hosp.title as hosp_external_order_api,
            himself_input_external_hosp.title as himself_input_external_hosp_title,
            restubes.title as tube_title,
            restubes.color as tube_color
            
            FROM directions_tubesregistration
            LEFT JOIN directions_issledovaniya_tubes dit on directions_tubesregistration.id = dit.tubesregistration_id
            LEFT JOIN directory_releationsft drft on drft.id = directions_tubesregistration.type_id
            LEFT JOIN researches_tubes restubes on drft.tube_id = restubes.id 
            LEFT JOIN directions_issledovaniya di on dit.issledovaniya_id = di.id
            LEFT JOIN directions_napravleniya dn on di.napravleniye_id = dn.id
            LEFT JOIN directory_researches dr on di.research_id = dr.id
            LEFT JOIN podrazdeleniya_podrazdeleniya pp on dr.podrazdeleniye_id = pp.id
            LEFT JOIN hospitals_hospitals plan_org on dr.plan_external_performing_organization_id = plan_org.id
            LEFT JOIN directions_registeredorders dregorder on dn.external_order_id = dregorder.id
            LEFT JOIN hospitals_hospitals externalordre_hosp on dregorder.organization_id = externalordre_hosp.id
            LEFT JOIN hospitals_hospitals himself_input_external_hosp on dn.hospital_id=himself_input_external_hosp.id
            
            WHERE directions_tubesregistration.doc_recive_id = %(doctorprofile_id)s
            AND directions_tubesregistration.time_recive AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
            ORDER BY directions_tubesregistration.daynum DESC
            """,
            params={'doctorprofile_id': doctorprofile_id, 'd_start': d_start, 'd_end': d_end, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows
