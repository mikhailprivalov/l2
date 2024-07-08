from django.core.management.base import BaseCommand
from django.db.models import Q
from openpyxl.workbook import Workbook

from appconf.manager import SettingManager
from directory.models import Researches, Fractions, Unit
from openpyxl import load_workbook

from external_system.models import FsliRefbookTest


class Command(BaseCommand):
    def add_arguments(self, parser):
        """
        :param path - файл
        Фаил с  колонками "Код", "Условия", "Ед. изм", Нижняя Гр., Верхняя Гр.
        для импорта референсов в фракции по внешнему коду
        """
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        fp = kwargs["path"]
        wb = load_workbook(filename=fp)
        ws = wb[wb.sheetnames[0]]

        starts = False
        code_idx, conditions_idx, unit_idx, start_ref_idx, end_ref_idx = None, None, None, None, None
        current_code = None
        for row in ws.rows:
            cells = [str(x.value) for x in row]
            if not starts:
                if "Условия" in cells:
                    code_idx = cells.index("Код")
                    conditions_idx = cells.index("Условия")
                    unit_idx = cells.index("Ед.изм")
                    start_ref_idx = cells.index("Нижняя Гр.")
                    end_ref_idx = cells.index("Верхняя Гр.")
                    starts = True
            else:
                code = cells[code_idx].strip()
                conditions = cells[conditions_idx].strip()
                unit = cells[unit_idx].strip()
                start = cells[start_ref_idx].strip()
                end = cells[end_ref_idx].strip()
                gender = conditions.split("Пол: ")
                print(gender)
                # if code != "None" and code != current_code:
                    # fraction = Fractions.objects.filter(external_code__iexact=code).first()
                    # if not fraction:
                    #     print('Такой фракции нет в справочнике л2')
                    #     continue


                # current_code = code
        if not starts:
            self.stdout.write('Не найдено столбца "Условия"')


