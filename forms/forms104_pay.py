from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, FrameBreak, Table, \
    TableStyle
from reportlab.platypus import PageBreak, NextPageTemplate, Indenter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, StyleSheet1
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.graphics.barcode import code128
from laboratory.settings import FONTS_FOLDER
import datetime
import locale
import sys
import pytils
import os.path
from io import BytesIO
from . import forms_func
from datetime import *; from dateutil.relativedelta import *
import calendar
from dateutil.relativedelta import *
from directions.models import Napravleniya, IstochnikiFinansirovaniya, Issledovaniya

def form_104_01(**kwargs):
    """
    Форма Лист на оплату по созданным направлениям на услуги
    """
    form_name = "Лист на оплату"

    ind_card = kwargs.get('ind_card')
    ind_doc = kwargs.get('ind_doc')
    ind = kwargs.get('ind')
    try:
        ind_dir = kwargs.get('ind_dir')
    except Exception:
        ind_dir = None
    # Получить данные с клиента физлицо-ФИО, пол, дата рождения
    individual_fio = ind.fio()
    individual_sex = ind.sex
    individual_date_born = ind.bd()

    # Отфильтровать направления - по источнику финансирования "платно" Если таковых не имеется отдать "пусто"
    dir_temp = []
    pay_source={13,3}
    for i in ind_dir:
        try:
            n = Napravleniya.objects.get(id=i)
        except Napravleniya.DoesNotExist:
            n = None
        if n:
            if n.istochnik_f_id in pay_source:
                dir_temp.append(n.pk)

    # Получить прайс по источнику "платно"
    price_obj=forms_func.get_price(13)

    # получить УСЛУГИ по направлениям(отфильтрованы уже по "платно" и нет сохраненных исследований) из Issledovaniya
    research_direction = forms_func.get_research_by_dir(dir_temp)

    # получить по прайсу и услугам: текущие цена
    research_price = forms_func.get_coast(research_direction, price_obj)


    # (пере)записать текущие цены, скидку, в БД (по issledovaniya)


    #Получить сформированную структуру данных вида Направление, услуга, цена, количество, скидка, цена со скидкой, Сумма по позиции

    mark_down_up=10
    count = 2

    result_data = forms_func.get_final_data(research_price,mark_down_up, count)



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

    indivudual_insurance_org="38014_ИРКУТСКИЙ ФИЛИАЛ АО \"СТРАХОВАЯ КОМПАНИЯ \"СОГАЗ-МЕД\" (Область Иркутская)"
    individual_benefit_code="_________"

    card_attr = forms_func.get_card_attr(ind_card)
    ind_cards_num_total = card_attr['num_type']
    # Получить данные номер и тип карты по физ лицу
    ind_cards_num = ""
    for k, v in ind_cards_num_total.items():
        if v == "Поликлиника":
            num = k
        ind_cards_num += "{} ({})".format(k, v) + '&nbsp;&nbsp;&nbsp;&nbsp;'


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
                            title="Форма {}".format("025/у"))
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 13
    style.leading = 12
    style.spaceAfter = 0 * mm
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 12
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

    date_now = datetime.strftime(datetime.now(), "%d.%m.%Y")
    objs = [
        Paragraph('{}'.format(hospital_name),styleCenter),
        Spacer(1, 1 *mm),
        Paragraph('({} тел. 28-61-00)'.format(hospital_address), styleCenter),
        Spacer(1, 3 * mm),
        Paragraph('{}'.format(form_name), styleCenterBold),
        Spacer(1, 4 * mm),
        Paragraph('<font size = 11> <u> {}</u> </font>'.format(date_now), styleCenter),
        Paragraph('<font size = 8> дата оформления </font>', styleCenter),
    ]

    styleTCenter = deepcopy(styleCenter)
    styleTCenter.alignment = TA_CENTER
    styleTCenter.leading = 3.5 * mm

    styleTBold = deepcopy(styleCenterBold)
    styleTBold.fontSize =20
    styleTBold.alignment = TA_LEFT


    num = '0123456'
    barcode128 = code128.Code128(num,barHeight= 10 * mm, barWidth = 1.3)
    date_now = datetime.strftime(datetime.now(), "%d.%m.%Y")

    opinion = [
        [Paragraph('№ карты:', style), Paragraph(num + " - L2", styleTBold), barcode128 ],
     ]

    tbl = Table(opinion, colWidths=(25 * mm, 55 * mm, 100 * mm))

    tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
        ('BOTTOMPADDING', (1, 0), (1, 0), 3.0 * mm),
        ('ALIGN',(-1,0),(-1,-1),'RIGHT'),
    ]))

    objs.append(Spacer(1,4.5 * mm))
    objs.append(tbl)

    opinion = [
        [Paragraph('', style), Paragraph('', style), ],
        [Paragraph('Пациент:', style), Paragraph(individual_fio, style), ],
        [Paragraph('Паспорт:', style), Paragraph('серия: {} &nbsp;&nbsp;&nbsp;&nbsp; номер: {} &nbsp;&nbsp;&nbsp;&nbsp; дата выдачи: {}'.
                    format(document_passport_serial,document_passport_num,document_passport_issued), style), ],
        [Paragraph('Д/р:', style), Paragraph(individual_date_born, style), ],
    ]

    tbl = Table(opinion, colWidths=(25 * mm, 155 * mm))

    tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))

    objs.append(Spacer(1,2 * mm))
    objs.append(tbl)

    styleTB = deepcopy(style)
    styleTB.fontSize = 12
    styleTB.alignment = TA_CENTER
    styleTB.fontName = "PTAstraSerifBold"

    styleTC = deepcopy(style)
    styleTC.fontSize =10.5
    styleTC.alignment = TA_LEFT

    styleTCright = deepcopy(styleTC)
    styleTCright.alignment = TA_RIGHT

    styleTCcenter=deepcopy(styleTC)
    styleTCcenter.alignment = TA_CENTER

    opinion = [
        [Paragraph('Код услуги', styleTB), Paragraph('Направление', styleTB), Paragraph('Услуга', styleTB),
          Paragraph('Цена,<br/>руб.', styleTB), Paragraph('Скидка,<br/>%', styleTB), Paragraph('Цена со<br/> скидкой,<br/>руб.', styleTB),
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



    tbl = Table(opinion, colWidths=(18 * mm, 19 * mm, 50 * mm, 25 * mm, 20 * mm, 25 * mm, 15 * mm, 25 * mm))

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
    end_date1 = datetime.strftime(end_date, "%d.%m.%Y")

    objs.append(Spacer(1,15 * mm))
    objs.append(Paragraph('<font size=16> Внимание:</font>', styleTBold))
    objs.append(Paragraph('<font size=16> Лист на оплату действителен в течение 10 (десяти) дней – до {}.'
               '</font>'.format(end_date1), style))


    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf