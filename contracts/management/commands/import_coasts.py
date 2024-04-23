from django.core.management.base import BaseCommand
from openpyxl import load_workbook
from contracts.models import Company, PriceName
from django.db.models import Q


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        """
        :param path - xlsx файл  со столбцами:
        Плательщик/Контрагент, Тарифный план, Действует С
        """
        fp = kwargs["path"]
        wb = load_workbook(filename=fp)
        ws = wb[wb.sheetnames[0]]
        starts = False
        company_idx = ''
        for row in ws.rows:
            cells = [str(x.value) for x in row]
            if not starts:
                if "Тарифный план" in cells:
                    company_idx = cells.index("Плательщик/Контрагент")
                    price_name_idx = cells.index("Тарифный план")
                    price_start_idx = cells.index("Действует С")
                    starts = True
