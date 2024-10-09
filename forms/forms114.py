import locale
import os.path
import sys
from copy import deepcopy
from io import BytesIO
from typing import List, Union

import pytz
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, Image

from directions.models import TubesRegistration, Issledovaniya
from directions.sql_func import get_data_by_directions_id, get_directions_by_who_create
from hospitals.models import Hospitals
from laboratory.settings import FONTS_FOLDER, TIME_ZONE
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.lib.pagesizes import A4
from laboratory.utils import current_time, strdate, strdatetimeru
from utils.dates import normalize_dots_date
from utils.pagenum import PageNumCanvasPartitionAll
import simplejson as json


def form_01(request_data):
    """
    акт передачи материала
    """

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Symbola', os.path.join(FONTS_FOLDER, 'Symbola.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=12 * mm, rightMargin=5 * mm, topMargin=1 * mm, bottomMargin=15 * mm, allowSplitting=1, title="Форма {}".format("80 мм"))
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10
    style.leading = 11
    style.spaceAfter = 1 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = 0 * mm

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"

    styleFL = deepcopy(style)
    styleFL.firstLineIndent = 10
    styleFL.fontSize = 16

    styleCenter = deepcopy(styleBold)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 10

    styleCenterHospital = deepcopy(styleCenter)
    styleCenterHospital.fontSize = 8

    styleRightBold = deepcopy(styleCenter)
    styleRightBold.alignment = TA_RIGHT

    styleCenterTitle = deepcopy(styleCenter)
    styleCenterTitle.fontSize = 14

    styleTypeResearch = deepcopy(style)
    styleTypeResearch.firstLineIndent = -0.5 * mm

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm
    styleT.face = 'PTAstraSerifReg'

    objs: List[Union[Spacer, Paragraph, Table, KeepTogether]] = []
    user_data = request_data.get("user")

    hospital_title = request_data.get("hospital").title
    date_current = strdate(current_time(only_date=True))
    date_act = request_data.get("date", date_current)
    normalize_date_act = normalize_dots_date(date_act)
    time_now = strdatetimeru(current_time())

    file_jpg = None
    def_hospital = Hospitals.get_default_hospital()
    if def_hospital.title_stamp_executor:
        file_jpg = def_hospital.get_title_stamp_executor_pdf()
    img = None
    if file_jpg:
        img = Image(
            file_jpg,
            185 * mm,
            27 * mm,
        )

    opinion = [
        [img, ''],
    ]
    tbl = Table(opinion, colWidths=(90 * mm, 110 * mm), hAlign='LEFT')
    tbl.setStyle(
        TableStyle(
            [
                ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), -0.5 * mm),
            ]
        )
    )
    objs.append(tbl)
    objs.append(Spacer(1, 3 * mm))
    department_data = f"{user_data.doctorprofile.podrazdeleniye.title} ({hospital_title})"
    objs.append(Paragraph(f'Подразделение: {department_data}', style))
    objs.append(Spacer(1, 0.5 * mm))
    objs.append(Paragraph(f'За дату: {date_act}', style))
    objs.append(Paragraph(f'Время формирования: {time_now} ', style))
    objs.append(Spacer(1, 3 * mm))
    tubes = []
    directions = []
    if "filter" in request_data.keys():
        filterArray = json.loads(request_data.get("filter"))
        for v in filterArray:
            tube_registration = TubesRegistration.objects.get(number=int(v))
            tubes.append(tube_registration)
            date_act = tube_registration.statement_document.create_at.astimezone(pytz.timezone(TIME_ZONE)).strftime("%d.%m.%Y (%H:%M:%S)")

        for v in tubes:  # Перебор пробирок
            iss: Issledovaniya = Issledovaniya.objects.filter(tubes__number=v.number).first()
            directions.append(iss.napravleniye_id)
        directions = list(set(directions))
    else:
        directions = get_directions_by_who_create(tuple([user_data.doctorprofile.pk]), f"{normalize_date_act} 00:00:00", f"{normalize_date_act} 23:59:59")
        directions = [i.napravleniye_id for i in directions]

    objs.append(Paragraph(f'Сопроводительная ведомость от {date_act}', styleCenterTitle))
    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Контейнеры', style))
    objs.append(Spacer(1, 1 * mm))
    opinion = [
        [
            Paragraph('Тип', styleT),
            Paragraph('Биоматериал', styleT),
            Paragraph('ФИО пациента', styleT),
            Paragraph('ШтрихКод', styleT),
            Paragraph('Примечание', styleT),
        ]
    ]

    directions_data = get_data_by_directions_id(tuple(sorted(directions)))
    old_tube_number = ""
    old_type_material = ""
    old_tube_title = ""
    old_patient_fio = ""
    old_direction = ""
    old_tube_registration_time = ""
    step = 0

    total_container = {}
    for i in directions_data:
        if i.tube_number != old_tube_number and step > 0:
            bcd = createBarcodeDrawing('Code128', value=old_tube_number, humanReadable=1, barHeight=7 * mm, width=45 * mm)
            bcd.hAlign = 'LEFT'
            opinion.append(
                [
                    Paragraph(str(old_tube_title), styleT),
                    Paragraph(str(old_type_material), styleT),
                    Paragraph(old_patient_fio, styleT),
                    bcd,
                    Paragraph(f"№{str(old_direction)}<br/>{old_tube_registration_time}", styleT),
                ]
            )
            count = total_container.get(old_tube_title, 0)
            count += 1
            total_container[old_tube_title] = count
        old_tube_number = i.tube_number
        old_type_material = i.laboratory_material
        old_tube_title = i.tube_title
        old_patient_fio = f'{i.patient_family} {i.patient_name} {i.patient_patronymic}'
        old_direction = i.direction_number
        old_tube_registration_time = i.tube_registration_time
        step += 1
    bcd = createBarcodeDrawing('Code128', value=old_tube_number, humanReadable=1, barHeight=7 * mm, width=45 * mm)
    bcd.hAlign = 'LEFT'
    count = total_container.get(old_tube_title, 0)
    count += 1
    total_container[old_tube_title] = count
    opinion.append(
        [
            Paragraph(str(old_tube_title), styleT),
            Paragraph(str(old_type_material), styleT),
            Paragraph(old_patient_fio, styleT),
            bcd,
            Paragraph(f"№{str(old_direction)}<br/>{old_tube_registration_time}", styleT),
        ]
    )

    tbl = Table(opinion, colWidths=[35 * mm, 30 * mm, 50 * mm, 45 * mm, 28 * mm], hAlign='LEFT')
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 2 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0.4 * mm),
                ('TOPPADDING', (0, 0), (-1, -1), 0.3 * mm),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Свод по контейнерам', style))
    objs.append(Spacer(1, 0.5 * mm))

    opinion = [
        [
            Paragraph('Тип', styleT),
            Paragraph('Количество', styleT),
        ]
    ]
    total = 0
    for k, v in total_container.items():
        opinion.append(
            [
                Paragraph(str(k), styleT),
                Paragraph(str(v), styleCenter),
            ]
        )
        total += v

    opinion.append(
        [
            Paragraph("Итого", styleRightBold),
            Paragraph(str(total), styleCenter),
        ]
    )

    tbl = Table(opinion, colWidths=[90 * mm, 25 * mm], hAlign='LEFT')
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 2 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0.4 * mm),
                ('TOPPADDING', (0, 0), (-1, -1), 0.3 * mm),
            ]
        )
    )
    objs.append(tbl)
    objs.append(Spacer(1, 5 * mm))
    objs.append(Paragraph("Ответственный ", style))
    objs.append(Paragraph("____________________/____________________ ", style))

    def first_pages(canvas, document):
        canvas.saveState()
        canvas.setFont("PTAstraSerifReg", 9)
        # вывести атрибуты для подписей
        canvas.setFont('PTAstraSerifReg', 10)
        canvas.drawString(40 * mm, 10 * mm, '____________________________')
        canvas.drawString(135 * mm, 10 * mm, '____________________________')

        canvas.setFont('PTAstraSerifReg', 8)
        canvas.drawString(50 * mm, 7 * mm, '(подпись кто передал)')
        canvas.drawString(145 * mm, 7 * mm, '(подпись кто принял)')

        # вывестии защитны вертикальный мелкий текст
        canvas.rotate(90)
        left_size_str = f"{date_act}-{time_now}-{department_data}"
        canvas.setFont('PTAstraSerifReg', 5.2)
        canvas.drawString(2 * mm, -8 * mm, '{}'.format(6 * left_size_str))
        canvas.restoreState()

    def later_pages(canvas, document):
        canvas.saveState()
        canvas.setFont("PTAstraSerifReg", 9)
        # вывести атрибуты для подписей
        canvas.setFont('PTAstraSerifReg', 10)
        canvas.drawString(40 * mm, 10 * mm, '____________________________')
        canvas.drawString(135 * mm, 10 * mm, '____________________________')

        canvas.setFont('PTAstraSerifReg', 8)
        canvas.drawString(50 * mm, 7 * mm, '(подпись кто передал)')
        canvas.drawString(145 * mm, 7 * mm, '(подпись кто принял)')

        # вывестии защитны вертикальный мелкий текст
        canvas.rotate(90)
        left_size_str = f"{date_act}-{time_now}-{department_data}"
        canvas.setFont('PTAstraSerifReg', 5.2)
        canvas.drawString(2 * mm, -8 * mm, '{}'.format(6 * left_size_str))
        canvas.restoreState()

    doc.build(objs, onFirstPage=first_pages, onLaterPages=later_pages, canvasmaker=PageNumCanvasPartitionAll)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
