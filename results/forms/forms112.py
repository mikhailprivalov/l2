import json
from typing import Union

from reportlab.lib import colors

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from results.prepare_data import get_protocol_data
from directions.models import Issledovaniya, Napravleniya
from laboratory.settings import FONTS_FOLDER
import os.path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from utils.dates import normalize_date


def gen_table(
    table_data: list, column: Union[list, None] = None, full_grid: bool = False, outer_and_row_grid: bool = False, custom_style: Union[list[tuple], None] = None
) -> Union[Table, list]:
    if not table_data:
        return []
    if column:
        table = Table(table_data, column, hAlign="LEFT")
    else:
        table = Table(table_data, hAlign="LEFT")
    table_style = [("VALIGN", (0, 0), (-1, -1), "TOP")]
    if full_grid:
        table_style.append(("GRID", (0, 0), (-1, -1), 0.75, colors.black))
    if outer_and_row_grid:
        table_style.append(("BOX", (0, 0), (-1, -1), 0.75, colors.black))
        table_style.append(("LINEBELOW", (0, 0), (-1, -1), 0.75, colors.black))
    if custom_style:
        table_style.extend(custom_style)
    table.setStyle(TableStyle(table_style))

    return table


def gen_medicament_table(style_left_bold, style_center, left_none: bool, title: str, row_data: Union[list, None] = None) -> Union[Table, list]:
    table_data = [
        [
            Paragraph(f"{title}", style_left_bold),
            Paragraph("", style_left_bold),
            Paragraph("", style_left_bold),
            Paragraph("", style_left_bold),
            Paragraph("", style_left_bold),
            Paragraph("", style_left_bold),
            Paragraph("", style_left_bold),
            Paragraph("", style_left_bold),
        ],
        [
            Paragraph("", style_center),
            Paragraph("Наименование ЛС (торговое)*", style_center),
            Paragraph("Производитель", style_center),
            Paragraph("Номер серии", style_center),
            Paragraph('Доза, путь введения', style_center),
            Paragraph("Дата начала терапии", style_center),
            Paragraph("Дата окончания терапии", style_center),
            Paragraph("Показание", style_center),
        ],
    ]
    table_data.extend(row_data)

    if left_none:
        column_params = [7 * mm, 32 * mm, 28 * mm, 18 * mm, 20 * mm, 21 * mm, 21 * mm, 28 * mm]
    else:
        column_params = [7 * mm, 37 * mm, 32 * mm, 20 * mm, 20 * mm, 21 * mm, 21 * mm, 28 * mm]
    custom_style = [("SPAN", (0, 0), (-1, 0)), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#99ccff"))]
    table = gen_table(table_data, column_params, True, False, custom_style)

    return table


def string_check(text: str, value: str = "да") -> bool:
    return text.lower() == value.lower()


def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None, **kwargs):
    """
    112.01 - Извещение о НР ЛП
    """
    patient_data = direction.client.get_data_individual()

    pdfmetrics.registerFont(TTFont("PTAstraSerifBold", os.path.join(FONTS_FOLDER, "PTAstraSerif-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("PTAstraSerifReg", os.path.join(FONTS_FOLDER, "PTAstraSerif-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("Symbola", os.path.join(FONTS_FOLDER, "Symbola.ttf")))

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

    protocol_fields = [
        "Первичное",
        "Дополнение к сообщению №",
        "Дополнение к сообщению от",
        "Вес (кг)",
        "Беременность",
        "Срок беременности (недель)",
        "Аллергия",
        "Аллергия на",
        "Лечение",
        "ЛП предположительно вызвавшие НР",
        "Дата начала НР",
        "Описание НР",
        "Дата разрешения НР",
        "Смерть",
        "Угроза жизни",
        "Госпитализация",
        "Инвалидность",
        "Врожденные аномалии",
        "Клинически значимое событие",
        "Не применимо",
        "Без лечения",
        "Отмена подозреваемого ЛС",
        "Снижение дозы ЛС",
        "Немедикаментозная терапия",
        "Лекарственная терапия",
        "Лекарственная терапия(описание)",
        "Исход",
        "Последствия",
        "Сопровождалась ли отмена ЛС исчезновением НР",
        "Назначалось ли лекарство повторно",
        "Результат",
        "Другие ЛП принимаемые в течение последних 3 месяцев",
        "Сообщающее лицо",
        "Контактный телефон/e-mail",
        "Ф.И.О",
        "Должность и место работы",
        "Дата сообщения",
    ]
    protocol_data = get_protocol_data(iss, protocol_fields)

    space = 5 * mm
    space_symbol = "&nbsp;"
    empty_checkbox = '<font face="Symbola" size=8>\u2610</font>'
    filled_checkbox = '<font face="Symbola" size=8>\u2611</font>'
    objs = []
    objs.append(Paragraph("ИЗВЕЩЕНИЕ О ПОБОЧНОМ ДЕЙСТВИИ, НЕЖЕЛАТЕЛЬНОЙ РЕАКЦИИ ИЛИ ОТСУТСТВИИ ОЖИДАЕМОГО ТЕРАПЕВТИЧЕСКОГО ЭФФЕКТА ЛЕКАРСТВЕННОГО ПРЕПАРАТА", style_header))
    primary = empty_checkbox
    addition = empty_checkbox
    message_num = '___________'
    message_date = '_________________'
    if string_check(protocol_data["Первичное"]):
        primary = filled_checkbox
    elif string_check(protocol_data["Первичное"], 'нет'):
        addition = filled_checkbox
        message_num = protocol_data["Дополнение к сообщению №"] if protocol_data["Дополнение к сообщению №"] else message_num
        message_date = protocol_data["Дополнение к сообщению от"] if protocol_data["Дополнение к сообщению от"] else message_date

    objs.append(Spacer(1, space * 2))
    table_data = [
        [
            Paragraph(f"Первичное {primary}", style_center),
            Paragraph(f"Дополнительная информация к сообщению {addition}<br/>№ {message_num} от {message_date}", style_left),
        ]
    ]
    objs.append(gen_table(table_data))

    objs.append(Spacer(1, space * 2))

    weight = "__________"
    pregnancy = f"{empty_checkbox}"
    term_pregnancy = '_____'
    allegry_variants = ['нет', 'есть']
    allergy = [empty_checkbox, empty_checkbox]
    allergy_reason = "______________________________________ "
    treatments_variants = ['амбулаторное', 'стационарное', 'самолечение']
    treatments = [empty_checkbox, empty_checkbox, empty_checkbox]

    if protocol_data["Вес (кг)"]:
        weight = protocol_data["Вес (кг)"]
    if string_check(protocol_data["Беременность"], "Да"):
        pregnancy = f'{filled_checkbox},'
        term_pregnancy = protocol_data["Срок беременности (недель)"]
    if protocol_data["Аллергия"]:
        title = protocol_data["Аллергия"]
        index = allegry_variants.index(title.lower())
        allergy[index] = filled_checkbox
    if protocol_data["Аллергия на"]:
        allergy_reason = protocol_data["Аллергия на"]
    if protocol_data["Лечение"]:
        title = protocol_data["Лечение"]
        index = treatments_variants.index(title.lower())
        treatments[index] = filled_checkbox

    table_data = [
        [Paragraph("Данные пациента", style_left_bold)],
        [Paragraph(f'Инициалы пациента (код пациента): {patient_data["fio"]} ({direction.client_id}) Пол: {patient_data["sex"]} Вес: {weight} кг', style_left)],
        [Paragraph(f'Возраст: {patient_data["age"]} Беременность: {pregnancy} Срок {term_pregnancy} недель', style_left)],
        [Paragraph(f"Аллергия {allergy[0]} Нет {allergy[1]} Есть, на {allergy_reason}", style_left)],
        [Paragraph(f"Лечение {treatments[0]} амбулаторное {treatments[1]} стационарное {treatments[2]} самолечение", style_left)],
    ]

    custom_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#99ccff")),
    ]
    objs.append(gen_table(table_data, full_grid=True, custom_style=custom_style))

    list_bad_medicaments = [["", "", "", "", "", "", ""], ["", "", "", "", "", "", ""], ["", "", "", "", "", "", ""]]

    if protocol_data["ЛП предположительно вызвавшие НР"]:
        list_bad_medicaments = json.loads(protocol_data["ЛП предположительно вызвавшие НР"]).get("rows", [])

    bad_medicaments = [
        [
            Paragraph(f'{key}', style_center),
            Paragraph(f"{medicament[0] if len(medicament) >= 1 else ''}", style_center),
            Paragraph(f"{medicament[1] if len(medicament) >= 2 else ''}", style_center),
            Paragraph(f"{medicament[2] if len(medicament) >= 3 else ''}", style_center),
            Paragraph(f"{medicament[3] if len(medicament) >= 4 else ''}", style_center),
            Paragraph(f"{normalize_date(medicament[4]) if len(medicament) >= 5 else ''}", style_center),
            Paragraph(f"{normalize_date(medicament[5]) if len(medicament) >= 6 else ''}", style_center),
            Paragraph(f"{medicament[6] if len(medicament) >= 7 else ''}", style_center),
        ]
        for key, medicament in enumerate(list_bad_medicaments, 1)
    ]

    title_table = "Лекарственные средства, предположительно вызвавшие НР"
    objs.append(gen_medicament_table(style_left_bold, style_center, leftnone, title_table, bad_medicaments))

    start_reaction = "__________"
    end_reaction = "_________________________________"
    description_reaction = "Описание реакции* (укажите все детали, включая данные лабораторных исследований)"
    death, threat_life, hospitalization, disability, anomalies, clinically_event, not_applicable = (
        protocol_data["Смерть"],
        protocol_data["Угроза жизни"],
        protocol_data["Госпитализация"],
        protocol_data["Инвалидность"],
        protocol_data["Врожденные аномалии"],
        protocol_data["Клинически значимое событие"],
        protocol_data["Не применимо"],
    )
    if protocol_data["Дата начала НР"]:
        start_reaction = protocol_data["Дата начала НР"]
    if protocol_data["Дата разрешения НР"]:
        end_reaction = protocol_data["Дата разрешения НР"]
    if protocol_data["Описание НР"]:
        description_reaction = protocol_data["Описание НР"]

    table_data = [
        [
            Paragraph("Нежелательная реакция", style_left_bold),
            Paragraph(f"Дата начала НР: {start_reaction}", style_left_bold),
        ],
        [
            Paragraph(f"{description_reaction}", style_left),
            Paragraph("Критерии серьезности НР:", style_left_bold),
        ],
        [
            Paragraph("", style_left),
            Paragraph(f"{filled_checkbox if string_check(death) else empty_checkbox} Смерть", style_left),
        ],
        [
            Paragraph("", style_left),
            Paragraph(f"{filled_checkbox if string_check(threat_life) else empty_checkbox} Угроза жизни", style_left),
        ],
        [
            Paragraph("", style_left),
            Paragraph(f"{filled_checkbox if string_check(hospitalization) else empty_checkbox} Госпитализация или ее продление", style_left),
        ],
        [
            Paragraph(f"Дата разрешения НР: {end_reaction}", style_left_bold),
            Paragraph(f"{filled_checkbox if string_check(disability) else empty_checkbox} Инвалидность", style_left),
        ],
        [
            Paragraph("", style_left),
            Paragraph(f"{filled_checkbox if string_check(anomalies) else empty_checkbox} Врожденные аномалии", style_left),
        ],
        [
            Paragraph("", style_left),
            Paragraph(f"{filled_checkbox if string_check(clinically_event) else empty_checkbox} Клинически значимое событие", style_left),
        ],
        [
            Paragraph("", style_left),
            Paragraph(f"{filled_checkbox if string_check(not_applicable) else empty_checkbox} Не применимо  ", style_left),
        ],
    ]

    if leftnone:
        column_params = [125 * mm, 49 * mm]
    else:
        column_params = [137 * mm, 49 * mm]

    custom_style = [
        ("SPAN", (0, 1), (0, 4)),
        ("SPAN", (0, 5), (0, 8)),
        ("GRID", (1, 0), (1, -1), 0.75, colors.black),
        ("GRID", (0, 0), (0, 0), 0.75, colors.black),
        ("BOX", (0, 0), (0, -1), 0.75, colors.black),
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#99ccff")),
    ]
    objs.append(gen_table(table_data, column_params, False, False, custom_style))

    not_treatment, cancel_medicament, reducing_medicament, non_grug_therapy, medicament_therapy = (
        protocol_data["Без лечения"],
        protocol_data["Отмена подозреваемого ЛС"],
        protocol_data["Снижение дозы ЛС"],
        protocol_data["Немедикаментозная терапия"],
        protocol_data["Лекарственная терапия"],
    )
    description_therapy = "_________________________________________________________________"
    if protocol_data["Лекарственная терапия(описание)"]:
        description_therapy = protocol_data["Лекарственная терапия(описание)"]

    issue_list = ["выздоровление без последствий", "улучшение состояние", "состояние без изменений", "выздоровление с последствиями", "смерть", "неизвестно", "не применимо"]
    issue = [
        empty_checkbox,
        empty_checkbox,
        empty_checkbox,
        empty_checkbox,
        empty_checkbox,
        empty_checkbox,
        empty_checkbox,
    ]
    issue_effect = "___________________________________________"
    if protocol_data["Исход"]:
        title = protocol_data["Исход"]
        index = issue_list.index(title.lower())
        issue[index] = filled_checkbox
    if protocol_data["Последствия"]:
        issue_effect = protocol_data["Последствия"]

    table_data = [
        [Paragraph("Предпринятые меры", style_left_bold)],
        [
            Paragraph(
                f"{filled_checkbox if string_check(not_treatment) else empty_checkbox}  Без лечения     {filled_checkbox if string_check(cancel_medicament) else empty_checkbox} "
                f"Отмена подозреваемого ЛС {filled_checkbox if string_check(reducing_medicament) else empty_checkbox} Снижение дозы ЛС",
                style_left,
            )
        ],
        [Paragraph(f"{filled_checkbox if string_check(non_grug_therapy) else empty_checkbox} Немедикаментозная терапия (в т.ч. хирургическое вмешательство) ", style_left)],
        [Paragraph(f"{filled_checkbox if string_check(medicament_therapy) else empty_checkbox}  Лекарственная терапия: {description_therapy}", style_left)],
        [Paragraph("Исход", style_left_bold)],
        [Paragraph(f"{issue[0]} Выздоровление без последствий {issue[1]} Улучшение состояние {issue[2]} Состояние без изменений", style_left)],
        [Paragraph(f"{issue[3]} Выздоровление с последствиями (указать): {issue_effect}", style_left)],
        [Paragraph(f"{issue[4]} Смерть {issue[5]} Неизвестно {issue[6]} Не применимо", style_left)],
    ]

    custom_style = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#99ccff")), ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#99ccff"))]
    objs.append(gen_table(table_data, full_grid=True, custom_style=custom_style))

    objs.append(Spacer(1, space * 2))

    result_cancel_list = ["нет", "да", "лс не отменялось", "не применимо"]
    result_cancel = [
        empty_checkbox,
        empty_checkbox,
        empty_checkbox,
        empty_checkbox,
    ]
    if protocol_data["Сопровождалась ли отмена ЛС исчезновением НР"]:
        title = protocol_data["Сопровождалась ли отмена ЛС исчезновением НР"]
        index = result_cancel_list.index(title.lower())
        result_cancel[index] = filled_checkbox

    repeat_variant = ["нет", "да", 'не применимо']
    repeat = [empty_checkbox, empty_checkbox, empty_checkbox]
    repeat_result = "___________________"
    if protocol_data["Назначалось ли лекарство повторно"]:
        title = protocol_data["Назначалось ли лекарство повторно"]
        index = repeat_variant.index(title.lower())
        repeat[index] = filled_checkbox

    if protocol_data["Результат"]:
        repeat_result = protocol_data["Результат"]

    table_data = [
        [
            Paragraph("Сопровождалась ли отмена ЛС исчезновением НР?", style_left),
            Paragraph(f"{result_cancel[0]} Нет {result_cancel[1]} Да {result_cancel[2]} ЛС не отменялось {result_cancel[3]} Не применимо", style_left),
        ],
        [Paragraph(f"Назначалось ли лекарство повторно?  {repeat[0]} Нет  {repeat[1]} Да", style_left), Paragraph(f"Результат: {repeat_result} {repeat[2]} Не применимо", style_left)],
    ]

    objs.append(gen_table(table_data, outer_and_row_grid=True))
    list_other_medicament = [["", "", "", "", "", "", ""], ["", "", "", "", "", "", ""], ["", "", "", "", "", "", ""]]

    if protocol_data["Другие ЛП принимаемые в течение последних 3 месяцев"]:
        list_other_medicament = json.loads(protocol_data["Другие ЛП принимаемые в течение последних 3 месяцев"]).get("rows", [])

    other_medicaments = [
        [
            Paragraph(f"{key}", style_center),
            Paragraph(f"{medicament[0] if len(medicament) >= 1 else ''}", style_center),
            Paragraph(f"{medicament[1] if len(medicament) >= 2 else ''}", style_center),
            Paragraph(f"{medicament[2] if len(medicament) >= 3 else ''}", style_center),
            Paragraph(f"{medicament[3] if len(medicament) >= 4 else ''}", style_center),
            Paragraph(f"{normalize_date(medicament[4]) if len(medicament) >= 5 else ''}", style_center),
            Paragraph(f"{normalize_date(medicament[5]) if len(medicament) >= 6 else ''}", style_center),
            Paragraph(f"{medicament[6] if len(medicament) >= 7 else ''}", style_center),
        ]
        for key, medicament in enumerate(list_other_medicament, 1)
    ]
    title_table = "Другие лекарственные средства, принимаемые в течение последних 3 месяцев, включая ЛС принимаемые пациентом самостоятельно (по собственному желанию)"
    objs.append(gen_medicament_table(style_left_bold, style_center, leftnone, title_table, other_medicaments))

    reporting_person_variants = [
        "врач",
        "другой специалист системы здравоохранения",
        "пациент",
        "иной",
    ]
    reporting_person = [
        empty_checkbox,
        empty_checkbox,
        empty_checkbox,
        empty_checkbox,
    ]
    contacts = "________________________________________________________________"
    reporting_person_fio = "_____________________________________________________________________________________"
    reporting_person_position = "____________________________________________________________________"
    reporting_date = "_____________________________________________________________________________"

    if protocol_data["Сообщающее лицо"]:
        title = protocol_data["Сообщающее лицо"]
        index = reporting_person_variants.index(title.lower())
        reporting_person[index] = filled_checkbox
    if protocol_data["Контактный телефон/e-mail"]:
        contacts = protocol_data["Контактный телефон/e-mail"]
    if protocol_data["Ф.И.О"]:
        reporting_person_fio = protocol_data["Ф.И.О"]
    if protocol_data["Должность и место работы"]:
        reporting_person_position = protocol_data["Должность и место работы"]
    if protocol_data["Дата сообщения"]:
        reporting_date = protocol_data["Дата сообщения"]

    table_data = [
        [Paragraph("Данные сообщающего лица", style_left_bold)],
        [Paragraph(f"{reporting_person[0]} Врач {reporting_person[1]} Другой специалист системы здравоохранения {reporting_person[2]} Пациент {reporting_person[3]}  Иной", style_left)],
        [Paragraph(f"Контактный телефон/e-mail:* {contacts}", style_left)],
        [Paragraph(f"Ф.И.О: {reporting_person_fio}", style_left)],
        [Paragraph(f"Должность и место работы: {reporting_person_position}", style_left)],
        [Paragraph(f"Дата сообщения: {reporting_date}", style_left)],
    ]

    custom_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#99ccff")),
    ]

    objs.append(gen_table(table_data, full_grid=True, custom_style=custom_style))
    objs.append(Paragraph(f"{space_symbol * 12} * поле обязательно к заполнению", style))
    objs.append(Spacer(1, space * 2))
    objs.append(Paragraph("Сообщение может быть отправлено:", style))
    objs.append(Paragraph(f"{space_symbol * 7}•{space_symbol * 4}	e-mail: pharm@roszdravnadzor.ru", style))
    objs.append(Paragraph(f"{space_symbol * 7}•{space_symbol * 4}	факс: +7(495)698-15-73,", style))
    objs.append(Paragraph(f"{space_symbol * 7}•{space_symbol * 4}	он-лайн на сайте npr.roszdravnadzor.ru", style))
    objs.append(Paragraph(f"{space_symbol * 7}•{space_symbol * 4}	почтовый адрес: 109074, г. Москва, Славянская площадь, д. 4, строение 1.", style))

    fwb.extend(objs)

    return fwb
