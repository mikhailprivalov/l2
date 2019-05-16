from clients.models import Document, DispensaryReg
from directions.models import Napravleniya, IstochnikiFinansirovaniya, Issledovaniya
from directory.models import Researches
from copy import deepcopy
from collections import OrderedDict
from django.db.models import Q
import datetime


def get_all_doc(docs: [Document]):
    """
    возвращает словарь словарей documents. Данные о документах: паспорт : номер: серия, полис: номер, снислс: номер
    """
    documents = {
        'passport': {'num': "", 'serial': "", 'date_start': "", 'issued': ""},
        'polis': {'serial': "", 'num': "", 'issued': ""},
        'snils': {'num': ""},
        'bc': {'num': "", 'serial': "", 'date_start': "", 'issued': ""},
    }

    for d in docs:
        if d.document_type.title == "СНИЛС":
            documents["snils"]["num"] = d.number

        if d.document_type.title == 'Паспорт гражданина РФ':
            documents["passport"]["num"] = d.number
            documents["passport"]["serial"] = d.serial
            documents["passport"]["date_start"] = "" if not d.date_start else d.date_start.strftime("%d.%m.%Y")
            documents["polis"]["issued"] = d.who_give

        if d.document_type.title == 'Полис ОМС':
            documents["polis"]["num"] = d.number
            documents["polis"]["serial"] = d.serial
            documents["polis"]["date_start"] = "" if not d.date_start else d.date_start.strftime("%d.%m.%Y")
            documents["polis"]["issued"] = d.who_give

        if d.document_type.title == 'Свидетельство о рождении':
            documents["bc"]["num"] = d.number
            documents["bc"]["serial"] = d.serial
            documents["bc"]["date_start"] = "" if not d.date_start else d.date_start.strftime("%d.%m.%Y")
            documents["bc"]["issued"] = d.who_give

    return documents


def get_coast_from_issledovanie(dir_research_loc):
    """
    При печати листа на оплату возвращает (цены из записанных в Исследования)
    На основании прайса, услуг возвращает Для листа на оплату {
                                                             направление: {услуга:[цена, скидка, количество],услуга:[цена, скидка, количество]},
                                                             направление: {услуга:[цена, скидка, количество],услуга:[цена, скидка, количество]},
                                                             направление: {услуга:[цена, скидка, количество],услуга:[цена, скидка, количество]},
                                                             }
    """
    d = tuple()
    if type(dir_research_loc) == dict:
        dict_coast = {}
        for k, v in dir_research_loc.items():
            d = ({r: [s, d, h, ] for r, s, d, h in
                  Issledovaniya.objects.filter(napravleniye=k, research__in=v, coast__isnull=False).values_list(
                      'research_id', 'coast', 'discount', 'how_many')})
            dict_coast[k] = d
        return dict_coast
    else:
        return 0


def get_research_by_dir(dir_temp_l):
    """
    Получить словаь: {направление1:[услуга1, услуга2, услуга3],направление2:[услуга1].....}
    :param dir_temp_l:
    :return:
    """
    dict_research_dir = {}
    for i in dir_temp_l:
        # Если есть хотя бы одно сохранения услуги по направлению, то не учитывается
        if any([x.doc_save is not None for x in Issledovaniya.objects.filter(napravleniye=i)]):
            continue
        else:
            research_l = ([x.research_id for x in Issledovaniya.objects.filter(napravleniye=i)])
        dict_research_dir[i] = research_l
    return dict_research_dir


def get_final_data(research_price_loc):
    """
    Получить итоговую структуру данных: код услуги, напрвление, услуга, цена, скидка/наценка, цена со скидкой, кол-во, сумма

    Направление указывается один раз для нескольких строк
    """

    total_sum = 0
    tmp_data = []
    is_discount = False
    z = ""
    x = ""
    tmp_napr = []
    for k, v in research_price_loc.items():
        research_attr = ([s for s in Researches.objects.filter(id__in=v.keys()).values_list('id', 'title')])
        research_attr_list = [list(z) for z in research_attr]
        for research_id, research_coast in v.items():
            h = []
            for j in research_attr_list:
                if research_id == j[0]:
                    if k != 0:
                        h.append(k)
                        k = 0
                    else:
                        h.append("")
                    h.extend(j)
                    h.append("{:,.2f}".format(research_coast[0]).replace(",", " "))
                    coast_with_discount = research_coast[0] + (research_coast[0] * research_coast[1] / 100)
                    if research_coast[1] != 0:
                        z = "+"
                        if research_coast[1] > 0:
                            x = "+"
                        else:
                            x = ""
                    h.append(x + str(research_coast[1]))
                    h.append("{:,.2f}".format(coast_with_discount).replace(",", " "))
                    h.append(research_coast[2])
                    research_sum = coast_with_discount * research_coast[2]
                    h.append("{:,.2f}".format(research_sum).replace(",", " "))
                    h[0], h[1] = h[1], h[0]
                    total_sum += research_sum
                    research_attr_list.remove(j)
                    tmp_data.append(h)
                    if h[1]:
                        tmp_napr.append(h[1])
                if h:
                    break

    res_lis = []
    for t in tmp_data:
        tmp_d = list(map(str, t))
        res_lis.append(tmp_d)

    total_data = []

    total_data.append(res_lis)

    total_data.append("{:,.2f}".format(total_sum).replace(",", " "))
    if z == "+":
        total_data.append("is_discount")
    else:
        total_data.append("no_discount")

    total_data.append(tmp_napr)

    # total_data:[стру-рка данных, итоговая сумма, есть ли скидка, номера направлений]

    return total_data


def get_data_individual(card_object):
    """
    Получает на входе объект Карта
    возвращает словарь атрибутов по карте и Физ.лицу(Индивидуалу)
    :param card_object:
    :return:
    """
    ind_data = {}
    ind_data['ind'] = card_object.individual
    ind_data['age'] = ind_data['ind'].age()
    ind_data['doc'] = Document.objects.filter(individual=ind_data['ind'], is_active=True)
    ind_data['fio'] = ind_data['ind'].fio()
    ind_data['born'] = ind_data['ind'].bd()
    ind_data['main_address'] = "____________________________________________________" if not card_object.main_address \
        else card_object.main_address
    ind_data['fact_address'] = "____________________________________________________" if not card_object.fact_address \
        else card_object.fact_address

    #     document_passport = "Паспорт РФ"
    ind_documents = get_all_doc(ind_data['doc'])
    ind_data['passport_num'] = ind_documents['passport']['num']
    ind_data['passport_serial'] = ind_documents['passport']['serial']
    ind_data['passport_date_start'] = ind_documents['passport']['date_start']
    ind_data['passport_issued'] = ind_documents['passport']['issued']

    ind_data['bc_num'] = ind_documents['bc']['num']
    ind_data['bc_serial'] = ind_documents['bc']['serial']
    ind_data['bc_date_start'] = ind_documents['bc']['date_start']
    ind_data['bc_issued'] = ind_documents['bc']['issued']

    ind_data['snils'] = ind_documents["snils"]["num"]
    ind_data['oms'] = {}
    ind_data['oms']['polis_num'] = ind_documents["polis"]["num"]
    ind_data['oms']['polis_serial'] = ind_documents["polis"]["serial"]
    # ind_data['oms']['polis_date_start'] = ind_documents["polis"]["date_start"]
    ind_data['oms']['polis_issued'] = ind_documents["polis"]["issued"]

    return ind_data


def form_notfound():
    """
    В случае не верной настройки форм по типам и функциям или переданным аргументам в параметры
    :return:
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from copy import deepcopy
    from reportlab.lib.enums import TA_CENTER
    import os.path
    from io import BytesIO
    from laboratory.settings import FONTS_FOLDER

    buffer = BytesIO()
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=10 * mm,
                            rightMargin=10 * mm, topMargin=10 * mm,
                            bottomMargin=10 * mm, allowSplitting=1,
                            title="Форма {}".format("Паспорт здоровья"))
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifBold"
    style.fontSize = 16
    style.leading = 15
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER

    objs = [
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifBold">Ая-я-я-я-я-я-я-яй!</font>',
                  styleCenter),
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifBold">Что-то Администраторы не верно настроили с типами форм! </font>',
                  styleCenter),
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifBold">А-та-та-та им!</font>',
                  styleCenter),
    ]
    doc.build(objs)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def get_doc_results(doc_obj, date_result):
    """
    возвращает результаты врача за определенную дату. ***** Ни в коем случае не переделывать на диапозон дат
    """
    doc_results = Issledovaniya.objects.filter(doc_confirmation=doc_obj, time_confirmation__date=date_result)
    return doc_results


def get_finaldata_talon(doc_result_obj):
    """
    Вход результаты врача за определенную дату
    Выход: стр-ра данных {'№п.п':'номер',	'ФИО пациента':'Иванов Иван Иванович',	'№ карты (тип)':'1212 (L2)',
                          'Данные полиса':'номер;Компаня', 'цель посещения': '(код)', 'первичны прием':'Нет',
                          'Диагноз по МКБ': '(код)',	'Впервые':'Да',	'Результат обращения':'код',
                          'Исход':'Код',	'Д-стоит':'коды', 'Д-взят':'коды', 'Д-снят':'коды'
						  'причина снятия':'', 'Онкоподозрение':'Да'

    """
    fin_oms = 'омс'
    fin_dms = 'дмс'
    fin_pay = 'платно'
    fin_medexam = 'медосмотр'

    fin_source = OrderedDict()
    fin_source[fin_oms] = OrderedDict()
    fin_source[fin_pay] = OrderedDict()
    fin_source[fin_dms] = OrderedDict()
    fin_source[fin_medexam] = OrderedDict()

    oms_count = 0
    dms_count = 0
    pay_count = 0
    medexam_count = 0
    empty = '-'
    today = datetime.datetime.now().date()
    print(today)

    for i in doc_result_obj:
        napr_attr = Napravleniya.get_attr(i.napravleniye)
        temp_dict = OrderedDict()
        dict_fsourcce = ''
        order = ''
        if napr_attr['istochnik_f'] == 'омс':
            oms_count += 1
            dict_fsourcce = fin_oms
            order = oms_count
        elif napr_attr['istochnik_f'] == 'платно':
            pay_count += 1
            dict_fsourcce = fin_pay
            order = pay_count
        elif napr_attr['istochnik_f'] == 'дмс':
            dms_count += 1
            dict_fsourcce = fin_dms
            order = dms_count
        elif napr_attr['istochnik_f'] == 'медосмотр':
            medexam_count += 1
            dict_fsourcce = fin_medexam
            order = medexam_count
        else:
            continue
        polis_who_giv = empty if not napr_attr['polis_who_give'] else napr_attr['polis_who_give']
        temp_dict['client_fio'] = napr_attr['client_fio'] + ', ' + str(i.napravleniye.pk)
        temp_dict['client_bd'] = napr_attr['client_bd']
        temp_dict['card_num'] = napr_attr['card_num']
        temp_dict['polis_data'] = '<u>'+napr_attr['polis_n']+'</u>' + '<br/>' +  polis_who_giv
        temp_dict['purpose'] = empty if not i.purpose else i.purpose
        temp_dict['is_first_reception'] = 'Да' if i.research.is_first_reception else 'Нет'
        temp_dict['diagnos'] = empty if not i.diagnos else i.diagnos
        temp_dict['first_time'] = 'Да' if i.first_time else 'Нет'
        temp_dict['result_reception'] = empty if not i.result_reception else i.result_reception
        temp_dict['outcome_illness'] = empty if not i.outcome_illness else i.outcome_illness

        #Данные Д-учета
        disp = DispensaryReg.objects.filter(Q(card=i.napravleniye.client),(Q(date_end=None)| Q(date_end=today)))
        d_stand = []
        d_take = []
        d_stop = []
        d_whystop = []
        if disp:
            for d in disp:
                if d.date_end == None and d.date_start != i.time_confirmation.date():
                    d_stand.append(d.diagnos)
                elif d.date_end == None and d.date_start == i.time_confirmation.date():
                    d_take.append(d.diagnos)
                elif d.date_end == i.time_confirmation.date():
                    d_stop.append(d.diagnos)
                    d_whystop.append(d.why_stop)

        temp_dict['d_stand'] = '' if not d_stand else ', '.join(d_stand)
        temp_dict['d_take'] = '' if not d_take else ', '.join(d_take)
        temp_dict['d_stop'] = '' if not d_stand else ', '.join(d_stop)
        temp_dict['d_whystop'] = '' if not d_whystop else ', '.join(d_whystop)
        temp_dict['maybe_onco'] = 'Да' if i.maybe_onco else ''
        fin_source[dict_fsourcce].update({order: temp_dict})

    return fin_source
