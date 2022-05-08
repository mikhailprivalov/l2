from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os.path
from laboratory.settings import FONTS_FOLDER

from directions.models import Issledovaniya
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER


def form_01(iss: Issledovaniya):
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    styleSheet = getSampleStyleSheet()

    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifBold"
    style.fontSize = 12
    style.leading = 8
    style.spaceAfter = 0 * mm
    style.alignment = TA_CENTER

    hospital = iss.doc_confirmation.hospital
    hospital_short_title = hospital.safe_short_title
    hospital_address = hospital.safe_address
    hospital_ogrn = hospital.safe_ogrn

    data = [
        [Paragraph("Министерство здравоохранения Российской Федерации", style)],
        [Paragraph(hospital_short_title, style)],
        [Paragraph(hospital_address, style)],
        [Paragraph(f"Код ОГРН {hospital_ogrn}", style)],
        [Spacer(1, 1 * mm)],
        [Paragraph("<u>ВЫПИСКА ИЗ АМБУЛАТОРНОЙ КАРТЫ</u>", style)]
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
