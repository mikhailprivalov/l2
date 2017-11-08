from django.core.management import BaseCommand
from directions.models import Napravleniya
from rmis_integration.client import Client
from users.models import DoctorProfile


class Command(BaseCommand):
    help = "Выгрузка результатов и направлений в РМИС"

    def add_arguments(self, parser):
        parser.add_argument('directions_range', type=str)

    def handle(self, *args, **options):
        r = options['directions_range'].split('-')
        f = r[0]
        t = r[1]
        c = Client()
        for d in Napravleniya.objects.filter(pk__gte=f, pk__lte=t):
            self.stdout.write("RESEND %s -> %s" % (d.pk, c.directions.delete_services(d, user=DoctorProfile.objects.all().order_by("pk")[0])))
