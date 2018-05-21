import threading

import simplejson as json
from django.core.management import BaseCommand
from datetime import date, datetime

from django.utils import timezone
from zeep import helpers
import time

from directions.models import RMISServiceInactive
from rmis_integration.client import Client as RC

def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))

class Command(BaseCommand):
    help = "Получение списка услуг из РМИС"

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout=None, stderr=None, no_color=False)
        self.n = 0

    def handle(self, *args, **options):
        sema = threading.BoundedSemaphore(8)
        c = RC()
        srv = c.services.client.getServices(clinic=c.search_organization_id())
        self.stdout.write("!!!!!!!")
        cnt = len(srv)

        def ip(self, c, cnt, start_time, r):
            sema.acquire()
            try:
                data = helpers.serialize_object(c.services.client.getService(r["id"]))
                inactive = False
                if data["toDate"]:
                    inactive = datetime.strptime(data["toDate"].strftime('%Y%m%d'), "%Y%m%d") < datetime.now()
                RMISServiceInactive.checkInactive(serviceId=r["id"], enabled=inactive)
            except:
                self.stdout.write("except")
            finally:
                self.n += 1
                if self.n % 10 == 0 or self.n == cnt:
                    self.stdout.write("{}/{}".format(self.n, cnt))
                if self.n % 100 == 0 or self.n == cnt:
                    sec = time.time() - start_time
                    self.stdout.write("--- %s op/s ---" % (int(self.n/sec)))
                sema.release()

        start_time = time.time()
        threads = []
        for r in srv:
            thread = threading.Thread(target=ip, args=(self, c, cnt, start_time, r))
            threads.append(thread)
            thread.start()

        [t.join() for t in threads]
