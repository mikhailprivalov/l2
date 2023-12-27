import re

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

        colors = {
            "красной": "#FF0000",
            "оранжевый": "#FF8C00",
            "желтый": "#FFFF00",
            "жёлтой": "#FFFF00",
            "зеленый": "#008000",
            "голубой": "#00FFFF",
            "синий": "#0000FF",
            "фиолетовой": "#9400D3",
            "сиреневой": "#c8a2c8",
            "розовой": "#FF1493",
            "белый": "#FFFFFF",
            "серой": "#808080",
            "коричневый": "#8B4513",
        }
        color_string = "|".join(list(colors.keys()))
        regex_pattern = f"\b({color_string})\b=ig"
        print(regex_pattern)
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
            elif starts and cells[tubes_title] != 'None':
                color = re.search(regex_pattern, cells[tubes_title].lower())
                if color:
                    print(color.group(0))
                current_tubes = Tubes.objects.filter(title=cells[tubes_title]).first()
                if not current_tubes:
                    new_tubes = Tubes(title=cells[tubes_title], color='#1122FF')
                    # new_tubes.save()
                    # self.stdout.write(f'Пробирка добавлена - {new_tubes.title}')
                # else:
                #     print('f')
                #     # self.stdout.write(f'Такая пробирка уже есть - {current_tubes.title}')
