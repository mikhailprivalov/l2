import datetime
import locale
import os.path
import sys
import zlib
from copy import deepcopy
from datetime import date
from io import BytesIO
from typing import List, Union

import pytils
import simplejson as json
from dateutil.relativedelta import relativedelta
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import code128, qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.colors import white, black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak, Macro
from reportlab.platypus.flowables import HRFlowable

from appconf.manager import SettingManager
from clients.models import Card
from directions.models import Napravleniya, IstochnikiFinansirovaniya, PersonContract, Issledovaniya
from hospitals.models import Hospitals
from laboratory import utils
from laboratory.settings import FONTS_FOLDER, BASE_DIR
from utils.xh import save_tmp_file
from . import forms_func
from utils.pagenum import PageNumCanvasPartitionAll
from .sql_func import sort_direction_by_file_name_contract, get_research_data_for_contract_specification
from directions.views import gen_pdf_dir as f_print_direction
from django.http import HttpRequest


def form_01(request_data):
    """
    Договор, включающий услуги на оплату и необходимые реквизиты. С Учетом представителей и Заказчиков(Плательщиков)
    у пациента
    """
    return False
    p_payer = None
    p_agent = None
    ind_card = Card.objects.get(pk=request_data["card_pk"])
    ind_dir = json.loads(request_data["napr_id"])
    exec_person = request_data['user'].doctorprofile.get_full_fio()

    patient_data = ind_card.get_data_individual()
    agent_status = None
    p_agent = None
    if ind_card.who_is_agent:
        p_agent = getattr(ind_card, ind_card.who_is_agent)
        agent_status = bool(p_agent)

    # Если владельцу карты меньше 15 лет и не передан представитель, то вернуть ошибку
    who_patient = 'пациента'
    if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i') and not agent_status:
        return False
    elif patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i') and agent_status:
        who_patient = 'ребёнка'

    if p_agent:
        person_data = p_agent.get_data_individual()
    else:
        person_data = patient_data

    p_payer = None
    payer_data = None
    if ind_card.payer:
        p_payer = ind_card.payer
        payer_data = p_payer.get_data_individual()

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
    research_direction = forms_func.get_research_by_dir(dir_temp)

    if not research_direction:
        return False

    # получить по направлению-услугам цену из Issledovaniya
    research_price = forms_func.get_coast_from_issledovanie(research_direction)

    # Получить Итоговую стр-ру данных
    result_data = forms_func.get_final_data(research_price)

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

    # ПереЗаписать номер контракта Если в наборе направлении значение разные значения
    if len(num_contract_set) > 1 or len(protect_code_set) > 1:
        PersonContract.person_contract_save(date_now_str, protect_code, qr_napr, sum_research, patient_data['fio'], ind_card, p_payer, p_agent)
        Napravleniya.objects.filter(id__in=result_data[3]).update(num_contract=date_now_str, protect_code=protect_code)

    if len(num_contract_set) == 1 and None not in num_contract_set:
        if len(protect_code_set) == 1 and None not in protect_code_set:
            if protect_code_set.pop() == protect_code:
                date_now_str = num_contract_set.pop()
            else:
                PersonContract.person_contract_save(date_now_str, protect_code, qr_napr, sum_research, patient_data['fio'], ind_card, p_payer, p_agent)
                Napravleniya.objects.filter(id__in=result_data[3]).update(num_contract=date_now_str, protect_code=protect_code)

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    # Генерировать pdf-Лист на оплату
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Symbola', os.path.join(FONTS_FOLDER, 'Symbola.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=12 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=28 * mm, allowSplitting=1, title="Форма {}".format("Договор на оплату")
    )
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 9
    style.leading = 12
    style.spaceAfter = 0 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = 15

    styleAppendix = deepcopy(style)
    styleAppendix.fontSize = 9
    styleAppendix.firstLineIndent = 8
    styleAppendix.leading = 9

    styleFL = deepcopy(style)
    styleFL.firstLineIndent = 0
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleBoldCenter = deepcopy(styleBold)
    styleBoldCenter.alignment = TA_CENTER

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 9
    styleCenter.leading = 10
    styleCenter.spaceAfter = 0 * mm

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 20
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'

    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    objs: List[Union[Spacer, Paragraph, Table, KeepTogether]] = []
    barcode128 = code128.Code128(date_now_str, barHeight=6 * mm, barWidth=1.25)
    objs.append(Spacer(1, 11 * mm))

    objs.append(Paragraph('ДОГОВОР &nbsp;&nbsp; № <u>{}</u>'.format(date_now_str), styleCenter))
    objs.append(Spacer(1, 1 * mm))
    objs.append(Paragraph('НА ОКАЗАНИЕ ПЛАТНЫХ МЕДИЦИНСКИХ УСЛУГ НАСЕЛЕНИЮ', styleCenter))
    styleTCenter = deepcopy(styleCenter)
    styleTCenter.alignment = TA_CENTER
    styleTCenter.leading = 3.5 * mm

    styleTBold = deepcopy(styleCenterBold)
    styleTBold.fontSize = 10
    styleTBold.alignment = TA_LEFT

    styles_obj = {'style': style, 'styleCenter': styleCenter, 'styleAppendix': styleAppendix, "styleBoldCenter": styleBoldCenter}

    date_now = pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=datetime.datetime.now())

    styleTR = deepcopy(style)
    styleTR.alignment = TA_RIGHT

    opinion = [
        [Paragraph('г. Иркутск', style), Paragraph('{} года'.format(date_now), styleTR)],
    ]

    tbl = Table(opinion, colWidths=(95 * mm, 95 * mm))

    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
            ]
        )
    )

    objs.append(Spacer(1, 5 * mm))
    objs.append(tbl)

    objs.append(Spacer(1, 4.5 * mm))

    hospital: Hospitals = request_data["hospital"]

    hospital_name = hospital.safe_short_title
    hospital_short_name = hospital.safe_short_title
    hospital_address = hospital.safe_address

    post_contract = SettingManager.get("post_contract")
    document_base = SettingManager.get("document_base")

    contract_from_file = SettingManager.get("contract_from_file", default='False', default_type='b')
    contract_file = os.path.join(BASE_DIR, 'forms', 'contract.json')

    executor = None
    if contract_from_file:
        with open(contract_file) as json_file:
            data = json.load(json_file)
            contract_header = data['contract_header']
            body_paragraphs = data['body_paragraphs']
            org_contacts = data['org_contacts']
            executor = data['executor']
            appendix_paragraphs = data.get('appendix_paragraphs', None)
            appendix_route_list = data.get('appendix_route_list', None)
    else:
        executor = None

    if contract_from_file:
        objs.append(Paragraph('{}'.format(contract_header), style))
    else:
        objs.append(
            Paragraph(
                '<font fontname ="PTAstraSerifBold"> Исполнитель:  </font>  {}, в лице {} {}, действующего(ей) на основании {} с одной стороны, и'.format(
                    hospital_name, post_contract, exec_person, document_base
                ),
                style,
            )
        )

    them_contract = 'настоящий договор о нижеследующем:'
    client_who = 'Заказчик'
    is_payer = False
    # Добавдяем представителя (мать, отец, опекун или др. не дееспособный)
    is_pagent = False
    # представитель==Заказчик ()
    payer_fio = None
    if (p_payer is None) or (p_payer == p_agent) or (p_agent and p_payer is None):
        payer_fio = person_data['fio']
        is_pagent = True
        p_agent_who = client_who + " (представитель пациента)"
    else:
        p_agent_who = "Представитель пациента"

    # Если Заказчик(Плательщик) другое физ лицо отдельный Заказчик, отдельно Представитель, отдельно пациент
    if p_payer and (p_payer != p_agent):
        client_side = ''
        if p_agent is None:
            client_side = ', с другой стороны, заключили в интересах Пациента (Потребителя)'
        is_payer = True
        payer_fio = payer_data['fio']
        objs.append(
            Paragraph(
                '<font fontname ="PTAstraSerifBold">{}: </font> {}, дата рождения {} г., '
                'паспорт: {}-{} '
                'выдан {} г. '
                'кем: {} '
                'адрес регистрации: {}, '
                'адрес проживания: {} {}'.format(
                    client_who,
                    payer_data['fio'],
                    payer_data['born'],
                    payer_data['passport_serial'],
                    payer_data['passport_num'],
                    payer_data['passport_date_start'],
                    payer_data['passport_issued'],
                    payer_data['main_address'],
                    payer_data['fact_address'],
                    client_side,
                ),
                style,
            )
        )

    if p_agent:
        client_side = ', с другой стороны, заключили в интересах Пациента (Потребителя)'
        objs.append(
            Paragraph(
                '<font fontname ="PTAstraSerifBold"> {}: </font> {} ({} {}), дата рождения {} г., '
                'паспорт: {}-{} '
                'выдан {} г. '
                'кем: {} '
                'адрес регистрации: {}, '
                'адрес проживания: {} {}'.format(
                    p_agent_who,
                    person_data['fio'],
                    ind_card.get_who_is_agent_display(),
                    who_patient,
                    person_data['born'],
                    person_data['passport_serial'],
                    person_data['passport_num'],
                    person_data['passport_date_start'],
                    person_data['passport_issued'],
                    person_data['main_address'],
                    person_data['fact_address'],
                    client_side,
                ),
                style,
            )
        )

    # Добавдяем потребителя услуги (пациента)
    if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i'):
        p_doc_serial, p_doc_num, p_doc_start = patient_data['bc_serial'], patient_data['bc_num'], patient_data['bc_date_start']
        p_doc_issued = patient_data['passport_issued']
    else:
        p_doc_serial, p_doc_num, p_doc_start = patient_data['passport_serial'], patient_data['passport_num'], patient_data['passport_date_start']
        p_doc_issued = patient_data['bc_issued']

    # Пациент==Заказчик
    if p_payer is None and p_agent is None:
        p_who = client_who + " - Пациент (потребитель)"
        client_side = ', с другой стороны, заключили настоящий договор о нижеследующем:'
        them_contract = ''
    else:
        p_who = "Пациент (потребитель)"
        client_side = ''

    objs.append(
        Paragraph(
            '<font fontname ="PTAstraSerifBold"> {}:</font> {}, дата рождения {} г.,'
            '{}: {}-{} '
            'выдан {} г. '
            'кем: {} '
            'адрес регистрации: {}, '
            'адрес проживания: {} {} '.format(
                p_who,
                patient_data['fio'],
                patient_data['born'],
                patient_data['type_doc'],
                p_doc_serial,
                p_doc_num,
                p_doc_start,
                p_doc_issued,
                patient_data['main_address'],
                patient_data['fact_address'],
                client_side,
            ),
            style,
        )
    )

    objs.append(Paragraph('{}'.format(them_contract), styleFL))
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph('1. ПРЕДМЕТ ДОГОВОРА', styleCenter))
    objs.append(Paragraph('1.1. Исполнитель на основании обращения Заказчика обязуется оказать ему медицинские услуги в соответствие с лицензией:', style))

    template_research = "Перечень услуг"

    tr = ""
    if template_research:
        tr = template_research
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph('{}'.format(tr), style))

    styleTB = deepcopy(style)
    styleTB.firstLineIndent = 0
    styleTB.fontSize = 8.5
    styleTB.alignment = TA_CENTER
    styleTB.fontName = "PTAstraSerifBold"

    styleTC = deepcopy(style)
    styleTC.firstLineIndent = 0
    styleTC.fontSize = 8.5
    styleTC.alignment = TA_LEFT

    styleTCright = deepcopy(styleTC)
    styleTCright.alignment = TA_RIGHT

    styleTCcenter = deepcopy(styleTC)
    styleTCcenter.alignment = TA_CENTER

    # Всегда заголовки одинаково со скидкой
    opinion = [
        [
            Paragraph('Код услуги', styleTB),
            Paragraph('Направление', styleTB),
            Paragraph('Услуга', styleTB),
            Paragraph('Цена,<br/>руб.', styleTB),
            Paragraph('Скидка<br/>Наценка<br/>%', styleTB),
            Paragraph('Цена со<br/> скидкой,<br/>руб.', styleTB),
            Paragraph('Кол-во, усл.', styleTB),
            Paragraph('Сумма, руб.', styleTB),
        ],
    ]

    # example_template = [
    #     ['1.2.3','4856397','Полный гематологический анализ','1000.00','0','1000.00','1','1000.00'],
    #     ['1.2.3','','РМП','2500.45','0','2500.45','1','2500.45'],
    #     ['1.2.3', '4856398', 'УЗИ брюшной полости', '3500.49', '0', '3500.49', '1', '3500.49'],
    #     ['1.2.3','4856398','Эзофагогастродуоденоскопия','5700.99','0','5700.99','1','5700.99']
    # ]
    #

    example_template = result_data[0]

    list_g = []
    route_list = [[Paragraph('Направление', styleTB), Paragraph('Услуга', styleTB)]]
    # используется range(len()) - к определенной колонке (по номеру) применяется свое свойство
    for i in range(len(example_template)):
        list_t = []
        for j in range(len(example_template[i])):
            if j in (3, 5, 7):
                s = styleTCright
            elif j in (4, 6):
                s = styleTCcenter
            else:
                s = styleTC
            list_t.append(Paragraph(example_template[i][j], s))
        list_g.append(list_t)
        route_list.append([Paragraph(example_template[i][1], styleTC), Paragraph(example_template[i][2], styleTC)])

    opinion.extend(list_g)

    sum_research_decimal = sum_research.replace(' ', '')

    tbl = Table(opinion, colWidths=(18 * mm, 19 * mm, 52 * mm, 22 * mm, 21 * mm, 22 * mm, 13 * mm, 25 * mm))

    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
    )

    s = pytils.numeral.rubles(float(sum_research_decimal))
    end_date = date.today() + relativedelta(days=+10)
    end_date1 = datetime.datetime.strftime(end_date, "%d.%m.%Y")
    objs.append(
        Paragraph(
            'Сроки оплаты: в течение<font fontname ="PTAstraSerifBold"> 10 дней </font> со дня заключения договора до <font fontname ="PTAstraSerifBold"> {}</font>'.format(end_date1), style
        )
    )
    if contract_from_file:
        for section in body_paragraphs:
            if section.get('is_price'):
                objs.append(Paragraph('{} <font fontname = "PTAstraSerifBold"> <u> {} </u></font>'.format(section['text'], s.capitalize()), styles_obj[section['style']]))
            elif section.get('time_pay'):
                objs.append(
                    Paragraph(
                        '{} в течение<font fontname ="PTAstraSerifBold"> 10 дней </font> со дня заключения договора до <font fontname ="PTAstraSerifBold"> {}</font>'.format(
                            section['text'], end_date1
                        ),
                        styles_obj[section['style']],
                    )
                )
            elif section.get('is_researches'):
                objs.append(tbl)
                objs.append(Spacer(1, 1 * mm))
                objs.append(Paragraph('<font size=12> Итого: {}</font>'.format(sum_research), styleTCright))
                objs.append(Spacer(1, 2 * mm))
                objs.append(Spacer(1, 3 * mm))
            else:
                objs.append(Paragraph(section['text'], styles_obj[section['style']]))
    else:
        objs.append(
            Paragraph(
                '1.2. Исполнитель оказывает услуги по месту своего нахождения по адресу: '
                'г. Иркутск, Байкальская, 201, в соответствии с установленными Правилами предоставления платных медицинских услуг.',
                style,
            )
        )
        objs.append(Spacer(1, 2 * mm))
        objs.append(Paragraph('2. ПРАВА И ОБЯЗАННОСТИ СТОРОН', styleCenter))
        objs.append(Paragraph('<u>2.1. Исполнитель обязуется:</u>', style))
        objs.append(Paragraph('2.1.1. Обеспечить Пациента бесплатной, доступной и достоверной информацией о платных медицинских услугах, ' 'содержащей следующие сведения о:', style))
        objs.append(Paragraph('а) порядках оказания медицинской помощи и стандартах медицинской помощи, применяемых при предоставлении платных медицинских услуг;', style))
        objs.append(
            Paragraph('б) данных о конкретном медицинском работнике, предоставляющем соответствующую платную медицинскую услугу (его профессиональном образовании и квалификации);', style)
        )
        objs.append(
            Paragraph(
                'в) данных о методах оказания медицинской помощи, связанных с ними рисках, возможных видах медицинского вмешательства, их последствиях и '
                'ожидаемых результатах оказания медицинской помощи;',
                style,
            )
        )
        objs.append(Paragraph('г) других сведениях, относящихся к предмету настоящего Договора.', style))
        objs.append(Paragraph('2.1.2.Оказывать Пациенту услуги, предусмотренные п. 1.1 настоящего Договора, а при необходимости и дополнительные услуги.', style))
        objs.append(
            Paragraph(
                '2.1.3.Давать при необходимости по просьбе Пациента разъяснения о ходе оказания услуг ему и ' 'предоставлять по требованию Пациента необходимую медицинскую документацию.',
                style,
            )
        )
        objs.append(
            Paragraph(
                '2.1.4.Предоставить в доступной форме информацию о возможности получения соответствующих видов '
                'и объемов медицинской помощи без взимания платы в рамках Программы государственных гарантий '
                'бесплатного оказания гражданам медицинской помощи и территориальной программы государственных гарантий '
                'бесплатного оказания гражданам медицинской помощи.',
                style,
            )
        )
        objs.append(Paragraph('2.15. Соблюдать порядки оказания медицинской помощи, утвержденные Министерством здравоохранения ' 'Российской Федерации.', style))
        objs.append(Paragraph('<u>2.2. Заказчик обязуется:</u>', style))
        objs.append(Paragraph('2.2.1. Соблюдать назначение и рекомендации лечащих врачей.', style))
        objs.append(Paragraph('2.2.3. Оплачивать услуги Исполнителя в порядке, сроки и на условиях, которые установлены настоящим Договором.', style))
        objs.append(Paragraph('2.2.4. Подписывать своевременно акты об оказании услуг Исполнителем.', style))
        objs.append(Paragraph('2.2.5. Кроме того Пациент обязан:', style))
        objs.append(Paragraph('- информировать врача о перенесенных заболеваниях, известных ему аллергических реакциях, противопоказаниях;', style))
        objs.append(Paragraph('- соблюдать правила поведения пациентов в медицинском учреждении, режим работы медицинского учреждения;', style))
        objs.append(
            Paragraph(
                '- выполнять все рекомендации медицинского персонала и третьих лиц, оказывающих ему по настоящему Договору'
                'медицинские услуги, по лечению, в том числе соблюдать указания медицинского учреждения, предписанные на период после оказания услуг.',
                style,
            )
        )
        objs.append(Paragraph('2.3. Предоставление Исполнителем дополнительных услуг оформляется дополнительным соглашением Сторон и оплачивается дополнительно.', style))
        objs.append(
            Paragraph(
                '2.4. Стороны обязуются хранить в тайне лечебную, финансовую и иную конфиденциальную информацию, ' 'полученную от другой Стороны при исполнении настоящего Договора.', style
            )
        )
        objs.append(Spacer(1, 2 * mm))
        objs.append(Paragraph('3. ПОРЯДОК ИСПОЛНЕНИЯ ДОГОВОРА', styleCenter))
        objs.append(
            Paragraph(
                '3.1. Условия получения Пациентом медицинских услуг: (вне медицинской организации; амбулаторно; '
                'в дневном стационаре; стационарно; указать,организационные моменты, связанные с оказанием медицинских услуг)',
                style,
            )
        )
        objs.append(
            Paragraph(
                '3.2. В случае если при предоставлении платных медицинских услуг требуется предоставление '
                'на возмездной основе дополнительных медицинских услуг, не предусмотренных настоящим Договором, '
                'Исполнитель обязан предупредить об этом Пациента.',
                style,
            )
        )
        objs.append(Paragraph('Без согласия Пациента Исполнитель не вправе предоставлять дополнительные медицинские услуги на возмездной основе.', style))
        objs.append(
            Paragraph(
                '3.3. В случае, если при предоставлении платных медицинских услуг потребуется предоставление '
                'дополнительных медицинских услуг по экстренным показаниям для устранения угрозы жизни Пациента'
                ' при внезапных острых заболеваниях, состояниях, обострениях хронических заболеваний, такие '
                'медицинские услуги оказываются без взимания платы в соответствии с Федеральным загоном '
                'от 21.11.2011N 323-ФЗ "Об основах охраны здоровья граждан в Российской Федерации".',
                style,
            )
        )
        objs.append(
            Paragraph(
                '3.4. В случае отказа Пациента после заключения Договора от получения медицинских услуг Договор '
                'расторгается. При этом Пациент оплачивает Исполнителю фактически понесенные Исполнителем расходы,'
                'связанные с исполнением обязательств по Договору. ',
                style,
            )
        )
        objs.append(
            Paragraph(
                '3.5. К отношениям, связанным с исполнением настоящего Договора, применяются положения Закона '
                'Российской Федерации от 7 февраля 1992 г. N 2300-1 "О защите прав потребителей".',
                style,
            )
        )
        objs.append(Spacer(1, 2 * mm))
        objs.append(Paragraph('4. ПОРЯДОК ОПЛАТЫ', styleCenter))
        objs.append(Paragraph('4.1. Стоимость медицинских услуг составляет:<font fontname ="PTAstraSerifBold"> <u>{}</u> </font> '.format(s.capitalize()), style))
        end_date = date.today() + relativedelta(days=+10)
        end_date1 = datetime.datetime.strftime(end_date, "%d.%m.%Y")
        objs.append(
            Paragraph(
                'Сроки оплаты: в течение<font fontname ="PTAstraSerifBold"> 10 дней </font> со дня заключения договора до <font fontname ="PTAstraSerifBold"> {}</font>'.format(end_date1),
                style,
            )
        )
        objs.append(Paragraph('Предоплата 100%.', style))
        objs.append(Paragraph('4.2. Оплата услуг производится путем перечисления суммы на расчетный счет Исполнителя или путем внесения в кассу Исполнителя.', style))
        objs.append(
            Paragraph(
                'Заказчику в соответствии с законодательством Российской Федерации выдается документ; '
                'подтверждающий произведенную оплату предоставленных медицинских услуг (кассовый чек, квитанция '
                'или иные документы).',
                style,
            )
        )
        objs.append(Paragraph('4.3. Дополнительные услуги оплачиваются на основании акта об оказанных услугах, подписанного Сторонами.', style))
        objs.append(Spacer(1, 2 * mm))
        objs.append(Paragraph('5. ОТВЕТСТВЕННОСТЬ СТОРОН', styleCenter))
        objs.append(
            Paragraph(
                '5.1. Исполнитель несет ответственность перед Пациентом за неисполнение или ненадлежащее '
                'исполнение условий настоящего Договора, несоблюдение требований, предъявляемых к методам '
                'диагностики, профилактики и лечения, разрешенным на территории Российской Федерации, а также '
                'в случае причинения вреда здоровью и жизни Пациента.',
                style,
            )
        )
        objs.append(Paragraph('5.2. При несоблюдении Исполнителем обязательств по срокам исполнения услуг Заказчик вправе по своему выбору:', style))
        objs.append(Paragraph('- назначить новый срок оказания услуги;', style))
        objs.append(Paragraph('- потребовать уменьшения стоимости предоставленной услуги;', style))
        objs.append(Paragraph('- потребовать исполнения услуги другим специалистом;', style))
        objs.append(Paragraph('- расторгнуть настоящий Договор и потребовать возмещения убытков.', style))
        objs.append(
            Paragraph(
                '5.3. Ни одна из Сторон не будет нести ответственности за полное или частичное неисполнение другой '
                'Стороной своих обязанностей, если, неисполнение будет являться следствием обстоятельств непреодолимой '
                'силы, таких как, пожар, наводнение, землетрясение, забастовки и другие стихийные бедствия; '
                'война и военные действия или другие обстоятельства, находящиеся вне контроля Сторон, '
                'препятствующие выполнению настоящего Договора, возникшие после заключения Договора, а также по '
                'иным основаниям, предусмотренным законом',
                style,
            )
        )
        objs.append(
            Paragraph(
                'Если любое из таких обстоятельств непосредственно повлияло на неисполнение обязательства в '
                'срок, указанный в Договоре, то этот срок соразмерно отодвигается на время действия соответствующего '
                'обстоятельства.',
                style,
            )
        )
        objs.append(
            Paragraph(
                '5.4. Вред, причиненный жизни или здоровью Пациента в результате предоставления некачественной '
                'платной медицинской услуги, подлежит возмещению Исполнителем в соответствии с законодательством '
                'Российской Федерации.',
                style,
            )
        )
        objs.append(Spacer(1, 2 * mm))
        objs.append(Paragraph('6. ПОРЯДОК РАССМОТРЕНИЯ СПОРОВ', styleCenter))
        objs.append(Paragraph('6.1. Все споры, претензии и разногласия, которые могут возникнуть между Сторонами, будут ' 'разрешаться путем переговоров.', style))
        objs.append(Paragraph('6.2. При не урегулировании в процессе переговоров спорных вопросов споры подлежат рассмотрению ' 'в судебном порядке.', style))
        objs.append(Spacer(1, 2 * mm))
        objs.append(Paragraph('7. СРОК ДЕЙСТВИЯ ДОГОВОРА', styleCenter))
        objs.append(Paragraph('7.1. Срок действия настоящего Договора: с «  »    201  г. по «  »    201  г.', style))
        objs.append(Paragraph('7.2. Настоящий Договор, может быть, расторгнут по обоюдному согласию Сторон или в порядке, ' 'предусмотренном действующим законодательством.', style))
        objs.append(
            Paragraph(
                '7.3. Все изменения и дополнения к настоящему Договору, а также его расторжение считаются '
                'действительными при условии, если они совершены в письменной форме и подписаны уполномоченными'
                ' на то представителями обеих Сторон.',
                style,
            )
        )
        objs.append(Spacer(1, 2 * mm))
        objs.append(Paragraph('8. ИНЫЕ УСЛОВИЯ', styleCenter))
        objs.append(
            Paragraph(
                '8.1. Все дополнительные соглашения Сторон, акты и иные приложения к настоящему Договору, '
                'подписываемые Сторонами при исполнении настоящего Договора, являются его неотъемлемой частью.',
                style,
            )
        )
        objs.append(Paragraph('8.2. Настоящий Договор составлен в 2 (двух) экземплярах, имеющих одинаковую юридическую силу, ' 'по одному для каждой из Сторон', style))

    styleAtr = deepcopy(style)
    styleAtr.firstLineIndent = 0

    # Данные исполнителя в Договоре
    fio_director_list = exec_person.split(' ')
    dir_f = fio_director_list[0]
    dir_n = fio_director_list[1]
    dir_p = fio_director_list[2]
    dir_npf = dir_n[0:1] + '.' + ' ' + dir_p[0:1] + '.' + ' ' + dir_f
    if executor:
        dir_npf = executor

    space_symbol = '&nbsp;'

    # Данные плательщика в Договоре
    npf = ''
    if payer_fio:
        fio_list = payer_fio.split(' ')
        f = fio_list[0]
        n = fio_list[1][0:1] + '.'
        p = fio_list[2][0:1] + '.' if len(fio_list) > 2 else ''
        npf = n + ' ' + p + ' ' + f

    # Данные пациента в Договоре
    patient_list = patient_data['fio'].split(' ')
    pf = patient_list[0]
    pn = patient_list[1][0:1] + '.'
    pp = patient_list[2][0:1] + '.' if len(patient_list) > 2 else ''
    p_npf = pn + ' ' + pp + ' ' + pf

    rowHeights = None

    # Ниже реквизиты в таблице. Возможные варианты: Заказчик(Пациент), Заказчик + Пациент, Заказчик+Представитель+Пациент (Ужасно)
    # Если есть отдельный заказчик
    row_count = 0
    if contract_from_file:
        hospital_address = org_contacts
    if is_payer:
        row_count = 0
        opinion = [
            [
                Paragraph('<font fontname ="PTAstraSerifBold">Исполнитель</font>', styleAtr),
                Paragraph('', styleAtr),
                Paragraph('<font fontname ="PTAstraSerifBold">{}:</font>'.format(client_who), styleAtr),
            ],
            [
                Paragraph('{} <br/>{}'.format(hospital_name, hospital_address), styleAtr),
                Paragraph('', styleAtr),
                Paragraph('{}<br/>Паспорт: {}-{}<br/>Адрес:{}'.format(payer_data['fio'], payer_data['passport_serial'], payer_data['passport_num'], payer_data['main_address']), styleAtr),
            ],
            [Paragraph('', styleAtr), Paragraph('', style), Paragraph('', styleAtr)],
            [Paragraph('Сотрудник {}'.format(hospital_short_name), styleAtr), Paragraph('', styleAtr), Paragraph('', styleAtr)],
            [
                Paragraph('________________________/{}/'.format(dir_npf), styleAtr),
                Paragraph('', styleAtr),
                Paragraph('/{}/________________________ <font face="Symbola" size=18>\u2713</font>'.format(npf), styleAtr),
            ],
        ]
        row_count = row_count + len(opinion)

        # Если Заказчик и представитель разные лица. Добавить представителя
        if p_agent:
            agent_list = person_data['fio'].split(' ')
            af = agent_list[0]
            an = agent_list[1]
            ap = agent_list[2][0:1] if len(agent_list) > 2 else ''
            a_npf = an + '.' + ' ' + ap + '.' + ' ' + af

            opinion_agent = [
                [Paragraph('', styleAtr), Paragraph('', style), Paragraph('', styleAtr)],
                [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('', styleAtr)],
                [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('<font fontname ="PTAstraSerifBold">{}:</font>'.format(p_agent_who), styleAtr)],
                [
                    Paragraph('', styleAtr),
                    Paragraph('', styleAtr),
                    Paragraph(
                        '{}<br/>{}: {}-{}<br/>Адрес:{}'.format(
                            person_data['fio'], person_data['type_doc'], person_data['passport_serial'], person_data['passport_num'], person_data['main_address']
                        ),
                        styleAtr,
                    ),
                ],
                [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('/{}/________________________ <font face="Symbola" size=18>\u2713</font>'.format(a_npf), styleAtr)],
            ]
            opinion.extend(opinion_agent)
            row_count = row_count + len(opinion_agent)

        # Добавить Пациента
        opinion_patient = [
            [Paragraph('', styleAtr), Paragraph('', style), Paragraph('', styleAtr)],
            [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('', styleAtr)],
            [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('<font fontname ="PTAstraSerifBold">{}:</font>'.format(p_who), styleAtr)],
            [
                Paragraph('', styleAtr),
                Paragraph('', styleAtr),
                Paragraph('{}<br/>{}: {}-{}<br/>Адрес:{}'.format(patient_data['fio'], patient_data['type_doc'], p_doc_serial, p_doc_num, patient_data['main_address']), styleAtr),
            ],
        ]

        parient_sign = [
            [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('/{}/________________________ <font face="Symbola" size=18>\u2713</font>'.format(p_npf), styleAtr)],
        ]

        if not p_agent:
            opinion_patient.extend(parient_sign)

        row_count = row_count + len(opinion_patient)

        opinion.extend(opinion_patient)

        rowHeights = row_count * [None]
        rowHeights[4] = 35
        rowHeights[9] = 35

    # Таблица для Заказчика-представителя
    if is_pagent and not is_payer:
        row_count = 0
        opinion = [
            [
                Paragraph('<font fontname ="PTAstraSerifBold">Исполнитель</font>', styleAtr),
                Paragraph('', styleAtr),
                Paragraph('<font fontname ="PTAstraSerifBold">{}:</font>'.format(p_agent_who), styleAtr),
            ],
            [
                Paragraph('{} <br/>{}'.format(hospital_name, hospital_address), styleAtr),
                Paragraph('', styleAtr),
                Paragraph(
                    '{}<br/>Паспорт: {}-{}<br/>Адрес:{}'.format(person_data['fio'], person_data['passport_serial'], person_data['passport_num'], person_data['main_address']), styleAtr
                ),
            ],
            [Paragraph('', styleAtr), Paragraph('', style), Paragraph('', styleAtr)],
            [Paragraph('Сотрудник {}'.format(hospital_short_name), styleAtr), Paragraph('', styleAtr), Paragraph('', styleAtr)],
            [
                Paragraph('________________________/{}/'.format(dir_npf), styleAtr),
                Paragraph('', styleAtr),
                Paragraph('/{}/________________________ <font face="Symbola" size=18>\u2713</font>'.format(npf), styleAtr),
            ],
        ]
        row_count = row_count + len(opinion)

        # Таблица для Пациента
        opinion_patient = [
            [Paragraph('', styleAtr), Paragraph('', style), Paragraph('', styleAtr)],
            [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('', styleAtr)],
            [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('<font fontname ="PTAstraSerifBold">{}:</font>'.format(p_who), styleAtr)],
            [
                Paragraph('', styleAtr),
                Paragraph('', styleAtr),
                Paragraph('{}<br/>{}: {}-{}<br/>Адрес:{}'.format(patient_data['fio'], patient_data['type_doc'], p_doc_serial, p_doc_num, patient_data['main_address']), styleAtr),
            ],
            # [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('', styleAtr)],
            [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('', styleAtr)],
        ]
        row_count = row_count + len(opinion_patient)

        opinion.extend(opinion_patient)
        rowHeights = row_count * [None]
        rowHeights[4] = 35
        rowHeights[9] = 35

    # Выводим Заказчик-Пациент(потребитель) - одно лицо
    if (not p_payer) and (not p_agent):
        row_count = 0
        opinion = [
            [
                Paragraph('<font fontname ="PTAstraSerifBold">Исполнитель</font>', styleAtr),
                Paragraph('', styleAtr),
                Paragraph('<font fontname ="PTAstraSerifBold">{}:</font>'.format(p_who), styleAtr),
            ],
            [
                Paragraph('{} <br/>{}'.format(hospital_name, hospital_address), styleAtr),
                Paragraph('', styleAtr),
                Paragraph(
                    '{}<br/>Паспорт: {}-{}<br/>Адрес:{}'.format(patient_data['fio'], patient_data['passport_serial'], patient_data['passport_num'], patient_data['main_address']), styleAtr
                ),
            ],
            [Paragraph('', styleAtr), Paragraph('', style), Paragraph('', styleAtr)],
            [Paragraph('Сотрудник {}'.format(hospital_short_name), styleAtr), Paragraph('', styleAtr), Paragraph('', styleAtr)],
            [
                Paragraph('________________________/{}/'.format(dir_npf), styleAtr),
                Paragraph('', styleAtr),
                Paragraph('/{}/________________________ <font face="Symbola" size=18>\u2713</font>'.format(npf), styleAtr),
            ],
        ]
        row_count = row_count + 5
        rowHeights = row_count * [None]
        rowHeights[4] = 35

    # Строим необходимую таблицу
    tbl = Table(opinion, colWidths=(90 * mm, 10 * mm, 90 * mm), rowHeights=rowHeights)
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
                ('TOPPADDING', (0, 0), (-1, -1), 1.5 * mm),
                ('VALIGN', (0, 0), (-1, -2), 'TOP'),
                ('VALIGN', (0, 4), (-1, 4), 'BOTTOM'),
                # ('VALIGN', (1, 4), (-1, -1), 'BOTTOM'),
                ('BOTTOMPADDING', (-1, 4), (-1, 4), 4.2 * mm),
                ('BOTTOMPADDING', (0, -1), (0, -1), 1 * mm),
                ('BOTTOMPADDING', (-1, -1), (-1, -1), 4.2 * mm),
            ]
        )
    )

    objs.append(Spacer(1, 2 * mm))

    # Заголовок Адреса и реквизиты + сами реквизиты всегда вместе, если разрыв на странице

    objs.append(KeepTogether([Paragraph('9. АДРЕСА И РЕКВИЗИТЫ СТОРОН', styleCenter), tbl]))
    objs.append(Spacer(1, 7 * mm))

    styleRight = deepcopy(style)
    styleRight.alignment = TA_RIGHT

    space_symbol = ' '

    left_size_str = hospital_short_name + 15 * space_symbol + protect_code + 15 * space_symbol

    qr_value = protect_code + ',' + npf + '(' + qr_napr + ')' + protect_val

    if npf != p_npf:
        qr_value = protect_code + ',' + npf + '-' + p_npf + '(' + qr_napr + ')' + protect_val

    def first_pages(canvas, document):
        canvas.saveState()
        canvas.setFont("PTAstraSerifReg", 9)
        # вывести интерактивную форму "текст"
        form = canvas.acroForm
        # canvas.drawString(25, 780, '')
        form.textfield(
            name='comment',
            tooltip='comment',
            fontName='Times-Roman',
            fontSize=10,
            x=57,
            y=750,
            borderStyle='underlined',
            borderColor=black,
            fillColor=white,
            width=515,
            height=13,
            textColor=black,
            forceBorder=False,
        )

        # Вывести на первой странице код-номер договора
        barcode128.drawOn(canvas, 120 * mm, 283 * mm)

        # вывести внизу QR-code (ФИО, (номера направлений))
        qr_code = qr.QrCodeWidget(qr_value)
        qr_code.barWidth = 70
        qr_code.barHeight = 70
        qr_code.qrVersion = 1
        d = Drawing()
        d.add(qr_code)
        renderPDF.draw(d, canvas, 90 * mm, 7)
        # вывести атрибуты для подписей
        canvas.setFont('PTAstraSerifReg', 10)
        canvas.drawString(40 * mm, 10 * mm, '____________________________')
        canvas.drawString(115 * mm, 10 * mm, '/{}/____________________________'.format(npf))
        canvas.setFont('Symbola', 18)
        canvas.drawString(195 * mm, 10 * mm, '\u2713')

        canvas.setFont('PTAstraSerifReg', 8)
        canvas.drawString(50 * mm, 7 * mm, '(подпись сотрудника)')
        canvas.drawString(160 * mm, 7 * mm, '(подпись плательщика)')

        # вывестии защитны вертикальный мелкий текст
        canvas.rotate(90)
        canvas.setFillColor(HexColor(0x4F4B4B))
        canvas.setFont('PTAstraSerifReg', 5.2)
        canvas.drawString(10 * mm, -12 * mm, '{}'.format(6 * left_size_str))

        canvas.restoreState()

    def later_pages(canvas, document):
        canvas.saveState()
        # вывести внизу QR-code (ФИО, (номера направлений))
        qr_code = qr.QrCodeWidget(qr_value)
        qr_code.barWidth = 70
        qr_code.barHeight = 70
        qr_code.qrVersion = 1
        d = Drawing()
        d.add(qr_code)
        renderPDF.draw(d, canvas, 90 * mm, 7)
        # вывести атрибуты для подписей
        canvas.setFont('PTAstraSerifReg', 10)
        canvas.drawString(40 * mm, 10 * mm, '____________________________')
        canvas.drawString(115 * mm, 10 * mm, '/{}/____________________________'.format(npf))

        canvas.setFont('Symbola', 18)
        canvas.drawString(195 * mm, 10 * mm, '\u2713')

        canvas.setFont('PTAstraSerifReg', 8)
        canvas.drawString(50 * mm, 7 * mm, '(подпись сотрудника)')
        canvas.drawString(160 * mm, 7 * mm, '(подпись плательщика)')
        canvas.rotate(90)
        canvas.setFillColor(HexColor(0x4F4B4B))
        canvas.setFont('PTAstraSerifReg', 5.2)
        canvas.drawString(10 * mm, -12 * mm, '{}'.format(6 * left_size_str))
        canvas.restoreState()

    if contract_from_file and appendix_paragraphs:
        for section in appendix_paragraphs:
            if section.get('page_break'):
                objs.append(PageBreak())
                objs.append(Macro("canvas._pageNumber=1"))
            elif section.get('Spacer'):
                height_spacer = section.get('spacer_data')
                objs.append(Spacer(1, height_spacer * mm))
            elif section.get('HRFlowable'):
                objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
            elif section.get('patient_fio'):
                objs.append(Paragraph(f"{section['text']} {patient_data['fio']} ({patient_data['born']})", styles_obj[section['style']]))
            elif section.get('patient_addresses'):
                objs.append(Paragraph(f"{section['text']} {patient_data['main_address']}", styles_obj[section['style']]))
            elif section.get('patient_document'):
                objs.append(Paragraph(f"{section['text']} {patient_data['type_doc']} {p_doc_serial} {p_doc_num}", styles_obj[section['style']]))
            elif section.get('executor_l2'):
                objs.append(Paragraph(f"{section['text']} {exec_person}", styles_obj[section['style']]))
            else:
                objs.append(Paragraph(f"{section['text']}", styles_obj[section['style']]))

    if contract_from_file and appendix_route_list:
        for section in appendix_route_list:
            if section.get('page_break'):
                objs.append(PageBreak())
                objs.append(Macro("canvas._pageNumber=1"))
            elif section.get('Spacer'):
                height_spacer = section.get('spacer_data')
                objs.append(Spacer(1, height_spacer * mm))
            elif section.get('patient_fio'):
                objs.append(Paragraph(f"{section['text']} {patient_data['fio']} ({patient_data['born']})", styles_obj[section['style']]))
            else:
                objs.append(Paragraph(f"{section['text']}", styles_obj[section['style']]))

        tbl = Table(route_list, colWidths=(30 * mm, 100 * mm), hAlign='LEFT')
        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]
            )
        )

        objs.append(Spacer(1, 5 * mm))
        objs.append(tbl)

    doc.build(objs, onFirstPage=first_pages, onLaterPages=later_pages, canvasmaker=PageNumCanvasPartitionAll)

    pdf = buffer.getvalue()

    buffer.close()
    return pdf


def form_02(request_data):
    """
    Договор, включающий услуги на оплату и необходимые реквизиты. С Учетом представителей и Заказчиков(Плательщиков)
    у пациента
    """
    contract_id_param = request_data.get("contract_id", None)
    contract_id = None
    from_appendix_pages = request_data.get("from_appendix_pages")
    if contract_id_param:
        contract_id = json.loads(request_data.get("contract_id"))
    ind_card = Card.objects.get(pk=request_data["card_pk"])
    if not contract_id_param:
        work_dir = json.loads(request_data["napr_id"])
    else:
        work_dir = PersonContract.objects.values_list("dir_list", flat=True).get(pk=int(contract_id))
        work_dir = work_dir.split(",")
    napr = Napravleniya.objects.filter(pk__in=work_dir)

    dir_temp = []

    # Получить все источники, у которых title-ПЛАТНО
    ist_f = list(IstochnikiFinansirovaniya.objects.values_list('id').filter(title__exact='Платно'))
    ist_f_list = [int(x[0]) for x in ist_f]

    # Проверить, что все направления принадлежат к одной карте и имеют ист.финансирования "Платно"
    for n in napr:
        if n.istochnik_f_id in ist_f_list and n.client == ind_card:
            dir_temp.append(n.pk)

    if not dir_temp:
        return False

    result_contract = sort_direction_by_file_name_contract(tuple(dir_temp), '0')

    # получить уникальные номера контрактов
    unique_num_contract = list(set([i.num_contract for i in result_contract]))
    get_directions_list = PersonContract.objects.filter(num_contract__in=unique_num_contract)
    temp_directions_list = [i.dir_list.split(',') for i in get_directions_list]
    unique_directions_list = list(set([data for i in temp_directions_list for data in i]))
    result_contract = sort_direction_by_file_name_contract(tuple(unique_directions_list), '0')

    # получить структуру: [{"num_contract": "номера контракта", "file_name_contract": "шаблон контракта, "directions_contract": [направления контракта]}]
    temp_contract = {"file_name_contract": "", "num_contract": "", "directions_contract": []}
    sorted_contract_result = []
    count = 0
    prev_num_contract = None
    for i in result_contract:
        if not i.num_contract:
            continue
        if count != 0 and i.num_contract != prev_num_contract:
            sorted_contract_result.append(temp_contract.copy())
            temp_contract["directions_contract"] = list(set(temp_contract["directions_contract"]))
            temp_contract = {"num_contract": "", "file_name_contract": "", "directions_contract": []}
        temp_contract["num_contract"] = i.num_contract
        temp_contract["file_name_contract"] = i.file_name_contract
        temp_dir = temp_contract["directions_contract"]
        temp_dir.append(i.napravleniye_id)
        temp_contract["directions_contract"] = temp_dir.copy()
        prev_num_contract = i.num_contract
        count += 1
    temp_contract["directions_contract"] = list(set(temp_contract["directions_contract"]))
    sorted_contract_result.append(temp_contract.copy())

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    # Генерировать pdf-Лист на оплату
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Symbola', os.path.join(FONTS_FOLDER, 'Symbola.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=12 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=28 * mm, allowSplitting=1, title="Форма {}".format("Договор на оплату")
    )
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 9
    style.leading = 12
    style.spaceAfter = 0 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = 15

    styleAppendix = deepcopy(style)
    styleAppendix.fontSize = 9
    styleAppendix.firstLineIndent = 8
    styleAppendix.leading = 9

    styleFL = deepcopy(style)
    styleFL.firstLineIndent = 0
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleBoldCenter = deepcopy(styleBold)
    styleBoldCenter.alignment = TA_CENTER

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 9
    styleCenter.leading = 10
    styleCenter.spaceAfter = 0 * mm

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 20
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'

    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    styleTCenter = deepcopy(styleCenter)
    styleTCenter.alignment = TA_CENTER
    styleTCenter.leading = 3.5 * mm

    styleTBold = deepcopy(styleCenterBold)
    styleTBold.fontSize = 10
    styleTBold.alignment = TA_LEFT

    styles_obj = {'style': style, 'styleCenter': styleCenter, 'styleAppendix': styleAppendix, "styleBoldCenter": styleBoldCenter}

    styleTR = deepcopy(style)
    styleTR.alignment = TA_RIGHT

    objs: List[Union[Spacer, Paragraph, Table, KeepTogether]] = []
    direction_data = []
    for contract in sorted_contract_result:
        person_contract_data = PersonContract.objects.get(num_contract=contract["num_contract"])
        exec_person = request_data['user'].doctorprofile.get_full_fio()

        patient_data = person_contract_data.patient_card.get_data_individual()
        p_agent = person_contract_data.agent_card
        agent_status = None
        if p_agent:
            agent_status = True

        # Если владельцу карты меньше 15 лет и не передан представитель, то вернуть ошибку
        who_patient = 'пациента'
        if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i') and not agent_status:
            return False
        elif patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i') and agent_status:
            who_patient = 'ребёнка'

        if p_agent:
            person_data = p_agent.get_data_individual()
        else:
            person_data = patient_data

        p_payer = person_contract_data.payer_card
        if p_payer:
            payer_data = p_payer.get_data_individual()

        # получить УСЛУГИ по направлениям(отфильтрованы по "платно" и нет сохраненных исследований) в Issledovaniya
        research_direction = forms_func.get_research_by_dir(contract["directions_contract"], only_new=False)

        if not research_direction:
            return False

        # получить по направлению-услугам цену из Issledovaniya
        research_price = forms_func.get_coast_from_issledovanie(research_direction)

        # Получить Итоговую стр-ру данных
        result_data = forms_func.get_final_data(research_price)

        sum_research = result_data[1]

        # Контрольная сумма расчет: послдеовательность направлений+Итоговая сумма (стоимость денежная)
        qr_napr = ','.join([str(elem) for elem in result_data[3]])
        protect_val = sum_research.replace(' ', '')
        bstr = (qr_napr + protect_val).encode()
        protect_code = str(zlib.crc32(bstr))

        date_create = datetime.datetime.strftime(person_contract_data.create_at, '%y%m%d%H%M%S')
        date_now_str = f'{ind_card.pk}-{date_create}/{person_contract_data.pk}'
        book = person_contract_data.pk
        barcode128 = code128.Code128(book, barHeight=6 * mm, barWidth=1.25)
        contract_from_file = SettingManager.get("contract_from_file", default='False', default_type='b')
        if not os.path.join(BASE_DIR, 'forms', 'contract_forms', contract["file_name_contract"]):
            contract_file = os.path.join(BASE_DIR, 'forms', 'contract_forms', "default")
        else:
            contract_file = os.path.join(BASE_DIR, 'forms', 'contract_forms', contract["file_name_contract"])
        if contract_from_file:
            with open(contract_file) as json_file:
                data = json.load(json_file)
                contract_header = data['contract_header']
                body_paragraphs = data['body_paragraphs']
                org_contacts = data['org_contacts']
                executor = data['executor']
                appendix_paragraphs = data.get('appendix_paragraphs', None)
                appendix_route_list = data.get('appendix_route_list', None)
                appendix_direction_list = data.get('appendix_direction_list', None)
                ticket_list = data.get('ticket_list', None)
        else:
            executor = None

        objs.append(Spacer(1, 11 * mm))
        objs.append(Paragraph(f'ДОГОВОР &nbsp;&nbsp; № <u>{date_now_str}</u>', styleCenter))
        objs.append(Spacer(1, 1 * mm))
        objs.append(Paragraph('НА ОКАЗАНИЕ ПЛАТНЫХ МЕДИЦИНСКИХ УСЛУГ НАСЕЛЕНИЮ', styleCenter))

        date_contract = pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=person_contract_data.create_at)

        opinion = [
            [Paragraph('г. Иркутск', style), Paragraph('{} года'.format(date_contract), styleTR)],
        ]

        tbl = Table(opinion, colWidths=(95 * mm, 95 * mm))

        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                ]
            )
        )
        date_tbl = tbl

        objs.append(Spacer(1, 5 * mm))
        objs.append(tbl)

        objs.append(Spacer(1, 0.5 * mm))

        hospital: Hospitals = request_data["hospital"]

        hospital_short_name = hospital.safe_short_title
        hospital_address = hospital.safe_address

        if contract_from_file:
            objs.append(Paragraph('{}'.format(contract_header), style))
        else:
            return False
        them_contract = 'настоящий договор о нижеследующем:'
        client_who = 'Заказчик'
        is_payer = False
        # Добавдяем представителя (мать, отец, опекун или др. не дееспособный)
        is_pagent = False
        # представитель==Заказчик ()
        payer_fio = None
        if (p_payer is None) or (p_payer == p_agent) or (p_agent and p_payer is None):
            payer_fio = person_data['fio']
            is_pagent = True
            p_agent_who = client_who + " (представитель пациента)"
        else:
            p_agent_who = "Представитель пациента"

        # Если Заказчик(Плательщик) другое физ лицо отдельный Заказчик, отдельно Представитель, отдельно пациент
        if p_payer and (p_payer != p_agent):
            client_side = ''
            if p_agent is None:
                client_side = ', с другой стороны, заключили в интересах Пациента (Потребителя)'
            is_payer = True
            payer_fio = payer_data['fio']
            objs.append(
                Paragraph(
                    '<font fontname ="PTAstraSerifBold">{}: </font> {}, дата рождения {} г., '
                    'паспорт: {}-{} '
                    'выдан {} г. '
                    'кем: {} '
                    'адрес регистрации: {}, '
                    'адрес проживания: {} {}'.format(
                        client_who,
                        payer_data['fio'],
                        payer_data['born'],
                        payer_data['passport_serial'],
                        payer_data['passport_num'],
                        payer_data['passport_date_start'],
                        payer_data['passport_issued'],
                        payer_data['main_address'],
                        payer_data['fact_address'],
                        client_side,
                    ),
                    style,
                )
            )

        if p_agent:
            client_side = ', с другой стороны, заключили в интересах Пациента (Потребителя)'
            objs.append(
                Paragraph(
                    '<font fontname ="PTAstraSerifBold"> {}: </font> {} ({} {}), дата рождения {} г., '
                    'паспорт: {}-{} '
                    'выдан {} г. '
                    'кем: {} '
                    'адрес регистрации: {}, '
                    'адрес проживания: {} {}'.format(
                        p_agent_who,
                        person_data['fio'],
                        ind_card.get_who_is_agent_display(),
                        who_patient,
                        person_data['born'],
                        person_data['passport_serial'],
                        person_data['passport_num'],
                        person_data['passport_date_start'],
                        person_data['passport_issued'],
                        person_data['main_address'],
                        person_data['fact_address'],
                        client_side,
                    ),
                    style,
                )
            )

        # Добавдяем потребителя услуги (пациента)
        if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i'):
            p_doc_serial, p_doc_num, p_doc_start = patient_data['bc_serial'], patient_data['bc_num'], patient_data['bc_date_start']
            p_doc_issued = patient_data['bc_issued']
        else:
            p_doc_serial, p_doc_num, p_doc_start = patient_data['passport_serial'], patient_data['passport_num'], patient_data['passport_date_start']
            p_doc_issued = patient_data['passport_issued']

        # Пациент==Заказчик
        if p_payer is None and p_agent is None:
            p_who = client_who + " - Пациент (потребитель)"
            client_side = ', с другой стороны, заключили настоящий договор о нижеследующем:'
            them_contract = ''
        else:
            p_who = "Пациент (потребитель)"
            client_side = ''

        objs.append(
            Paragraph(
                '<font fontname ="PTAstraSerifBold"> {}:</font> {}, дата рождения {} г.,'
                '{}: {}-{} '
                'выдан {} г. '
                'кем: {} '
                'адрес регистрации: {}, '
                'адрес проживания: {} {} '.format(
                    p_who,
                    patient_data['fio'],
                    patient_data['born'],
                    patient_data['type_doc'],
                    p_doc_serial,
                    p_doc_num,
                    p_doc_start,
                    p_doc_issued,
                    patient_data['main_address'],
                    patient_data['fact_address'],
                    client_side,
                ),
                style,
            )
        )

        objs.append(Paragraph('{}'.format(them_contract), styleFL))
        objs.append(Spacer(1, 2 * mm))
        contract_add_header = deepcopy(objs)

        objs.append(Spacer(1, 2 * mm))
        # objs.append(Paragraph('{}'.format(tr), style))

        styleTB = deepcopy(style)
        styleTB.firstLineIndent = 0
        styleTB.fontSize = 8.5
        styleTB.alignment = TA_CENTER
        styleTB.fontName = "PTAstraSerifBold"

        styleTC = deepcopy(style)
        styleTC.firstLineIndent = 0
        styleTC.fontSize = 8.5
        styleTC.alignment = TA_LEFT

        styleTCright = deepcopy(styleTC)
        styleTCright.alignment = TA_RIGHT

        styleTCcenter = deepcopy(styleTC)
        styleTCcenter.alignment = TA_CENTER

        # Всегда заголовки одинаково со скидкой
        opinion = [
            [
                Paragraph('Код услуги', styleTB),
                Paragraph('Направление', styleTB),
                Paragraph('Услуга', styleTB),
                Paragraph('Цена,<br/>руб.', styleTB),
                Paragraph('Скидка<br/>Наценка<br/>%', styleTB),
                Paragraph('Цена со<br/> скидкой,<br/>руб.', styleTB),
                Paragraph('Кол-во, усл.', styleTB),
                Paragraph('Сумма, руб.', styleTB),
            ],
        ]

        # example_template = [
        #     ['1.2.3','4856397','Полный гематологический анализ','1000.00','0','1000.00','1','1000.00'],
        #     ['1.2.3','','РМП','2500.45','0','2500.45','1','2500.45'],
        #     ['1.2.3', '4856398', 'УЗИ брюшной полости', '3500.49', '0', '3500.49', '1', '3500.49'],
        #     ['1.2.3','4856398','Эзофагогастродуоденоскопия','5700.99','0','5700.99','1','5700.99']
        # ]
        #

        example_template = result_data[0]

        list_g = []
        route_list = [[Paragraph('Направление', styleTB), Paragraph('Услуга', styleTB), Paragraph('Примечание', styleTB), Paragraph(' Ш/к', styleTB)]]
        # используется range(len()) - к определенной колонке (по номеру) применяется свое свойство
        for i in range(len(example_template)):
            list_t = []
            for j in range(len(example_template[i]) - 2):
                if j in (3, 5, 7):
                    s = styleTCright
                elif j in (4, 6):
                    s = styleTCcenter
                else:
                    s = styleTC
                list_t.append(Paragraph(example_template[i][j], s))
            list_g.append(list_t)
            if example_template[i][1]:
                barcode = code128.Code128(example_template[i][1], barHeight=5 * mm, barWidth=1.25, lquiet=1 * mm)
            else:
                barcode = Paragraph('', styleTC)
            comment_strip = example_template[i][8][0:40].replace('<', '').replace('>', '')
            research_title = example_template[i][9] if example_template[i][9] else example_template[i][2]
            route_list.append([Paragraph(example_template[i][1], styleTC), Paragraph(research_title, styleTC), Paragraph(comment_strip, styleTC), barcode])

        opinion.extend(list_g)

        sum_research_decimal = sum_research.replace(' ', '')

        tbl = Table(opinion, colWidths=(18 * mm, 19 * mm, 52 * mm, 22 * mm, 21 * mm, 22 * mm, 13 * mm, 25 * mm))

        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]
            )
        )

        # objs.append(tbl)
        # objs.append(Spacer(1, 1 * mm))
        # objs.append(Paragraph('<font size=12> Итого: {}</font>'.format(sum_research), styleTCright))
        # objs.append(Spacer(1, 2 * mm))
        # objs.append(Spacer(1, 3 * mm))

        s = pytils.numeral.rubles(float(sum_research_decimal))
        end_date = date.today() + relativedelta(days=+10)
        end_date1 = datetime.datetime.strftime(end_date, "%d.%m.%Y")
        tbl_price = tbl
        if contract_from_file:
            for section in body_paragraphs:
                objs = check_section_param(objs, s, styles_obj, sum_research, styleTCright, section, tbl_price)

        styleAtr = deepcopy(style)
        styleAtr.firstLineIndent = 0
        # Данные исполнителя в Договоре
        fio_director_list = exec_person.split(' ')
        dir_f = fio_director_list[0]
        dir_n = fio_director_list[1]
        dir_p = fio_director_list[2]
        dir_npf = dir_n[0:1] + '.' + ' ' + dir_p[0:1] + '.' + ' ' + dir_f
        if executor:
            dir_npf = executor

        space_symbol = '&nbsp;'

        # Данные плательщика в Договоре
        npf = ''
        if payer_fio:
            fio_list = payer_fio.split(' ')
            f = fio_list[0]
            n = fio_list[1][0:1] + '.'
            p = fio_list[2][0:1] + '.' if len(fio_list) > 2 else ''
            npf = n + ' ' + p + ' ' + f

        # Данные пациента в Договоре
        patient_list = patient_data['fio'].split(' ')
        pf = patient_list[0]
        pn = patient_list[1][0:1] + '.'
        pp = patient_list[2][0:1] + '.' if len(patient_list) > 2 else ''
        p_npf = pn + ' ' + pp + ' ' + pf

        rowHeights = None

        # Ниже реквизиты в таблице. Возможные варианты: Заказчик(Пациент), Заказчик + Пациент, Заказчик+Представитель+Пациент (Ужасно)
        # Если есть отдельный заказчик
        row_count = 0
        if contract_from_file:
            hospital_address = org_contacts
        if is_payer:
            row_count = 0
            opinion = [
                [
                    Paragraph('<font fontname ="PTAstraSerifBold">Исполнитель</font>', styleAtr),
                    Paragraph('', styleAtr),
                    Paragraph('<font fontname ="PTAstraSerifBold">{}:</font>'.format(client_who), styleAtr),
                ],
                [
                    Paragraph('{} <br/>{}'.format("", hospital_address), styleAtr),
                    Paragraph('', styleAtr),
                    Paragraph(
                        '{}<br/>Паспорт: {}-{}<br/>Адрес:{}'.format(payer_data['fio'], payer_data['passport_serial'], payer_data['passport_num'], payer_data['main_address']), styleAtr
                    ),
                ],
                [Paragraph('', styleAtr), Paragraph('', style), Paragraph('', styleAtr)],
                [Paragraph('Сотрудник {}'.format(""), styleAtr), Paragraph('', styleAtr), Paragraph('', styleAtr)],
                [
                    Paragraph('________________________/{}/'.format(dir_npf), styleAtr),
                    Paragraph('', styleAtr),
                    Paragraph('/{}/________________________ <font face="Symbola" size=18>\u2713</font>'.format(npf), styleAtr),
                ],
            ]
            row_count = row_count + len(opinion)

            # Если Заказчик и представитель разные лица. Добавить представителя
            if p_agent:
                agent_list = person_data['fio'].split(' ')
                af = agent_list[0]
                an = agent_list[1]
                ap = agent_list[2][0:1] if len(agent_list) > 2 else ''
                a_npf = an + '.' + ' ' + ap + '.' + ' ' + af

                opinion_agent = [
                    [Paragraph('', styleAtr), Paragraph('', style), Paragraph('', styleAtr)],
                    [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('', styleAtr)],
                    [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('<font fontname ="PTAstraSerifBold">{}:</font>'.format(p_agent_who), styleAtr)],
                    [
                        Paragraph('', styleAtr),
                        Paragraph('', styleAtr),
                        Paragraph(
                            '{}<br/>{}: {}-{}<br/>Адрес:{}'.format(
                                person_data['fio'], person_data['type_doc'], person_data['passport_serial'], person_data['passport_num'], person_data['main_address']
                            ),
                            styleAtr,
                        ),
                    ],
                    [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('/{}/________________________ <font face="Symbola" size=18>\u2713</font>'.format(a_npf), styleAtr)],
                ]
                opinion.extend(opinion_agent)
                row_count = row_count + len(opinion_agent)

            # Добавить Пациента
            opinion_patient = [
                [Paragraph('', styleAtr), Paragraph('', style), Paragraph('', styleAtr)],
                [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('', styleAtr)],
                [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('<font fontname ="PTAstraSerifBold">{}:</font>'.format(p_who), styleAtr)],
                [
                    Paragraph('', styleAtr),
                    Paragraph('', styleAtr),
                    Paragraph('{}<br/>{}: {}-{}<br/>Адрес:{}'.format(patient_data['fio'], patient_data['type_doc'], p_doc_serial, p_doc_num, patient_data['main_address']), styleAtr),
                ],
            ]

            parient_sign = [
                [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('/{}/________________________ <font face="Symbola" size=18>\u2713</font>'.format(p_npf), styleAtr)],
            ]

            if not p_agent:
                opinion_patient.extend(parient_sign)

            row_count = row_count + len(opinion_patient)

            opinion.extend(opinion_patient)

            rowHeights = row_count * [None]
            rowHeights[4] = 35
            rowHeights[9] = 35

        # Таблица для Заказчика-представителя
        if is_pagent and not is_payer:
            row_count = 0
            opinion = [
                [
                    Paragraph('<font fontname ="PTAstraSerifBold">Исполнитель</font>', styleAtr),
                    Paragraph('', styleAtr),
                    Paragraph('<font fontname ="PTAstraSerifBold">{}:</font>'.format(p_agent_who), styleAtr),
                ],
                [
                    Paragraph('{} <br/>{}'.format("", hospital_address), styleAtr),
                    Paragraph('', styleAtr),
                    Paragraph(
                        '{}<br/>Паспорт: {}-{}<br/>Адрес:{}'.format(person_data['fio'], person_data['passport_serial'], person_data['passport_num'], person_data['main_address']), styleAtr
                    ),
                ],
                [Paragraph('', styleAtr), Paragraph('', style), Paragraph('', styleAtr)],
                [Paragraph('Сотрудник {}'.format(""), styleAtr), Paragraph('', styleAtr), Paragraph('', styleAtr)],
                [
                    Paragraph('________________________/{}/'.format(dir_npf), styleAtr),
                    Paragraph('', styleAtr),
                    Paragraph('/{}/________________________ <font face="Symbola" size=18>\u2713</font>'.format(npf), styleAtr),
                ],
            ]
            row_count = row_count + len(opinion)

            # Таблица для Пациента
            opinion_patient = [
                [Paragraph('', styleAtr), Paragraph('', style), Paragraph('', styleAtr)],
                [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('', styleAtr)],
                [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('<font fontname ="PTAstraSerifBold">{}:</font>'.format(p_who), styleAtr)],
                [
                    Paragraph('', styleAtr),
                    Paragraph('', styleAtr),
                    Paragraph('{}<br/>{}: {}-{}<br/>Адрес:{}'.format(patient_data['fio'], patient_data['type_doc'], p_doc_serial, p_doc_num, patient_data['main_address']), styleAtr),
                ],
                # [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('', styleAtr)],
                [Paragraph('', styleAtr), Paragraph('', styleAtr), Paragraph('', styleAtr)],
            ]
            row_count = row_count + len(opinion_patient)

            opinion.extend(opinion_patient)
            rowHeights = row_count * [None]
            rowHeights[4] = 35
            rowHeights[9] = 35

        # Выводим Заказчик-Пациент(потребитель) - одно лицо
        if (not p_payer) and (not p_agent):
            row_count = 0
            opinion = [
                [
                    Paragraph('<font fontname ="PTAstraSerifBold">Исполнитель</font>', styleAtr),
                    Paragraph('', styleAtr),
                    Paragraph('<font fontname ="PTAstraSerifBold">{}:</font>'.format(p_who), styleAtr),
                ],
                [
                    Paragraph('{} <br/>{}'.format("", hospital_address), styleAtr),
                    Paragraph('', styleAtr),
                    Paragraph(
                        '{}<br/>Паспорт: {}-{}<br/>Адрес:{}'.format(patient_data['fio'], patient_data['passport_serial'], patient_data['passport_num'], patient_data['main_address']),
                        styleAtr,
                    ),
                ],
                [Paragraph('', styleAtr), Paragraph('', style), Paragraph('', styleAtr)],
                [Paragraph('Сотрудник {}'.format(""), styleAtr), Paragraph('', styleAtr), Paragraph('', styleAtr)],
                [
                    Paragraph('________________________/{}/'.format(dir_npf), styleAtr),
                    Paragraph('', styleAtr),
                    Paragraph('/{}/________________________ <font face="Symbola" size=18>\u2713</font>'.format(npf), styleAtr),
                ],
            ]
            row_count = row_count + 5
            rowHeights = row_count * [None]
            rowHeights[4] = 35

        # Строим необходимую таблицу
        tbl = Table(opinion, colWidths=(90 * mm, 10 * mm, 90 * mm), rowHeights=rowHeights)
        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
                    ('TOPPADDING', (0, 0), (-1, -1), 1.5 * mm),
                    ('VALIGN', (0, 0), (-1, -2), 'TOP'),
                    ('VALIGN', (0, 4), (-1, 4), 'BOTTOM'),
                    # ('VALIGN', (1, 4), (-1, -1), 'BOTTOM'),
                    ('BOTTOMPADDING', (-1, 4), (-1, 4), 4.2 * mm),
                    ('BOTTOMPADDING', (0, -1), (0, -1), 1 * mm),
                    ('BOTTOMPADDING', (-1, -1), (-1, -1), 4.2 * mm),
                ]
            )
        )

        objs.append(Spacer(1, 2 * mm))

        # Заголовок Адреса и реквизиты + сами реквизиты всегда вместе, если разрыв на странице
        contract_add_org_contracts = deepcopy(tbl)
        objs.append(KeepTogether([Paragraph('АДРЕСА И РЕКВИЗИТЫ СТОРОН', styleCenter), tbl]))
        objs.append(Spacer(1, 7 * mm))

        styleRight = deepcopy(style)
        styleRight.alignment = TA_RIGHT

        space_symbol = ' '

        left_size_str = hospital_short_name + 15 * space_symbol + protect_code + 15 * space_symbol

        qr_value = protect_code + ',' + npf + '(' + qr_napr + ')' + protect_val

        if npf != p_npf:
            qr_value = protect_code + ',' + npf + '-' + p_npf + '(' + qr_napr + ')' + protect_val

        if contract_from_file and appendix_paragraphs:
            for section in appendix_paragraphs:
                if section.get('page_break'):
                    objs.append(PageBreak())
                    objs.append(Macro("canvas._pageNumber=1"))
                elif section.get('Spacer'):
                    height_spacer = section.get('spacer_data')
                    objs.append(Spacer(1, height_spacer * mm))
                elif section.get('HRFlowable'):
                    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
                elif section.get('patient_fio'):
                    objs.append(Paragraph(f"{section['text']} {patient_data['fio']} ({patient_data['born']})", styles_obj[section['style']]))
                elif section.get('patient_addresses'):
                    objs.append(Paragraph(f"{section['text']} {patient_data['main_address']}", styles_obj[section['style']]))
                elif section.get('patient_document'):
                    objs.append(Paragraph(f"{section['text']} {patient_data['type_doc']} {p_doc_serial} {p_doc_num}", styles_obj[section['style']]))
                elif section.get('executor_l2'):
                    objs.append(Paragraph(f"{section['text']} {exec_person}", styles_obj[section['style']]))
                else:
                    objs.append(Paragraph(f"{section['text']}", styles_obj[section['style']]))

        if contract_from_file and appendix_route_list:
            for section in appendix_route_list:
                if section.get('page_break'):
                    objs.append(PageBreak())
                    objs.append(Macro("canvas._pageNumber=1"))
                elif section.get('Spacer'):
                    height_spacer = section.get('spacer_data')
                    objs.append(Spacer(1, height_spacer * mm))
                elif section.get('patient_fio'):
                    objs.append(Paragraph(f"{section['text']} {patient_data['fio']} ({patient_data['born']})", styles_obj[section['style']]))
                else:
                    objs.append(Paragraph(f"{section['text']}", styles_obj[section['style']]))

            tbl = Table(route_list, colWidths=(30 * mm, 58 * mm, 60 * mm, 42 * mm), hAlign='LEFT')
            tbl.setStyle(
                TableStyle(
                    [
                        ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]
                )
            )

            objs.append(Spacer(1, 5 * mm))
            objs.append(tbl)

        if contract_from_file and appendix_direction_list:
            types_direction = {"islab": set(), "isDocrefferal": set(), "isParaclinic": set(), "isGistology": set()}
            for d in result_data[3]:
                iss_obj = Issledovaniya.objects.filter(napravleniye_id=d).first()
                if iss_obj.research.is_doc_refferal:
                    types_direction["isDocrefferal"].add(d)
                elif iss_obj.research.is_paraclinic:
                    types_direction["isParaclinic"].add(d)
                elif iss_obj.research.is_paraclinic:
                    types_direction["isGistology"].add(d)
                elif (
                    not iss_obj.research.is_form
                    and not iss_obj.research.is_citology
                    and not iss_obj.research.is_gistology
                    and not iss_obj.research.is_stom
                    and not iss_obj.research.is_application
                    and not iss_obj.research.is_direction_params
                    and not iss_obj.research.is_microbiology
                    and not iss_obj.research.is_treatment
                ):
                    types_direction["islab"].add(d)

            for section in appendix_direction_list:
                if section.get('islab'):
                    direction_data.extend(list(types_direction["islab"]))
                elif section.get('isDocrefferal'):
                    direction_data.extend(list(types_direction["isDocrefferal"]))
                elif section.get('isParaclinic'):
                    direction_data.extend(list(types_direction["isParaclinic"]))

        if contract_from_file and ticket_list:
            for ticket_section in ticket_list:
                if ticket_section.get('page_break'):
                    objs.append(PageBreak())
                    objs.append(Macro("canvas._pageNumber=1"))
                elif ticket_section.get('Spacer'):
                    height_spacer = ticket_section.get('spacer_data')
                    objs.append(Spacer(1, height_spacer * mm))
                elif ticket_section.get('contract_add_header'):
                    objs.extend(contract_add_header)
                elif ticket_section.get('body_adds_paragraphs'):
                    for section in ticket_section.get('body_adds_paragraphs'):
                        objs = check_section_param(objs, s, styles_obj, sum_research, styleTCright, section, tbl_price, date_tbl)
            objs.append(Spacer(1, 2 * mm))
            objs.append(KeepTogether([Paragraph('АДРЕСА И РЕКВИЗИТЫ СТОРОН', styleCenter), contract_add_org_contracts]))

    def first_pages(canvas, document):
        canvas.saveState()
        canvas.setFont("PTAstraSerifReg", 9)
        # вывести интерактивную форму "текст"
        form = canvas.acroForm
        # canvas.drawString(25, 780, '')
        form.textfield(
            name='comment',
            tooltip='comment',
            fontName='Times-Roman',
            fontSize=10,
            x=57,
            y=750,
            borderStyle='underlined',
            borderColor=black,
            fillColor=white,
            width=515,
            height=13,
            textColor=black,
            forceBorder=False,
        )

        # Вывести на первой странице код-номер договора
        barcode128.drawOn(canvas, 10 * mm, 282 * mm)

        # вывести внизу QR-code (ФИО, (номера направлений))
        qr_code = qr.QrCodeWidget(qr_value)
        qr_code.barWidth = 70
        qr_code.barHeight = 70
        qr_code.qrVersion = 1
        d = Drawing()
        d.add(qr_code)
        renderPDF.draw(d, canvas, 90 * mm, 7)
        # вывести атрибуты для подписей
        canvas.setFont('PTAstraSerifReg', 10)
        canvas.drawString(40 * mm, 10 * mm, '____________________________')
        canvas.drawString(115 * mm, 10 * mm, '/{}/____________________________'.format(npf))
        canvas.setFont('Symbola', 18)
        canvas.drawString(195 * mm, 10 * mm, '\u2713')

        canvas.setFont('PTAstraSerifReg', 8)
        canvas.drawString(50 * mm, 7 * mm, '(подпись сотрудника)')
        canvas.drawString(160 * mm, 7 * mm, '(подпись плательщика)')

        # вывестии защитны вертикальный мелкий текст
        canvas.rotate(90)
        canvas.setFillColor(HexColor(0x4F4B4B))
        canvas.setFont('PTAstraSerifReg', 5.2)
        canvas.drawString(10 * mm, -12 * mm, '{}'.format(6 * left_size_str))

        canvas.restoreState()

    def later_pages(canvas, document):
        canvas.saveState()
        # вывести внизу QR-code (ФИО, (номера направлений))
        qr_code = qr.QrCodeWidget(qr_value)
        qr_code.barWidth = 70
        qr_code.barHeight = 70
        qr_code.qrVersion = 1
        d = Drawing()
        d.add(qr_code)
        renderPDF.draw(d, canvas, 90 * mm, 7)
        # вывести атрибуты для подписей
        canvas.setFont('PTAstraSerifReg', 10)
        canvas.drawString(40 * mm, 10 * mm, '____________________________')
        canvas.drawString(115 * mm, 10 * mm, '/{}/____________________________'.format(npf))

        canvas.setFont('Symbola', 18)
        canvas.drawString(195 * mm, 10 * mm, '\u2713')

        canvas.setFont('PTAstraSerifReg', 8)
        canvas.drawString(50 * mm, 7 * mm, '(подпись сотрудника)')
        canvas.drawString(160 * mm, 7 * mm, '(подпись плательщика)')
        canvas.rotate(90)
        canvas.setFillColor(HexColor(0x4F4B4B))
        canvas.setFont('PTAstraSerifReg', 5.2)
        canvas.drawString(10 * mm, -12 * mm, '{}'.format(6 * left_size_str))
        canvas.restoreState()

    doc.build(objs, onFirstPage=first_pages, onLaterPages=later_pages)

    pdf = buffer.getvalue()

    if SettingManager.get("print_direction_after_contract", default='False', default_type='b') and len(direction_data) > 0 and not from_appendix_pages:
        direction_obj = HttpRequest()
        direction_obj._body = json.dumps({"napr_id": direction_data})
        direction_obj.user = request_data['user']
        fc = f_print_direction(direction_obj)
        if fc:
            fc_buf = BytesIO()
            fc_buf.write(fc.content)
            fc_buf.seek(0)
            buffer.seek(0)
            from pdfrw import PdfReader, PdfWriter

            today = datetime.datetime.now()
            date_now1 = datetime.datetime.strftime(today, "%y%m%d%H%M%S%f")[:-3]
            date_now_str = str(ind_card.pk) + str(date_now1)
            dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
            file_dir = os.path.join(dir_param, date_now_str + '_dir.pdf')
            file_contract = os.path.join(dir_param, date_now_str + '_contract.pdf')
            save_tmp_file(fc_buf, filename=file_dir)
            save_tmp_file(buffer, filename=file_contract)
            pdf_all = BytesIO()
            inputs = [file_contract, file_dir]
            writer = PdfWriter()
            for inpfn in inputs:
                writer.addpages(PdfReader(inpfn).pages)
            writer.write(pdf_all)
            pdf_out = pdf_all.getvalue()
            pdf_all.close()
            buffer.close()
            os.remove(file_dir)
            os.remove(file_contract)
            fc_buf.close()
            return pdf_out

    buffer.close()
    return pdf


def check_section_param(objs, s, styles_obj, sum_research, styleTCright, section, tbl_price, date_tbl=None):
    if section.get('is_price'):
        objs.append(Paragraph('{} <font fontname = "PTAstraSerifBold"> <u> {} </u></font>'.format(section['text'], s.capitalize()), styles_obj[section['style']]))
    elif section.get('is_researches'):
        objs.append(tbl_price)
        objs.append(Spacer(1, 1 * mm))
        objs.append(Paragraph('<font size=12> Итого: {}</font>'.format(sum_research), styleTCright))
        objs.append(Spacer(1, 2 * mm))
        objs.append(Spacer(1, 3 * mm))
    elif section.get('Spacer'):
        height_spacer = section.get('spacer_data')
        objs.append(Spacer(1, height_spacer * mm))
    elif section.get('Date'):
        objs.append(Spacer(1, 2 * mm))
        objs.append(date_tbl)
        objs.append(Spacer(1, 2 * mm))
    else:
        objs.append(Paragraph(section['text'], styles_obj[section['style']]))
    return objs


def form_03(request_data):
    """
    Шаблон договора с юрлицами
    """
    price_id = request_data.get("priceId", 1)
    result = get_research_data_for_contract_specification(price_id)
    result = [{"code": i.research_code, "title": i.research_title, "coast": i.coast, "counts": i.number_services_by_contract} for i in result]

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Symbola', os.path.join(FONTS_FOLDER, 'Symbola.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=12 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=28 * mm, allowSplitting=1, title="Форма {}".format("Договор на оплату")
    )

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 11
    style.leading = 13
    style.spaceAfter = 0 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = 15

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleBoldCenter = deepcopy(styleBold)
    styleBoldCenter.alignment = TA_CENTER

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.spaceAfter = 0 * mm

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 20
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'

    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    styleTCenter = deepcopy(styleCenter)
    styleTCenter.alignment = TA_CENTER
    styleTCenter.leading = 3.5 * mm
    styleTCenter.firstLineIndent = 0
    style.fontSize = 9

    styleTBold = deepcopy(styleCenterBold)
    styleTBold.fontSize = 10
    styleTBold.alignment = TA_LEFT

    styleAppendix = deepcopy(style)
    styleAppendix.fontSize = 9
    styleAppendix.firstLineIndent = 8
    styleAppendix.leading = 9

    styleTB = deepcopy(style)
    styleTB.firstLineIndent = 0
    styleTB.fontSize = 9

    styleTR = deepcopy(style)
    styleTR.alignment = TA_RIGHT
    styleTB.fontSize = 9

    styles_obj = {'style': style, 'styleCenter': styleCenter, 'styleAppendix': styleAppendix, "styleBoldCenter": styleBoldCenter, "styleTR": styleTR}

    contract_file_partner = SettingManager.get("contract_from_file_partner", default='', default_type='s')
    if not os.path.join(
        BASE_DIR,
        'forms',
        'contract_forms',
    ):
        contract_file = os.path.join(BASE_DIR, 'forms', 'contract_forms', "contract_file_partner.json")
    else:
        contract_file = os.path.join(BASE_DIR, 'forms', 'contract_forms', contract_file_partner)
    objs = []
    if contract_file:
        with open(contract_file) as json_file:
            data = json.load(json_file)
            body_paragraphs = data['body_paragraphs']

    objs.append(Spacer(1, 5 * mm))
    price_spec = [[Paragraph('Код', styleTCenter), Paragraph('Услуга', styleTCenter), Paragraph('Кол-во', styleTCenter), Paragraph('Цена', styleTCenter), Paragraph('Итого', styleTCenter)]]
    for i in result:
        price_spec.append(
            [
                Paragraph(i.get('code', "0"), styleTB),
                Paragraph(i.get('title', "-"), styleTB),
                Paragraph(str(i.get("counts", 0)), styleTCenter),
                Paragraph(str(i.get('coast', 0)), styleTR),
                Paragraph(str(i.get("counts", 0) * i.get('coast', 0)), styleTR),
            ]
        )

    tbl = Table(price_spec, colWidths=(33 * mm, 85 * mm, 19 * mm, 24 * mm, 24 * mm), hAlign='LEFT')
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
    )

    if contract_file:
        for section in body_paragraphs:
            objs = partner_check_section_param(objs, styles_obj, section, tbl)

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def partner_check_section_param(objs, styles_obj, section, tbl_specification):
    space_symbol = '&nbsp;'
    if section.get('Spacer'):
        height_spacer = section.get('spacer_data')
        objs.append(Spacer(1, height_spacer * mm))
    elif section.get('page_break'):
        objs.append(PageBreak())
    elif section.get('specification'):
        objs.append(tbl_specification)
    elif section.get('List_data'):
        data = section.get('List_data').split("@#")
        s = ""
        for i in data:
            if "space_symbol" in i:
                space_result = i.split("*")
                s = f"{s} {space_symbol * int(space_result[1])}"
                continue
            s = s + i
        objs.append(Paragraph(s, styles_obj[section['style']]))
    else:
        objs.append(Paragraph(f"{section['text']}", styles_obj[section['style']]))
    return objs
