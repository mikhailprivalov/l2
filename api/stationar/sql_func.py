from django.db import connection

from laboratory.settings import TIME_ZONE


def get_research(title_podr, vertical_result_display):
    """
    Возврат: id услуги, title-услуги

    """

    with connection.cursor() as cursor:
        cursor.execute("""WITH
        t_podr AS (
            SELECT id as podr_id, title as podr_title FROM public.podrazdeleniya_podrazdeleniya),

        t_research AS (
            SELECT id as research_id, title as research_title, vertical_result_display, podrazdeleniye_id 
            FROM public.directory_researches)

        SELECT research_id, research_title FROM t_research
        LEFT JOIN t_podr
        ON t_research.podrazdeleniye_id=t_podr.podr_id
        WHERE podr_title = %(title_podr)s and vertical_result_display = %(vertical)s
        ORDER BY research_id
        """, params={'title_podr': title_podr, 'vertical': vertical_result_display})

        row = cursor.fetchall()
    return row


def get_iss(list_research_id, list_dirs):
    """
    Возврат: id-iss
    добавить:
    """
    with connection.cursor() as cursor:
        cursor.execute("""
        SELECT id, research_id FROM public.directions_issledovaniya
        WHERE napravleniye_id = ANY(ARRAY[%(num_dirs)s]) AND research_id = ANY(ARRAY[%(id_researches)s]) 
        AND time_confirmation IS NOT NULL
        """, params={'id_researches': list_research_id, 'num_dirs': list_dirs})
        row = cursor.fetchall()
    return row


def get_distinct_research(list_research_id, list_dirs, is_text_research=False):
    """
    Возврат: уникальных research
    добавить:
    """
    with connection.cursor() as cursor:
        cursor.execute("""WITH
        t_iss AS (SELECT id, research_id FROM public.directions_issledovaniya
        WHERE CASE 
        WHEN  %(is_text_research)s = TRUE THEN 
          napravleniye_id = ANY(ARRAY[%(num_dirs)s]) AND time_confirmation IS NOT NULL         
        WHEN  %(is_text_research)s = FALSE THEN
          napravleniye_id = ANY(ARRAY[%(num_dirs)s]) AND research_id = ANY(ARRAY[%(id_researches)s]) AND time_confirmation IS NOT NULL
        END)

        SELECT DISTINCT ON (research_id) research_id FROM t_iss

        """, params={'id_researches': list_research_id, 'num_dirs': list_dirs, 'is_text_research': is_text_research})
        row = cursor.fetchall()
    return row


def get_distinct_fraction(list_iss):
    """
    возвращает уникальные фракци(id, title, units), которые присутствуют во всех исследованиях
    """
    with connection.cursor() as cursor:
        cursor.execute("""WITH
        t_fraction AS (SELECT id as id_frac, title as title_frac FROM public.directory_fractions ORDER BY id)

        SELECT DISTINCT ON (fraction_id) fraction_id, title_frac, units FROM directions_result
        LEFT JOIN t_fraction ON directions_result.fraction_id = t_fraction.id_frac
        WHERE issledovaniye_id = ANY(ARRAY[%(id_iss)s])
        ORDER by fraction_id
        """, params={'id_iss': list_iss})
        row = cursor.fetchall()
    return row


def get_result_fraction(list_iss):
    """
    возвращает результат: дата, фракция, значение(value)
    """
    with connection.cursor() as cursor:
        cursor.execute("""WITH
        t_fraction AS (SELECT id as id_frac, title as title_frac FROM public.directory_fractions ORDER BY id),
        
        t_iss AS (SELECT id as iss_id, napravleniye_id, to_char(time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YY') as date_confirm
        FROM public.directions_issledovaniya 
        WHERE id = ANY(ARRAY[%(id_iss)s]) AND time_confirmation IS NOT NULL)

        SELECT fraction_id, issledovaniye_id, title_frac, value, date_confirm, napravleniye_id FROM directions_result
        LEFT JOIN t_fraction ON directions_result.fraction_id = t_fraction.id_frac
        LEFT JOIN t_iss ON directions_result.issledovaniye_id = t_iss.iss_id
        WHERE issledovaniye_id = ANY(ARRAY[%(id_iss)s])
        ORDER by napravleniye_id, date_confirm
        """, params={'id_iss': list_iss, 'tz': TIME_ZONE})
        row = cursor.fetchall()
    return row


def get_result_text_research(research_pk, listdirs):
    with connection.cursor() as cursor:
        cursor.execute("""
           WITH
            t_research AS (SELECT id as research_id, title as research_title FROM directory_researches
                          WHERE id = %(id_research)s),
                                       
            t_groups AS (SELECT id as group_id, title as group_title, "order" as group_order
                         FROM public.directory_paraclinicinputgroups
                         WHERE research_id = %(id_research)s),
            
            t_fields AS (SELECT id as field_id, title, "order" as field_order, 
                         directory_paraclinicinputfield.group_id, group_title, group_order
                         FROM public.directory_paraclinicinputfield
            LEFT JOIN t_groups on directory_paraclinicinputfield.group_id = t_groups.group_id
            WHERE (directory_paraclinicinputfield.group_id in (SELECT group_id from t_groups) and for_extract_card=true) or
                    (directory_paraclinicinputfield.group_id in (SELECT group_id from t_groups) and title ILIKE 'Заключение')),
            
            t_iss AS (SELECT id as iss_id, time_confirmation,
                      to_char(time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YY') as date_confirm,
                      napravleniye_id, t_research.research_title FROM directions_issledovaniya
                LEFT JOIN t_research on t_research.research_id = directions_issledovaniya.research_id
                WHERE directions_issledovaniya.research_id=%(id_research)s and napravleniye_id = ANY(ARRAY[%(id_dirs)s]))
                     
            SELECT research_title, date_confirm, napravleniye_id, group_title, title, "value" FROM directions_paraclinicresult
            LEFT JOIN t_iss on directions_paraclinicresult.issledovaniye_id = t_iss.iss_id
            LEFT JOIN t_fields on directions_paraclinicresult.field_id = t_fields.field_id
            WHERE issledovaniye_id in (SELECT iss_id from t_iss) and 
            directions_paraclinicresult.field_id in (SELECT field_id from t_fields)
            order by time_confirmation, group_order, field_order

         """, params={'id_research': research_pk, 'id_dirs': listdirs, 'tz': TIME_ZONE})
        row = cursor.fetchall()
    return row


def get_result_value_iss(iss_pk, research_pk, titles_field):
    with connection.cursor() as cursor:
        cursor.execute("""
        WITH
           t_field AS (SELECT "id", title FROM directory_paraclinicinputfield
           WHERE group_id in (SELECT "id" FROM directory_paraclinicinputgroups WHERE research_id=%(id_research)s)
             AND title = ANY(ARRAY[%(titles_field)s]))

            SELECT field_id, issledovaniye_id, "value", title FROM public.directions_paraclinicresult
            LEFT JOIN t_field ON directions_paraclinicresult.field_id = t_field.id
            where field_id in (SELECT "id" FROM t_field)  and issledovaniye_id = %(id_iss)s


         """, params={'id_iss': iss_pk, 'id_research': research_pk, 'titles_field': titles_field})
        row = cursor.fetchall()
    return row
