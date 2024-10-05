from django.core.management.base import BaseCommand
from openpyxl import load_workbook
from podrazdeleniya.models import Podrazdeleniya


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
        department_title_idx, chamber_title_idx, bed_number_idx = '', '', ''
        department_title = None
        for row in ws.rows:
            cells = [str(x.value) for x in row]
            if not starts:
                if "Название палаты" in cells:
                    department_title_idx = cells.index("Отделение")
                    chamber_title_idx = cells.index("Название палаты")
                    bed_number_idx = cells.index("Номер койки")
                    starts = True
            else:
                current_department_title = cells[department_title_idx].strip()
                if current_department_title != department_title:
                    department = Podrazdeleniya.objects.filter(title__iexact=cells[department_title_idx]).first()
                    department_title = department.title

                podrazdeleniye_obj = Podrazdeleniya.objects.filter(title=cells[title].strip()).first()
                if not podrazdeleniye_obj:
                    Podrazdeleniya(title=cells[title], p_type=int(cells[type_podr].strip())).save()
                    self.stdout.write(f'Подразделение добавлено - {cells[title]}')
