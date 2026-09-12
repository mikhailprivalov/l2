from django.core.management.base import BaseCommand
from directory.models import Researches


class Command(BaseCommand):
    help = 'Fill empty Researches.internal_code with "{pk}-code"'

    def handle(self, *args, **kwargs):
        researches = Researches.objects.filter(internal_code="")
        updated = 0
        for research in researches.iterator():
            if research.ensure_internal_code():
                research.save(update_fields=["internal_code"])
                updated += 1
                self.stdout.write(f"{research.pk}: {research.internal_code}")
        self.stdout.write(self.style.SUCCESS(f"Updated {updated}"))
