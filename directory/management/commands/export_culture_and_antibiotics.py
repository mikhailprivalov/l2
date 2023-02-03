from django.core.management.base import BaseCommand
from directory.models import GroupCulture, Culture, GroupAntibiotic, Antibiotic
import json
from appconf.manager import SettingManager


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        culture_groups = []
        for group in GroupCulture.objects.all():
            culture_in_group = []
            for culture in Culture.objects.filter(group_culture=group):
                culture_in_group.append({"title": culture.title, "fsli": culture.fsli, "lis": culture.lis})
            culture_groups.append(
                {
                    "title": group.title,
                    "culture_in_group": culture_in_group,
                }
            )
        culture_without_group = []
        for culture in Culture.objects.filter(group_culture=None):
            culture_without_group.append({
                "title": culture.title,
                "fsli": culture.fsli,
                "lis": culture.lis
            })
        antibiotic_groups = []
        for group in GroupAntibiotic.objects.all():
            antibiotic_in_group = []
            for antibiotic in Antibiotic.objects.filter(group_antibiotic=group):
                antibiotic_in_group.append({
                    "title": antibiotic.title,
                    "fsli": antibiotic.fsli,
                    "lis": antibiotic.lis
                })
            antibiotic_groups.append({
                "title": group.title,
                "antibiotic_in_group": antibiotic_in_group
            })
        antibiotic_without_group = []
        for antibiotic in Antibiotic.objects.filter(group_antibiotic=None):
            antibiotic_without_group.append({
                "title": antibiotic.title,
                "fsli": antibiotic.fsli,
                "lis": antibiotic.lis
            })

        data = {
            "culture_group": culture_groups,
            "culture_without_group": culture_without_group,
            "antibiotic_group": antibiotic_groups,
            "antibiotic_without_group": antibiotic_without_group,
        }
        dir_tmp = SettingManager.get("dir_param")
        with open(f'{dir_tmp}/culture_and_antibiotics.json', 'w') as fp:
            json.dump(data, fp)
