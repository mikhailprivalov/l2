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


def gen_table(table_data: list, column: Union[list, None] = None, full_grid: bool = False, outer_and_row_grid: bool = False, custom_style=None) -> Table:
    if not table_data:
        return []
    if column:
        table = Table(table_data, column, hAlign='LEFT')
    else:
        table = Table(table_data, hAlign='LEFT')
    table_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]
    if full_grid:
        table_style.append(('GRID', (0, 0), (-1, -1), 0.75, colors.black))
    if outer_and_row_grid:
        table_style.append(('BOX', (0, 0), (-1, -1), 0.75, colors.black))
        table_style.append(('LINEBELOW', (0, 0), (-1, -1), 0.75, colors.black))
    if custom_style:
        table_style.extend(custom_style)
    table.setStyle(TableStyle(table_style))

    return table


def gen_medicament_table(style_left_bold, style_center, leftnone, title, row_data: list = None):
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
        column_params = [7 * mm, 32 * mm, 29 * mm, 18 * mm, 20 * mm, 19 * mm, 21 * mm, 28 * mm]
    else:
        column_params = [7 * mm, 37 * mm, 33 * mm, 20 * mm, 20 * mm, 20 * mm, 21 * mm, 28 * mm]
    custom_style = [
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#99ccff'))
    ]
    table = gen_table(table_data, column_params, True, False, custom_style)

    return table

def get_boxed_tag(font_size: Union[int, float]=12):
    op_boxed_tag = f'<font face="digit8" size={font_size}>'
    cl_boxed_tag = '</font>'
    return op_boxed_tag, cl_boxed_tag


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
    pdfmetrics.registerFont(TTFont('digit8', os.path.join(FONTS_FOLDER, 'digit88table.ttf')))
    pdfmetrics.registerFont(TTFont('Symbola', os.path.join(FONTS_FOLDER, 'Symbola.ttf')))

    op_boxed_tag = f'<font face="digit8" size=15>'
    cl_boxed_tag = '</font>'
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

    protocol_fields = ['Вес(кг)', 'Беременность', 'Срок беременности (недель)', 'Аллергия', 'Аллергия на', 'Лечение']
    protocol_data = get_protocol_data(iss, protocol_fields)

    space = 5 * mm
    space_symbol = "&nbsp;"
    objs = []
    objs.append(Paragraph('ИЗВЕЩЕНИЕ О НЕЖЕЛАТЕЛЬНОЙ РЕАКЦИИ ИЛИ ОТСУТСТВИИ ТЕРАПЕВТИЧЕСКОГО ЭФФЕКТАЛЕКАРСТВЕННОГО ПРЕПАРАТА', style_header))

    objs.append(Spacer(1, space * 2))
    table_data = [
        [
            Paragraph(f'Первичное {op_boxed_tag}{space_symbol}{cl_boxed_tag}', style_center),
            Paragraph(f'Дополнительная информация к сообщению {op_boxed_tag}{space_symbol}{cl_boxed_tag}<br/>№___________ от_________________', style_left),
        ]
    ]
    objs.append(gen_table(table_data))

    objs.append(Spacer(1, space * 2))

    empty_checkbox = '<font face="Symbola" size=8>\u2610</font>'
    filled_checkbox = '<font face="Symbola" size=8>\u2611</font>'

    if protocol_data["Беременность"] == 'Да':
        pregnancy = f'{filled_checkbox},'
        term_pregnancy = f'Срок {protocol_data["Срок беременности (недель)"]} недель'
    else:
        pregnancy = f'{empty_checkbox}'
        term_pregnancy = ''

    if protocol_data["Аллергия"] == 'Нет':
        allergy = f'{empty_checkbox} Нет'
        allergy_reason = ''
    else:
        allergy = f'{filled_checkbox} Есть'
        allergy_reason = f'на {protocol_data["Аллергия на"]}'

    table_data = [
        [
            Paragraph('Данные пациента', style_left_bold)
        ],
        [
            Paragraph(f'Инициалы пациента (код пациента) {patient_data["fio"]} Пол {patient_data["sex"]} Вес {protocol_data["Вес(кг)"]} кг', style_left)
        ],
        [
            Paragraph(f'Возраст: {patient_data["age"]} Беременность {pregnancy} {term_pregnancy}', style_left)
        ],
        [
            Paragraph(f'Аллергия {allergy} {allergy_reason} ', style_left)
        ],
        [
            Paragraph(f'Лечение {protocol_data["Лечение"]}', style_left)
        ],
    ]

    custom_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#99ccff')),
    ]
    objs.append(gen_table(table_data, full_grid=True, custom_style=custom_style))

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
    ] for key, medicament in enumerate(list_bad_medicaments, 1)]

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
            Paragraph('Дата разрешения НР _________________________________', style_left_bold),
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

    custom_style = [
        ('SPAN', (0, 1), (0, 4)),
        ('SPAN', (0, 5), (0, 8)),
        ('GRID', (1, 0), (1, -1), 0.75, colors.black),
        ('GRID', (0, 0), (0, 0), 0.75, colors.black),
        ('BOX', (0, 0), (0, -1), 0.75, colors.black),
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#99ccff'))
    ]
    objs.append(gen_table(table_data, column_params, False, False, custom_style))

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

    custom_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#99ccff')),
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#99ccff'))
    ]
    objs.append(gen_table(table_data, full_grid=True, custom_style=custom_style))

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
    ] for key, medicament in enumerate(list_other_medicament, 1)]
    objs.append(gen_table(table_data, outer_and_row_grid=True))
    title_table = 'Другие лекарственные средства, принимаемые в течение последних 3 месяцев, включая ЛС принимаемые пациентом самостоятельно (по собственному желанию)'
    objs.append(gen_medicament_table(style_left_bold, style_center, leftnone, title_table, other_medicaments))
    table_data = [
        [
            Paragraph('Данные сообщающего лица', style_left_bold)
        ],
        [
            Paragraph('□  Врач    □  Другой специалист системы здравоохранения    □   Пациент    □  Иной', style_left)
        ],
        [
            Paragraph('Контактный телефон/e-mail:* ________________________________________________________________    ', style_left)
        ],
        [
            Paragraph('Ф.И.О _____________________________________________________________________________________', style_left)
        ],
        [
            Paragraph('Должность и место работы____________________________________________________________________', style_left)
        ],
        [
            Paragraph('Дата сообщения_____________________________________________________________________________', style_left)
        ],
    ]

    custom_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#99ccff')),
    ]

    objs.append(gen_table(table_data, full_grid=True, custom_style=custom_style))
    objs.append(Paragraph(f'{space_symbol * 12} * поле обязательно к заполнению', style))
    objs.append(Spacer(1, space * 2))
    objs.append(Paragraph('Сообщение может быть отправлено:', style))
    objs.append(Paragraph(f'{space_symbol * 7}•{space_symbol * 4}	e-mail: pharm@roszdravnadzor.ru', style))
    objs.append(Paragraph(f'{space_symbol * 7}•{space_symbol * 4}	факс: +7(495)698-15-73,', style))
    objs.append(Paragraph(f'{space_symbol * 7}•{space_symbol * 4}	он-лайн на сайте npr.roszdravnadzor.ru', style))
    objs.append(Paragraph(f'{space_symbol * 7}•{space_symbol * 4}	почтовый адрес: 109074, г. Москва, Славянская площадь, д. 4, строение 1.', style))

    fwb.extend(objs)

    return fwb
