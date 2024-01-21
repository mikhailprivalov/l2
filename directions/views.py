import os.path
import uuid
from datetime import date, datetime
from io import BytesIO

import simplejson as json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.http import HttpResponse, JsonResponse
from django.utils import dateformat
from django.utils.text import Truncator
from django.views.decorators.csrf import csrf_exempt
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import eanbc, qr, createBarcodeDrawing
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A6
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfdoc
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from transliterate import translit

import directory.models as directory
from directions.sql_func import get_researches_by_number_directions
from users.models import DoctorProfile
from api.sql_func import search_case_by_card_date
from hospitals.models import Hospitals
import slog.models as slog
from appconf.manager import SettingManager
from directions.models import Napravleniya, Issledovaniya, TubesRegistration, DirectionParamsResult, IstochnikiFinansirovaniya
from laboratory.decorators import logged_in_or_token
from laboratory.settings import FONTS_FOLDER, PRINT_ADDITIONAL_PAGE_DIRECTION_FIN_SOURCE, PRINT_APPENDIX_PAGE_DIRECTION
from laboratory.utils import strtime, strdate
from podrazdeleniya.models import Podrazdeleniya
from utils import xh
from utils.dates import try_parse_range, normalize_dots_date
from django.utils.module_loading import import_string

from utils.matrix import transpose
from utils.xh import save_tmp_file, translation_number_from_decimal
from users.models import User

w, h = A4


@login_required
def gen_pdf_execlist(request):
    """
    Лист исполнения
    :param request:
    :return:
    """
    type = int(request.GET["type"])
    date_start = request.GET["datestart"]
    date_end = request.GET["dateend"]
    if type != 2:
        date_start, date_end = try_parse_range(date_start, date_end)

    researches = json.loads(request.GET["researches"])
    xsize = 8
    ysize = 8
    from reportlab.lib.pagesizes import landscape

    lw, lh = landscape(A4)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="execlist.pdf"'
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=10, leftMargin=80, topMargin=10, bottomMargin=0)
    doc.pagesize = landscape(A4)

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os.path
    from django.utils.text import Truncator

    pdfmetrics.registerFont(TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))
    elements = []
    for res in directory.Researches.objects.filter(pk__in=researches):
        if type != 2:
            iss_list = Issledovaniya.objects.filter(
                tubes__doc_recive_id__isnull=False, tubes__time_recive__range=(date_start, date_end), time_confirmation__isnull=True, research__pk=res.pk, deferred=False
            ).order_by('tubes__time_recive')
        else:
            iss_list = Issledovaniya.objects.filter(research__pk=res.pk, deferred=True, time_confirmation__isnull=True, tubes__doc_recive__isnull=False).order_by('tubes__time_recive')

        if iss_list.count() == 0:
            # if not hb:
            #    elements.append(PageBreak())
            continue
        pn = 0
        tubes = []
        for iss in iss_list:
            for tube in iss.tubes.all():
                # if not tube.doc_recive:
                #    pass
                # else:
                tubes.append(tube)
        if len(tubes) == 0:
            continue
        pn += 1
        p = Paginator(tubes, xsize * (ysize - 1))

        for pg_num in p.page_range:
            pg = p.page(pg_num)
            data = [[]]
            for j in range(0, xsize):
                data[-1].append("<br/><br/><br/><br/><br/>")
            inpg = Paginator(pg.object_list, xsize)
            for inpg_num in inpg.page_range:
                inpg_o = inpg.page(inpg_num)
                data.append([])
                for inobj in inpg_o.object_list:
                    data[-1].append(
                        inobj.issledovaniya_set.first().napravleniye.client.individual.fio(short=True, dots=True)
                        + ", "
                        + inobj.issledovaniya_set.first().napravleniye.client.individual.age_s(iss=inobj.issledovaniya_set.first())
                        + "<br/>№ напр.: "
                        + str(inobj.issledovaniya_set.first().napravleniye_id)
                        + "<br/>"
                        + "№ ёмкости: "
                        + str(inobj.number)
                        + "<br/>"
                        + Truncator(inobj.issledovaniya_set.first().napravleniye.doc.podrazdeleniye.title).chars(19)
                        + "<br/><br/>"
                    )
            if len(data) < ysize:
                for i in range(len(data), ysize):
                    data.append([])
            for y in range(0, ysize):
                if len(data[y]) < xsize:
                    for i in range(len(data[y]), xsize):
                        data[y].append("<br/><br/><br/><br/><br/>")
            style = TableStyle(
                [
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.black),
                    ('BOX', (0, 0), (-1, -1), 0.3, colors.black),
                ]
            )

            s = getSampleStyleSheet()
            s = s["BodyText"]
            s.wordWrap = 'LTR'
            data = transpose(data)
            data2 = [[Paragraph('<font face="OpenSans" size="7">' + cell + "</font>", s) for cell in row] for row in data]
            tw = lw - 90
            t = Table(data2, colWidths=[int(tw / 8), int(tw / 8), int(tw / 8), int(tw / 8), int(tw / 8), int(tw / 8), int(tw / 8), int(tw / 8)])
            t.setStyle(style)
            st = ""
            if type == 2:
                st = ", отложенные"
            elements.append(Paragraph('<font face="OpenSans" size="10">' + res.title + st + ", " + str(pg_num) + " стр<br/><br/></font>", s))
            elements.append(t)
            elements.append(PageBreak())

    doc.build(elements)
    pdf = buffer.getvalue()  # Получение данных из буфера
    buffer.close()  # Закрытие буфера
    response.write(pdf)  # Запись PDF в ответ
    return response


@logged_in_or_token
def gen_pdf_dir(request):
    """Генерация PDF направлений"""
    direction_id = json.loads(request.GET.get("napr_id", '[]'))
    appendix = request.GET.get("appendix", 0)
    narrow_format = request.GET.get("narrowFormat", "0") == "1"

    req_from_additional_pages = False
    req_from_appendix_pages = False
    if direction_id == []:
        request_direction_id = json.loads(request.body)
        direction_id = request_direction_id.get("napr_id", "[]")
        req_from_additional_pages = request_direction_id.get("from_additional_pages", False)
        req_from_appendix_pages = request_direction_id.get("from_appendix_pages", False)
    if SettingManager.get("pdf_auto_print", "true", "b") and not request.GET.get('normis') and not request.GET.get('embedded'):
        pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:true,bSilent:false,bShrinkToFit:true}\);)>>'

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="directions.pdf"'

    pdfmetrics.registerFont(TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSansBold', os.path.join(FONTS_FOLDER, 'OpenSans-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('TimesNewRoman', os.path.join(FONTS_FOLDER, 'TimesNewRoman.ttf')))
    dn = (
        Napravleniya.objects.filter(pk__in=direction_id)
        .prefetch_related(
            Prefetch(
                'issledovaniya_set',
                queryset=Issledovaniya.objects.all().select_related('research', 'research__podrazdeleniye', 'localization', 'service_location').prefetch_related('research__fractions_set'),
            ),
            Prefetch('directionparamsresult_set', queryset=DirectionParamsResult.objects.all()),
        )
        .select_related(
            'client',
            'client__base',
            'client__individual',
            'parent',
            'parent__research',
            'doc_who_create',
            'doc_who_create__podrazdeleniye',
            'doc',
            'doc__podrazdeleniye',
            'imported_org',
            'istochnik_f',
        )
        .order_by('pk')
    )

    if narrow_format:
        from directions.forms.forms580 import form_01 as form_80
        fc = form_80(
            request_data={
                **dict(request.GET.items()),
                "user": request.user,
                "card_pk": dn[0].client_id,
                "hospital": request.user.doctorprofile.get_hospital() if hasattr(request.user, "doctorprofile") else Hospitals.get_default_hospital(),
            }
        )
        if fc:
            response.write(fc)
            return response

    donepage = dn.exclude(issledovaniya__research__direction_form=0)
    donepage = donepage.exclude(external_organization__isnull=False)
    external_org_form = dn.filter(external_organization__isnull=False)

    buffer = BytesIO()
    count_direction = len(direction_id)
    format_A6 = SettingManager.get("format_A6", default='False', default_type='b') and count_direction == 1 and donepage.count() == 0
    page_size = A6 if format_A6 else A4
    c = canvas.Canvas(buffer, pagesize=page_size)
    c.setTitle('Направления {}'.format(', '.join([str(x) for x in direction_id])))

    # для внешних организацй
    external_print_form = False
    if external_org_form.count() > 0:
        external_print_form = True
        f = import_string('directions.forms.forms' + '380' + '.form_' + '05')
        c = canvas.Canvas(buffer, pagesize=A4)
        f(c, external_org_form)

    ddef = dn.filter(issledovaniya__research__direction_form=0, external_organization=None).distinct()
    p = Paginator(ddef, 4)  # Деление списка направлений по 4
    instructions = []
    has_def = ddef.count() > 0
    def_form_print = False
    if has_def and not format_A6:
        if external_print_form:
            def_form_print = True
            c.showPage()
        framePage(c)
    for pg_num in p.page_range:
        pg = p.page(pg_num)
        i = 4  # Номер позиции направления на странице (4..1)
        for n_ob in pg.object_list:  # Перебор номеров направлений на странице
            def_form_print = True
            print_direction(c, i, n_ob, format_A6)  # Вызов функции печати направления на указанную позицию
            instructions += n_ob.get_instructions()
            i -= 1
        if pg.has_next():  # Если есть следующая страница
            c.showPage()  # Создание новой страницы
            framePage(c)  # Рисование разделительных линий для страницы

    if donepage.count() > 0 and has_def:
        if external_print_form or def_form_print:
            c.showPage()
    n = 0
    cntn = donepage.count()
    for d in donepage:
        n += 1
        iss = d.issledovaniya_set.all()
        if not iss.exists():
            continue
        form = iss[0].research.direction_form
        if form != 0 and not d.external_organization:
            current_type_form = str(form)
            f = import_string('directions.forms.forms' + current_type_form[0:3] + '.form_' + current_type_form[3:5])
            f(c, d)
        if n != cntn:
            c.showPage()

    instructions_pks = []
    instructions_filtered = []
    for i in instructions:
        if i["pk"] in instructions_pks:
            continue
        instructions_pks.append(i["pk"])
        instructions_filtered.append(i)
    if len(instructions_filtered) > 0:
        s = getSampleStyleSheet()
        s = s["BodyText"]
        s.wordWrap = 'LTR'
        c.showPage()
        tx = '<font face="OpenSansBold" size="10">Памятка пациенту по проведению исследований</font>\n'
        for i in instructions_filtered:
            tx += '--------------------------------------------------------------------------------------\n<font face="OpenSansBold" size="10">{}</font>\n<font face="OpenSans" size="10">&nbsp;&nbsp;&nbsp;&nbsp;{}\n</font>'.format(  # noqa: E501
                i["title"], i["text"]
            )
        data = [[Paragraph(tx.replace("\n", "<br/>"), s)]]

        t = Table(data, colWidths=[w - 30 * mm])
        t.setStyle(
            TableStyle(
                [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                    ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.25, colors.white),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 0.5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]
            )
        )
        t.canv = c
        wt, ht = t.wrap(0, 0)
        t.drawOn(c, 15 * mm, h - 15 * mm - ht)
        c.showPage()

    c.save()  # Сохранение отрисованного на PDF
    pdf = buffer.getvalue()  # Получение данных из буфера

    # Проверить, если единый источник финансирвоания у направлений и title==платно, тогода печатать контракт
    fin_ist_set = set()
    card_pk_set = set()
    setup_print_additional_page_direction = {}
    for n in dn:
        if n.istochnik_f:
            fin_ist_set.add(n.istochnik_f)
        card_pk_set.add(n.client_id)
        iss = Issledovaniya.objects.filter(napravleniye=n)
        for i in iss:
            if i.research.podrazdeleniye and i.research.podrazdeleniye.print_additional_page_direction:
                setup_print_additional_page_direction = json.loads(i.research.podrazdeleniye.print_additional_page_direction)
            if i.research.print_additional_page_direction:
                setup_print_additional_page_direction = json.loads(i.research.print_additional_page_direction)

    internal_type = n.client.base.internal_type

    fin_status = None
    fin_title = None
    if fin_ist_set:
        fin_title = fin_ist_set.pop().title.lower()
        if fin_title == 'платно':
            fin_status = True

    if request.GET.get("contract") and internal_type:
        if request.GET["contract"] == '1' and SettingManager.get("direction_contract", default='False', default_type='b'):
            if len(card_pk_set) == 1 and fin_status:
                new_form_contract = SettingManager.get("new_form_contract", default='True', default_type='b')
                if new_form_contract:
                    from forms.forms102 import form_02 as f_contract
                else:
                    from forms.forms102 import form_01 as f_contract

                fc = f_contract(
                    request_data={
                        **dict(request.GET.items()),
                        "user": request.user,
                        "card_pk": card_pk_set.pop(),
                        "hospital": request.user.doctorprofile.get_hospital() if hasattr(request.user, "doctorprofile") else Hospitals.get_default_hospital(),
                    }
                )
                if fc and not req_from_appendix_pages:
                    pdf_out = exteranl_add_pdf(fc, buffer, n)
                    response.write(pdf_out)
                    return response

    if (PRINT_ADDITIONAL_PAGE_DIRECTION_FIN_SOURCE.get(fin_title, None) or setup_print_additional_page_direction.get(fin_title, None)) and not req_from_additional_pages:
        type_additional_pdf = PRINT_ADDITIONAL_PAGE_DIRECTION_FIN_SOURCE.get(fin_title)
        if setup_print_additional_page_direction.get(fin_title, None):
            type_additional_pdf = setup_print_additional_page_direction.get(fin_title)
        additional_page = import_string('forms.forms112.' + type_additional_pdf.split(".")[0])
        if additional_page:
            fc = additional_page(
                request_data={
                    **dict(request.GET.items()),
                    "user": request.user,
                    "card_pk": card_pk_set.pop(),
                    "hospital": request.user.doctorprofile.get_hospital() if hasattr(request.user, "doctorprofile") else Hospitals.get_default_hospital(),
                    "type_additional_pdf": type_additional_pdf.split(".")[1],
                    "fin_title": fin_title,
                }
            )
            if fc:
                pdf_out = exteranl_add_pdf(fc, buffer, n)
                response.write(pdf_out)
                return response

    if appendix == '1' and PRINT_APPENDIX_PAGE_DIRECTION and not req_from_appendix_pages:
        type_additional_pdf = PRINT_APPENDIX_PAGE_DIRECTION.get(fin_title)
        if type_additional_pdf:
            additional_page = import_string('forms.forms112.' + type_additional_pdf.split(".")[0])
            fc = additional_page(
                request_data={
                    **dict(request.GET.items()),
                    "user": request.user,
                    "card_pk": card_pk_set.pop(),
                    "hospital": request.user.doctorprofile.get_hospital() if hasattr(request.user, "doctorprofile") else Hospitals.get_default_hospital(),
                    "type_additional_pdf": type_additional_pdf.split(".")[1],
                    "fin_title": fin_title,
                }
            )
            if fc:
                pdf_out = exteranl_add_pdf(fc, buffer, n)
                response.write(pdf_out)
                return response

    buffer.close()  # Закрытие буфера
    response.write(pdf)  # Запись PDF в ответ
    return response


def exteranl_add_pdf(fc_cur, buffer_cur, n_cl):
    fc_buf = BytesIO()
    fc_buf.write(fc_cur)
    fc_buf.seek(0)
    buffer_cur.seek(0)
    from pdfrw import PdfReader, PdfWriter

    today = datetime.now()
    date_now1 = datetime.strftime(today, "%y%m%d%H%M%S%f")[:-3]
    date_now_str = str(n_cl.client_id) + str(date_now1)
    dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
    file_dir = os.path.join(dir_param, date_now_str + '_dir.pdf')
    file_contract = os.path.join(dir_param, date_now_str + '_contract.pdf')
    save_tmp_file(buffer_cur, filename=file_dir)
    save_tmp_file(fc_buf, filename=file_contract)
    pdf_all = BytesIO()
    inputs = [file_contract] if SettingManager.get("only_contract", default='False', default_type='b') else [file_dir, file_contract]
    writer = PdfWriter()
    for inpfn in inputs:
        writer.addpages(PdfReader(inpfn).pages)
    writer.write(pdf_all)
    pdf_out_cur = pdf_all.getvalue()
    pdf_all.close()
    os.remove(file_dir)
    os.remove(file_contract)
    buffer_cur.close()
    fc_buf.close()
    return pdf_out_cur


def framePage(canvas):
    # Деление страницы на 4 зоны линиями
    canvas.setFont('Times-Roman', 20)
    canvas.setStrokeColorRGB(0, 0, 0)
    canvas.setLineWidth(1)
    canvas.line(w / 2, 0, w / 2, h)
    canvas.line(0, h / 2, w, h / 2)


def print_direction(c: Canvas, n, dir: Napravleniya, format_a6: bool = False):
    xn, yn = 0, 0
    if not format_a6:
        if n % 2 != 0:
            xn = 1
        if n > 2:
            yn = 1

    barcode = eanbc.Ean13BarcodeWidget(dir.pk + 460000000000, humanReadable=0, barHeight=17)
    bounds = barcode.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    d = Drawing(width, height)
    d.add(barcode)
    paddingx = 15
    ac = dir.is_all_confirm()
    canc = dir.cancel
    visit = dir.visit_date is not None
    if ac or canc or visit:
        c.saveState()
        c.setFillColorRGB(0, 0, 0, 0.2)
        c.rotate(45)
        if xn == 0 and yn == 1:
            ox = w / 2 + 40 * mm
            oy = h / 2 - 30 * mm
        elif xn == 0 and yn == 0:
            ox = w / 2 - 65 * mm
            oy = 13.5 * mm
        elif xn == 1 and yn == 0:
            ox = w - 95.75 * mm
            oy = 13.5 * mm - h / 4
        else:
            ox = w + 9.25 * mm
            oy = h / 2 - 30 * mm - h / 4
        c.setFont('OpenSansBold', 50)
        s = 'ОТМЕНЕНО'
        if ac:
            s = 'ИСПОЛНЕНО'
        elif visit:
            s = 'ПОСЕЩЕНО'
        c.drawString(ox, oy, s)
        c.restoreState()

    c.setFont('OpenSans', 10)
    c.drawCentredString(w / 2 - w / 4 + (w / 2 * xn), (h / 2 - height - 5) + (h / 2) * yn, dir.hospital_short_title)

    c.setFont('OpenSans', 8)
    c.drawCentredString(w / 2 - w / 4 + (w / 2 * xn), (h / 2 - height - 15) + (h / 2) * yn, "(%s. %s)" % (dir.hospital_address, dir.hospital_phones))

    c.setFont('OpenSans', 14)
    c.drawCentredString(w / 2 - w / 4 + (w / 2 * xn), (h / 2 - height - 30) + (h / 2) * yn, "Направление" + ("" if not dir.imported_from_rmis else " из РМИС"))

    renderPDF.draw(d, c, w / 2 - width + (w / 2 * xn) - paddingx / 3 - 5 * mm, (h / 2 - height - 57) + (h / 2) * yn)

    c.setFont('OpenSans', 20)
    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height) + (h / 2) * yn - 57, "№ " + str(dir.pk))  # Номер направления

    c.setFont('OpenSans', 9)
    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 70) + (h / 2) * yn, "Создано: " + strdate(dir.data_sozdaniya) + " " + strtime(dir.data_sozdaniya)[:5])
    history_num = dir.history_num
    additional_num = dir.additional_num
    if history_num and len(history_num) > 0:
        c.drawRightString(w / 2 * (xn + 1) - paddingx, (h / 2 - height - 70) + (h / 2) * yn, "№ истории: " + history_num)
    elif additional_num and len(additional_num) > 0:
        c.drawRightString(w / 2 * (xn + 1) - paddingx, (h / 2 - height - 67) + (h / 2) * yn, f"({str(additional_num).strip()})")
    elif dir.client.number_poliklinika and len(dir.client.number_poliklinika) > 0:
        c.drawRightString(w / 2 * (xn + 1) - paddingx, (h / 2 - height - 70) + (h / 2) * yn, f"({str(dir.client.number_poliklinika).strip()})")

    if dir.history_num and len(dir.history_num) > 0:
        c.drawRightString(w / 2 * (xn + 1) - paddingx, (h / 2 - height - 70) + (h / 2) * yn, "№ истории: " + dir.history_num)

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 80) + (h / 2) * yn, "ФИО: " + dir.client.individual.fio())

    c.setFont('OpenSans', 13.5)
    c.drawRightString(w / 2 * (xn + 1) - paddingx, (h / 2 - height - 80) + (h / 2) * yn, "Код {}".format(translation_number_from_decimal(int(dir.client.pk))))

    c.setFont('OpenSans', 9)
    c.drawRightString(
        w / 2 * (xn + 1) - paddingx,
        (h / 2 - height - 90) + (h / 2) * yn,
        "Д/р: {} ({}) – {}".format(dir.client.individual.bd(), dir.client.individual.age_s(direction=dir), dir.client.individual.sex),
    )

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 90) + (h / 2) * yn, "{}: {}".format("ID" if dir.client.base.is_rmis else "Номер карты", dir.client.number_with_type()))
    diagnosis = dir.diagnos.strip()[:35]
    if not dir.imported_from_rmis:
        if diagnosis != "":
            c.drawString(
                paddingx + (w / 2 * xn),
                (h / 2 - height - 100) + (h / 2) * yn,
                ("" if dir.vich_code == "" else ("Код: " + dir.vich_code + "  ")) + "Диагноз (МКБ 10): " + ("не указан" if diagnosis == "-" else diagnosis),
            )
        elif dir.vich_code != "":
            c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 100) + (h / 2) * yn, "Код: " + dir.vich_code)
        if dir.istochnik_f:
            c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 110) + (h / 2) * yn, "Источник финансирования: " + dir.client.base.title + " - " + dir.istochnik_f.title)
        else:
            c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 110) + (h / 2) * yn, "Источник финансирования: ")
    else:
        nds = 0
        if diagnosis != "":
            c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 100) + (h / 2) * yn, "Диагноз (МКБ 10): " + diagnosis)
            nds = 5
        if dir.imported_org:
            c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 105 - nds) + (h / 2) * yn, "Организация: " + dir.imported_org.title)

    issledovaniya = dir.issledovaniya_set.all()

    vid = []
    has_descriptive = False
    has_doc_refferal = False
    need_qr_code = False
    for i in issledovaniya:
        rtp = i.research.reversed_type
        if rtp < -1:
            has_doc_refferal = True
            rt = {
                -2: 'Консультации',
                -3: 'Лечение',
                -4: 'Стоматология',
                -5: 'Стационар',
                -6: 'Микробиология',
                -9998: 'Морфология',
                -9: 'Формы',
                -11: 'Заявления',
                -12: 'Мониторинги',
                -14: 'Случай',
            }[rtp]
            # if rtp == -6:
            #     has_micro = True
        else:
            rt = i.research.podrazdeleniye.get_title()
        if rt not in vid:
            vid.append(rt)
            if i.research.podrazdeleniye and i.research.podrazdeleniye.p_type == Podrazdeleniya.PARACLINIC:
                has_descriptive = True
                if i.research.podrazdeleniye.can_has_pacs:
                    need_qr_code = True

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 120) + (h / 2) * yn, "Вид: " + ", ".join(vid))

    if dir.purpose:
        c.drawRightString(w / 2 * (xn + 1) - paddingx, (h / 2 - height - 120) + (h / 2) * yn, "Цель: " + dir.get_purpose_display())

    if dir.external_organization:
        c.drawRightString(w / 2 * (xn + 1) - paddingx, (h / 2 - height - 134) + (h / 2) * yn, dir.external_organization.title)

    if dir.parent and dir.parent.research.is_hospital:
        c.setFont('OpenSansBold', 8)
        c.drawRightString(w / 2 * (xn + 1) - paddingx, (h / 2 - height - 129) + (h / 2) * yn, ("Стационар-" + str(dir.parent.napravleniye_id)))
    c.setFont('OpenSans', 9)

    styleSheet = getSampleStyleSheet()

    all_iss = issledovaniya.count()
    max_f = 9
    min_f = 7
    max_res = 36

    max_off = max_f - min_f
    font_size = max_f - (max_off * (all_iss / max_res))

    styleSheet["BodyText"].leading = font_size + 0.5
    data = []

    values = []

    service_locations = {}

    n = 0
    for v in issledovaniya:
        n += 1
        service_location_title = "" if not v.service_location else v.service_location.title
        if service_location_title:
            if service_location_title not in service_locations:
                service_locations[service_location_title] = []
            service_locations[service_location_title].append(n)
        values.append(
            {
                "title": v.research.get_title(),
                "full_title": v.research.title,
                "sw": v.research.sort_weight,
                "count": v.how_many,
                "comment": v.localization.title if v.localization else v.comment,
                "n": n,
                "g": -1 if not v.research.fractions_set.exists() else v.research.fractions_set.first().relation_id,
                "info": v.research.paraclinic_info,
                "hospital_department_replaced_title": v.hospital_department_replaced_title,
            }
        )

    one_sl = len(service_locations) <= 1

    tw = w / 2 - paddingx * 2
    m = 0
    ns = {}
    if has_descriptive or has_doc_refferal:
        tmp = [
            Paragraph('<font face="OpenSansBold" size="8">%s</font>' % ("Исследование" if not has_doc_refferal else "Назначение"), styleSheet["BodyText"]),
            Paragraph('<font face="OpenSansBold" size="8">Информация</font>', styleSheet["BodyText"]),
        ]
        data.append(tmp)
        colWidths = [int(tw * 0.5), int(tw * 0.5)]
        values.sort(key=lambda l: l["full_title"])

        for v in values:
            ns[v["n"]] = v["n"]
            tmp = [
                Paragraph(
                    '<font face="OpenSans" size="8">'
                    + ("" if one_sl else "№{}: ".format(v["n"]))
                    + xh.fix(v["full_title"])
                    + ("" if not v["comment"] else " <font face=\"OpenSans\" size=\"" + str(font_size * 0.8) + "\">[{}]</font>".format(v["comment"]))
                    + ("" if not v["hospital_department_replaced_title"] else f"<br/>Направлен в: {v['hospital_department_replaced_title']}")
                    + "</font>",
                    styleSheet["BodyText"],
                ),
                Paragraph('<font face="OpenSans" size="8">' + xh.fix(v["info"]) + "</font>", styleSheet["BodyText"]),
            ]
            data.append(tmp)
        m = 8
    else:
        colWidths = [int(tw / 2), int(tw / 2)]
        c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 134) + (h / 2) * yn, "Назначения: ")
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(1)
        values.sort(key=lambda l: (l["g"], l["sw"]))

        n_rows = int(len(values) / 2)

        normvars = []
        c_cnt = nc_cnt = 0
        for i in range(0, len(values) + 1):
            if (i + 1) % 2 == 0:
                nc_cnt += 1
                if nc_cnt + n_rows < len(values):
                    normvars.append(values[nc_cnt + n_rows])
            else:
                normvars.append(values[c_cnt])
                c_cnt += 1

        p = Paginator(normvars, 2)
        n = 1
        for pg_num in p.page_range:
            pg = p.page(pg_num)
            tmp = []
            for obj in pg.object_list:
                ns[obj["n"]] = n
                tmp.append(
                    Paragraph(
                        '<font face="OpenSans" size="'
                        + str(font_size)
                        + '">'
                        + ("" if one_sl else "№{}: ".format(n))
                        + obj["title"]
                        + ("" if not obj["count"] or obj["count"] == 1 else " ({}шт.)".format(str(obj["count"])))
                        + ("" if not obj["comment"] else " <font face=\"OpenSans\" size=\"" + str(font_size * 0.8) + "\">[{}]</font>".format(obj["comment"]))
                        + "</font>",
                        styleSheet["BodyText"],
                    )
                )
                n += 1
            if len(pg.object_list) < 2:
                tmp.append(Paragraph('<font face="OpenSans" size="' + str(font_size) + '"></font>', styleSheet["BodyText"]))
            data.append(tmp)

    t = Table(data, colWidths=colWidths)
    t.setStyle(
        TableStyle(
            [
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 0.5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]
        )
    )
    t.canv = c
    wt, ht = t.wrap(0, 0)
    t.drawOn(c, paddingx + (w / 2 * xn), ((h / 2 - height - 138 + m) + (h / 2) * yn - ht))

    height_params_table = 0
    direction_params = dir.directionparamsresult_set.all()
    if len(direction_params) > 0:
        params_data = [
            [
                Paragraph(
                    '<font face=\"OpenSansBold\" size=\"'
                    + str(font_size * 0.8)
                    + f'\">{params.title}:</font>'
                    + '<font face=\"OpenSans\" size=\"'
                    + str(font_size * 0.8)
                    + f'\"> {params.string_value_normalized}</font>',
                    styleSheet["BodyText"],
                )
            ]
            for params in direction_params
        ]
        params_col = [int(tw)]
        params_table = Table(data=params_data, colWidths=params_col)
        params_table.setStyle(
            TableStyle(
                [
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]
            )
        )
        params_table.canv = c
        width_params_table, height_params_table = params_table.wrap(0, 0)
        params_table.drawOn(c, paddingx + (w / 2 * xn), ((h / 2 - height - 138 + m) + (h / 2) * yn - ht - height_params_table))

    c.setFont('OpenSans', 8)
    if not has_descriptive and not has_doc_refferal:
        c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 138 + m) + (h / 2) * yn - ht - height_params_table - 10, "Всего назначено: " + str(len(issledovaniya)))

    if service_locations:
        n = 0 if has_descriptive or has_doc_refferal else 1
        if one_sl:
            c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 138 + m) + (h / 2) * yn - ht - height_params_table - 14 - n * 10, "Место: " + list(service_locations)[0])
        else:
            c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 138 + m) + (h / 2) * yn - ht - height_params_table - 14 - n * 10, "Места оказания услуг:")
            for title in service_locations:
                n += 1
                c.drawString(
                    paddingx + (w / 2 * xn),
                    (h / 2 - height - 138 + m) + (h / 2) * yn - ht - height_params_table - 14 - n * 10,
                    title + " – услуги " + ', '.join(map(lambda x: "№{}".format(ns[x]), service_locations[title])),
                )

    if need_qr_code:
        qr_value = translit(dir.client.individual.fio(), 'ru', reversed=True)
        qr_code = qr.QrCodeWidget(qr_value)
        qr_code.barWidth = 70
        qr_code.barHeight = 70
        qr_code.qrVersion = 1
        d = Drawing()
        d.add(qr_code)
        renderPDF.draw(d, c, paddingx + (w / 2 * xn) + 200, 32 + (h / 2) * yn)

    nn = 0
    if not dir.imported_from_rmis:
        if dir.doc_who_create and dir.doc_who_create != dir.doc:
            nn = 9
            c.drawString(paddingx + (w / 2 * xn), 13 + (h / 2) * yn, Truncator("Выписал: %s, %s" % (dir.doc_who_create.get_fio(), dir.doc_who_create.podrazdeleniye.title)).chars(63))

        if dir.doc:
            c.drawString(paddingx + (w / 2 * xn), 22 + (h / 2) * yn + nn, "Отделение: " + Truncator(dir.get_doc_podrazdeleniye_title()).chars(50))
            c.drawString(paddingx + (w / 2 * xn), 13 + (h / 2) * yn + nn, "Л/врач: " + dir.doc.get_fio())
    else:
        c.drawString(paddingx + (w / 2 * xn), 31 + (h / 2) * yn + nn, "РМИС#" + dir.rmis_number)
        c.drawString(paddingx + (w / 2 * xn), 22 + (h / 2) * yn + nn, "Создал направление: " + dir.doc_who_create.get_fio())
        c.drawString(paddingx + (w / 2 * xn), 13 + (h / 2) * yn + nn, dir.doc_who_create.podrazdeleniye.title)

    c.setFont('OpenSans', 7)
    c.setLineWidth(0.25)
    # c.line(w / 2 * (xn + 1) - paddingx, 21 + (h / 2) * yn + nn, w / 2 * (xn + 1) - 82, 21 + (h / 2) * yn + nn)
    # c.drawRightString(w / 2 * (xn + 1) - paddingx - paddingx, 13 + (h / 2) * yn + nn, "(подпись)")


def calculate_age(born):
    """Подсчет возраста"""
    today = date.today()
    try:
        birthday = born.replace(year=today.year)
    except ValueError:
        birthday = born.replace(year=today.year, month=born.month + 1, day=1)
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year


@login_required
def print_history(request):
    """Печать истории забора материала за день"""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    styleSheet = getSampleStyleSheet()
    import os.path
    import collections

    filter = False
    filterArray = []
    if "filter" in request.GET.keys():
        filter = True
        filterArray = json.loads(request.GET["filter"])

    pdfmetrics.registerFont(TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))  # Загрузка шрифта

    response = HttpResponse(content_type='application/pdf')  # Формирование ответа
    response['Content-Disposition'] = 'inline; filename="napr.pdf"'  # Content-Disposition inline для показа PDF в браузере
    buffer = BytesIO()  # Буфер
    c = canvas.Canvas(buffer, pagesize=A4)  # Холст
    tubes = []
    if not filter:
        tubes = list(TubesRegistration.objects.filter(doc_get=request.user.doctorprofile).order_by('time_get').exclude(time_get__lt=datetime.now().date()))
    else:
        for v in filterArray:
            tubes.append(TubesRegistration.objects.get(number=v))
    labs = {}  # Словарь с пробирками, сгруппироваными по лаборатории
    for v in tubes:  # Перебор пробирок
        iss = Issledovaniya.objects.filter(tubes__number=v.number)  # Получение исследований для пробирки
        iss_list = []  # Список исследований
        podr = iss[0].research.get_podrazdeleniye()
        podr_title = podr.title if podr else ""
        doc_podr = v.doc_get and v.doc_get.podrazdeleniye
        doc_podr_title = doc_podr.title if doc_podr else ""
        k = doc_podr_title + "@" + podr_title
        for val in iss:  # Цикл перевода полученных исследований в список
            iss_list.append(val.research.title)
        if k not in labs.keys():  # Добавление списка в словарь если по ключу k нет ничего в словаре labs
            labs[k] = []
        for value in iss_list:  # Перебор списка исследований
            labs[k].append(
                {
                    "type": v.type.tube.title,
                    "researches": value,
                    "client-type": iss[0].napravleniye.client.base.short_title,
                    "lab_title": podr_title,
                    "time": strtime(v.time_get),
                    "dir_id": iss[0].napravleniye_id,
                    "podr": doc_podr_title,
                    "reciver": None,
                    "tube_id": str(v.number),
                    "history_num": iss[0].napravleniye.history_num,
                    "fio": iss[0].napravleniye.client.individual.fio(short=True, dots=True),
                }
            )  # Добавление в список исследований и пробирок по ключу k в словарь labs
    labs = collections.OrderedDict(sorted(labs.items()))  # Сортировка словаря
    c.setFont('OpenSans', 20)

    paddingx = 17
    data_header = ["№", "ФИО, № истории", "№ емкости", "Тип емкости", "Наименования исследований", "Штрих пробирки"]
    tw = w - paddingx * 4.5
    tx = paddingx * 3
    ty = 90
    c.setFont('OpenSans', 9)
    styleSheet["BodyText"].fontName = "OpenSans"
    styleSheet["BodyText"].fontSize = 7
    doc_num = 0

    for key in labs:
        doc_num += 1
        p = Paginator(labs[key], 47)
        i = 0
        if doc_num >= 2:
            c.showPage()

        for pg_num in p.page_range:
            pg = p.page(pg_num)
            if pg_num >= 0:
                draw_tituls(c, p.num_pages, pg_num, paddingx, pg[0], request.user.doctorprofile.hospital_safe_title)
            data = []
            tmp = []
            for v in data_header:
                tmp.append(Paragraph(str(v), styleSheet["BodyText"]))
            data.append(tmp)
            merge_list = {}
            num = 0
            lastid = "-1"

            for obj in pg.object_list:
                tmp = []
                if lastid != obj["tube_id"]:
                    i += 1
                    lastid = obj["tube_id"]
                    shownum = True
                else:
                    shownum = False
                    if lastid not in merge_list.keys():
                        merge_list[lastid] = []
                    merge_list[lastid].append(num)

                if shownum:
                    tmp.append(Paragraph(str(i), styleSheet["BodyText"]))
                    fio = obj["fio"]
                    if obj["history_num"] and len(obj["history_num"]) > 0:
                        fio += ", " + obj["history_num"]
                    tmp.append(Paragraph(fio, styleSheet["BodyText"]))
                    tmp.append(Paragraph(obj["tube_id"], styleSheet["BodyText"]))
                    tmp.append(Paragraph(obj["type"], styleSheet["BodyText"]))
                else:
                    tmp.append("")
                    tmp.append("")
                    tmp.append("")
                    tmp.append("")
                research_tmp = obj["researches"]
                if len(research_tmp) > 38:
                    research_tmp = research_tmp[0 : -(len(research_tmp) - 38)] + "..."
                tmp.append(Paragraph(research_tmp, styleSheet["BodyText"]))
                bcd = createBarcodeDrawing('Code128', value=obj["tube_id"], humanReadable=0, barHeight=5 * mm, width=43 * mm)
                tmp.append(bcd)

                data.append(tmp)
                num += 1

            style = TableStyle(
                [
                    ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                    ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
                    ('LEFTPADDING', (0, 0), (-1, -1), 1 * mm),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                    ('TOPPADDING', (0, 0), (-1, -1), 2 * mm),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3 * mm),
                    ('LEFTPADDING', (-1, 1), (-1, -1), -6 * mm),
                ]
            )
            for span in merge_list:  # Цикл объединения ячеек
                for pos in range(0, 6):
                    style.add('INNERGRID', (pos, merge_list[span][0]), (pos, merge_list[span][0] + len(merge_list[span])), 0.28, colors.white)
                    style.add('BOX', (pos, merge_list[span][0]), (pos, merge_list[span][0] + len(merge_list[span])), 0.2, colors.black)
            t = Table(data, colWidths=[int(tw * 0.03), int(tw * 0.21), int(tw * 0.1), int(tw * 0.23), int(tw * 0.29), int(tw * 0.17)], style=style)

            t.canv = c
            wt, ht = t.wrap(0, 0)
            t.drawOn(c, tx, h - ht - ty)
            if pg.has_next():
                c.showPage()

    c.save()

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    slog.Log(key="", type=10, body="", user=request.user.doctorprofile).save()
    return response


def draw_tituls(c, pages, page, paddingx, obj, hospital_title):
    """Функция рисования шапки и подвала страницы pdf"""
    c.setFont('OpenSans', 9)
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)

    c.drawCentredString(w / 2, h - 30, hospital_title)
    c.setFont('OpenSans', 12)
    c.drawCentredString(w / 2, h - 50, "АКТ приёма-передачи емкостей с биоматериалом")

    c.setFont('OpenSans', 10)
    # c.drawString(paddingx * 3, h - 70, "№ " + str(doc_num))
    c.drawRightString(w - paddingx, h - 70, "Дата: " + str(dateformat.format(date.today(), settings.DATE_FORMAT)))

    c.drawString(paddingx * 3, h - 70, "Отделение (от кого): " + str(obj["podr"]))
    c.drawString(paddingx * 3, h - 80, "Лаборатория (кому): " + str(obj["lab_title"]))
    c.drawString(paddingx * 3, 55, "Сдал: ________________/_____________________________/")
    c.setFont('OpenSans', 8)
    c.drawString(paddingx * 3 + 50, 45, "(подпись)")
    c.setFont('OpenSans', 10)
    c.drawRightString(w - paddingx, 55, "Принял: ________________/_____________________________/")
    c.setFont('OpenSans', 8)
    c.drawRightString(w - paddingx - 150, 45, "(подпись)")

    c.drawRightString(w - paddingx, 20, "Страница " + str(page) + " из " + str(pages))


@csrf_exempt
@login_required
def order_researches(request):
    from directions.models import CustomResearchOrdering

    if request.method == "POST":
        order = json.loads(request.POST.get("order", "[]"))
        lab = request.POST.get("lab")
        CustomResearchOrdering.objects.filter(research__podrazdeleniye_id=lab).delete()
        for i in range(len(order)):
            w = len(order) - i
            CustomResearchOrdering(research=directory.Researches.objects.get(pk=order[i]), user=request.user.doctorprofile, weight=w).save()

    return JsonResponse(1, safe=False)


def py(y=0.0):
    y *= mm
    return h - y


def pyb(y=0.0):
    y *= mm
    return y


def px(x=0.0):
    return x * mm


def pxr(x=0.0):
    x *= mm
    return w - x


def create_case_by_cards(cards):
    research_case = directory.Researches.objects.filter(is_case=True, hide=False).first()
    doc = DoctorProfile.objects.filter(fio='Системный Пользователь', is_system_user=True).first()
    if not doc:
        user = User.objects.create_user(uuid.uuid4().hex)
        user.is_active = True
        user.save()
        doc = DoctorProfile(user=user, fio='Системный Пользователь', is_system_user=True)
        doc.save()
        doc.get_fio_parts()
    card_directions = {}
    number_directons = None
    for card in cards:
        card_id = card.get("card_id")
        researches = card.get("research")
        plan_start_date_case = normalize_dots_date(card.get("date"))
        plan_start_date_case = f"{plan_start_date_case} 00:00:00"
        result_search_case = search_case_by_card_date(card_id, plan_start_date_case, research_case.pk, 1)
        case_issledovaniye_number, case_direction_number = None, None
        for i in result_search_case:
            case_issledovaniye_number = i.case_issledovaniye_number
            case_direction_number = i.case_direction_number
            break
        financing_source = IstochnikiFinansirovaniya.objects.filter(title__in=["Профосмотр", "Юрлицо"]).first()

        if case_issledovaniye_number:
            number_directons = Napravleniya.objects.values_list("id", flat=True).filter(parent_case_id=case_issledovaniye_number)
            researches_sql = get_researches_by_number_directions(tuple(number_directons))
            current_researches_case = set([i.research_id for i in researches_sql])
            api_researches = set(researches)
            api_researches -= current_researches_case
            researches = list(api_researches)
            result = Napravleniya.gen_napravleniya_by_issledovaniya(
                card_id,
                "",
                financing_source.pk,
                "",
                None,
                doc,
                {-1: researches},
                {},
                False,
                {},
                vich_code="",
                count=1,
                discount=0,
                rmis_slot=None,
                price_name=None,
                case_id=case_direction_number,
                case_by_direction=True,
                plan_start_date=plan_start_date_case,
            )
        else:
            napravleniye_case = Napravleniya.gen_napravleniye(
                card_id,
                doc,
                financing_source,
                "",
                "",
                doc,
                -1,
                doc,
            )

            issledovaniye_case = Issledovaniya(napravleniye=napravleniye_case, research=research_case, deferred=False, plan_start_date=plan_start_date_case)
            issledovaniye_case.save()
            result = Napravleniya.gen_napravleniya_by_issledovaniya(
                card_id,
                "",
                financing_source.pk,
                "",
                None,
                doc,
                {-1: researches},
                {},
                False,
                {},
                vich_code="",
                count=1,
                discount=0,
                rmis_slot=None,
                price_name=None,
                case_id=napravleniye_case.pk,
                case_by_direction=True,
                plan_start_date=plan_start_date_case,
            )
        if number_directons:
            number_directons = [i for i in number_directons]
        else:
            number_directons = []
        number_directons.extend(result.get("list_id"))
        card_directions[card_id] = list(set(number_directons))
    return card_directions
