from django.core.management import BaseCommand

from rmis_integration.client import Client


class Command(BaseCommand):
    help = "Получение названия организации"

    def add_arguments(self, parser):
        parser.add_argument('id', type=int)

    def handle(self, *args, **options):
        c = Client()
        self.stdout.write(str(c.get_organization_title(options["id"], full=True)))
        self.stdout.write(str(c.get_organization_title(options["id"])))
