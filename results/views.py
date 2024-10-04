import base64
import collections
import datetime
import operator
import os.path
import random
import re
import uuid
from copy import deepcopy
from io import BytesIO
from typing import Optional

import simplejson as json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils import dateformat
from django.utils import timezone
from django.utils.text import Truncator
from django.views.decorators.csrf import csrf_exempt
from pdfrw import PdfReader, PdfWriter
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfdoc
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Image
from reportlab.platypus import PageBreak, Spacer, KeepTogether, Flowable, Frame, PageTemplate, NextPageTemplate, BaseDocTemplate
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.platypus.flowables import HRFlowable, Macro

import directory.models as directory
import slog.models as slog
from api.stationar.stationar_func import hosp_get_hosp_direction
from appconf.manager import SettingManager
from clients.models import CardBase
from directions.models import Issledovaniya, Result, Napravleniya, ParaclinicResult, Recipe, DirectionDocument, DocumentSign, IssledovaniyaFiles, ComplexResearchAccountPerson
from laboratory.decorators import logged_in_or_token
from laboratory.settings import (
    DEATH_RESEARCH_PK,
    LK_USER,
    SYSTEM_AS_VI,
    QRCODE_OFFSET_SIZE,
    LEFT_QRCODE_OFFSET_SIZE,
    GISTOLOGY_RESEARCH_PK,
    RESEARCHES_NOT_PRINT_FOOTERS,
    RESULT_LABORATORY_FORM,
    SELF_WATERMARKS,
)
from laboratory.settings import FONTS_FOLDER
from laboratory.utils import strdate
from podrazdeleniya.models import Podrazdeleniya
from utils.dates import try_strptime
from utils.flowable import InteractiveTextField, QrCodeSite
from utils.pagenum import PageNumCanvas, PageNumCanvasPartitionAll
from .laboratory_form import default_lab_form
from .prepare_data import default_title_result_form, structure_data_for_result, plaint_tex_for_result, microbiology_result, procedural_text_for_result
from django.utils.module_loading import import_string

pdfmetrics.registerFont(TTFont('FreeSans', os.path.join(FONTS_FOLDER, 'FreeSans.ttf')))
pdfmetrics.registerFont(TTFont('FreeSansBold', os.path.join(FONTS_FOLDER, 'FreeSansBold.ttf')))
pdfmetrics.registerFont(TTFont('OpenSansItalic', os.path.join(FONTS_FOLDER, 'OpenSans-Italic.ttf')))
pdfmetrics.registerFont(TTFont('OpenSansBoldItalic', os.path.join(FONTS_FOLDER, 'OpenSans', 'OpenSans-BoldItalic.ttf')))
pdfmetrics.registerFont(TTFont('OpenSansLight', os.path.join(FONTS_FOLDER, 'OpenSans', 'OpenSans-Light.ttf')))
pdfmetrics.registerFont(TTFont('Consolas', os.path.join(FONTS_FOLDER, 'consolas.ttf')))
pdfmetrics.registerFont(TTFont('Consolas-Bold', os.path.join(FONTS_FOLDER, 'Consolas-Bold.ttf')))
pdfmetrics.registerFont(TTFont('cour', os.path.join(FONTS_FOLDER, 'cour.ttf')))


@login_required
def enter(request):
    return redirect('/laboratory/results')


def lr(s, ll=7, r=17):
    if not s:
        s = ""
    return s.ljust(ll).rjust(r)


def result_normal(s):
    s = s.strip()
    if re.match(r'\d+\.\d{5,}$', s):
        try:
            s = str(round(float(s), 4))
        except:
            pass
    # s = lr(s).replace(" ", "&nbsp;")
    s = s.replace("<br>", "<br/>")
    return s


def save(form, filename: str):
    with open(filename, 'wb') as f:
        f.write(form.read())


@logged_in_or_token
def results_preview(request):
    return redirect('/ui/results/preview?{}'.format(request.META['QUERY_STRING']))


@logged_in_or_token
def result_print(request):
    """Печать результатов"""
    plain_response = True if hasattr(request, 'plain_response') and request.plain_response else False
    inline = request.GET.get("inline", "1") == "1" or plain_response
    response = HttpResponse(content_type='application/pdf')

    if inline:
        if SettingManager.get("pdf_auto_print", "true", "b") and not plain_response:
            pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:true,bSilent:false,bShrinkToFit:true}\);)>>'
        response['Content-Disposition'] = 'inline; filename="results.pdf"'
    else:
        response['Content-Disposition'] = 'attachment; filename="results.pdf"'

    pk = [x for x in json.loads(request.GET["pk"]) if x is not None]

    show_norm = True  # request.GET.get("show_norm", "0") == "1"
    interactive_text_field = SettingManager.get("interactive_text_field", default='False', default_type='b')

    buffer = BytesIO()
    split = request.GET.get("split", "1") == "1"
    protocol_plain_text = request.GET.get("protocol_plain_text", "0") == "1"
    leftnone = request.GET.get("leftnone", "0") == "0"
    med_certificate = request.GET.get("med_certificate", "0") == "1"
    med_certificate_title = ""
    if med_certificate:
        med_certificate_title = "Справка - "
    hosp = request.GET.get("hosp", "0") == "1"
    complex = request.GET.get("complex", "0") == "1"
    with_signature_stamps = request.GET.get("withSignatureStamps", "0") == "1"

    if complex:
        pk = ComplexResearchAccountPerson.get_complex_confirm_directions(tuple(pk))

    doc = BaseDocTemplate(
        buffer,
        leftMargin=(27 if leftnone else 15) * mm,
        rightMargin=12 * mm,
        topMargin=5 * mm,
        bottomMargin=16 * mm,
        allowSplitting=1,
        _pageBreakQuick=1,
        title="Результаты для направлений {}".format(", ".join([str(x) for x in pk])),
        invariant=1,
    )
    temp_iss = Issledovaniya.objects.filter(napravleniye_id=pk[0]).first()
    left_padding = 15
    right_padding = 9
    top_padding = 5
    bottom_padding = 18
    if temp_iss.research.paddings_size:
        data_padding = temp_iss.research.paddings_size.split('|')
        left_padding = float(data_padding[0])
        top_padding = float(data_padding[1])
        right_padding = float(data_padding[2])
        bottom_padding = float(data_padding[3])
    p_frame = Frame(
        0 * mm,
        0 * mm,
        210 * mm,
        297 * mm,
        leftPadding=(27 if leftnone else left_padding) * mm,
        rightPadding=right_padding * mm,
        topPadding=top_padding * mm,
        bottomPadding=bottom_padding * mm,
        id='portrait_frame',
        showBoundary=0,
    )

    l_frame = Frame(
        0 * mm, 0 * mm, 297 * mm, 210 * mm, leftPadding=10 * mm, rightPadding=15 * mm, topPadding=(27 if leftnone else 15) * mm, bottomPadding=18 * mm, id='landscape_frame', showBoundary=0
    )

    naprs = []
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
    styleLogo = deepcopy(styleBold)
    styleLogo.alignment = TA_CENTER
    styleLogo.fontName = 'FreeSansBold'
    styleLogo.fontSize = 25
    styleLogo.spaceBefore = 0
    styleLogo.spaceAfter = 0
    styleLogo.leftIndent = 0
    styleLogo.rightIndent = 0

    styleSheet["BodyText"].wordWrap = 'CJK'
    stl = deepcopy(styleSheet["BodyText"])
    stl.alignment = TA_CENTER
    logo_text = SettingManager.get("results_l2_logo_string", default='', default_type='s')
    if logo_text:
        logo_cell = Paragraph(logo_text, styleLogo)
    else:
        img_path = os.path.join(FONTS_FOLDER, '..', 'static', 'img')
        if not os.path.exists(img_path):
            os.makedirs(img_path)
        logo_path = os.path.join(img_path, 'logo.png')
        if request.GET.get("update_logo", "0") == "1" or not os.path.isfile(logo_path):
            with open(logo_path, "wb") as fh:
                fh.write(base64.decodebytes(SettingManager.get("logo_base64_img").split(",")[1].encode()))

        logo_cell = Image(logo_path)
        nw = 158
        logo_cell.drawHeight = logo_cell.drawHeight * (nw / logo_cell.drawWidth)
        logo_cell.drawWidth = nw
    region = SettingManager.get("region", default='38', default_type='s')

    def logo_col(d: Napravleniya):
        return [
            logo_cell,
            '',
            '',
            '',
            '',
            Paragraph(
                f'Результат из <font face="OpenSansBoldItalic">{"VI-MIS" if SYSTEM_AS_VI else "L²"}</font>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;%s<br/><br/>%s<br/>%s<br/>%s'
                % (
                    '<font face="OpenSansLight">(L2-irk.ru)</font>' if region == '38' else 'DEMO' if region == 'DEMO' else '',
                    d.hospital_short_title,
                    d.hospital_www,
                    d.hospital_phones,
                ),
                styleAb,
            ),
            '',
            '',
            '',
        ]

    pw = doc.width

    def print_vtype(data, f, iss, j, style_t, styleSheet):
        if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
            result = Result.objects.filter(issledovaniye=iss, fraction=f).order_by("-pk")[0].value.replace("<br>", "<br/>")
            jo = json.loads(result)["rows"]
            style_t.add('LINEBELOW', (0, j - 1), (-1, j - 1), 2, colors.black)
            for key, val in jo.items():
                style_t.add('SPAN', (0, j), (-1, j))
                j += 1

                norm_vals = []
                for rowk, rowv in val["rows"].items():
                    if rowv["value"] not in ["", "null"]:
                        norm_vals.insert(0, {"title": rowv["title"], "value": rowv["value"], "k": int(rowk)})
                if len(norm_vals) > 0:
                    style_t.add('SPAN', (0, j), (-1, j))
                    j += 1
                    tmp = ["", "", "", "", "", ""]
                    data.append(tmp)

                tmp = [
                    Paragraph('&nbsp;&nbsp;&nbsp;&nbsp;<font face="FreeSans" size="8">' + ("" if len(norm_vals) == 0 else f.title + ": ") + val["title"] + "</font>", styleSheet["BodyText"]),
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
                data.append(tmp)
                if len(norm_vals) > 0:
                    li = 0
                    norm_vals.sort(key=operator.itemgetter('k'))
                    for idx, rowv in enumerate(norm_vals):
                        li = idx
                        if li % 2 == 0:
                            tmp = [
                                Paragraph('<font face="FreeSans" size="8">' + rowv["title"] + "</font>", styleSheet["BodyText"]),
                                Paragraph('<font face="FreeSans" size="8">' + rowv["value"] + "</font>", styleSheet["BodyText"]),
                                "",
                            ]
                        else:
                            tmp.append(Paragraph('<font face="FreeSans" size="8">' + rowv["title"] + "</font>", styleSheet["BodyText"]))
                            tmp.append(Paragraph('<font face="FreeSans" size="8">' + rowv["value"] + "</font>", styleSheet["BodyText"]))
                            tmp.append("")
                            tmp.append("")
                            data.append(tmp)
                            j += 1

                    if li % 2 == 0:
                        tmp.append("")
                        tmp.append("")
                        tmp.append("")
                        tmp.append("")
                        data.append(tmp)
                        j += 1
        return j

    client_prev = -1
    link_result = []
    fwb = []
    hosp_nums_obj = hosp_get_hosp_direction(pk[0])
    hosp_nums = ''
    for i in hosp_nums_obj:
        hosp_nums = hosp_nums + ' - ' + str(i.get('direction'))
        break
    portion = request.GET.get("portion", "0") == "1"
    sort = request.GET.get("sort", "0") == "1"
    dirs = []
    if not portion:
        dirs = (
            Napravleniya.objects.filter(pk__in=pk)
            .select_related('client')
            .prefetch_related(
                Prefetch(
                    'issledovaniya_set',
                    queryset=(
                        Issledovaniya.objects.filter(Q(time_save__isnull=False) | Q(time_confirmation__isnull=False)).select_related(
                            'research', 'doc_confirmation', 'doc_confirmation__podrazdeleniye'
                        )
                    ),
                )
            )
            .annotate(results_count=Count('issledovaniya__result'))
            .distinct()
        )
    elif portion and len(pk) == 1:
        dirs = Napravleniya.objects.filter(pk=pk[0])

    count_direction = 0
    previous_size_form = None
    is_page_template_set = False

    def mark_pages(canvas_mark, direction: Napravleniya, qr_data: Optional[str] = None, watermarks: Optional[str] = None):
        canvas_mark.saveState()
        canvas_mark.setFont('FreeSansBold', 8)
        if watermarks:
            canvas_mark.rotate(90)
            canvas_mark.setFillColor(HexColor(0xED775C))
            canvas_mark.setFont('FreeSans', 6)
            canvas_mark.drawString(10 * mm, -23 * mm, '{}'.format(40 * " #ЕРЦП# - НЕ ПОДТВЕРЖДЕНО (ОБРАЗЕЦ) - "))
            canvas_mark.rotate(-90)
            canvas_mark.setFont('FreeSans', 14)
            canvas_mark.drawString(155 * mm, 285 * mm, '{}'.format(" НЕ ПОДТВЕРЖДЕНО "))
            canvas_mark.setFont('FreeSans', 12)
            canvas_mark.drawString(175 * mm, 281 * mm, '{}'.format("( образец )"))
        if not watermarks and not DEATH_RESEARCH_PK and not GISTOLOGY_RESEARCH_PK and not SELF_WATERMARKS and not DISABLE_PATIENT_CANVAS_MARKER:
            if direction.hospital:
                canvas_mark.drawString(55 * mm, 13 * mm, direction.hospital.safe_short_title)
            else:
                canvas_mark.drawString(55 * mm, 13 * mm, '{}'.format(SettingManager.get("org_title")))
            if direction.is_external:
                canvas_mark.drawString(55 * mm, 9.6 * mm, f'№ карты: {direction.client.number_with_type()}; Номер в организации: {direction.id_in_hospital}; Направление № {direction.pk}')
            else:
                canvas_mark.drawString(
                    55 * mm, 9.6 * mm, '№ карты: {}; Номер: {} {}; Направление № {}'.format(direction.client.number_with_type(), num_card, number_poliklinika, direction.pk)
                )
            if not DISABLE_PATIENT_CANVAS_MARKER:
                canvas_mark.drawString(55 * mm, 7.1 * mm, 'Пациент: {} {}'.format(direction.client.individual.fio(), individual_birthday))
                canvas_mark.line(55 * mm, 12.7 * mm, 181 * mm, 11.5 * mm)
            if qr_data:
                qr_code = qr.QrCodeWidget(qr_data)
                qr_code.barWidth = 15 * mm
                qr_code.barHeight = 15 * mm
                qr_code.qrVersion = 1
                d = Drawing()
                d.add(qr_code)
                renderPDF.draw(d, canvas_mark, 20 * mm, 3 * mm)
        if SELF_WATERMARKS:
            self_watermarks_func = import_string('results.laboratory_form.' + SELF_WATERMARKS)
            canvas_mark = self_watermarks_func(canvas_mark)

        canvas_mark.restoreState()

    count_pages = 0
    has_page_break = False
    has_own_form_result = False
    instance_id = SettingManager.instance_id()
    qr_check_url = SettingManager.qr_check_url()
    need_qr = SettingManager.qr_check_result()

    direction: Napravleniya
    if not portion and not sort:
        sorted_direction = sorted(dirs, key=lambda dir: dir.client.individual_id * 100000000 + dir.results_count * 10000000 + dir.pk)
    else:
        sorted_direction = dirs

    if sort:
        sorted_direction_d = deepcopy(pk)
        for d in dirs:
            index_el = sorted_direction_d.index(d.pk)
            sorted_direction_d[index_el] = d
        sorted_direction = sorted_direction_d

    for direction in sorted_direction:
        dpk = direction.pk

        if not direction.is_all_confirm() and not portion:
            continue
        dates = {}
        date_t = ""
        has_paraclinic = False
        link_files = False
        is_extract = False
        is_gistology = False
        current_size_form = None
        temp_iss = None
        has_own_form_result = False

        for iss in direction.issledovaniya_set.all():
            if iss.time_save:
                dt = str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                if dt not in dates.keys():
                    dates[dt] = 0
                dates[dt] += 1
            if iss.tubes.exists() and iss.tubes.first().time_get:
                date_t = strdate(iss.tubes.first().time_get)
            if (
                iss.research.is_paraclinic
                or iss.research.is_doc_refferal
                or iss.research.is_treatment
                or iss.research.is_microbiology
                or iss.research.is_citology
                or iss.research.is_gistology
                or iss.research.is_form
                or iss.research.is_aux
                or iss.research.is_expertise
            ):
                has_paraclinic = True
            if directory.HospitalService.objects.filter(slave_research=iss.research).exists():
                has_paraclinic = True
            if iss.link_file:
                link_result.append(iss.link_file)
                link_files = True
            if IssledovaniyaFiles.objects.filter(issledovaniye=iss).first():
                iss_uploaded_file = IssledovaniyaFiles.objects.filter(issledovaniye=iss).first()
                link_result.append(iss_uploaded_file.uploaded_file.path)
                link_files = True
            if 'выпис' in iss.research.title.lower():
                is_extract = True
            if iss.research.is_gistology:
                is_gistology = True
            if iss.research.has_own_form_result:
                has_own_form_result = True

            current_size_form = iss.research.size_form
            temp_iss = iss

        qr_data = None

        if not has_paraclinic and need_qr and instance_id and qr_check_url:
            if not direction.qr_check_token:
                direction.qr_check_token = uuid.uuid4()
                direction.save(update_fields=['qr_check_token'])
            qr_data = qr_check_url
            qr_data = qr_data.replace('<qr_token>', str(direction.qr_check_token))
            qr_data = qr_data.replace('<direction_id>', str(direction.pk))
            qr_data = qr_data.replace('<instance_id>', instance_id)

        def local_mark_pages(c, _):
            if not iss.time_confirmation and has_own_form_result and portion:
                mark_pages(c, direction, qr_data, "Образец")

            if not has_own_form_result and portion:
                mark_pages(c, direction, qr_data, "Образец")
            elif iss.time_confirmation and iss.research.pk not in RESEARCHES_NOT_PRINT_FOOTERS:
                mark_pages(c, direction, qr_data)

        portrait_tmpl = PageTemplate(id='portrait_tmpl', frames=[p_frame], pagesize=portrait(A4), onPageEnd=local_mark_pages)
        landscape_tmpl = PageTemplate(id='landscape_tmpl', frames=[l_frame], pagesize=landscape(A4), onPageEnd=local_mark_pages)

        if link_files:
            continue

        count_direction += 1
        count_pages += 1

        if previous_size_form == current_size_form:
            is_different_form = False
        else:
            is_different_form = True
        previous_size_form = current_size_form

        fwb = []
        if not is_page_template_set:
            if count_direction == 1 and temp_iss.research.size_form == 1:
                doc.addPageTemplates([landscape_tmpl, portrait_tmpl])
                is_page_template_set = True
            elif count_direction == 1 and temp_iss.research.size_form == 0:
                doc.addPageTemplates([portrait_tmpl, landscape_tmpl])
                is_page_template_set = True

        if is_different_form:
            if temp_iss.research.size_form == 1:
                next_tpl = 'landscape_tmpl'
            else:
                next_tpl = 'portrait_tmpl'

            naprs.append(NextPageTemplate(next_tpl))

        maxdate = ""
        if dates != {}:
            maxdate = max(dates.items(), key=operator.itemgetter(1))[0]

        if not has_paraclinic and date_t == "":
            date_t = maxdate

        number_poliklinika = f' ({direction.client.number_poliklinika})' if direction.client.number_poliklinika else ''
        individual_birthday = f'({strdate(direction.client.individual.birthday)})'
        result_title_form = None
        if not hosp and not is_gistology and not has_own_form_result or is_extract:
            type_title_form = temp_iss.research.result_title_form
            if type_title_form != 0:
                current_type_title_form = str(type_title_form)
                result_title_form = import_string('results.title.forms' + current_type_title_form[0:3] + '.form_' + current_type_title_form[3:5])
            if result_title_form:
                t = result_title_form(temp_iss)
            else:
                t = default_title_result_form(direction, doc, date_t, has_paraclinic, individual_birthday, number_poliklinika, logo_col, is_extract)
            fwb.append(t)
            fwb.append(Spacer(1, 5 * mm))
            lk_address = SettingManager.get("lk_address", default='', default_type='s')
            if lk_address:
                if leftnone:
                    qr_code_param = LEFT_QRCODE_OFFSET_SIZE
                else:
                    qr_code_param = QRCODE_OFFSET_SIZE
                fwb.append(QrCodeSite(lk_address, qr_code_param))
        if not has_paraclinic:
            if not RESULT_LABORATORY_FORM:
                fwb = default_lab_form(fwb, interactive_text_field, pw, direction, styleSheet, directory, show_norm, stl, print_vtype, get_r, result_normal)
            else:
                laboratory_form = import_string('results.laboratory_form.' + RESULT_LABORATORY_FORM)
                fwb = laboratory_form(fwb, interactive_text_field, pw, direction, styleSheet, directory, show_norm, stl, print_vtype, get_r, result_normal)
        else:
            iss: Issledovaniya
            for iss in direction.issledovaniya_set.all().order_by("research__pk"):
                fwb.append(Spacer(1, 5 * mm))
                if not hosp and not is_gistology and not has_own_form_result:
                    if not plain_response:
                        if interactive_text_field:
                            fwb.append(InteractiveTextField())
                        fwb.append(Spacer(1, 2 * mm))
                    if (
                        iss.research.is_doc_refferal
                        or iss.research.is_microbiology
                        or iss.research.is_treatment
                        or iss.research.is_microbiology
                        or iss.research.is_citology
                        or iss.research.is_gistology
                        or iss.research.is_form
                    ):
                        iss_title = f"{med_certificate_title}{iss.research.title}"
                    elif iss.doc_confirmation and iss.doc_confirmation.podrazdeleniye.vaccine:
                        iss_title = "Вакцина: " + iss.research.title
                    elif iss.doc_confirmation and iss.research.is_paraclinic:
                        iss_title = "Исследование: " + iss.research.title
                    else:
                        iss_title = iss.research.title
                    if not result_title_form:
                        fwb.append(Paragraph(f"<para align='center'><font size='9'>{iss_title}</font></para>", styleBold))
                else:
                    if not is_gistology and not has_own_form_result:
                        fwb.append(Paragraph(iss.research.title + ' (' + str(dpk) + ')', styleBold))

                type_form = iss.research.result_form
                form_result = None
                if type_form != 0:
                    current_type_form = str(type_form)
                    form_result = import_string('results.forms.forms' + current_type_form[0:3] + '.form_' + current_type_form[3:5])

                if iss.research.is_microbiology:
                    fwb = microbiology_result(iss, fwb, doc)
                elif form_result:
                    has_any_signature = False
                    if with_signature_stamps and direction.total_confirmed:
                        last_time_confirm = direction.last_time_confirm()
                        document_for_sign = DirectionDocument.objects.filter(
                            direction=direction, last_confirmed_at=last_time_confirm, is_archive=False, file_type=DirectionDocument.PDF
                        ).first()
                        if document_for_sign:
                            for _ in DocumentSign.objects.filter(document=document_for_sign, sign_certificate__isnull=False):
                                has_any_signature = True
                                break
                    fwb = form_result(direction, iss, fwb, doc, leftnone, request.user, has_any_signature=has_any_signature)
                elif not protocol_plain_text:
                    fwb = structure_data_for_result(iss, fwb, doc, leftnone, med_certificate)
                else:
                    fwb = plaint_tex_for_result(iss, fwb, doc, leftnone, protocol_plain_text, med_certificate)

                recipies = Recipe.objects.filter(issledovaniye=iss).order_by('pk')
                if recipies.exists():
                    style_recipe = deepcopy(style)
                    style_recipe.leftIndent = 14
                    fwb.append(Spacer(1, 1 * mm))
                    fwb.append(Paragraph('Рецепты', styleBold))
                    fwb.append(Paragraph('<u>Наименование ЛП: форма выпуска, дозировка, количество; (способ применения)</u>', style_recipe))
                    fwb.append(Spacer(1, 0.25 * mm))
                    for r in recipies:
                        fwb.append(
                            Paragraph("<font face=\"FreeSansBold\">{}:</font> {}{}".format(r.drug_prescription, r.method_of_taking, '' if not r.comment else f'; ({r.comment})'), style_ml)
                        )

                fwb.append(Spacer(1, 2.5 * mm))
                t1 = iss.get_visit_date()
                t2 = strdate(iss.time_confirmation)
                if iss.research.is_doc_refferal:
                    napr_child = Napravleniya.objects.filter(parent=iss, cancel=False)
                    br = ""
                    if not protocol_plain_text:
                        br = '<br/>'
                    if napr_child:
                        fwb.append(Paragraph("Направления:", styleBold))
                        s_napr = ""
                        for n_child in napr_child:
                            iss_research = [s.research.title for s in Issledovaniya.objects.filter(napravleniye=n_child)]
                            iss_research_str = ', '.join(iss_research)
                            n = "<font face=\"FreeSansBold\">№{}:&nbsp;</font>".format(n_child.pk)
                            n += "{}; {} ".format(iss_research_str, br)
                            s_napr = s_napr + n + '\n'
                        fwb.append(Paragraph("{}".format(s_napr), style))

                        # Добавить Дополнительные услуги
                        add_research = Issledovaniya.objects.filter(parent_id__napravleniye=pk[0])
                        if add_research:
                            fwb.append(Spacer(1, 3 * mm))
                            fwb.append(Paragraph('Дополнительные услуги:', styleBold))
                            for i in add_research:
                                fwb.append(Paragraph('{}-{}'.format(i.research.code, i.research.title), style))

                # Добавить выписанные направления для стационарных дневников
                if iss.research.is_slave_hospital:
                    # Найти все направления, где данное исследование родитель
                    napr_child = Napravleniya.objects.filter(parent_slave_hosp=iss, cancel=False)
                    br = ""
                    if not protocol_plain_text:
                        br = '<br/>'
                    if napr_child.count() > 0:
                        fwb.append(Paragraph("Назначено:", styleBold))
                        s_napr = ""
                        for n_child in napr_child:
                            iss_research = [s.research.title for s in Issledovaniya.objects.filter(napravleniye=n_child)]
                            iss_research_str = ', '.join(iss_research)
                            n = "<font face=\"FreeSansBold\">№{}:&nbsp;</font>".format(n_child.pk)
                            n += "{}; {} ".format(iss_research_str, br)
                            s_napr = s_napr + n + '\n'
                        fwb.append(Paragraph("{}".format(s_napr), style))
                    fwb = procedural_text_for_result(iss.napravleniye, fwb, napr_child)
                    if iss.research.has_own_form_result:
                        fwb.append(Paragraph("Исполнитель: {}, {}".format(iss.doc_confirmation.get_full_fio(), iss.doc_confirmation.podrazdeleniye.title), styleBold))

                fwb.append(Spacer(1, 3 * mm))
                if not hosp and not iss.research.is_slave_hospital and not iss.research.has_own_form_result and not iss.research.is_form:
                    if iss.research.is_doc_refferal:
                        fwb.append(Paragraph("Дата осмотра: {}".format(strdate(iss.get_medical_examination())), styleBold))
                    else:
                        if not is_gistology:
                            fwb.append(Paragraph("Дата оказания услуги: {}".format(t1), styleBold))
                    if not iss.research.is_doc_refferal:
                        fwb.append(Paragraph("Дата формирования протокола: {}".format(t2), styleBold))
                elif iss.research.can_created_patient and iss.doc_confirmation.user_id == LK_USER:
                    fwb.append(Paragraph("Дата заполнения пациентом: {}".format(t2), styleBold))

                if not iss.research.has_own_form_result and not iss.research.is_form and not iss.research.is_aux and not iss.research.is_expertise:
                    if iss.doc_confirmation and iss.doc_confirmation.podrazdeleniye.vaccine:
                        fwb.append(Paragraph("Исполнитель: {}, {}".format(iss.doc_confirmation.get_full_fio(), iss.doc_confirmation.podrazdeleniye.title), styleBold))
                    else:
                        if iss.doc_confirmation:
                            doc_execute = "фельдшер" if request.user.is_authenticated and iss.doc_confirmation.has_group("Фельдшер") else "врач"
                            fwb.append(Paragraph("Исполнитель: {} {}, {}".format(doc_execute, iss.doc_confirmation.get_full_fio(), iss.doc_confirmation.podrazdeleniye.title), styleBold))
                        else:
                            fwb.append(
                                Paragraph("Исполнитель: {}, {}".format(iss.doc_confirmation_string, iss.napravleniye.hospital.short_title or iss.napravleniye.hospital.title), styleBold)
                            )

                        if iss.research.is_doc_refferal and SettingManager.get("agree_diagnos", default='True', default_type='b'):
                            fwb.append(Spacer(1, 3.5 * mm))
                            fwb.append(Paragraph("С диагнозом, планом обследования и лечения ознакомлен и согласен _________________________", style))

                        fwb.append(Spacer(1, 2.5 * mm))

        if with_signature_stamps and direction.total_confirmed:
            last_time_confirm = direction.last_time_confirm()
            document_for_sign = DirectionDocument.objects.filter(direction=direction, last_confirmed_at=last_time_confirm, is_archive=False, file_type=DirectionDocument.PDF).first()
            if document_for_sign:
                paragraphs = []
                has_thumbprints = {}
                for sign in DocumentSign.objects.filter(document=document_for_sign, sign_certificate__isnull=False):
                    if sign.sign_certificate.thumbprint in has_thumbprints:
                        continue
                    has_thumbprints[sign.sign_certificate.thumbprint] = True
                    stamp_font_size = "7"
                    stamp_lines = [
                        f'<font face="FreeSansBold" size="{stamp_font_size}">ДОКУМЕНТ ПОДПИСАН ЭЛЕКТРОННОЙ ПОДПИСЬЮ</font>',
                        f'Сертификат: {sign.sign_certificate.thumbprint}',
                        f'Владелец: {sign.sign_certificate.owner}',
                        f'Действителен с {sign.sign_certificate.valid_from.strftime("%d.%m.%Y")} по {sign.sign_certificate.valid_to.strftime("%d.%m.%Y")}',
                    ]

                    for line in range(1, len(stamp_lines)):
                        stamp_lines[line] = f'<font size="{stamp_font_size}">{stamp_lines[line]}</font>'

                    style_stamp = deepcopy(style)
                    style_stamp.borderWidth = 0.3 * mm
                    style_stamp.borderColor = colors.black
                    style_stamp.borderPadding = 1.3 * mm
                    style_stamp.borderRadius = 1.5 * mm
                    style_stamp.leading = 3 * mm
                    par = Paragraph("<br/>".join(stamp_lines), style_stamp)
                    paragraphs.append(par)

                if paragraphs:
                    if len(paragraphs) == 1:
                        paragraphs = [
                            "",
                            paragraphs[0],
                        ]

                    if len(paragraphs) % 2 == 1:
                        paragraphs.append("")

                    table_rows = []
                    for i in range(0, len(paragraphs), 2):
                        table_rows.append([paragraphs[i], paragraphs[i + 1]])

                    tw = pw
                    cw = [int(tw * 0.5), int(tw * 0.5)]
                    cw = cw + [tw - sum(cw)]
                    t = Table(table_rows, colWidths=cw)
                    style_t = TableStyle(
                        [
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 3 * mm),
                            ('TOPPADDING', (0, 0), (-1, -1), 3 * mm),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 3 * mm),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 3 * mm),
                        ]
                    )

                    t.setStyle(style_t)
                    fwb.append(Spacer(1, 2.5 * mm))
                    fwb.append(t)

        if client_prev == direction.client.individual_id and not split and not is_different_form:
            naprs.append(HRFlowable(width=pw, spaceAfter=3 * mm, spaceBefore=3 * mm, color=colors.lightgrey))
        elif client_prev > -1:
            naprs.append(PageBreak())
            has_page_break = True
            naprs.append(Macro("canvas._pageNumber=1"))
            count_pages = 0

        if len(pk) == 1:
            naprs.append(fwb)
            client_prev = direction.client.individual_id
            continue
        naprs.append(KeepTogether(fwb))
        client_prev = direction.client.individual_id

    num_card = hosp_nums

    if not hosp:
        num_card = pk[0]

    if len(pk) == 1 and has_own_form_result:
        doc.build(fwb)
    elif len(pk) == 1 and not link_result and not hosp and fwb:
        doc.build(fwb, canvasmaker=PageNumCanvas)
    elif len(pk) == 1 and not link_result and hosp:
        doc.build(fwb, canvasmaker=PageNumCanvasPartitionAll)
    elif has_page_break or SELF_WATERMARKS:
        doc.build(naprs, canvasmaker=PageNumCanvasPartitionAll)
    elif fwb:
        doc.build(naprs)

    if len(link_result) > 0:
        date_now1 = datetime.datetime.strftime(datetime.datetime.now(), "%y%m%d%H%M%S")
        date_now_str = str(random.random()) + str(date_now1)
        dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')

        buffer.seek(0)
        file_dir_l2 = None
        if buffer.getbuffer().nbytes > 0:
            file_dir_l2 = os.path.join(dir_param, date_now_str + '_dir.pdf')
            save(buffer, filename=file_dir_l2)
        file_dir = [link_f for link_f in link_result]
        if file_dir_l2:
            file_dir.append(file_dir_l2)
        writer = PdfWriter()
        pdf_all = BytesIO()
        for inpfn in file_dir:
            writer.addpages(PdfReader(inpfn).pages)
        writer.write(pdf_all)
        pdf_out = pdf_all.getvalue()
        pdf_all.close()
        response.write(pdf_out)
        buffer.close()
        if file_dir_l2:
            os.remove(file_dir_l2)
        return response

    pdf = buffer.getvalue()
    buffer.close()
    if plain_response:
        return pdf
    response.write(pdf)
    k = str(request.GET["pk"])
    slog.Log(
        key=f"{k[:497]}..." if len(k) > 497 else k,
        type=15,
        body=json.dumps({"leftnone": request.GET.get("leftnone", "0"), "split": request.GET.get("split", "1")}),
        user=request.user.doctorprofile if request.user.is_authenticated else None,
    ).save()

    return response


def draw_obj(c: canvas.Canvas, obj: int, i: int, doctorprofile):
    w, h = landscape(A4)
    napr = Napravleniya.objects.get(pk=obj)
    s = 0
    if i % 2 == 0:
        s = w / 2
    paddingx = 15
    dates = {}
    for iss in Issledovaniya.objects.filter(napravleniye=napr, time_save__isnull=False):
        if iss.time_save:
            dt = str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
            if dt not in dates.keys():
                dates[dt] = 0
            dates[dt] += 1

    if dates:
        maxdate = max(dates.items(), key=operator.itemgetter(1))[0]
    elif Issledovaniya.objects.filter(napravleniye=napr, time_confirmation__isnull=False).exists():
        maxdate = str(dateformat.format(Issledovaniya.objects.filter(napravleniye=napr, time_confirmation__isnull=False).time_confirmation, settings.DATE_FORMAT))
    else:
        maxdate = ""

    last_iss = napr.issledovaniya_set.filter(time_confirmation__isnull=False).order_by("-time_confirmation").first()

    c.setFont('FreeSans', 10)
    c.drawCentredString(w / 4 + s, h - 18, SettingManager.get("org_title"))
    c.setFont('FreeSans', 8)
    c.drawCentredString(w / 4 + s, h - 28, "(%s. %s)" % (SettingManager.get("org_address"), SettingManager.get("org_phones")))
    c.setFont('FreeSans', 10)
    c.drawString(paddingx + s, h - 42, "Результаты анализов")

    c.setFont('FreeSans', 20)
    c.drawString(paddingx + s, h - 28, "№ " + str(obj))

    c.setFont('FreeSans', 10)
    c.drawRightString(s + w / 2 - paddingx, h - 42, "Лечащий врач: " + napr.doc.get_fio())
    c.drawRightString(s + w / 2 - paddingx, h - 54, "Дата: " + maxdate)

    c.drawString(s + paddingx, h - 54, "ФИО пациента: " + napr.client.fio())
    c.drawString(s + paddingx, h - 64, "Карта: " + napr.client.number_with_type())
    c.drawCentredString(w / 4 + s, h - 64, "Пол: " + napr.client.sex)
    c.drawRightString(s + w / 2 - paddingx, h - 64, napr.client.age_s(direction=napr) + " " + "(д.р. " + str(dateformat.format(napr.client.bd(), settings.DATE_FORMAT)) + ")")
    if last_iss and last_iss.doc_confirmation:
        c.drawString(
            s + paddingx,
            18,
            "Врач (лаборант): "
            + last_iss.doc_confirmation_fio.split(" ")[0]
            + " "
            + last_iss.doc_confirmation_fio.split(" ")[1][0]
            + "."
            + last_iss.doc_confirmation_fio.split(" ")[2][0]
            + ".   ____________________   (подпись)",
        )
    else:
        c.drawString(s + paddingx, 18, "Результат не подтвержден")
    c.setFont('FreeSans', 8)

    iss_list = Issledovaniya.objects.filter(napravleniye=napr).order_by("research__pk", "research__sort_weight")

    styleSheet = getSampleStyleSheet()

    tw = w / 2 - paddingx * 2
    pos = h - 64 - paddingx / 2

    data = []
    tmp = [
        Paragraph('<font face="FreeSans" size="7">Исследование</font>', styleSheet["BodyText"]),
        Paragraph('<font face="FreeSans" size="7">Значение</font>', styleSheet["BodyText"]),
        Paragraph('<font face="FreeSans" size="7">Ед. изм.</font>', styleSheet["BodyText"]),
    ]
    if napr.client.sex.lower() == "м":
        tmp.append(Paragraph('<font face="FreeSans" size="7">Референсы (М)</font>', styleSheet["BodyText"]))
    else:
        tmp.append(Paragraph('<font face="FreeSans" size="7">Референсы (Ж)</font>', styleSheet["BodyText"]))
    data.append(tmp)
    cw = [int(tw * 0.485), int(tw * 0.164), int(tw * 0.12), int(tw * 0.232)]
    t = Table(data, colWidths=cw)
    t.setStyle(
        TableStyle(
            [
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]
        )
    )
    t.canv = c
    wt, ht = t.wrap(0, 0)
    t.drawOn(c, paddingx + s, pos - ht)
    pos = pos - ht

    for iss in iss_list:
        data = []
        fractions = directory.Fractions.objects.filter(research=iss.research).order_by("pk").order_by("sort_weight")
        if fractions.count() == 1:
            tmp = [
                Paragraph(
                    '<font face="FreeSansBold" size="7">'
                    + iss.research.title
                    + '</font>'
                    + '<font face="FreeSansBold" size="7">'
                    + ("" if not iss.comment else "<br/>" + iss.comment)
                    + "</font>",
                    styleSheet["BodyText"],
                )
            ]
            result = "не завершено"
            ref = {"": ""}
            f_units = fractions[0].get_unit_str()
            if Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).exists():
                r = Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).order_by("-pk")[0]
                ref = r.get_ref()
                result = r.value
                f_units = r.get_units()
            if not iss.doc_confirmation and iss.deferred:
                result = "отложен"
            elif iss.time_save and maxdate != str(dateformat.format(iss.time_save, settings.DATE_FORMAT)):
                result += "<br/>" + str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
            tmp.append(Paragraph('<font face="FreeSans" size="8">' + result + "</font>", styleSheet["BodyText"]))
            tmp.append(Paragraph('<font face="FreeSans" size="7">&nbsp;&nbsp;&nbsp;' + f_units + "</font>", styleSheet["BodyText"]))

            tmp.append(Paragraph('<font face="FreeSans" size="7">' + get_r(ref) + "</font>", styleSheet["BodyText"]))
            data.append(tmp)
            t = Table(data, colWidths=cw)
            t.setStyle(
                TableStyle(
                    [
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                        ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                        ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                        ('LEFTPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                    ]
                )
            )
        else:
            tmp = [
                Paragraph(
                    '<font face="FreeSansBold" size="7">'
                    + iss.research.title
                    + "</font>"
                    + '<font face="FreeSansBold" size="7">'
                    + ("" if not iss.comment else "<br/>" + iss.comment)
                    + "</font>",
                    styleSheet["BodyText"],
                ),
                '',
                '',
                '',
            ]
            data.append(tmp)
            style_t = TableStyle(
                [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                    ('INNERGRID', (0, 0), (-1, -1), 0.2, colors.black),
                    ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]
            )
            j = 0

            for f in fractions:
                j += 1
                tmp = [Paragraph('&nbsp;&nbsp;&nbsp;&nbsp;<font face="FreeSans" size="7">' + f.title + "</font>", styleSheet["BodyText"])]
                result = "не завершено"
                ref = {"": ""}
                f_units = f.get_unit_str()
                if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
                    r = Result.objects.filter(issledovaniye=iss, fraction=f).order_by("-pk")[0]
                    ref = r.get_ref()
                    result = r.value
                    f_units = r.get_units()
                if not iss.doc_confirmation and iss.deferred:
                    result = "отложен"
                elif iss.time_save and maxdate != str(dateformat.format(iss.time_save, settings.DATE_FORMAT)):
                    result += "<br/>" + str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                tmp.append(Paragraph('<font face="FreeSans" size="8">' + result + "</font>", styleSheet["BodyText"]))
                tmp.append(Paragraph('<font face="FreeSans" size="7">&nbsp;&nbsp;&nbsp;' + f_units + "</font>", styleSheet["BodyText"]))
                tmp.append(Paragraph('<font face="FreeSans" size="7">' + get_r(ref) + "</font>", styleSheet["BodyText"]))

                data.append(tmp)

            for k in range(0, 4):
                style_t.add('INNERGRID', (k, 0), (k, j), 0.01, colors.black)
                style_t.add('BOX', (k, 0), (k, j), 0.8, colors.black)

            t = Table(data, colWidths=cw)
            t.setStyle(style_t)
        t.canv = c
        wt, ht = t.wrap(0, 0)
        t.drawOn(c, paddingx + s, pos - ht)
        pos = pos - ht
    napr.save()


class TTR(Flowable):
    def __init__(self, text, fontname="FreeSans", fontsize=9, lenmin=16, domin=False):
        Flowable.__init__(self)
        self.text = text
        self.fontname = fontname
        self.fontsize = fontsize
        self.domin = domin
        self.lenmin = lenmin

    def draw(self):
        canvas = self.canv
        canvas.rotate(90)
        splits = self.text.split("\n")
        i = 0
        for s in splits:
            font = self.fontname if i > 0 else self.fontname + "Bold"
            if self.domin and len(s) > self.lenmin:
                canvas.setFont(font, self.fontsize - (len(s) - self.lenmin) / 3)
            else:
                canvas.setFont(font, self.fontsize)
            canvas.drawString(mm, (mm + i * 4 * mm) * (-1), s)
            i += 1


@login_required
def result_journal_table_print(request):
    dateo = request.GET["date"]
    date = try_strptime(
        dateo,
        formats=(
            '%d.%m.%Y',
            '%Y-%m-%d',
        ),
    )
    end_date = date + datetime.timedelta(days=1)
    onlyjson = False

    ist_f = json.loads(request.GET.get("ist_f", "[]"))
    lab = Podrazdeleniya.objects.get(pk=request.GET.get("lab_pk", request.user.doctorprofile.podrazdeleniye_id))

    iss_list = Issledovaniya.objects.filter(
        time_confirmation__gte=date, time_confirmation__lt=end_date, research__podrazdeleniye=lab, napravleniye__cancel=False, napravleniye__istochnik_f__pk__in=ist_f
    )
    patients = {}
    researches_pks = set()
    for iss in iss_list.order_by("napravleniye__client__individual__family").order_by("research__direction_id", "research__pk", "tubes__number", "research__sort_weight"):
        d = iss.napravleniye
        otd = d.doc.podrazdeleniye
        k = "%d_%s" % (otd.pk, iss.napravleniye.fin_title)
        if k not in patients:
            patients[k] = {"title": otd.title, "ist_f": iss.napravleniye.fin_title, "patients": {}}
        if d.client_id not in patients[k]["patients"]:
            patients[k]["patients"][d.client_id] = {"fio": d.client.individual.fio(short=True, dots=True), "card": d.client.number_with_type(), "history": d.history_num, "researches": {}}
        if iss.research_id not in patients[k]["patients"][d.client_id]["researches"]:
            patients[k]["patients"][d.client_id]["researches"][iss.research_id] = {"title": iss.research.title, "fractions": {}}
        for fr in iss.research.fractions_set.all():
            fres = Result.objects.filter(issledovaniye=iss, fraction=fr)
            if fres.exists():
                fres = fres.first()
                patients[k]["patients"][d.client_id]["researches"][iss.research_id]["fractions"][fr.pk] = {"title": fr.title, "result": result_normal(fres.value)}
    if onlyjson:
        return HttpResponse(json.dumps(patients), content_type="application/json")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="table_results.pdf"'

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    marginx = 6 * mm
    marginy = 10 * mm

    pw = w - marginx

    def py(y=0.0):
        y *= mm
        return h - y - marginy

    def pyb(y=0.0):
        y *= mm
        return y + marginy

    def px(x=0.0):
        return x * mm + marginx

    def pxr(x=0.0):
        x *= mm
        return pw - x + marginx

    def truncate_chars(value, max_length):
        if len(value) > max_length and "</" not in value:
            truncd_val = value[:max_length]
            if not len(value) == max_length + 1 and value[max_length + 1] != " ":
                truncd_val = truncd_val[: truncd_val.rfind(" ")]
            return truncd_val
        return value

    styleSheet = getSampleStyleSheet()
    styleSheet["BodyText"].wordWrap = 'CJK'
    stl = deepcopy(styleSheet["BodyText"])
    stl.alignment = TA_CENTER

    tw = pw - marginx * 2 - 3 * mm

    max_patients = 13
    style = TableStyle(
        [
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 0.3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (0, -2), 1.3),
            ('LEFTPADDING', (1, 0), (-1, -2), 1.3),
            ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
        ]
    )

    ordered = {}
    for f in directory.Fractions.objects.filter(
        Q(research__podrazdeleniye=lab, hide=False, research__hide=False) | Q(research__podrazdeleniye=lab, hide=False, research__hide=True, research__pk__in=researches_pks)
    ):
        k = (9999 if not f.research.direction else f.research.direction_id) * 1000000 + f.relation_id * 100000 + f.research.sort_weight * 10000 + f.sort_weight * 100 + f.pk
        d = dict(pk=f.pk, title=f.title)
        ordered[k] = d

    researches_results = collections.OrderedDict([(x[1]['pk'], [x[1]['title']]) for x in sorted(ordered.items(), key=lambda t: t[0])])

    for otd in patients.values():
        p = Paginator(list(otd["patients"].values()), max_patients)
        for pagenum in p.page_range:
            resilts_cp = deepcopy(researches_results)
            c.setFont('FreeSans', 10)
            c.rotate(90)
            c.drawString(300, -22, "Журнал: %s - %s за %s (источник - %s)" % (lab.title, otd["title"], dateo, otd["ist_f"]))
            c.rotate(-90)
            c.drawRightString(pxr(marginx / 2), pyb(-1), "Страница %d из %d" % (pagenum, p.num_pages))
            data = []
            tmp2 = [Paragraph('<font face="FreeSans" size="8">Исследования<br/><br/><br/><br/><br/><br/><br/></font>', styleSheet["BodyText"])]
            for patient in p.page(pagenum).object_list:
                tmp2.append(
                    TTR(
                        "%s\nКарта: %s\n%s" % (patient["fio"], patient["card"], "" if not patient["history"] or patient["history"] in ["None", ""] else "История: %s" % patient["history"]),
                        domin=True,
                    )
                )
                patient_rs = {}
                for research1 in patient["researches"].values():
                    for fraction in research1["fractions"].keys():
                        patient_rs[fraction] = truncate_chars(research1["fractions"][fraction]["result"], 12)
                for rr in researches_results.keys():
                    resilts_cp[rr].append(patient_rs.get(rr, ""))

            tmp2 += [""] * (max_patients + 1 - len(tmp2))
            for r in resilts_cp.keys():
                tmp = []
                for n in range(0, len(resilts_cp[r])):
                    s = 8
                    maxlen = 8
                    if n == 0:
                        maxlen = 25
                    data_str = truncate_chars(resilts_cp[r][n], 28)
                    if n == 0 and len(data_str) > maxlen:
                        s = s - (len(data_str) - maxlen) / 5
                    elif len(data_str) > maxlen:
                        s = s - (len(data_str) - maxlen) * 0.7
                    tmp.append(Paragraph('<font face="FreeSans" size="%d">%s</font>' % (s, data_str), styleSheet["BodyText"]))
                data.append(tmp)
            data.append(tmp2)
            w = 0.84 / max_patients
            cw = [int(tw * 0.2)]
            cw += [int(tw * w)] * max_patients
            t = Table(data, colWidths=cw)
            t.setStyle(style)
            t.canv = c
            wt, ht = t.wrap(0, 0)
            t.drawOn(c, px(3), py(-4) - ht)

            c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    slog.Log(key="", type=28, body=json.dumps({"date": dateo, "lab": lab.title}), user=request.user.doctorprofile).save()

    return response


@login_required
def result_journal_print(request):
    """Печать журнала подтверждений"""
    pw, ph = A4
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="journal.pdf"'
    dateo = request.GET["date"]
    date = try_strptime(
        dateo,
        formats=(
            '%d.%m.%Y',
            '%Y-%m-%d',
        ),
    )
    lab = Podrazdeleniya.objects.get(pk=request.GET.get("lab_pk", request.user.doctorprofile.podrazdeleniye_id))

    ist_f = json.loads(request.GET.get("ist_f", "[]"))
    group = int(request.GET.get("group", "-2"))

    codes = request.GET.get("codes", "-1") == "1"
    group_to_otd = request.GET.get("group_to_otd", "1") == "1"

    end_date = date + datetime.timedelta(days=1)
    iss_list = Issledovaniya.objects.filter(
        time_confirmation__gte=date, time_confirmation__lt=end_date, research__podrazdeleniye=lab, napravleniye__cancel=False, napravleniye__istochnik_f__pk__in=ist_f
    )
    group_str = "Все исследования"
    if group != -2:
        if group == -1:
            group_str = "Без группы"
            iss_list = iss_list.filter(research__groups__isnull=True)
        else:
            g = directory.ResearchGroup.objects.get(pk=group)
            group_str = g.title
            iss_list = iss_list.filter(research__groups=g)

    styles = getSampleStyleSheet()

    buffer = BytesIO()
    elements = []
    doc = SimpleDocTemplate(buffer, rightMargin=5 * mm, leftMargin=20 * mm, topMargin=15 * mm, bottomMargin=17 * mm, pagesize=A4)

    class FooterCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            canvas.Canvas.__init__(self, *args, **kwargs)
            self.pages = []

        def showPage(self):
            self.pages.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            page_count = len(self.pages)
            for page in self.pages:
                self.__dict__.update(page)
                self.draw_canvas(page_count)
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)

        def draw_canvas(self, page_count):
            self.setFont('FreeSans', 12)
            self.drawCentredString((A4[0] - 25 * mm) / 2 + 20 * mm, ph - 12 * mm, "%s - %s, %s" % (request.user.doctorprofile.podrazdeleniye.title, group_str, dateo))
            self.saveState()
            if not codes:
                self.setStrokeColorRGB(0, 0, 0)
                self.setLineWidth(0.5)
                self.line(20 * mm, 22, A4[0] - 5 * mm, 22)
            self.setFont('FreeSans', 8)
            self.drawRightString(A4[0] - 8 * mm, 16, "Страница %s из %s" % (self._pageNumber, page_count))
            if codes:
                self.drawCentredString(A4[0] / 2, 16, "Проверил: ____________________________ (подпись)")
            if codes:
                self.drawString(23 * mm, 16, "Распечатано: " + str(dateformat.format(timezone.now(), settings.DATE_FORMAT)))
                self.drawString(23 * mm, 8, "Распечатал: " + request.user.doctorprofile.get_fio(dots=True))
            else:
                self.drawString(23 * mm, 16, dateo)
            self.restoreState()

    styles["Normal"].fontName = "FreeSans"
    styles["Normal"].fontSize = 12

    otds = collections.defaultdict(dict)
    clientresults = {}
    for iss in iss_list.order_by("napravleniye__client__individual__family"):
        key = iss.napravleniye.client.individual.family + "-" + str(iss.napravleniye.client_id)
        if key not in clientresults.keys():
            clientresults[key] = {
                "directions": {},
                "ist_f": iss.napravleniye.fin_title,
                "fio": iss.napravleniye.client.individual.fio(short=True, dots=True)
                + "<br/>Карта: "
                + iss.napravleniye.client.number_with_type()
                + (("<br/>История: " + iss.napravleniye.history_num) if iss.napravleniye.history_num and iss.napravleniye.history_num != "" else ""),
            }
        if iss.napravleniye_id not in clientresults[key]["directions"]:
            clientresults[key]["directions"][iss.napravleniye_id] = {"researches": {}}
        if iss.research_id not in clientresults[key]["directions"][iss.napravleniye_id]["researches"]:
            clientresults[key]["directions"][iss.napravleniye_id]["researches"][iss.research_id] = {"title": iss.research.title, "res": [], "code": iss.research.code, "fail": False}

        for fr in iss.research.fractions_set.all():
            fres = Result.objects.filter(issledovaniye=iss, fraction=fr)
            if fres.exists():
                tres = {"value": fr.title + ": " + fres.first().value, "v": fres.first().value, "code": fr.code, "title": fr.title, "fail": False}
                if codes:
                    tmpval = tres["v"].lower().strip()
                    tres["fail"] = not (
                        all([x not in tmpval for x in ["забор", "тест", "неправ", "ошибк", "ошибочный", "кров", "брак", "мало", "недостаточно", "реактив"]])
                        and tmpval != ""
                        and tmpval != "-"
                    )
                    if tmpval == "":
                        tres["v"] = "пустой результат"
                    if tres["fail"]:
                        clientresults[key]["directions"][iss.napravleniye_id]["researches"][iss.research_id]["fail"] = True
                clientresults[key]["directions"][iss.napravleniye_id]["researches"][iss.research_id]["res"].append(tres)
        if not group_to_otd:
            otds[iss.napravleniye.get_doc_podrazdeleniye_title() + " - " + iss.napravleniye.fin_title][key] = clientresults[key]
        else:
            otds[iss.napravleniye.fin_title][key] = clientresults[key]
    j = 0

    for otd in otds.keys():
        data = []
        if not codes:
            data = [[Paragraph('<font face="FreeSans" size="12">' + otd + "</font>", styles["Normal"])]]
            data_header = ["№", "ФИО", "Направление: Результаты"]
            tmp = []
            for v in data_header:
                tmp.append(Paragraph(str(v), styles["Normal"]))
            data.append(tmp)
        else:
            data.append(
                [
                    Paragraph("№", styles["Normal"]),
                    Paragraph("Пациент", styles["Normal"]),
                    Paragraph('<font face="cour" size="9">' + "Код".ljust(16, '.') + "исследование" + "</font>", styles["Normal"]),
                ]
            )

        clientresults = collections.OrderedDict(sorted(otds[otd].items()))
        for cleint_pk in clientresults.keys():
            client = clientresults[cleint_pk]
            data_tmp = ""
            for dir_pk in client["directions"].keys():
                dir = client["directions"][dir_pk]
                if not codes:
                    data_tmp += "Направление: " + str(dir_pk) + " | "
                    for research_pk in dir["researches"].keys():
                        research_obj = dir["researches"][research_pk]
                        if len(research_obj["res"]) == 1:
                            data_tmp += research_obj["res"][0]["value"]
                        else:
                            data_tmp += research_obj["title"] + ":" + "; ".join([x["value"] for x in research_obj["res"]])
                        data_tmp += "<br/>"
                else:
                    for research_pk in dir["researches"].keys():
                        research_obj = dir["researches"][research_pk]
                        if research_obj["code"] != '':
                            if research_obj["fail"]:
                                for code_res in research_obj["code"].split(";"):
                                    data_tmp += "%s%s%s<br/>" % (Truncator("Ошибка результ").chars(15).ljust(16, '.'), code_res, Truncator(research_obj["title"]).chars(30))
                            else:
                                for code_res in research_obj["code"].split(";"):
                                    data_tmp += "%s%s<br/>" % (code_res.ljust(16, '.'), Truncator(research_obj["title"]).chars(48))
                        else:
                            for res in research_obj["res"]:
                                if res["fail"]:
                                    for code_res in res["code"].split(";"):
                                        data_tmp += "%s%s%s<br/>" % (Truncator(res["v"]).chars(15).ljust(16, '.'), code_res.ljust(16, '.'), Truncator(res["title"]).chars(32))
                                else:
                                    for code_res in res["code"].split(";"):
                                        data_tmp += "%s%s<br/>" % (code_res.ljust(16, '.'), Truncator(res["title"]).chars(48))
            j += 1
            if not codes:
                data.append(
                    [
                        Paragraph('<font face="FreeSans" size="8">' + str(j) + "</font>", styles["Normal"]),
                        Paragraph('<font face="FreeSans" size="8">' + client["fio"] + "</font>", styles["Normal"]),
                        Paragraph('<font face="FreeSans" size="8">' + data_tmp + "</font>", styles["Normal"]),
                    ]
                )
            else:
                data.append(
                    [
                        Paragraph('<font face="FreeSans" size="8">' + str(j) + "</font>", styles["Normal"]),
                        Paragraph('<font face="FreeSans" size="8">' + client["fio"] + "<br/>" + client["ist_f"] + "</font>", styles["Normal"]),
                        Paragraph('<font face="cour" size="9">' + data_tmp + "</font>", styles["Normal"]),
                    ]
                )
        sta = [
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 2), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, 1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, 1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 2), (-1, -1), 1),
        ]
        if not codes:
            sta.append(
                (
                    'SPAN',
                    (0, 0),
                    (-1, 0),
                )
            )
        st = TableStyle(sta)
        tw = pw - 25 * mm
        t = Table(data, colWidths=[tw * 0.05, tw * 0.19, tw * 0.76])
        t.setStyle(st)
        elements.append(t)
        elements.append(PageBreak())
    doc.multiBuild(elements, canvasmaker=FooterCanvas)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response


def get_r(ref) -> str:
    if isinstance(ref, str):
        r = json.loads(ref)
    else:
        r = ref
    tmp = []
    for k in r.keys():
        if len(r[k]) > 0:
            if k == "Все" and len(r) == 1:
                tmp.append(r[k])
            else:
                tmp.append(k + " : " + r[k])
    t2 = []
    for ttt in tmp:
        if ":" not in ttt:
            t2.append(ttt)
        else:
            t2.append(ttt)

    s = "<br/>".join(t2)
    if s == " : ":
        s = ""
    return s


@csrf_exempt
@login_required
def result_get(request):
    """Получение результатов для исследования"""
    result = {"results": {}, "norms": {}, "refs": {}, "comment": ""}
    if request.method == "GET":
        issledovaniye = Issledovaniya.objects.get(pk=int(request.GET["iss_id"]))
        results = Result.objects.filter(issledovaniye=issledovaniye)
        for v in results:
            result["results"][str(v.fraction_id)] = v.value
            result["norms"][str(v.fraction_id)] = v.get_is_norm(recalc=True)[0]
            result["refs"][str(v.fraction_id)] = v.get_ref(full=True)
        if issledovaniye.lab_comment:
            result["comment"] = issledovaniye.lab_comment.strip()
    return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
@login_required
def get_day_results(request):
    if request.method == "POST":
        researches = json.loads(request.POST["researches"])
        day = request.POST["date"]
        otd = request.POST.get("otd", "-1")
    else:
        researches = json.loads(request.GET["researches"])
        day = request.GET["date"]
        otd = request.GET.get("otd", "-1")

    day1 = try_strptime(
        day,
        formats=(
            '%d.%m.%Y',
            '%Y-%m-%d',
        ),
    )
    day2 = day1 + datetime.timedelta(days=1)
    directions = collections.defaultdict(list)
    otd = int(otd)

    if otd == -1:
        for dir in Napravleniya.objects.filter(issledovaniya__time_confirmation__range=(day1, day2), issledovaniya__research_id__in=researches).order_by("client__pk"):
            if dir.pk not in directions[dir.get_doc_podrazdeleniye_title()]:
                directions[dir.get_doc_podrazdeleniye_title()].append(dir.pk)
    else:
        for dir in Napravleniya.objects.filter(issledovaniya__time_confirmation__range=(day1, day2), issledovaniya__research_id__in=researches, doc__podrazdeleniye__pk=otd).order_by(
            "client__pk"
        ):
            if dir.pk not in directions[dir.get_doc_podrazdeleniye_title()]:
                directions[dir.get_doc_podrazdeleniye_title()].append(dir.pk)

    return HttpResponse(json.dumps({"directions": directions}), content_type="application/json")


@csrf_exempt
@login_required
def results_search_directions(request):
    if request.method == "POST":
        data = request.POST
    else:
        data = request.GET

    period = json.loads(data.get("period", "{}"))
    rq_researches = json.loads(data.get("researches", "[]"))
    type = period.get("type", "d")
    type_patient = int(data.get("type_patient", "-1"))
    query = ' '.join(data.get("query", "").strip().split())
    perform_norms = data.get("perform_norms", "false").lower() == "true"
    archive = data.get("archive", "false").lower() == "true"
    grouping = data.get("grouping", "patient")
    sorting = data.get("sorting", "confirm-date")
    sorting_direction = data.get("sorting_direction", "up")
    otd_search = int(data.get("otd", "-1"))
    doc_search = data.get("doc", "-1")
    doc_search = -1 if not doc_search.isdigit() else int(doc_search)
    offset = data.get("offset", "0")
    offset = 0 if not offset.isdigit() else int(offset)
    on_page = SettingManager.get("search_rows_on_page", "100", "i")

    if type not in ["d", "m", "y"]:
        type = "d"
        period = {}

    filter_type = "any"
    family = ""
    name = ""
    twoname = ""
    bdate = ""

    if query.isdigit() or bool(re.compile(r'^([a-zA-Z0-9]{14,17})$').match(query)):
        filter_type = "card_number"
    elif bool(re.compile(r'^([a-zA-Zа-яА-ЯёЁ]+)( [a-zA-Zа-яА-ЯёЁ]+)?( [a-zA-Zа-яА-ЯёЁ]+)?( \d{2}\.\d{2}\.\d{4})?$').match(query)):
        filter_type = "fio"
        split = query.split()
        if len(split) > 0:
            family = split[0]
        if len(split) > 1:
            name = split[1]
        if len(split) > 2:
            twoname = split[2]
        if len(split) > 2:
            twoname = split[2]
        if len(split) > 3:
            spq = split[3].split(".")
            bdate = "%s-%s-%s" % (spq[2], spq[1], spq[0])
    elif bool(re.compile(r'^(.)(.)(.)(\d{2})(\d{2})(\d{4})$').match(query)):
        filter_type = "fio_short"
        family = query[0:1]
        name = query[1:2]
        twoname = query[2:3]
        bdate = "%s-%s-%s" % (query[7:11], query[5:7], query[3:5])

    try:
        if type == "d":
            day = period.get("date", "01.01.2015")
            day1 = datetime.date(int(day.split(".")[2]), int(day.split(".")[1]), int(day.split(".")[0]))
            day2 = day1 + datetime.timedelta(days=1)
        elif type == "m":
            month = int(period.get("month", "0")) + 1
            next_m = month + 1 if month < 12 else 1
            year = int(period.get("year", "2015"))
            next_y = year + 1 if next_m == 1 else year
            day1 = datetime.date(year, month, 1)
            day2 = datetime.date(next_y, next_m, 1)
        else:
            year = int(period.get("year", "2015"))
            day1 = datetime.date(year, 1, 1)
            day2 = datetime.date(year + 1, 1, 1)
    except (ValueError, IndexError, OverflowError):
        return JsonResponse({"rows": [], "grouping": grouping, "len": 0, "next_offset": 0, "all_rows": 0, "error_message": "Некорректная дата"})
    collection = Napravleniya.objects.filter(issledovaniya__time_confirmation__range=(day1, day2), issledovaniya__time_confirmation__isnull=False, client__is_archive=archive)
    if len(rq_researches) > 0:
        collection = collection.filter(issledovaniya__research__pk__in=rq_researches)

    if otd_search != -1:
        collection = collection.filter(doc__podrazdeleniye__pk=otd_search)

    if doc_search != -1:
        collection = collection.filter(doc__pk=doc_search)

    client_base = None
    if type_patient != -1:
        client_base = CardBase.objects.get(pk=type_patient)
    if filter_type == "fio" or filter_type == "fio_short":
        collection = collection.filter(client__individual__family__istartswith=family, client__individual__name__istartswith=name, client__individual__patronymic__istartswith=twoname)
        if bdate != "":
            collection = collection.filter(client__individual__birthday=bdate)

    if filter_type == "card_number":
        if type_patient != -1:
            qq = Q(client__base=client_base, client__number__iexact=query)
            for cb in CardBase.objects.filter(assign_in_search=client_base):
                qq |= Q(client__individual__card__number__iexact=query, client__base=cb)
            collection = collection.filter(qq)
        else:
            collection = collection.filter(client__number__iexact=query)
    elif client_base is not None:
        collection = collection.filter(client__base=client_base)

    rows = collections.OrderedDict()
    n = 0
    directions_pks = []
    if sorting_direction == "up":
        sort_types = {
            "confirm-date": ("issledovaniya__time_confirmation",),
            "patient": (
                "issledovaniya__time_confirmation",
                "client__individual__family",
                "client__individual__name",
                "client__individual__patronymic",
            ),
        }
    else:
        sort_types = {
            "confirm-date": ("-issledovaniya__time_confirmation",),
            "patient": (
                "-issledovaniya__time_confirmation",
                "-client__individual__family",
                "-client__individual__name",
                "-client__individual__patronymic",
            ),
        }
    filtered = []
    cnt = 0
    for direction in collection.order_by(*sort_types.get(sorting, ("issledovaniya__time_confirmation",))):
        if direction.pk in directions_pks or not direction.is_all_confirm():
            continue
        datec = str(
            dateformat.format(direction.issledovaniya_set.filter(time_confirmation__isnull=False).order_by("-time_confirmation").first().time_confirmation.date(), settings.DATE_FORMAT)
        )
        key = "%s_%s@%s" % (datec, direction.client.number, direction.client.base_id)
        if key not in rows:
            if n - offset >= on_page or key in filtered:
                if key not in filtered:
                    filtered.append(key)
                    cnt += 1
                continue
            cnt += 1
            n += 1
            if n <= offset:
                filtered.append(key)
                continue
            rows[key] = {
                "fio": direction.client.individual.fio(),
                "birthdate": direction.client.individual.age_s(direction=direction),
                "sex": direction.client.individual.sex,
                "cardnum": direction.client.number,
                "type": direction.client.base.title,
                "date": datec,
                "directions_cnt": 0,
                "directions": [],
                "is_normal": "none",
            }
        rows[key]["directions_cnt"] += 1
        researches = []

        row_normal = "none"
        iss_dir = direction.issledovaniya_set.all()
        if len(rq_researches) > 0:
            iss_dir = iss_dir.filter(research__pk__in=rq_researches)

        for r in iss_dir:
            if not r.research.is_paraclinic and not r.research.is_doc_refferal and not r.research.is_form:
                if not Result.objects.filter(issledovaniye=r).exists():
                    continue
                tmp_r = {"title": r.research.title}
                is_normal = "none"
                if perform_norms:
                    for res_row in Result.objects.filter(issledovaniye=r):
                        tmp_normal = res_row.get_is_norm(recalc=True)
                        if is_normal != "not_normal":
                            if is_normal == "maybe":
                                if tmp_normal == "not_normal":
                                    is_normal = tmp_normal
                            else:
                                is_normal = tmp_normal
                        if row_normal != "not_normal":
                            if row_normal == "maybe":
                                if tmp_normal == "not_normal":
                                    row_normal = tmp_normal
                            else:
                                row_normal = tmp_normal
                        if is_normal == "not_normal":
                            break
                tmp_r["is_normal"] = is_normal
                researches.append(tmp_r)
            else:
                if not ParaclinicResult.objects.filter(issledovaniye=r).exists():
                    continue
                tmp_r = {"title": r.research.title, "is_normal": "none"}
                researches.append(tmp_r)
        if len(researches) == 0:
            continue
        pod = direction.issledovaniya_set.first().research.get_podrazdeleniye()
        tmp_dir = {
            "pk": direction.pk,
            "laboratory": "Консультации" if not pod else pod.title,
            "otd": ("" if not direction.imported_org else direction.imported_org.title) if direction.imported_from_rmis else direction.get_doc_podrazdeleniye_title(),
            "doc": "" if direction.imported_from_rmis else direction.doc.get_fio(),
            "researches": researches,
            "is_normal": row_normal,
        }

        if rows[key]["is_normal"] != "not_normal":
            if rows[key]["is_normal"] == "maybe":
                if row_normal == "not_normal":
                    rows[key]["is_normal"] = row_normal
            else:
                rows[key]["is_normal"] = row_normal
        rows[key]["directions"].append(tmp_dir)
        directions_pks.append(direction.pk)
    if offset == 0:
        slog.Log(
            key="",
            type=27,
            body=json.dumps(
                {
                    "query": query,
                    "period": period,
                    "type_patient": type_patient,
                    "perform_norms": perform_norms,
                    "grouping": grouping,
                    "otd_search": otd_search,
                    "doc_search": doc_search,
                    "researches": rq_researches,
                }
            ),
            user=request.user.doctorprofile,
        ).save()

    return JsonResponse({"rows": rows, "grouping": grouping, "len": n - offset, "next_offset": n, "all_rows": cnt, "error_message": ""})


@login_required
def results(request):
    return redirect('/ui/laboratory/results')
