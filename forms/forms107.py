import datetime
import locale
import os.path
import sys
from copy import deepcopy
from io import BytesIO

import simplejson as json
from reportlab.lib import colors
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, portrait, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Indenter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable

from appconf.manager import SettingManager
from directions.models import Issledovaniya, Napravleniya, ParaclinicResult
from laboratory import utils
from laboratory.settings import FONTS_FOLDER
from api.stationar.stationar_func import hosp_get_hosp_direction, get_temperature_list
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import SampleHorizontalLineChart
from reportlab.graphics.widgets.markers import makeMarker


def form_01(request_data):
    """
    Температурный лист (АД, Пульс)
    на входе: type=107.01&hosps_pk=[113110]&titles=['Температура (°C)', 'Пульс', 'Давление']
    """
    # num_dir = request_data["hosps_pk"]
    num_dir = json.loads(request_data["hosps_pk"])
    direction_obj = Napravleniya.objects.get(pk=num_dir[0])
    hosp_nums_obj = hosp_get_hosp_direction(num_dir[0])
    hosp_nums = ''
    for i in hosp_nums_obj:
        hosp_nums = hosp_nums + ' - ' + str(i.get('direction'))

    ind_card = direction_obj.client
    patient_data = ind_card.get_data_individual()

    hospital_name = SettingManager.get("org_title")
    hospital_address = SettingManager.get("org_address")
    hospital_kod_ogrn = SettingManager.get("org_ogrn")

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=25 * mm,
                            rightMargin=5 * mm, topMargin=5 * mm,
                            bottomMargin=10 * mm, allowSplitting=1,
                            title="Форма {}".format("Лист показателей"))
    width, height = landscape(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.leading = 15
    style.spaceAfter = 0.5 * mm
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 12
    styleCenter.leading = 15
    styleCenter.spaceAfter = 1 * mm
    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'
    styleCenterBold.borderColor = black
    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    objs = []

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm
    styleT.face = 'PTAstraSerifReg'

    print_district = ''
    if SettingManager.get("district", default='True', default_type='b'):
        if ind_card.district is not None:
            print_district = 'Уч: {}'.format(ind_card.district.title)

    space_symbol = '&nbsp;'
    if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i'):
        patient_data['serial'] = patient_data['bc_serial']
        patient_data['num'] = patient_data['bc_num']
    else:
        patient_data['serial'] = patient_data['passport_serial']
        patient_data['num'] = patient_data['passport_num']

    card_num_obj = patient_data['card_num'].split(' ')
    p_card_num = card_num_obj[0]

    title_page = [
        Indenter(left=0 * mm),
        Spacer(1, 2 * mm),
        Paragraph('<font fontname="PTAstraSerifBold" size=13>Показатели жизненно важных функций</font><br/>', styleCenter),
        Paragraph('({} № {} {})'.format(patient_data['fio'], p_card_num, hosp_nums), styleCenter),
    ]
    objs.extend(title_page)
    objs.append(Spacer(1, 3 * mm))

    result = get_temperature_list(num_dir[0])
    titles = json.loads(request_data["titles"])
    print(result)
    print(titles)
    for k, v in result.items():
        if k in titles:
            objs.append(Paragraph('Температура (°C)', style))
            objs.append(draw_graph(v))
            break

    def first_pages(canvas, document):
        canvas.saveState()
        canvas.restoreState()

    def later_pages(canvas, document):
        canvas.saveState()
        canvas.restoreState()

    doc.build(objs, onFirstPage=first_pages, onLaterPages=later_pages)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def draw_graph(value):
    for k, v in value.items():
        print(k, v)

    drawing = Drawing(250 * mm, 25 * mm)
    data = [
        (36.6, 36.5, 37.0, 38.4, 34.5, 36.7, 38.2, 36.6, 36.5, 37.0, 38.4, 34.5, 36.7, 38.2, 36.6, 36.5, 37.0, 38.4, 34.5, 36.7, 38.2,
         36.6, 36.5, 37.0, 38.4, 34.5, 36.7, 38.2),
        # (5, 20, 46, 38, 23, 21, 6, 14)
    ]

    lc = SampleHorizontalLineChart()
    lc.x = 0
    lc.y = 0
    lc.height = 70
    lc.width = 250 * mm
    lc.data = data
    lc.joinedLines = 1
    lc.strokeColor = colors.white
    # lc.lines.symbol = makeMarker('FilledDiamond')
    # lc.lines.symbol = makeMarker('FilledCircle')
    lc.lines.symbol = makeMarker('FilledSquare')
    lc.lines[0].strokeColor = colors.black
    # lc.lines[0].strokeDashArray = [3, 1]
    lc.lineLabelFormat = '%3.1f'
    catNames = ['26.02.20\n09:30', '26.02.20\n18:00', '26.02.20\n21:00', '27.02.20\n09:20', '27.02.20\n09:20', '27.02.20\n09:24', '28.02.20\n06:23',
                '26.02.20\n09:30', '26.02.20\n18:00', '26.02.20\n21:00', '27.02.20\n09:20', '27.02.20\n09:20', '27.02.20\n09:24', '28.02.20\n06:23',
                '26.02.20\n09:30', '26.02.20\n18:00', '26.02.20\n21:00', '27.02.20\n09:20', '27.02.20\n09:20', '27.02.20\n09:24', '28.02.20\n06:23',
                '26.02.20\n09:30', '26.02.20\n18:00', '26.02.20\n21:00', '27.02.20\n09:20', '27.02.20\n09:20', '27.02.20\n09:24', '28.02.20\n06:23']
    lc.categoryAxis.categoryNames = catNames
    lc.categoryAxis.labels.boxAnchor = 'n'
    lc.categoryAxis.labels.angle = 90
    lc.categoryAxis.labels.dy = -18
    lc.categoryAxis.labels.dx = -13
    lc.valueAxis.valueMin = 34
    lc.valueAxis.valueMax = 40
    lc.valueAxis.valueStep = 1
    drawing.add(lc)

    return drawing
