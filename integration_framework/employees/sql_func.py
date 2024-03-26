from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def get_cash_resister_by_person_period(date_start, date_end):
    with connection.cursor() as cursor:
        cursor.execute(
            """
             SELECT
             employee_position_id,
             accounting_day,
             to_char(accounting_day AT TIME ZONE %(tz)s, 'YYYY-MM-DD') AS char_day,
             ed.name,
             received_cash,
             received_terminal,
             return_cash,
             return_terminal,
             ee.family,
             ee.name,
             ee.patronymic
            FROM employees_cashregister
            LEFT JOIN employees_department ed
            ON ed.id=employees_cashregister.department_id
            LEFT JOIN employees_employeeposition ep
            ON ep.id = employees_cashregister.employee_position_id
            LEFT JOIN employees_employee ee
            ON ep.employee_id = ee.id
            WHERE accounting_day AT TIME ZONE %(tz)s BETWEEN %(date_start)s and %(date_end)s
            ORDER BY accounting_day
                  """,
            params={"date_start": date_start, "date_end": date_end, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_cash_resister_by_depatment_period(date_start, date_end):
    with connection.cursor() as cursor:
        cursor.execute(
            """
             SELECT
                  department_id,
                  ed.name as depart_name,
                  to_char(accounting_day, 'DD.MM.YYYY') AS char_day,
                  SUM(received_cash) as received_cash,
                  SUM(received_terminal) as received_terminal,
                  SUM(return_cash) as return_cash,
                  SUM(return_terminal) as return_terminal
            FROM employees_cashregister
            LEFT JOIN employees_department ed ON
            ed.id=employees_cashregister.department_id    
            WHERE accounting_day AT TIME ZONE %(tz)s BETWEEN %(date_start)s and %(date_end)s
            GROUP BY department_id, ed.name, accounting_day
            ORDER BY department_id, accounting_day DESC
                  """,
            params={"date_start": date_start, "date_end": date_end, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_total_cash_register_by_day(date_start, date_end):
    with connection.cursor() as cursor:
        cursor.execute(
            """
             SELECT
                  to_char(accounting_day, 'DD.MM.YYYY') AS char_day,
                  SUM(received_cash) as received_cash,
                  SUM(received_terminal) as received_terminal,
                  SUM(return_cash) as return_cash,
                  SUM(return_terminal) as return_terminal
            FROM employees_cashregister
            WHERE accounting_day AT TIME ZONE %(tz)s BETWEEN %(date_start)s and %(date_end)s
            GROUP BY accounting_day
                  """,
            params={"date_start": date_start, "date_end": date_end, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows
