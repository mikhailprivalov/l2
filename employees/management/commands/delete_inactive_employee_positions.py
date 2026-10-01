from django.core.management.base import BaseCommand
from django.db import transaction

from employees.models import EmployeePosition


class Command(BaseCommand):
    help = "Удаляет EmployeePosition с is_active=False. Карточки Employee не удаляет."

    def add_arguments(self, parser):
        parser.add_argument(
            "--hospital",
            type=int,
            default=None,
            help="ID организации (Hospitals.pk). Без параметра — все организации.",
        )

    def handle(self, *args, **options):
        qs = EmployeePosition.objects.filter(is_active=False)
        hospital_id = options.get("hospital")
        if hospital_id is not None:
            qs = qs.filter(employee__hospital_id=hospital_id)
        ids = list(qs.order_by("pk").values_list("pk", flat=True))
        if not ids:
            self.stdout.write(self.style.SUCCESS("Неактивные EmployeePosition не найдены"))
            return
        with transaction.atomic():
            EmployeePosition.objects.filter(pk__in=ids).delete()
        self.stdout.write(f"Удалены EmployeePosition: {ids}")
        self.stdout.write(self.style.SUCCESS(f"Удалено EmployeePosition: {len(ids)}"))
