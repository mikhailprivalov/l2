import locale
import os.path
import sys
from copy import deepcopy
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
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
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=20 * mm,
                            rightMargin=12 * mm, topMargin=6 * mm,
                            bottomMargin=4 * mm, allowSplitting=1,
                            title="Форма {}".format("003/у"))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.leading = 12
    style.spaceAfter = 0 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = 0
    style.spaceAfter = 1.5 * mm

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 16
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'

    styleTB = deepcopy(style)
    styleTB.firstLineIndent = 0
    styleTB.fontSize = 10
    styleTB.alignment = TA_CENTER
    styleTB.fontName = "PTAstraSerifBold"

    styleTC = deepcopy(style)
    styleTC.firstLineIndent = 0
    styleTC.fontSize = 10
    styleTC.alignment = TA_LEFT

    styleCenter = deepcopy(styleTC)
    styleCenter.alignment = TA_CENTER

    data = request_data["pks_plan"]
    pks_plan = [int(i) for i in data.split(',')]
    plans = get_plans_by_pk(pks_plan)

    objs = []
    objs.append(Paragraph("План операций", styleCenterBold))
    objs.append(Spacer(1, 5 * mm))

    opinion = [
        [Paragraph('Год', styleTB), Paragraph('Месяц', styleTB), Paragraph('Сведения', styleTB)],
    ]

    for i in plans:
        opinion.append([Paragraph(f"{i[0]}", styleCenter), Paragraph(f"{i[1]}", styleCenter),
                        Paragraph(f"{i[2]}", styleTC)])

    tbl = Table(opinion, colWidths=(20 * mm, 20 * mm, 140 * mm), splitByRow=1, repeatRows=1)

    tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    #
    objs.append(tbl)
    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    print('111', request_data['pks_plan'])
    return pdf
