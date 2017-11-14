import datetime
from django.core.management import BaseCommand
from clients.models import Individual


class Command(BaseCommand):
    help = "Синхронизация данных физ.лиц с РМИС"

    def add_arguments(self, parser):
        parser.add_argument('individual_id', type=str)

    def handle(self, *args, **options):
        Individual.objects.get(pk=options["individual_id"]).sync_with_rmis(self.stdout)
