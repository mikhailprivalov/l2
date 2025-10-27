from django.core.management.base import BaseCommand

from employees.models import EmployeePosition
from hospitals.models import Hospitals
from laboratory.settings import WORK_DAYS_PER_WEEK_DEFAULT


class Command(BaseCommand):
    """
    Добавление кол-ва рабочих дней в неделю в трудовые договора для организации по умолчанию
    """

    def handle(self, *args, **kwargs):
        self.stdout.write("Добавление началось, ожидайте...")
        default_hospital = Hospitals.get_default_hospital()
        employee_positions = EmployeePosition.all_by_organization(default_hospital.id)
        count_employee_position_change = len(employee_positions)
        for employee_position in employee_positions:
            employee_position.work_days_per_week = WORK_DAYS_PER_WEEK_DEFAULT
            employee_position.save()
        self.stdout.write(f"Добавление закончилось, отредактировано {count_employee_position_change} трудовых договоров")
