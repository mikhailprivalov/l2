from django.core.management.base import BaseCommand

from employees.duplicate_cleanup import delete_employee_duplicates


class Command(BaseCommand):
    help = "Удаляет дубликаты Employee. В группе остаётся запись с меньшим id, должности переносятся на неё."

    def add_arguments(self, parser):
        parser.add_argument(
            "--hospital",
            type=int,
            default=None,
            help="ID организации (Hospitals.pk). Без параметра — все организации.",
        )

    def handle(self, *args, **options):
        deleted = delete_employee_duplicates(options.get("hospital"), self.stdout)
        if deleted == 0:
            self.stdout.write(self.style.SUCCESS("Дубликаты Employee не найдены"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Удалено Employee: {deleted}"))
