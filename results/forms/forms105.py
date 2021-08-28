
from utils.dates import normalize_date
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import directory.models as directory
from directions.models import ParaclinicResult
from appconf.manager import SettingManager
import os.path
from laboratory.settings import FONTS_FOLDER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .flowable import FrameDataUniversal
from directions.models import Issledovaniya

pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
styleSheet = getSampleStyleSheet()
style = styleSheet["Normal"]
style.fontName = "PTAstraSerifReg"
style.fontSize = 9
style.alignment = TA_JUSTIFY
style.leading = 3 * mm

styleCentre = deepcopy(style)
styleCentre.alignment = TA_CENTER

styleBold = deepcopy(style)
styleBold.fontName = "PTAstraSerifBold"

styleCentreBold = deepcopy(styleBold)
styleCentreBold.alignment = TA_CENTER

hospital_name = SettingManager.get("org_title")
hospital_address = SettingManager.get("org_address")
hospital_kod_ogrn = SettingManager.get("org_ogrn")

styleT = deepcopy(style)
styleT.alignment = TA_LEFT
styleT.fontSize = 9
styleT.leading = 3 * mm

styleTBold = deepcopy(styleT)
styleTBold.fontName = "PTAstraSerifBold"


def form_01(direction, iss: Issledovaniya, fwb, doc, leftnone, user=None):
    # Мед. св-во о смерти 106/у
    template = add_template(iss, direction, 0)
    fwb.extend(template)
    template = add_line_split(iss, direction, 107)
    fwb.extend(template)
    template = death_data(iss, direction, 107)
    fwb.extend(template)

    return fwb


def add_template(iss: Issledovaniya, direction, offset=0):
    # Мед. св-во о смерти 106/у
    text = []
    text = title_data(text, "2xx", "123456789", "20.08.2021", "взамен окончательного")
    fio = "Ивано Иван Иванович Ивано Иван"
    text.append(Spacer(1, 1.7 * mm))
    text = fio_tbl(text, "1. Фамилия, имя, отчество (при наличии) умершего(ей):", fio)

    # Пол
    text.append(Spacer(1, 0.3 * mm))
    text = sex_tbl(text, "ж")

    # Дата рождения
    born_day = "01"
    born_month = "01"
    born_year = "1970"
    text = born_tbl(text, "")
    text.append(Spacer(1, 0.3 * mm))

    # Дата смерти
    text = death_tbl(text, "4. Дата смерти:", "",)

    text = address_tbl(text, "", "5. Регистрация по месту жительства (пребывания) умершего(ей):")

    # Смерть наступила
    text = where_death_start_tbl(text, "")
    text.append(Spacer(1, 0.2 * mm))
    text.append(Paragraph('Для детей, умерших в возрасте до 1 года:', styleBold))
    text.append(Spacer(1, 0.5 * mm))

    opinion = [
        [
            Paragraph('7. Дата рождения:', styleT),
            Paragraph(f'число', styleT),
            Paragraph('', styleT),
            Paragraph(', месяц', styleT),
            Paragraph('', styleT),
            Paragraph(', год', styleT),
            Paragraph('', styleT),
            Paragraph(', число месяцев', styleT),
            Paragraph('', styleT),
            Paragraph(', число дней', styleT),
            Paragraph('', styleT),
            Paragraph('жизни', styleT),
        ],
    ]
    col_width = (29 * mm, 17 * mm, 8 * mm, 15 * mm, 8 * mm, 10 * mm, 8 * mm, 24 * mm, 8 * mm, 20 * mm, 8 * mm, 15 * mm)
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), 0 * mm),
        ('LINEBELOW', (2, 0), (2, 0), 0.75, colors.black),
        ('LINEBELOW', (4, 0), (4, 0), 0.75, colors.black),
        ('LINEBELOW', (6, 0), (6, 0), 0.75, colors.black),
        ('LINEBELOW', (8, 0), (8, 0), 0.75, colors.black),
        ('LINEBELOW', (10, 0), (10, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    # Место рождения
    text = address_tbl(text, "", "8. Место рождения")
    text = fio_tbl(text, "9. Фамилия, имя, отчество (при наличии) матери:", fio)

    obj = []
    obj.append(FrameDataUniversal(0 * mm, 5 * mm, 190 * mm, 95 * mm, text=text))

    return obj


def add_line_split(iss: Issledovaniya, direction, offset=0):
    # Лини отреза
    text = []
    text = line_split(text)

    obj = []
    obj.append(FrameDataUniversal(0 * mm, 4 * mm, 190 * mm, 5 * mm, text=text))

    return obj


def death_data(iss: Issledovaniya, direction, offset=0):
    # Лини отреза
    text = []
    text = title_med_organization(text, {"full_title": "Государственное бюджетное учреждение здравоохранения Иркутское областное бюро судебномедицинской экспертизы",
                                         "org_address": "обл Иркутская, г Усолье-Сибирское, ул Менделеева, ДОМ 21", "org_license": "", "org_okpo": ""})
    text = title_data(text, "2xx", "123456789", "20.08.2021", "взамен окончательного")
    fio = "Ивано Иван Иванович Ивано Иван"
    text.append(Spacer(1, 1.7 * mm))
    text = fio_tbl(text, "1. Фамилия, имя, отчество (при наличии) умершего(ей):", fio)

    # Пол
    text.append(Spacer(1, 0.3 * mm))
    text = sex_tbl(text, "ж")

    # Дата рождения
    born_day = "01"
    born_month = "01"
    born_year = "1970"
    text = born_tbl(text, "")

    text = patient_passport(text, {"type": "Паспорт гражданина РФ (России)", "serial": "2504", "number": "000000"})
    text = who_issue_passport(text, {"who_issue": "УВД Свердловского района гор Иркутска", "date_issue": "20.00.2000"})
    text = patient_snils(text, "1234567890123")
    text = patient_polis(text, "0000 0000 0000 0000")
    text = death_tbl(text, "7. Дата смерти:", "")
    text = address_tbl(text, "", "8. Регистрация по месту жительства (пребывания) умершего(ей):")
    text = type_city(text, "город")
    text = where_death_start_tbl(text, "")
    text = child_death_befor_month(text, "")
    text = child_death_befor_year(text, {"weight": 3500, "child_count": 1, "mother_born": "", "mother_age": "", "mother_family": "", "mother_name": "", "mother_patronimyc": ""})
    text = family_status(text, "")
    text = education(text, "")
    text = work_position(text, "")
    text = bottom_colontitul(text, "* В случае смерти детей, возраст которых указан в пунктах 13 - 14, пункты 15 - 17 заполняются в отношении их матерей.")

    obj = []
    obj.append(FrameDataUniversal(0 * mm, 0 * mm, 190 * mm, 158 * mm, text=text))

    return obj


# общие функции
def title_data(text, serial, number, date_issue, type_death_document):
    text.append(Paragraph("КОРЕШОК МЕДИЦИНСКОГО СВИДЕТЕЛЬСТВА О СМЕРТИ", styleCentreBold))
    text.append(Spacer(1, 0.1 * mm))
    text.append(Paragraph("К УЧЕТНОЙ ФОРМЕ № 106/У", styleCentreBold))
    text.append(Spacer(1, 0.2 * mm))
    text.append(Paragraph(f"СЕРИЯ {serial} No {number}", styleCentreBold))
    text.append(Spacer(1, 0.1 * mm))
    text.append(Paragraph(f"Дата выдачи {date_issue}", styleCentreBold))
    final, preparatory, instead_preparatory, instead_final = "окончательного", "предварительного", "взамен предварительного", "взамен окончательного"
    if type_death_document.lower().find('взамен окончательного') != -1:
        instead_final = "<u><font face=\"PTAstraSerifBold\">взамен окончательного</font></u>"
    elif type_death_document.lower().find('взамен предварительного') != -1:
        instead_final = "<u><font face=\"PTAstraSerifBold\">взамен предварительного</font></u>"
    elif type_death_document.lower().find('окончательн') != -1:
        instead_final = "<u><font face=\"PTAstraSerifBold\">окончательного</font></u>"
    elif type_death_document.lower().find('предварительн') != -1:
        instead_final = "<u><font face=\"PTAstraSerifBold\">предварительного</font></u>"
    text.append(Paragraph(f"({final}, {preparatory}, {instead_preparatory}, {instead_final}) (подчеркнуть)", styleCentre))

    return text


def gen_table(opinion, col_width, tbl_style, row_height=None):
    tbl = Table(opinion, colWidths=col_width, rowHeights=row_height, hAlign='LEFT', )
    tbl.setStyle(TableStyle(tbl_style))
    return tbl


def fio_tbl(text, type, fio):
    opinion = [
        [
            Paragraph(f'{type}', styleT),
            Paragraph(f'{fio}', styleT),
        ],
    ]
    col_width = (80 * mm, 110 * mm)
    tbl_style = [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
                ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
            ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)
    return text


def sex_tbl(text, sex):
    if sex == "м":
        sex_m = Paragraph(', <u>мужской</u>', styleTBold)
    else:
        sex_m = Paragraph(' мужской', styleT)
    if sex == "ж":
        sex_w = Paragraph(', <u>женский</u>', styleTBold)
    else:
        sex_w = Paragraph(', женский', styleT)

    opinion = [
        [
            Paragraph(f'2.Пол:', styleT),
            sex_m,
            Paragraph('1', styleT),
            sex_w,
            Paragraph('2', styleT),
        ],
    ]
    col_width = (11 * mm, 17 * mm, 6 * mm, 19 * mm, 6 * mm)
    tbl_style = [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
                ('GRID', (2, 0), (2, 0), 0.75, colors.black),
                ('GRID', (-1, -1), (-1, -1), 0.75, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
            ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)
    return text


def born_tbl(text, born_data):
    # Дата рождения
    born_day = "01"
    born_month = "01"
    born_year = "1970"

    opinion = [
        [
            Paragraph(f'3.Дата рождения:', styleT),
            Paragraph(f'число', styleT),
            Paragraph(f'{born_day}', styleT),
            Paragraph('месяц', styleT),
            Paragraph(f'{born_month}', styleT),
            Paragraph('год', styleT),
            Paragraph(f'{born_year}', styleT),
        ],
    ]

    tbl_style = [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
                ('LEFTPADDING', (0, 1), (0, 1), 0 * mm),
                ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
                ('LINEBELOW', (2, 0), (2, 0), 0.75, colors.black),
                ('LINEBELOW', (4, 0), (4, 0), 0.75, colors.black),
                ('LINEBELOW', (6, 0), (6, 0), 0.75, colors.black),
                ('LINEBELOW', (2, 1), (2, 1), 0.75, colors.black),
                ('LINEBELOW', (4, 1), (4, 1), 0.75, colors.black),
                ('LINEBELOW', (6, 1), (6, 1), 0.75, colors.black),
                ('LINEBELOW', (8, 1), (8, 1), 0.75, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
            ]
    col_width = (28 * mm, 14 * mm, 8 * mm, 14 * mm, 8 * mm, 10 * mm, 12 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    return text


def death_tbl(text, number, death_data):
    # Дата смерти
    death_day = "01"
    death_month = "01"
    death_year = "1970"
    death_hour = "23"
    death_min = "00"

    opinion = [
        [
            Paragraph(f'{number}', styleT),
            Paragraph(f'число', styleT),
            Paragraph(f'{death_day}', styleT),
            Paragraph('месяц', styleT),
            Paragraph(f'{death_month}', styleT),
            Paragraph('год', styleT),
            Paragraph(f'{death_year}', styleT),
            Paragraph('час.', styleT),
            Paragraph(f'{death_hour}', styleT),
            Paragraph('мин.', styleT),
            Paragraph(f'{death_min}', styleT),
        ],
    ]

    tbl_style = [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
                ('LEFTPADDING', (0, 1), (0, 1), 0 * mm),
                ('TOPPADDING', (0, 0), (-1, -1), -1 * mm),
                ('LINEBELOW', (2, 0), (2, 0), 0.75, colors.black),
                ('LINEBELOW', (4, 0), (4, 0), 0.75, colors.black),
                ('LINEBELOW', (6, 0), (6, 0), 0.75, colors.black),
                ('LINEBELOW', (8, 0), (8, 0), 0.75, colors.black),
                ('LINEBELOW', (10, 0), (10, 0), 0.75, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
            ]
    col_width = (28 * mm, 14 * mm, 8 * mm, 14 * mm, 8 * mm, 10 * mm, 12 * mm, 10 * mm, 8 * mm, 12 * mm, 8 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    return text


def address_tbl(text, data_address, type_address):
    region = "Область Иркутская"
    opinion = [
        [
            Paragraph(f'{type_address} субъект Российской Федерации:', styleT),
            Paragraph(f'{region}', styleT),
        ],
    ]
    col_widths = (135 * mm, 55 * mm)
    tbl_style = [
                ('GRID', (0, 0), (-1, -1), 0.1, colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
                ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
                ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
            ]
    tbl = gen_table(opinion, col_widths, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    # город
    region_town = ""
    city = "Иркутск"
    opinion = [[Paragraph('район', styleT), Paragraph(f'{region_town}', styleT), Paragraph('город', styleT), Paragraph(f'{city}', styleT), ], ]
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.1, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('LINEBELOW', (3, 0), (3, 0), 0.75, colors.black),
    ]
    col_width = (17 * mm, 77 * mm, 16 * mm, 80 * mm,)
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    # населенный пунк
    localcity = ""
    street = "Иркутск"
    opinion = [[Paragraph('населенный пункт', styleT), Paragraph(f'{localcity}', styleT), Paragraph('улица', styleT), Paragraph(f'{street}', styleT), ], ]
    col_width = (37 * mm, 67 * mm, 16 * mm, 70 * mm,)
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.1, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('LINEBELOW', (3, 0), (3, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    # дом, стр, корп, кв, комн
    opinion = [
        [
            Paragraph('дом', styleT),
            Paragraph(f'', styleT),
            Paragraph('стр.', styleT),
            Paragraph(f'', styleT),
            Paragraph('корп.', styleT),
            Paragraph(f'', styleT),
            Paragraph('кв.', styleT),
            Paragraph(f'', styleT),
            Paragraph('комн.', styleT),
            Paragraph(f'', styleT),
        ],
    ]
    col_width = (14 * mm, 15 * mm, 12 * mm, 12 * mm, 14 * mm, 15 * mm, 12 * mm, 15 * mm, 14 * mm, 15 * mm,)
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.1, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('LINEBELOW', (3, 0), (3, 0), 0.75, colors.black),
        ('LINEBELOW', (5, 0), (5, 0), 0.75, colors.black),
        ('LINEBELOW', (7, 0), (7, 0), 0.75, colors.black),
        ('LINEBELOW', (9, 0), (9, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    return text


def where_death_start_tbl(text, params):
    opinion = [
        [
            Paragraph('6.Смерть наступила:', styleT),
            Paragraph(f' на месте происшествия', styleT),
            Paragraph('1', styleT),
            Paragraph(', в машине скорой помощи', styleT),
            Paragraph('2', styleT),
            Paragraph(f', в стационаре', styleT),
            Paragraph('3', styleT),
            Paragraph(f' , дома', styleT),
            Paragraph('4', styleT),
        ],
    ]
    col_width = (30 * mm, 36 * mm, 6 * mm, 42 * mm, 6 * mm, 24 * mm, 6 * mm, 12 * mm, 6 * mm,)
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),
        ('GRID', (6, 0), (6, 0), 0.75, colors.black),
        ('GRID', (8, 0), (8, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    # Смерть наступила
    opinion = [
        [
            Paragraph('в образовательной организации', styleT),
            Paragraph(f'5', styleT),
            Paragraph('в другом месте', styleT),
            Paragraph('6', styleT),
        ],
    ]
    col_width = (50 * mm, 6 * mm, 24 * mm, 6 * mm,)
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.1, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    return text


def line_split(text):
    step_round_dash = (1.5 * mm, 1 * mm)

    opinion = [
        [
            Paragraph('', style),
            Paragraph('линия отреза', style),
            Paragraph('', style),
        ],
    ]
    tbl = Table(opinion, hAlign='LEFT', rowHeights=5 * mm, colWidths=(80 * mm, 25 * mm, 80 * mm))
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.1 * mm, colors.white),
                ('LINEBELOW', (0, 0), (0, 0),  0.2 * mm, colors.gray, 'round', step_round_dash),
                ('LINEBELOW', (2, 0), (2, 0), 0.2 * mm, colors.gray, 'round', step_round_dash),
                ('BOTTOMPADDING', (1, 0), (1, 0), 1 * mm),
            ]
        )
    )
    text.append(tbl)
    return text


def patient_passport(text, data_document):
    opinion = [
        [
            Paragraph(f'4.Документ, удостоверяющий личность умершего:', styleT),
            Paragraph(f"{data_document['type']}", styleT),
            Paragraph('серия', styleT),
            Paragraph(f"{data_document['serial']}", styleT),
            Paragraph('номер', styleT),
            Paragraph(f"{data_document['number']}", styleT),
        ],
    ]

    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LINEBELOW', (1,0), (1, 0), 0.75, colors.black),
        ('LINEBELOW', (3, 0), (3, 0), 0.75, colors.black),
        ('LINEBELOW', (5, 0), (5, 0), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    col_width = (73 * mm, 52 * mm, 15 * mm, 15 * mm, 15 * mm, 18 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    return text


def who_issue_passport(text, data_document):
    opinion = [
        [
            Paragraph(f'кем и когда выдан', styleT),
            Paragraph(f"{data_document['who_issue']} {data_document['date_issue']}", styleT),
        ],
    ]

    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('LINEBELOW', (1,0), (1, 0), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    col_width = (33 * mm, 157 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    return text


def patient_snils(text, snils_number):
    opinion = [
        [
            Paragraph(f'5. СНИЛС', styleT),
            Paragraph(f"{snils_number}", styleT),
        ],
    ]

    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LINEBELOW', (1,0), (1, 0), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    col_width = (23 * mm, 167 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    return text


def patient_polis(text, polis_number):
    opinion = [
        [
            Paragraph(f'6.Полис ОМС:', styleT),
            Paragraph(f"{polis_number}", styleT),
        ],
    ]

    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LINEBELOW', (1,0), (1, 0), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    col_width = (23 * mm, 167 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    return text


def type_city(text, type):
    if type == "город":
        type_gorod = Paragraph(' <u>городская</u>', styleTBold)
    else:
        type_gorod = Paragraph(' городская', styleT)
    if type == "село":
        type_selo = Paragraph(', <u>сельская</u>', styleTBold)
    else:
        type_selo = Paragraph(', сельская', styleT)

    opinion = [
        [
            Paragraph(f'9. Местность:', styleT),
            type_gorod,
            Paragraph('1', styleT),
            type_selo,
            Paragraph('2', styleT),
        ],
    ]
    col_width = (21 * mm, 19 * mm, 6 * mm, 18 * mm, 6 * mm)
    tbl_style = [
                ('GRID', (0, 0), (-1, -1), 0.1, colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
                ('GRID', (2, 0), (2, 0), 0.75, colors.black),
                ('GRID', (-1, -1), (-1, -1), 0.75, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
            ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)
    return text


def child_death_befor_month(text, params):
    opinion = [
        [
            Paragraph('13. * Для детей, умерших в возрасте от 168 час. до 1 месяца:', styleT),
            Paragraph(f' доношенный (37-41 недель)', styleT),
            Paragraph('1', styleT),
            Paragraph(', недоношенный (менее 37 недель)', styleT),
            Paragraph('2', styleT),
        ],
    ]
    col_width = (84 * mm, 42 * mm, 6 * mm, 50 * mm, 6 * mm, )
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    opinion = [
        [
            Paragraph('переношенный (42 недель и более)', styleT),
            Paragraph(f'3', styleT),
        ],
    ]
    col_width = (55 * mm, 6 * mm,)
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.1, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (1, 0), (1, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    return text


def child_death_befor_year(text, params):
    opinion = [
        [
            Paragraph('14.*Для детей, умерших в возрасте от 168 час. до 1 года:', styleT),
            Paragraph(f' масса тела ребёнка при рождении  ', styleT),
            Paragraph(f' {params["weight"]}', styleT),
            Paragraph(f' грамм', styleT),
            Paragraph('1', styleT),
        ],
    ]
    col_width = (82 * mm, 50 * mm, 12 * mm, 12 * mm, 6 * mm, )
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.1, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('LINEBELOW', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    opinion = [
        [
            Paragraph('каким по счету был ребенок у матери (считая умерших и не считая мертворождённых)', styleT),
            Paragraph(f' {params["child_count"]}', styleT),
            Paragraph("", styleT),
            Paragraph('2', styleT),
        ],
    ]
    col_width = (125 * mm, 6 * mm, 5 * mm, 6 * mm,)
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.2, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    opinion = [
        [
            Paragraph('дата рождения матери', styleT),
            Paragraph(f' {params["mother_born"]}', styleT),
            Paragraph("", styleT),
            Paragraph('3', styleT),
            Paragraph('возраст матери (полных лет)', styleT),
            Paragraph(f' {params["mother_age"]}', styleT),
            Paragraph("", styleT),
            Paragraph('4', styleT),
        ],
    ]
    col_width = (40 * mm, 15 * mm, 5 * mm, 6 * mm, 45 * mm, 15 * mm, 5 * mm, 6 * mm,)
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.2, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
        ('LINEBELOW', (5, 0), (5, 0), 0.75, colors.black),
        ('GRID', (7, 0), (7, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.5 * mm))
    text.append(tbl)

    opinion = [
        [
            Paragraph('фамилия матери', styleT),
            Paragraph(f' {params["mother_family"]}', styleT),
            Paragraph("", styleT),
            Paragraph('5', styleT),
            Paragraph(', имя', styleT),
            Paragraph(f' {params["mother_name"]}', styleT),
            Paragraph("", styleT),
            Paragraph('6', styleT),
            Paragraph(', отчество (при наличии)', styleT),
            Paragraph(f' {params["mother_patronimyc"]}', styleT),
            Paragraph("", styleT),
            Paragraph('7', styleT),

        ],
    ]
    col_width = (30 * mm, 25 * mm, 5 * mm, 6 * mm, 14 * mm, 20 * mm, 5 * mm, 6 * mm, 40 * mm, 25 * mm, 5 * mm, 6 * mm,)
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.2, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
        ('LINEBELOW', (5, 0), (5, 0), 0.75, colors.black),
        ('GRID', (7, 0), (7, 0), 0.75, colors.black),
        ('LINEBELOW', (9, 0), (9, 0), 0.75, colors.black),
        ('GRID', (11, 0), (11, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.5 * mm))
    text.append(tbl)

    return text


def family_status(text, params):
    brak, not_brak, not_known = "состоял(а) в зарегистрированном браке", "не состоял(а) в зарегистрированном браке", "неизвестно"
    opinion = [
        [
            Paragraph('15.*Семейное положение:', styleT),
            Paragraph(f' {brak}', styleT),
            Paragraph('1', styleT),
            Paragraph(f' {not_brak}', styleT),
            Paragraph('2', styleT),
            Paragraph(f' {not_known}', styleT),
            Paragraph('3', styleT),
        ],
    ]
    col_width = (38 * mm, 56 * mm, 6 * mm, 60 * mm, 6 * mm, 18 * mm, 6 * mm, )
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.1, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),
        ('GRID', (6, 0), (6, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    return text


def education(text, params):
    high_prof, not_high_prof, middle_prof, middle_common = "профессиональное: высшее", ", неполное высшее", ", среднее профессиональное", "общее: среднее"
    opinion = [
        [
            Paragraph('16.* Образование:', styleT),
            Paragraph(f' {high_prof}', styleT),
            Paragraph('1', styleT),
            Paragraph(f' {not_high_prof}', styleT),
            Paragraph('2', styleT),
            Paragraph(f' {middle_prof}', styleT),
            Paragraph('3', styleT),
            Paragraph(f' {middle_common}', styleT),
            Paragraph('4', styleT),
        ],
    ]
    col_width = (27 * mm, 40 * mm, 6 * mm, 30 * mm, 6 * mm, 41 * mm, 6 * mm,  26 * mm, 6 * mm, )
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.1, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),
        ('GRID', (6, 0), (6, 0), 0.75, colors.black),
        ('GRID', (8, 0), (8, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    common, start, before_school, not_has_start, not_known = "основное", ", начальное", ", дошкольное", ", не имеет начального образования", ", неизвестно"
    opinion = [
        [
            Paragraph(f' {common}', styleT),
            Paragraph('5', styleT),
            Paragraph(f' {start}', styleT),
            Paragraph('6', styleT),
            Paragraph(f' {before_school}', styleT),
            Paragraph('7', styleT),
            Paragraph(f' {not_has_start}', styleT),
            Paragraph('8', styleT),
            Paragraph(f' {not_known}', styleT),
            Paragraph('9', styleT),
        ],
    ]
    col_width = (20 * mm, 6 * mm, 20 * mm, 6 * mm, 21 * mm, 6 * mm,  50 * mm, 6 * mm, 19 * mm, 6 * mm, )
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.1, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
        ('GRID', (5, 0), (5, 0), 0.75, colors.black),
        ('GRID', (7, 0), (7, 0), 0.75, colors.black),
        ('GRID', (9, 0), (9, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    return text


def work_position(text, params):
    worked, military, pensioner, student = "работал(а)", ", проходил(а) военную или приравненную к ней службу", ", пенсионер(ка)", "студент(ка)"
    opinion = [
        [
            Paragraph('17. * Занятость:', styleT),
            Paragraph(f' {worked}', styleT),
            Paragraph('1', styleT),
            Paragraph(f' {military}', styleT),
            Paragraph('2', styleT),
            Paragraph(f' {pensioner}', styleT),
            Paragraph('3', styleT),
            Paragraph(f' {student}', styleT),
            Paragraph('4', styleT),
        ],
    ]
    col_width = (24 * mm, 18 * mm, 6 * mm, 80 * mm, 6 * mm, 24 * mm, 6 * mm,  20 * mm, 6 * mm, )
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.1, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),
        ('GRID', (6, 0), (6, 0), 0.75, colors.black),
        ('GRID', (8, 0), (8, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    not_work, others, not_known = "не работал(а)", ", прочие", ", неизвестно"
    opinion = [
        [
            Paragraph(f' {not_work}', styleT),
            Paragraph('5', styleT),
            Paragraph(f' {others}', styleT),
            Paragraph('6', styleT),
            Paragraph(f' {not_known}', styleT),
            Paragraph('7', styleT),
        ],
    ]
    col_width = (26 * mm, 6 * mm, 17 * mm, 6 * mm, 21 * mm, 6 * mm, )
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.1, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
        ('GRID', (5, 0), (5, 0), 0.75, colors.black),
        ('GRID', (7, 0), (7, 0), 0.75, colors.black),
        ('GRID', (9, 0), (9, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    return text


def title_med_organization(text, params):
    styleOrg = deepcopy(styleT)
    styleOrg.fontSize = 8
    # styleOrg.leading = 2 * mm
    opinion = [
        [
            Paragraph(f'Наименование медицинской организации (индивидуального предпринимателя,осуществляющего медицинскую деятельность)<br/>{params["full_title"]}<br/>'
                      f'адрес места нахождения {params["org_address"]}<br/>'
                      f'Код по ОКПО {params["org_okpo"]}<br/>'
                      f'Номер и дата выдачи лицензии на осуществление медицинской деятельности: <br/>{params["org_license"]}<br/>', styleOrg),
            Paragraph('', styleOrg),
            Paragraph('Код формы по ОКУД _______<br/>Медицинская документация<br/>Учётная форма № 106/У<br/>Утверждена приказом Минздрава России <br/>от «15» апреля 2021 г. № 352н', styleOrg),
        ],
    ]
    col_width = (125 * mm, 5 * mm, 60 * mm,)
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (-1, -1), 1 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    return text


def bottom_colontitul(text, params):
    styleOrg = deepcopy(styleT)
    styleOrg.fontSize = 7
    styleOrg.leading = 2 * mm
    opinion = [
        [
            Paragraph(f'{params}', styleOrg),
        ],
    ]
    col_width = (190 * mm)
    tbl_style = [
        ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 15 * mm),
        ('LEFTPADDING', (0, 0), (-1, -1), 1 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    return text

