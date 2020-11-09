from django.core.management import BaseCommand

from hospitals.models import Hospitals
from podrazdeleniya.models import Podrazdeleniya
from users.models import DoctorProfile


class Command(BaseCommand):
    help = "Заполнение пустых hospital"

    def handle(self, *args, **options):
        default_h = Hospitals.get_default_hospital()
        if not default_h:
            print('Не настроена организация по умолчанию')
            return
        Podrazdeleniya.objects.filter(hospital__isnull=True).update(hospital=default_h)
        DoctorProfile.objects.filter(hospital__isnull=True).update(hospital=default_h)

