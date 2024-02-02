import datetime
import locale
import os.path
import sys
from copy import deepcopy
from io import BytesIO
from typing import List, Union

import simplejson as json
from reportlab.graphics.barcode import code128
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
from hospitals.models import Hospitals
from laboratory.settings import FONTS_FOLDER, BASE_DIR
from utils.xh import save_tmp_file, correspondence_get_file_hash
from directions.views import gen_pdf_dir as f_print_direction
from django.http import HttpRequest
from django.utils.module_loading import import_string
from pdfrw import PdfReader, PdfWriter


def form_01(request_data):
    """
    Дополнительные страницы при печати направлений
    """
    ind_card = Card.objects.get(pk=request_data["card_pk"])
    patient_data = ind_card.get_data_individual()
    work_dir = json.loads(request_data["napr_id"])
    fin_title = request_data["fin_title"]
    type_additional_pdf = request_data["type_additional_pdf"]
    napr = Napravleniya.objects.filter(pk__in=work_dir)
    dir_temp = [n.pk for n in napr if n.istochnik_f.title.lower() == fin_title.lower() and n.client == ind_card]
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

    styleTB = deepcopy(style)
    styleTB.firstLineIndent = 0
    styleTB.fontSize = 8.5
    styleTB.alignment = TA_CENTER
    styleTB.fontName = "PTAstraSerifBold"

    styleTC = deepcopy(style)
    styleTC.firstLineIndent = 0
    styleTC.fontSize = 8.5
    styleTC.alignment = TA_LEFT

    styles_obj = {'style': style, 'styleCenter': styleCenter, 'styleAppendix': styleAppendix, "styleBoldCenter": styleBoldCenter, "styleTB": styleTB, "styleTC": styleTC}
    styleTR = deepcopy(style)
    styleTR.alignment = TA_RIGHT

    objs: List[Union[Spacer, Paragraph, Table, KeepTogether]] = []

    if not os.path.join(BASE_DIR, 'forms', 'additional_pages', type_additional_pdf):
        additional_data_from_file = os.path.join(BASE_DIR, 'forms', 'additional_pages', "default.json")
    else:
        additional_data_from_file = os.path.join(BASE_DIR, 'forms', 'additional_pages', type_additional_pdf)
    if additional_data_from_file:
        with open(additional_data_from_file) as json_file:
            data = json.load(json_file)
            appendix_paragraphs = data.get('appendix_paragraphs', None)
            appendix_route_list = data.get('appendix_route_list', None)
            appendix_direction_list = data.get('appendix_direction_list', None)

    additional_objects = {"work_dir": work_dir}
    if additional_data_from_file and appendix_paragraphs:
        objs = add_appendix_paragraphs(objs, appendix_paragraphs, patient_data, styles_obj, additional_objects)

    styleTB = deepcopy(style)
    styleTB.firstLineIndent = 0
    styleTB.fontSize = 8.5
    styleTB.alignment = TA_CENTER
    styleTB.fontName = "PTAstraSerifBold"

    if additional_data_from_file and appendix_route_list:
        objs = add_route_list(objs, appendix_route_list, patient_data, styles_obj, additional_objects)

    direction_data = []
    if additional_data_from_file and appendix_direction_list:
        direction_data = add_appendix_direction_list(appendix_direction_list, dir_temp)

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


def form_02(request_data):
    """
    Приложения страницы при печати направлений
    """
    ind_card = Card.objects.get(pk=request_data["card_pk"])
    patient_data = ind_card.get_data_individual()
    work_dir = json.loads(request_data["napr_id"])
    fin_title = request_data["fin_title"]
    type_additional_pdf = request_data["type_additional_pdf"]
    napr = Napravleniya.objects.filter(pk__in=work_dir)
    dir_temp = [n.pk for n in napr if n.istochnik_f.title.lower() == fin_title.lower() and n.client == ind_card]
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

    styleTB = deepcopy(style)
    styleTB.firstLineIndent = 0
    styleTB.fontSize = 8.5
    styleTB.alignment = TA_CENTER
    styleTB.fontName = "PTAstraSerifBold"

    styleTC = deepcopy(style)
    styleTC.firstLineIndent = 0
    styleTC.fontSize = 8.5
    styleTC.alignment = TA_LEFT

    styles_obj = {'style': style, 'styleCenter': styleCenter, 'styleAppendix': styleAppendix, "styleBoldCenter": styleBoldCenter, "styleTB": styleTB, "styleTC": styleTC}

    styleTR = deepcopy(style)
    styleTR.alignment = TA_RIGHT

    objs: List[Union[Spacer, Paragraph, Table, KeepTogether]] = []

    if not os.path.join(BASE_DIR, 'forms', 'additional_pages', type_additional_pdf):
        additional_data_from_file = os.path.join(BASE_DIR, 'forms', 'additional_pages', "default.json")
    else:
        additional_data_from_file = os.path.join(BASE_DIR, 'forms', 'additional_pages', type_additional_pdf)

    if additional_data_from_file:
        with open(additional_data_from_file) as json_file:
            data = json.loads(json_file.read())
            appendix_paragraphs = data.get('appendix_paragraphs', None)
            appendix_route_list = data.get('appendix_route_list', None)
            appendix_direction_list = data.get('appendix_direction_list', None)
            appendix_orders = data.get('appendix_orders', None)
            appendix_cards_agrees = data.get('appendix_cards_agrees', None)

    additional_objects = {"work_dir": work_dir}

    if additional_data_from_file:
        if appendix_orders:
            for k, v in appendix_orders.items():
                result_form = import_string('forms.forms112.' + v)
                objs = result_form(objs, locals()[k], patient_data, styles_obj, additional_objects)
        else:
            if appendix_paragraphs:
                objs = add_appendix_paragraphs(objs, appendix_paragraphs, patient_data, styles_obj, additional_objects)
            if additional_data_from_file and appendix_route_list:
                objs = add_route_list(objs, appendix_route_list, patient_data, styles_obj, additional_objects)

    doc.build(objs)
    pdf = buffer.getvalue()
    result_join_pdf = None

    direction_data = []
    if additional_data_from_file and appendix_direction_list:
        direction_data = add_appendix_direction_list(appendix_direction_list, dir_temp)

    if SettingManager.get("print_direction_after_contract", default='False', default_type='b'):
        # печать дополнительных форм
        http_params = {
            "card_pk": request_data["card_pk"],
            "user": request_data["user"],
            "hospital": request_data["user"].doctorprofile.get_hospital() if hasattr(request_data["user"], "doctorprofile") else Hospitals.get_default_hospital(),
            "napr_id": f'[{", ".join(str(e) for e in dir_temp)}]',
            "from_appendix_pages": True,
        }
        if appendix_cards_agrees:
            for i in appendix_cards_agrees:
                result_join_pdf = join_two_pdf_data(import_string(i), http_params, request_data['user'], buffer, ind_card, "get")
                buffer = BytesIO()
                buffer.write(result_join_pdf)

        # печать направлений в конце
        if len(direction_data) > 0:
            http_params = {"napr_id": direction_data, "from_additional_pages": True, "from_appendix_pages": True}
            result_join_pdf = join_two_pdf_data(f_print_direction, http_params, request_data['user'], buffer, ind_card)
        if not result_join_pdf:
            result_join_pdf = pdf
        return result_join_pdf

    buffer.close()
    return pdf


def join_two_pdf_data(func_name, http_params, user_data, buffer, ind_card, type="post"):
    if type == "get":
        fc = func_name(request_data=http_params)
        is_get = False
    else:
        http_obj = HttpRequest()
        http_obj._body = json.dumps(http_params)
        http_obj.user = user_data
        fc = func_name(http_obj)
        is_get = True
    if fc:
        fc_buf = BytesIO()
        if is_get:
            fc_buf.write(fc.content)
        else:
            fc_buf.write(fc)
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


def add_appendix_paragraphs(objs, appendix_paragraphs, patient_data, styles_obj, additional_objects):
    p_doc_serial, p_doc_num = patient_data['passport_serial'], patient_data['passport_num']
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

    return objs


def add_route_list(objs, appendix_route_list, patient_data, styles_obj, additional_objectsj):
    styleTB = styles_obj["styleTB"]
    styleTC = styles_obj["styleTC"]
    route_list = [[Paragraph('Направление', styleTB), Paragraph('Пройдено', styleTB), Paragraph('Услуга', styleTB), Paragraph('Примечание', styleTB), Paragraph(' Ш/к', styleTB)]]
    notation = False
    for section in appendix_route_list:
        if section.get('page_break'):
            objs.append(PageBreak())
            objs.append(Macro("canvas._pageNumber=1"))
        elif section.get('Spacer'):
            height_spacer = section.get('spacer_data')
            objs.append(Spacer(1, height_spacer * mm))
        elif section.get('patient_fio'):
            objs.append(Paragraph(f"{section['text']} {patient_data['fio']} ({patient_data['born']})", styles_obj[section['style']]))
        elif section.get('notation'):
            notation = True
        else:
            objs.append(Paragraph(f"{section['text']}", styles_obj[section['style']]))

    work_dir = additional_objectsj["work_dir"]
    dir_by_profile = {'not_profile': []}
    for current_dir in work_dir:
        iss_obj = Issledovaniya.objects.filter(napravleniye_id=current_dir).first()
        if iss_obj.research.speciality:
            if not dir_by_profile.get(iss_obj.research.speciality.title):
                dir_by_profile[iss_obj.research.speciality.title] = [current_dir]
            else:
                dir_by_profile[iss_obj.research.speciality.title].append(current_dir)
        else:
            dir_by_profile['not_profile'].append(current_dir)

    work_dir = []
    for v in dir_by_profile.values():
        work_dir.extend(v)

    for current_dir in work_dir:
        barcode = code128.Code128(current_dir, barHeight=5 * mm, barWidth=1.25, lquiet=1 * mm)
        iss_obj = Issledovaniya.objects.filter(napravleniye_id=current_dir)
        step = 0
        for current_iss in iss_obj:
            paraclinic_info = ""
            if step > 0:
                barcode = Paragraph('', styleTC)
                current_dir = ""
            if notation:
                paraclinic_info = current_iss.research.paraclinic_info[0:40].replace('<', '').replace('>', '')
            research_title = current_iss.research.short_title if current_iss.research.short_title else current_iss.research.title
            route_list.append(
                [Paragraph(f"{current_dir}", styleTC), Paragraph("", styleTC), Paragraph(f"{research_title}", styleTC), Paragraph(f"{paraclinic_info}", styleTC), barcode]
            )
            step += 1

    tbl = Table(route_list, colWidths=(25 * mm, 28 * mm, 47 * mm, 45 * mm, 45 * mm), rowHeights=25 * mm, hAlign='LEFT')
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

    return objs


def add_appendix_direction_list(appendix_direction_list, dir_temp):
    direction_data = []
    types_direction = {"islab": set(), "isDocrefferal": set(), "isParaclinic": set(), "isGistology": set(), "isHospital": set(), "isForm": set()}
    for d in dir_temp:
        iss_obj = Issledovaniya.objects.filter(napravleniye_id=d).first()
        if iss_obj.research.is_doc_refferal:
            types_direction["isDocrefferal"].add(d)
        elif iss_obj.research.is_paraclinic:
            types_direction["isParaclinic"].add(d)
        elif iss_obj.research.is_paraclinic:
            types_direction["isGistology"].add(d)
        elif iss_obj.research.is_hospital:
            types_direction["isHospital"].add(d)
        elif iss_obj.research.is_form:
            types_direction["isForm"].add(d)
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
        elif section.get('isHospital'):
            direction_data.extend(list(types_direction["isHospital"]))
        elif section.get('isForm'):
            direction_data.extend(list(types_direction["isForm"]))

    return direction_data


def form_03(request_data):
    id_file = request_data.get("id").replace('"', "")
    file_data = correspondence_get_file_hash(id_file)
    if file_data:
        dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
        file_dir = os.path.join(dir_param, file_data)
        pdf_all = BytesIO()
        inputs = [file_dir]
        writer = PdfWriter()
        for inpfn in inputs:
            writer.addpages(PdfReader(inpfn).pages)
        writer.write(pdf_all)
        pdf_out = pdf_all.getvalue()
        os.remove(file_dir)
        return pdf_out
