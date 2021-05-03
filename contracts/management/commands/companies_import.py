from django.core.management.base import BaseCommand
from openpyxl import load_workbook
from contracts.models import Company
from django.db.models import Q


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        """
        :param path - xlsx файл с микроорганизмами со столбцами:
        Название, Группа, LIS(код)
        """
        fp = kwargs["path"]
        self.stdout.write("Path: " + fp)
        wb = load_workbook(filename=fp)
        ws = wb[wb.sheetnames[0]]
        starts = False
        title, short_title = '', ''
        for row in ws.rows:
            cells = [str(x.value) for x in row]
            if not starts:
                if "Название" in cells:
                    title = cells.index("Название")
                    short_title = cells.index("Короткое название")
                    starts = True
            else:
                company = Company.objects.filter(Q(title=cells[title]) | Q(short_title=cells[short_title]))
                if not company.exists():
                    Company(title=cells[title], short_title=cells[short_title]).save()
                    print('компания создана', cells[title])  # noqa: T001
