from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, FrameBreak, Table, \
    TableStyle
from reportlab.platypus import PageBreak, NextPageTemplate
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from laboratory.settings import FONTS_FOLDER

import datetime
import locale
import sys
import pytils
import os.path
from io import BytesIO
from directory.models import RouteSheet, NameRouteSheet, Researches


def form_route_sheet(t):
    """
    generate health passport (Пасспорт здровья)
    :param ind: individual object(объекти физлицо)
    :param t: type form (тип формы)
    :return:
    """
    hospital_name = "ОГАУЗ \"Иркутская медикосанитарная часть № 2\""
    organization_address = "г. Иркутс, ул. Байкальская 201"
    hospital_kod_ogrn = "1033801542576"


    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    # http://www.cnews.ru/news/top/2018-12-10_rossijskim_chinovnikam_zapretili_ispolzovat
    # Причина PTAstraSerif использовать

    buffer = BytesIO()
    if t=='1':
      obj_name_route_sheet = NameRouteSheet.objects.filter(title="Водители") #тип формы

    obj1 = RouteSheet.objects.filter(name_route_sheet=obj_name_route_sheet[0])


    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=10 * mm,
                            rightMargin=10 * mm, topMargin=10 * mm,
                            bottomMargin=10 * mm, allowSplitting=1,
                            title="Форма {}".format("Паспорт здоровья"))
    width, height = A4
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifBold"
    style.fontSize = 12
    style.leading = 9
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 5.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    st = 'aaaaa <u> {i_fio}</u> aaaaaa <br/> {i_born_date}'
    space = 5.5 * mm
    objs = [
        Spacer(1, 3 * mm),
        # Paragraph('<font face="PTAstraSerifBold">st</font>'.format('23'),
        #           styleCenter),
        Paragraph(st.format(i_fio='23', i_born_date=obj_name_route_sheet[0]),
                  styleCenter),
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifBold"><u>{}</u></font>'.format(obj1[0].research.title), styleCenter),
    ]

    doc.build(objs)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf