from django.core.management.base import BaseCommand
from openpyxl import load_workbook

from researches.models import Tubes


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        """
        :param path - xlsx файл со столбцами:
        Контейнер
        """

        fp = kwargs['path']
        self.stdout.write('Path: ' + fp)
        wb = load_workbook(filename=fp)
        ws = wb[wb.sheetnames[0]]
        starts = False
        tubes_title = ''
        for row in ws.rows:
            cells = [str(x.value) for x in row]
            if not starts:
                if 'Контейнер' in cells:
                    tubes_title = cells.index('Контейнер')
                    starts = True
            elif cells[tubes_title] != 'None':
                current_tubes = Tubes.objects.filter(title=cells[tubes_title]).first()
                if not current_tubes:
                    new_tubes = Tubes(title=cells[tubes_title], color='#1122FF')
                    new_tubes.save()
                    self.stdout.write(f'Пробирка добавлена - {new_tubes.title}')
                else:
                    self.stdout.write(f'Такая пробирка уже есть - {current_tubes.title}')
