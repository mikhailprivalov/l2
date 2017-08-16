from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Выгрузка результатов "

    def handle(self, *args, **options):
        self.stdout.write("Doing All The Things!")
