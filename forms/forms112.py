import datetime
import locale
import os.path
import sys
import zlib
from copy import deepcopy
from datetime import date
from io import BytesIO
from typing import List, Union

import pytils
import simplejson as json
from dateutil.relativedelta import relativedelta
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import code128, qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.colors import white, black
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
from directions.models import Napravleniya, IstochnikiFinansirovaniya, PersonContract, Issledovaniya
from hospitals.models import Hospitals
from laboratory import utils
from laboratory.settings import FONTS_FOLDER, BASE_DIR
from utils.xh import save_tmp_file
from . import forms_func
from utils.pagenum import PageNumCanvasPartitionAll
from .sql_func import sort_direction_by_file_name_contract
from directions.views import gen_pdf_dir as f_print_direction
from django.http import HttpRequest


def form_01(request_data):
    """
    Дополнительные страницы при печати направлений
    """
    ind_card = Card.objects.get(pk=request_data["card_pk"])
    work_dir = json.loads(request_data["napr_id"])
    type_additional_pdf = request_data["type_additional_pdf"]
    napr = Napravleniya.objects.filter(pk__in=work_dir)
    dir_temp = [n.pk for n in napr if n.istochnik_f_id.title.lower() == "омс" and n.client == ind_card ]
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

    types_direction = {"islab": set(), "isDocrefferal": set(), "isParaclinic": set(), "isGistology": set()}
    objs: List[Union[Spacer, Paragraph, Table, KeepTogether]] = []

    if not os.path.join(BASE_DIR, 'forms', 'additionla_pages', type_additional_pdf):
        additional_data_from_file = os.path.join(BASE_DIR, 'forms', 'additionla_pages', "default")
    else:
        additional_data_from_file = os.path.join(BASE_DIR, 'forms', 'additionla_pages', type_additional_pdf)
    if additional_data_from_file:
        with open(additional_data_from_file) as json_file:
            data = json.load(json_file)
            body_paragraphs = data['body_paragraphs']
            appendix_paragraphs = data.get('appendix_paragraphs', None)
            appendix_route_list = data.get('appendix_route_list', None)
            appendix_direction_list = data.get('appendix_direction_list', None)
    else:
        executor = None

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
            elif section.get('executor_l2'):
                objs.append(Paragraph(f"{section['text']} {exec_person}", styles_obj[section['style']]))
            else:
                objs.append(Paragraph(f"{section['text']}", styles_obj[section['style']]))

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

        tbl = Table(route_list, colWidths=(30 * mm, 58 * mm, 60 * mm, 42 * mm), hAlign='LEFT')
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

    def first_pages(canvas, document):
        canvas.saveState()
        canvas.setFont("PTAstraSerifReg", 9)
        # вывести интерактивную форму "текст"
        form = canvas.acroForm
        # canvas.drawString(25, 780, '')
        form.textfield(
            name='comment',
            tooltip='comment',
            fontName='Times-Roman',
            fontSize=10,
            x=57,
            y=750,
            borderStyle='underlined',
            borderColor=black,
            fillColor=white,
            width=515,
            height=13,
            textColor=black,
            forceBorder=False,
        )

        # Вывести на первой странице код-номер договора
        barcode128.drawOn(canvas, 10 * mm, 282 * mm)

        # вывести внизу QR-code (ФИО, (номера направлений))
        qr_code = qr.QrCodeWidget(qr_value)
        qr_code.barWidth = 70
        qr_code.barHeight = 70
        qr_code.qrVersion = 1
        d = Drawing()
        d.add(qr_code)
        renderPDF.draw(d, canvas, 90 * mm, 7)
        # вывести атрибуты для подписей
        canvas.setFont('PTAstraSerifReg', 10)
        canvas.drawString(40 * mm, 10 * mm, '____________________________')
        canvas.drawString(115 * mm, 10 * mm, '/{}/____________________________'.format(npf))
        canvas.setFont('Symbola', 18)
        canvas.drawString(195 * mm, 10 * mm, '\u2713')

        canvas.setFont('PTAstraSerifReg', 8)
        canvas.drawString(50 * mm, 7 * mm, '(подпись сотрудника)')
        canvas.drawString(160 * mm, 7 * mm, '(подпись плательщика)')

        # вывестии защитны вертикальный мелкий текст
        canvas.rotate(90)
        canvas.setFillColor(HexColor(0x4F4B4B))
        canvas.setFont('PTAstraSerifReg', 5.2)
        canvas.drawString(10 * mm, -12 * mm, '{}'.format(6 * left_size_str))

        canvas.restoreState()

    def later_pages(canvas, document):
        canvas.saveState()
        # вывести внизу QR-code (ФИО, (номера направлений))
        qr_code = qr.QrCodeWidget(qr_value)
        qr_code.barWidth = 70
        qr_code.barHeight = 70
        qr_code.qrVersion = 1
        d = Drawing()
        d.add(qr_code)
        renderPDF.draw(d, canvas, 90 * mm, 7)
        # вывести атрибуты для подписей
        canvas.setFont('PTAstraSerifReg', 10)
        canvas.drawString(40 * mm, 10 * mm, '____________________________')
        canvas.drawString(115 * mm, 10 * mm, '/{}/____________________________'.format(npf))

        canvas.setFont('Symbola', 18)
        canvas.drawString(195 * mm, 10 * mm, '\u2713')

        canvas.setFont('PTAstraSerifReg', 8)
        canvas.drawString(50 * mm, 7 * mm, '(подпись сотрудника)')
        canvas.drawString(160 * mm, 7 * mm, '(подпись плательщика)')
        canvas.rotate(90)
        canvas.setFillColor(HexColor(0x4F4B4B))
        canvas.setFont('PTAstraSerifReg', 5.2)
        canvas.drawString(10 * mm, -12 * mm, '{}'.format(6 * left_size_str))
        canvas.restoreState()

    doc.build(objs)

    pdf = buffer.getvalue()

    if SettingManager.get("print_direction_after_contract", default='False', default_type='b') and len(direction_data) > 0:
        direction_obj = HttpRequest()
        direction_obj._body = json.dumps({"napr_id": direction_data})
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
