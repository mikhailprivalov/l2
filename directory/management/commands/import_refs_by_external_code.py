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
        """
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        fp = kwargs["path"]
        wb = load_workbook(filename=fp)
        ws = wb[wb.sheetnames[0]]

        starts = False
        title, unit, research, fsli, code = '', '', '', '', ''
        for row in ws.rows:
            cells = [str(x.value) for x in row]
            if not starts:
                if "Код ФСЛИ" in cells:
                    title = cells.index("Название")
                    unit = cells.index("Ед.Изм.")
                    research = cells.index("Список услуг")
                    fsli = cells.index("Код ФСЛИ")
                    code = cells.index("Код")
                    starts = True
            else:
                research_nmy_code = cells[research].split(' - ')[0].strip()
