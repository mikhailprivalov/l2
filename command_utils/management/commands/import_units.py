import json

from django.db import transaction 
from django.core.management import BaseCommand
from directory.models import Fractions, Unit


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
                    print("##########", i)
                    u: Unit = Unit.objects.filter(code=i['ID']).first()
                    if not u:
                        u = Unit.objects.create(code=i['ID'], title=i['FULLNAME'], short_title=i['SHORTNAME'], ucum=i["UCUM"])
                        self.stdout.write(f"{n}/{len(items)} Добавлено: {str(u)}")
                    else:
                        u.hide = False
                        u.title = i['FULLNAME']
                        u.short_title = i['SHORTNAME']
                        u.ucum = i['UCUM'] if i['UCUM'] else ""
                        u.save()
                        self.stdout.write(f"{n}/{len(items)} Обновлено: {str(u)}")

                self.stdout.write("\nОбновление устаревших фракций")
                fs = Fractions.objects.filter(unit__isnull=True, research__hide=False).exclude(units='')
                c = fs.count()
                self.stdout.write(f"Фракций с устаревшими единицами измерения: {c}")

                n = 0
                for f in fs:
                    n += 1
                    self.stdout.write(f"{n}/{c} {f.research.get_title()} — {f.title}")
                    self.stdout.write(f"{n}/{c} устаревшее значение: {f.units}")
                    u = f.get_unit()

                    if u:
                        self.stdout.write(f"{n}/{c} найденное: {u}")
                    else:
                        self.stdout.write(f"{n}/{c} значение для замены не найдено!")


