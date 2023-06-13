from django.core.management.base import BaseCommand
from django.db.models import F

from directions.models import TubesRegistration


class Command(BaseCommand):
    help = "Заполнить пустые номера ёмкостей"

    def handle(self, *args, **kwargs):
        ts = TubesRegistration.objects.filter(number__isnull=True)
        print("Пустых номеров:", ts.count())  # noqa: T001
        ts.update(number=F('id'))
        ts = TubesRegistration.objects.filter(number__isnull=True)
        print("Пустых номеров после обновления:", ts.count())  # noqa: T001
