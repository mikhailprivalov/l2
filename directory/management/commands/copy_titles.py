from django.core.management.base import BaseCommand
from directory.models import Researches


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('type_researches', type=str)

    def handle(self, *args, **kwargs):
        type_researches = kwargs["type_researches"]
        if type_researches == "is_lab":
            researches = Researches.objects.filter(podrazdeleniye__p_type=2, hide=False)
            if researches:
                for r in researches:
                    if r.short_title == "":
                        r.short_title = r.title
                        r.save()
                        print(f"{r.podrazdeleniye.title}@ {r.title}@ {r.short_title}")  # noqa: T001
