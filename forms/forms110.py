from reportlab.lib.pagesizes import A4
from forms.sql_func import get_extra_notification_data_for_pdf
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_JUSTIFY
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
    style.fontSize = 10
    style.alignment = TA_JUSTIFY

    directions = [x for x in json.loads(request_data["pk"]) if x is not None]

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=25 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=6 * mm, allowSplitting=1, title="Форма {}".format("Эпид. извещение"))
    result = get_extra_notification_data_for_pdf(directions)

    data_result = {}
    for i in result:
        if data_result.get(i.slave_dir) is None:
            data_result[i.slave_dir] = {
                'master_dir': i.master_dir,
                'epid_title': i.epid_title,
                'epid_value': i.epid_value,
                'master_field_results': [{'master_field_title': i.master_field_title, 'master_value': i.master_value}],
            }
        else:
            temp_data = data_result.get(i.slave_dir)
            temp_data['master_field_results'].append({'master_field_title': i.master_field_title, 'master_value': i.master_value})

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
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5 * mm),
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
