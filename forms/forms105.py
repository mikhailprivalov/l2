from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, portrait, landscape
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.graphics.barcode import code128, qr
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
import os.path
from io import BytesIO
from . import forms_func
from directions.models import Napravleniya, IstochnikiFinansirovaniya, Issledovaniya, PersonContract
from clients.models import Card, Document
from laboratory.settings import FONTS_FOLDER
import simplejson as json
from dateutil.relativedelta import *
from datetime import *
import datetime
import locale
import sys
import pytils
from appconf.manager import SettingManager
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.colors import white, black
import zlib

def form_01(request_data):
    """
    Печать статталона по амбулаторному приему. Входные параметры врач, дата.
    Выходные: форма
    """

    doc_confirm = request_data['user'].doctorprofile
    str_date = request_data['date']
    date_confirm = datetime.datetime.strptime(str_date, "%d%m%Y")
    doc_results = forms_func.get_doc_results(doc_confirm, date_confirm)
    talon = forms_func.get_finaldata_talon(doc_results)

    # Генерировать pdf-Лист на оплату
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Symbola', os.path.join(FONTS_FOLDER, 'Symbola.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=12 * mm,
                            rightMargin=5 * mm, topMargin=10 * mm,
                            bottomMargin=28 * mm, allowSplitting=1,
                            title="Форма {}".format("Договор на оплату"))

    styleSheet = getSampleStyleSheet()
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 9
    style.leading = 12
    style.spaceAfter = 0 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = 15

    styleFL = deepcopy(style)
    styleFL.firstLineIndent = 0
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)

    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 9
    styleCenter.leading = 10
    styleCenter.spaceAfter = 0 * mm

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 14
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'

    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    title = 'Ведомость статистических талонов по пациентам'

    objs = []
    objs.append(Spacer(1, 1 * mm))

    counter = 0
    for i in talon:
        if len(talon.get(i)) == 0:
            continue
        else:
            pass
        print(i, len(talon.get(i)), talon.get(i))


    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.firstLineIndent = 0
    styleT.fontSize = 11

    opinion = [
        [Paragraph('ФИО врача:', styleT), Paragraph('{}'.format(doc_confirm.fio), styleT),
         Paragraph('{}'.format(date_confirm.strftime('%d.%m.%Y')), styleT)],
        [Paragraph('Специальность:', styleT), Paragraph('{}'.format(doc_confirm.specialities), styleT),
         Paragraph('', styleT)],
    ]

    def later_pages(canvas, document):
        canvas.saveState()
        #вывести Название и данные врача
        width, height = landscape(A4)
        canvas.setFont('PTAstraSerifBold', 14)
        canvas.drawString(99 * mm, 200 * mm, '{}'.format(title))

        tbl = Table(opinion, colWidths=(35 * mm, 220 * mm, 25 * mm), rowHeights=(5 * mm))
        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
        ]))
        tbl.wrapOn(canvas, width, height)
        tbl.drawOn(canvas, 30, 530)

        canvas.restoreState()

    doc.build(objs, onFirstPage=later_pages, onLaterPages=later_pages,)

    pdf = buffer.getvalue()

    buffer.close()
    return pdf