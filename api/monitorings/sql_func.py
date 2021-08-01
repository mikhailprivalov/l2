from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def monitoring_sql_by_all_hospital(
    monitoring_research=None,
    type_period=None,
    period_param_hour=None,
    period_param_day=None,
    period_param_month=None,
    period_param_quarter=None,
    period_param_halfyear=None,
    period_param_year=None,
    period_param_week_date_start=None,
    period_param_week_date_end=None,
):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                hospitals_hospitals.short_title,
                directions_monitoringresult.hospital_id,
                directions_monitoringresult.napravleniye_id,
                directions_monitoringresult.issledovaniye_id,
                to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY HH24:MI') as confirm,
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
                directions_monitoringresult.research_id=%(monitoring_research)s AND
                directions_monitoringresult.period_param_day=%(period_param_day)s  AND
                directions_monitoringresult.period_param_month=%(period_param_month)s AND
                directions_monitoringresult.period_param_year=%(period_param_year)s AND
                directions_issledovaniya.time_confirmation is NOT NULL
            WHEN %(type_period)s = 'PERIOD_WEEK' THEN 
                directions_monitoringresult.type_period = 'PERIOD_WEEK' AND
                directions_monitoringresult.research_id=%(monitoring_research)s AND
                directions_monitoringresult.period_param_year=%(period_param_year)s AND
                directions_monitoringresult.period_param_week_date_start=%(period_param_week_date_start)s AND
                directions_monitoringresult.period_param_week_date_end=%(period_param_week_date_end)s AND
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
                'period_param_week_date_start': period_param_week_date_start,
                'period_param_week_date_end': period_param_week_date_end,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def dashboard_sql_by_day(charts_id=None, period_param_day=None, period_param_month=None, period_param_year=None):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            DISTINCT ON (
                directions_dashboardcharts.id,
                directions_monitoringresult.hospital_id,
                directions_dashboardchartfields.order,
                directions_dashboardchartfields.field_id,
                directions_monitoringresult.period_param_day,
                directions_monitoringresult.period_param_month,
                directions_monitoringresult.period_param_year
            )
            
                directions_dashboardcharts.id as chart_id,
                directions_dashboardcharts.order as chart_order,
                directions_dashboardcharts.title as chart_title,
                directions_dashboardcharts.type as chart_type,
                directions_monitoringresult.hospital_id,
                hospitals_hospitals.short_title as hosp_short_title,
                hospitals_hospitals.title as hosp_title,
                directions_dashboardchartfields.order as order_field, 
                directions_dashboardchartfields.field_id,
                title_for_field,
                directory_paraclinicinputfield.title as field_title,
                directions_monitoringresult.value_aggregate,
                directions_monitoringresult.period_param_hour,
                directions_monitoringresult.period_param_day,
                directions_monitoringresult.period_param_month,
                directions_monitoringresult.period_param_year
            
            FROM public.directions_dashboardchartfields
            LEFT JOIN directions_dashboardcharts
            ON directions_dashboardcharts.id = directions_dashboardchartfields.charts_id
            
            LEFT JOIN directory_paraclinicinputfield
            ON directory_paraclinicinputfield.id = directions_dashboardchartfields.field_id
            
            LEFT JOIN directions_monitoringresult
            ON directions_monitoringresult.field_id = directions_dashboardchartfields.field_id
            
            LEFT JOIN hospitals_hospitals
            ON hospitals_hospitals.id = directions_monitoringresult.hospital_id

            WHERE
                directions_dashboardcharts.id = ANY(ARRAY[%(charts_id)s]) AND 
                directions_monitoringresult.period_param_day = %(period_param_day)s AND
                directions_monitoringresult.period_param_month = %(period_param_month)s AND
                directions_monitoringresult.period_param_year = %(period_param_year)s
            ORDER BY 
                directions_dashboardcharts.id, 
                directions_monitoringresult.hospital_id,
                directions_dashboardchartfields.order,
                directions_dashboardchartfields.field_id,
                directions_monitoringresult.period_param_day,
                directions_monitoringresult.period_param_month,
                directions_monitoringresult.period_param_year,
                directions_monitoringresult.period_param_hour DESC                
            """,
            params={
                'tz': TIME_ZONE,
                'charts_id': charts_id,
                'period_param_day': period_param_day,
                'period_param_month': period_param_month,
                'period_param_year': period_param_year,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def dashboard_sql_by_day_filter_hosp(
    charts_id=None, period_param_day=None, period_param_month=None, period_param_year=None, param_day_end=None, param_month_end=None, param_year_end=None, filter_hospitals=None
):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT main_table.chart_id, main_table.chart_order, main_table.chart_title, main_table.chart_type, main_table.order_field, 
                main_table.field_id, main_table.title_for_field, sum(main_table.value_aggregate) as value_aggregate FROM
            (SELECT
            DISTINCT ON (
                directions_dashboardcharts.id,
                directions_monitoringresult.hospital_id,
                directions_dashboardchartfields.order,
                directions_dashboardchartfields.field_id,
                directions_monitoringresult.period_param_day,
                directions_monitoringresult.period_param_month,
                directions_monitoringresult.period_param_year
            )

                directions_dashboardcharts.id as chart_id,
                directions_dashboardcharts.order as chart_order,
                directions_dashboardcharts.title as chart_title,
                directions_dashboardcharts.type as chart_type,
                directions_monitoringresult.hospital_id,
                hospitals_hospitals.short_title as hosp_short_title,
                hospitals_hospitals.title as hosp_title,
                directions_dashboardchartfields.order as order_field, 
                directions_dashboardchartfields.field_id,
                title_for_field,
                directory_paraclinicinputfield.title as field_title,
                directions_monitoringresult.value_aggregate,
                directions_monitoringresult.period_param_hour,
                directions_monitoringresult.period_param_day,
                directions_monitoringresult.period_param_month,
                directions_monitoringresult.period_param_year

            FROM public.directions_dashboardchartfields
            LEFT JOIN directions_dashboardcharts
            ON directions_dashboardcharts.id = directions_dashboardchartfields.charts_id

            LEFT JOIN directory_paraclinicinputfield
            ON directory_paraclinicinputfield.id = directions_dashboardchartfields.field_id

            LEFT JOIN directions_monitoringresult
            ON directions_monitoringresult.field_id = directions_dashboardchartfields.field_id

            LEFT JOIN hospitals_hospitals
            ON hospitals_hospitals.id = directions_monitoringresult.hospital_id

            WHERE
                directions_dashboardcharts.id = ANY(ARRAY[%(charts_id)s]) AND 
                directions_monitoringresult.hospital_id = ANY(ARRAY[%(filter_hospitals)s]) AND  
                directions_monitoringresult.period_param_day >= %(period_param_day)s AND
                directions_monitoringresult.period_param_month >= %(period_param_month)s AND
                directions_monitoringresult.period_param_year >= %(period_param_year)s AND
                directions_monitoringresult.period_param_day <= %(param_day_end)s AND
                directions_monitoringresult.period_param_month <= %(param_month_end)s AND
                directions_monitoringresult.period_param_year <= %(param_year_end)s
            ORDER BY 
                directions_dashboardcharts.id, 
                directions_monitoringresult.hospital_id,
                directions_dashboardchartfields.order,
                directions_dashboardchartfields.field_id,
                directions_monitoringresult.period_param_day,
                directions_monitoringresult.period_param_month,
                directions_monitoringresult.period_param_year,
                directions_monitoringresult.period_param_hour DESC) main_table  
            GROUP BY main_table.chart_id, main_table.chart_order, main_table.chart_title, main_table.chart_type, 
            main_table.field_id,  main_table.order_field, main_table.title_for_field;               
            """,
            params={
                'tz': TIME_ZONE,
                'charts_id': charts_id,
                'filter_hospitals': filter_hospitals,
                'period_param_day': period_param_day,
                'period_param_month': period_param_month,
                'period_param_year': period_param_year,
                'param_day_end': param_day_end,
                'param_month_end': param_month_end,
                'param_year_end': param_year_end,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def sql_charts_sum_by_field_all_hospitals(
    charts_id=None, period_param_day=None, period_param_month=None, period_param_year=None, param_day_end=None, param_month_end=None, param_year_end=None
):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT main_table.chart_id, main_table.chart_order, main_table.chart_title, main_table.chart_type, main_table.order_field, 
                main_table.field_id, main_table.title_for_field, sum(main_table.value_aggregate) as value_aggregate FROM
            (SELECT
            DISTINCT ON (
                directions_dashboardcharts.id,
                directions_dashboardchartfields.order,
                directions_dashboardchartfields.field_id,
                directions_monitoringresult.period_param_day,
                directions_monitoringresult.period_param_month,
                directions_monitoringresult.period_param_year
            )

                directions_dashboardcharts.id as chart_id,
                directions_dashboardcharts.order as chart_order,
                directions_dashboardcharts.title as chart_title,
                directions_dashboardcharts.type as chart_type,
                directions_dashboardchartfields.order as order_field, 
                directions_dashboardchartfields.field_id as field_id,
                title_for_field,
                sum(directions_monitoringresult.value_aggregate) as value_aggregate,
                directions_monitoringresult.period_param_hour,
                directions_monitoringresult.period_param_day,
                directions_monitoringresult.period_param_month,
                directions_monitoringresult.period_param_year

            FROM public.directions_dashboardchartfields
            LEFT JOIN directions_dashboardcharts
            ON directions_dashboardcharts.id = directions_dashboardchartfields.charts_id

            LEFT JOIN directory_paraclinicinputfield
            ON directory_paraclinicinputfield.id = directions_dashboardchartfields.field_id

            LEFT JOIN directions_monitoringresult
            ON directions_monitoringresult.field_id = directions_dashboardchartfields.field_id

            LEFT JOIN hospitals_hospitals
            ON hospitals_hospitals.id = directions_monitoringresult.hospital_id

            WHERE 
                charts_id = ANY(ARRAY[%(charts_id)s]) AND
                directions_monitoringresult.period_param_day >= %(period_param_day)s AND
                directions_monitoringresult.period_param_month >= %(period_param_month)s AND
                directions_monitoringresult.period_param_year >= %(period_param_year)s AND
                directions_monitoringresult.period_param_day <= %(param_day_end)s AND
                directions_monitoringresult.period_param_month <= %(param_month_end)s AND
                directions_monitoringresult.period_param_year <= %(param_year_end)s
            GROUP BY
                directions_dashboardchartfields.field_id,
                directions_dashboardcharts.id,
                directions_dashboardchartfields.order,
                title_for_field,
                directions_monitoringresult.period_param_hour,
                directions_monitoringresult.period_param_day,
                directions_monitoringresult.period_param_month,
                directions_monitoringresult.period_param_year
            ORDER BY 
                directions_dashboardcharts.id, 
                directions_dashboardchartfields.order,
                directions_dashboardchartfields.field_id,
                directions_monitoringresult.period_param_day,
                directions_monitoringresult.period_param_month,
                directions_monitoringresult.period_param_year,
                directions_monitoringresult.period_param_hour DESC) main_table  
            GROUP BY main_table.chart_id, main_table.chart_order, main_table.chart_title, main_table.chart_type, 
            main_table.field_id,  main_table.order_field, main_table.title_for_field;          
            """,
            params={
                'tz': TIME_ZONE,
                'charts_id': charts_id,
                'period_param_day': period_param_day,
                'period_param_month': period_param_month,
                'period_param_year': period_param_year,
                'param_day_end': param_day_end,
                'param_month_end': param_month_end,
                'param_year_end': param_year_end,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def sql_charts_sum_by_field_filter_hospitals(charts_id=None, period_param_day=None, period_param_month=None, period_param_year=None, param_day_end=None, param_month_end=None, param_year_end=None, filter_hospitals=None):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            DISTINCT ON (
                directions_dashboardcharts.id,
                directions_dashboardchartfields.order,
                directions_dashboardchartfields.field_id,
                directions_monitoringresult.period_param_day,
                directions_monitoringresult.period_param_month,
                directions_monitoringresult.period_param_year
            )

                directions_dashboardcharts.id as chart_id,
                directions_dashboardcharts.order as chart_order,
                directions_dashboardcharts.title as chart_title,
                directions_dashboardcharts.type as chart_type,
                directions_dashboardchartfields.order as order_field, 
                directions_dashboardchartfields.field_id,
                title_for_field,
                sum(directions_monitoringresult.value_aggregate) as value_aggregate,
                directions_monitoringresult.period_param_hour,
                directions_monitoringresult.period_param_day,
                directions_monitoringresult.period_param_month,
                directions_monitoringresult.period_param_year

            FROM public.directions_dashboardchartfields
            LEFT JOIN directions_dashboardcharts
            ON directions_dashboardcharts.id = directions_dashboardchartfields.charts_id

            LEFT JOIN directory_paraclinicinputfield
            ON directory_paraclinicinputfield.id = directions_dashboardchartfields.field_id

            LEFT JOIN directions_monitoringresult
            ON directions_monitoringresult.field_id = directions_dashboardchartfields.field_id

            LEFT JOIN hospitals_hospitals
            ON hospitals_hospitals.id = directions_monitoringresult.hospital_id

            WHERE 
                charts_id = ANY(ARRAY[%(charts_id)s]) AND
                directions_monitoringresult.hospital_id = ANY(ARRAY[%(filter_hospitals)s]) AND
                directions_monitoringresult.period_param_day >= %(period_param_day)s AND
                directions_monitoringresult.period_param_month >= %(period_param_month)s AND
                directions_monitoringresult.period_param_year >= %(period_param_year)s AND
                directions_monitoringresult.period_param_day <= %(param_day_end)s AND
                directions_monitoringresult.period_param_month <= %(param_month_end)s AND
                directions_monitoringresult.period_param_year <= %(param_year_end)s
            GROUP BY
               directions_dashboardchartfields.field_id,
                directions_dashboardcharts.id,
                directions_dashboardchartfields.order,
                title_for_field,
                directions_monitoringresult.period_param_hour,
                directions_monitoringresult.period_param_day,
                directions_monitoringresult.period_param_month,
                directions_monitoringresult.period_param_year
            ORDER BY 
                directions_dashboardcharts.id, 
                directions_dashboardchartfields.order,
                directions_dashboardchartfields.field_id,
                directions_monitoringresult.period_param_day,
                directions_monitoringresult.period_param_month,
                directions_monitoringresult.period_param_year,
                directions_monitoringresult.period_param_hour DESC                
            """,
            params={
                'tz': TIME_ZONE,
                'charts_id': charts_id,
                'filter_hospitals': filter_hospitals,
                'period_param_day': period_param_day,
                'period_param_month': period_param_month,
                'period_param_year': period_param_year,
                'param_day_end': param_day_end,
                'param_month_end': param_month_end,
                'param_year_end': param_year_end
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows
