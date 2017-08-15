from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "My test command"

    def handle(self, *args, **options):
        self.stdout.write("Doing All The Things!")
