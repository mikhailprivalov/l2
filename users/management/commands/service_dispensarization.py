from django.core.management.base import BaseCommand
from openpyxl import load_workbook
from directory.models import DispensaryRouteSheet


class Command(BaseCommand):
    def add_arguments(self, parser):
        """
        :param path - файл с кодами МКБ10.2019 + расшифровка
        """
        parser.add_argument('path', type=str)


    def handle(self, *args, **kwargs):
        fp = kwargs["path"]
        self.stdout.write("Path: " + fp)
        wb = load_workbook(filename=fp)
        ws = wb[wb.sheetnames[0]]
        starts = False
        for row in ws.rows:
            cells = [str(x.value) for x in row]
            if not starts:
                if "код" in cells:
                    starts = True
                    code = cells.index("код")
            else:
                age_client = models.PositiveSmallIntegerField(db_index=True, help_text='Возраст', null=False,
                                                              blank=False)
                sex_client = models.CharField(max_length=1, choices=SEX, help_text="Пол", db_index=True)
                research = models.ForeignKey(Researches, db_index=True, help_text='Исследование включенное в список',
                                             on_delete=models.CASCADE)
                doctor = DoctorProfile.objects.filter(pk=cells[code]).first()
                if doctor:
                    doctor.rmis_login = cells[rmis_login]
                    doctor.rmis_password = cells[rmis_password]
                    doctor.save(update_fields=['rmis_login','rmis_password'])
                    print("Обновлен", doctor)
