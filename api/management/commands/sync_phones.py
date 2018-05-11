from django.core.management import BaseCommand

from clients.models import Phones


class Command(BaseCommand):
    help = "Синхронизация номеров"

    def handle(self, *args, **options):
        n = 0
        pp = Phones.objects.all()
        c = pp.count()
        for p in pp:
            n += 1
            self.stdout.write("{}/{} {} -> {}".format(n, c, p.number, p.normalize_number()))
