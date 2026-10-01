from django.core.management.base import BaseCommand

from employees.duplicate_cleanup import delete_same_employee_positions


class Command(BaseCommand):
    help = "Удаляет одинаковые EmployeePosition: подразделение, ФИО, название должности, ставка и активность. Табельный номер не учитывается."

    def add_arguments(self, parser):
        parser.add_argument(
            "--hospital",
            type=int,
            default=None,
            help="ID организации (Hospitals.pk). Без параметра — все организации.",
        )

    def handle(self, *args, **options):
        deleted = delete_same_employee_positions(options.get("hospital"), self.stdout)
        if deleted == 0:
            self.stdout.write(self.style.SUCCESS("Одинаковые EmployeePosition не найдены"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Удалено EmployeePosition: {deleted}"))
