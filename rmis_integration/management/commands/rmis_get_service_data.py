import simplejson as json
from django.core.management import BaseCommand

from rmis_integration.client import Client as RC


class Command(BaseCommand):
    help = "Получение данных по оказанной услуге"

    def add_arguments(self, parser):
        parser.add_argument('service_id', type=str)

    def handle(self, *args, **options):
        c = RC()
        self.stdout.write(json.dumps(c.rendered_services.get_data_by_id(options["service_id"])))
