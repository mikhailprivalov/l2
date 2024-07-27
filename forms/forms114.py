import datetime
import locale
import os.path
import sys
from copy import deepcopy
from io import BytesIO
from typing import List, Union
import simplejson as json
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, Image

from directions.models import Napravleniya
from directions.sql_func import get_data_by_directions_id, get_directions_by_who_create
from hospitals.models import Hospitals
from laboratory.settings import FONTS_FOLDER
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.lib.pagesizes import A4
from laboratory.utils import current_time, strdate, strdatetimeru
from utils.dates import normalize_dots_date


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
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=10 * mm, rightMargin=5 * mm, topMargin=1 * mm, bottomMargin=1 * mm, allowSplitting=1, title="Форма {}".format("80 мм"))
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

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 10
    styleCenter.leading = 10
    styleCenter.spaceAfter = 0 * mm

    styleCenterHospital = deepcopy(styleCenter)
    styleCenterHospital.fontSize = 8

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
    objs.append(Paragraph(f'Подразделение: {user_data.doctorprofile.podrazdeleniye.title} ({hospital_title})', style))
    objs.append(Spacer(1, 0.5 * mm))
    objs.append(Paragraph(f'За дату: {date_act}', style))
    objs.append(Paragraph(f'Время формирования: {time_now} ', style))
    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Контейнеры', style))
    objs.append(Spacer(1, 1 * mm))
    opinion = [
        [
            Paragraph('Тип', styleT),
            Paragraph('Биоматериал', styleT),
            Paragraph('ФИО пациента', styleT),
            Paragraph('ШтрихКод', styleT),
            Paragraph('Направление №', styleT),
        ]
    ]

    directions = get_directions_by_who_create(tuple([user_data.doctorprofile.pk]), f"{normalize_date_act} 00:00:00", f"{normalize_date_act} 23:59:59")
    directions = [i.napravleniye_id for i in directions]
    directions_data = get_data_by_directions_id(tuple(sorted(directions)))
    old_tube_number = ""
    old_type_material = ""
    old_tube_title = ""
    old_patient_fio = ""
    old_direction = ""
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
                    Paragraph(str(old_direction), styleT),
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
            Paragraph(str(old_direction), styleT),
        ]
    )

    tbl = Table(opinion, colWidths=[35 * mm, 30 * mm, 50 * mm, 50 * mm, 28 * mm], hAlign='LEFT')
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




    objs.append(Paragraph("ПОДПИСЬ ________________ ", style))

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
