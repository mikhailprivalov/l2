import simplejson as json
from django.core.management import BaseCommand

import directions.models as directions
from rmis_integration.client import Client as RC


class Command(BaseCommand):
    help = "Поиск записи госпитализации для направления"

    def add_arguments(self, parser):
        parser.add_argument('direction_id', type=str)

    def handle(self, *args, **options):
        c = RC()
        d = directions.Napravleniya.objects.get(pk=options["direction_id"])
        self.stdout.write(json.dumps(c.hosp.search_last_opened_hosp_record(d.client.individual.check_rmis(client=c))))
