from django.core.management.base import BaseCommand
from directory.models import Researches, Fractions


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('type_researches', type=str)

    def handle(self, *args, **kwargs):
        type_researches = kwargs["type_researches"]
        if type_researches == "is_lab":
            researches = Researches.objects.filter(podrazdeleniye__p_type=2, hide=False)
            if researches:
                k = 0
                for r in researches:
                    k += 1
                    research_code = r.code if r.code else "Код НМУ услуги не заполнен"
                    fractions = Fractions.objects.filter(research=r)
                    if fractions and len(fractions) > 0:
                        for f in fractions:
                            unit_title = "Ед изм - не заполнено"
                            unit_code = "Ед изм - код не заполнен"
                            if f.unit:
                                unit_title = f.unit.title
                                unit_code = f.unit.code
                            fsli = f.fsli if f.fsli else "ФСЛИ не заполнено"
                            print(f"{k}@{r.podrazdeleniye.title}@ {r.title}@ {research_code}@ {r.hide}@ - @{f.title}@ {fsli}@ {unit_title}@ {unit_code}")  # noqa: T001

        if type_researches == "is_paraclinic":
            researches = Researches.objects.filter(is_paraclinic=True, hide=False)
            k = 0
            for r in researches:
                k += 1
                research_code = r.code if r.code else "Код НМУ услуги не заполнен"
                nsi_id = r.nsi_id if r.nsi_id else "НСИ исследования не заполнен"
                print(f"{k}@{r.title}@ {r.short_title}@{r.podrazdeleniye.title}@{research_code}@ {nsi_id}")  # noqa: T001
