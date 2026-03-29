from django.core.management.base import BaseCommand
from openpyxl import load_workbook

from directory.models import Culture, GroupCulture, Researches


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
        code_price, code_nmu, uet = '', '', ''
        for row in ws.rows:
            cells = [str(x.value) for x in row]
            if not starts:
                if "Код по прайсу" in cells:
                    code_price = cells.index("Код по прайсу")
                    title = cells.index("Услуга")
                    code_nmu = cells.index("Код ОКМУ")
                    uet = cells.index("УЕТ")
                    starts = True
            else:
                research = Researches.objects.filter(internal_code=cells[code_price]).first()
                if not research:
                    continue
                research.uet_refferal_doc = float(cells[uet])
                research.save()
                print('UET', cells[title], '--', cells[code_price], '--', cells[uet])  # noqa: T001
