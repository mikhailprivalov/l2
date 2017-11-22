import datetime
from django.core.management import BaseCommand

from clients.models import Individual
from rmis_integration.client import Client


class Command(BaseCommand):
    help = "Синхронизация пациентов с РМИС"

    def handle(self, *args, **options):
        self.stdout.write("{:%Y-%m-%d %H:%M}".format(datetime.datetime.now()) + " - TRIGGER")

        ind = Individual.objects.all()
        all_cnt = ind.count()
        cnt = 0
        c = Client()
        for i in ind:
            cnt += 1
            i.sync_with_rmis(out=self.stdout, c=c)
            self.stdout.write("Снхронизировано {}/{}".format(cnt, all_cnt))

        ind = Individual.objects.all()
        after_ind = ind.count()
        self.stdout.write("Физ.лиц осталось {} из {}".format(after_ind, all_cnt))
