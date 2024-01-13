from django.core.management.base import BaseCommand
from directory.models import Researches, ParaclinicInputGroups, ParaclinicInputField, Fractions
import json
from appconf.manager import SettingManager


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('research_pk', type=int)

    def handle(self, *args, **kwargs):
        research_pk = kwargs["research_pk"]
        research_data = {}
        r = Researches.objects.get(pk=research_pk)
        factions = Fractions.objects.filter(research_id=research_pk)
        data_fractions = [
            {
                "title": f.title,
                "unit_code": f.unit.code,
                "unit_title": f.unit.title,
                "unit_short_title": f.unit.short_title,
                "sort_weight": f.sort_weight,
                "code": f.code,
                "fsli": f.fsli,
            }
            for f in factions
        ]
        dir_tmp = SettingManager.get("dir_param")
        with open(f'{dir_tmp}/{research_pk}_fractions.json', 'w') as fp:
            json.dump(data_fractions, fp)
