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
