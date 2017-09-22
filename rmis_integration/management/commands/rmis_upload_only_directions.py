import datetime

from django.core.management import BaseCommand
from rmis_integration.client import Client as RC

import simplejson as json


class Command(BaseCommand):
    help = "Выгрузка направлений в РМИС"

    def handle(self, *args, **options):
        self.stdout.write("{:%Y-%m-%d %H:%M}".format(datetime.datetime.now()) + " - TRIGGER")
        c = RC()
        self.stdout.write(json.dumps(c.directions.check_and_send_all(self.stdout, True)))
