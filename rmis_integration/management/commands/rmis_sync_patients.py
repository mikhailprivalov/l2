import datetime
from django.core.management import BaseCommand

from clients.models import Card, Individual
from rmis_integration.client import Client as RC


class Command(BaseCommand):
    help = "Синхронизация пациентов с РМИС"

    def handle(self, *args, **options):
        self.stdout.write("{:%Y-%m-%d %H:%M}".format(datetime.datetime.now()) + " - TRIGGER")

        objs = Card.objects.filter(napravleniya__isnull=True, is_archive=True)
        cnt = objs.count()
        _, cnt = objs.delete()
        cnt = cnt.get("clients.Card", 0)
        self.stdout.write("Архивных карт без направлений удалено: {}".format(cnt))

        objs = Individual.objects.filter(card__isnull=True)
        cnt = objs.count()
        _, cnt = objs.delete()
        cnt = cnt.get("clients.Individual", 0)
        self.stdout.write("Пацтентов без карт удалено: {}".format(cnt))

        c = RC()
        cds = Card.objects.filter(base__is_rmis=True, is_archive=False)
        count = cds.count()
        i = 0
        for card in cds:
            i += 1
            if card.individual.card_set.filter(base__is_rmis=False).exists():
                continue
            da = c.patients.sync_data(card)
            if da:
                self.stdout.write("Обработка карты {}/{}".format(i, count))
                self.stdout.write(da)
        self.stdout.write("OK")
