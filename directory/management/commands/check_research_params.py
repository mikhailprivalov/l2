from django.core.management.base import BaseCommand
from directory.models import Researches, Fractions


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('type_researches', type=str)

    def handle(self, *args, **kwargs):

        type_researches = kwargs["type_researches"]
        researches = None
        if type_researches == "is_lab":
            researches = Researches.objects.filter(podrazdeleniye__p_type=2)
        if researches:
            k = 0
            for r in researches:
                k += 1
                research_code = r.code if r.code else "Код услуги не заполнен"
                fractions = Fractions.objects.filter(research=r)
                if fractions and len(fractions) > 0:
                    for f in fractions:
                        unit_title = "Ед изм - не заполнено"
                        unit_code = "Ед изм - код не заполнен"
                        if f.unit:
                            unit_title = f.unit.title
                            unit_code = f.unit.code
                        print(f"{k}; {r.title}; {research_code}; {r.hide}; - ;{f.title}; {f.fsli}; {unit_title}; {unit_code}")

