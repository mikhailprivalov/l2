from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Проверка и заполнение дат смерти"

    def handle(self, *args, **options):
        pass
