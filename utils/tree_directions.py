from django.db import connection
from laboratory.settings import TIME_ZONE


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
        cursor.execute("""WITH RECURSIVE r AS (
               SELECT nn.id, 
               to_char(nn.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_create,
               to_char(nn.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI:SS') as time_create,
               nn.parent_id, 
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
                      n.parent_id,
                      i.napravleniye_id,
                      i.id, r.level + 1 AS level
               FROM directions_issledovaniya i 
               LEFT JOIN directions_napravleniya n 
               ON i.napravleniye_id=n.id
               JOIN r
               ON r.parent_id = i.id
            )
            
            SELECT * FROM r;""",
                       params={'num_direction': napravleniye, 'tz': TIME_ZONE})

        row = cursor.fetchall()
    return row


def tree_direction(iss):
    """
    парам: услуга

    Вернуть стуркутру Направлений:
    id-направления, дата создания, id-услуг(и) относящейся к данному направлению, уровень поиска. 1(корень)
    в SQL:
    nn - directions_napravleniya
    ii - directions_issledovaniya
    """

    with connection.cursor() as cursor:
        cursor.execute("""WITH RECURSIVE r AS (
            SELECT nn.id, 
            to_char(nn.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_create,
            to_char(nn.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI') as time_create,
            nn.parent_id, 
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
                  n.parent_id,
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
            ON r.iss = n.parent_id
            )
            
            SELECT * FROM r;""",
                       params={'num_issledovaniye': iss, 'tz': TIME_ZONE})

        row = cursor.fetchall()
    return row


def hospital_get_direction(iss):
    """
    парам: услуга

    Вернуть стуркутру Направлений:
    id-направления, дата создания, id-услуг(и) относящейся к данному направлению, уровень поиска. 1(корень)
    в SQL:
    nn - directions_napravleniya
    ii - directions_issledovaniya
    """

    with connection.cursor() as cursor:
        cursor.execute("""WITH RECURSIVE r AS (
            SELECT nn.id, 
            to_char(nn.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_create,
            to_char(nn.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI') as time_create,
            nn.parent_id, 
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
                  n.parent_id,
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
            ON r.iss = n.parent_id
            ),
            t_podrazdeleniye AS (SELECT podrazdeleniya_podrazdeleniya.id, title FROM podrazdeleniya_podrazdeleniya),
            t_research AS (SELECT directory_researches.id as research_id, podrazdeleniye_id, is_paraclinic, is_doc_refferal, is_stom,
			   is_hospital, is_microbiology, t_podrazdeleniye.title FROM directory_researches
			  LEFT JOIN t_podrazdeleniye ON t_podrazdeleniye.id = directory_researches.podrazdeleniye_id)

            SELECT * FROM r
            LEFT JOIN t_research ON r.research_id = t_research.research_id;""",
                       params={'num_issledovaniye': iss, 'tz': TIME_ZONE})

        row = cursor.fetchall()
    return row


