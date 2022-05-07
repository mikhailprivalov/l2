from utils.dates import normalize_date
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


def form_01(direction, doc, date_t, has_paraclinic, individual_birthday, number_poliklinika, logo_col_func, is_extract):
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "FreeSans"
    style.fontSize = 9
    style.alignment = TA_JUSTIFY
    style_ml = deepcopy(style)
    style_ml.leftIndent = 5 * mm
    styleBold = deepcopy(style)
    styleBold.fontName = "FreeSansBold"
    styleTable = deepcopy(style)
    styleTableMono = deepcopy(styleTable)
    styleTableMono.fontName = "Consolas"
    styleTableMono.fontSize = 10
    styleAb = deepcopy(styleTable)
    styleAb.fontSize = 7
    styleAb.leading = 7
    styleAb.spaceBefore = 0
    styleAb.spaceAfter = 0
    styleAb.leftIndent = 0
    styleAb.rightIndent = 0
    styleAb.alignment = TA_CENTER
    styleTableMonoBold = deepcopy(styleTable)
    styleTableMonoBold.fontName = "Consolas-Bold"
    styleTableSm = deepcopy(styleTable)
    styleTableSm.fontSize = 4

    data = [
        [Paragraph("Министерство здравоохранения Российской Федерации", styleTableMono)],
        [Paragraph("ОГАУЗ «Иркутская Медико-санитарная часть №2»", styleTableMono)],
        [Paragraph("г.Иркутск, ул.Байкальская, д.201", styleTableMono)],
        [Paragraph("Код ОГРН 1033801542576", styleTableMono)],
        [Paragraph("ВЫПИСКА ИЗ АМБУЛАТОРНОЙ КАРТЫ", styleTableMono)]
    ]
    t = Table(data, colWidths= 180 * mm)
    t.setStyle(
        TableStyle(
            [
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
    )

    return t
