from django.core.management import BaseCommand
import simplejson as json

from api.models import Analyzer
from api.to_astm import get_iss_direction
from directions.models import Napravleniya


class Command(BaseCommand):
    help = "Получение направления в формате ASTM"

    def add_arguments(self, parser):
        parser.add_argument('direction_id', type=int)
        parser.add_argument('analyzer_id', type=int)

    def handle(self, *args, **options):
        self.stdout.write(json.dumps(get_iss_direction(Napravleniya.objects.get(pk=options['direction_id']), Analyzer.objects.get(pk=options['analyzer_id']))))
