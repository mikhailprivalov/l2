from django.core.management.base import BaseCommand
from openpyxl import load_workbook
import clients.models as clients
from django.db.models import Q
import datetime

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('path', type=str)


    def handle(self, *args, **kwargs):
        fp = kwargs["path"]
        self.stdout.write("Path: " + fp)
        wb = load_workbook(filename=fp)
        ws = wb[wb.sheetnames[0]]
        starts = False
        for row in ws.rows:
            cells = [str(x.value) for x in row]
            # print(cells)
            if not starts:
                if "снилс" in cells and "паспорт" in cells and "полис" in cells:
                    starts = True
                    num_card = cells.index("карта")
                    distict_num = cells.index("участок")
                    lastname = cells.index("фамилия")
                    name = cells.index("имя")
                    patronymic = cells.index("отчество")
                    sex = cells.index("пол")
                    pasport = cells.index("паспорт")
                    distict_gin = cells.index("участок-жк")
                    pasport_serial = cells.index("серия")
                    pasport_num = cells.index("номер")
                    snils = cells.index("снилс")
                    polis = cells.index("полис")
                    born_date = cells.index("дата рождения")
                    continue
            else:
                if clients.Document.objects.filter(Q(document_type=4, number=cells[snils]) |
                                                   Q(document_type=3, number=cells[polis]) |
                                                   Q(document_type=1, serial=cells[pasport_serial], number=cells[pasport_num])).first():
                    ind = clients.Document.objects.filter(Q(document_type=4, number=cells[snils]) |
                                                   Q(document_type=3, number=cells[polis]) |
                                                   Q(document_type=1, serial=cells[pasport_serial], number=cells[pasport_num])).first()
                    i = ind.individual
                    print(i)
                    # if clients.Card.objects.filter(individual=i, base=5).first():
                    #     card_l2 = clients.Card.objects.filter(individual=i, base=5).first()
                    #     print(card_l2)
                else:
                    ind = clients.Individual(family=cells[lastname],
                                             name=cells[name],
                                             patronymic=cells[patronymic],
                                             birthday=datetime.datetime.strptime(cells[born_date], "%Y-%m-%d %H:%M:%S").date(),
                                             sex=cells[sex])
                    ind.save()

                    print('Создан user', ind)

