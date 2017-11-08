import threading
import simplejson as json
from django.core.management import BaseCommand
from directions.models import Napravleniya
from rmis_integration.client import Client
from users.models import DoctorProfile


class Command(BaseCommand):
    help = "Повторная выгрузка результатов"

    def add_arguments(self, parser):
        parser.add_argument('directions_range', type=str)

    def handle(self, *args, **options):
        maxthreads = 20
        sema = threading.Semaphore(value=maxthreads)
        threads = list()

        def task(dir: Napravleniya, out):
            sema.acquire()
            out.write("ADD TO RESEND %s -> %s" % (dir.pk, c.directions.delete_services(dir, user=DoctorProfile.objects.all().order_by("pk")[0])))
            sema.release()

        def resend(out):
            sema.acquire()
            self.stdout.write("END")
            sema.release()

        r = options['directions_range'].split('-')
        f = r[0]
        t = r[1]
        c = Client()
        sema.acquire()
        for d in Napravleniya.objects.filter(pk__gte=f, pk__lte=t):
            thread = threading.Thread(target=task, args=(d, self.stdout))
            threads.append(thread)
            thread.start()
        sema.release()
        thread = threading.Thread(target=resend, args=(self.stdout,))
        threads.append(thread)
        thread.start()

        #self.stdout.write(json.dumps(c.directions.check_and_send_all(self.stdout)))
