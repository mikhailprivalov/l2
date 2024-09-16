from django.core.management.base import BaseCommand
from api.parse_file.forms100 import form_02


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        """
        Загрузка посещений из файла

        На входе:
        Файл XLSX с посещениями
        Cтруктура:
        номер карты, Заведующий отделением, Отделение, Услуга, Фамилия, Имя, Отчество, Дата рождения, СНИЛС, Диагноз, Дата услуги, Это травма
        """

        fp = kwargs['path']
        result = form_02({"file": fp})
        if result["ok"]:
            self.stdout.write('Файл выгружен')
        else:
            self.stdout.write("Ошибка выгрузки файла")


