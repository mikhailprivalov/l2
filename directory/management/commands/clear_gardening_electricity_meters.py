from django.core.management.base import BaseCommand
from django.db import transaction

from directory.models import GardeningElectricityMeter, GardeningElectricityMeterReading


class Command(BaseCommand):
    help = "Удалить все счётчики электроэнергии и связанные показания"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Показать количество записей без удаления")
        parser.add_argument("-y", "--noinput", action="store_true", help="Удалить без подтверждения")

    def handle(self, *args, **kwargs):
        dry_run = kwargs["dry_run"]
        noinput = kwargs["noinput"]

        deletion_steps = [
            ("GardeningElectricityMeterReading", GardeningElectricityMeterReading.objects.all()),
            ("GardeningElectricityMeter", GardeningElectricityMeter.objects.all()),
        ]

        counts = {label: qs.count() for label, qs in deletion_steps}
        total = sum(counts.values())

        self.stdout.write("Удаление всех счётчиков электроэнергии и показаний")
        for label, count in counts.items():
            self.stdout.write(f"  {label}: {count}")

        if total == 0:
            self.stdout.write("Нет записей для удаления.")
            return

        if dry_run:
            self.stdout.write(f"Итого будет удалено: {total} (dry-run, изменений нет)")
            return

        if not noinput:
            answer = input(f"Удалить все {total} записей? [y/N] ")
            if answer.strip().lower() not in ("y", "yes", "д", "да"):
                self.stdout.write("Отменено.")
                return

        with transaction.atomic():
            deleted_total = 0
            for label, qs in deletion_steps:
                _, deleted_by_model = qs.delete()
                count = sum(deleted_by_model.values())
                if count:
                    self.stdout.write(f"  {label}: {count}")
                    deleted_total += count

        self.stdout.write(f"Готово. Удалено записей: {deleted_total}")
