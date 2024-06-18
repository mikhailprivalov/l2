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
from directions.sql_func import get_data_by_directions_id
from hospitals.models import Hospitals
from laboratory.settings import FONTS_FOLDER
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.lib.pagesizes import A4


def form_01(request_data):
    """
    одна из настраиваемых форм по умолчанию
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

    directions = json.loads(request_data.get("napr_id", '[]'))
    directions_data = get_data_by_directions_id(tuple(sorted(directions)))
    unique_card = set([i.patient_card_id for i in directions_data])
    unique_hospital_orders = set([i.himself_input_external_hosp_title for i in directions_data])
    directions_set = sorted(directions)

    if len(unique_card) > 1 or len(unique_hospital_orders) > 1:
        return False
    patient_fio = ''
    patient_birthday = ''
    patient_sex = ''
    himself_input_external_hosp_title = ''
    direction_create = ''
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
    patient_family = ""
    patient_name = ""
    patient_patronymic = ""

    for i in directions_data:
        himself_input_external_hosp_title = i.himself_input_external_hosp_title
        patient_fio = f'{i.patient_family} {i.patient_name} {i.patient_patronymic}'
        patient_family = i.patient_family
        patient_name = i.patient_name
        patient_patronymic = i.patient_patronymic
        patient_birthday = i.patient_birthday
        patient_sex = i.patient_sex
        direction_create = i.direction_create
        break

    opinion = [
        [
            Paragraph('Заказчик', styleT),
            Paragraph(f'{himself_input_external_hosp_title}', styleT),
        ],
        [
            Paragraph('Пациент', styleT),
            Paragraph(f'{patient_fio}', styleT),
        ],
        [
            Paragraph('Дата рождения:', styleT),
            Paragraph(f'{patient_birthday}', styleT),
        ],
        [
            Paragraph('Пол:', styleT),
            Paragraph(f'{patient_sex}', styleT),
        ],
        [
            Paragraph('Телефон:', styleT),
            Paragraph('', styleT),
        ],
    ]

    tbl = Table(opinion, colWidths=[29 * mm, 160 * mm], hAlign='LEFT')
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (0, 0), (-1, -1), 0 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), -0.2 * mm),
                ('TOPPADDING', (0, 0), (-1, -1), -0.2 * mm),
            ]
        )
    )

    objs.append(tbl)
    objs.append(Spacer(1, 3 * mm))

    opinion = [
        [
            Paragraph('Лаборатория', styleT),
            Paragraph(def_hospital.title, styleT),
        ],
        [
            Paragraph('Время взятия', styleT),
            Paragraph(direction_create, styleT),
        ],
        [
            Paragraph('(создания заказа)', styleT),
            Paragraph('', styleT),
        ],
    ]

    tbl = Table(opinion, colWidths=[29 * mm, 160 * mm], hAlign='LEFT')
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (0, 0), (-1, -1), 0.1 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), -0.2 * mm),
                ('TOPPADDING', (0, 0), (-1, -1), -0.2 * mm),
            ]
        )
    )
    objs.append(tbl)
    objs.append(Spacer(1, 2 * mm))

    directions_string = ", ".join(str(elem) for elem in directions_set)
    objs.append(Paragraph(f'Направление № {directions_string}', style))
    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Исследования', style))
    objs.append(Spacer(1, 1 * mm))

    opinion = [
        [
            Paragraph('Код', styleT),
            Paragraph('Наименование', styleT),
            Paragraph('Контейнер', styleT),
            Paragraph('Направление', styleT),
        ]
    ]
    for i in directions_data:
        opinion.append(
            [
                Paragraph(str(i.research_internal_code), styleT),
                Paragraph(str(i.research_title), styleT),
                Paragraph(str(i.tube_number), styleT),
                Paragraph(str(i.direction_number), styleT),
            ]
        )

    tbl = Table(opinion, colWidths=[35 * mm, 90 * mm, 35 * mm, 25 * mm], hAlign='LEFT')
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 2 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), -0.1 * mm),
                ('TOPPADDING', (0, 0), (-1, -1), -0.1 * mm),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Контейнеры', style))
    objs.append(Spacer(1, 1 * mm))
    opinion = [
        [
            Paragraph('Тип', styleT),
            Paragraph('Биоматериал', styleT),
            Paragraph('ШтрихКод', styleT),
            Paragraph('Кол-во', styleT),
        ]
    ]
    old_tube_number = ""
    old_type_material = ""
    old_tube_title = ""
    step = 0
    for i in directions_data:
        if i.tube_number != old_tube_number and step > 0:
            bcd = createBarcodeDrawing('Code128', value=old_tube_number, humanReadable=1, barHeight=7 * mm, width=45 * mm)
            bcd.hAlign = 'LEFT'
            opinion.append(
                [
                    Paragraph(str(old_tube_title), styleT),
                    Paragraph(str(old_type_material), styleT),
                    bcd,
                    Paragraph("1", styleT),
                ]
            )
        old_tube_number = i.tube_number
        old_type_material = i.laboratory_material
        old_tube_title = i.tube_title
        step += 1
    bcd = createBarcodeDrawing('Code128', value=old_tube_number, humanReadable=1, barHeight=7 * mm, width=45 * mm)
    bcd.hAlign = 'LEFT'
    opinion.append(
        [
            Paragraph(str(old_tube_title), styleT),
            Paragraph(str(old_type_material), styleT),
            bcd,
            Paragraph("1", styleT),
        ]
    )

    tbl = Table(opinion, colWidths=[50 * mm, 70 * mm, 50 * mm, 15 * mm], hAlign='LEFT')
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
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph("Прием медикаментов (дозировка): _____________________________________________________________________", style))
    objs.append(Paragraph("Текущее состояние, влияющее на результаты исследования (диагноз, физическое состояние, ФИО лечащего врача): ", style))
    objs.append(Paragraph("________________________________________________________________________", style))
    objs.append(Paragraph("________________________________________________________________________", style))
    objs.append(Paragraph("Дополнительные сведения для отдельных исследований (рост, вес/ суточный диурез/ последний день менструации / срок беременности):", style))
    objs.append(Paragraph("________________________________________________________________________", style))
    objs.append(Paragraph("Сведение о биоматериале, собранном вне процедурного кабинета (дата взятия, время взятия):", style))
    objs.append(Paragraph("________________________________________________________________________", style))
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph("Настоящим подтверждаю правильность указанных в этом направлении данных кода и наименования исследования.", style))
    space_symbol = '&nbsp;'
    objs.append(Paragraph(f"ПОДПИСЬ ________________ {patient_family} {patient_name[0]}.{patient_patronymic[0]}.{space_symbol * 5} ДАТА: {direction_create.split(' ')[0]}", style))
    objs.append(Spacer(1, 2 * mm))
    objs.append(
        Paragraph("Настоящим подтверждаю, что с правилами преаналитики ознакомлен(а), мне разъяснено, что несоблюдение указанных правил может повлиять на результат исследований.", style))
    objs.append(Paragraph(f"ПОДПИСЬ ________________ {patient_family} {patient_name[0]}.{patient_patronymic[0]}.{space_symbol * 5}ДАТА: {direction_create.split(' ')[0]}", style))

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
