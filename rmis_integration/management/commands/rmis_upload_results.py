import datetime

import simplejson as json
from django.core.management import BaseCommand

from rmis_integration.client import Client as RC


class Command(BaseCommand):
    help = "Выгрузка результатов и направлений в РМИС"

    def handle(self, *args, **options):
        self.stdout.write("{:%Y-%m-%d %H:%M}".format(datetime.datetime.now()) + " - TRIGGER")
        c = RC()
        self.stdout.write(json.dumps(c.directions.check_and_send_all(self.stdout)))
