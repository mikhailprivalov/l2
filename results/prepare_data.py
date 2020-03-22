from api.stationar.stationar_func import hosp_get_lab_iss, hosp_get_text
import json
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os.path
from laboratory.settings import FONTS_FOLDER
from pyvirtualdisplay import Display
import imgkit
import sys


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
