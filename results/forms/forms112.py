import datetime
from typing import Union

from reportlab.lib import colors

from hospitals.models import Hospitals
from reportlab.platypus import Paragraph, Spacer, Table, FrameBreak, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.colors import black
from results.forms.flowable import FrameDataCol
from results.prepare_data import fields_result_only_title_fields, get_protocol_data
from directions.models import Issledovaniya, Napravleniya
from laboratory.settings import FONTS_FOLDER
import os.path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def gen_table(table_data: list, column: Union[list, None]=None, span=None, full_grid: bool = False, outer_and_row_grid: bool = False):
    if not table_data:
        return []
    if column:
        table = Table(table_data, column, hAlign='LEFT')
    else:
        table = Table(table_data,  hAlign='LEFT')
    table_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]
    if full_grid:
        table_style.append(('GRID', (0, 0), (-1, -1), 0.75, colors.black))
    if outer_and_row_grid:
        table_style.append(('BOX', (0, 0), (-1, -1), 0.75, colors.black))
        table_style.append(('LINEBELOW', (0, 0), (-1, -1), 0.75, colors.black))
    if span:
        table_style.extend(span)
    table.setStyle(TableStyle(table_style))

    return table


def gen_medicament_table(style_left_bold, style_center, leftnone, title, row_data: list=None):
    table_data = [
        [
            Paragraph(f'{title}', style_left_bold),
            Paragraph('', style_left_bold),
            Paragraph('', style_left_bold),
            Paragraph('', style_left_bold),
            Paragraph('', style_left_bold),
            Paragraph('', style_left_bold),
            Paragraph('', style_left_bold),
            Paragraph('', style_left_bold),
        ],
        [
            Paragraph('', style_center),
            Paragraph('Наименование ЛС (торговое)*', style_center),
            Paragraph('Производитель', style_center),
            Paragraph('Номер серии', style_center),
            Paragraph('Доза, путь введения', style_center),
            Paragraph('Дата начала терапии', style_center),
            Paragraph('Дата окончания терапии', style_center),
            Paragraph('Показание', style_center),
        ]
    ]
    table_data.extend(row_data)

    if leftnone:
        column_params = [7 * mm, 32 * mm, 30 * mm, 15 * mm, 15 * mm, 20 * mm, 21 * mm, 34 * mm]
    else:
        column_params = [7 * mm, 35 * mm, 30 * mm, 15 * mm, 20 * mm, 20 * mm, 21 * mm, 38 * mm,]
    span_cell = [
        ('SPAN', (0, 0), (-1, 0)),
    ]
    table = gen_table(table_data, column_params, span_cell, True)

    return table

def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None):
    """
    112.01 - Извещение о НР ЛП
    """

    hospital: Hospitals = direction.hospital
    hospital_name = hospital.safe_short_title
    hospital_address = hospital.safe_address
    patient_data = direction.client.get_data_individual()

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10
    style.alignment = TA_JUSTIFY

    style_header = deepcopy(style)
    style_header.fontName = "PTAstraSerifBold"
    style_header.fontSize = 10
    style_header.alignment = TA_CENTER

    style_right = deepcopy(style)
    style_right.alignment = TA_RIGHT

    style_left = deepcopy(style)
    style_left.alignment = TA_LEFT

    style_center_bold = deepcopy(style)
    style_center_bold.alignment = TA_CENTER
    style_center_bold.fontName = "PTAstraSerifBold"

    style_center = deepcopy(style_center_bold)
    style_center.fontName = "PTAstraSerifReg"

    style_left_bold = deepcopy(style_left)
    style_left_bold.fontName = "PTAstraSerifBold"

    protocol_fields = []
    protocol_data = get_protocol_data(iss, protocol_fields)

    space = 5 * mm
    space_symbol = "&nbsp;"
    objs = []
    objs.append(Paragraph('ИЗВЕЩЕНИЕ О НЕЖЕЛАТЕЛЬНОЙ РЕАКЦИИ ИЛИ ОТСУТСТВИИ ТЕРАПЕВТИЧЕСКОГО ЭФФЕКТАЛЕКАРСТВЕННОГО ПРЕПАРАТА', style_header))

    objs.append(Spacer(1, space * 2))
    table_data = [
        [
            Paragraph('Первичное ', style_center),
            Paragraph('Дополнительная информация к сообщению <br/>№___________ от_________________', style_left),
        ]
    ]
    objs.append(gen_table(table_data))

    objs.append(Spacer(1, space * 2))

    table_data = [
        [
            Paragraph('Данные пациента', style_left)
        ],
        [
            Paragraph('Инициалы пациента (код пациента)  Пол Вес', style_left)
        ],
        [
            Paragraph('Возраст___________________ Беременность  □, срок _____ недель', style_left)
        ],
        [
            Paragraph('Аллергия    □ Нет    □ Есть, на ______________________________________ ', style_left)
        ],
        [
            Paragraph('Лечение    □    амбулаторное     □    стационарное    □    самолечение            ', style_left)
        ],
    ]

    objs.append(gen_table(table_data, full_grid=True))

    list_bad_medicaments = [
        {"title": "", "manufacturer": "", "serial_number": "", "dose_and_method": "", "start_date": "", "end_date": "", "reason": ""},
        {"title": "", "manufacturer": "", "serial_number": "", "dose_and_method": "", "start_date": "", "end_date": "", "reason": ""},
        {"title": "", "manufacturer": "", "serial_number": "", "dose_and_method": "", "start_date": "", "end_date": "", "reason": ""},
    ]
    bad_medicaments = [[
        [
            Paragraph(f'{key}', style_center),
            Paragraph(f'{medicament["title"]}', style_center),
            Paragraph(f'{medicament["manufacturer"]}', style_center),
            Paragraph(f'{medicament["serial_number"]}', style_center),
            Paragraph(f'{medicament["dose_and_method"]}', style_center),
            Paragraph(f'{medicament["start_date"]}', style_center),
            Paragraph(f'{medicament["end_date"]}', style_center),
            Paragraph(f'{medicament["reason"]}', style_center),
        ]
    ] for key, medicament in enumerate(list_bad_medicaments)]

    title_table = 'Лекарственные средства, предположительно вызвавшие НР'
    objs.append(gen_medicament_table(style_left_bold, style_center, leftnone, title_table, bad_medicaments))

    table_data = [
        [
            Paragraph('Нежелательная реакция', style_left_bold),
            Paragraph('Дата начала НР__________', style_left_bold),
        ],
        [
            Paragraph('Описание реакции* (укажите все детали, включая данные лабораторных исследований)', style_left),
            Paragraph('Критерии серьезности НР:       ', style_left_bold),
        ],
        [
            Paragraph('', style_left),
            Paragraph('□   Смерть', style_left),
        ],
        [
            Paragraph('', style_left),
            Paragraph('□   Угроза жизни', style_left),
        ],
        [
            Paragraph('', style_left),
            Paragraph('□   Госпитализация или ее продление', style_left),
        ],
        [
            Paragraph('Дата разрешения НР', style_left_bold),
            Paragraph('□   Инвалидность', style_left),
        ],
        [
            Paragraph('', style_left),
            Paragraph('□   Врожденные аномалии', style_left),
        ],
        [
            Paragraph('', style_left),
            Paragraph('□   Клинически значимое событие', style_left),
        ],
        [
            Paragraph('', style_left),
            Paragraph('□   Не применимо  ', style_left),
        ],
    ]

    if leftnone:
        column_params = [125 * mm, 49 * mm]
    else:
        column_params = [137 * mm, 49 * mm]

    span_cell = [
        ('SPAN', (0, 1), (0, 4)),
        ('SPAN', (0, 5), (0, 8)),
    ]
    objs.append(gen_table(table_data, column_params, span_cell, True))

    table_data = [
        [
            Paragraph('Предпринятые меры', style_left_bold)
        ],
        [
            Paragraph('□  Без лечения     □  Отмена подозреваемого ЛС     □  Снижение дозы ЛС', style_left)
        ],
        [
            Paragraph(' □  Немедикаментозная терапия (в т.ч. хирургическое вмешательство) ', style_left)
        ],
        [
            Paragraph('□  Лекарственная терапия _________________________________________________________________', style_left)
        ],
        [
            Paragraph('Исход', style_left_bold)
        ],
        [
            Paragraph('□   Выздоровление без последствий    □  Улучшение состояние    □  Состояние без изменений', style_left)
        ],
        [
            Paragraph('□   Выздоровление с последствиями (указать)___________________________________________', style_left)
        ],
        [
            Paragraph(' □   Смерть  □ Неизвестно   □ Не применимо', style_left)
        ],
    ]

    objs.append(gen_table(table_data, full_grid=True))

    objs.append(PageBreak())
    objs.append(Spacer(1, space * 2))

    table_data = [
        [
            Paragraph('Сопровождалась ли отмена ЛС исчезновением НР?', style_left),
            Paragraph('□ Нет □ Да □ ЛС не отменялось □ Не применимо', style_left)
        ],
        [
            Paragraph('Назначалось ли лекарство повторно?  □ Нет  □ Да', style_left),
            Paragraph('Результат___________________ □ Не применимо', style_left)
        ],
    ]

    list_other_medicament = [
        {"title": "", "manufacturer": "", "serial_number": "", "dose_and_method": "", "start_date": "", "end_date": "", "reason": ""},
        {"title": "", "manufacturer": "", "serial_number": "", "dose_and_method": "", "start_date": "", "end_date": "", "reason": ""},
        {"title": "", "manufacturer": "", "serial_number": "", "dose_and_method": "", "start_date": "", "end_date": "", "reason": ""},
        {"title": "", "manufacturer": "", "serial_number": "", "dose_and_method": "", "start_date": "", "end_date": "", "reason": ""},
        {"title": "", "manufacturer": "", "serial_number": "", "dose_and_method": "", "start_date": "", "end_date": "", "reason": ""},
        {"title": "", "manufacturer": "", "serial_number": "", "dose_and_method": "", "start_date": "", "end_date": "", "reason": ""},
    ]
    other_medicaments = [[
        [
            Paragraph(f'{key}', style_center),
            Paragraph(f'{medicament["title"]}', style_center),
            Paragraph(f'{medicament["manufacturer"]}', style_center),
            Paragraph(f'{medicament["serial_number"]}', style_center),
            Paragraph(f'{medicament["dose_and_method"]}', style_center),
            Paragraph(f'{medicament["start_date"]}', style_center),
            Paragraph(f'{medicament["end_date"]}', style_center),
            Paragraph(f'{medicament["reason"]}', style_center),
        ]
    ] for key, medicament in enumerate(list_other_medicament)]
    objs.append(gen_table(table_data, outer_and_row_grid=True))
    title_table = 'Другие лекарственные средства, принимаемые в течение последних 3 месяцев, включая ЛС принимаемые пациентом самостоятельно (по собственному желанию)'
    objs.append(gen_medicament_table(style_left_bold, style_center, leftnone, title_table, other_medicaments))

    fwb.extend(objs)

    return fwb
