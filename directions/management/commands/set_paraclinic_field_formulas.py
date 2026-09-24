from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from directory.models import ParaclinicInputField


class Command(BaseCommand):
    help = "Записать формулы Видимости и Контроля в поля протокола по id"

    def add_arguments(self, parser):
        parser.add_argument("field_ids", help="id полей через запятую")
        parser.add_argument("visibility", help="формула Видимости")
        parser.add_argument("control", help="формула Контроля")

    def handle(self, *args, **options):
        raw_ids = [part.strip() for part in options["field_ids"].split(",") if part.strip()]
        if not raw_ids:
            raise CommandError("Список id пуст")
        field_ids = []
        for raw_id in raw_ids:
            if not raw_id.isdigit():
                raise CommandError(f"Неверный id: {raw_id}")
            field_id = int(raw_id)
            if field_id not in field_ids:
                field_ids.append(field_id)

        visibility = options["visibility"]
        control = options["control"]
        found = set(ParaclinicInputField.objects.filter(pk__in=field_ids).values_list("pk", flat=True))
        missing = [field_id for field_id in field_ids if field_id not in found]
        with transaction.atomic():
            updated = ParaclinicInputField.objects.filter(pk__in=found).update(visibility=visibility, control_param=control)
        self.stdout.write(f"Обновлено: {updated}")
        if missing:
            self.stdout.write("Не найдены: " + ",".join(str(field_id) for field_id in missing))
