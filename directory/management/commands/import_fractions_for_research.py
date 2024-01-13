from django.core.management.base import BaseCommand
from directory.models import Fractions, Unit
import json


class Command(BaseCommand):
    def add_arguments(self, parser):
        """
        :param path - файл
        """
        parser.add_argument('path', type=str)
        parser.add_argument('research', type=str)

    def handle(self, *args, **kwargs):
        fp = kwargs["path"]
        research_pk = kwargs["research"]
        with open(fp) as json_file:
            data = json.load(json_file)
            for fraction in data:
                unit = Unit.objects.filter(code=fraction["code"]).first()
                fraction_data = Fractions.objects.filter(research_id=research_pk).first()
                fraction_obj = Fractions(
                    research_id=research_pk,
                    relation=fraction_data.relation,
                    title=fraction["title"],
                    unit=unit,
                    sort_weight=fraction["sort_weight"],
                    code=fraction["code"],
                    fsli=fraction["fsli"]
                )
                fraction_obj.save()
                self.stdout.write(f'Фракция добавлена - {fraction_obj.title}')
