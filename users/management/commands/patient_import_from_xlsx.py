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
        distr = {'19000000': 'ОГАУЗ Иркутская МСЧ 2', '19010000': 'Терапевтич. 1',
                 '19020000': 'Терапевтич. 2', '19030000': 'Терапевтич. 3', '19040000': 'Стоматологическ',
                 '19050000': 'Стомат.-ортопед', '19060000': 'Женская консуль', '19070000': 'Невропатолог',
                 '19080000': 'Эндоскопист', '19090000': 'Отоларинголог', '19100000': 'Окулист', '19110000': 'Кардиолог',
                 '19120000': 'Ревматолог', '19130000': 'Уролог', '19140000': 'Онколог', '19150000': 'Фтизиатр',
                 '19160000': 'Хирург', '19170000': 'Эндокринолог', '19180000': 'Гастроэнтеролог',
                 '19190000': 'Иглорефлексотер', '19200000': 'ЛФК', '19210000': 'Мануальный тера', '19220000': 'ФТО',
                 '19230000': 'Проктолог', '19240000': 'Луч. диагностик', '19250000': 'КДЛ', '19260000': 'Инфекционист',
                 '19270000': 'Психиатр', '19410000': 'Цитология', '19490000': 'Травмпункт', '19580000': 'Психолог',
                 '19310000': 'ОФД', '19320000': 'УЗС', '19460000': 'Терапевтич. 4', '19470000': 'Терапевтич. 5',
                 '19480000': 'Терапевпич. 6', '19280000': 'Процедурный', '19300000': 'Гематолог',
                 '19330000': 'Нефролог', '19340000': 'Невролог', '19350000': 'Травматолог орт',
                 '19360000': 'Пульмонолог', '19370000': 'Дерматолог', '19510000': 'Рентген', '19520000': 'Маммолог',
                 '19530000': 'Радиолог', '19540000': 'Радиолог-гинеко', '19550000': 'Анастезиолог',
                 '19560000': 'Логопед', '19570000': 'Иммунолог', '19380000': 'Патаморфолог',
                 '19390000': 'Конс. отдел ДЦ', '19400000': 'Стационар ДЦ', '19420000': 'Чел-лиц стомат.',
                 '19430000': 'Смотровой', '19440000': 'Подросковый', '19450000': 'Дн.стационар',
                 '19500000': 'Химиотерапия', '19290000': 'Аллерголок', '19050100': 'Ортопеды',
                 '19050200': 'Ортопеды-техник', '19600000': 'Лаб.биохимии', '19590000': 'Нейрофизиология',
                 '19610000': 'Лаб.гематологии', '19620000': 'Общеклин.лаб.', '19630000': 'Иммунолог.лаб.',
                 '19640000': 'Реанимац,анесте', '19650000': 'Бак.лаборатория', '19010400': 'Участок 4',
                 '19010800': 'Участок 8', '19020400': 'Участок 11', '19030100': 'ПРОЧИЕ', '19470100': 'ДИСПАНСЕРИЗАЦИЯ',
                 '19040100': 'Пародонтология', '19040200': 'Хирургия', '19040300': 'Терапия', '19040400': 'Хоз.расчет',
                 '19060100': 'Участок 1', '19060300': 'Участок 2', '19060400': 'Участок 3', '19020500': 'Участок 1',
                 '19020600': 'Участок 2', '19020700': 'Участок 5', '19020800': 'Участок 6', '19020900': 'Участок 7',
                 '19021000': 'Медработники', '19010900': 'Участок 9', '19011000': 'Участок 10',
                 '19011100': 'Участок 12', '19660000': 'ПЦР-лаборатория', '19011200': 'Участок 3',
                 '19030200': 'ПРОФОТДЕЛЕНИЕ', '19030300': 'РЕЕСТР', '19060500': 'Участок 4',
                 '19030101': 'ДНЕВНОЙ СТАЦИОНАР', '19850000': 'Скорая помощь', '19860000': 'Тромболизис',
                 '19870000': 'Мед.генетич. консультация', '19880000': 'Репродукт. технологии',
                 '19770000': 'Терапевтич.7', '19780000': 'Терапевтич.8', '19030400': 'ГРАЖДАНЕ УКРАИНЫ',
                 '19030500': 'Мед.работники', '19030600': 'ВОЕНКОМАТ', '19900000': 'Приемное', '19021100': 'Участок 14',
                 '19011300': 'Участок 13', '19680000': 'Процедурный', '19720000': 'Сурдолог',
                 '19760000': 'Нейрохирургия', '19800000': 'Изосерол.лаборатория', '19810000': 'Лаб.полим.цепн.',
                 '19990000': 'Гистология', '19021200': 'Участок 16', '19011400': 'Участок 15'}

        def get_district(uch=None, gin_uch=None):
            """
            парам1 - код для обычного участка
            парам2 - код для гинекологического участка
            """
            uch.strip()
            gin_uch.strip()
            obj_return = [None, None]
            if uch:
                title_uch = distr.get(uch)
                if title_uch != None:
                    obj_uch, created = clients.District.objects.get_or_create(code_poliklinika=uch,
                        defaults={'title':title_uch, 'is_ginekolog':False, 'sort_weight':'0'})
                    obj_return.insert(0, obj_uch)
            if gin_uch != None:
                title_gin = distr.get(gin_uch)
                if title_gin != None:
                    obj_gin, gin_created = clients.District.objects.get_or_create(code_poliklinika=gin_uch,
                        defaults={'title':title_gin,'is_ginekolog':True, 'sort_weight':'0'})
                    obj_return.insert(1, obj_gin)

            return obj_return


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
                    continue
            else:
                #если есть индивидуал по документам
                if clients.Document.objects.filter(Q(document_type=4, number=cells[snils]) |
                                                   Q(document_type=3, number=cells[polis]) |
                                                   Q(document_type=1, serial=cells[pasport_serial], number=cells[pasport_num])).first():
                    ind = clients.Document.objects.filter(Q(document_type=4, number=cells[snils]) |
                                                   Q(document_type=3, number=cells[polis]) |
                                                   Q(document_type=1, serial=cells[pasport_serial], number=cells[pasport_num])).first()

                    add_dist = get_district(cells[distict_num], cells[district_gin])

                    i = ind.individual
                    if clients.Card.objects.filter(individual=i, base=base_l2).first():
                        clients.Card.objects.filter(individual=i, base=base_l2).update(number_poliklinika=cells[num_card],
                            district=add_dist[0], ginekolog_district = add_dist[1])
                    else:
                        #создать карту L2
                        last_l2 = clients.Card.objects.filter(base__internal_type=True).extra(
                            select={'numberInt': 'CAST(number AS INTEGER)'}
                        ).order_by("-numberInt").first()
                        n = 0
                        if last_l2:
                            n = int(last_l2.number)
                        c = clients.Card.objects.create(number=n + 1, base=base_l2, individual=i, number_poliklinika=cells[num_card],
                            district=add_dist[0], ginekolog_district = add_dist[1])
                else:
                    #создать индивидуал, докумнты, карты в l2.
                    ind = clients.Individual.objects.create(family=cells[lastname], name=cells[name], patronymic=cells[patronymic],
                                             birthday=datetime.datetime.strptime(cells[born_date], "%Y-%m-%d %H:%M:%S").date(),
                                             sex=cells[sex])

                    if cells[snils]:
                        clients.Document.objects.create(document_type=4, number=cells[snils], individual=ind)

                    document_polis = None
                    if cells[polis]:
                        document_polis = clients.Document.objects.create(document_type=3, number=cells[polis], individual=ind)
                    if cells[pasport_serial] and cells[pasport_num]:
                        clients.Document.objects.create(document_type=1, number=cells[pasport_num], serial=cells[pasport_serial],
                                                                   individual=ind)

                    add_dist = get_district(cells[distict_num], cells[district_gin])
                    clients.Card.objects.create(individual=i, base=base_l2, number_poliklinika=cells[num_card],
                                    polis=document_polis, district=add_dist[0], ginekolog_district = add_dist[1])




