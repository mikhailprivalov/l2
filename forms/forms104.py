import locale
import os.path
import sys
from copy import deepcopy
from io import BytesIO

import simplejson as json
from reportlab.graphics.barcode import code128
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from clients.models import Card, Document
from directions.models import Napravleniya, IstochnikiFinansirovaniya
from laboratory.settings import FONTS_FOLDER
from . import forms_func


def form_01(request_data):
    """
    Форма Лист на оплату по созданным направлениям на услуги
    """
    form_name = "Маршрутный лист"

    ind_card = Card.objects.get(pk=request_data["card_pk"])
    ind = ind_card.individual
    ind_doc = Document.objects.filter(individual=ind, is_active=True)
    ind_dir = json.loads(request_data["dir"])

    # Получить данные с клиента физлицо-ФИО, пол, дата рождения
    individual_fio = ind.fio()
    individual_date_born = ind.bd()

    # Получить все источники, у которых title-ПЛАТНО
    ist_f = list(IstochnikiFinansirovaniya.objects.values_list('id').filter(title__exact='Платно'))
    ist_f_list = [int(x[0]) for x in ist_f]

    napr = Napravleniya.objects.filter(id__in=ind_dir)
    dir_temp = []

    # Проверить, что все направления принадлежат к одной карте и имеют ист.финансирования "Платно"
    for n in napr:
        if (n.istochnik_f_id in ist_f_list) and (n.client == ind_card):
            dir_temp.append(n.pk)

    # получить по направлению-услугам цену из Issledovaniya
    hospital_name = "ОГАУЗ \"Иркутская медикосанитарная часть ИАПО\""
    hospital_address = "г. Иркутс, ул. Жукова 9"

    # Получить данные физлицо-документы: паспорт, полис, снилс
    documents = forms_func.get_all_doc(ind_doc)
    document_passport_num = documents['passport']['num']
    document_passport_serial = documents['passport']['serial']
    document_passport_issued = documents['passport']['issued']
    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    # Генерировать pdf-Лист на оплату
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=10 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=5 * mm, allowSplitting=1, title="Форма {}".format("Лист на оплату"))
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

    date_now = ''

    objs = [
        Paragraph('{}'.format(hospital_name), styleCenter),
        Spacer(1, 1 * mm),
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
    styleTBold.fontSize = 14
    styleTBold.alignment = TA_LEFT

    num = ind_card.number
    barcode128 = code128.Code128(num, barHeight=9 * mm, barWidth=1.25)

    opinion = [
        [Paragraph('№ карты:', style), Paragraph(num + "-" + "(" + num + ")", styleTBold), barcode128],
    ]

    tbl = Table(opinion, colWidths=(23 * mm, 75 * mm, 100 * mm))

    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.0 * mm),
                ('BOTTOMPADDING', (1, 0), (1, 0), 1.0 * mm),
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ]
        )
    )

    objs.append(Spacer(1, 2 * mm))
    objs.append(tbl)

    opinion = [
        [
            Paragraph('', style),
            Paragraph('', style),
        ],
        [
            Paragraph('Пациент:', style),
            Paragraph(individual_fio, style),
        ],
        [
            Paragraph('Паспорт:', style),
            Paragraph(
                'серия: {} &nbsp;&nbsp;&nbsp;&nbsp; номер: {} &nbsp;&nbsp;&nbsp;&nbsp; дата выдачи: {}'.format(document_passport_serial, document_passport_num, document_passport_issued),
                style,
            ),
        ],
        [
            Paragraph('Д/р:', style),
            Paragraph(individual_date_born, style),
        ],
    ]

    tbl = Table(opinion, colWidths=(23 * mm, 175 * mm))

    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.1 * mm),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ]
        )
    )

    objs.append(Spacer(1, 2 * mm))
    objs.append(tbl)

    styleTB = deepcopy(style)
    styleTB.fontSize = 11.5
    styleTB.alignment = TA_CENTER
    styleTB.fontName = "PTAstraSerifBold"

    styleTC = deepcopy(style)
    styleTC.fontSize = 10.5
    styleTC.alignment = TA_LEFT

    styleTCright = deepcopy(styleTC)
    styleTCright.alignment = TA_RIGHT

    styleTCcenter = deepcopy(styleTC)
    styleTCcenter.alignment = TA_CENTER

    opinion = [
        [
            Paragraph('Код услуги', styleTB),
            Paragraph('Направление', styleTB),
            Paragraph('Услуга', styleTB),
            Paragraph('Информация', styleTB),
            Paragraph('Утвержденный перечень исследований', styleTB),
        ],
    ]

    example_template = [
        [
            Paragraph('1.2.3', style),
            Paragraph('4856397', style),
            Paragraph('Полный гематологический анализ', style),
            Paragraph('', style),
            Paragraph('', style),
        ],
        [
            Paragraph('1.2.3', style),
            Paragraph('97', style),
            Paragraph('ЛОР', style),
            Paragraph('каб.45', style),
            Paragraph('Аудиометрия, Исследование вестибулярного анализатора', style),
        ],
        [
            Paragraph('1.2.3', style),
            Paragraph('4856398', style),
            Paragraph('Офтальмолог', style),
            Paragraph('каб.14 с 8.00 до 15.00', style),
            Paragraph('биомикроскопия переднего отрезка глаза, Острота зрения, поле зрения', style),
        ],
        [
            Paragraph('1.2', style),
            Paragraph('98', style),
            Paragraph('Рентгенография грудной клетки в 2 проекциях', style),
            Paragraph('каб.19 с 8.00 до 15.00', style),
            Paragraph('', style),
        ],
        [
            Paragraph('1.5', style),
            Paragraph('981', style),
            Paragraph('Спирометрия', style),
            Paragraph('каб.16 с 9.00 до 15.00', style),
            Paragraph('', style),
        ],
    ]

    opinion.extend(example_template)

    tbl = Table(opinion, colWidths=(18 * mm, 25 * mm, 52 * mm, 45 * mm, 59 * mm))

    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
    )

    objs.append(Spacer(1, 2 * mm))
    objs.append(tbl)
    objs.append(Spacer(1, 2 * mm))
    objs.append(Spacer(1, 2 * mm))

    objs.append(Spacer(1, 2 * mm))
    objs.append(Spacer(1, 7 * mm))

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
