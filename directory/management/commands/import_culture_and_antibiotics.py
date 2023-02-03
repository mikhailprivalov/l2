from django.core.management.base import BaseCommand
from directory.models import GroupCulture, Culture, GroupAntibiotic, Antibiotic
import json
from laboratory import utils


class Command(BaseCommand):
    def add_arguments(self, parser):
        """
        :param path - файл
        """
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        fp = kwargs["path"]
        self.stdout.write("Path: " + fp)
        with open(fp) as json_file:
            data = json.load(json_file)
            for group in data["culture_group"]:
                culture_group = GroupCulture(title=group["title"])
                culture_group.save()
                for culture in group["culture_in_group"]:
                    culture_in_group = Culture(title=culture["title"], group_culture=culture_group, fsli=culture["fsli"], lis=culture["lis"])
                    culture_in_group.save()
            for culture in data["culture_without_group"]:
                culture_without_group = Culture(title=culture["title"], group_culture=None, fsli=culture["fsli"], lis=culture["lis"])
                culture_without_group.save()
            for group in data["antibiotic_group"]:
                antibiotic_group = GroupAntibiotic(title=group["title"])
                antibiotic_group.save()
                for antibiotic in group["antibiotic_in_group"]:
                    antibiotic_in_group = Antibiotic(title=antibiotic["title"], group_antibiotic=antibiotic_group, fsli=antibiotic["fsli"], lis=antibiotic["lis"])
                    antibiotic_in_group.save()
            for antibiotic in data["antibiotic_without_group"]:
                antibiotic_withou_group = Antibiotic(title=antibiotic["title"], group_antibiotic=None, fsli=antibiotic["fsli"], lis=antibiotic["lis"])
                antibiotic_withou_group.save()
