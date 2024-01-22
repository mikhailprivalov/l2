from django.core.management.base import BaseCommand
from directory.models import LaboratoryMaterial, Researches
from openpyxl import load_workbook


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        lab_research_groups = Researches.get_tubes(-1)
        for research_group in lab_research_groups:
            step = 0
            for researches in research_group["researches"]:
                current_research = Researches.objects.get(pk=researches["pk"])
                current_research.sort_weight = 1 + step
                current_research.save()
                self.stdout.write(f'Порядок изменён - {current_research.title}')
                step += 1
