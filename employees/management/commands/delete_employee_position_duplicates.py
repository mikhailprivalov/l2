from django.core.management.base import BaseCommand

from employees.duplicate_cleanup import delete_employee_position_duplicates


class Command(BaseCommand):
    help = "Удаляет дубликаты EmployeePosition. В группе остаётся запись с меньшим id, связи переносятся на неё."

    def add_arguments(self, parser):
        parser.add_argument(
            "--hospital",
            type=int,
            default=None,
            help="ID организации (Hospitals.pk). Без параметра — все организации.",
        )

    def handle(self, *args, **options):
        deleted = delete_employee_position_duplicates(options.get("hospital"), self.stdout)
        if deleted == 0:
            self.stdout.write(self.style.SUCCESS("Дубликаты EmployeePosition не найдены"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Удалено EmployeePosition: {deleted}"))
