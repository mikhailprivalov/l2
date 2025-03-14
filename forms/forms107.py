import locale
import os.path
import sys
from copy import deepcopy
from io import BytesIO
import simplejson as json
from django.http import HttpRequest
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Indenter, Table, TableStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether

from api.procedure_list.views import get_procedure_by_dir
from appconf.manager import SettingManager
from directions.models import Napravleniya
from forms.forms_func import primary_reception_get_data, hosp_extract_get_data
from laboratory.settings import FONTS_FOLDER
from api.stationar.stationar_func import hosp_get_hosp_direction, get_temperature_list, get_assignments
from reportlab.lib import colors
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.widgets.markers import makeMarker
from datetime import datetime
from math import ceil

from utils.dates import normalize_date


class VerticalParagraph(Paragraph):
    """Вертикальный текст в Paragraph"""

    def __init__(self, args, **kwargs):
        super().__init__(args, **kwargs)
        self.horizontal_position = -self.style.leading

    def draw(self):
        canvas = self.canv
        canvas.rotate(90)
        canvas.translate(1, self.horizontal_position)
        super().draw()

    def wrap(self, available_width, _):
        string_width = self.canv.stringWidth(
            self.getPlainText(), self.style.fontName, self.style.fontSize
        )
        self.horizontal_position = - (available_width + self.style.leading) / 2
        height, _ = super().wrap(availWidth=1 + string_width, availHeight=available_width)
        return self.style.leading, height


def form_01_old(request_data):
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
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4), leftMargin=15 * mm, rightMargin=5 * mm, topMargin=13 * mm, bottomMargin=10 * mm, allowSplitting=1, title="Форма {}".format("Лист показателей")
    )
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
    count_in_graph = 26
    if 'Температура (°C)' in titles and 'Температура (°C)' in result:
        result_data = result['Температура (°C)']
        min_max = result_data['min_max']
        count_param = count_len_param(result_data, count_in_graph)
        for i in range(count_param):
            elements = count_graph_el(count_in_graph, result_data)
            temp_obj = [
                Paragraph(' <u>Температура (°C)</u>', style),
                Spacer(1, 2 * mm),
                draw_temper_pulse({'data': elements[0], 'xtext': elements[1], 'min_max': min_max}, 10, 250 * mm, 27 * mm),
                Spacer(1, 10 * mm),
            ]
            objs.append(KeepTogether(temp_obj))

    if 'Пульс (уд/м)' in titles and 'Пульс (уд/м)' in result:
        result_data = result['Пульс (уд/м)']
        min_max = result_data['min_max']
        count_param = count_len_param(result_data, count_in_graph)
        for i in range(count_param):
            elements = count_graph_el(count_in_graph, result_data)
            temp_obj = [
                Paragraph(' <u>Пульс (уд/м)</u>', style),
                Spacer(1, 2 * mm),
                draw_temper_pulse({'data': elements[0], 'xtext': elements[1], 'min_max': min_max}, 10, 250 * mm, 27 * mm),
                Spacer(1, 10 * mm),
            ]
            objs.append(KeepTogether(temp_obj))

    diastolic = 'Диастолическое давление (мм рт.с)'
    systolic = 'Систолическое давление (мм рт.с)'
    if 'Давление' in titles and diastolic in result and systolic in result:
        result_data = {diastolic: result[diastolic], systolic: result[systolic]}
        min_max_diastolic = result_data[diastolic]['min_max']
        min_max_systolic = result_data[systolic]['min_max']
        count_param = count_len_param(result_data[diastolic], count_in_graph)
        for i in range(count_param):
            elements = count_graph_el_pressure(count_in_graph, result_data, diastolic, systolic, min_max_diastolic, min_max_systolic)
            temp_obj = [
                Paragraph(
                    '<u>Давление:</u> (<img src="forms/img/squreline.png" width="20" height="10" />  систолическое, '
                    '<img src="forms/img/strokedot.png" width="20" height="10" />  диастолическое)',
                    style,
                ),
                Spacer(1, 2 * mm),
                draw_pressure(elements, 10, 250 * mm, 45 * mm),
                Spacer(1, 10 * mm),
            ]
            objs.append(KeepTogether(temp_obj))
    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def count_len_param(param_object, count_in_graph):
    len_param = len(param_object['data'])
    count_param = 0
    if len_param > count_in_graph:
        count_param = len_param // count_in_graph
    if len_param % count_in_graph > 0 or count_param == 0:
        count_param += 1
    return count_param


def count_graph_el(count_in_graph, param_object):
    data = param_object['data'][:count_in_graph]
    del param_object['data'][:count_in_graph]
    xtext = param_object['xtext'][:count_in_graph]
    del param_object['xtext'][:count_in_graph]

    return data, xtext


def count_graph_el_pressure(count_in_graph, param_object, diastolic, systolic, min_max_diastolic, min_max_systolic):
    data_diastolic = param_object[diastolic]['data'][:count_in_graph]
    del param_object[diastolic]['data'][:count_in_graph]

    data_systolic = param_object[systolic]['data'][:count_in_graph]
    del param_object[systolic]['data'][:count_in_graph]

    xtext_diastolic = param_object[diastolic]['xtext'][:count_in_graph]
    del param_object[diastolic]['xtext'][:count_in_graph]

    xtext_systolic = param_object[systolic]['xtext'][:count_in_graph]
    del param_object[systolic]['xtext'][:count_in_graph]

    return {
        diastolic: {'data': data_diastolic, 'xtext': xtext_diastolic, 'min_max': min_max_diastolic},
        systolic: {'data': data_systolic, 'xtext': xtext_systolic, 'min_max': min_max_systolic},
    }


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
    lc.x = 15
    lc.y = 0
    lc.height = 28 * mm
    lc.width = 250 * mm
    lc.data = data
    lc.joinedLines = 1
    lc.strokeColor = colors.white
    lc.strokeColor = None
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
    lc.x = 15
    lc.y = 0
    lc.height = 45 * mm
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
    lc.lineLabels.dy = -1
    lc.lines[0].strokeColor = colors.black
    lc.lines[1].strokeColor = colors.black
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


def form_02_old(request_data):
    """
    Процедурный лист
    """

    num_dir = json.loads(request_data["hosp_pk"])
    ind_card = Napravleniya.objects.get(pk=num_dir)
    patient_data = ind_card.client.get_data_individual()

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4), leftMargin=15 * mm, rightMargin=5 * mm, topMargin=13 * mm, bottomMargin=10 * mm, allowSplitting=1, title="Форма {}".format("Лист процедурный")
    )
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
    styleT.leading = 3.5 * mm
    styleT.face = 'PTAstraSerifReg'

    styleTtime = deepcopy(styleT)
    styleTtime.fontSize = 8.5
    styleTtime.leading = 2.5 * mm
    styleTtime.spaceAfter = 1.0 * mm

    styleTCBold = deepcopy(style)
    styleTCBold.fontSize = 9
    styleTCBold.fontName = "PTAstraSerifBold"
    space_symbol = '&nbsp;'
    title_page = [
        Indenter(left=0 * mm),
        Spacer(1, 2 * mm),
        Paragraph(f'<font fontname="PTAstraSerifBold" size=13>ПРОЦЕДУРНЫЙ ЛИСТ {space_symbol*3} № {num_dir}</font> ', styleCenter),
    ]

    objs.extend(title_page)
    objs.append(Paragraph(f'{patient_data["fio"]}  {space_symbol*150} Палата______', style))
    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('V - выполнено, Х - не выполнено, О - отменено', styleT))
    objs.append(Spacer(1, 1 * mm))
    procedural = json.dumps({'direction': num_dir})
    procedural_obj = HttpRequest()
    procedural_obj._body = procedural
    procedural_obj.user = request_data["user"]
    data = get_procedure_by_dir(procedural_obj)
    results_json = json.loads(data.content.decode('utf-8'))

    timesInDates = results_json['timesInDates']
    unique_dates = sorted(set([k for k in timesInDates.keys()]))
    unique_dates.sort(key=lambda x: datetime.strptime(x, '%d.%m.%Y'))

    count_table = 1
    slice_count = 14
    if len(unique_dates) > slice_count:
        count_table = ceil(len(unique_dates) / slice_count)

    start = 0
    for v_table in range(count_table):
        v_table = []
        end = start + slice_count

        if len(unique_dates) > slice_count:
            dates_record = [[Paragraph(f'{date[0:6]}{date[-2:]}', styleTCBold)] for date in unique_dates[start:end]]
        else:
            dates_record = [[Paragraph(f'{date[0:6]}{date[-2:]}', styleTCBold)] for date in unique_dates]
        dates_record.insert(0, [Paragraph("Наименование", styleTCBold)])

        v_table.append(dates_record)

        for record in results_json['result']:
            temp_time = [[Paragraph(" ", styleTtime)] for i in range(len(dates_record) - 1)]
            comment = ''
            for date, times in record['dates'].items():
                if len(unique_dates) > slice_count:
                    if date not in unique_dates[start:end]:
                        continue
                    index = unique_dates[start:end].index(date)
                else:
                    index = unique_dates.index(date)
                temp_time_index = temp_time[index]
                for time, value in times.items():
                    strike_o = ""
                    strike_cl = ""
                    if value['empty']:
                        continue
                    status = 'X'
                    if value['cancel']:
                        strike_o = "<strike>"
                        strike_cl = "</strike>"
                        status = 'О'
                    if value['ok']:
                        strike_o = ""
                        strike_cl = ""
                        status = 'V'
                    temp_time_index.append([Paragraph(f"{strike_o}{time}{strike_cl}-{status}", styleTtime)])
                    temp_time[index] = temp_time_index.copy()

            if record['comment']:
                comment = record['comment']
            temp_time.insert(0, [Paragraph(f"{record['drug']} {record['form_release']} {record['method']} {record['dosage']} " f"{comment}", styleT)])
            v_table.append(temp_time)

        cols_width = [15.5 * mm for i in range(len(dates_record))]
        cols_width[0] = 50 * mm

        tbl = Table(v_table, repeatRows=1, colWidths=cols_width, hAlign='LEFT')
        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3 * mm),
                    ('TOPPADDING', (0, 0), (-1, -1), 1 * mm),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]
            )
        )

        objs.append(tbl)
        objs.append(Spacer(1, 15 * mm))
        start = end
        end += slice_count

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def form_03(request_data):
    """
    Лист назначений
    """

    direction_id = json.loads(request_data["hosp_pk"])
    ind_card = Napravleniya.objects.get(pk=direction_id)
    patient_card = ind_card.client.pk
    patient_data = ind_card.client.get_data_individual()
    assignments = get_assignments(direction_id)
    if sys.platform == "win32":
        locale.setlocale(locale.LC_ALL, "rus_rus")
    else:
        locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")

    pdfmetrics.registerFont(TTFont("PTAstraSerifBold", os.path.join(FONTS_FOLDER, "PTAstraSerif-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("PTAstraSerifReg", os.path.join(FONTS_FOLDER, "PTAstraSerif-Regular.ttf")))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=15 * mm, rightMargin=7 * mm, topMargin=40 * mm, bottomMargin=10 * mm, title="Лист назначений")

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.alignment = TA_JUSTIFY
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    tableTitle = deepcopy(style)
    tableTitle.fontName = "PTAstraSerifBold"
    tableTitle.alignment = TA_LEFT
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenterBold = deepcopy(styleCenter)
    styleCenterBold.fontName = "PTAstraSerifBold"
    styleHeader = deepcopy(style)
    styleHeader.fontName = "PTAstraSerifBold"
    styleHeader.fontSize = 14
    styleHeader.leading = 14
    styleHeader.alignment = TA_CENTER

    objs = []

    table_data = [
        [
            Paragraph("Медицинское вмешательство", tableTitle),
            Paragraph("Дата назначения", tableTitle),
            Paragraph("Подпись лечащего врача (врача-специалиста), сделавшего назначение", tableTitle),
            Paragraph("Дата и время исполнения назначения", tableTitle),
            Paragraph("Фамилия, имя, отчество (при наличии) и подпись медицинского работника, ответственного за исполнение назначения", tableTitle),
        ],
    ]
    assignments_data = [
        [
            Paragraph(f'{" ".join(i["researchTitle"])}', style),
            Paragraph(f'{i["createDate"]}', styleCenter),
            Paragraph(f'{i["whoAssigned"]}', styleCenter),
            Paragraph(f'{i["timeConfirmation"]}', styleCenter),
            Paragraph(f'{i["whoConfirm"]}', styleCenter),
        ]
        for i in assignments
    ]

    table_data.extend(assignments_data)

    columns_width = [None, 40 * mm, 43 * mm, 35 * mm, 40 * mm]

    tbl = Table(table_data, repeatRows=1, colWidths=columns_width, hAlign='LEFT')
    tbl.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.75, colors.black),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 1 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    objs.append(tbl)

    def first_pages(canvas, doc):
        canvas.saveState()
        table_data = [
            [
                Paragraph("Лист назначений", styleHeader),
            ],
            [
                Paragraph(f"История болезни № {direction_id}", styleCenterBold),
            ],
        ]
        tbl = Table(table_data, colWidths=100 * mm, hAlign='CENTER')
        tbl.wrapOn(canvas, 105 * mm, 195 * mm)
        tbl.drawOn(canvas, 105 * mm, 195 * mm)
        canvas.setFont("PTAstraSerifBold", 12)
        canvas.drawString(17 * mm, 185 * mm, "Фамилия, имя, отчество (при наличии):")
        canvas.setFont("PTAstraSerifReg", 12)
        canvas.drawString(95 * mm, 185 * mm, f"{patient_data['fio']}")
        canvas.setFont("PTAstraSerifBold", 12)
        canvas.drawString(17 * mm, 180 * mm, "Дата рождения:")
        canvas.setFont("PTAstraSerifReg", 12)
        canvas.drawString(48 * mm, 180 * mm, f"{patient_data['born']}")
        canvas.setFont("PTAstraSerifBold", 12)
        canvas.drawString(68 * mm, 180 * mm, "г. № медицинской карты:")
        canvas.setFont("PTAstraSerifReg", 12)
        canvas.drawString(118 * mm, 180 * mm, f"{patient_card}")
        canvas.setFont("PTAstraSerifBold", 12)
        canvas.drawString(17 * mm, 175 * mm, "Диагноз (основное заболевание): ")
        canvas.restoreState()

    def later_pages(canvas, doc):
        first_pages(canvas, doc)

    doc.build(objs, onFirstPage=first_pages, onLaterPages=later_pages)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def form_01(request_data):
    """
    Температурный лист по 530н приказу
    """
    num_dir = json.loads(request_data["hosp_pks"])
    direction_obj = Napravleniya.objects.get(pk=num_dir[0])
    hosp_nums_obj = hosp_get_hosp_direction(num_dir[0])
    hosp_nums = ''
    for i in hosp_nums_obj:
        hosp_nums = hosp_nums + ' - ' + str(i.get('direction'))

    ind_card = direction_obj.client
    patient_data = ind_card.get_data_individual()

    hosp_first_num = hosp_nums_obj[0].get("direction")
    first_inspection = primary_reception_get_data(hosp_first_num)

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=portrait(A4), leftMargin=5 * mm, rightMargin=5 * mm, topMargin=13 * mm, bottomMargin=10 * mm,
        allowSplitting=1, title="Форма {}".format("Лист регистрации показателей жизненно важных функций организма")
    )

    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 3.5 * mm

    styleTable = deepcopy(style)
    styleTable.alignment = TA_CENTER
    styleTable.fontSize = 8
    styleTable.leading = 3.5 * mm
    styleTable.spaceAfter = 1.0 * mm

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 12
    styleCenter.leading = 15
    styleCenter.spaceAfter = 1 * mm

    styleCheckMark = deepcopy(style)
    styleCheckMark.alignment = TA_CENTER
    styleCheckMark.fontSize = 6.5
    styleCheckMark.leading = 2.5 * mm
    styleCheckMark.spaceAfter = 1.0 * mm

    range_coeff = 18
    data_temp = get_temperature_list(num_dir[0])
    temperature_data = data_temp.get('Температура (°C)')
    count_table = ceil(len(temperature_data.get('xtext')) / range_coeff)

    objs = []

    date_temperature_with_data = {}
    for date, value in zip(temperature_data.get('xtext'), temperature_data.get('data')):
        date_only = date.split(' ')[0]
        time_only = date.split(' ')[1]
        if date_only not in date_temperature_with_data:
            date_temperature_with_data[date_only] = [f'{time_only} {value}']
        else:
            date_temperature_with_data[date_only].append(f'{time_only} {value}')

    dates = [date for date in date_temperature_with_data for _ in date_temperature_with_data[date]]

    times_values = [time for item in date_temperature_with_data.values() for time in item]

    day_numbers = [Paragraph('', styleCheckMark) for _ in range(len(times_values))]
    day_number = 0
    for day in dates:
        if day in date_temperature_with_data.keys():
            index = list(date_temperature_with_data.keys()).index(day)
            day_numbers[day_number] = Paragraph(f'{index + 1}', styleCheckMark)
        day_number += 1

    values_matrix = [[Paragraph('', styleCheckMark) for _ in range(len(times_values))] for _ in range(8)]
    time_index = 0
    for time_value in times_values:
        temperature = time_value.split(' ')[1]
        if float(temperature) >= 41:
            values_matrix[0][time_index] = Paragraph(temperature, styleCheckMark)
        elif 40 <= float(temperature) < 41:
            values_matrix[1][time_index] = Paragraph(temperature, styleCheckMark)
        elif 39 <= float(temperature) < 40:
            values_matrix[2][time_index] = Paragraph(temperature, styleCheckMark)
        elif 38 <= float(temperature) < 39:
            values_matrix[3][time_index] = Paragraph(temperature, styleCheckMark)
        elif 37 <= float(temperature) < 38:
            values_matrix[4][time_index] = Paragraph(temperature, styleCheckMark)
        elif 36 <= float(temperature) < 37:
            values_matrix[5][time_index] = Paragraph(temperature, styleCheckMark)
        elif 35 <= float(temperature) < 36:
            values_matrix[6][time_index] = Paragraph(temperature, styleCheckMark)
        elif float(temperature) < 35:
            values_matrix[7][time_index] = Paragraph(temperature, styleCheckMark)
        time_index += 1

    for count in range(count_table):
        title_page = [
            Indenter(left=0 * mm),
            Spacer(1, 2 * mm),
            Paragraph('<font fontname="PTAstraSerifBold" size=13>ЛИСТ РЕГИСТРАЦИИ ПОКАЗАТЕЛЕЙ ЖИЗНЕННО ВАЖНЫХ ФУНКЦИЙ ОРГАНИЗМА</font><br/>', styleCenter),
        ]
        objs.extend(title_page)
        objs.append(Spacer(1, 3 * mm))
        objs.extend([Paragraph(f'Фамилия, имя, отчество (при наличии) {patient_data["fio"]}, возраст {patient_data["age"]}, рост пациента, {first_inspection["height"]} см', styleT),
                     Spacer(1, 2 * mm),
                     ])

        inner_table = [
            [Paragraph('Сутки пребывания в стационаре, дневном стационаре', styleTable)] + day_numbers[range_coeff * count:range_coeff * (count + 1)],
            [Paragraph('Дата', styleTable)] + [Paragraph(f'{date}', styleCheckMark) for date in dates][range_coeff * count:range_coeff * (count + 1)],
            [Paragraph('Время', styleTable)] + [Paragraph(f'{time.split(" ")[0]}', styleCheckMark) for time in times_values][range_coeff * count:range_coeff * (count + 1)],
            [Paragraph('Температура тела, (С°)', styleTable)],
            [Paragraph('выше 41', styleTable)] + values_matrix[0][range_coeff * count:range_coeff * (count + 1)],
            [Paragraph('40 - 40,9', styleTable)] + values_matrix[1][range_coeff * count:range_coeff * (count + 1)],
            [Paragraph('39 - 39,9', styleTable)] + values_matrix[2][range_coeff * count:range_coeff * (count + 1)],
            [Paragraph('38 - 38,9', styleTable)] + values_matrix[3][range_coeff * count:range_coeff * (count + 1)],
            [Paragraph('37 - 37,9', styleTable)] + values_matrix[4][range_coeff * count:range_coeff * (count + 1)],
            [Paragraph('36 - 36,9', styleTable)] + values_matrix[5][range_coeff * count:range_coeff * (count + 1)],
            [Paragraph('35 - 35,9', styleTable)] + values_matrix[6][range_coeff * count:range_coeff * (count + 1)],
            [Paragraph('ниже 35', styleTable)] + values_matrix[7][range_coeff * count:range_coeff * (count + 1)],
            [Paragraph('Частота дыхания', styleTable)],
            [Paragraph('SpO2, %', styleTable)],
            [Paragraph('Масса тела (кг)', styleTable)],
            [Paragraph('Выпито жидкости (мл)', styleTable)],
            [Paragraph('Введено жидкостей (в мл) парентерально', styleTable)],
            [Paragraph('Суточный объем мочи (мл)', styleTable)],
            [Paragraph('Стул', styleTable)],
        ]

        cols_width = [10 * mm for _ in range(len(inner_table))]
        cols_width[0] = 20 * mm

        tbl = Table(inner_table, repeatRows=2, colWidths=cols_width, hAlign='LEFT')
        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3 * mm),
                    ('BOTTOMPADDING', (1, 2), (2, 8), 8 * mm),
                    ('TOPPADDING', (0, 0), (-1, -1), 1 * mm),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
                ]
            )
        )

        objs.append(tbl)
        objs.append(Spacer(1, 41 * mm))

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def form_02(request_data):
    """
    Процедурный лист по 530н приказу
    """
    num_dir = json.loads(request_data["hosp_pk"])
    direction = Napravleniya.objects.get(pk=num_dir)
    patient_data = direction.client.get_data_individual()

    hosp_nums_obj = hosp_get_hosp_direction(num_dir)
    hosp_first_num = hosp_nums_obj[0].get("direction")

    first_inspection = primary_reception_get_data(hosp_first_num)
    medicament_allergy = first_inspection.get("medicament_allergy")
    final_diagnos = first_inspection.get("final_diagnos")

    if sys.platform == "win32":
        locale.setlocale(locale.LC_ALL, "rus_rus")
    else:
        locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4), leftMargin=15 * mm, rightMargin=5 * mm, topMargin=13 * mm, bottomMargin=10 * mm, allowSplitting=1, title="Форма {}".format("Лист назначений и их выполнение")
    )

    width, height = landscape(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 3.5 * mm

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 12
    styleCenter.leading = 15
    styleCenter.spaceAfter = 1 * mm

    styleTable = deepcopy(style)
    styleTable.alignment = TA_CENTER
    styleTable.fontSize = 9
    styleTable.leading = 3.5 * mm
    styleTable.spaceAfter = 1.0 * mm

    styleTitleDrug = deepcopy(style)
    styleTitleDrug.alignment = TA_CENTER
    styleTitleDrug.fontSize = 8
    styleTitleDrug.leading = 3.5 * mm
    styleTitleDrug.spaceAfter = 1.0 * mm

    styleCheckMark = deepcopy(style)
    styleCheckMark.alignment = TA_CENTER
    styleCheckMark.fontSize = 6.5
    styleCheckMark.leading = 2.5 * mm
    styleCheckMark.spaceAfter = 1.0 * mm
    space_symbol = '&nbsp;'
    title_page = [
        Indenter(left=0 * mm),
        Spacer(1, 2 * mm),
        Paragraph(f'<font fontname="PTAstraSerifBold" size=13>ЛИСТ НАЗНАЧЕНИЙ И ИХ ВЫПОЛНЕНИЕ {space_symbol*3}</font> ', styleCenter),
    ]

    objs = []

    objs.extend(title_page)
    objs.append(Paragraph(f'Фамилия, имя, отчество (при наличии) {patient_data["fio"]}  Дата рождения {normalize_date(patient_data["born"])}г.', style))
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph(f'N медицинской карты {num_dir}  Палата______', styleT))
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph(f'Диагноз (основное заболевание): {final_diagnos}', styleT))
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph(f'Аллергические реакции на лекарственные препараты, пищевая аллергия или иные виды непереносимости в анамнезе, с указанием типа и вида аллергической реакции: {medicament_allergy}', styleT))
    objs.append(Spacer(1, 2 * mm))

    procedural = json.dumps({'direction': num_dir})
    procedural_obj = HttpRequest()
    procedural_obj._body = procedural
    procedural_obj.user = request_data["user"]
    data = get_procedure_by_dir(procedural_obj)
    results_json = json.loads(data.content.decode('utf-8'))

    all_dates = results_json.get('dates')

    drugs_and_dates = []

    result = results_json.get('result')

    for item in result:
        drug_info_dates = {
            'info': f'{item.get("form_release")} {item.get("drug")} {item.get("method")} {item.get("dosage")}',
        }

        dates = item['dates']
        for date, time_slots in dates.items():
            available_times = [time for time, check in time_slots.items() if check.get('ok')]
            if available_times:
                drug_info_dates[date] = available_times

        drugs_and_dates.append(drug_info_dates)

    range_coeff = 15

    count_table = ceil(len(all_dates) / 15)

    dates_for_table = [Paragraph('', styleTitleDrug) for _ in range(3)]

    for count in range(count_table):

        dates_on_one_sheet = all_dates[range_coeff * count:range_coeff * (count + 1)]

        drugs_title = Paragraph('Лекарственный препарат (наименование, лекарственная форма, дозировка, способ введения (применения), лечебное питание, режим', styleTable)
        start_date = Paragraph('Дата назначения; подпись лечащего врача (врача-специалиста), сделавшего назначение', styleTable)
        cancel_date = Paragraph('Дата отменены; подпись лечащего врача (врача-специалиста), отменившего назначение', styleTable)
        marks = Paragraph(
            'Отметки об исполнении назначения лекарственного препарата, лечебного питания, режима, (дата и время исполнения, подпись медицинского работника, ответственного за исполнение)(время, дата, подпись)',
            styleTable)

        dates_for_table.extend([VerticalParagraph(f'{x}', style=styleTitleDrug) for x in dates_on_one_sheet])

        dates_for_table.append(Paragraph('Сведения о реакции на применение (при наличии)', styleTable))

        inner_table = [
            [drugs_title, start_date, cancel_date, marks],
            dates_for_table
        ]

        for record in drugs_and_dates:

            drug_info = Paragraph(record.get('info'), styleTitleDrug)
            drug_start_date = Paragraph(list(record.keys())[1], styleTitleDrug)
            end_date = Paragraph(list(record.keys())[-1], styleTitleDrug)
            drug_row = [drug_info, drug_start_date, end_date]

            drug_row.extend(['' for _ in range(len(dates_on_one_sheet))])

            for date in list(record.keys())[(range_coeff - 1) * count:(range_coeff - 1) * (count + 1)]:
                if date in dates_on_one_sheet:
                    mark = ''
                    for time in record.get(date):
                        mark += f'V {time} '
                    index = dates_on_one_sheet.index(date)
                    drug_row[index + 3] = Paragraph(mark, styleCheckMark)

            inner_table.append(drug_row)

        signature_row = [Paragraph('Подпись медицинского работника, ответственного за контроль исполнения назначений', styleTable)]
        inner_table.append(signature_row)

        cols_width = [10 * mm for i in range(len(dates_on_one_sheet) + 4)]
        cols_width[0] = cols_width[1] = cols_width[2] = cols_width[-1] = 30 * mm

        tbl = Table(inner_table, repeatRows=2, colWidths=cols_width, hAlign='LEFT')
        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3 * mm),
                    ('BOTTOMPADDING', (1, 2), (2, 8), 8 * mm),
                    ('TOPPADDING', (0, 0), (-1, -1), 1 * mm),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('SPAN', (3, 0), (len(dates_on_one_sheet) + 3, 0)),
                    ('SPAN', (0, 0), (0, 1)),
                    ('SPAN', (1, 0), (1, 1)),
                    ('SPAN', (2, 0), (2, 1)),
                    ('SPAN', (0, len(inner_table) - 1), (2, len(inner_table) - 1)),
                ]
            )
        )

        objs.append(tbl)
        objs.append(Spacer(1, 15 * mm))

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
