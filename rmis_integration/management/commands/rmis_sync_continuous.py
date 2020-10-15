import datetime
import time

from django.core.management import BaseCommand

from rmis_integration.client import Client as RC


WAIT_TIME_SECS = 4


class Command(BaseCommand):
    help = "Выгрузка результатов и направлений в РМИС (непрерывная)"

    def handle(self, *args, **options):
        c = RC()
        while True:
            self.stdout.write("{:%Y-%m-%d %H:%M}".format(datetime.datetime.now()) + " - Starting")
            results = c.directions.check_and_send_all(self.stdout, slice_to_upload=True)
            self.stdout.write("Directions uploaded: {}".format(results.get("directions")))
            self.stdout.write("Results uploaded: {}".format(results.get("results")))
            self.stdout.write("Waiting {}\n".format(WAIT_TIME_SECS))
            time.sleep(WAIT_TIME_SECS)
