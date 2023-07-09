from django.core.management.base import BaseCommand
from django.db.models import F

from directions.models import TubesRegistration, NumberGenerator
from hospitals.models import Hospitals


class Command(BaseCommand):
    help = "Заполнить пустые номера ёмкостей"

    def handle(self, *args, **kwargs):
        ts = TubesRegistration.objects.filter(number__isnull=True)
        print("Пустых номеров:", ts.count())  # noqa: T001
        ts.update(number=F('id'))
        ts = TubesRegistration.objects.filter(number__isnull=True)
        print("Пустых номеров после обновления:", ts.count())  # noqa: T001

        def_gen = NumberGenerator.objects.filter(end__isnull=True).first()

        if def_gen:
            print(f"Генератор по умолчанию существует ({def_gen})")  # noqa: T001
        else:
            hospital = Hospitals.get_default_hospital()
            pk = TubesRegistration.get_tube_number_generator_pk(hospital)
            print(f"Генератор по умолчанию создан ({NumberGenerator.objects.get(pk=pk)})")  # noqa: T001
