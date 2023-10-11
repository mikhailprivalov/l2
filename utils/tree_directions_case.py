from django.db import connection

from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def root_direction(napravleniye):
    """
    парам: napravleniye

    Вернуть корневой узел среди Направлений:
    id-направления, дата создания, id-услуг(и) относящейся к данному направлению, уровень поиска. 1(корень)
    в SQL:
    nn - directions_napravleniya
    ii - directions_issledovaniya
    """

    with connection.cursor() as cursor:
        cursor.execute(
            """WITH RECURSIVE r AS (
               SELECT nn.id, 
               to_char(nn.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_create,
               to_char(nn.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI:SS') as time_create,
               nn.parent_case_id, 
               ii.napravleniye_id,
               ii.id, 1 AS level
               FROM directions_issledovaniya ii 
               LEFT JOIN directions_napravleniya nn 
               ON ii.napravleniye_id=nn.id
                   WHERE nn.id = %(num_direction)s
               
               UNION ALL
              
               SELECT n.id, 
                      to_char(n.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_create,
                      to_char(n.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI:SS') as time_create,
                      n.parent_case_id,
                      i.napravleniye_id,
                      i.id, r.level + 1 AS level
               FROM directions_issledovaniya i 
               LEFT JOIN directions_napravleniya n 
               ON i.napravleniye_id=n.id
               JOIN r
               ON r.parent_case_id = i.id
            )
            
            SELECT * FROM r;""",
            params={'num_direction': napravleniye, 'tz': TIME_ZONE},
        )

        row = cursor.fetchall()
    return row


def tree_direction(iss):
    """
    парам: услуга

    Вернуть стуркутру Направлений:
    id-направления, дата создания, id-услуг(и) относящейся к данному направлению, уровень поиска.
    в SQL:
    nn - directions_napravleniya
    ii - directions_issledovaniya
    """

    with connection.cursor() as cursor:
        cursor.execute(
            """WITH RECURSIVE r AS (
            SELECT nn.id, 
            to_char(nn.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_create,
            to_char(nn.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI') as time_create,
            nn.parent_case_id, 
            ii.napravleniye_id,
            ii.id as iss, 
            to_char(ii.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm, 
            to_char(ii.time_confirmation AT TIME ZONE %(tz)s, 'HH24:MI') as time_confirm, 
            ii.research_id, ddrr.title,
            ii.diagnos, 1 AS level
            FROM directions_issledovaniya ii 
            LEFT JOIN directions_napravleniya nn 
            ON ii.napravleniye_id=nn.id
            LEFT JOIN directory_researches ddrr
            ON ii.research_id = ddrr.id
            
            WHERE ii.id = %(num_issledovaniye)s
            
            UNION ALL
            
            SELECT n.id, 
                  to_char(n.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_create,
                  to_char(n.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI') as time_create,
                  n.parent_case_id,
                  i.napravleniye_id,
                  i.id, 
                  to_char(i.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm, 
                  to_char(i.time_confirmation AT TIME ZONE %(tz)s, 'HH24:MI') as time_confirm,
                  i.research_id, dr.title,
                  i.diagnos, 
                  r.level + 1 AS level
            FROM directions_issledovaniya i 
            LEFT JOIN directions_napravleniya n 
            ON i.napravleniye_id=n.id
            LEFT JOIN directory_researches dr
            ON i.research_id = dr.id
            JOIN r
            ON r.iss = n.parent_case_id
            )
            
            SELECT * FROM r;""",
            params={'num_issledovaniye': iss, 'tz': TIME_ZONE},
        )

        row = cursor.fetchall()
    return row


def hosp_tree_direction(iss):
    """
    парам: услуга

    Вернуть стуркутру Направлений:
    id-направления, дата создания, id-услуг(и) относящейся к данному направлению, уровень поиска.
    в SQL:
    nn - directions_napravleniya
    ii - directions_issledovaniya
    """

    with connection.cursor() as cursor:
        cursor.execute(
            """WITH RECURSIVE r AS (
            SELECT nn.id, 
            to_char(nn.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_create,
            to_char(nn.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI') as time_create,
            nn.parent_case_id, 
            ii.napravleniye_id,
            ii.id as iss, 
            to_char(ii.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm, 
            to_char(ii.time_confirmation AT TIME ZONE %(tz)s, 'HH24:MI') as time_confirm, 
            ii.research_id, 
            ddrr.title,
            ii.diagnos, 1 AS level, 
            ddrr.short_title,
            ddrr.is_case,
            nn.cancel
            FROM directions_issledovaniya ii 
            LEFT JOIN directions_napravleniya nn 
            ON ii.napravleniye_id=nn.id
            LEFT JOIN directory_researches ddrr
            ON ii.research_id = ddrr.id

            WHERE ii.id = %(num_issledovaniye)s

            UNION ALL

            SELECT n.id, 
                  to_char(n.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_create,
                  to_char(n.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI') as time_create,
                  n.parent_case_id,
                  i.napravleniye_id,
                  i.id, 
                  to_char(i.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm, 
                  to_char(i.time_confirmation AT TIME ZONE %(tz)s, 'HH24:MI') as time_confirm,
                  i.research_id, 
                  dr.title,
                  i.diagnos, 
                  r.level + 1 AS level, 
                  dr.short_title,
                  dr.is_case,
                  n.cancel
            FROM directions_issledovaniya i 
            LEFT JOIN directions_napravleniya n 
            ON i.napravleniye_id=n.id
            LEFT JOIN directory_researches dr
            ON i.research_id = dr.id
            JOIN r
            ON r.iss = n.parent_case_id
            )

            SELECT * FROM r WHERE r.is_case = TRUE;""",
            params={'num_issledovaniye': iss, 'tz': TIME_ZONE},
        )

        row = cursor.fetchall()
    return row


def hospital_get_direction(iss, main_research, hosp_site_type, hosp_is_paraclinic, hosp_is_doc_refferal, hosp_is_lab, hosp_is_hosp, hosp_level, hosp_is_all, hosp_morfology):
    """
    парам: услуга
    Вернуть стуркутру в след порядке:
    num_dir, date_creat, time_create, parent_iss, num_dir,
    issled_id, date_confirm, time_confirm, id_research, title_research,
    diagnos, Level-подчинения, id_research, id_podrazde, is_paraclinic,
    is_doc, is_stom, is_case, is_micrbiology, title_podr,
    p_type_podr, site_type_hospital, slave_research_id
    в SQL:
    nn - directions_napravleniya
    ii - directions_issledovaniya
    """

    with connection.cursor() as cursor:
        cursor.execute(
            """WITH RECURSIVE r AS (
            SELECT nn.id,
            to_char(nn.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_create,
            to_char(nn.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI') as time_create,
            nn.parent_case_id, nn.cancel,
            ii.napravleniye_id,
            ii.id as iss, 
            to_char(ii.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm, 
            to_char(ii.time_confirmation AT TIME ZONE %(tz)s, 'HH24:MI') as time_confirm, 
            ii.research_id, ddrr.title, ddrr.short_title,
            ii.diagnos, 1 AS level
            FROM directions_issledovaniya ii 
            LEFT JOIN directions_napravleniya nn 
            ON ii.napravleniye_id=nn.id
            LEFT JOIN directory_researches ddrr
            ON ii.research_id = ddrr.id
            WHERE ii.id = %(num_issledovaniye)s
            UNION ALL
            SELECT n.id, 
                  to_char(n.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_create,
                  to_char(n.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI') as time_create,
                  n.parent_case_id, n.cancel,
                  i.napravleniye_id,
                  i.id, 
                  to_char(i.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm, 
                  to_char(i.time_confirmation AT TIME ZONE %(tz)s, 'HH24:MI') as time_confirm,
                  i.research_id, dr.title, dr.short_title,
                  i.diagnos, 
                  r.level + 1 AS level
            FROM directions_issledovaniya i 
            LEFT JOIN directions_napravleniya n 
            ON i.napravleniye_id=n.id
            LEFT JOIN directory_researches dr
            ON i.research_id = dr.id
            JOIN r
            ON r.iss = n.parent_case_id
            ),
            
            t_podrazdeleniye AS (SELECT podrazdeleniya_podrazdeleniya.id, title, p_type FROM podrazdeleniya_podrazdeleniya),
            
            t_research AS (SELECT directory_researches.id as research_iddir, podrazdeleniye_id, is_paraclinic, is_doc_refferal, 
            is_stom, is_case, is_microbiology, is_slave_hospital, is_citology, is_gistology, t_podrazdeleniye.title as podr_title, 
            t_podrazdeleniye.p_type FROM directory_researches
                LEFT JOIN t_podrazdeleniye ON t_podrazdeleniye.id = directory_researches.podrazdeleniye_id),

            t_hospital_service AS (SELECT site_type, slave_research_id FROM directory_hospitalservice
            WHERE 
              CASE 
               WHEN %(hosp_level)s > -1 THEN 
                    EXISTS (SELECT id FROM r)
               WHEN %(hosp_level)s = -1 THEN 
                  EXISTS (SELECT id FROM r)
              END),
            
            t_all AS (SELECT * FROM r
            LEFT JOIN t_research ON r.research_id = t_research.research_iddir
            LEFT JOIN t_hospital_service ON r.research_id = t_hospital_service.slave_research_id
            WHERE 
            CASE when %(hosp_site_type)s > -1 THEN 
            site_type = %(hosp_site_type)s
            when %(hosp_is_paraclinic)s = TRUE THEN
            is_paraclinic = true and site_type is NULL
            when %(hosp_is_hosp)s = TRUE THEN
            is_case = true and site_type is NULL
            when %(hosp_is_doc_refferal)s = TRUE THEN
            is_doc_refferal = true and site_type is NULL
            when %(hosp_morfology)s = TRUE THEN
            (is_microbiology = true or is_citology = true or is_gistology = true) and site_type is NULL
            when %(hosp_is_lab)s = TRUE THEN
            is_paraclinic = FALSE and is_doc_refferal = FALSE and is_stom = FALSE and is_case = FALSE and is_microbiology = FALSE 
                and is_citology = FALSE and is_gistology = FALSE and site_type is NULL AND is_slave_hospital = FALSE
            when %(hosp_site_type)s = -1 and %(hosp_is_all)s = TRUE THEN
                EXISTS (SELECT id FROM r)
            END       

            ORDER BY napravleniye_id, p_type, site_type)

            SELECT DISTINCT "id", date_create, time_create, parent_case_id, napravleniye_id, iss, date_confirm, time_confirm, research_id, title,
            diagnos, "level", research_iddir, podrazdeleniye_id, is_paraclinic, is_doc_refferal, is_stom, is_case, 
            is_microbiology, podr_title, p_type, site_type, slave_research_id, short_title, is_slave_hospital, cancel, is_citology, is_gistology FROM t_all WHERE 
                CASE 
                WHEN %(hosp_level)s > -1 THEN 
                    level = %(hosp_level)s
                WHEN %(hosp_level)s = -1 THEN 
                EXISTS (SELECT id FROM r)
                END
            ORDER BY napravleniye_id
           ;""",
            params={
                'num_issledovaniye': iss,
                'main_research': main_research,
                'hosp_site_type': hosp_site_type,
                'hosp_is_paraclinic': hosp_is_paraclinic,
                'hosp_is_doc_refferal': hosp_is_doc_refferal,
                'hosp_is_lab': hosp_is_lab,
                'hosp_is_hosp': hosp_is_hosp,
                'hosp_level': hosp_level,
                'hosp_is_all': hosp_is_all,
                'hosp_morfology': hosp_morfology,
                'tz': TIME_ZONE,
            },
        )
        row = cursor.fetchall()
    return row


def get_research_by_dir(numdir):
    """Выход стр-ра:
    issledovaniya.id - для последующего поиска подчинений по исследованию
    directions_issledovaniya.research_id - является main_research
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT directions_issledovaniya.id, directions_issledovaniya.research_id 
            FROM directions_issledovaniya where napravleniye_id = %(num_dir)s
            """,
            params={'num_dir': numdir},
        )

        row = cursor.fetchall()
    return row


def expertise_tree_direction(iss):
    """
    парам: услуга

    Вернуть стуркутру Направлений:
    id-направления, дата создания, id-услуг(и) относящейся к данному направлению, уровень поиска.
    в SQL:
    nn - directions_napravleniya
    ii - directions_issledovaniya
    """

    with connection.cursor() as cursor:
        cursor.execute(
            """WITH RECURSIVE r AS (
            SELECT nn.id, 
            to_char(nn.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_create,
            to_char(nn.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI') as time_create,
            nn.parent_case_id, 
            ii.napravleniye_id,
            ii.id as iss, 
            to_char(ii.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm, 
            to_char(ii.time_confirmation AT TIME ZONE %(tz)s, 'HH24:MI') as time_confirm, 
            ii.research_id, 
            ddrr.title,
            ii.diagnos, 
            1 AS level,
            ddrr.is_expertise
            FROM directions_issledovaniya ii 
            LEFT JOIN directions_napravleniya nn
            ON ii.napravleniye_id=nn.id
            LEFT JOIN directory_researches ddrr
            ON ii.research_id = ddrr.id

            WHERE ii.id = %(num_issledovaniye)s

            UNION ALL

            SELECT n.id, 
                  to_char(n.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_create,
                  to_char(n.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI') as time_create,
                  n.parent_case_id,
                  i.napravleniye_id,
                  i.id, 
                  to_char(i.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm, 
                  to_char(i.time_confirmation AT TIME ZONE %(tz)s, 'HH24:MI') as time_confirm,
                  i.research_id, 
                  dr.title,
                  i.diagnos, 
                  r.level + 1 AS level,
                  dr.is_expertise
            FROM directions_issledovaniya i 
            LEFT JOIN directions_napravleniya n 
            ON i.napravleniye_id=n.id
            LEFT JOIN directory_researches dr
            ON i.research_id = dr.id
            JOIN r
            ON r.iss = n.parent_case_id
            )

            SELECT * FROM r;""",
            params={'num_issledovaniye': iss, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows
