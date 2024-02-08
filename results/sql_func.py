from django.db import connection

from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def get_confirm_direction(list_dirs):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT DISTINCT ON (napravleniye_id) napravleniye_id FROM public.directions_issledovaniya
        WHERE napravleniye_id = ANY(ARRAY[%(num_dirs)s])
        AND time_confirmation IS NOT NULL
        """,
            params={'num_dirs': list_dirs},
        )
        row = cursor.fetchall()
    return row


def get_not_confirm_direction(list_dirs):
    if not list_dirs:
        return []

    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT DISTINCT ON (napravleniye_id) napravleniye_id FROM public.directions_issledovaniya
        WHERE napravleniye_id = ANY(ARRAY[%(num_dirs)s])
        AND time_confirmation IS NULL
        """,
            params={'num_dirs': list_dirs},
        )
        row = cursor.fetchall()
    return row


def get_direction_by_client(list_dirs):
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT id as dir_id, client_id  FROM public.directions_napravleniya WHERE id = ANY(ARRAY[%(num_dirs)s]) order by client_id""",
            params={'num_dirs': list_dirs},
        )
        row = cursor.fetchall()
    return row


def get_laboratory_results_by_directions(list_dirs):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT 
                directions_issledovaniya.id as iss_id,
                directions_issledovaniya.napravleniye_id as direction,
                directions_issledovaniya.research_id,
                directions_issledovaniya.doc_confirmation_id as doctor_id,
                directions_issledovaniya.doc_confirmation_string as doc_confirmation_string,
                directory_researches.title as research_title,
                directory_researches.internal_code as research_internal_code,
                directions_result.value as value,
                directions_result.fraction_id,
                directions_result.id as result_is,
                directory_fractions.title as fraction_title,
                directory_fractions.fsli as fraction_fsli,
                directions_result.units as units,
                directions_result.ref_m as ref_m,
                directions_result.ref_f as ref_f,
                users_doctorprofile.fio as fio,
                to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm
                from directions_issledovaniya
                INNER JOIN directions_result ON (directions_result.issledovaniye_id = directions_issledovaniya.id)
                LEFT JOIN directory_researches ON
                directions_issledovaniya.research_id=directory_researches.id
                LEFT JOIN directory_fractions ON
                directions_result.fraction_id=directory_fractions.id
                LEFT JOIN users_doctorprofile ON
                users_doctorprofile.id=directions_issledovaniya.doc_confirmation_id
                WHERE directions_issledovaniya.napravleniye_id in %(num_dirs)s
                ORDER BY directions_issledovaniya.napravleniye_id

        """,
            params={'num_dirs': list_dirs, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_paraclinic_results_by_direction(pk_dir):
    with connection.cursor() as cursor:
        cursor.execute(
            """
              SELECT 
                directions_issledovaniya.id,
                directions_issledovaniya.napravleniye_id,
                directions_issledovaniya.research_id,
                directions_paraclinicresult.value,
                directions_paraclinicresult.field_id,
                directory_paraclinicInputField.title,
                cda_paraclinicfields.title as cda_title_field,
                cda_groupfields.title as cda_title_group,
                directory_paraclinicinputgroups.title as group_title
                FROM directions_issledovaniya
                LEFT JOIN directions_paraclinicresult ON
                directions_issledovaniya.id=directions_paraclinicresult.issledovaniye_id
                LEFT JOIN directory_researches ON
                directions_issledovaniya.research_id=directory_researches.id
                LEFT JOIN directory_paraclinicinputfield ON
                directions_paraclinicresult.field_id=directory_paraclinicinputfield.id
                LEFT JOIN directory_paraclinicinputgroups ON
                directory_paraclinicInputField.group_id=directory_paraclinicinputgroups.id
                LEFT JOIN external_system_cdafields cda_paraclinicfields ON
                directory_paraclinicInputField.cda_option_id = cda_paraclinicfields.id
                LEFT JOIN external_system_cdafields cda_groupfields ON
                directory_paraclinicinputgroups.cda_option_id = cda_groupfields.id

              WHERE directions_issledovaniya.napravleniye_id = %(num_dir)s

        """,
            params={'num_dir': pk_dir},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_expertis_child_iss_by_issledovaniya(parent_iss_tuple):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                  directions_napravleniya.id, 
                  directions_napravleniya.parent_id, 
                  directions_issledovaniya.id as child_iss 
                FROM public.directions_napravleniya
                Left JOIN directions_issledovaniya ON
                  directions_issledovaniya.napravleniye_id = directions_napravleniya.id 
                where directions_napravleniya.parent_id in %(parent_iss_tuple)s
                order by directions_napravleniya.parent_id
        """,
            params={'parent_iss_tuple': parent_iss_tuple},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_expertis_results_by_issledovaniya(issledovaniye_tuple):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                    directions_paraclinicresult.issledovaniye_id,
                    directions_paraclinicresult.value,
                    directions_paraclinicresult.field_id,
                    directory_ParaclinicInputField.title
                FROM directions_paraclinicresult
                LEFT JOIN directory_paraclinicinputfield ON
                    directions_paraclinicresult.field_id=directory_paraclinicinputfield.id
                WHERE directions_paraclinicresult.issledovaniye_id in %(issledovaniye_tuple)s
                order by directions_paraclinicresult.issledovaniye_id

        """,
            params={'issledovaniye_tuple': issledovaniye_tuple},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def check_lab_instrumental_results_by_cards_and_period(cards_id, lab_days_ago_confirm, paraclinic_days_ago_confirm, lab_researches, paraclinic_researches):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                dn.client_id as client_id,
                directions_issledovaniya.research_id
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya dn on directions_issledovaniya.napravleniye_id = dn.id                
                WHERE 
                dn.client_id in %(cards_id)s and
                directions_issledovaniya.research_id in %(lab_researches)s and
                directions_issledovaniya.time_confirmation BEtWEEN (NOW() - interval '%(lab_days_ago_confirm)s day')  AND (NOW())
                OR 
                    directions_issledovaniya.research_id in %(paraclinic_researches)s and 
                    directions_issledovaniya.time_confirmation BEtWEEN (NOW() - interval '%(paraclinic_days_ago_confirm)s day')  AND (NOW()) 
                ORDER BY dn.client_id
        """,
            params={
                'cards_id': cards_id,
                'lab_days_ago_confirm': lab_days_ago_confirm,
                'paraclinic_days_ago_confirm': paraclinic_days_ago_confirm,
                'lab_researches': lab_researches,
                'paraclinic_researches': paraclinic_researches,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows