from django.db import connection
from laboratory.settings import TIME_ZONE


def direction_collect(d_s, type_integration, limit):
    """
    парам: d_s - date-start, researches - списко исследований которые требуются

    Вернуть:
    Направления, в к-рых все исследования подтверждены, и подтверждены после определенной даты

    в SQL:
    t_iss - это временная таблица запроса для направлений в к-рых есть подтвержденные исследований (Направления уникальны)
    t_iss_null - это временная таблица запроса направлений, у к-рых есть неподтвержденные исследования
    t_all - это готовая выборка направлений, где подтверждены ВСЕ исследования в определенном направлении
    SELECT research_id FROM integration_framework_integrationresearches WHERE
    """

    with connection.cursor() as cursor:
        cursor.execute("""WITH
        t_field AS ( SELECT research_id FROM integration_framework_integrationresearches WHERE 
            CASE 
            WHEN %(type_integration)s = '*' THEN 
                type_integration IS NOT NULL
            ELSE type_integration=%(type_integration)s
            END),
        t_iss AS 
            (SELECT distinct on (napravleniye_id) napravleniye_id, research_id, time_confirmation AT TIME ZONE %(tz)s AS time_confirmation,
             to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'YYYY-MM-DD HH24:MI:SS.US') AS t_confirm
             FROM public.directions_issledovaniya
                   WHERE time_confirmation > %(d_start)s AND (research_id IN (SELECT * FROM t_field))
            order by napravleniye_id),
        t_iss_null AS
            (SELECT distinct on (napravleniye_id) napravleniye_id as napr_null FROM public.directions_issledovaniya
                   WHERE time_confirmation is null 
            order by napravleniye_id),
        t_all AS 
            (SELECT * FROM t_iss LEFT JOIN t_iss_null ON t_iss.napravleniye_id = t_iss_null.napr_null)
            
            SELECT napravleniye_id, research_id, time_confirmation, t_confirm FROM t_all WHERE napr_null IS NULL
            ORDER BY time_confirmation LIMIT %(limit)s """,
                       params={'d_start': d_s, 'tz': TIME_ZONE, 'type_integration':type_integration, 'limit':limit})

        row = cursor.fetchall()
    return row