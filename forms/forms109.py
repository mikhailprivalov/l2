import locale
import os.path
import sys
from copy import deepcopy
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from api.stationar.stationar_func import hosp_get_hosp_direction
from forms.forms_func import primary_reception_get_data
from laboratory.settings import FONTS_FOLDER
from api.plans.sql_func import get_plans_by_pk
from doctor_call.models import DoctorCall
from list_wait.models import ListWait
import datetime
from utils.dates import normalize_dash_date, try_parse_range


def form_01(request_data):
    # план операций
    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4), leftMargin=20 * mm, rightMargin=12 * mm, topMargin=6 * mm, bottomMargin=4 * mm, allowSplitting=1, title="Форма {}".format("План операций")
    )

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10.5
    style.leading = 12
    style.spaceAfter = 0 * mm
    style.alignment = TA_LEFT
    style.firstLineIndent = 0
    style.spaceAfter = 1.5 * mm

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 16
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'

    styleTB = deepcopy(style)
    styleTB.firstLineIndent = 0
    styleTB.alignment = TA_CENTER
    styleTB.fontName = "PTAstraSerifBold"

    styleCenter = deepcopy(style)
    styleCenter.firstLineIndent = 0
    styleCenter.alignment = TA_CENTER

    data = request_data["pks_plan"]
    pks_plan = [int(i) for i in data.split(',')]
    plans = get_plans_by_pk(pks_plan)

    objs = []
    objs.append(Paragraph("План операций", styleCenterBold))
    objs.append(Spacer(1, 5 * mm))

    opinion = [
        [
            Paragraph('Дата операции', styleTB),
            Paragraph('№ Истории', styleTB),
            Paragraph('Пациент', styleTB),
            Paragraph('Вид операции', styleTB),
            Paragraph('Врач - хирург', styleTB),
            Paragraph('Отделение', styleTB),
            Paragraph('Анестезиолог', styleTB),
        ],
    ]

    for i in plans:
        doc_fio = ''
        if i[6]:
            doc_fio = i[6].split(' ')
            doc_fio = f"{doc_fio[0]} {doc_fio[1][0]}.{doc_fio[2][0]}."
        anesthetist_fio = ''
        if i[9]:
            anesthetist_fio = i[9].split(' ')
            anesthetist_fio = f"{anesthetist_fio[0]} {anesthetist_fio[1][0]}.{anesthetist_fio[2][0]}."
        strike_o = ""
        strike_cl = ""
        if i[10]:
            strike_o = "<strike>"
            strike_cl = "</strike>"
        department = i[7] if i[7] else i[16]

        hosp_nums_obj = hosp_get_hosp_direction(i[2])
        hosp_first_num = hosp_nums_obj[0].get('direction')
        primary_reception_data = primary_reception_get_data(hosp_first_num)
        if primary_reception_data['weight']:
            weight = f", Вес-{primary_reception_data['weight']}"
        else:
            weight = ''
        opinion.append(
            [
                Paragraph(f"{strike_o}{i[3]}{strike_cl}", styleCenter),
                Paragraph(f"{strike_o}{i[2]}{strike_cl}", styleCenter),
                Paragraph(f"{strike_o}{i[11]} {i[12]} {i[13]}, {i[14]}{weight}{strike_cl}", style),
                Paragraph(f"{strike_o}{i[4]}{strike_cl}", style),
                Paragraph(f"{strike_o}{doc_fio}{strike_cl}", style),
                Paragraph(f"{strike_o}{department}{strike_cl}", style),
                Paragraph(f"{strike_o}{anesthetist_fio}{strike_cl}", style),
            ]
        )

    tbl = Table(opinion, colWidths=(30 * mm, 27 * mm, 50 * mm, 50 * mm, 40 * mm, 30 * mm, 40 * mm), splitByRow=1, repeatRows=1)

    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
    )

    objs.append(tbl)
    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_02(request_data):
    # Вызов врача
    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4), leftMargin=20 * mm, rightMargin=12 * mm, topMargin=6 * mm, bottomMargin=4 * mm, allowSplitting=1, title="Форма {}".format("План операций")
    )

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10.5
    style.leading = 12
    style.spaceAfter = 0 * mm
    style.alignment = TA_LEFT
    style.firstLineIndent = 0
    style.spaceAfter = 1.5 * mm

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 16
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'

    styleTB = deepcopy(style)
    styleTB.firstLineIndent = 0
    styleTB.alignment = TA_CENTER
    styleTB.fontName = "PTAstraSerifBold"

    styleCenter = deepcopy(style)
    styleCenter.firstLineIndent = 0
    styleCenter.alignment = TA_CENTER

    print(request_data)
    date = request_data["date"]
    district = int(request_data["district"])

    objs = []
    objs.append(Paragraph(f"Вызов врача {normalize_dash_date(date)}", styleCenterBold))
    objs.append(Spacer(1, 5 * mm))

    if district > -1:
        doc_call = DoctorCall.objects.filter(exec_at=datetime.datetime.strptime(date, '%Y-%m-%d'), district_id__pk=district).order_by("pk")
    else:
        doc_call = DoctorCall.objects.filter(exec_at=datetime.datetime.strptime(date, '%Y-%m-%d')).order_by("district__title")

    opinion = [
        [
            Paragraph('№ п/п', styleTB),
            Paragraph('Пациент', styleTB),
            Paragraph('Адрес', styleTB),
            Paragraph('Участок', styleTB),
            Paragraph('Телефон', styleTB),
            Paragraph('Врач', styleTB),
            Paragraph('Примечание', styleTB),
        ],
    ]

    count = 0
    for i in doc_call:
        count += 1
        title = ''
        if i.district:
            title = i.district.title
        opinion.append(
            [
                Paragraph(f"{count}", styleCenter),
                Paragraph(f"{i.client.individual.fio()} ({i.client.number_with_type()})", styleCenter),
                Paragraph(f"{i.address}", styleCenter),
                Paragraph(f"{title}", style),
                Paragraph(f"{i.client.phone}", style),
                Paragraph(f"{i.research.title}", style),
                Paragraph(f"{i.comment}", style),
            ]
        )

    tbl = Table(opinion, colWidths=(10 * mm, 60 * mm, 50 * mm, 20 * mm, 30 * mm, 60 * mm, 40 * mm), splitByRow=1, repeatRows=1)

    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
    )

    objs.append(tbl)
    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_03(request_data):
    # Лист ожидания
    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4), leftMargin=20 * mm, rightMargin=12 * mm, topMargin=6 * mm, bottomMargin=4 * mm, allowSplitting=1, title="Форма {}".format("План операций")
    )

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10.5
    style.leading = 12
    style.spaceAfter = 0 * mm
    style.alignment = TA_LEFT
    style.firstLineIndent = 0
    style.spaceAfter = 1.5 * mm

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 16
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'

    styleTB = deepcopy(style)
    styleTB.firstLineIndent = 0
    styleTB.alignment = TA_CENTER
    styleTB.fontName = "PTAstraSerifBold"

    styleCenter = deepcopy(style)
    styleCenter.firstLineIndent = 0
    styleCenter.alignment = TA_CENTER

    dates = request_data["date"].split(",")
    date_start, date_end = try_parse_range(dates[0], dates[1])

    objs = []

    objs.append(Paragraph(f"Лист ожидани: {dates[0]} - {dates[1]}", styleCenterBold))
    objs.append(Spacer(1, 5 * mm))

    research_pk = int(request_data["research_pk"])
    if research_pk > -1:
        list_wait = ListWait.objects.filter(
            exec_at__range=(
                date_start,
                date_end,
            ),
            research_id__pk=research_pk,
        ).order_by("exec_at")
    else:
        list_wait = ListWait.objects.filter(
            exec_at__range=(
                date_start,
                date_end,
            )
        ).order_by("exec_at")

    opinion = [
        [
            Paragraph('№ п/п', styleTB),
            Paragraph('Пациент', styleTB),
            Paragraph('Телефон', styleTB),
            Paragraph('Услуга', styleTB),
            Paragraph('Статус', styleTB),
            Paragraph('Примечание', styleTB),
        ],
    ]

    count = 0
    for i in list_wait:
        count += 1
        opinion.append(
            [
                Paragraph(f"{count}", styleCenter),
                Paragraph(f"{i.client.individual.fio()} ({i.client.number_with_type()})", styleCenter),
                Paragraph(f"{i.client.phone}", styleCenter),
                Paragraph(f"{i.research.title}", style),
                Paragraph(f"{i.get_work_status_display()}", style),
                Paragraph(f"{i.comment}", style),
            ]
        )

    tbl = Table(opinion, colWidths=(10 * mm, 80 * mm, 30 * mm, 50 * mm, 30 * mm, 40 * mm), splitByRow=1, repeatRows=1)

    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
    )

    objs.append(tbl)
    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf
