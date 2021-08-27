from reportlab.lib.colors import HexColor

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
from results.prepare_data import text_to_bold
import os.path
from laboratory.settings import FONTS_FOLDER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .flowable import FrameDataUniversal
from directions.models import Issledovaniya


def form_01(direction, iss: Issledovaniya, fwb, doc, leftnone, user=None):
    # Мед. св-во о смерти 106/у
    template = add_template(iss, direction, 0)
    fwb.extend(template)
    # template = add_template(iss, direction, 107)
    # fwb.extend(template)

    return fwb


def add_template(iss: Issledovaniya, direction, offset=0):
    # Мед. св-во о смерти 106/у
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 9
    style.alignment = TA_JUSTIFY

    style_ml = deepcopy(style)
    style_ml.leftIndent = 5 * mm
    style_ml.spaceAfter = 0.5 * mm

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

    text = []
    text.append(Paragraph("КОРЕШОК МЕДИЦИНСКОГО СВИДЕТЕЛЬСТВА О СМЕРТИ", styleCentreBold))
    text.append(Paragraph("К УЧЕТНОЙ ФОРМЕ № 106/У", styleCentreBold))
    serial = "2XX"
    number = "12345678"
    text.append(Spacer(1, 1 * mm))
    text.append(Paragraph(f"СЕРИЯ {serial} No {number}", styleCentreBold))
    date_issue = "20.08.2021"
    text.append(Paragraph(f"Дата выдачи {date_issue}", styleCentreBold))
    final, preparatory, instead_preparatory, instead_final = "окончательного", "предварительного", "взамен предварительного", "взамен окончательного"
    text.append(Paragraph(f"({final}, {preparatory}, {instead_preparatory}, {instead_final}) (подчеркнуть)", styleCentre))
    fio = "Ивано Иван Иванович"
    text.append(Spacer(1, 1 * mm))
    text.append(Paragraph(f"1.Фамилия, имя, отчество (при наличии) умершего(ей) <u>{fio}</u>", style))

    # Пол
    opinion = [
        [
            Paragraph(f'2.Пол:', styleT),
            Paragraph(f'<u>мужской</u>', styleT),
            Paragraph('1', styleT),
            Paragraph(', женский', styleT),
            Paragraph('2', styleT),
        ],
    ]

    tbl = Table(opinion, colWidths=(12 * mm, 18 * mm, 6 * mm, 19 * mm, 6 * mm), rowHeights=(4 * mm), hAlign='LEFT')
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
                ('GRID', (2, 0), (2, 0), 0.75, colors.black),
                ('GRID', (-1, -1), (-1, -1), 0.75, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
            ]
        )
    )
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    # Дата рождения
    born_day = "01"
    born_month = "01"
    born_year = "1970"

    death_day = "01"
    death_month = "01"
    death_year = "1970"
    death_hour = "23"
    death_min = "00"

    opinion = [
        [
            Paragraph(f'3.Дата рождения:', styleT),
            Paragraph(f'число', styleT),
            Paragraph(f'{born_day}', styleT),
            Paragraph('месяц', styleT),
            Paragraph(f'{born_month}', styleT),
            Paragraph('год', styleT),
            Paragraph(f'{born_year}', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
        ],
        [
            Paragraph(f'4.Дата смерти:', styleT),
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

    tbl = Table(opinion, colWidths=(30 * mm, 14 * mm, 8 * mm, 14 * mm, 8 * mm, 12 * mm, 12 * mm, 11 * mm, 8 * mm, 12 * mm, 8 * mm), rowHeights=(5 * mm), hAlign='LEFT')
    tbl.setStyle(
        TableStyle(
            [
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
                ('LINEBELOW', (10, 1), (10, 1), 0.75, colors.black),
            ]
        )
    )

    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    region = "Область Иркутская"
    opinion = [
        [
            Paragraph('5. Регистрация по месту жительства (пребывания) умершего(ей): субъект Российской Федерации:', styleT),
            Paragraph(f'{region}', styleT),
        ],
    ]

    tbl = Table(opinion, colWidths=(150 * mm, 40 * mm), rowHeights=(5 * mm), hAlign='LEFT')
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
                ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
                ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
            ]
        )
    )

    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    region_town = ""
    city = "Иркутск"
    opinion = [
        [
            Paragraph('район', styleT),
            Paragraph(f'{region_town}', styleT),
            Paragraph('город', styleT),
            Paragraph(f'{city}', styleT),
        ],
    ]

    tbl = Table(
        opinion,
        colWidths=(
            17 * mm,
            77 * mm,
            16 * mm,
            80 * mm,
        ),
        hAlign='LEFT',
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
                ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
                ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
                ('LINEBELOW', (3, 0), (3, 0), 0.75, colors.black),
            ]
        )
    )

    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    localcity = ""
    street = "Иркутск"
    opinion = [
        [
            Paragraph('населенный пункт', styleT),
            Paragraph(f'{localcity}', styleT),
            Paragraph('улица', styleT),
            Paragraph(f'{street}', styleT),
        ],
    ]

    tbl = Table(
        opinion,
        colWidths=(
            37 * mm,
            67 * mm,
            16 * mm,
            70 * mm,
        ),
        hAlign='LEFT',
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
                ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
                ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
                ('LINEBELOW', (3, 0), (3, 0), 0.75, colors.black),
            ]
        )
    )

    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    localcity = ""
    street = "Иркутск"
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

    tbl = Table(opinion, colWidths=(14 * mm, 15 * mm, 12 * mm, 12 * mm, 14* mm, 15 * mm, 12 * mm, 15 * mm, 14 * mm, 15 * mm,), hAlign='LEFT',)
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
                ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
                ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
                ('LINEBELOW', (3, 0), (3, 0), 0.75, colors.black),
                ('LINEBELOW', (5, 0), (5, 0), 0.75, colors.black),
                ('LINEBELOW', (7, 0), (7, 0), 0.75, colors.black),
                ('LINEBELOW', (9, 0), (9, 0), 0.75, colors.black),
            ]
        )
    )

    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    thick_dashed_for_symbol = 0.7
    step_round_dash = (0.03 * mm, 1 * mm)
    round_dash = 'round'

    type_dash = 'round'
    step_dash = step_round_dash
    # color_dash_for_symbol = HexColor('#5b5e5c')
    color_dash_for_symbol = HexColor('#b3b3b3')

    objs = []
    space_symbol = '&nbsp;'

    opinion = [
        [
            Paragraph(' ', ),
            Paragraph('линия отреза', style),
            Paragraph('', style),
        ],
    ]
    tbl = Table(opinion, hAlign='LEFT', colWidths=(82 * mm, 25 * mm, 83 * mm))
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LINEABOVE', (0, 0), (0, 0), 1.5, colors.black, 'round', step_round_dash),
                ('LINEABOVE', (2, 0), (2, 0), 1.5, colors.black, 'round', step_round_dash),
                ('TOPPADDING', (1, 0), (1, 0), -1.7 * mm),

            ]
        )
    )
    text.append(Spacer(1, 35 * mm))
    text.append(tbl)




    opinion = [
        [
            Paragraph(f'<font size=10>{hospital_name}<br/>Адрес: {hospital_address}<br/>ОГРН: {hospital_kod_ogrn} <br/> </font>', styleT),
            Paragraph('<font size=9 >Медицинская документация <br/> Учетная форма № 014/1-у<br/>Утверждена приказом Минздрава России<br/>от 24 марта 2016г. № 179н</font>', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [100 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (1, 0), (-1, -1), 35 * mm),
                ('LEFTPADDING', (0, 0), (0, -1), 15 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    # text.append(tbl)

    obj = []
    obj.append(FrameDataUniversal(0, -60, 190, 100, text=text))

    return obj
