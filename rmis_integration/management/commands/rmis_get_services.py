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
        self.cnt = 0
        self.n = 0
        self.nn = 0
        self.start_time = time.time()

    def handle(self, *args, **options):
        # sema = threading.BoundedSemaphore(4)
        c = RC()
        srv = c.services.client.getServices(clinic=c.search_organization_id())
        self.stdout.write("!!!!!!!")
        self.cnt = len(srv)

        def ip(self, c, r):
            # sema.acquire()
            try:
                data = helpers.serialize_object(c.services.client.getService(r["id"]))
                inactive = False
                if data["toDate"]:
                    inactive = datetime.strptime(data["toDate"].strftime('%Y%m%d'), "%Y%m%d") < datetime.now()
                RMISServiceInactive.checkInactive(serviceId=r["id"], enabled=inactive)
            finally:
                self.n += 1
                self.nn += 1
                if self.n % 10 == 0 or self.n == self.cnt:
                    self.stdout.write("{}/{}".format(self.n, self.cnt))
                if self.n % 100 == 0 or self.n == self.cnt:
                    sec = time.time() - self.start_time
                    self.start_time = time.time()
                    self.stdout.write("--- %s op/s ---" % (int(self.nn/sec)))
                    self.nn = 0
                # sema.release()

        self.start_time = time.time()
        threads = []
        for r in srv:
            ip(self, c, r)
            # thread = threading.Thread(target=ip, args=
            # threads.append(thread)
            # thread.start()

        [t.join() for t in threads]
