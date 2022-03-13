from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_JUSTIFY

from forms.views import get_epid_data
from laboratory.settings import FONTS_FOLDER
import os.path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import simplejson as json
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak


def form_01(request_data):
    # Результат Экстренные извещения
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 9
    style.alignment = TA_JUSTIFY

    directions = [x for x in json.loads(request_data["pk"]) if x is not None]

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=25 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=6 * mm, allowSplitting=1, title="Форма {}".format("Эпид. извещение"))

    data_result = get_epid_data(directions, 1)
    objs = []
    for k, v in data_result.items():
        opinion = [
            [Paragraph('Эпид Номер', style), Paragraph(v.get('epid_value'), style)],
        ]

        for i in v.get('master_field_results'):
            opinion.append(
                [Paragraph(i.get('master_field_title'), style), Paragraph(i.get('master_value'), style)],
            )

        tbl = Table(opinion, colWidths=(60 * mm, 120 * mm))

        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0.1 * mm),
                ]
            )
        )
        objs.append(Spacer(1, 3 * mm))
        objs.append(tbl)
        objs.append(PageBreak())

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf
