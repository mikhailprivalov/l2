from api.stationar.stationar_func import hosp_get_lab_iss, hosp_get_text_iss, hosp_get_text
import json
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Frame, KeepInFrame
from reportlab.platypus import PageBreak, Indenter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import black
import os.path
from laboratory.settings import FONTS_FOLDER

# field_type
# (16, 'Agg lab'),
# (17, 'Agg desc')
# {
# directions: [],
# exclude: {
#     titles: [],
#     dirDate: [],
# }
# }

def lab_iss_to_pdf(data):

    pdfmetrics.registerFont(
        TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))
    pdfmetrics.registerFont(
        TTFont('Champ', os.path.join(FONTS_FOLDER, 'Champ.ttf')))
    pdfmetrics.registerFont(
        TTFont('ChampB', os.path.join(FONTS_FOLDER, 'Calibri.ttf')))
    pdfmetrics.registerFont(
        TTFont('CalibriBold', os.path.join(FONTS_FOLDER, 'calibrib.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansBold', os.path.join(FONTS_FOLDER, 'OpenSans-Bold.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansItalic', os.path.join(FONTS_FOLDER, 'OpenSans-Italic.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansBoldItalic', os.path.join(FONTS_FOLDER, 'OpenSans', 'OpenSans-BoldItalic.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansLight', os.path.join(FONTS_FOLDER, 'OpenSans', 'OpenSans-Light.ttf')))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "OpenSans"
    style.fontSize = 9
    style.leading = 5
    style.spaceAfter = 0.5 * mm
    style.alignment = TA_LEFT
    style.spaceAfter = 0.2 * mm

    data = json.loads(data)
    exclude_direction = data['excluded']['dateDir']
    exclude_fraction = data['excluded']['titles']
    print("exclude_direction: ", exclude_direction)
    print("exclude_fraction: ", exclude_fraction)
    lab_iss = hosp_get_lab_iss(None, False, data['directions'])
    # Таблица для операции
    prepare_fwb = []
    for type_lab, v in lab_iss.items():
        print(type_lab)
        print(v)
        for type_disposition, data in v.items():
            if type_disposition == 'vertical':
                if not data:
                    continue
                for i in data:
                    title_research = i['title_research']
                    print('reser', title_research)
                    prepare_fwb.append(Paragraph('{}'.format(title_research), style))
                    prepare_fwb.append(Spacer(1, 8 * mm))
                    title_fractions = i['title_fracions']
                    for fraction in title_fractions:
                        maybe_exclude_fraction = f'{title_research}#@#{fraction}'
                        if maybe_exclude_fraction in exclude_fraction:
                            print("Exclude: ", maybe_exclude_fraction)

            if type_disposition == 'horizontal':
                if not data:
                    continue
                for i in data:
                    title_fractions = i['title_fracions']
                    result_fraction = i['result']
                    for fraction in title_fractions:
                        print('frac', fraction)
                        prepare_fwb.append(Paragraph('{}'.format(fraction), style))
                        prepare_fwb.append(Spacer(1, 8 * mm))
                        maybe_exclude_fraction = f'{title_research}#@#{fraction}'
                        if maybe_exclude_fraction in exclude_fraction:
                            print("Exclude: ", maybe_exclude_fraction)

                    for dir_date, value in result_fraction.items():
                        maybe_exclude_dir = f'{type_lab}#@#{dir_date}'
                        if maybe_exclude_dir in exclude_direction:
                            print("Exclude: ", maybe_exclude_dir)
    return prepare_fwb


def text_iss_to_pdf(data):
    pdfmetrics.registerFont(
        TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))
    pdfmetrics.registerFont(
        TTFont('Champ', os.path.join(FONTS_FOLDER, 'Champ.ttf')))
    pdfmetrics.registerFont(
        TTFont('ChampB', os.path.join(FONTS_FOLDER, 'Calibri.ttf')))
    pdfmetrics.registerFont(
        TTFont('CalibriBold', os.path.join(FONTS_FOLDER, 'calibrib.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansBold', os.path.join(FONTS_FOLDER, 'OpenSans-Bold.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansItalic', os.path.join(FONTS_FOLDER, 'OpenSans-Italic.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansBoldItalic', os.path.join(FONTS_FOLDER, 'OpenSans', 'OpenSans-BoldItalic.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansLight', os.path.join(FONTS_FOLDER, 'OpenSans', 'OpenSans-Light.ttf')))

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

    styleBold = deepcopy(style)
    styleBold.fontName = "OpenSansBold"

    data = json.loads(data)
    text_iss = hosp_get_text(None, False, None, data)
    prepare_fwb = []
    title_researches = ''
    for i in text_iss:
        title_research = i['title_research']
        prepare_fwb.append(Paragraph('{}'.format(title_research), styleBold))
        results = i['result']
        result_dates = ''
        for result in results:
            result_date = result['date'].split(' ')
            result_data = result['data']
            result_dates = f'{result_dates} <font face=\"OpenSansBold\">{result_date[0]}-{result_date[1]}:</font>'
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
        prepare_fwb.append(Paragraph('{}'.format(result_dates), style_ml))

    return prepare_fwb
