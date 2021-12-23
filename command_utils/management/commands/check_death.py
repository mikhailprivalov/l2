from django.core.management import BaseCommand

from hospitals.models import Hospitals
from laboratory.settings import DEATH_RESEARCH_PK, PERINATAL_DEATH_RESEARCH_PK
from users.models import DoctorProfile


class Command(BaseCommand):
    help = "Проверка и заполнение дат смерти"
    def handle(self, *args, **options):
        pass



