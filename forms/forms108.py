import locale
import os.path
import sys
from copy import deepcopy
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from clients.models import Card
from laboratory.settings import FONTS_FOLDER
from utils.pagenum import PageNumCanvasPartitionAll
from laboratory.utils import strdate
from clients.models import AmbulatoryData


def form_01(request_data):
    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=portrait(A4),
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

    ind_card = Card.objects.get(pk=request_data["card_pk"])
    patient_data = ind_card.get_data_individual()
    objs = []
    objs.append(Paragraph("Сведения из формы 112", styleCenterBold))
    objs.append(Spacer(1, 5 * mm))
    objs.append(Paragraph(f"<br/>Пациент: {patient_data['fio']}, д.р. {patient_data['born']}", style))

    opinion = [
        [Paragraph('Год', styleTB), Paragraph('Месяц', styleTB), Paragraph('Сведения', styleTB)],
    ]

    for a in AmbulatoryData.objects.filter(card__pk=request_data["card_pk"]).order_by('date', 'pk'):
        opinion.append([Paragraph(f"{strdate(a.date)[6:10]}", styleCenter), Paragraph(f"{strdate(a.date)[3:5]}", styleCenter),
                        Paragraph(f"{a.data}".replace('<', '&lt;').replace('>', '&gt;').replace("\n", "<br/>"), styleTC)])

    tbl = Table(opinion, colWidths=(20 * mm, 20 * mm, 140 * mm), splitByRow=1, repeatRows=1)

    tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    objs.append(tbl)

    def first_pages(canvas, document):
        canvas.saveState()
        canvas.setFont('PTAstraSerifReg', 10)
        canvas.drawString(115 * mm, 8 * mm, 'Пациент: {}, {}'.format(patient_data['fio'], patient_data['born']))
        canvas.restoreState()

    def later_pages(canvas, document):
        canvas.saveState()

        canvas.setFont('PTAstraSerifReg', 10)
        canvas.drawString(115 * mm, 8 * mm, 'Пациент: {}, {}'.format(patient_data['fio'], patient_data['born']))
        canvas.setFont('PTAstraSerifReg', 8)

        canvas.restoreState()

    doc.build(objs, onFirstPage=first_pages, onLaterPages=later_pages, canvasmaker=PageNumCanvasPartitionAll)

    pdf = buffer.getvalue()

    buffer.close()
    return pdf
