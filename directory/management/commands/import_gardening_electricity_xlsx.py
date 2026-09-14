import json

from django.core.management.base import BaseCommand

from api.gardening.electricity_import import import_electricity_xlsx


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("path", type=str)

    def handle(self, *args, **kwargs):
        fp = kwargs["path"]
        self.stdout.write("Path: " + fp)
        result = import_electricity_xlsx(fp)
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2, default=str))
