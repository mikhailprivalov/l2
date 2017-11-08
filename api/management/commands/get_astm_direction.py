from django.core.management import BaseCommand
import simplejson as json

from api.models import Analyzer
from api.to_astm import get_astm
from directions.models import Napravleniya


class Command(BaseCommand):
    help = "Получение направления в формате ASTM"

    def add_arguments(self, parser):
        parser.add_argument('directions', type=str)
        parser.add_argument('analyzer_id', type=int)

    def handle(self, *args, **options):
        self.stdout.write(json.dumps(get_astm(Napravleniya.objects.get(pk__in=options['directions'].split(",")), Analyzer.objects.get(pk=options['analyzer_id']), True)))
