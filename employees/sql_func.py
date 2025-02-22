from django.db import connection

from utils.db import namedtuplefetchall


def get_work_time_by_document(document_id: int):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT employees_employee.family, employees_employee.name, employees_employee.patronymic, employees_position.name as position_name, 
        employees_employeeworkinghoursschedule.id as worktime_id, start, "end", day, work_day_status_id, employee_position_id FROM employees_employeeWorkingHoursSchedule
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


def get_employee_position(org_id: int, department_ids: tuple = None, position_ids: tuple = None, employment_form_ids: tuple = None):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT 
        employees_typeworktimeemployee.title as employment_form,
        employees_employee.snils,
        employees_employeeposition.tabel_number,
        employees_employee.family as employee_family,
        employees_employee.name as employee_name,
        employees_employee.patronymic as employee_patronymic,
        employees_department.name as department_title,
        employees_position.name as position_title,
        employees_employeeposition.rate,
        employees_employeeposition.date_employment,
        employees_employeeposition.date_dismissal
        
        FROM employees_employeeposition
        INNER JOIN employees_employee ON employees_employeeposition.employee_id = employees_employee.id
        INNER JOIN employees_position ON employees_employeeposition.position_id = employees_position.id
        INNER JOIN employees_department ON employees_employeeposition.department_id = employees_department.id
        LEFT JOIN employees_typeworktimeemployee on employees_employeeposition.type_work_time_id = employees_typeworktimeemployee.id
        
        WHERE 
        employees_employee.hospital_id = %(org_id)s
        AND 
        CASE
        WHEN %(department_ids)s IS NOT NULL THEN
          employees_employeeposition.department_id IN %(department_ids)s
        WHEN %(position_ids)s IS NOT NULL THEN
          employees_employeeposition.position_id IN %(position_ids)s
        WHEN %(employment_form_ids)s IS NOT NULL THEN
          employees_employeeposition.type_work_time_id IN %(employment_form_ids)s
        END

        """,
            params={'org_id': org_id, "department_ids": department_ids, "position_ids": position_ids, "employment_form_ids": employment_form_ids},
        )
        row = namedtuplefetchall(cursor)
    return row
