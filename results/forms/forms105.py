
from utils.dates import normalize_date
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
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

styleOrg = deepcopy(styleT)
styleOrg.fontSize = 8

styleColontitul = deepcopy(styleT)
styleColontitul.fontSize = 7
styleColontitul.leading = 2 * mm

styleColontitulBold = deepcopy(styleColontitul)
styleColontitulBold.fontName = "PTAstraSerifBold"

styleTBold = deepcopy(styleT)
styleTBold.fontName = "PTAstraSerifBold"

op_bold_tag = '<font face="PTAstraSerifBold">'
cl_bold_tag = '</font>'

space_symbol = '&nbsp;'


def form_01(direction, iss: Issledovaniya, fwb, doc, leftnone, user=None):
    # Мед. св-во о смерти 106/у
    template = add_template(iss, direction, 5 * mm)
    fwb.extend(template)
    template = add_line_split(iss, direction, 4 * mm)
    fwb.extend(template)
    template = death_data(iss, direction, 0 * mm)
    fwb.extend(template)
    fwb.append(PageBreak())

    template = second_page_add_template(iss, direction, 0 * mm)
    fwb.extend(template)
    template = add_line_split(iss, direction, -1 * mm)
    fwb.extend(template)
    template = death_data(iss, direction, -5 * mm)
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

    opinion = gen_opinion(['7. Дата рождения', 'число', '', ', месяц', '', ', год', '', ', число месяцев', '', ', число дней', '', 'жизни'])
    col_width = (29 * mm, 17 * mm, 8 * mm, 15 * mm, 8 * mm, 10 * mm, 8 * mm, 24 * mm, 8 * mm, 20 * mm, 8 * mm, 15 * mm)
    tbl_style = [
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
    obj.append(FrameDataUniversal(0 * mm,  offset, 190 * mm, 95 * mm, text=text))

    return obj


def second_page_add_template(iss: Issledovaniya, direction, offset=0):
    #
    text = []
    text = back_size(text)
    text = why_death(text, "")
    fio = ""
    text = fio_tbl(text, "14. Фамилия, имя, отчество (при наличии) получателя", fio)
    text.append(Paragraph("Документ, удостоверяющий личность получателя (серия, номер, кем выдан)", styleT))
    text = destination_person_passport(text, "")
    text = destination_person_snils(text, "")
    text.append(Spacer(1, 2 * mm))
    text.append(Paragraph(f"«___» ___________ 20 ___ г.{space_symbol * 30} Подпись получателя _________________________", styleT))


    obj = []
    obj.append(FrameDataUniversal(0 * mm,  offset, 190 * mm, 95 * mm, text=text))

    return obj


def add_line_split(iss: Issledovaniya, direction, offset=0):
    # Лини отреза
    text = []
    text = line_split(text)

    obj = [(FrameDataUniversal(0 * mm, offset, 190 * mm, 5 * mm, text=text))]

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
    obj.append(FrameDataUniversal(0 * mm, offset, 190 * mm, 168 * mm, text=text))

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


def gen_opinion(data):
    opinion = [[Paragraph(f"{k}", styleT) for k in data]]
    return opinion


def gen_table(opinion, col_width, tbl_style, row_height=None):
    tbl = Table(opinion, colWidths=col_width, rowHeights=row_height, hAlign='LEFT', )
    tbl.setStyle(TableStyle(tbl_style))
    return tbl


def fio_tbl(text, type, fio):
    opinion = gen_opinion([type, fio])
    col_width = (80 * mm, 110 * mm)
    tbl_style = [
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
        sex_m = f'{op_bold_tag}<u>мужской</u>{cl_bold_tag}'
    else:
        sex_m = ' мужской'
    if sex == "ж":
        sex_w = f'{op_bold_tag}<u>женский</u>{cl_bold_tag}'
    else:
        sex_w = ', женский'

    opinion = gen_opinion(['2.Пол:', sex_m, '1', sex_w, '2' ])
    col_width = (11 * mm, 17 * mm, 6 * mm, 19 * mm, 6 * mm)
    tbl_style = [
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

    opinion = gen_opinion(['3.Дата рождения:', 'число', born_day, 'месяц', born_month, 'год', born_year])

    tbl_style = [
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

    opinion = gen_opinion([number, 'число', death_day, 'месяц', death_month, 'год', death_year, 'час.', death_hour, 'мин.', death_min])

    tbl_style = [
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
    opinion = gen_opinion([f'{type_address} субъект Российской Федерации:', region ])
    col_widths = (135 * mm, 55 * mm)
    tbl_style = [
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
    opinion = gen_opinion(['район', region_town, 'город', city])
    tbl_style = [
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
    opinion = gen_opinion(['населенный пункт', localcity, 'улица', street])
    col_width = (37 * mm, 67 * mm, 16 * mm, 70 * mm,)
    tbl_style = [
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
    opinion = gen_opinion(['дом', '', 'стр.', '', 'корп.', '', 'кв.', '', 'комн.', ''])
    col_width = (14 * mm, 15 * mm, 12 * mm, 12 * mm, 14 * mm, 15 * mm, 12 * mm, 15 * mm, 14 * mm, 15 * mm,)
    tbl_style = [
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
    opinion = gen_opinion(['6.Смерть наступила:', ' на месте происшествия', '1', ', в машине скорой помощи', '2', ', в стационаре', '3', ' , дома', '4'])
    col_width = (30 * mm, 36 * mm, 6 * mm, 42 * mm, 6 * mm, 24 * mm, 6 * mm, 12 * mm, 6 * mm,)
    tbl_style = [
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
    opinion = gen_opinion(['в образовательной организации', '5', 'в другом месте', '6'])
    col_width = (50 * mm, 6 * mm, 24 * mm, 6 * mm,)
    tbl_style = [
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

    styleColor = deepcopy(style)
    styleColor.textColor = colors.gray

    opinion = [[Paragraph('', style), Paragraph('линия отреза', styleColor), Paragraph('', style), ], ]
    tbl = Table(opinion, hAlign='LEFT', rowHeights=5 * mm, colWidths=(80 * mm, 25 * mm, 80 * mm))
    tbl.setStyle(
        TableStyle(
            [
                ('LINEBELOW', (0, 0), (0, 0),  0.2 * mm, colors.gray, 'round', step_round_dash),
                ('LINEBELOW', (2, 0), (2, 0), 0.2 * mm, colors.gray, 'round', step_round_dash),
                ('BOTTOMPADDING', (1, 0), (1, 0), -0.5 * mm),
            ]
        )
    )
    text.append(tbl)
    return text


def patient_passport(text, data_document):
    opinion = gen_opinion(['4.Документ, удостоверяющий личность умершего:', data_document["type"], 'серия', data_document["serial"], 'номер', data_document['number']])
    tbl_style = [
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
    opinion = gen_opinion(['кем и когда выдан', f"{data_document['who_issue']} {data_document['date_issue']}"])
    tbl_style = [
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
    opinion = gen_opinion(['5.СНИЛС', snils_number ])
    tbl_style = [
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
    opinion = gen_opinion(['6.Полис ОМС:', polis_number])

    tbl_style = [
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
        type_gorod = f'{op_bold_tag}<u>городская</u>{cl_bold_tag}'
    else:
        type_gorod = ' городская'
    if type == "село":
        type_selo = f'{op_bold_tag}<u>сельская</u>{cl_bold_tag}'
    else:
        type_selo = ', сельская'

    opinion = gen_opinion(['9. Местность:', type_gorod, '1', type_selo, '2'])
    col_width = (21 * mm, 19 * mm, 6 * mm, 18 * mm, 6 * mm)
    tbl_style = [
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
    opinion = gen_opinion(['13. * Для детей, умерших в возрасте от 168 час. до 1 месяца:', ' доношенный (37-41 недель)', '1', ', недоношенный (менее 37 недель)', '2'])
    col_width = (84 * mm, 42 * mm, 6 * mm, 50 * mm, 6 * mm, )
    tbl_style = [
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

    opinion = gen_opinion(['переношенный (42 недель и более)', '3'])
    col_width = (55 * mm, 6 * mm,)
    tbl_style = [
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
    opinion = gen_opinion(['14.*Для детей, умерших в возрасте от 168 час. до 1 года:', ' масса тела ребёнка при рождении', params["weight"], ' грамм', '1' ])
    col_width = (82 * mm, 50 * mm, 12 * mm, 12 * mm, 6 * mm, )
    tbl_style = [
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

    opinion = gen_opinion(['каким по счету был ребенок у матери (считая умерших и не считая мертворождённых)',  params["child_count"], '', '2' ])
    col_width = (125 * mm, 6 * mm, 5 * mm, 6 * mm,)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    opinion = gen_opinion(['дата рождения матери', params["mother_born"], '', '3', 'возраст матери (полных лет)', params["mother_age"], '', '4'])
    col_width = (40 * mm, 15 * mm, 5 * mm, 6 * mm, 45 * mm, 15 * mm, 5 * mm, 6 * mm,)
    tbl_style = [
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

    opinion = gen_opinion(['фамилия матери', params["mother_family"], '', '5', ', имя', params["mother_name"], '', '6', ' , отчество (при наличии)', params["mother_patronimyc"], '', '7' ])
    col_width = (30 * mm, 25 * mm, 5 * mm, 6 * mm, 14 * mm, 20 * mm, 5 * mm, 6 * mm, 40 * mm, 25 * mm, 5 * mm, 6 * mm,)
    tbl_style = [
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
    opinion = gen_opinion(['15.*Семейное положение:', brak, '1', not_brak, '2', not_known, '3'  ])
    col_width = (38 * mm, 56 * mm, 6 * mm, 60 * mm, 6 * mm, 18 * mm, 6 * mm, )
    tbl_style = [
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
    opinion = gen_opinion(['16.* Образование:', high_prof, '1', not_high_prof, '2', middle_prof, '3', middle_common, '4'])
    col_width = (27 * mm, 40 * mm, 6 * mm, 30 * mm, 6 * mm, 41 * mm, 6 * mm,  26 * mm, 6 * mm, )
    tbl_style = [
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
    opinion = gen_opinion([common, '5', start, '6', before_school, '7', not_has_start, '8', not_known, '9'])
    col_width = (20 * mm, 6 * mm, 20 * mm, 6 * mm, 21 * mm, 6 * mm,  50 * mm, 6 * mm, 19 * mm, 6 * mm, )
    tbl_style = [
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
    opinion = gen_opinion(['17. * Занятость:', worked, '1', military, '2', pensioner, '3', student, '4'])

    col_width = (24 * mm, 18 * mm, 6 * mm, 80 * mm, 6 * mm, 24 * mm, 6 * mm,  20 * mm, 6 * mm, )
    tbl_style = [
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
    opinion = gen_opinion([not_work, '5', others, '6', not_known, '6'])
    col_width = (26 * mm, 6 * mm, 17 * mm, 6 * mm, 21 * mm, 6 * mm, )
    tbl_style = [
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
    opinion = [
        [
            Paragraph(f'{params["full_title"]}<br/>'
                      f'адрес места нахождения {params["org_address"]}<br/>'
                      f'Код по ОКПО {params["org_okpo"]}<br/>'
                      f'Номер и дата выдачи лицензии на осуществление медицинской деятельности: <br/>{params["org_license"]}<br/>', styleOrg),
            Paragraph('', styleOrg),
            Paragraph('Код формы по ОКУД _______<br/>Медицинская документация<br/>Учётная форма № 106/У<br/>Утверждена приказом Минздрава России <br/>от «15» апреля 2021 г. № 352н', styleOrg),
        ],
    ]
    col_width = (125 * mm, 5 * mm, 60 * mm,)
    tbl_style = [
        ('GRID', (0, 0), (0, 0), 0.75, colors.black),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (-1, -1), 1 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    return text


def bottom_colontitul(text, params):
    opinion = [[Paragraph(f'{params}', styleColontitul), ], ]
    col_width = (190 * mm)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 10 * mm),
        ('LEFTPADDING', (0, 0), (-1, -1), 1 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    return text


def back_size(text):
    opinion = [[Paragraph('Оборотная сторона', styleColontitulBold),],]
    col_width = (190 * mm,)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 166 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)
    return text


def why_death(text, params):
    opinion = [
        [
            Paragraph('10. Причины смерти:', styleT),
            Paragraph('Приблизительный период времени между началом патологического процесса и смертью', styleOrg),
            Paragraph('Коды по МКБ', styleOrg),
        ],
    ]
    col_width = (110 * mm, 40 * mm, 40 * mm,)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
        ('LEFTPADDING', (2, 0), (2, 0), 8 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    tbl = diagnos_tbl({"para": "I.", "item": "а)"})
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    tbl = about_diagnos("(болезнь или состояние, непосредственно приведшее к смерти)")
    text.append(Spacer(1, 0.1 * mm))
    text.append(tbl)

    tbl = diagnos_tbl({"para": "", "item": "б)"})
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    tbl = about_diagnos("(патологическое состояние, которое привело к возникновению причины, указанной в пункте «а»)")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    tbl = diagnos_tbl({"para": "", "item": "в)"})
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    tbl = about_diagnos("(первоначальная причина смерти указывается последней)")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    tbl = diagnos_tbl({"para": "", "item": "в)"})
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    tbl = about_diagnos("(внешняя причина при травмах и отравлениях)")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    opinion = [
        [
            Paragraph('II. Прочие важные состояния, способствовавшие смерти, но не связанные с болезнью или патологическим состоянием, приведшим к ней, включая употребление '
                      'алкоголя, наркотических средств, психотропных и других токсических веществ, содержание их в крови, а также операции (название, дата)', styleColontitul),
        ],
    ]
    col_width = (190 * mm,)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.1 * mm))
    text.append(tbl)

    count =1
    for k in range(count):
        tbl = diagnos_tbl({"para": "", "item": ""})
        text.append(Spacer(1, 0 * mm))
        text.append(tbl)

    days30, days7 = "смерть наступила - в течение 30 суток", ", из них в течение 7 суток"
    opinion = gen_opinion(['11.В случае смерти в результате ДТП:', days30, '1', days7, '2'])
    col_width = (55 * mm, 55 * mm, 6 * mm, 40 * mm, 6 * mm,)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),

    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    pregnant, process_birth = "В случае смерти беременной (независимо от срока и локализации)", ", в процессе родов"
    opinion = gen_opinion(['12. ', pregnant, '1', process_birth, '2'])
    col_width = (7 * mm, 92 * mm, 6 * mm, 30 * mm, 6 * mm,)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LEFTPADDING', (1, 0), (1, 0), -2 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),

    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    final_process_birth_42days, final_process_birth_365days  = "в течение 42 дней после окончания беременности, родов", ", кроме того в течение 43-365 дней после окончания беременности"
    opinion = gen_opinion([final_process_birth_42days, '3', final_process_birth_365days, '4'])
    col_width = (83 * mm, 6 * mm, 94 * mm, 6 * mm,)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 4 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),

    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    opinion = gen_opinion([f'{13}.Фамилия, имя, отчество (при наличии) врача (фельдшера, акушерки), заполнившего Медицинское свидетельство о смерти'])
    col_width = (190* mm,)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)
    return text


def diagnos_tbl(data):
    opinion = gen_opinion([data["para"], data["item"], '', '', '', '', '', '', '', ''])
    col_width = (7 * mm, 7 * mm, 96 * mm, 40 * mm, 5 * mm, 7 * mm, 7 * mm, 7 * mm, 6 * mm, 7 * mm,)
    tbl_style = [
        ('GRID', (5, 0), (5, 0), 0.75, colors.black),
        ('GRID', (6, 0), (6, 0), 0.75, colors.black),
        ('GRID', (7, 0), (7, 0), 0.75, colors.black),
        ('GRID', (9, 0), (9, 0), 0.75, colors.black),
        ('LINEBELOW', (0, 0), (3, 0), 0.75, colors.black),
        ('LINEBEFORE', (3, 0), (3, 0), 0.75, colors.black),
        ('LINEAFTER', (3, 0), (3, 0), 0.75, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (2, 0), (2, 0), 30 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style, 4 * mm)
    return tbl


def about_diagnos(data):
    styleMicro = deepcopy(styleT)
    styleMicro.fontSize = 6
    styleMicro.alignment = TA_CENTER
    opinion = [
        [
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph(f'{data}', styleMicro),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
        ],
    ]
    col_width = (7 * mm, 7 * mm, 96 * mm, 40 * mm, 5 * mm, 7 * mm, 7 * mm, 7 * mm, 6 * mm, 7 * mm,)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), -0.5 * mm),
        ('LINEBEFORE', (3, 0), (3, 0), 0.75, colors.black),
        ('LINEAFTER', (3, 0), (3, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    return tbl


def destination_person_passport(text, data):
    opinion = gen_opinion([data])
    tbl_style = [
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LINEBELOW', (0, 0), (-1, -1), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    col_width = (190 * mm)
    tbl = gen_table(opinion, col_width, tbl_style, 4 * mm)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)
    return text


def destination_person_snils(text, data):
    opinion = gen_opinion(['СНИЛС получателя (при наличии)', data])
    tbl_style = [
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    col_width = (50 * mm, 140 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)
    return text
