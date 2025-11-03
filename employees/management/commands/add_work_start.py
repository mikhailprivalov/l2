from django.core.management.base import BaseCommand

from employees.models import EmployeePosition, Department, default_work_start
from hospitals.models import Hospitals


class Command(BaseCommand):
    """
    Добавление/изменение начала рабочего дня в подразделениях и трудовых договора (EmployeePosition, Department)
    """

    def add_arguments(self, parser):
        parser.add_argument('mode', type=int)

    def handle(self, *args, **kwargs):
        mode = kwargs["mode"]
        self.stdout.write("Добавление началось, ожидайте...")
        default_hospital = Hospitals.get_default_hospital()
        if mode == 1:
            departments = Department.get_active_departments(default_hospital.id)
            count_departments_change = len(departments)
            for department in departments:
                department.work_start = default_work_start()
                department.save()
            self.stdout.write(f"Добавление закончилось, отредактировано {count_departments_change} подразделений")
        else:
            employee_positions = EmployeePosition.all_by_organization(default_hospital.id)
            count_employee_position_change = len(employee_positions)
            for employee_position in employee_positions:
                employee_position.work_start = default_work_start()
                employee_position.save()
            self.stdout.write(f"Добавление закончилось, отредактировано {count_employee_position_change} трудовых договоров")
