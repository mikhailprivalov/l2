from django.core.management.base import BaseCommand
from openpyxl import load_workbook
from contracts.models import Company, PriceName
from django.db.models import Q

from directory.models import Researches


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        """
        :param path - xlsx файл  со столбцами:

        """
        fp = kwargs["path"]
        wb = load_workbook(filename=fp)
        ws = wb[wb.sheetnames[0]]
        starts = False
        internal_code_idx = ''
        prices_position = {}
        for row in ws.rows:
            cells = [str(x.value) for x in row]
            if not starts:
                if "Цена Базовая" in cells:
                    internal_code_idx = cells.index("Код прайса")
                    for idx, value in enumerate(cells):
                        prices_position[idx] = value
                    starts = True
