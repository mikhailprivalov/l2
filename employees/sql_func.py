from django.db import connection

from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def get_work_time_by_document(document_id: int):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT employees_employee.family, employees_employee.name, employees_employee.patronymic, employees_position.name as position_name, employees_employeeworktime.id as worktime_id, 
        start, "end", employee_position_id FROM employees_employeeworktime
         INNER JOIN employees_employeeposition ON employees_employeeworktime.employee_position_id = employees_employeeposition.id    
         INNER JOIN employees_employee ON employees_employeeposition.employee_id = employees_employee.id
         INNER JOIN employees_position ON employees_employeeposition.position_id = employees_position.id
         WHERE document_id = %(document_id)s
         ORDER BY employee_position_id
        """,
            params={'document_id': document_id},
        )
        row = namedtuplefetchall(cursor)
    return row
