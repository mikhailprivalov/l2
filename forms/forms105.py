from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, FrameBreak, Table, \
    TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, StyleSheet1
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.graphics.barcode import code128
import datetime
import locale
import sys
import os.path
from io import BytesIO
from . import forms_func
from datetime import *
from dateutil.relativedelta import *
from directions.models import Napravleniya, IstochnikiFinansirovaniya, Issledovaniya
from clients.models import Card, Document
from laboratory.settings import FONTS_FOLDER
import simplejson as json
from contracts.models import PriceName
from datetime import *
from dateutil.relativedelta import *
import datetime
import locale
import sys
import pytils
from appconf.manager import SettingManager


def form_01(request_data):
    """
    Договор, включающий услуги на оплату и необходимые реквизиты
    """
    form_name = "Лист на оплату"

    ind_card = Card.objects.get(pk=request_data["card_pk"])
    ind = ind_card.individual
    ind_doc = Document.objects.filter(individual=ind, is_active=True)
    ind_dir = json.loads(request_data["dir"])

    # Получить данные с клиента физлицо-ФИО, пол, дата рождения
    individual_fio = ind.fio()
    individual_sex = ind.sex
    individual_date_born = ind.bd()

    # Получить все источники, у которых title-ПЛАТНО
    ist_f = []
    ist_f = list(IstochnikiFinansirovaniya.objects.values_list('id').filter(title__exact='Платно'))
    ist_f_list = []
    ist_f_list = ([int(x[0]) for x in ist_f])


    napr = Napravleniya.objects.filter(id__in=ind_dir)
    dir_temp = []

    #Проверить, что все направления принадлежат к одной карте и имеют ист. финансирования "Платно"
    for n in napr:
        if (n.istochnik_f_id in ist_f_list) and (n.client ==ind_card):
            dir_temp.append(n.pk)

    # Получить объект прайс по источнику "платно" из всех видов источников имеющих title платно, берется первое значение
    price_modifier_obj= PriceName.get_price(ist_f_list[0])

    # получить УСЛУГИ по направлениям(отфильтрованы по "платно" и нет сохраненных исследований) в Issledovaniya
    research_direction = forms_func.get_research_by_dir(dir_temp)

    # получить по направлению-услугам цену из Issledovaniya
    # research_price = forms_func.get_coast(research_direction, price_modifier_obj)
    research_price = forms_func.get_coast_from_issledovanie(research_direction)

    result_data = forms_func.get_final_data(research_price)

    hospital_name = "ОГАУЗ \"Иркутская медикосанитарная часть № 2\""
    hospital_address = "г. Иркутс, ул. Байкальская 201"
    hospital_kod_ogrn = "1033801542576"
    hospital_okpo = "31348613"

    # Получить данные физлицо-документы: паспорт, полис, снилс
    document_passport = "Паспорт РФ"
    documents = forms_func.get_all_doc(ind_doc)
    document_passport_num = documents['passport']['num']
    document_passport_serial = documents['passport']['serial']
    document_passport_date_start = documents['passport']['date_start']
    document_passport_issued = documents['passport']['issued']
    document_polis = documents['polis']['num']
    document_snils = documents['snils']['num']


    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    # Генерировать pdf-Лист на оплату
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=10 * mm,
                            rightMargin=5 * mm, topMargin=6 * mm,
                            bottomMargin=5 * mm, allowSplitting=1,
                            title="Форма {}".format("Лист на оплату"))
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 9
    style.leading = 12
    style.spaceAfter = 0 * mm
    style.alignment = TA_JUSTIFY
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
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

    objs = []

    today = datetime.datetime.now()
    date_now1 = datetime.datetime.strftime(today, "%Y%m%d%H%M%S%f")
    date_now_int = int(date_now1)

    objs = [
        Paragraph('ДОГОВОР &nbsp;&nbsp; № <u>{}</u>'.format(date_now_int),styleCenter),
        Spacer(1, 1 * mm),
        Paragraph('НА ОКАЗАНИЕ ПЛАТНЫХ МЕДИЦИНСКИХ УСЛУГ НАСЕЛЕНИЮ', styleCenter),
        ]

    styleTCenter = deepcopy(styleCenter)
    styleTCenter.alignment = TA_CENTER
    styleTCenter.leading = 3.5 * mm

    styleTBold = deepcopy(styleCenterBold)
    styleTBold.fontSize = 10
    styleTBold.alignment = TA_LEFT

    num = ind_card.number
    num_type = ind_card.full_type_card()
    # barcode128 = code128.Code128(num,barHeight= 9 * mm, barWidth = 1.25)

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    date_now = pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=datetime.datetime.now())

    styleTR = deepcopy(style)
    styleTR.alignment = TA_RIGHT

    opinion = [
        [Paragraph('г. Иркутск', style),
         Paragraph(date_now, styleTR)],
    ]

    tbl = Table(opinion, colWidths=(95 * mm, 95 * mm))

    tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
        ]))

    objs.append(Spacer(1, 2 * mm))
    objs.append(tbl)

    objs.append(Spacer(1, 4.5 * mm))
    hospital_name = SettingManager.get("rmis_orgname")
    director = SettingManager.get("post_director")
    fio_director = SettingManager.get("name_director")
    objs.append(Paragraph('{}, именуемая в дальнейшем "Исполнитель", в лице {} {}, действующей на основании Устава с'
                          'одной стороны, и <u>{}</u>, именуемый(ая) в дальнейшем "Пациент", дата рождения {} '
                          ' г., паспорт: {}-{}'.
                          format(hospital_name, director,fio_director,individual_fio,individual_date_born,
                                 document_passport_serial, document_passport_num),style))
    opinion =[]


    styleTB = deepcopy(style)
    styleTB.fontSize = 11.5
    styleTB.alignment = TA_CENTER
    styleTB.fontName = "PTAstraSerifBold"

    styleTC = deepcopy(style)
    styleTC.fontSize =10.5
    styleTC.alignment = TA_LEFT

    styleTCright = deepcopy(styleTC)
    styleTCright.alignment = TA_RIGHT

    styleTCcenter=deepcopy(styleTC)
    styleTCcenter.alignment = TA_CENTER

    if result_data[2]=='no_discount':
        opinion = [
            [Paragraph('Код услуги', styleTB), Paragraph('Направление', styleTB), Paragraph('Услуга', styleTB),
             Paragraph('Цена,<br/>руб.', styleTB), Paragraph('Кол-во, усл.', styleTB),
             Paragraph('Сумма, руб.', styleTB), ],
        ]
    else:
        opinion = [
            [Paragraph('Код услуги', styleTB), Paragraph('Направление', styleTB), Paragraph('Услуга', styleTB),
             Paragraph('Цена,<br/>руб.', styleTB), Paragraph('Скидка<br/>Наценка<br/>%', styleTB),
             Paragraph('Цена со<br/> скидкой,<br/>руб.', styleTB),
             Paragraph('Кол-во, усл.', styleTB), Paragraph('Сумма, руб.', styleTB), ],
        ]

    # example_template = [
    #     ['1.2.3','4856397','Полный гематологический анализ','1000.00','0','1000.00','1','1000.00'],
    #     ['1.2.3','','РМП','2500.45','0','2500.45','1','2500.45'],
    #     ['1.2.3', '4856398', 'УЗИ брюшной полости', '3500.49', '0', '3500.49', '1', '3500.49'],
    #     ['1.2.3','4856398','Эзофагогастродуоденоскопия','5700.99','0','5700.99','1','5700.99']
    # ]
    # #

    example_template=result_data[0]

    list_g =[]
    #используется range(len()) - к определенной колонке (по номеру) применяется свое свойство
    for i in range(len(example_template)):
        list_t = []
        for j in range(len(example_template[i])):
            if j in (3,5,7):
                s=styleTCright
            elif j in (4,6):
                s=styleTCcenter
            else:
                s=styleTC
            list_t.append(Paragraph(example_template[i][j],s))
        list_g.append(list_t)

    sum_research = result_data[1]

    opinion.extend(list_g)

    if result_data[2] == 'is_discount':
        tbl = Table(opinion, colWidths=(18 * mm, 19 * mm, 52 * mm, 22 * mm, 21 * mm, 22 * mm, 13 * mm, 25 * mm))
    else:
        tbl = Table(opinion, colWidths=(23 * mm, 34 * mm, 62 * mm, 22 * mm, 23 * mm, 25 * mm))

    tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    objs.append(Spacer(1, 2 * mm))
    objs.append(tbl)
    objs.append(Spacer(1, 2 * mm))
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph('<font size=16> Итого: {}</font>'.format(sum_research), styleTCright))

    objs.append(Spacer(1, 2 * mm))
    # start_day = datetime.today()
    end_date = (date.today() + relativedelta(days=+10))
    end_date1 = datetime.datetime.strftime(end_date, "%d.%m.%Y")

    objs.append(Spacer(1,7 * mm))
    objs.append(Paragraph('<font size=16> Внимание:</font>', styleTBold))
    objs.append(Spacer(1, 1 * mm))
    objs.append(Paragraph('<font size=16> 1) Лист на оплату действителен в течение 10 (десяти) дней – до {}.'
               '</font>'.format(end_date1), style))
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph('<font size=16> 2) Проверяйте услуги с направлениями</font>', style))


    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf