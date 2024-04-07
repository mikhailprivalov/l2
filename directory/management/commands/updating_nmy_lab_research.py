from django.core.management.base import BaseCommand
from directory.models import Fractions, LaboratoryMaterial, Researches, ReleationsFT
from openpyxl import load_workbook

from podrazdeleniya.models import Podrazdeleniya
from researches.models import Tubes


class Command(BaseCommand):
    def add_arguments(self, parser):
        """
        :param path - файл
        """
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        fp = kwargs["path"]
        wb = load_workbook(filename=fp)
        ws = wb[wb.sheetnames[0]]
        starts = False
        internal_code, nmy_cod,  = '', ''
        for row in ws.rows:
            cells = [str(x.value) for x in row]
            if not starts:
                if "Код" in cells:
                    internal_code = cells.index("Код по прайсу")
                    nmy_cod = cells.index("Код ОКМУ")
                    starts = True
            else:
                self.stdout.write("Услуга добавлена")
