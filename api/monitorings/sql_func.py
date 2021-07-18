from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def monitoring_sql_by_all_hospital(monitoring_research, type_period, period_param_hour, period_param_day, period_param_month, period_param_quarter,
                          period_param_halfyear, period_param_year, period_param_week_day_start, period_param_week_day_end):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                directions_monitoringresult.napravleniye_id,
                directions_monitoringresult.issledovaniye_id,
                directions_issledovaniya.time_confirmation,
                directions_monitoringresult.hospital_id,
                hospitals_hospitals.short_title,
                directions_monitoringresult.research_id,
                directions_monitoringresult.group_id,
                directory_paraclinicinputgroups.title as group_title,
                directions_monitoringresult.group_order,
                directions_monitoringresult.field_id,
                directory_paraclinicinputfield.title as field_title,
                directions_monitoringresult.field_order,
                directions_monitoringresult.field_type,
                directions_monitoringresult.value_aggregate,
                directions_monitoringresult.value_text,
                directions_monitoringresult.type_period,
                directions_monitoringresult.period_param_hour,
                directions_monitoringresult.period_param_day,
                directions_monitoringresult.period_param_week_description,
                directions_monitoringresult.period_param_week_date_start,
                directions_monitoringresult.period_param_week_date_end,
                directions_monitoringresult.period_param_month,
                directions_monitoringresult.period_param_quarter,
                directions_monitoringresult.period_param_halfyear,
                directions_monitoringresult.period_param_year
            FROM directions_monitoringresult
            LEFT JOIN directory_paraclinicinputgroups
            ON directory_paraclinicinputgroups.id = directions_monitoringresult.group_id
            LEFT JOIN directory_paraclinicinputfield
            ON directory_paraclinicinputfield.id = directions_monitoringresult.field_id
            LEFT JOIN hospitals_hospitals
            ON hospitals_hospitals.id = directions_monitoringresult.hospital_id
            LEFT JOIN directions_issledovaniya
            ON directions_issledovaniya.id = directions_monitoringresult.issledovaniye_id
            WHERE
            CASE 
            WHEN %(type_period)s = 'PERIOD_HOUR' THEN 
                directions_monitoringresult.type_period = 'PERIOD_HOUR' AND
                directions_monitoringresult.research_id=%(monitoring_research)s AND
                directions_monitoringresult.period_param_hour=%(period_param_hour)s  AND
                directions_monitoringresult.period_param_day=%(period_param_day)s  AND
                directions_monitoringresult.period_param_month=%(period_param_month)s AND
                directions_monitoringresult.period_param_year=%(period_param_year)s AND
                directions_issledovaniya.time_confirmation is NOT NULL
            WHEN %(type_period)s = 'PERIOD_DAY' THEN
                directions_monitoringresult.type_period = 'PERIOD_DAY' AND
                directions_monitoringresult.period_param_day=%(period_param_day)s  AND
                directions_monitoringresult.period_param_month=%(period_param_month)s AND
                directions_monitoringresult.period_param_year=%(period_param_year)s AND
                directions_issledovaniya.time_confirmation is NOT NULL
            WHEN %(type_period)s = 'PERIOD_WEEK' THEN 
                directions_monitoringresult.type_period = 'PERIOD_WEEK' AND
                directions_monitoringresult.period_param_year=%(period_param_year)s AND
                directions_monitoringresult.period_param_week_date_start=%(period_param_week_day_start)s AND
                directions_monitoringresult.period_param_week_date_end=%(period_param_week_day_end)s AND
                directions_issledovaniya.time_confirmation is NOT NULL
            WHEN %(type_period)s = 'PERIOD_MONTH' THEN 
                directions_monitoringresult.research_id=%(monitoring_research)s AND
                directions_monitoringresult.period_param_month=%(period_param_month)s AND
                directions_monitoringresult.period_param_year=%(period_param_year)s AND
                directions_issledovaniya.time_confirmation is NOT NULL
            WHEN %(type_period)s = 'PERIOD_QUARTER' THEN 
                directions_monitoringresult.research_id=%(monitoring_research)s AND
                directions_monitoringresult.period_param_quarter=%(period_param_quarter)s AND
                directions_monitoringresult.period_param_year=%(period_param_year)s AND
                directions_issledovaniya.time_confirmation is NOT NULL
            WHEN %(type_period)s = 'PERIOD_HALFYEAR' THEN 
                directions_monitoringresult.research_id=%(monitoring_research)s AND
                directions_monitoringresult.period_param_halfyear=%(period_param_halfyear)s AND
                directions_monitoringresult.period_param_year=%(period_param_year)s AND
                directions_issledovaniya.time_confirmation is NOT NULL
            WHEN %(type_period)s = 'PERIOD_YEAR' THEN 
                directions_monitoringresult.research_id=%(monitoring_research)s AND
                directions_monitoringresult.period_param_year=%(period_param_year)s AND
                directions_issledovaniya.time_confirmation is NOT NULL
            END 
                
            ORDER BY hospital_id, directions_monitoringresult.napravleniye_id, group_order, field_order
            """,
            params={
                'tz': TIME_ZONE,
                'monitoring_research': monitoring_research,
                'type_period': type_period,
                'period_param_hour': period_param_hour,
                'period_param_day': period_param_day,
                'period_param_month': period_param_month,
                'period_param_quarter': period_param_quarter,
                'period_param_halfyear': period_param_halfyear,
                'period_param_year': period_param_year,
                'period_param_week_day_start': period_param_week_day_start,
                'period_param_week_day_end': period_param_week_day_end
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows
