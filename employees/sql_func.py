from django.db import connection

from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def get_work_time_by_document(document_id: int):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT employees_employee.family, employees_employee.name, employees_employee.patronymic, employees_position.name as position_name, 
        employees_employeeworkinghoursschedule.id as worktime_id, start, "end", day, work_day_status, employee_position_id FROM employees_employeeWorkingHoursSchedule
          INNER JOIN employees_employeeposition ON employees_employeeWorkingHoursSchedule.employee_position_id = employees_employeeposition.id    
          INNER JOIN employees_employee ON employees_employeeposition.employee_id = employees_employee.id
          INNER JOIN employees_position ON employees_employeeposition.position_id = employees_position.id
        WHERE time_tracking_document_id = %(document_id)s
        ORDER BY employee_position_id
        """,
            params={'document_id': document_id},
        )
        row = namedtuplefetchall(cursor)
    return row


def get_employees_by_department(department_id: int):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT employees_employeeposition.id as employee_position_id, employees_position.name as position_name, family, 
        employees_employee.name, patronymic FROM employees_employeeposition
        INNER JOIN employees_position ON employees_employeeposition.position_id = employees_position.id
        INNER JOIN employees_employee ON employees_employeeposition.employee_id = employees_employee.id
        WHERE department_id = %(department_id)s and employees_employeeposition.is_active = true
        ORDER BY family
        """,
            params={'department_id': department_id},
        )
        row = namedtuplefetchall(cursor)
    return row
