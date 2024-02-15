from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_JUSTIFY
import directory.models as directory
from appconf.manager import SettingManager
from directions.models import ParaclinicResult
from results.prepare_data import html_to_pdf, text_iss_to_pdf, text_to_bold, lab_iss_to_pdf, previous_laboratory_result, previous_doc_refferal_result
from utils.dates import normalize_date
from api.stationar.stationar_func import hosp_get_curent_hosp_dir
import datetime
import os.path
import simplejson as json


def form_01(direction, iss, fwb, doc, leftnone, user=None, **kwargs):
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
    txt = ""
    pw = doc.width
    append_table = False
    for group in directory.ParaclinicInputGroups.objects.filter(research=iss.research).order_by("order"):
        i += 1
        results = ParaclinicResult.objects.filter(issledovaniye=iss, field__group=group).exclude(value="").order_by("field__order")
        if i <= 3:
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
                    v = text_to_bold(v)
                    column_result = column_result + "<font face=\"FreeSans\">{}:</font>{}".format(r.field.get_title(force_type=field_type).replace('<', '&lt;').replace('>', '&gt;'), v) + ";"
                    if i == 1:
                        column_result += "<br/>"
                column_data.append(Paragraph(column_result, style))
        if i > 3:
            if not append_table:
                column_data += [''] * (3 - len(column_data))
                opinion = [title_opinion, column_data]
                tbl = Table(opinion, colWidths=(33 * mm, 100 * mm, 50 * mm))
                tbl.setStyle(
                    TableStyle(
                        [
                            ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 5 * mm),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ]
                    )
                )
                hosp_dir = hosp_get_curent_hosp_dir(iss.pk)
                fwb.append(Spacer(1, 2 * mm))
                fwb.append(Paragraph('Пациент: {}. (№:{})'.format(patient_fio, hosp_dir), style))
                fwb.append(Paragraph('Дата-время осмотра: {} в {}'.format(date, time), style))
                fwb.append(Spacer(1, 0.5 * mm))
                fwb.append(tbl)
                append_table = True

            if results.exists():
                if group.show_title and group.title != "":
                    txt += "<font face=\"FreeSansBold\">{}:</font>&nbsp;".format(group.title.replace('<', '&lt;').replace('>', '&gt;'))
                    txt += "<br/>"
                    fwb.append(Spacer(1, 2 * mm))
                    fwb.append(Paragraph(txt, style))
                    txt = ''
                vals = []
                for r in results:
                    field_type = r.get_field_type()
                    v = r.value.replace('<', '&lt;').replace('>', '&gt;').replace("\n", "<br/>")
                    v = v.replace('&lt;sub&gt;', '<sub>')
                    v = v.replace('&lt;/sub&gt;', '</sub>')
                    v = v.replace('&lt;sup&gt;', '<sup>')
                    v = v.replace('&lt;/sup&gt;', '</sup>')
                    if field_type == 1:
                        vv = v.split('-')
                        if len(vv) == 3:
                            v = "{}.{}.{}".format(vv[2], vv[1], vv[0])
                    if field_type in [11, 13]:
                        v = '<font face="FreeSans" size="8">{}</font>'.format(v.replace("&lt;br/&gt;", " "))
                    if field_type == 15:
                        txt += "; ".join(vals)
                        fwb.append(Paragraph(txt, style))
                        txt = ''
                        vals = []
                        date_now1 = datetime.datetime.strftime(datetime.datetime.now(), "%y%m%d%H%M%S")
                        dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
                        file_tmp = os.path.join(dir_param, f'field_{date_now1}_{r.pk}.png')
                        fwb.append(Spacer(1, 2 * mm))
                        img = html_to_pdf(file_tmp, r.value, pw, leftnone)
                        fwb.append(img)
                        os.remove(file_tmp)
                        continue
                    if field_type == 16:
                        v = json.loads(v)
                        if not v['directions']:
                            continue
                        txt += "; ".join(vals)
                        fwb.append(Paragraph(txt, style))
                        txt = ''
                        vals = []
                        fwb.append(Spacer(1, 2 * mm))
                        fwb.append(Paragraph(r.field.get_title(), styleBold))
                        aggr_lab = lab_iss_to_pdf(v)
                        fwb.extend(aggr_lab)
                        continue
                    if field_type == 24:
                        previous_laboratory = previous_laboratory_result(v)
                        if not previous_laboratory:
                            continue
                        fwb.append(Spacer(1, 2 * mm))
                        fwb.append(Paragraph("<font face=\"FreeSansBold\">{}</font>".format(r.field.get_title(force_type=field_type).replace('<', '&lt;').replace('>', '&gt;')), style))
                        fwb.extend(previous_laboratory)
                        continue
                    if field_type in [26, 25]:
                        if v:
                            fwb.append(Spacer(1, 2 * mm))
                            fwb.append(Paragraph("<font face=\"FreeSansBold\">{}</font>".format(r.field.get_title(force_type=field_type).replace('<', '&lt;').replace('>', '&gt;')), style))
                            fwb = previous_doc_refferal_result(v, fwb)
                            continue
                    if field_type == 17:
                        if v:
                            v = json.loads(v)
                            if not v['directions']:
                                continue
                            v = text_iss_to_pdf(v, True)
                    v = text_to_bold(v)
                    if r.field.get_title(force_type=field_type) != "":
                        vals.append("{}:&nbsp;{}".format(r.field.get_title().replace('<', '&lt;').replace('>', '&gt;'), v))
                    else:
                        vals.append(v)

                    txt += "; ".join(vals)
                    txt = txt.strip()
                    if len(txt) > 0 and txt.strip()[-1] != ".":
                        txt += ". "
                    elif len(txt) > 0:
                        txt += " "
                fwb.append(Paragraph(txt, style))
                txt = ''

    fwb.append(Spacer(1, 0.5 * mm))
    if i <= 3:
        column_data += [''] * (3 - len(column_data))

        opinion = [title_opinion, column_data]
        tbl = Table(opinion, colWidths=(33 * mm, 100 * mm, 50 * mm))

        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5 * mm),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]
            )
        )

        hosp_dir = hosp_get_curent_hosp_dir(iss.pk)

        fwb.append(Spacer(1, 2 * mm))
        fwb.append(Paragraph('Пациент: {}. (№:{})'.format(patient_fio, hosp_dir), style))
        fwb.append(Paragraph('Дата-время осмотра: {} в {}'.format(date, time), style))
        fwb.append(Spacer(1, 0.5 * mm))
        fwb.append(tbl)
        fwb.append(Spacer(1, 0.5 * mm))

    return fwb
