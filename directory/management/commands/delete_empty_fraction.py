from django.core.management.base import BaseCommand
from directory.models import Researches, Fractions


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        lab_research = Researches.get_laboratory_researches(-1)
        for research in lab_research:
            fractions = Fractions.objects.filter(research_id=research.pk)
            if len(fractions) < 2:
                continue
            for fraction in fractions:
                if fraction.fsli is None and len(fractions) > 1:
                    fraction.delete()



