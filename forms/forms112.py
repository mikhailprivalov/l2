import datetime
import locale
import os.path
import sys
from copy import deepcopy
from io import BytesIO
from typing import List, Union

import simplejson as json
from reportlab.graphics.barcode import code128, qr
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak, Macro
from reportlab.platypus.flowables import HRFlowable
from appconf.manager import SettingManager
from clients.models import Card
from directions.models import Napravleniya, Issledovaniya
from laboratory.settings import FONTS_FOLDER, BASE_DIR
from utils.xh import save_tmp_file
from directions.views import gen_pdf_dir as f_print_direction
from django.http import HttpRequest


def form_01(request_data):
    """
    Дополнительные страницы при печати направлений
    """
    ind_card = Card.objects.get(pk=request_data["card_pk"])
    patient_data = ind_card.get_data_individual()
    p_doc_serial, p_doc_num = patient_data['passport_serial'], patient_data['passport_num']
    work_dir = json.loads(request_data["napr_id"])
    fin_title = request_data["fin_title"]
    type_additional_pdf = request_data["type_additional_pdf"]
    napr = Napravleniya.objects.filter(pk__in=work_dir)
    dir_temp = [n.pk for n in napr if n.istochnik_f.title.lower() == fin_title and n.client == ind_card]
    if not dir_temp:
        return False

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    # Генерировать pdf-Лист на оплату
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Symbola', os.path.join(FONTS_FOLDER, 'Symbola.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=12 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=28 * mm, allowSplitting=1, title="Форма {}".format("Договор на оплату")
    )
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 9
    style.leading = 12
    style.spaceAfter = 0 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = 15

    styleAppendix = deepcopy(style)
    styleAppendix.fontSize = 9
    styleAppendix.firstLineIndent = 8
    styleAppendix.leading = 9

    styleFL = deepcopy(style)
    styleFL.firstLineIndent = 0
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleBoldCenter = deepcopy(styleBold)
    styleBoldCenter.alignment = TA_CENTER

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 9
    styleCenter.leading = 10
    styleCenter.spaceAfter = 0 * mm

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 20
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'

    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    styleTCenter = deepcopy(styleCenter)
    styleTCenter.alignment = TA_CENTER
    styleTCenter.leading = 3.5 * mm

    styleTBold = deepcopy(styleCenterBold)
    styleTBold.fontSize = 10
    styleTBold.alignment = TA_LEFT

    styles_obj = {'style': style, 'styleCenter': styleCenter, 'styleAppendix': styleAppendix, "styleBoldCenter": styleBoldCenter}

    styleTR = deepcopy(style)
    styleTR.alignment = TA_RIGHT

    objs: List[Union[Spacer, Paragraph, Table, KeepTogether]] = []

    if not os.path.join(BASE_DIR, 'forms', 'additionla_pages', type_additional_pdf):
        additional_data_from_file = os.path.join(BASE_DIR, 'forms', 'additionla_pages', "default")
    else:
        additional_data_from_file = os.path.join(BASE_DIR, 'forms', 'additional_pages', "default")
    if additional_data_from_file:
        with open(additional_data_from_file) as json_file:
            data = json.load(json_file)
            appendix_paragraphs = data.get('appendix_paragraphs', None)
            appendix_route_list = data.get('appendix_route_list', None)
            appendix_direction_list = data.get('appendix_direction_list', None)

    if additional_data_from_file and appendix_paragraphs:
        for section in appendix_paragraphs:
            if section.get('page_break'):
                objs.append(PageBreak())
                objs.append(Macro("canvas._pageNumber=1"))
            elif section.get('Spacer'):
                height_spacer = section.get('spacer_data')
                objs.append(Spacer(1, height_spacer * mm))
            elif section.get('HRFlowable'):
                objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
            elif section.get('patient_fio'):
                objs.append(Paragraph(f"{section['text']} {patient_data['fio']} ({patient_data['born']})", styles_obj[section['style']]))
            elif section.get('patient_addresses'):
                objs.append(Paragraph(f"{section['text']} {patient_data['main_address']}", styles_obj[section['style']]))
            elif section.get('patient_document'):
                objs.append(Paragraph(f"{section['text']} {patient_data['type_doc']} {p_doc_serial} {p_doc_num}", styles_obj[section['style']]))
            else:
                objs.append(Paragraph(f"{section['text']}", styles_obj[section['style']]))

    styleTB = deepcopy(style)
    styleTB.firstLineIndent = 0
    styleTB.fontSize = 8.5
    styleTB.alignment = TA_CENTER
    styleTB.fontName = "PTAstraSerifBold"
    route_list = [[Paragraph('Направление', styleTB), Paragraph('Услуга', styleTB), Paragraph(' Ш/к', styleTB)]]

    if additional_data_from_file and appendix_route_list:
        for section in appendix_route_list:
            if section.get('page_break'):
                objs.append(PageBreak())
                objs.append(Macro("canvas._pageNumber=1"))
            elif section.get('Spacer'):
                height_spacer = section.get('spacer_data')
                objs.append(Spacer(1, height_spacer * mm))
            elif section.get('patient_fio'):
                objs.append(Paragraph(f"{section['text']} {patient_data['fio']} ({patient_data['born']})", styles_obj[section['style']]))
            else:
                objs.append(Paragraph(f"{section['text']}", styles_obj[section['style']]))
        styleTC = deepcopy(style)
        styleTC.firstLineIndent = 0
        styleTC.fontSize = 8.5
        styleTC.alignment = TA_LEFT

        for current_dir in work_dir:
            barcode = code128.Code128(current_dir, barHeight=5 * mm, barWidth=1.25, lquiet=1 * mm)
            iss_obj = Issledovaniya.objects.filter(napravleniye_id=current_dir)
            step = 0
            for current_iss in iss_obj:
                if step > 0:
                    barcode = Paragraph('', styleTC)
                    current_dir = ""
                route_list.append([Paragraph(f"{current_dir}", styleTC), Paragraph(f"{current_iss.research.title}", styleTC), barcode])
                step += 1

        tbl = Table(route_list, colWidths=(40 * mm, 78 * mm, 72 * mm), hAlign='LEFT')
        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]
            )
        )

        objs.append(Spacer(1, 5 * mm))
        objs.append(tbl)
    direction_data = []
    if additional_data_from_file and appendix_direction_list:
        types_direction = {"islab": set(), "isDocrefferal": set(), "isParaclinic": set(), "isGistology": set()}
        for d in dir_temp:
            iss_obj = Issledovaniya.objects.filter(napravleniye_id=d).first()
            if iss_obj.research.is_doc_refferal:
                types_direction["isDocrefferal"].add(d)
            elif iss_obj.research.is_paraclinic:
                types_direction["isParaclinic"].add(d)
            elif iss_obj.research.is_paraclinic:
                types_direction["isGistology"].add(d)
            elif (
                not iss_obj.research.is_form
                and not iss_obj.research.is_citology
                and not iss_obj.research.is_gistology
                and not iss_obj.research.is_stom
                and not iss_obj.research.is_application
                and not iss_obj.research.is_direction_params
                and not iss_obj.research.is_microbiology
                and not iss_obj.research.is_treatment
            ):
                types_direction["islab"].add(d)

        for section in appendix_direction_list:
            if section.get('islab'):
                direction_data.extend(list(types_direction["islab"]))
            elif section.get('isDocrefferal'):
                direction_data.extend(list(types_direction["isDocrefferal"]))
            elif section.get('isParaclinic'):
                direction_data.extend(list(types_direction["isParaclinic"]))

    doc.build(objs)

    pdf = buffer.getvalue()

    if SettingManager.get("print_direction_after_contract", default='False', default_type='b') and len(direction_data) > 0:
        direction_obj = HttpRequest()
        direction_obj._body = json.dumps({"napr_id": direction_data, "from_additional_pages": True})
        direction_obj.user = request_data['user']
        fc = f_print_direction(direction_obj)
        if fc:
            fc_buf = BytesIO()
            fc_buf.write(fc.content)
            fc_buf.seek(0)
            buffer.seek(0)
            from pdfrw import PdfReader, PdfWriter

            today = datetime.datetime.now()
            date_now1 = datetime.datetime.strftime(today, "%y%m%d%H%M%S%f")[:-3]
            date_now_str = str(ind_card.pk) + str(date_now1)
            dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
            file_dir = os.path.join(dir_param, date_now_str + '_dir.pdf')
            file_contract = os.path.join(dir_param, date_now_str + '_contract.pdf')
            save_tmp_file(fc_buf, filename=file_dir)
            save_tmp_file(buffer, filename=file_contract)
            pdf_all = BytesIO()
            inputs = [file_contract, file_dir]
            writer = PdfWriter()
            for inpfn in inputs:
                writer.addpages(PdfReader(inpfn).pages)
            writer.write(pdf_all)
            pdf_out = pdf_all.getvalue()
            pdf_all.close()
            buffer.close()
            os.remove(file_dir)
            os.remove(file_contract)
            fc_buf.close()
            return pdf_out

    buffer.close()
    return pdf
