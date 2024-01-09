from django.core.management import BaseCommand

from appconf.manager import SettingManager
from directions.models import Napravleniya
from results_feed.models import ResultFeed


class Command(BaseCommand):
    help = "Пересоздание ленты результатов"

    def handle(self, *args, **options):
        if not SettingManager.l2('feed'):
            self.stdout.write("Лента результатов отключена")
            return

        self.stdout.write("Очистка ленты результатов...")
        _, deleted = ResultFeed.objects.all().delete()
        self.stdout.write(f"Удалено {deleted.get('results_feed.ResultFeed', 0)} записей")

        directions = Napravleniya.objects.all()
        self.stdout.write(f"Создание ленты результатов для {directions.count()} направлений...")
        cnt = 0
        for direction in directions:
            cnt += 1
            ResultFeed.insert_feed_by_direction(direction, disable_send=True)
            self.stdout.write(f"{cnt}/{directions.count()}")
        self.stdout.write("Готово")
