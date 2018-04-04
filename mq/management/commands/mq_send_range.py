from django.core.management import BaseCommand

from mq.publisher import mq_send


class Command(BaseCommand):
    help = "Пакетная отправка объектов в MQ"

    def add_arguments(self, parser):
        parser.add_argument('model', type=str)
        parser.add_argument('pk_range', type=str)

    def handle(self, *args, **options):
        n = options['model']
        r = options['pk_range']
        f = 0
        if r != "*":
            r = r.split('-')
            f = int(r[0])
            t = int(r[1])
        else:
            from django.apps import apps
            na = n.split(".")
            m = apps.get_model(app_label=na[0], model_name=na[2])
            t = 0
            a = m.objects.all().order_by("-pk").first()
            if a:
                t = a.pk
        for pk in range(f, t + 1):
            mq_send("updated", n, str(pk))
            self.stdout.write("{} {} -> MQ".format(n, pk))
