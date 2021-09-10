from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def sql_load(
    hospital_pk=None,
    research_pk=None,
    type_period=None,
    quarter=None,
    year=None,
):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                directions_monitoringresult.id,
                directory_paraclinicinputgroups.title as group_title,
                directions_monitoringresult.group_id,
                directory_paraclinicinputfield.title as field_title,
                directions_monitoringresult.field_id,
                directions_monitoringresult.field_type,
                directions_monitoringresult.value_aggregate,
                directions_monitoringresult.value_text,
                directions_curatorgrade.grade_values as curator_grade,
                users_doctorprofile.fio as curator_fio
            FROM directions_monitoringresult 
            LEFT JOIN directory_paraclinicinputgroups
            ON directory_paraclinicinputgroups.id = directions_monitoringresult.group_id
            LEFT JOIN directory_paraclinicinputfield
            ON directory_paraclinicinputfield.id = directions_monitoringresult.field_id
            LEFT JOIN directions_curatorgrade
            ON directions_curatorgrade.monitoring_field_id = directions_monitoringresult.id
            LEFT JOIN users_doctorprofile
            ON users_doctorprofile.id = directions_curatorgrade.curator_id
            WHERE            
                directions_monitoringresult.period_param_quarter = %(quarter)s AND
                directions_monitoringresult.hospital_id = %(hospital_pk)s AND
                array_position(%(research_pk)s, directions_monitoringresult.research_id) IS NOT NULL AND
                directions_monitoringresult.period_param_year = %(year)s 
            ORDER BY group_order, field_order
            """,
            params={
                'tz': TIME_ZONE,
                'hospital_pk': hospital_pk,
                'research_pk': research_pk,
                'type_period': type_period,
                'quarter': quarter,
                'year': year,
            }
        )
        rows = namedtuplefetchall(cursor)
    return rows
