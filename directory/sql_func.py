from django.db import connection
from utils.db import namedtuplefetchall


def is_paraclinic_filter_research(reserches_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                  directory_researches.id as research_id
                FROM directory_researches
                WHERE directory_researches.id in %(reserches_id)s AND
                directory_researches.is_paraclinic = true
                order by directory_researches.id
        """,
            params={'reserches_id': reserches_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def is_lab_filter_research(reserches_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                directory_researches.id as research_id
                FROM directory_researches
                LEFT JOIN podrazdeleniya_podrazdeleniya pp on directory_researches.podrazdeleniye_id = pp.id
                WHERE directory_researches.id in %(reserches_id)s AND
                pp.p_type = 2
                order by directory_researches.id
        """,
            params={'reserches_id': reserches_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_lab_research_reference_books():
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                directory_fractions.id as fraction_id,
                directory_fractions.title as fraction_title,
                directory_fractions.fsli as fraction_fsli,
                directory_fractions.ref_m as fraction_ref_m,
                directory_fractions.ref_f as fraction_ref_f,

                du.title as unit_title,
                du.code as unit_code,
                du.ucum as unit_ucum,

                dr.id as research_id,
                dr.title as research_title,
                dr.internal_code as research_internal_code,
                dr.code as research_nmu_code

                FROM directory_fractions
                LEFT JOIN directory_researches dr on dr.id = directory_fractions.research_id
                LEFT JOIN directory_unit du on du.id = directory_fractions.unit_id
                LEFT JOIN podrazdeleniya_podrazdeleniya pp on dr.podrazdeleniye_id = pp.id
                WHERE pp.p_type = 2
                order by dr.id
        """,
            params={},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_fsli_fractions_by_research_id(research_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                directory_fractions.id as fraction_id,
                directory_fractions.title as fraction_title,
                directory_fractions.fsli as fraction_fsli
                FROM directory_fractions
                WHERE directory_fractions.research_id = %(research_id)s
        """,
            params={'research_id': research_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_lab_research_data(department_id, lab_podr=None):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                df.id as fraction_id,
                df.title as fraction_title,
                df.fsli as fraction_fsli,
                dr.internal_code as internal_code,
                dr.title as research_title,
                dr.code as nmu_code,
                dr.hide as hide_status,
                pp.title as group_title,
                ds.title as subgroup_title,
                rft.id as tube_id,
                rt.title as tube_title,
                dr.ecp_id as research_ecp,
                df.ecp_id as fraction_ecp
                FROM directory_researches as dr
                LEFT JOIN directory_fractions df on df.research_id = dr.id
                LEFT JOIN podrazdeleniya_podrazdeleniya pp on dr.podrazdeleniye_id = pp.id
                LEFT JOIN directory_subgroupdirectory ds on dr.sub_group_id = ds.id
                LEFT JOIN directory_releationsft rft on df.relation_id = rft.id
                LEFT JOIN researches_tubes rt on rft.tube_id = rt.id
                WHERE 
                CASE 
                WHEN %(department_id)s > 0 THEN
                    pp.id = %(department_id)s
                WHEN %(department_id)s = 0 THEN 
                    pp.id in %(lab_podr)s
                END
                ORDER BY pp.title, ds.title, dr.title
        """,
            params={'department_id': department_id, 'lab_podr': lab_podr},
        )
        rows = namedtuplefetchall(cursor)
    return rows
