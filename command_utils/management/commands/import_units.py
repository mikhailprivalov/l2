import json

from django.db import transaction 
from django.core.management import BaseCommand
from directory.models import Unit


class Command(BaseCommand):
    help = "Единицы измерения (N3)"

    def add_arguments(self, parser):
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        fp = kwargs["path"]
        self.stdout.write(f"Файл: {fp}")
        with open(fp) as f:
            data = json.load(f)
            items = data['items']

            self.stdout.write(f"Число записей: {len(items)}")
            with transaction.atomic():
                Unit.objects.all().update(hide=True)

                n = 0
                for item in items:
                    n += 1
                    i = item['attributes']
                    u: Unit = Unit.objects.filter(code=i['ID']).first()
                    if not u:
                        u = Unit.objects.create(code=i['ID'], title=i['FULLNAME'], short_title=i['SHORTNAME'])
                        self.stdout.write(f"{n}/{len(items)} Добавлено: {str(u)}")
                    else:
                        u.hide = False
                        u.title = i['FULLNAME']
                        u.short_title = i['SHORTNAME']
                        u.save()
                        self.stdout.write(f"{n}/{len(items)} Обновлено: {str(u)}")

