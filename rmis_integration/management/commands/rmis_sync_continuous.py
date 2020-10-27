import datetime
import time

from django.core.management import BaseCommand

from rmis_integration.client import Client as RC


WAIT_TIME_SECS = 8
WAIT_LONG_TIME_SECS = 300
COUNT_TO_REFRESH_CLIENT = 100


class Command(BaseCommand):
    help = "Выгрузка результатов и направлений в РМИС (непрерывная)"

    def handle(self, *args, **options):
        c = RC()
        cnt = 0
        while True:
            if cnt == COUNT_TO_REFRESH_CLIENT:
                self.stdout.write("Recreating RMIS instance...")
                c = RC()
            self.stdout.write("Start sync at {:%Y-%m-%d %H:%M}".format(datetime.datetime.now()))
            results = c.directions.check_and_send_all(self.stdout, slice_to_upload=True)
            self.stdout.write("Directions uploaded: {}".format(results.get("directions")))
            self.stdout.write("Results uploaded: {}".format(results.get("results")))
            cnt += 1
            if len(results.get("directions") or []) + len(results.get("results") or []) == 0:
                self.stdout.write("Waiting {}\n".format(WAIT_LONG_TIME_SECS))
                time.sleep(WAIT_LONG_TIME_SECS)
            else:
                self.stdout.write("Waiting {}\n".format(WAIT_TIME_SECS))
                time.sleep(WAIT_TIME_SECS)
