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
from laboratory.settings import FONTS_FOLDER
from api.plans.sql_func import get_plans_by_pk


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

        opinion.append(
            [
                Paragraph(f"{strike_o}{i[3]}{strike_cl}", styleCenter),
                Paragraph(f"{strike_o}{i[2]}{strike_cl}", styleCenter),
                Paragraph(f"{strike_o}{i[11]} {i[12]} {i[13]}, {i[14]}{strike_cl}", style),
                Paragraph(f"{strike_o}{i[4]}{strike_cl}", style),
                Paragraph(f"{strike_o}{doc_fio}{strike_cl}", style),
                Paragraph(f"{strike_o}{department}{strike_cl}", style),
                Paragraph(f"{strike_o}{anesthetist_fio}{strike_cl}", style),
            ]
        )

    tbl = Table(opinion, colWidths=(30 * mm, 27 * mm, 50 * mm, 50 * mm, 40 * mm, 30 * mm, 40 * mm), splitByRow=1, repeatRows=1)

    tbl.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 1.0, colors.black), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),]))

    objs.append(tbl)
    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf
