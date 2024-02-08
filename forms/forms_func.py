import datetime
import zlib
from collections import OrderedDict
from copy import deepcopy
from decimal import Decimal

from django.db.models import Q

from clients.models import Document, DispensaryReg, Card
from directions.models import Napravleniya, Issledovaniya, ParaclinicResult, IstochnikiFinansirovaniya, PersonContract
from directory.models import Researches
from laboratory import utils
from laboratory.settings import MEDEXAM_FIN_SOURCE_TITLE
from laboratory.utils import strdate
from api.stationar.stationar_func import hosp_get_data_direction, check_transfer_epicrisis
from api.stationar.sql_func import get_result_value_iss
from utils.dates import normalize_date
import json


def get_all_doc(docs: [Document]):
    """
    Возвращает словарь словарей documents. Данные о документах: паспорт : номер: серия, полис: номер, снислс: номер
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
            d = {
                r: [
                    s,
                    d,
                    h,
                ]
                for r, s, d, h in Issledovaniya.objects.filter(napravleniye=k, research__in=v, coast__isnull=False).values_list('research_id', 'coast', 'discount', 'how_many')
            }
            dict_coast[k] = d
        return dict_coast
    else:
        return 0


def get_research_by_dir(dir_temp_l, only_new=True):
    """
    Получить словаь: {направление1:[услуга1, услуга2, услуга3],направление2:[услуга1].....}
    :param dir_temp_l:
    :return:
    """
    dict_research_dir = {}
    for i in dir_temp_l:
        # Если есть хотя бы одно сохранения услуги по направлению, то не учитывается
        if only_new and any([x.doc_save is not None for x in Issledovaniya.objects.filter(napravleniye=i)]):
            continue
        else:
            research_l = [x.research_id for x in Issledovaniya.objects.filter(napravleniye=i)]
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
        research_attr = [s for s in Researches.objects.filter(id__in=v.keys()).values_list('id', 'title', 'internal_code', 'short_title')]
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
                    res_obj = Researches.objects.get(pk=research_id)
                    h.append(res_obj.paraclinic_info)
                    h[0], h[1] = h[1], h[0]
                    total_sum += research_sum
                    h.append(j[3])
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
    возвращает словарь атрибутов по карте и Физ.лицу (Индивидуалу)
    :param card_object:
    :return:
    """
    ind_data = {'ind': card_object.individual}
    ind_data['age'] = ind_data['ind'].age()
    ind_data['doc'] = Document.objects.filter(individual=ind_data['ind'], is_active=True)
    ind_data['fio'] = ind_data['ind'].fio()
    ind_data['born'] = ind_data['ind'].bd()
    ind_data['main_address'] = "____________________________________________________" if not card_object.main_address else card_object.main_address
    ind_data['fact_address'] = "____________________________________________________" if not card_object.fact_address else card_object.fact_address

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
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=10 * mm, rightMargin=10 * mm, topMargin=10 * mm, bottomMargin=10 * mm, allowSplitting=1, title="Форма {}".format("Паспорт здоровья")
    )
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
        Paragraph('<font face="PTAstraSerifBold">Ая-я-я-я-я-я-я-яй!</font>', styleCenter),
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifBold">Что-то Администраторы не верно настроили с типами форм! </font>', styleCenter),
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifBold">А-та-та-та им!</font>', styleCenter),
    ]
    doc.build(objs)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def get_doc_results(doc_obj, date_result):
    """
    Возвращает результаты врача за определенную дату. ***** Ни в коем случае не переделывать на диапозон дат
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
    fin_medexam = MEDEXAM_FIN_SOURCE_TITLE
    fin_disp = 'диспансеризация'
    fin_budget = 'бюджет'

    fin_source = OrderedDict()
    fin_source[fin_oms] = OrderedDict()
    fin_source[fin_pay] = OrderedDict()
    fin_source[fin_dms] = OrderedDict()
    fin_source[fin_medexam] = OrderedDict()
    fin_source[fin_disp] = OrderedDict()
    fin_source[fin_budget] = OrderedDict()

    fin_source_iss = OrderedDict()
    fin_source_iss[fin_oms] = OrderedDict()
    fin_source_iss[fin_pay] = OrderedDict()
    fin_source_iss[fin_dms] = OrderedDict()
    fin_source_iss[fin_medexam] = OrderedDict()
    fin_source_iss[fin_disp] = OrderedDict()
    fin_source_iss[fin_budget] = OrderedDict()

    oms_count = 0
    dms_count = 0
    pay_count = 0
    disp_count = 0
    medexam_count = 0
    budget_count = 0
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
        elif napr_attr['istochnik_f'] == MEDEXAM_FIN_SOURCE_TITLE:
            medexam_count += 1
            dict_fsourcce = fin_medexam
            order = medexam_count
        elif napr_attr['istochnik_f'] == 'диспансеризация':
            disp_count += 1
            dict_fsourcce = fin_disp
            order = disp_count
        elif napr_attr['istochnik_f'] == 'бюджет':
            budget_count += 1
            dict_fsourcce = fin_budget
            order = budget_count
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
                    date_start = strdate(d.date_start, short_year=True)
                    date_start = normalize_date(date_start)
                    d_stand.append(f'{d.diagnos}<br/>{date_start}<br/>')
                elif d.date_end is None and d.date_start == i.time_confirmation.date():
                    d_take.append(d.diagnos)
                elif d.date_end == i.time_confirmation.date():
                    d_stop.append(d.diagnos)
                    d_whystop.append(d.why_stop)

        temp_dict['d_stand'] = '' if not d_stand else ''.join(d_stand)
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


def primary_reception_get_data(hosp_first_num, site_type=0):
    # Получение данных из певичного приема
    hosp_primary_receptions = hosp_get_data_direction(hosp_first_num, site_type=site_type, type_service='None', level=2)
    hosp_primary_iss, primary_research_id = None, None
    if hosp_primary_receptions:
        hosp_primary_iss = hosp_primary_receptions[0].get('iss')
        primary_research_id = hosp_primary_receptions[0].get('research_id')

    titles_field = [
        'Дата поступления',
        'Время поступления',
        'Виды транспортировки',
        'Побочное действие лекарств (непереносимость)',
        'Кем направлен больной',
        'Вид госпитализации',
        'Время через, которое доставлен после начала заболевания, получения травмы',
        'Диагноз направившего учреждения',
        'Диагноз при поступлении',
        'Госпитализирован по поводу данного заболевания',
        'Общее состояние',
        'Социальный статус',
        'Категория льготности',
        'Всего госпитализаций',
        'Вид травмы',
        'Группа крови',
        'Резус принадлежность',
        'Вес',
        'Основной диагноз (описание)',
        'Основной диагноз по МКБ',
        'Осложнение основного диагноза (описание)',
        'Осложнение основного диагноза по МКБ',
        'Сопутствующий диагноз (описание)',
        'Сопутствующий диагноз по МКБ',
        'Номер направления',
        'Дата направления',
        'Госпитализирован по поводу данного заболевания',
        'Диагноз при направлении',
        'Код МКБ при направлении',
        'Предварительный диагноз при поступлении',
        'Основное заболевание код по МКБ',
        'Осложнения основного заболевания код по МКБ',
        'Сопутствующие заболевания код по МКБ',
        'Внешняя причина при травмах, отравлениях код по МКБ',
        'Дополнительные сведения о заболевании',
        'туберкулез',
        'ВИЧ-инфекция',
        'вирусные гепатиты',
        'сифилис',
        'COVID-19',
        'осмотр на педиклез, чесотку',
        'результат осмотра',
        'Аллергические реакции',
        'Дата установления диагноза',
        'Время установления диагноза',
        'Кому доверяю',
    ]
    list_values = None
    if titles_field and hosp_primary_receptions:
        list_values = get_result_value_iss(hosp_primary_iss, primary_research_id, titles_field)

    date_entered_value, time_entered_value, type_transport, medicament_allergy = '', '', '', ''
    who_directed, plan_hospital, extra_hospital, type_hospital = '', '', '', ''
    time_start_ill, diagnos_who_directed, diagnos_entered = '', '', ''
    what_time_hospitalized, state, social_status, category_privilege = '', '', '', ''
    all_hospitalized, type_trauma, blood_group, resus_factor = '', '', '', ''
    weight = ''
    final_diagnos, other_diagnos, near_diagnos, final_diagnos_mkb, other_diagnos_mkb, near_diagnos_mkb = '', '', '', '', '', ''
    ext_direction_number, ext_direction_date, direction_diagnos, direction_mkb_diagnos = "", "", "", ""
    external_reason_mkb, additional_data_ill = "", ""
    tuberculosis, hiv_infection, viral_infections, covid19, syphilis, pediculosis, result_pediculosis_exam = "", "", "", "", "", "", ""
    allergic_reactions, preliminary_diagnosis = "", ""
    date_diagnosis, time_diagnosis = "", ""
    whom_transfer_health_data = ""

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
            if type_hospital.lower() == 'экстренная':
                time_start_ill_obj = get_result_value_iss(hosp_primary_iss, primary_research_id, ['Время через, которое доставлен после начала заболевания, получения травмы'])
                if time_start_ill_obj:
                    time_start_ill = time_start_ill_obj[0][2]
                extra_hospital = "Да"
                plan_hospital = "Нет"
            else:
                plan_hospital = "Да"
                extra_hospital = "Нет"
            if i[3] == 'Диагноз направившего учреждения':
                diagnos_who_directed = i[2]
                continue
            if i[3] == 'Диагноз при поступлении':
                diagnos_entered = i[2]
                continue
            if i[3] == 'Госпитализирован по поводу данного заболевания':
                what_time_hospitalized = i[2]
                continue
            if i[3] == 'Общее состояние':
                state = i[2]
                continue
            if i[3] == 'Социальный статус':
                social_status = i[2]
                continue
            if i[3] == 'Категория льготности':
                category_privilege = i[2]
                continue
            if i[3] == 'Всего госпитализаций':
                all_hospitalized = i[2]
                continue
            if i[3] == 'Вид травмы':
                type_trauma = i[2]
                continue
            if i[3] == 'Группа крови':
                blood_group = i[2]
                continue
            if i[3] == 'Резус принадлежность':
                resus_factor = i[2]
                continue
            if i[3] == 'Вес':
                weight = i[2]
                continue
            if i[3] == 'Основной диагноз (описание)':
                final_diagnos = i[2]
            if i[3] == 'Осложнение основного диагноза (описание)':
                other_diagnos = i[2]
            if i[3] == 'Сопутствующий диагноз (описание)':
                near_diagnos = i[2]
            if i[3] == 'Основной диагноз по МКБ':
                final_diagnos_mkb = str(i[2])
            if i[3] == 'Осложнение основного диагноза по МКБ':
                other_diagnos_mkb = str(i[2]).split(' ')[0]
            if i[3] == 'Сопутствующий диагноз по МКБ':
                near_diagnos_mkb = str(i[2]).split(' ')[0]
            if i[3] == 'Время через, которое доставлен после начала заболевания, получения травмы':
                time_start_ill = i[2]
            if i[3] == 'Номер направления':
                ext_direction_number = i[2]
            if i[3] == 'Дата направления':
                ext_direction_date = i[2]
            if i[3] == 'Диагноз при направлении':
                direction_diagnos = i[2]
            if i[3] == 'Код МКБ при направлении':
                direction_mkb_diagnos = str(i[2])
            if i[3] == 'Предварительный диагноз при поступлении':
                preliminary_diagnosis = i[2]

            if i[3] == "Основное заболевание код по МКБ":
                final_diagnos_mkb_data = i[2]
                final_diagnos_mkb_details = {}
                if final_diagnos_mkb_data:
                    try:
                        final_diagnos_mkb_details = json.loads(final_diagnos_mkb_data)
                    except:
                        final_diagnos_mkb_details = {}
                final_diagnos_mkb_row = final_diagnos_mkb_details.get("rows", [])
                final_diagnos_mkb = []
                for rr in final_diagnos_mkb_row:
                    final_diagnos_mkb.append({"code": json.loads(rr[0]).get('code', ''), "data": f"{json.loads(rr[0]).get('title', '')} ({rr[1]})"})
            if i[3] == "Осложнения основного заболевания код по МКБ":
                other_diagnos_mkb_data = i[2]
                other_diagnos_mkb_details = {}
                if other_diagnos_mkb_data:
                    try:
                        other_diagnos_mkb_details = json.loads(other_diagnos_mkb_data)
                    except:
                        other_diagnos_mkb_details = {}
                other_diagnos_mkb_row = other_diagnos_mkb_details.get("rows", [])
                other_diagnos_mkb = []
                for rr in other_diagnos_mkb_row:
                    other_diagnos_mkb.append({"code": json.loads(rr[0]).get('code', ''), "data": f"{json.loads(rr[0]).get('title', '')} ({rr[1]})"})
            if i[3] == 'Сопутствующие заболевания код по МКБ':
                near_diagnos_mkb_data = i[2]
                near_diagnos_mkb_details = {}
                if near_diagnos_mkb_data:
                    try:
                        near_diagnos_mkb_details = json.loads(near_diagnos_mkb_data)
                    except:
                        near_diagnos_mkb_details = {}
                near_diagnos_mkb_row = near_diagnos_mkb_details.get("rows", [])
                near_diagnos_mkb = []
                for rr in near_diagnos_mkb_row:
                    near_diagnos_mkb.append({"code": json.loads(rr[0]).get('code', ''), "data": f"{json.loads(rr[0]).get('title', '')}. {rr[1] if len(rr) > 1 else '' }"})
            if i[3] == 'Внешняя причина при травмах, отравлениях код по МКБ':
                external_reason_mkb_data = i[2]
                external_reason_mkb_details = {}
                if external_reason_mkb_data:
                    try:
                        external_reason_mkb_details = json.loads(external_reason_mkb_data)
                    except:
                        external_reason_mkb_details = {}
                external_reason_mkb_row = external_reason_mkb_details.get("rows", [])
                external_reason_mkb = []
                if len(external_reason_mkb_row) > 0:
                    for rr in external_reason_mkb_row:
                        adds_data = rr[1] if len(rr) > 1 else ""
                        external_reason_mkb.append({"code": json.loads(rr[0]).get('code', ''), "data": f"{json.loads(rr[0]).get('title', '')} ({adds_data})"})
            if i[3] == 'Дополнительные сведения о заболевании':
                additional_data_ill = i[2]
            if i[3] == 'туберкулез':
                tuberculosis = i[2]
            if i[3] == 'ВИЧ-инфекция':
                hiv_infection = i[2]
            if i[3] == 'вирусные гепатиты':
                viral_infections = i[2]
            if i[3] == 'COVID-19':
                covid19 = i[2]
            if i[3] == 'сифилис':
                syphilis = i[2]
            if i[3] == 'осмотр на педиклез, чесотку':
                pediculosis = i[2]
            if i[3] == 'результат осмотра':
                result_pediculosis_exam = i[2]
            if i[3] == "Аллергические реакции":
                allergic_reactions = i[2]
            if i[3] == "Дата установления диагноза":
                date_diagnosis = normalize_date(i[2])
            if i[3] == "Время установления диагноза":
                time_diagnosis = i[2]
            if i[3] == "Кому доверяю":
                whom_transfer_health_data = i[2]

    return {
        'date_entered_value': date_entered_value,
        'time_entered_value': time_entered_value,
        'type_transport': type_transport,
        'medicament_allergy': medicament_allergy,
        'who_directed': who_directed,
        'plan_hospital': plan_hospital,
        'extra_hospital': extra_hospital,
        'type_hospital': type_hospital,
        'time_start_ill': time_start_ill,
        'diagnos_who_directed': diagnos_who_directed,
        'diagnos_entered': diagnos_entered,
        'what_time_hospitalized': what_time_hospitalized,
        'state': state,
        'social_status': social_status,
        'category_privilege': category_privilege,
        'all_hospitalized': all_hospitalized,
        'type_trauma': type_trauma,
        'blood_group': blood_group,
        'resus_factor': resus_factor,
        'weight': weight,
        'final_diagnos': final_diagnos,
        'other_diagnos': other_diagnos,
        'near_diagnos': near_diagnos,
        'final_diagnos_mkb': final_diagnos_mkb,
        'other_diagnos_mkb': other_diagnos_mkb,
        'near_diagnos_mkb': near_diagnos_mkb,
        'ext_direction_date': ext_direction_date,
        'ext_direction_number': ext_direction_number,
        'direction_diagnos': direction_diagnos,
        'direction_mkb_diagnos': direction_mkb_diagnos,
        'external_reason_mkb': external_reason_mkb,
        'additional_data_ill': additional_data_ill,
        'tuberculosis': tuberculosis,
        'hiv_infection': hiv_infection,
        'viral_infections': viral_infections,
        'covid19': covid19,
        'syphilis': syphilis,
        'pediculosis': pediculosis,
        'result_pediculosis_exam': result_pediculosis_exam,
        'allergic_reactions': allergic_reactions,
        'preliminary_diagnosis': preliminary_diagnosis,
        'date_diagnosis': date_diagnosis,
        'time_diagnosis': time_diagnosis,
        'whom_transfer_health_data': whom_transfer_health_data,
    }


def hosp_extract_get_data(hosp_last_num):
    # Получение данных из выписки
    hosp_extract = hosp_get_data_direction(hosp_last_num, site_type=7, type_service='None', level=2)
    if not hosp_extract:
        return {}
    hosp_extract_iss, extract_research_id, doc_confirm = None, None, None
    if hosp_extract:
        hosp_extract_iss = hosp_extract[0].get('iss')
        doc_confirm = Issledovaniya.objects.get(pk=hosp_extract_iss).doc_confirmation
        if not doc_confirm:
            return {}
        extract_research_id = hosp_extract[0].get('research_id')

    titles_field = [
        'Время выписки',
        'Дата выписки',
        'Основной диагноз (описание)',
        'Основной диагноз по МКБ',
        'Осложнение основного диагноза (описание)',
        'Осложнение основного диагноза по МКБ',
        'Сопутствующий диагноз (описание)',
        'Сопутствующий диагноз по МКБ',
        'Исход госпитализации',
        'Результат госпитализации',
        'Проведено койко-дней',
        'Заведующий отделением',
        'Палата №',
        'Основное заболевание код по МКБ',
        'Осложнения основного заболевания код по МКБ',
        'Сопутствующие заболевания код по МКБ',
        'Внешняя причина при травмах, отравлениях код по МКБ',
        'Дополнительные сведения о заболевании',
        'Куда переведен',
        'Отметка о выдаче листка нетрудоспособности',
        'Отметка о выдаче листка нетрудоспособности через врачебную комиссию',
    ]
    list_values = None
    if titles_field and hosp_extract:
        list_values = get_result_value_iss(hosp_extract_iss, extract_research_id, titles_field)
    date_value, time_value = '', ''
    final_diagnos, other_diagnos, near_diagnos, outcome, final_diagnos_mkb, other_diagnos_mkb, near_diagnos_mkb, additional_data_ill = '', '', '', '', '', '', '', ''
    days_count, result_hospital, manager_depart, room_num, transfer_to = '', '', '', '', ''
    ln_data, ln_vk_data, external_reason_mkb = '', '', ''
    final_diagnos_mkb_dict, other_diagnos_mkb_dict, near_diagnos_mkb_dict, external_reason_mkb_dict = [], [], [], []

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
            if i[3] == 'Исход госпитализации':
                outcome = i[2]
            if i[3] == 'Результат госпитализации':
                result_hospital = i[2]
            if i[3] == 'Основной диагноз по МКБ':
                final_diagnos_mkb = str(i[2])
            if i[3] == 'Осложнение основного диагноза по МКБ':
                other_diagnos_mkb = str(i[2]).split(' ')[0]
            if i[3] == 'Сопутствующий диагноз по МКБ':
                near_diagnos_mkb = str(i[2]).split(' ')[0]
            if i[3] == 'Проведено койко-дней':
                days_count = str(i[2])
            if i[3] == 'Заведующий отделением':
                manager_depart = str(i[2])
            if i[3] == 'Палата №':
                room_num = str(i[2])
            if i[3] == "Основное заболевание код по МКБ":
                final_diagnos_mkb_data = i[2]
                final_diagnos_mkb_details = {}
                if final_diagnos_mkb_data:
                    try:
                        final_diagnos_mkb_details = json.loads(final_diagnos_mkb_data)
                    except:
                        final_diagnos_mkb_details = {}
                final_diagnos_mkb_row = final_diagnos_mkb_details.get("rows", [])
                final_diagnos_mkb = []
                for rr in final_diagnos_mkb_row:
                    final_diagnos_mkb_dict.append({"code": json.loads(rr[0]).get('code', ''), "data": f"{json.loads(rr[0]).get('title', '')} ({rr[1]})"})
            if i[3] == "Осложнения основного заболевания код по МКБ":
                other_diagnos_mkb_data = i[2]
                other_diagnos_mkb_details = {}
                if other_diagnos_mkb_data:
                    try:
                        other_diagnos_mkb_details = json.loads(other_diagnos_mkb_data)
                    except:
                        other_diagnos_mkb_details = {}
                other_diagnos_mkb_row = other_diagnos_mkb_details.get("rows", [])
                other_diagnos_mkb = []
                for rr in other_diagnos_mkb_row:
                    other_diagnos_mkb_dict.append({"code": json.loads(rr[0]).get('code', ''), "data": f"{json.loads(rr[0]).get('title', '')} ({rr[1]})"})
            if i[3] == 'Сопутствующие заболевания код по МКБ':
                near_diagnos_mkb_data = i[2]
                near_diagnos_mkb_details = {}
                if near_diagnos_mkb_data:
                    try:
                        near_diagnos_mkb_details = json.loads(near_diagnos_mkb_data)
                    except:
                        near_diagnos_mkb_details = {}
                near_diagnos_mkb_row = near_diagnos_mkb_details.get("rows", [])
                near_diagnos_mkb = []
                for rr in near_diagnos_mkb_row:
                    near_diagnos_mkb_dict.append({"code": json.loads(rr[0]).get('code', ''), "data": f"{json.loads(rr[0]).get('title', '')}. {rr[1] if len(rr) > 1 else '' }"})
            if i[3] == 'Внешняя причина при травмах, отравлениях код по МКБ':
                external_reason_mkb_data = i[2]
                external_reason_mkb_details = {}
                if external_reason_mkb_data:
                    try:
                        external_reason_mkb_details = json.loads(external_reason_mkb_data)
                    except:
                        external_reason_mkb_details = {}
                external_reason_mkb_row = external_reason_mkb_details.get("rows", [])
                external_reason_mkb = []
                if len(external_reason_mkb_row) > 0:
                    for rr in external_reason_mkb_row:
                        adds_data = rr[1] if len(rr) > 1 else ""
                        external_reason_mkb_dict.append({"code": json.loads(rr[0]).get('code', ''), "data": f"{json.loads(rr[0]).get('title', '')} ({adds_data})"})
            if i[3] == 'Дополнительные сведения о заболевании':
                additional_data_ill = i[2]
            if i[3] == 'Куда переведен':
                transfer_to = i[2]
            if i[3] == 'Отметка о выдаче листка нетрудоспособности через врачебную комиссию':
                ln_vk_data = i[2]
            if i[3] == 'Отметка о выдаче листка нетрудоспособности':
                ln_data = i[2]

    doc_fio = doc_confirm.get_fio()
    return {
        'date_value': date_value,
        'time_value': time_value,
        'final_diagnos': final_diagnos,
        'other_diagnos': other_diagnos,
        'near_diagnos': near_diagnos,
        'outcome': outcome,
        'final_diagnos_mkb': final_diagnos_mkb,
        'other_diagnos_mkb': other_diagnos_mkb,
        'near_diagnos_mkb': near_diagnos_mkb,
        'external_reason_mkb': external_reason_mkb,
        'final_diagnos_mkb_dict': final_diagnos_mkb_dict,
        'other_diagnos_mkb_dict': other_diagnos_mkb_dict,
        'near_diagnos_mkb_dict': near_diagnos_mkb_dict,
        'external_reason_mkb_dict': external_reason_mkb_dict,
        'extract_iss': hosp_extract_iss,
        'days_count': days_count,
        'result_hospital': result_hospital,
        'doc_fio': doc_fio,
        'manager_depart': manager_depart,
        'room_num': room_num,
        'transfer_to': transfer_to,
        'ln_data': ln_data,
        'ln_vk_data': ln_vk_data,
        'additional_data_ill': additional_data_ill,
    }


def hosp_get_clinical_diagnos(hosp_obj):
    clinic_diagnos = ''
    tmp_clinic_diagnos = []
    for i in hosp_obj:
        hosp_diagnostic_epicris = hosp_get_data_direction(i['direction'], site_type=6, type_service='None', level=2)
        day_entries_iss = []
        day_entries_research_id = None
        if hosp_diagnostic_epicris:
            for i in hosp_diagnostic_epicris:
                # найти эпикризы диагностические
                if i.get('research_title').lower().find('диагностич') != -1:
                    day_entries_iss.append(i.get('iss'))
                    if not day_entries_research_id:
                        day_entries_research_id = i.get('research_id')
        titles_field = ['Диагноз клинический', 'Дата установления диагноза', 'Основной', 'Осложнение', 'Сопутствующий', 'Внешняя причина при травмах, отравлениях']
        list_values = []
        if titles_field and day_entries_iss:
            for i in day_entries_iss:
                list_values.append(get_result_value_iss(i, day_entries_research_id, titles_field))

        if list_values:
            for fields in list_values:
                clinical_data = {'clinic_diagnos': '', 'main_diagnos': '', 'other_diagnos': '', 'near_diagnos': '', 'date': '', 'foreign_reason': ''}
                for i in fields:
                    if i[3] == 'Дата установления диагноза':
                        clinical_data['date'] = normalize_date(i[2])
                        continue
                    if i[3] == 'Диагноз клинический':
                        clinical_data['clinic_diagnos'] = i[2]
                        continue
                    if i[3] == 'Основной':
                        clinical_data['main_diagnos'] = f"(Основной): {i[2]}"
                        continue
                    if i[3] == 'Осложнение':
                        clinical_data['other_diagnos'] = f"; (Осложнение): {i[2]}"
                        continue
                    if i[3] == 'Сопутствующий':
                        clinical_data['near_diagnos'] = f"; (Сопутствующий): {i[2]}"
                        continue
                    if i[3] == 'Внешняя причина при травмах, отравлениях':
                        clinical_data['foreign_reason'] = f"{i[2]}"
                        continue
                if clinical_data['date'] and (clinical_data['clinic_diagnos'] or clinical_data['main_diagnos']):
                    tmp_clinic_diagnos.append(clinical_data.copy())

    for i in tmp_clinic_diagnos:
        clinic_diagnos = f"{clinic_diagnos}{i['clinic_diagnos']} <u>{i['main_diagnos']}</u>{i['other_diagnos']}{i['near_diagnos']}; дата: {i['date']}<br/>"

    return clinic_diagnos, tmp_clinic_diagnos


def hosp_get_transfers_data(hosp_nums_obj):
    titles_field = ['Дата перевода', 'Время перевода']
    date_transfer_value, time_transfer_value = '', ''
    transfers = []
    list_values = None
    for i in range(len(hosp_nums_obj)):
        if i == 0:
            continue

        transfer_research_title = hosp_nums_obj[i].get('research_title')
        iss_data = Issledovaniya.objects.get(pk=hosp_nums_obj[i].get('issledovaniye'))
        transfer_depart = iss_data.hospital_department_override.title if iss_data.hospital_department_override else ""
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

        transfers.append(
            {'transfer_research_title': transfer_research_title, 'transfer_depart': transfer_depart, 'date_transfer_value': date_transfer_value, 'time_transfer_value': time_transfer_value}
        )

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
                doc_confirm_code = (
                    None if not Issledovaniya.objects.get(pk=extract_data['extract_iss']) else Issledovaniya.objects.get(pk=extract_data['extract_iss']).doc_confirmation.personal_code
                )

        list_values = None
        epicrisis_data = hosp_get_data_direction(hosp_dir, site_type=6, type_service='None', level=2)
        if epicrisis_data:
            result_check = check_transfer_epicrisis(epicrisis_data)
            if result_check['iss']:
                iss_transfer, research_id_transfer = result_check['iss'], result_check['research_id']
                if titles_field and iss_transfer:
                    list_values = get_result_value_iss(iss_transfer, research_id_transfer, titles_field)

        if list_values:
            for i in list_values:
                if i[3] == 'Дата перевода':
                    date_out = normalize_date(i[2])
                if i[3] == 'Клинический диагноз по МКБ':
                    diagnos_mkb = i[2]

        patient_movement.append(
            {
                'bed_profile_research_title': bed_profile_research_title,
                'date_entered_value': primary_reception_data['date_entered_value'],
                'date_oute': date_out,
                'diagnos_mkb': diagnos_mkb,
                'doc_confirm_code': doc_confirm_code,
            }
        )

    return patient_movement


def hosp_get_operation_data(num_dir):
    hosp_operation = hosp_get_data_direction(num_dir, site_type=3, type_service='None', level=-1)
    operation_iss_research = []
    if hosp_operation:
        for i in hosp_operation:
            # найти протоколы по типу операции
            if (i.get('research_title').lower().find('операци') != -1 or i.get('research_title').lower().find('манипул') != -1) and i['date_confirm']:
                operation_iss_research.append({'iss': i['iss'], 'research': i['research_id']})

    titles_field = [
        'Название операции',
        'Название манипуляции',
        'Дата проведения',
        'Время начала',
        'Время окончания',
        'Метод обезболивания',
        'Осложнения',
        'Код операции',
        'Код манипуляции',
        'Оперативное вмешательство',
        'Описание манипуляции',
        'Код анестезиолога',
        'Категория сложности',
        'Диагноз после оперативного лечения',
        'МКБ 10',
        'Оперировал',
        'Код хирурга',
        'Код врача',
        'Заключение',
        'Реакции и осложнения:',
        'Группа крови АВО',
        'Фенотип донора:',
        'Наименование компонента донорской крови',
        '№ единицы компонентов крови:',
    ]
    list_values = []

    operation_result = []
    if titles_field and operation_iss_research and hosp_operation:
        for i in operation_iss_research:
            list_values.append(get_result_value_iss(i['iss'], i['research'], titles_field))

        operation_result = []
        for fields_operation in list_values:
            pk_iss_operation = fields_operation[0][1]
            operation_data = {
                'name_operation': '',
                'date': '',
                'time_start': '',
                'time_end': '',
                'anesthesia method': '',
                'complications': '',
                'doc_fio': '',
                'code_operation': '',
                'code_doc_anesthesia': '',
                'plan_operation': '',
                'diagnos_after_operation': '',
                'mkb10': '',
                'category_difficult': '',
                'doc_code': '',
                'final': '',
                'Группа крови АВО': '',
                'Фенотип донора:': '',
                'Наименование компонента донорской крови': '',
                '№ единицы компонентов крови:': '',
            }
            iss_obj = Issledovaniya.objects.filter(pk=pk_iss_operation).first()
            if not iss_obj.time_confirmation:
                continue
            operation_data['doc_fio'] = iss_obj.doc_confirmation_fio
            operation_data['doc_code'] = None if not Issledovaniya.objects.get(pk=pk_iss_operation) else Issledovaniya.objects.get(pk=pk_iss_operation).doc_confirmation.personal_code
            if operation_data['doc_code'] == 0:
                operation_data['doc_code'] = ''
            category_difficult = ''
            for field in fields_operation:
                if field[3] == 'Название операции' or field[3] == 'Название манипуляции':
                    operation_data['name_operation'] = field[2]
                    continue
                if field[3] == 'Дата проведения':
                    operation_data['date'] = normalize_date(field[2])
                    continue
                if field[3] == 'Время начала':
                    operation_data['time_start'] = field[2]
                    continue
                if field[3] == 'Время окончания':
                    operation_data['time_end'] = field[2]
                    continue
                if field[3] == 'Метод обезболивания':
                    operation_data['anesthesia method'] = field[2]
                    continue
                if field[3] == 'Осложнения' or field[3] == 'Реакции и осложнения:':
                    operation_data['complications'] = field[2]
                    continue
                if field[3] == 'Код операции':
                    operation_data['code_operation'] = field[2]
                    continue
                if field[3] == 'Код манипуляции':
                    operation_data['code_operation'] = field[2]
                    continue
                if field[3] == 'Код анестезиолога':
                    operation_data['code_doc_anesthesia'] = field[2]
                    continue
                if field[3] == 'Оперативное вмешательство':
                    operation_data['plan_operation'] = field[2]
                    continue
                if field[3] == 'Категория сложности':
                    operation_data['category_difficult'] = f"Сложность - {field[2]}"
                    continue
                if field[3] == 'Диагноз после оперативного лечения':
                    operation_data['diagnos_after_operation'] = field[2]
                    continue
                if field[3] == 'МКБ 10':
                    operation_data['mkb10'] = field[2]
                    continue
                if field[3] == 'Оперировал':
                    if field[2]:
                        operation_data['doc_fio'] = field[2]
                    continue
                if field[3] == 'Код хирурга' or field[3] == 'Код врача':
                    if field[2]:
                        operation_data['doc_code'] = field[2]
                    continue
                if field[3] == 'Заключение':
                    if field[2]:
                        operation_data['final'] = field[2]
                    continue
                if field[3] == 'Группа крови АВО':
                    if field[2]:
                        operation_data['Группа крови АВО'] = field[2]
                    continue
                if field[3] == 'Фенотип донора:':
                    if field[2]:
                        operation_data['Фенотип донора:'] = field[2]
                    continue
                if field[3] == 'Наименование компонента донорской крови':
                    if field[2]:
                        operation_data['Наименование компонента донорской крови'] = field[2]
                    continue
                if field[3] == '№ единицы компонентов крови:':
                    if field[2]:
                        operation_data['№ единицы компонентов крови:'] = field[2]
                    continue

            operation_data['name_operation'] = f"{operation_data['name_operation']}-{category_difficult}"
            if operation_data.get('name_operation') == '-':
                operation_data["name_operation"] = (
                    f"{iss_obj.research.title} "
                    f"Группа крови АВО:{operation_data.get('Группа крови АВО')} "
                    f"Фенотип донора: {operation_data.get('Фенотип донора:', '-')} "
                    f"Наименование компонента донорской крови: {operation_data.get('Наименование компонента донорской крови', '-')} "
                    f"№ единицы компонентов крови:{operation_data.get('№ единицы компонентов крови:', '-')}"
                )
            operation_result.append(operation_data.copy())

    return operation_result


def closed_bl(hosp_num_dir):
    """
    Подтверждены больничные-протоколы со словом закрытие среди Б/Л?
    """
    result_bl = hosp_get_data_direction(hosp_num_dir, site_type=8, type_service='None', level=-1)
    num, who_get, who_care, start_date, end_date, start_work = '', '', '', '', '', ''
    for i in result_bl:
        if i['date_confirm'] is None:
            continue
        if i["research_title"].lower().find('закрыт') != -1:
            data_closed_bl = ParaclinicResult.objects.filter(issledovaniye=i['iss'])
            for b in data_closed_bl:
                if b.field.title == "Лист нетрудоспособности №":
                    num = b.value
                    continue
                if b.field.title == "Выдан кому":
                    who_get = b.value
                    continue
                if b.field.title == "по уходу за":
                    who_care = b.value
                    continue
                if b.field.title == "выдан с":
                    start_date = b.value
                    if start_date.find('-') != -1:
                        start_date = normalize_date(start_date)
                    continue
                if b.field.title == "по":
                    end_date = b.value
                    if end_date.find('-') != -1:
                        end_date = normalize_date(end_date)
                    continue
                if b.field.title == "к труду":
                    start_work = b.value
                    if start_work.find('-') != -1:
                        start_work = normalize_date(start_work)
                    continue

            return {'is_closed': True, 'num': num, 'who_get': who_get, 'who_care': who_care, 'start_date': start_date, 'end_date': end_date, 'start_work': start_work}

    return {'is_closed': False, 'num': num, 'who_get': who_get, 'who_care': who_care, 'start_date': start_date, 'end_date': end_date, 'start_work': start_work}


def create_contract(ind_dir, card_pk):
    ind_card = Card.objects.get(pk=card_pk)
    # exec_person = request_data['user'].doctorprofile.get_full_fio()

    patient_data = ind_card.get_data_individual()
    p_agent = None
    if ind_card.who_is_agent:
        p_agent = getattr(ind_card, ind_card.who_is_agent)

    p_payer = None
    if ind_card.payer:
        p_payer = ind_card.payer

    # Получить все источники, у которых title-ПЛАТНО
    ist_f = list(IstochnikiFinansirovaniya.objects.values_list('id').filter(title__exact='Платно'))
    ist_f_list = [int(x[0]) for x in ist_f]

    napr = Napravleniya.objects.filter(pk__in=ind_dir)
    dir_temp = []

    # Проверить, что все направления принадлежат к одной карте и имеют ист.финансирования "Платно"
    num_contract_set = set()
    for n in napr:
        if n.istochnik_f_id in ist_f_list and n.client == ind_card:
            num_contract_set.add(n.num_contract)
            dir_temp.append(n.pk)

    if not dir_temp:
        return False

    # получить УСЛУГИ по направлениям(отфильтрованы по "платно" и нет сохраненных исследований) в Issledovaniya
    research_direction = get_research_by_dir(dir_temp)

    if not research_direction:
        return False

    # получить по направлению-услугам цену из Issledovaniya
    research_price = get_coast_from_issledovanie(research_direction)

    # Получить Итоговую стр-ру данных
    result_data = get_final_data(research_price)

    sum_research = result_data[1]

    # Контрольная сумма расчет: послдеовательность направлений+Итоговая сумма (стоимость денежная)
    qr_napr = ','.join([str(elem) for elem in result_data[3]])
    protect_val = sum_research.replace(' ', '')
    bstr = (qr_napr + protect_val).encode()
    protect_code = str(zlib.crc32(bstr))

    today = utils.current_time()
    date_now1 = datetime.datetime.strftime(today, '%y%m%d%H%M%S%f')[:-3]
    date_now_str = str(ind_card.pk) + str(date_now1)

    # Проверить записан ли номер контракта в направлениях, и контрольная сумма
    # ПереЗаписать номер контракта Если в наборе направлений значение None, или в направлениях разные контракты,
    # а также разные контрольные суммы, все перезаписать.
    num_contract_set = set()
    protect_code_set = set()
    napr_end = Napravleniya.objects.filter(id__in=result_data[3])
    for n in napr_end:
        num_contract_set.add(n.num_contract)
        protect_code_set.add(n.protect_code)

    if len(num_contract_set) == 1 and None in num_contract_set or None in protect_code_set:
        PersonContract.person_contract_save(date_now_str, protect_code, qr_napr, sum_research, patient_data['fio'], ind_card, p_payer, p_agent)
        Napravleniya.objects.filter(id__in=result_data[3]).update(num_contract=date_now_str, protect_code=protect_code)

    return PersonContract.pk
