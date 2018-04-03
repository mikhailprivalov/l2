from django.core.management import BaseCommand

from mq.publisher import mq_send


class Command(BaseCommand):
    help = "Пакетная отправка объектов в MQ"

    def add_arguments(self, parser):
        parser.add_argument('model', type=str)
        parser.add_argument('pk_range', type=str)

    def handle(self, *args, **options):
        n = options['model']
        r = options['pk_range'].split('-')
        f = int(r[0])
        t = int(r[1])
        for pk in range(f, t + 1):
            mq_send("updated", n, str(pk))
            self.stdout.write("{} {} -> MQ".format(n, pk))
