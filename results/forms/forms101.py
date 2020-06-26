from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_JUSTIFY
import directory.models as directory
from directions.models import ParaclinicResult
from utils.dates import normalize_date
from api.stationar.stationar_func import hosp_get_curent_hosp_dir


def form_01(direction, iss, fwb, doc, leftnone):
    # Форма для печати дневников в 3 колонки
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "FreeSans"
    style.fontSize = 9
    style.alignment = TA_JUSTIFY
    style_ml = deepcopy(style)
    style_ml.leftIndent = 5 * mm
    styleBold = deepcopy(style)
    styleBold.fontName = "FreeSansBold"

    date, time = '', ''
    patient_fio = direction.client.individual.fio()

    i = 0
    title_opinion = []
    column_data = []
    for group in directory.ParaclinicInputGroups.objects.filter(research=iss.research).order_by("order"):
        i += 1
        if i > 3:
            break
        results = ParaclinicResult.objects.filter(issledovaniye=iss, field__group=group).exclude(value="").order_by("field__order")
        if results.exists():
            fwb.append(Spacer(1, 1 * mm))
            title_opinion.append(Paragraph(group.title.replace('<', '&lt;').replace('>', '&gt;'), styleBold))
            column_result = ''
            for r in results:
                field_type = r.get_field_type()
                if field_type == 1 and r.field.get_title(force_type=field_type) == 'Дата осмотра':
                    date = normalize_date(r.value)
                    continue
                if field_type == 20 and r.field.get_title(force_type=field_type) == 'Время осмотра':
                    time = r.value
                    continue
                if field_type == 21:
                    continue
                v = r.value.replace('<', '&lt;').replace('>', '&gt;').replace("\n", "<br/>")

                column_result = column_result + "<font face=\"FreeSans\">{}:</font>{}".format(r.field.get_title(force_type=field_type).replace('<', '&lt;').replace('>', '&gt;'), v) + ";"
                if i == 1:
                    column_result += "<br/>"

            column_data.append(Paragraph(column_result, style))
    column_data += [''] * (3 - len(column_data))

    opinion = [
        title_opinion,
        column_data
    ]
    tbl = Table(opinion, colWidths=(33 * mm, 100 * mm, 50 * mm))

    tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5 * mm),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    hosp_dir = hosp_get_curent_hosp_dir(iss.pk)

    fwb.append(Spacer(1, 2 * mm))
    fwb.append(Paragraph('Пациент: {}. (№:{})'.format(patient_fio, hosp_dir), style))
    fwb.append(Paragraph('Дата-время осмотра: {} в {}'.format(date, time), style))
    fwb.append(Spacer(1, 0.5 * mm))
    fwb.append(tbl)

    return fwb
