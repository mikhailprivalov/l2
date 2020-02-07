from collections import OrderedDict
from copy import deepcopy
from decimal import Decimal

from django.db.models import Q

from clients.models import Document, DispensaryReg
from directions.models import Napravleniya, Issledovaniya
from directory.models import Researches
from laboratory import utils
from laboratory.utils import strdate
from api.stationar.stationar_func import hosp_get_data_direction, check_transfer_epicrisis
from api.stationar.sql_func import get_result_value_iss
from utils.dates import normalize_date


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
    # is_discount = False
    z = ""
    x = ""
    tmp_napr = []
    for k, v in research_price_loc.items():
        # research_attr = ([s for s in Researches.objects.filter(id__in=v.keys()).values_list('id', 'title')])
        research_attr = (
            [s for s in Researches.objects.filter(id__in=v.keys()).values_list('id', 'title', 'internal_code')])
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
                    h.extend([j[2], j[1]])
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
    ind_data = {'ind': card_object.individual}
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
    doc_results = Issledovaniya.objects.filter(doc_confirmation=doc_obj, time_confirmation__date=date_result, napravleniye__isnull=False)
    return doc_results


def get_finaldata_talon(doc_result_obj):
    """
    Вход результаты врача за определенную дату
    Выход: стр-ра данных {'№п.п':'номер', 'ФИО пациента':'Иванов Иван Иванович', '№ карты (тип)':'1212 (L2)',
                          'Данные полиса':'номер;Компаня', 'цель посещения': '(код)', 'первичны прием':'Нет',
                          'Диагноз по МКБ': '(код)', 'Впервые':'Да', 'Результат обращения':'код',
                          'Исход':'Код', 'Д-стоит':'коды', 'Д-взят':'коды', 'Д-снят':'коды'
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

    fin_source_iss = OrderedDict()
    fin_source_iss[fin_oms] = OrderedDict()
    fin_source_iss[fin_pay] = OrderedDict()
    fin_source_iss[fin_dms] = OrderedDict()
    fin_source_iss[fin_medexam] = OrderedDict()

    oms_count = 0
    dms_count = 0
    pay_count = 0
    medexam_count = 0
    empty = '-'
    today = utils.timezone.now().date()

    for i in doc_result_obj:
        napr_attr = Napravleniya.get_attr(i.napravleniye)
        temp_dict = OrderedDict()
        temp_dict_iss = OrderedDict()
        dict_fsourcce = ''
        order = ''
        if napr_attr['istochnik_f'] in ['омс', '']:
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
        polis_num = empty if not napr_attr['polis_n'] else napr_attr['polis_n']

        temp_dict['client_fio'] = napr_attr['client_fio'] + ', ' + napr_attr['client_bd']
        temp_dict['med_exam'] = strdate(i.medical_examination) + ', ' + str(i.napravleniye_id)
        num_poliklinika = f'\n({napr_attr["number_poliklinika"]})' if napr_attr['number_poliklinika'] else ''
        temp_dict['card_num'] = napr_attr['card_num'] + num_poliklinika
        temp_dict['polis_data'] = '<u>' + polis_num + '</u>' + '<br/>' + polis_who_giv

        temp_dict_iss = temp_dict.copy()
        temp_dict_iss['research_code'] = i.research.code
        temp_dict_iss['research_title'] = i.research.title

        temp_dict['purpose'] = empty if not i.purpose else i.purpose
        temp_dict['is_first_reception'] = 'Да' if i.research.is_first_reception else 'Нет'
        temp_dict['diagnos'] = empty if not i.diagnos else i.diagnos
        temp_dict['first_time'] = 'Да' if i.first_time else 'Нет'
        temp_dict['result_reception'] = empty if not i.result_reception else i.result_reception
        temp_dict['outcome_illness'] = empty if not i.outcome_illness else i.outcome_illness

        # Данные Д-учета
        disp = DispensaryReg.objects.filter(Q(card=i.napravleniye.client), (Q(date_end=None) | Q(date_end=today)))
        d_stand = []
        d_take = []
        d_stop = []
        d_whystop = []
        if disp:
            for d in disp:
                if d.date_end is None and d.date_start != i.time_confirmation.date():
                    d_stand.append(d.diagnos)
                elif d.date_end is None and d.date_start == i.time_confirmation.date():
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
        fin_source_iss[dict_fsourcce].update({order: temp_dict_iss})

        if Issledovaniya.objects.filter(parent=i).exists():
            temp_dict_iss_copy = deepcopy(temp_dict_iss)
            add_iss_dict = OrderedDict()
            for iss in Issledovaniya.objects.filter(parent=i):
                temp_dict_iss_copy['research_code'] = iss.research.code
                temp_dict_iss_copy['research_title'] = iss.research.title
                order = Decimal(str(order)) + Decimal('0.1')
                add_iss_dict[order] = deepcopy(temp_dict_iss_copy)
            fin_source_iss[dict_fsourcce].update(add_iss_dict)

    return [fin_source, fin_source_iss]


def primary_reception_get_data(hosp_first_num):
    # Получение данных из певичного приема
    hosp_primary_receptions = hosp_get_data_direction(hosp_first_num, site_type=0, type_service='None', level=2)
    hosp_primary_iss, primary_research_id = None, None
    if hosp_primary_receptions:
        hosp_primary_iss = hosp_primary_receptions[0].get('iss')
        primary_research_id = hosp_primary_receptions[0].get('research_id')

    titles_field = ['Дата поступления', 'Время поступления', 'Виды транспортировки',
                    'Побочное действие лекарств (непереносимость)', 'Кем направлен больной',
                    'Вид госпитализации',
                    'Время через, которое доставлен после начала заболевания, получения травмы',
                    'Диагноз направившего учреждения', 'Диагноз при поступлении', 'Госпитализирован по поводу данного заболевания']
    list_values = None
    if titles_field and hosp_primary_receptions:
        list_values = get_result_value_iss(hosp_primary_iss, primary_research_id, titles_field)

    date_entered_value, time_entered_value, type_transport, medicament_allergy = '', '', '', ''
    who_directed, plan_hospital, extra_hospital, type_hospital = '', '', '', ''
    time_start_ill, diagnos_who_directed, diagnos_entered = '', '', ''
    what_time_hospitalized = ''

    if list_values:
        for i in list_values:
            if i[3] == 'Дата поступления':
                date_entered_value = normalize_date(i[2])
                continue
            if i[3] == 'Время поступления':
                time_entered_value = i[2]
                continue
            if i[3] == 'Виды транспортировки':
                type_transport = i[2]
                continue
            if i[3] == 'Побочное действие лекарств (непереносимость)':
                medicament_allergy = i[2]
                continue
            if i[3] == 'Кем направлен больной':
                who_directed = i[2]
                continue
            if i[3] == 'Вид госпитализации':
                type_hospital = i[2]
            if type_hospital == 'Экстренная':
                time_start_ill_obj = get_result_value_iss(hosp_primary_iss, primary_research_id, ['Время через, которое доставлен после начала заболевания, получения травмы'])
                if time_start_ill_obj:
                    time_start_ill = time_start_ill_obj[0][2]
                extra_hospital = "Да"
                plan_hospital = "Нет"
            else:
                plan_hospital = "Да"
                extra_hospital = "Нет"
                time_start_ill = ''
            if i[3] == 'Диагноз направившего учреждения':
                diagnos_who_directed = i[2]
                continue
            if i[3] == 'Диагноз при поступлении':
                diagnos_entered = i[2]
                continue
            if i[3] == 'Госпитализирован по поводу данного заболевания':
                what_time_hospitalized = i[2]
                continue

    # return (date_entered_value, time_entered_value, type_transport, medicament_allergy, who_directed, plan_hospital, extra_hospital, type_hospital,
    #         time_start_ill, diagnos_who_directed, diagnos_entered, what_time_hospitalized,)
    return {'date_entered_value':date_entered_value, 'time_entered_value':time_entered_value, 'type_transport':type_transport,
            'medicament_allergy':medicament_allergy, 'who_directed':who_directed, 'plan_hospital':plan_hospital, 'extra_hospital':extra_hospital,
            'type_hospital':type_hospital, 'time_start_ill':time_start_ill, 'diagnos_who_directed':diagnos_who_directed,
            'diagnos_entered':diagnos_entered, 'what_time_hospitalized':what_time_hospitalized}


def hosp_extract_get_data(hosp_last_num):
    # Получение данных из выписки
    hosp_extract = hosp_get_data_direction(hosp_last_num, site_type=7, type_service='None', level=2)
    hosp_extract_iss, extract_research_id = None, None
    if hosp_extract:
        hosp_extract_iss = hosp_extract[0].get('iss')
        if not Issledovaniya.objects.get(pk=hosp_extract_iss).doc_confirmation:
            return {}
        extract_research_id = hosp_extract[0].get('research_id')
    titles_field = ['Время выписки', 'Дата выписки', 'Основной диагноз (описание)',
                    'Осложнение основного диагноза (описание)', 'Сопутствующий диагноз (описание)', 'Исход заболевания',
                    'Код по МКБ10']
    list_values = None
    if titles_field and hosp_extract:
        list_values = get_result_value_iss(hosp_extract_iss, extract_research_id, titles_field)
    date_value, time_value = '', ''
    final_diagnos, other_diagnos, near_diagnos, outcome, final_diagnos_mkb = '', '', '', '',''

    if list_values:
        for i in list_values:
            if i[3] == 'Дата выписки':
                date_value = normalize_date(i[2])
            if i[3] == 'Время выписки':
                time_value = i[2]
            if i[3] == 'Основной диагноз (описание)':
                final_diagnos = i[2]
            if i[3] == 'Осложнение основного диагноза (описание)':
                other_diagnos = i[2]
            if i[3] == 'Сопутствующий диагноз (описание)':
                near_diagnos = i[2]
            if i[3] == 'Исход заболевания':
                outcome = i[2]
            if i[3] == 'Код по МКБ10':
                final_diagnos_mkb = str(i[2]).split(' ')[0]

    return {'date_value':date_value, 'time_value':time_value, 'final_diagnos':final_diagnos, 'other_diagnos':other_diagnos, 'near_diagnos':near_diagnos,
            'outcome':outcome, 'final_diagnos_mkb':final_diagnos_mkb, 'extract_iss':hosp_extract_iss}


def hosp_get_clinical_diagnos(hosp_first_num):
    hosp_day_entries = hosp_get_data_direction(hosp_first_num, site_type=1, type_service='None', level=-1)
    day_entries_iss = []
    day_entries_research_id = None
    if hosp_day_entries:
        for i in hosp_day_entries:
            # найти дневники совместно с заведующим
            if i.get('research_title').find('заведующ') != -1:
                day_entries_iss.append(i.get('iss'))
                if not day_entries_research_id:
                    day_entries_research_id = i.get('research_id')

    titles_field = ['Диагноз клинический', 'Дата установления диагноза']
    list_values = []
    if titles_field and day_entries_iss:
        for i in day_entries_iss:
            list_values.append(get_result_value_iss(i, day_entries_research_id, titles_field))
    s = []
    if list_values:
        for i in list_values:
            if (i[1][3]).find('Дата установления диагноза') != -1:
                date_diag = normalize_date(i[1][2])
                if date_diag and i[0][2]:
                    s.append(i[0][2] + '; дата:' + date_diag)
            elif (i[0][3]).find('Дата установления диагноза') != -1:
                date_diag = normalize_date(i[0][2])
                if date_diag and i[1][2]:
                    s.append(i[1][2] + '; дата:' + str(date_diag))
    clinic_diagnos = ''
    if len(s) > 0:
        clinic_diagnos = s.pop()

    return clinic_diagnos


def hosp_get_transfers_data(hosp_nums_obj):
    titles_field = ['Дата перевода', 'Время перевода']
    date_transfer_value, time_transfer_value = '', ''
    transfers = []
    list_values = None
    for i in range(len(hosp_nums_obj)):
        if i == 0:
            continue

        transfer_research_title = hosp_nums_obj[i].get('research_title')
        # получить для текущего hosp_dir эпикриз с title - перевод.....
        from_hosp_dir_transfer = hosp_nums_obj[i - 1].get('direction')
        epicrisis_data = hosp_get_data_direction(from_hosp_dir_transfer, site_type=6, type_service='None', level=2)
        if epicrisis_data:
            result_check = check_transfer_epicrisis(epicrisis_data)
            if result_check['iss']:
                iss_transfer, research_id_transfer = result_check['iss'], result_check['research_id']
                if titles_field and iss_transfer:
                    list_values = get_result_value_iss(iss_transfer, research_id_transfer, titles_field)
            else:
                continue
        if list_values:
            for i in list_values:
                if i[3] == 'Дата перевода':
                    date_transfer_value = normalize_date(i[2])
                    continue
                if i[3] == 'Время перевода':
                    time_transfer_value = i[2]
                    continue

        transfers.append({'transfer_research_title':transfer_research_title, 'date_transfer_value':date_transfer_value, 'time_transfer_value':time_transfer_value})

    return transfers


def hosp_patient_movement(hosp_nums_obj):
    titles_field = ['Дата перевода']
    patient_movement = []
    list_values = None

    for i in range(len(hosp_nums_obj)):
        date_out, diagnos_mkb, doc_confirm_code = '', '', ''
        bed_profile_research_title = hosp_nums_obj[i].get('research_title')
        hosp_dir = hosp_nums_obj[i].get('direction')
        primary_reception_data = primary_reception_get_data(hosp_dir)
        hosp_extract_data = hosp_get_data_direction(hosp_dir, site_type=7, type_service='None', level=2)
        if hosp_extract_data:
            extract_data = hosp_extract_get_data(hosp_dir)
            if extract_data:
                date_out = extract_data['date_value']
                diagnos_mkb = extract_data['final_diagnos_mkb']
                doc_confirm_code = Issledovaniya.objects.get(pk=extract_data['extract_iss']).doc_confirmation.personal_code

        epicrisis_data = hosp_get_data_direction(hosp_dir, site_type=6, type_service='None', level=2)
        if epicrisis_data:
            result_check = check_transfer_epicrisis(epicrisis_data)
            if result_check['iss']:
                iss_transfer, research_id_transfer = result_check['iss'], result_check['research_id']
                if titles_field and iss_transfer:
                    list_values = get_result_value_iss(iss_transfer, research_id_transfer, titles_field)
            else:
                continue
        if list_values:
            for i in list_values:
                if i[3] == 'Дата перевода':
                    date_out = normalize_date(i[2])
                if i[3] == 'Клинический диагноз по МКБ':
                    diagnos_mkb = i[2]

#TODO: проверить подтверждение переводного эпикриза

        patient_movement.append({'bed_profile_research_title':bed_profile_research_title, 'date_entered_value':primary_reception_data['date_entered_value'],
                                'date_oute':date_out, 'diagnos_mkb':diagnos_mkb, 'doc_confirm_code':doc_confirm_code})

    return patient_movement
