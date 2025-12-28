from reportlab.platypus import PageBreak
import os.path
import simplejson as json
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from directions.models import Issledovaniya, Napravleniya
from laboratory.settings import FONTS_FOLDER
import os.path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from results.prepare_data import lab_iss_to_pdf, text_iss_to_pdf, previous_procedure_list_result
from results.sql_func import get_paraclinic_result_by_iss
from utils.dates import normalize_date
import os


def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None, **kwargs):
    """
    Форма печати протокола из шаблона
    """

    pdfmetrics.registerFont(TTFont("PTAstraSerifBold", os.path.join(FONTS_FOLDER, "PTAstraSerif-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("PTAstraSerifReg", os.path.join(FONTS_FOLDER, "PTAstraSerif-Regular.ttf")))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 11
    style.leading = 12
    style.spaceAfter = 1.2 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = 15

    styleFL = deepcopy(style)
    styleFL.firstLineIndent = 0

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleBold.firstLineIndent = 0

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.spaceAfter = 0 * mm

    styleRight = deepcopy(style)
    styleRight.aligment = TA_RIGHT

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.firstLineIndent = 0
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 13
    styleCenterBold.face = "PTAstraSerifBold"

    styleTableCentre = deepcopy(style)
    styleTableCentre.alignment = TA_CENTER
    styleTableCentre.spaceAfter = 4.5 * mm
    styleTableCentre.fontSize = 8
    styleTableCentre.leading = 4.5 * mm

    styleT = deepcopy(style)
    styleT.firstLineIndent = 0
    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    styles_obj = {
        "style": style,
        "styleCenter": styleCenter,
        "styleBold": styleBold,
        "styleCenterBold": styleCenterBold,
        "styleJustified": styleJustified,
        "styleRight": styleRight,
    }

    current_template_file = iss.research.schema_pdf.path

    fields_values = get_paraclinic_result_by_iss(iss.pk)
    result_data = {i.field_title: i.field_value for i in fields_values}
    result_data_by_id = {i.field_id: i.field_value for i in fields_values}

    result_field_type_by_id = {i.field_id: i.field_type for i in fields_values}
    result_field_type_by_title = {i.field_title: i.field_type for i in fields_values}

    if current_template_file:
        with open(current_template_file) as json_file:
            data = json.load(json_file)
            body_paragraphs = data["body_paragraphs"]
            header_paragraphs = data["header"]
            show_title = data.get("showTitle", [])

    objs = []
    if current_template_file:
        for section in header_paragraphs:
            objs = check_section_param(objs, styles_obj, section, result_data, show_title, result_data_by_id, result_field_type_by_title, result_field_type_by_id)
        fwb.extend(objs)
        objs = []
        for section in body_paragraphs:
            objs = check_section_param(objs, styles_obj, section, result_data, show_title, result_data_by_id, result_field_type_by_title, result_field_type_by_id)

    fwb.extend(objs)

    return fwb


def check_section_param(objs, styles_obj, section, field_titles_value, show_title, field_id_value, result_field_type_by_title, result_field_type_by_id):
    if section.get("Spacer"):
        height_spacer = section.get("spacer_data")
        objs.append(Spacer(1, height_spacer * mm))
    elif section.get("page_break"):
        objs.append(PageBreak())
    elif section.get("text"):
        field_titles_sec = section.get("fieldTitles")
        data_fields = []
        field_type = None
        for i in field_titles_sec:
            field_value = ""
            if field_titles_value.get(i):
                field_value = field_titles_value.get(i)
                field_type = result_field_type_by_title.get(i)
            elif field_id_value.get(i):
                field_value = field_id_value.get(i)
                field_type = result_field_type_by_id.get(i)
            if field_type in [17, 38, 16]:
                field_value = prepare_aggr_desc(field_value, field_type)
                objs.extend(field_value)
                return objs
            if field_type == 1:
                field_value = normalize_date(field_value)
            if i in show_title:
                field_value = f"<u>{i}</u> - {field_value}"
            data_fields.append(field_value)
        if styles_obj.get(section.get("style")):
            objs.append(Paragraph(section.get("text").format(*data_fields), styles_obj[section.get("style")]))
    return objs


def prepare_aggr_desc(field_value, field_type):
    v = field_value.replace('<', '&lt;').replace('>', '&gt;').replace("\n", "<br/>")
    v = v.replace('&lt;sub&gt;', '<sub>')
    v = v.replace('&lt;/sub&gt;', '</sub>')
    v = v.replace('&lt;sup&gt;', '<sup>')
    v = v.replace('&lt;/sup&gt;', '</sup>')
    if field_type == 17:
        if v:
            v = json.loads(v)
            if not v['directions']:
                return []
            aggr_text = text_iss_to_pdf(v)
            if not aggr_text:
                return []
            return aggr_text
    if field_type == 38:
        previous_procedure_result = previous_procedure_list_result(v)
        if not previous_procedure_result:
            return []
        return previous_procedure_result

    if field_type == 16:
        v = json.loads(v)
        if not v['directions']:
            return []
        aggr_lab = lab_iss_to_pdf(v)
        if not aggr_lab:
            return []
        return aggr_lab





