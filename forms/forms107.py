import locale
import os.path
import sys
from copy import deepcopy
from io import BytesIO
import simplejson as json
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Indenter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from appconf.manager import SettingManager
from directions.models import Napravleniya
from laboratory.settings import FONTS_FOLDER
from api.stationar.stationar_func import hosp_get_hosp_direction, get_temperature_list
from reportlab.lib import colors
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.widgets.markers import makeMarker


def form_01(request_data):
    """
    Температурный лист (АД, Пульс)
    на входе: type=107.01&hosps_pk=[113110]&titles=['Температура (°C)', 'Пульс', 'Давление']
    """
    num_dir = json.loads(request_data["hosp_pks"])
    direction_obj = Napravleniya.objects.get(pk=num_dir[0])
    hosp_nums_obj = hosp_get_hosp_direction(num_dir[0])
    hosp_nums = ''
    for i in hosp_nums_obj:
        hosp_nums = hosp_nums + ' - ' + str(i.get('direction'))

    ind_card = direction_obj.client
    patient_data = ind_card.get_data_individual()

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=15 * mm,
                            rightMargin=5 * mm, topMargin=13 * mm,
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
    print(titles)
    if 'Температура (°C)' in titles:
        temperature_data = result['Температура (°C)']
        objs.append(Paragraph('Температура (°C)', style))
        objs.append(draw_temper_pulse(temperature_data, 1, 250 * mm, 30 * mm))
        objs.append(Spacer(1, 15 * mm))
    if 'Пульс (уд/с)' in titles:
        pulse_data = result['Пульс (уд/с)']
        objs.append(Paragraph('Пульс (уд/с)', style))
        objs.append(draw_temper_pulse(pulse_data, 10, 250 * mm, 30 * mm))
        objs.append(Spacer(1, 15 * mm))
    if 'Давление' in titles:
        pressure_data = {'Диастолическое давление (мм рт.с)': result['Диастолическое давление (мм рт.с)'],
                         'Систолическое давление (мм рт.с)': result['Систолическое давление (мм рт.с)']}
        objs.append(Paragraph('Давление', style))
        objs.append(draw_pressure(pressure_data, 10, 250 * mm, 30 * mm))
        objs.append(Spacer(1, 15 * mm))

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def draw_temper_pulse(value, step, x_coord, y_coord):
    drawing = Drawing(x_coord, y_coord)
    data = []
    catNames = []
    min_value = 0
    max_value = 0
    for k, v in value.items():
        if k == 'data':
            data1 = tuple([i for i in v])
            data.append(data1)
        if k == 'xtext':
            catNames = [i.replace(' ', '\n') for i in v]
        if k == 'min_max':
            min_value = v[0] - step
            max_value = v[1] + step

    lc = HorizontalLineChart()
    lc.x = 0
    lc.y = 0
    lc.height = 70
    lc.width = 250 * mm
    lc.data = data
    lc.joinedLines = 1
    lc.strokeColor = colors.white
    # из markers
    lc.lines.symbol = makeMarker('FilledSquare')
    lc.lines.symbol.size = 4
    # lineLabels - свойства надбисей линии из textlabels class Label(Widget):
    lc.lineLabels.fontSize = 9
    lc.lineLabels.fontName = 'PTAstraSerifBold'
    lc.lineLabels.angle = 0
    lc.lineLabels.dx = 2
    lc.lineLabels.dy = 1
    lc.lines[0].strokeColor = colors.black
    lc.lineLabelFormat = '%3.1f'

    lc.categoryAxis.categoryNames = catNames
    lc.categoryAxis.labels.boxAnchor = 'n'
    lc.categoryAxis.labels.angle = 0
    lc.categoryAxis.labels.dy = -2
    lc.categoryAxis.labels.dx = 0
    lc.categoryAxis.labels.fontSize = 9
    lc.categoryAxis.labels.fontName = 'PTAstraSerifReg'
    lc.categoryAxis.labels.leading = 8

    lc.valueAxis.valueMin = min_value
    lc.valueAxis.valueMax = max_value
    lc.valueAxis.valueStep = step
    lc.valueAxis.labels.fontName = 'PTAstraSerifReg'
    lc.valueAxis.labels.fontSize = 9
    drawing.add(lc)

    return drawing


def draw_pressure(value, step, x_coord, y_coord):
    drawing = Drawing(x_coord, y_coord)
    data = []
    data_diastolic = value['Диастолическое давление (мм рт.с)']
    data1 = [i for i in data_diastolic['data']]
    data.append(tuple(data1))
    min_max = data_diastolic['min_max']
    data_systolic = value['Систолическое давление (мм рт.с)']
    data1 = [i for i in data_systolic['data']]
    data.append(tuple(data1))
    catNames = [i.replace(' ', '\n') for i in data_diastolic['xtext']]
    min_max.extend(data_systolic['min_max'])
    min_value = min(min_max) - step
    max_value = max(min_max) + step

    lc = HorizontalLineChart()
    lc.x = 0
    lc.y = 0
    lc.height = 70
    lc.width = 250 * mm
    lc.data = data
    lc.joinedLines = 1
    lc.strokeColor = colors.white
    # из markers
    lc.lines[0].symbol = makeMarker('FilledCircle')
    lc.lines.symbol = makeMarker('FilledSquare')
    lc.lines.symbol.size = 4
    # lineLabels - свойства надбисей линии из textlabels class Label(Widget):
    lc.lineLabels.fontSize = 9
    lc.lineLabels.fontName = 'PTAstraSerifBold'
    lc.lineLabels.angle = 0
    lc.lineLabels.dx = 2
    lc.lineLabels.dy = 0
    lc.lines[0].strokeColor = colors.black
    lc.lines[0].strokeDashArray = [3, 3]
    lc.lineLabelFormat = '%3.1f'

    lc.categoryAxis.categoryNames = catNames
    lc.categoryAxis.labels.boxAnchor = 'n'
    lc.categoryAxis.labels.angle = 0
    lc.categoryAxis.labels.dy = -2
    lc.categoryAxis.labels.dx = 0
    lc.categoryAxis.labels.fontSize = 9
    lc.categoryAxis.labels.fontName = 'PTAstraSerifReg'
    lc.categoryAxis.labels.leading = 8
    lc.valueAxis.valueMin = min_value
    lc.valueAxis.valueMax = max_value
    lc.valueAxis.valueStep = step
    lc.valueAxis.labels.fontName = 'PTAstraSerifReg'
    lc.valueAxis.labels.fontSize = 9
    drawing.add(lc)
    return drawing
