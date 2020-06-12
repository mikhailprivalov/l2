from api.stationar.stationar_func import hosp_get_lab_iss, hosp_get_text
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os.path
from laboratory.settings import FONTS_FOLDER
from pyvirtualdisplay import Display
import imgkit
import sys
import directory.models as directory
import collections
from directions.models import ParaclinicResult, MicrobiologyResultCulture
import datetime
from appconf.manager import SettingManager
import simplejson as json


def lab_iss_to_pdf(data1):
    pdfmetrics.registerFont(TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSansBold', os.path.join(FONTS_FOLDER, 'OpenSans-Bold.ttf')))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "OpenSans"
    style.fontSize = 7.7
    style.leading = 10
    style.spaceAfter = 0.2 * mm
    style.alignment = TA_LEFT

    style_centre = deepcopy(style)
    style_centre.alignment = TA_CENTER
    style_centre.spaceAfter = 0.1 * mm

    style_ml = deepcopy(style)
    style_ml.leftIndent = 5 * mm

    styleBold = deepcopy(style)
    styleBold.fontSize = 8.5
    styleBold.fontName = "OpenSansBold"

    exclude_direction = data1['excluded']['dateDir']
    exclude_fraction = data1['excluded']['titles']
    exclude_direction_final = [i.split('#@#')[1] for i in exclude_direction]
    lab_iss = hosp_get_lab_iss(None, False, data1['directions'])
    # Таблица для операции
    prepare_fwb = []
    const_width_vertical = 168
    const_width_horizontal = 150
    for type_lab, v in lab_iss.items():
        for type_disposition, data in v.items():
            if type_disposition == 'vertical':
                if not data:
                    continue
                for i in data:
                    title_research = i['title_research']
                    title_fractions = i['title_fracions']
                    fractions_result = i['result']
                    # получить индексы ислючнных фракций
                    fractions_index_to_remove = []
                    for fraction in title_fractions:
                        maybe_exclude_fraction = f'{title_research}#@#{fraction}'
                        if maybe_exclude_fraction in exclude_fraction:
                            fractions_index_to_remove.append(title_fractions.index(fraction))

                    # удалить заголовки для исключенных фракци
                    title_fractions_final = [Paragraph(f, style_centre) for f in title_fractions if title_fractions.index(f) not in fractions_index_to_remove]
                    title_fractions_final.insert(0, Paragraph('Дата, напр.', style_centre))

                    # удалить результаты для исключенных фракций
                    result_values_for_research = [title_fractions_final]
                    values_final = None
                    for date_dir, val in fractions_result.items():
                        if date_dir in exclude_direction_final:
                            continue
                        values_final = []
                        for w in range(len(val)):
                            if w not in fractions_index_to_remove:
                                values_final.append(Paragraph('{}'.format(val[w]), style_centre))
                        values_final.insert(0, Paragraph(date_dir, style_centre))
                        result_values_for_research.append(values_final)

                    result_values_for_research.insert(0, [Paragraph(title_research, styleBold)])
                    if values_final:
                        row_count = len(values_final) - 1
                        tbl = gen_table(result_values_for_research, const_width_vertical, row_count, type_disposition)
                        # prepare_fwb.append(Spacer(1, 1 * mm))
                        prepare_fwb.append(tbl)
                        prepare_fwb.append(Spacer(1, 2 * mm))

            if type_disposition == 'horizontal':
                if not data:
                    continue
                for i in data:
                    title_fractions = i['title_fracions']
                    # получить индексы ислючнных фракций
                    fractions_index_to_remove = []
                    for fraction in title_fractions:
                        maybe_exclude_fraction = f'{type_lab}#@#{fraction}'
                        if maybe_exclude_fraction in exclude_fraction:
                            fractions_index_to_remove.append(title_fractions.index(fraction))

                    # удалить заголовки для исключенных фракциq
                    title_fractions_final = [f for f in title_fractions if title_fractions.index(f) not in fractions_index_to_remove]
                    fractions_result = i['result']
                    # установить кол-вл колонок результатов
                    result_values = [[Paragraph(key, style_centre)] for key in fractions_result.keys()]
                    result_values.insert(0, [Paragraph('Анализ / Дата,напр.', style_centre)])
                    result_values_for_fractions = [result_values]
                    for t in title_fractions:
                        final_result_template = []
                        if t not in title_fractions_final:
                            continue
                        index_result = title_fractions.index(t)
                        final_result_template.append(Paragraph(t, style_centre))
                        for val in fractions_result.values():
                            final_result_template.append(Paragraph(str(val[index_result]), style_centre))
                        result_values_for_fractions.append(final_result_template)

                    result_values_for_fractions.insert(0, [Paragraph(type_lab, styleBold)])
                    row_count = len(fractions_result)
                    tbl = gen_table(result_values_for_fractions, const_width_horizontal, row_count, type_disposition)
                    prepare_fwb.append(Spacer(1, 2 * mm))
                    prepare_fwb.append(tbl)
                    prepare_fwb.append(Spacer(1, 2 * mm))

    return prepare_fwb


def gen_table(data, const_width, row_count, type_disposition):
    if row_count == 0:
        return ' '
    width_one_column = const_width / row_count
    width_one_column = round(width_one_column, 1)
    row_widths = [width_one_column * mm] * row_count
    if type_disposition == 'horizontal':
        row_widths.insert(0, 30 * mm)
    else:
        row_widths.insert(0, 13 * mm)
    tbl = Table(data, repeatRows=2, colWidths=row_widths)
    tbl.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('GRID', (0, 1), (-1, -1), 1.0, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 1),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))

    return tbl


def text_iss_to_pdf(data, solid_text=False):
    pdfmetrics.registerFont(TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSansBold', os.path.join(FONTS_FOLDER, 'OpenSans-Bold.ttf')))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "OpenSans"
    style.fontSize = 9
    style.leading = 12
    style.spaceAfter = 0.5 * mm
    style.alignment = TA_LEFT
    style.spaceAfter = 0.2 * mm

    style_ml = deepcopy(style)
    style_ml.leftIndent = 5 * mm

    styleBold = deepcopy(style_ml)
    styleBold.fontName = "OpenSansBold"
    directions = [dirs for dirs in data['directions'] if dirs not in data['excluded']]
    text_iss = hosp_get_text(None, False, None, directions)
    prepare_fwb = []
    txt = ''
    for i in text_iss:
        title_research = i['title_research']
        if solid_text:
            txt += f'<font face=\"OpenSansBold\">{title_research}:</font> '
        prepare_fwb.append(Paragraph('{}'.format(title_research), styleBold))
        results = i['result']
        result_dates = ''
        for result in results:
            result_date = result['date'].split(' ')
            result_data = result['data']
            if not solid_text:
                result_dates = f'{result_dates} <font face=\"OpenSansBold\">{result_date[0]}-{result_date[1]}:</font>'
            else:
                result_dates = f'{result_dates} {result_date[0]}-{result_date[1]}:'
            group_titles = ''
            for group_fields in result_data:
                group_titles = ''
                group_title = group_fields['group_title']
                group_titles = f'{group_titles} {group_title}'
                fields = group_fields['fields']
                tmp_fields = ''
                for field in fields:
                    title_field = field['title_field']
                    value_field = field['value']
                    tmp_fields = f'{tmp_fields} {title_field}: {value_field}'
                group_titles = f'{group_titles} - {tmp_fields}'
            result_dates = f'{result_dates} {group_titles}'
        if solid_text:
            txt += f'{result_dates}; '
        prepare_fwb.append(Paragraph('{}'.format(result_dates), style_ml))
    if solid_text:
        prepare_fwb = txt

    return prepare_fwb


def html_to_pdf(file_tmp, r_value, pw, leftnone=False):
    linux = None
    if sys.platform == 'linux':
        linux = True
    size_css = f"""
    html, body {{
        width: {1000 if leftnone else 1300}px;
    }}
    """

    css = """
    html, body, div,
    h1, h2, h3, h4, h5, h6 {
        margin: 0;
        padding: 0;
        border: 0;
        font-family: sans-serif;
        font-size: 14px;
    }

    body {
        padding-left: 15px;
    }

    table {
        width: 100%;
        table-layout: fixed;
        border-collapse: collapse;
    }

    table, th, td {
        border: 1px solid black;
    }

    th, td {
        word-break: break-word;
        white-space: normal;
    }

    td {
        padding: 2px;
    }

    td p, li p {
        margin: 0;
    }

    h1 {
        font-size: 24px;
    }

    h2 {
        font-size: 20px;
    }

    h3 {
        font-size: 18px;
    }
                                        """
    if linux:
        display = Display(visible=0, size=(800, 600))
        display.start()
    imgkit.from_string(f"""
    <html>
        <head>
            <meta name="imgkit-format" content="png"/>
            <meta name="imgkit-quality" content="100"/>
            <meta name="imgkit-zoom" content="3"/>
            <meta charset="utf-8">
            <style>
                {size_css}
                {css}
            </style>
        </head>
        <body>
            {r_value}
        </body>
    </html>
                                        """, file_tmp)
    if linux:
        display.stop()

    i = Image(file_tmp)
    i.drawHeight = i.drawHeight * (pw / i.drawWidth)
    i.drawWidth = pw

    return i


def default_title_result_form(direction, doc, date_t, has_paraclinic, individual_birthday, number_poliklinika, logo_col):
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
        ["Номер:", str(direction.pk)],
        ["Пациент:", Paragraph(direction.client.individual.fio(), styleTableMonoBold)],
        ["Пол:", direction.client.individual.sex],
        ["Возраст:", "{} {}".format(direction.client.individual.age_s(direction=direction), individual_birthday)],
    ]
    data += [["Дата забора:", date_t]] if not has_paraclinic else [["Диагноз:", direction.diagnos]]
    data += [[Paragraph('&nbsp;', styleTableSm), Paragraph('&nbsp;', styleTableSm)],
             ["РМИС ID:" if direction.client.base.is_rmis else "№ карты:",
              direction.client.number_with_type() + (
                  " - архив" if direction.client.is_archive else "") + number_poliklinika]]
    if not direction.imported_from_rmis:
        data.append(
            ["Врач:", "<font>%s<br/>%s</font>" % (direction.doc.get_fio(), direction.doc.podrazdeleniye.title)])
    elif direction.imported_org:
        data.append(["<font>Направляющая<br/>организация:</font>", direction.imported_org.title])

    data = [[Paragraph(y, styleTableMono) if isinstance(y, str) else y for y in data[xi]] + [logo_col[xi]] for xi in range(len(data))]

    t = Table(data, colWidths=[doc.width * 0.145, doc.width - 158 - doc.width * 0.145, 158])
    t.setStyle(TableStyle([
        ('ALIGN', (-1, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('VALIGN', (-1, 0), (-1, 0), 'BOTTOM'),
        ('VALIGN', (-1, 5), (-1, 5), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (-1, 0), (-1, -1), 0),
        ('TOPPADDING', (-1, 0), (-1, -1), 0),
        ('TOPPADDING', (-1, 5), (-1, 5), 3),
        ('TOPPADDING', (0, 5), (1, 5), 0),
        ('TOPPADDING', (0, 6), (1, 6), -6),
        ('BOTTOMPADDING', (0, 5), (1, 5), 0),
        ('LEFTPADDING', (0, 5), (1, 5), 0),
        ('RIGHTPADDING', (0, 5), (1, 5), 0),
        ('SPAN', (-1, 0), (-1, 4)),
        ('SPAN', (-1, 5), (-1, -1))

    ]))

    return t


def structure_data_for_result(iss, fwb, doc, leftnone):
    pw = doc.width
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "FreeSans"
    style.fontSize = 9
    style.alignment = TA_JUSTIFY
    style_ml = deepcopy(style)
    style_ml.leftIndent = 5 * mm
    styleBold = deepcopy(style)
    styleBold.fontName = "FreeSansBold"

    sick_result = None
    for group in directory.ParaclinicInputGroups.objects.filter(research=iss.research).order_by("order"):
        sick_title = True if group.title == "Сведения ЛН" else False
        if sick_title:
            sick_result = collections.OrderedDict()
        results = ParaclinicResult.objects.filter(issledovaniye=iss, field__group=group).exclude(value="").order_by("field__order")
        group_title = False
        if results.exists():
            fwb.append(Spacer(1, 1 * mm))
            if group.show_title and group.show_title != "":
                fwb.append(Paragraph(group.title.replace('<', '&lt;').replace('>', '&gt;'), styleBold))
                fwb.append(Spacer(1, 0.25 * mm))
                group_title = True
            for r in results:
                field_type = r.get_field_type()
                if field_type == 15:
                    date_now1 = datetime.datetime.strftime(datetime.datetime.now(), "%y%m%d%H%M%S")
                    dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
                    file_tmp = os.path.join(dir_param, f'field_{date_now1}_{r.pk}.png')
                    img = html_to_pdf(file_tmp, r.value, pw, leftnone)
                    fwb.append(img)
                    os.remove(file_tmp)
                else:
                    v = r.value.replace('<', '&lt;').replace('>', '&gt;').replace("\n", "<br/>")
                    v = v.replace('&lt;sub&gt;', '<sub>')
                    v = v.replace('&lt;/sub&gt;', '</sub>')
                    v = v.replace('&lt;sup&gt;', '<sup>')
                    v = v.replace('&lt;/sup&gt;', '</sup>')
                    if field_type == 16:
                        v = json.loads(v)
                        if not v['directions']:
                            continue
                        aggr_lab = lab_iss_to_pdf(v)
                        if not aggr_lab:
                            continue
                        fwb.append(Spacer(1, 2 * mm))
                        fwb.append(
                            Paragraph("<font face=\"FreeSansBold\">{}</font>".format(r.field.get_title(force_type=field_type).replace('<', '&lt;').replace('>', '&gt;')),
                                      style))
                        fwb.extend(aggr_lab)
                        continue
                    if field_type == 17:
                        if v:
                            v = json.loads(v)
                            if not v['directions']:
                                continue
                            aggr_text = text_iss_to_pdf(v)
                            if not aggr_text:
                                continue
                            fwb.append(
                                Paragraph("<font face=\"FreeSansBold\">{}</font>".format(r.field.get_title(force_type=field_type).replace('<', '&lt;').replace('>', '&gt;')),
                                          style))
                            fwb.extend(aggr_text)
                            continue
                    if field_type == 1:
                        vv = v.split('-')
                        if len(vv) == 3:
                            v = "{}.{}.{}".format(vv[2], vv[1], vv[0])
                    if field_type in [11, 13]:
                        v = '<font face="FreeSans" size="8">{}</font>'.format(v.replace("&lt;br/&gt;", " "))
                    if r.field.get_title(force_type=field_type) != "":
                        fwb.append(Paragraph(
                            "<font face=\"FreeSansBold\">{}:</font> {}".format(r.field.get_title(force_type=field_type).replace('<', '&lt;').replace('>', '&gt;'), v),
                            style_ml if group_title else style))
                    else:
                        fwb.append(Paragraph(v, style))
                    if sick_title:
                        sick_result[r.field.get_title(force_type=field_type)] = v

    return fwb


def plaint_tex_for_result(iss, fwb, doc, leftnone, protocol_plain_text):
    pw = doc.width
    sick_result = None
    txt = ""

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "FreeSans"
    style.fontSize = 9
    style.alignment = TA_JUSTIFY
    style_ml = deepcopy(style)
    style_ml.leftIndent = 5 * mm
    styleBold = deepcopy(style)
    styleBold.fontName = "FreeSansBold"
    for group in directory.ParaclinicInputGroups.objects.filter(research=iss.research).order_by("order"):
        sick_title = group.title == "Сведения ЛН"
        if sick_title:
            sick_result = collections.OrderedDict()
        results = ParaclinicResult.objects.filter(issledovaniye=iss, field__group=group).exclude(value="").order_by("field__order")
        if results.exists():
            if group.show_title and group.title != "":
                txt += "<font face=\"FreeSansBold\">{}:</font>&nbsp;".format(group.title.replace('<', '&lt;').replace('>', '&gt;'))
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
                if field_type == 17:
                    if v:
                        v = json.loads(v)
                        if not v['directions']:
                            continue
                        v = text_iss_to_pdf(v, protocol_plain_text)
                if r.field.get_title(force_type=field_type) != "":
                    vals.append("{}:&nbsp;{}".format(r.field.get_title().replace('<', '&lt;').replace('>', '&gt;'), v))
                else:
                    vals.append(v)
                if sick_title:
                    sick_result[r.field.get_title(force_type=field_type)] = v

            txt += "; ".join(vals)
            txt = txt.strip()
            if len(txt) > 0 and txt.strip()[-1] != ".":
                txt += ". "
            elif len(txt) > 0:
                txt += " "
    fwb.append(Paragraph(txt, style))
    return fwb


def microbiology_result(iss, fwb, doc):
    pw = doc.width
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "FreeSans"
    style.fontSize = 9
    style.alignment = TA_JUSTIFY
    style_ml = deepcopy(style)
    style_ml.leftIndent = 5 * mm
    styleBold = deepcopy(style)
    styleBold.fontName = "FreeSansBold"

    q = iss.culture_results.select_related('culture').prefetch_related('culture_antibiotic').all()
    tw = pw * 0.98
    culture: MicrobiologyResultCulture
    for culture in q:
        fwb.append(Spacer(1, 3 * mm))
        fwb.append(Paragraph("<font face=\"FreeSansBold\">Культура:</font> " + culture.culture.get_full_title(), style))
        if culture.koe:
            fwb.append(Paragraph("<font face=\"FreeSansBold\">КОЕ:</font> " + culture.koe, style))

        data = [
            [Paragraph(x, styleBold) for x in ['Антибиотик', 'Диаметр', 'Чувствительность']]
        ]

        for anti in culture.culture_antibiotic.all():
            data.append([Paragraph(x, style) for x in [
                anti.antibiotic.title,
                anti.dia,
                anti.sensitivity,
            ]])

        cw = [int(tw * 0.4), int(tw * 0.3)]
        cw = cw + [tw - sum(cw)]

        t = Table(data, colWidths=cw)
        style_t = TableStyle([('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                              ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                              ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                              ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                              ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                              ('LEFTPADDING', (0, 0), (-1, -1), 4),
                              ('TOPPADDING', (0, 0), (-1, -1), 1),
                              ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                              ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                              ])
        style_t.add('BOTTOMPADDING', (0, 0), (-1, 0), 1)
        style_t.add('TOPPADDING', (0, 0), (-1, 0), 0)

        t.setStyle(style_t)

        fwb.append(Spacer(1, 2 * mm))
        fwb.append(t)
        fwb.append(Paragraph("<para align='right'><font size='7'>S – чувствителен; R – резистентен; I – промежуточная чувствительность</font></para>", style))
        fwb.append(Spacer(1, 2 * mm))

    if iss.microbiology_conclusion:
        fwb.append(Spacer(1, 3 * mm))
        fwb.append(Paragraph('Заключение', styleBold))
        fwb.append(Paragraph(iss.microbiology_conclusion, style))

    return fwb



