import json

from datetime import date, datetime
from django.core.management import BaseCommand
from zeep import helpers

from rmis_integration.client import Client


def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


class Command(BaseCommand):
    help = "Поиск направлений"

    def add_arguments(self, parser):
        parser.add_argument('query', type=str)

    def handle(self, *args, **options):
        c = Client()
        sd = c.directions.search_directions(**dict(token.split(':') for token in options['query'].split(',')))
        self.stdout.write("PKS: %s" % json.dumps(sd))
        datas = [helpers.serialize_object(c.directions.get_direction_data(x)) for x in sd]
        datas = [x for x in datas if x.get("refServiceId")]
        self.stdout.write("datas: %s" % json.dumps(datas, default=json_serial))
        srv = {}
        for d in datas:
            for s in d["refServiceId"]:
                if s not in srv:
                    srv[s] = helpers.serialize_object(c.services.get_service_data(s))
        self.stdout.write("srv: %s" % json.dumps(srv, default=json_serial))
