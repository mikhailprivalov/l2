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
            if not starts:
                if "снилс" in cells and "полис" in cells:
                    starts = True
                    num_card = cells.index("карта")
                    distict_num = cells.index("участок")
                    lastname = cells.index("фамилия")
                    name = cells.index("имя")
                    patronymic = cells.index("отчество")
                    sex = cells.index("пол")
                    house = cells.index("дом")
                    room = cells.index("квартриа")
                    district_gin = cells.index("участок-жк")
                    city = cells.index("город")
                    street = cells.index("улица")
                    pasport_serial = cells.index("серия")
                    pasport_num = cells.index("номер")
                    snils = cells.index("снилс")
                    polis = cells.index("полис")
                    born_date = cells.index("дата рождения")
                    base_l2 = clients.CardBase.objects.get(internal_type=True)
                    distr_gin = {'19060000':'Женская консуль','19060100':'Участок 1','19060300':'Участок 2',
                               '19060400':'Участок 3','19060500':'Участок 4'}
                    distr = {}

                    continue
            else:
                if clients.Document.objects.filter(Q(document_type=4, number=cells[snils]) |
                                                   Q(document_type=3, number=cells[polis]) |
                                                   Q(document_type=1, serial=cells[pasport_serial], number=cells[pasport_num])).first():
                    ind = clients.Document.objects.filter(Q(document_type=4, number=cells[snils]) |
                                                   Q(document_type=3, number=cells[polis]) |
                                                   Q(document_type=1, serial=cells[pasport_serial], number=cells[pasport_num])).first()
                    i = ind.individual
                    if clients.Card.objects.filter(individual=i, base=base_l2).first():
                        clients.Card.objects.filter(individual=i, base=base_l2).update(number_poliklinika=cells[num_card])
                    else:
                        last_l2 = clients.Card.objects.filter(base__internal_type=True).extra(
                            select={'numberInt': 'CAST(number AS INTEGER)'}
                        ).order_by("-numberInt").first()
                        n = 0
                        if last_l2:
                            n = int(last_l2.number)
                        c = clients.Card.objects.create(number=n + 1, base=base_l2, individual=i)
                        print(c.number, c.number_poliklinika)
                else:
                    print('No non on')
                    #создать индивидуал, докумнты, карты в l2.
                    ind = clients.Individual.objects.create(family=cells[lastname], name=cells[name], patronymic=cells[patronymic],
                                             birthday=datetime.datetime.strptime(cells[born_date], "%Y-%m-%d %H:%M:%S").date(),
                                             sex=cells[sex])
                    print('Создан user', ind)
                    document = None
                    document_polis = None
                    if cells[snils]:
                        document = clients.Document.objects.create(document_type=4, number=cells[snils], individual=ind)
                    if cells[polis]:
                        document_polis = clients.Document.objects.create(document_type=3, number=cells[polis], individual=ind)
                    if cells[pasport_serial] and cells[pasport_num]:
                        document = clients.Document.objects.create(document_type=1, number=cells[pasport_num], serial=cells[pasport_serial],
                                                                   individual=ind)
                    #определим участки

                    if cells[sex] == 'ж':
                        pass

                    created_cardl2 = clients.Card.objects.create(individual=i, base=base_l2, number_poliklinika=cells[num_card],
                                    polis=document_polis)
                    print(created_cardl2)

        privalov = clients.Card.objects.filter(base=base_l2, number='14').first()
        print(privalov.number_poliklinika)
        print(privalov.base)




