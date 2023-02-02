from django.core.management.base import BaseCommand
from directory.models import GroupCulture, Culture, GroupAntibiotic, Antibiotic
import json
from appconf.manager import SettingManager


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        culture_group = [{
            "pk": group.pk,
            "title": group.title
        } for group in GroupCulture.objects.filter(hide=False)]
        culture_data = [{
            "title": culture.title,
            "group": culture.group_culture_id,
            "fsli": culture.fsli,
            "lis": culture.lis
        } for culture in Culture.objects.filter(hide=False)]
        antibiotic_groups = [{
            "pk": group.pk,
            "title": group.title,
        } for group in GroupAntibiotic.objects.filter(hide=False)]
        antibiotics = [{
            "title": antibiotic.title,
            "group": antibiotic.group_antibiotic_id,
            "fsli": antibiotic.fsli,
            "lis": antibiotic.lis
        } for antibiotic in Antibiotic.objects.filter(hide=False)]
        data = {
            "culture_group": culture_group,
            "culture": culture_data,
            "antibiotic_groups": antibiotic_groups,
            "antibiotics": antibiotics
        }
        dir_tmp = SettingManager.get("dir_param")
        with open(f'{dir_tmp}/culture_and_antibiotics.json', 'w') as fp:
            json.dump(data, fp)
