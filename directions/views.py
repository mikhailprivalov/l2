import sys
from datetime import date, datetime
from io import BytesIO

import simplejson as json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.utils import dateformat
from django.db.models import Q
from django.utils.text import Truncator
from django.views.decorators.csrf import csrf_exempt
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import eanbc
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfdoc
from reportlab.pdfgen import canvas
from reportlab.pdfgen.canvas import Canvas

import directory.models as directory
import slog.models as slog
from appconf.manager import SettingManager
from directions.models import Napravleniya, Issledovaniya, TubesRegistration
from laboratory.decorators import logged_in_or_token
from laboratory.settings import FONTS_FOLDER
from laboratory.utils import strtime
from podrazdeleniya.models import Podrazdeleniya
from utils import xh
from utils.dates import try_parse_range

w, h = A4

from django.utils import timezone
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
import numpy as np


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
    pdfmetrics.registerFont(
        TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))
    elements = []
    for res in directory.Researches.objects.filter(pk__in=researches):
        if type != 2:
            iss_list = Issledovaniya.objects.filter(tubes__doc_recive_id__isnull=False,
                                                    tubes__time_recive__range=(date_start, date_end),
                                                    doc_confirmation_id__isnull=True, research__pk=res.pk,
                                                    deferred=False).order_by('tubes__time_recive')
        else:
            iss_list = Issledovaniya.objects.filter(research__pk=res.pk, deferred=True, doc_confirmation__isnull=True,
                                                    tubes__doc_recive__isnull=False).order_by('tubes__time_recive')

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
                    data[-1].append(inobj.issledovaniya_set.first().napravleniye.client.individual.fio(short=True,
                                                                                                       dots=True) + ", " +
                                    inobj.issledovaniya_set.first().napravleniye.client.individual.age_s(
                                        iss=inobj.issledovaniya_set.first()) + "<br/>№ напр.: " + str(
                        inobj.issledovaniya_set.first().napravleniye.pk) + "<br/>" + "№ ёмкости: " + str(
                        inobj.pk) + "<br/>" + Truncator(
                        inobj.issledovaniya_set.first().napravleniye.doc.podrazdeleniye.title).chars(19) + "<br/><br/>")
            if len(data) < ysize:
                for i in range(len(data), ysize):
                    data.append([])
            for y in range(0, ysize):
                if len(data[y]) < xsize:
                    for i in range(len(data[y]), xsize):
                        data[y].append("<br/><br/><br/><br/><br/>")
            style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.black),
                                ('BOX', (0, 0), (-1, -1), 0.3, colors.black),
                                ])

            s = getSampleStyleSheet()
            s = s["BodyText"]
            s.wordWrap = 'LTR'
            data = np.array(data).T
            data2 = [[Paragraph('<font face="OpenSans" size="7">' + cell + "</font>", s) for cell in row] for row in
                     data]
            tw = lw - 90
            t = Table(data2, colWidths=[int(tw / 8), int(tw / 8), int(tw / 8), int(tw / 8), int(tw / 8), int(tw / 8),
                                        int(tw / 8), int(tw / 8)])
            t.setStyle(style)
            st = ""
            if type == 2:
                st = ", отложенные"
            elements.append(Paragraph(
                '<font face="OpenSans" size="10">' + res.title + st + ", " + str(pg_num) + " стр<br/><br/></font>", s))
            elements.append(t)
            elements.append(PageBreak())

    doc.build(elements)
    pdf = buffer.getvalue()  # Получение данных из буфера
    buffer.close()  # Закрытие буфера
    response.write(pdf)  # Запись PDF в ответ
    return response

# @cache_page(60 * 15)
@logged_in_or_token
def gen_pdf_dir(request):
    """Генерация PDF направлений"""
    if SettingManager.get("pdf_auto_print", "true", "b"):
        pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:true,bSilent:false,bShrinkToFit:true}\);)>>'
    direction_id = json.loads(request.GET["napr_id"])  # Перевод JSON строки в объект

    response = HttpResponse(content_type='application/pdf')  # Формирование ответа типа PDF
    response['Content-Disposition'] = 'inline; filename="directions.pdf"'  # Включение режима вывода PDF в браузер

    buffer = BytesIO()  # Буфер
    c = canvas.Canvas(buffer, pagesize=A4)  # Создание холста для PDF размера А4
    c.setTitle('Направления {}'.format(', '.join([str(x) for x in direction_id])))

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os.path

    pdfmetrics.registerFont(
        TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))  # Загрузка шрифта из файла
    pdfmetrics.registerFont(
        TTFont('OpenSansBold', os.path.join(FONTS_FOLDER, 'OpenSans-Bold.ttf')))  # Загрузка шрифта из файла
    pdfmetrics.registerFont(
        TTFont('TimesNewRoman', os.path.join(FONTS_FOLDER, 'TimesNewRoman.ttf')))  # Загрузка шрифта из файла
    dn = Napravleniya.objects.filter(pk__in=direction_id)
    ddef = dn.filter(issledovaniya__research__direction_form=0).distinct()
    p = Paginator(list(ddef), 4)  # Деление списка направлений по 4
    instructions = []
    has_def = ddef.count() > 0
    if has_def:
        framePage(c)
    for pg_num in p.page_range:
        pg = p.page(pg_num)
        i = 4  # Номер позиции направления на странице (4..1)
        for n_ob in pg.object_list:  # Перебор номеров направлений на странице
            printDirection(c, i, n_ob)  # Вызов функции печати направления на указанную позицию
            instructions += n_ob.get_instructions()
            i -= 1
        if pg.has_next():  # Если есть следующая страница
            c.showPage()  # Создание новой страницы
            framePage(c)  # Рисование разделительных линий для страницы

    donepage = dn.exclude(issledovaniya__research__direction_form=0)
    if donepage.count() > 0 and has_def:
        c.showPage()

    thismodule = sys.modules[__name__]
    n = 0
    cntn = donepage.count()
    for d in donepage:
        n += 1
        iss = Issledovaniya.objects.filter(napravleniye=d)
        if not iss.exists():
            continue
        form = iss[0].research.direction_form
        if hasattr(thismodule, 'form%s' % form):
            f = getattr(thismodule, 'form%s' % form)
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
            tx += '--------------------------------------------------------------------------------------\n<font face="OpenSansBold" size="10">{}</font>\n<font face="OpenSans" size="10">&nbsp;&nbsp;&nbsp;&nbsp;{}\n</font>'.format(
                i["title"], i["text"])
        data = [[Paragraph(tx.replace("\n", "<br/>"), s)]]

        t = Table(data, colWidths=[w - 30 * mm])
        t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                               ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                               ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.white),
                               ('BOX', (0, 0), (-1, -1), 0.25, colors.white),
                               ('LEFTPADDING', (0, 0), (-1, -1), 4),
                               ('TOPPADDING', (0, 0), (-1, -1), 0.5),
                               ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                               ]))
        t.canv = c
        wt, ht = t.wrap(0, 0)
        t.drawOn(c, 15 * mm, h - 15 * mm - ht)
        c.showPage()

    c.save()  # Сохранение отрисованного на PDF
    pdf = buffer.getvalue()  # Получение данных из буфера

    #Проверить, если единый источник финансирвоания у направлений и title==платно, тогода печатать контракт
    fin_ist_set = set()
    card_pk_set = set()
    for n in dn:
        fin_ist_set.add(n.istochnik_f)
        card_pk_set.add(n.client_id)

    fin_status = None
    if len(fin_ist_set) == 1 and fin_ist_set.pop().title.lower() == 'платно':
        fin_status = True

    def save(form, filename: str):
        with open(filename, 'wb') as f:
            f.write(form.read())

    if request.GET.get("contract"):
        if request.GET["contract"] == '1' and SettingManager.get("direction_contract", default='False', default_type='b'):
            if len(card_pk_set) == 1 and fin_status:
                from forms.forms102 import form_01 as f_contract
                fc = f_contract(request_data = {**dict(request.GET.items()), "user": request.user, "card_pk":card_pk_set.pop()})
                fc_buf = BytesIO()
                fc_buf.write(fc)
                fc_buf.seek(0)
                buffer.seek(0)
                from pdfrw import PdfReader, PdfWriter
                today = datetime.now()
                date_now1 = datetime.strftime(today, "%y%m%d%H%M%S%f")[:-3]
                date_now_str = str(n.client_id) + str(date_now1)
                file_dir = 'c:\\temp\\' + date_now_str + '_dir.pdf'
                file_contract = 'c:\\temp\\' + date_now_str + '_contract.pdf'
                save(buffer, filename=file_dir)
                save(fc_buf, filename=file_contract)
                pdf_all = BytesIO()
                inputs = [file_dir, file_contract]
                writer = PdfWriter()
                for inpfn in inputs:
                    writer.addpages(PdfReader(inpfn).pages)
                writer.write(pdf_all)
                pdf_out = pdf_all.getvalue()
                pdf_all.close()
                response.write(pdf_out)
                buffer.close()
                os.remove(file_dir)
                os.remove(file_contract)
                fc_buf.close()
                return response

    buffer.close()  # Закрытие буфера

    response.write(pdf)  # Запись PDF в ответ

    return response


def framePage(canvas):
    # Деление страницы на 4 зоны линиями
    canvas.setFont('Times-Roman', 20)
    canvas.setStrokeColorRGB(0, 0, 0)
    canvas.setLineWidth(1)
    canvas.line(w / 2, 0, w / 2, h)
    canvas.line(0, h / 2, w, h / 2)


def printDirection(c: Canvas, n, dir: Napravleniya):
    xn = 0
    if n % 2 != 0: xn = 1
    yn = 0
    if n > 2: yn = 1
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
    c.drawCentredString(w / 2 - w / 4 + (w / 2 * xn), (h / 2 - height - 5) + (h / 2) * yn,
                        SettingManager.get("org_title"))

    c.setFont('OpenSans', 8)
    c.drawCentredString(w / 2 - w / 4 + (w / 2 * xn), (h / 2 - height - 15) + (h / 2) * yn,
                        "(%s. %s)" % (SettingManager.get("org_address"), SettingManager.get("org_phones"),))

    c.setFont('OpenSans', 14)
    c.drawCentredString(w / 2 - w / 4 + (w / 2 * xn), (h / 2 - height - 30) + (h / 2) * yn,
                        "Направление" + ("" if not dir.imported_from_rmis else " из РМИС"))

    renderPDF.draw(d, c, w / 2 - width + (w / 2 * xn) - paddingx / 3 - 5 * mm, (h / 2 - height - 57) + (h / 2) * yn)

    c.setFont('OpenSans', 20)
    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height) + (h / 2) * yn - 57, "№ " + str(dir.pk))  # Номер направления

    c.setFont('OpenSans', 9)
    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 70) + (h / 2) * yn,
                 "Дата: " + str(dateformat.format(dir.data_sozdaniya.date(), settings.DATE_FORMAT)))
    if dir.history_num and len(dir.history_num) > 0:
        c.drawRightString(w / 2 * (xn + 1) - paddingx, (h / 2 - height - 70) + (h / 2) * yn,
                          "№ истории: " + dir.history_num)

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 80) + (h / 2) * yn,
                 "ФИО: " + dir.client.individual.fio())

    c.drawRightString(w / 2 * (xn + 1) - paddingx, (h / 2 - height - 80) + (h / 2) * yn,
                      "Пол: " + dir.client.individual.sex)

    c.drawRightString(w / 2 * (xn + 1) - paddingx, (h / 2 - height - 90) + (h / 2) * yn,
                      "Д/р: {} ({})".format(dir.client.individual.bd(), dir.client.individual.age_s(direction=dir)))

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 90) + (h / 2) * yn,
                 "{}: {}".format("ID" if dir.client.base.is_rmis else "Номер карты", dir.client.number_with_type()))
    diagnosis = dir.diagnos.strip()
    if not dir.imported_from_rmis:
        if diagnosis != "":
            c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 100) + (h / 2) * yn,
                         ("" if dir.vich_code == "" else ("Код: " + dir.vich_code + "  ")) + "Диагноз (МКБ 10): " + ("не указан" if diagnosis == "-" else diagnosis))
        elif dir.vich_code != "":
            c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 100) + (h / 2) * yn,
                         "Код: " + dir.vich_code)
        if dir.istochnik_f:
            c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 110) + (h / 2) * yn,
                         "Источник финансирования: " + dir.client.base.title + " - " + dir.istochnik_f.title)
        else:
            c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 110) + (h / 2) * yn, "Источник финансирования: ")
    else:
        nds = 0
        if diagnosis != "":
            c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 100) + (h / 2) * yn,
                         "Диагноз (МКБ 10): " + diagnosis)
            nds = 5
        if dir.imported_org:
            c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 105 - nds) + (h / 2) * yn,
                         "Организация: " + dir.imported_org.title)

    issledovaniya = Issledovaniya.objects.filter(napravleniye=dir)

    vid = []
    has_descriptive = False
    has_doc_refferal = False
    for i in issledovaniya:
        if i.research.is_doc_refferal:
            has_doc_refferal = True
            rt = "Консультации"
        else:
            rt = i.research.podrazdeleniye.get_title()
        if rt not in vid:
            vid.append(rt)
            if i.research.podrazdeleniye and i.research.podrazdeleniye.p_type == Podrazdeleniya.PARACLINIC:
                has_descriptive = True

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 120) + (h / 2) * yn, "Вид: " + ", ".join(vid))

    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

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

    for v in issledovaniya:
        values.append({"title": v.research.get_title(), "full_title": v.research.title, "sw": v.research.sort_weight,
                       "comment": v.comment,
                       "g": -1 if not v.research.fractions_set.exists() else v.research.fractions_set.first().relation.pk,
                       "info": v.research.paraclinic_info})
    tw = w / 2 - paddingx * 2
    m = 0
    if has_descriptive or has_doc_refferal:
        tmp = [Paragraph(
            '<font face="OpenSansBold" size="8">%s</font>' % ("Исследование" if not has_doc_refferal else "Назначение"),
            styleSheet["BodyText"]),
               Paragraph('<font face="OpenSansBold" size="8">Подготовка, кабинет</font>', styleSheet["BodyText"])]
        data.append(tmp)
        colWidths = [int(tw * 0.5), int(tw * 0.5)]
        values.sort(key=lambda l: l["full_title"])

        for v in values:
            tmp = [Paragraph('<font face="OpenSans" size="8">' + xh.fix(v["full_title"]) + ("" if not v["comment"] else " <font face=\"OpenSans\" size=\"" + str(font_size * 0.8) + "\">[{}]</font>".format(v["comment"])) + "</font>",
                             styleSheet["BodyText"]),
                   Paragraph('<font face="OpenSans" size="8">' + xh.fix(v["info"]) + "</font>", styleSheet["BodyText"])]
            data.append(tmp)
        m = 8
    else:
        colWidths = [int(tw / 2), int(tw / 2)]
        c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 134) + (h / 2) * yn, "Наименования исследований: ")
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

        for pg_num in p.page_range:
            pg = p.page(pg_num)
            tmp = []
            for obj in pg.object_list:
                tmp.append(Paragraph('<font face="OpenSans" size="' + str(font_size) + '">' + obj["title"] + ("" if not obj["comment"] else " <font face=\"OpenSans\" size=\"" + str(font_size * 0.8) + "\">[{}]</font>".format(obj["comment"])) + "</font>",
                                     styleSheet["BodyText"]))
            if len(pg.object_list) < 2:
                tmp.append(
                    Paragraph('<font face="OpenSans" size="' + str(font_size) + '"></font>', styleSheet["BodyText"]))
            data.append(tmp)

    t = Table(data, colWidths=colWidths)
    t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                           ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                           ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                           ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                           ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                           ('LEFTPADDING', (0, 0), (-1, -1), 4),
                           ('TOPPADDING', (0, 0), (-1, -1), 0.5),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                           ]))
    t.canv = c
    wt, ht = t.wrap(0, 0)
    t.drawOn(c, paddingx + (w / 2 * xn), ((h / 2 - height - 138 + m) + (h / 2) * yn - ht))

    c.setFont('OpenSans', 8)
    if not has_descriptive:
        c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 138 + m) + (h / 2) * yn - ht - 10,
                     "Всего назначено: " + str(len(issledovaniya)))

    nn = 0
    if not dir.imported_from_rmis:
        if dir.doc_who_create and dir.doc_who_create != dir.doc:
            nn = 9
            c.drawString(paddingx + (w / 2 * xn), 13 + (h / 2) * yn,
                         Truncator("Выписал: %s, %s" % (
                         dir.doc_who_create.get_fio(), dir.doc_who_create.podrazdeleniye.title)).chars(63))
        c.drawString(paddingx + (w / 2 * xn), 22 + (h / 2) * yn + nn,
                     "Отделение: " + Truncator(dir.doc.podrazdeleniye.title).chars(50))
        c.drawString(paddingx + (w / 2 * xn), 13 + (h / 2) * yn + nn, "Л/врач: " + dir.doc.get_fio())
    else:
        c.drawString(paddingx + (w / 2 * xn), 31 + (h / 2) * yn + nn, "РМИС#" + dir.rmis_number)
        c.drawString(paddingx + (w / 2 * xn), 22 + (h / 2) * yn + nn,
                     "Создал направление: " + dir.doc_who_create.get_fio())
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
def get_one_dir(request):
    """Получение одного направления и исследований из него по пробиркам"""
    # import logging
    # logger = logging.getLogger(__name__)

    response = {"ok": False}
    if request.method == 'GET':
        direction_pk = request.GET['id']
        direction_pk = ''.join(x for x in direction_pk if x.isdigit())
        try:
            direction_pk = int(direction_pk)
        except ValueError:
            direction_pk = -1
        if Napravleniya.objects.filter(pk=direction_pk).exists():
            if "check" not in request.GET.keys():
                tmp2 = Napravleniya.objects.get(pk=direction_pk)
                tmp = Issledovaniya.objects.filter(napravleniye=tmp2).order_by("research__title")
                response["direction"] = {"pk": tmp2.pk,
                                         "cancel": tmp2.cancel,
                                         "date": str(
                                             dateformat.format(tmp2.data_sozdaniya.date(), settings.DATE_FORMAT)),
                                         "doc": {"fio": "" if not tmp2.doc else tmp2.doc.get_fio(),
                                                 "otd": "" if not tmp2.doc else tmp2.doc.podrazdeleniye.title},
                                         "lab": tmp[0].research.get_podrazdeleniye().title,
                                         "type": tmp[0].research.get_podrazdeleniye().p_type,
                                         "imported_from_rmis": tmp2.imported_from_rmis,
                                         "imported_org": "" if not tmp2.imported_org else tmp2.imported_org.title,
                                         "full_confirm": tmp2.is_all_confirm()
                                         }
                response["tubes"] = {}
                tubes_buffer = {}

                fresearches = set()
                fuppers = set()
                flowers = set()
                for iss in Issledovaniya.objects.filter(napravleniye=tmp2):
                    for fr in iss.research.fractions_set.all():
                        absor = directory.Absorption.objects.filter(fupper=fr)
                        if absor.exists():
                            fuppers.add(fr.pk)
                            fresearches.add(fr.research.pk)
                            for absor_obj in absor:
                                flowers.add(absor_obj.flower.pk)
                                fresearches.add(absor_obj.flower.research.pk)

                for v in tmp:
                    for val in directory.Fractions.objects.filter(research=v.research):
                        vrpk = val.relation.pk
                        rel = val.relation
                        if val.research.pk in fresearches and val.pk in flowers:
                            absor = directory.Absorption.objects.filter(flower__pk=val.pk).first()
                            if absor.fupper.pk in fuppers:
                                vrpk = absor.fupper.relation.pk
                                rel = absor.fupper.relation

                        if vrpk not in tubes_buffer.keys():
                            if not v.tubes.filter(type=rel).exists():
                                ntube = TubesRegistration(type=rel)
                                ntube.save()
                            else:
                                ntube = v.tubes.get(type=rel)
                            v.tubes.add(ntube)
                            tubes_buffer[vrpk] = {"pk": ntube.pk, "researches": set()}
                        else:
                            ntube = TubesRegistration.objects.get(pk=tubes_buffer[vrpk]["pk"])
                            v.tubes.add(ntube)

                        tubes_buffer[vrpk]["researches"].add(v.research.title)

                for key in tubes_buffer.keys():
                    tubes_buffer[key]["researches"] = list(tubes_buffer[key]["researches"])

                for key in tubes_buffer.keys():  # Перебор исследований
                    v = tubes_buffer[key]
                    tube = TubesRegistration.objects.get(id=v["pk"])

                    barcode = ""
                    if tube.barcode:  # Проверка штрих кода пробирки
                        barcode = tube.barcode
                    if tube.id not in response["tubes"].keys():  # Если пробирки нет в словаре
                        response["tubes"][tube.id] = {"researches": v["researches"], "status": True,
                                                      "color": tube.type.tube.color,
                                                      "title": tube.type.tube.title, "id": tube.id,
                                                      "barcode": barcode}  # Добавление пробирки в словарь
                    s = tube.getstatus()  # Статус взятия материала для исследований
                    response["tubes"][tube.id]["status"] = s  # Установка статуса в объект пробирки

                response["client"] = {"fio": tmp2.client.individual.fio(),
                                      "sx": tmp2.client.individual.sex,
                                      "bth": tmp2.client.individual.bd()}  # Добавление информации о пациенте в вывод
            response["ok"] = True
    return JsonResponse(response)


@csrf_exempt
@login_required
def setdef(request):
    """
    Установка/снятия статуса 'отложен' для исследования
    :param request:
    :return:
    """
    response = {"ok": False}

    if "pk" in request.POST.keys() or "pk" in request.GET.keys():
        status = False
        if "status" in request.POST.keys() or "status" in request.GET.keys():
            if request.method == "POST":
                status = request.POST["status"]
            else:
                status = request.GET["status"]
            if isinstance(status, str):
                status = status == "true"
        response["s"] = status
        if request.method == "POST":
            pk = request.POST["pk"]
        else:
            pk = request.GET["pk"]
        iss = Issledovaniya.objects.get(pk=int(pk))
        iss.deferred = status
        iss.save()
    return JsonResponse(response)


@csrf_exempt
@login_required
def cancel_direction(request):
    """Функция отмены направления"""

    response = {"ok": False}
    if "pk" in request.POST.keys() or "pk" in request.GET.keys():
        cancel = False
        if "status" in request.POST.keys() or "status" in request.GET.keys():
            if request.method == "POST":
                cancel = request.POST["status"]
            else:
                cancel = request.GET["status"]
            if isinstance(cancel, str):
                cancel = cancel == "true"
        response["s"] = cancel
        if request.method == "POST":
            pk = request.POST["pk"]
        else:
            pk = request.GET["pk"]
        nap = Napravleniya.objects.get(pk=int(pk))
        nap.cancel = cancel
        nap.save()
    return JsonResponse(response)


@csrf_exempt
@login_required
def update_direction(request):
    """Функция обновления исследований в направлении"""

    res = {"r": False, "o": []}
    if request.method == 'POST':  # Проверка типа запроса
        statuses = json.loads(request.POST["data"])

        for k, v in statuses["statuses"].items():  # Перебор ключей и значений
            val = TubesRegistration.objects.get(id=k)  # Выборка пробирки по ключу
            if v and not val.doc_get and not val.time_get:  # Если статус выполнения забора установлен в True
                val.set_get(request.user.doctorprofile)
                res["o"].append(val.id)
            res["dn"] = Issledovaniya.objects.filter(tubes__id=k).first().napravleniye.pk
        res["r"] = True

    return JsonResponse(res)


@csrf_exempt
@login_required
def group_confirm_get(request):
    """Функция группового подтвержения взятия материала"""
    res = {"r": False}
    if request.method == 'POST':  # Проверка типа запроса
        checked = json.loads(request.POST["checked"])

        for t in TubesRegistration.objects.filter(pk__in=checked, doc_get__isnull=True):
            t.set_get(request.user.doctorprofile)

    return JsonResponse(res)


@login_required
def load_history(request):
    """Получение истории заборов материала за текущий день"""
    res = {"rows": []}
    tubes = TubesRegistration.objects.filter(doc_get=request.user.doctorprofile).order_by('time_get').exclude(
        time_get__lt=datetime.now().date())

    for v in tubes:  # Перебор пробирки
        iss = Issledovaniya.objects.filter(tubes__id=v.id)  # Выборка исследований по пробирке
        iss_list = []
        for val in iss:  # Перебор выбранных исследований
            iss_list.append(val.research.title)  # Добавление в список исследований по пробирке
        res["rows"].append({"type": v.type.tube.title, "researches": ', '.join(str(x) for x in iss_list),
                            "time": strtime(v.time_get),
                            "dir_id": iss[0].napravleniye.pk,
                            "tube_id": v.id})  # Добавление пробирки с исследованиями в вывод
    return JsonResponse(res)


@login_required
def get_worklist(request):
    """Получение необходимых пробирок для взятия"""
    tmprows = {}
    res = {"rows": []}
    from datetime import timedelta
    date_start = datetime.now() - timedelta(days=6)
    date_end = datetime.now()
    # if date_start.weekday() == 6: date_start -= timedelta(days=2)
    # if date_start.weekday() == 5: date_start -= timedelta(days=1)
    naps = Napravleniya.objects.filter(
        Q(data_sozdaniya__range=(date_start, date_end), doc_who_create=request.user.doctorprofile, cancel=False)
        | Q(data_sozdaniya__range=(date_start, date_end), doc=request.user.doctorprofile, cancel=False))
    for n in naps:
        for i in Issledovaniya.objects.filter(napravleniye=n):
            for t in i.tubes.filter(doc_get__isnull=True):
                tmprows[t.pk] = {"direction": n.pk, "patient": n.client.individual.fio(short=True, dots=True),
                                 "title": t.type.tube.title,
                                 "pk": t.pk, "color": t.type.tube.color}
    for pk in tmprows.keys():
        res["rows"].append(tmprows[pk])
    res["rows"] = sorted(res["rows"], key=lambda k: k['pk'])
    res["rows"] = sorted(res["rows"], key=lambda k: k['patient'])

    return JsonResponse(res)


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
    response[
        'Content-Disposition'] = 'inline; filename="napr.pdf"'  # Content-Disposition inline для показа PDF в браузере
    buffer = BytesIO()  # Буфер
    c = canvas.Canvas(buffer, pagesize=A4)  # Холст
    tubes = []
    if not filter:
        tubes = TubesRegistration.objects.filter(doc_get=request.user.doctorprofile).order_by('time_get').exclude(
            time_get__lt=datetime.now().date())  # Получение пробирок с материалом, взятым текущим пользователем
    else:
        for v in filterArray:
            tubes.append(TubesRegistration.objects.get(pk=v))
    labs = {}  # Словарь с пробирками, сгруппироваными по лаборатории
    for v in tubes:  # Перебор пробирок
        iss = Issledovaniya.objects.filter(tubes__id=v.id)  # Получение исследований для пробирки
        iss_list = []  # Список исследований
        k = v.doc_get.podrazdeleniye.title + "@" + str(iss[
                                                           0].research.get_podrazdeleniye().title)  # Формирование ключа для группировки по подгруппе лаборатории и названию подразделения направившего на анализ врача
        for val in iss:  # Цикл перевода полученных исследований в список
            iss_list.append(val.research.title)
        if k not in labs.keys():  # Добавление списка в словарь если по ключу k нету ничего в словаре labs
            labs[k] = []
        for value in iss_list:  # Перебор списка исследований
            labs[k].append(
                {"type": v.type.tube.title, "researches": value,
                 "client-type": iss[0].napravleniye.client.base.short_title,
                 "lab_title": iss[0].research.get_podrazdeleniye().title,
                 "time": strtime(v.time_get),
                 "dir_id": iss[0].napravleniye.pk,
                 "podr": v.doc_get.podrazdeleniye.title,
                 "reciver": None,
                 "tube_id": str(v.id),
                 "history_num": iss[0].napravleniye.history_num,
                 "fio": iss[
                     0].napravleniye.client.individual.fio(short=True,
                                                           dots=True)})  # Добавление в список исследований и пробирок по ключу k в словарь labs
    labs = collections.OrderedDict(sorted(labs.items()))  # Сортировка словаря
    c.setFont('OpenSans', 20)

    paddingx = 17
    data_header = ["№", "ФИО, № истории", "№ емкости", "Тип емкости", "Наименования исследований",
                   "Емкость не принята (замечания)"]
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
                drawTituls(c, p.num_pages, pg_num, paddingx, pg[0])
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
                    research_tmp = research_tmp[0:-(len(research_tmp) - 38)] + "..."
                tmp.append(Paragraph(research_tmp, styleSheet["BodyText"]))
                tmp.append(Paragraph("", styleSheet["BodyText"]))

                data.append(tmp)
                num += 1

            style = TableStyle([
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
                ('LEFTPADDING', (0, 0), (-1, -1), 1),
                ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                ('TOPPADDING', (0, 0), (-1, -1), 1),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1)
            ])
            for span in merge_list:  # Цикл объединения ячеек
                for pos in range(0, 6):
                    style.add('INNERGRID', (pos, merge_list[span][0]),
                              (pos, merge_list[span][0] + len(merge_list[span])), 0.28, colors.white)
                    style.add('BOX', (pos, merge_list[span][0]), (pos, merge_list[span][0] + len(merge_list[span])),
                              0.2, colors.black)
            t = Table(data, colWidths=[int(tw * 0.03), int(tw * 0.23), int(tw * 0.08), int(tw * 0.23), int(tw * 0.31),
                                       int(tw * 0.14)],
                      style=style)

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


def drawTituls(c, pages, page, paddingx, obj):
    """Функция рисования шапки и подвала страницы pdf"""
    c.setFont('OpenSans', 9)
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)

    c.drawCentredString(w / 2, h - 30, SettingManager.get("org_title"))
    c.setFont('OpenSans', 12)
    c.drawCentredString(w / 2, h - 50, "АКТ приёма-передачи емкостей с биоматериалом")

    c.setFont('OpenSans', 10)
    # c.drawString(paddingx * 3, h - 70, "№ " + str(doc_num))
    c.drawRightString(w - paddingx, h - 70,
                      "Дата: " + str(dateformat.format(date.today(), settings.DATE_FORMAT)))

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


@login_required
def get_issledovaniya(request):
    """ Получение списка исследований и направления для ввода результатов"""
    import time
    res = {"issledovaniya": [], "ok": False, "labs": [], "labs_objects": [], "msg": None}
    if request.method == "GET":
        iss = []
        napr = None
        id = request.GET["id"].strip()
        lab_pk = request.GET.get("lab_pk", "-1")
        res["all_confirmed"] = True
        t = request.GET["type"]
        if id.isdigit():
            id = int(id)
            if id >= 4600000000000:
                id -= 4600000000000
                id //= 10
                t = "2"
            if t == "0":
                iss = Issledovaniya.objects.filter(tubes__id=id)
                if iss.count() != 0:
                    napr = iss.first().napravleniye
                iss = iss.filter(research__podrazdeleniye__pk=lab_pk)
            elif t == "2":
                try:
                    napr = Napravleniya.objects.get(pk=id)
                    iss = Issledovaniya.objects.filter(napravleniye__pk=id, research__podrazdeleniye__pk=lab_pk)
                except Napravleniya.DoesNotExist:
                    napr = None
                    iss = []
            else:
                try:
                    napr = Napravleniya.objects.get(pk=id)
                    iss = Issledovaniya.objects.filter(napravleniye__pk=id, research__podrazdeleniye__pk=lab_pk)
                except Napravleniya.DoesNotExist:
                    napr = None
                    iss = []
            mnext = False
            for i in Issledovaniya.objects.filter(napravleniye=napr):
                po = i.research.podrazdeleniye
                p = "" if not po else po.title
                if p not in res["labs"] and po:
                    res["labs"].append(p)
                    res["labs_objects"].append({"pk": po.pk, "title": p, "islab": po.p_type == 2})
                if po and not i.research.is_paraclinic and not i.research.is_doc_refferal:
                    mnext = True
            if len(iss) > 0:
                if not mnext:
                    res["msg"] = "Направление %s не предназначено для лаборатории! Проверьте назначения и номер" % id
                else:
                    groups = {}
                    cnt = 0
                    researches_chk = []
                    for issledovaniye in iss.order_by("deferred", "-doc_save",
                                                      "-doc_confirmation", "tubes__pk",
                                                      "research__sort_weight"):
                        if True:  # issledovaniye.research.hide == 0:
                            if issledovaniye.pk in researches_chk:
                                continue
                            researches_chk.append(issledovaniye.pk)

                            tubes_list = issledovaniye.tubes.exclude(doc_recive__isnull=True).all()
                            tubes = []
                            titles = []
                            for tube_o in tubes_list:
                                tubes.append(tube_o.pk)
                                titles.append(tube_o.type.tube.title)

                            not_received_tubes_list = [str(x.pk) for x in
                                                       issledovaniye.tubes.exclude(doc_recive__isnull=False).all().order_by(
                                                           "pk")]

                            not_received_why = [x.notice for x in
                                                issledovaniye.tubes.exclude(doc_recive__isnull=False).all().order_by("pk")]

                            saved = True
                            confirmed = True
                            doc_save_fio = ""
                            doc_save_id = -1
                            current_doc_save = -1
                            isnorm = "unknown"

                            if not issledovaniye.doc_save:
                                saved = False
                            else:
                                doc_save_id = issledovaniye.doc_save.pk
                                doc_save_fio = issledovaniye.doc_save.get_fio()
                                if doc_save_id == request.user.doctorprofile.pk:
                                    current_doc_save = 1
                                else:
                                    current_doc_save = 0
                                isnorm = "normal"
                                if issledovaniye.result_set.count() > 0:
                                    if any([x.get_is_norm() == "not_normal" for x in issledovaniye.result_set.all()]):
                                        isnorm = "not_normal"
                                    elif any([x.get_is_norm() == "maybe" for x in issledovaniye.result_set.all()]):
                                        isnorm = "maybe"

                            if not issledovaniye.doc_confirmation:
                                confirmed = False
                                if not issledovaniye.deferred:
                                    res["all_confirmed"] = False
                            tb = ','.join(str(v) for v in tubes)

                            if tb not in groups.keys():
                                cnt += 1
                                groups[tb] = cnt
                            ctp = int(0 if not issledovaniye.time_confirmation else int(
                                time.mktime(timezone.localtime(issledovaniye.time_confirmation).timetuple())))
                            ctime = int(time.time())
                            cdid = -1 if not issledovaniye.doc_confirmation else issledovaniye.doc_confirmation.pk
                            rt = SettingManager.get("lab_reset_confirm_time_min") * 60
                            res["issledovaniya"].append({"pk": issledovaniye.pk, "title": issledovaniye.research.title,
                                                         "research_pk": issledovaniye.research.pk,
                                                         "sort": issledovaniye.research.sort_weight,
                                                         "saved": saved,
                                                         "is_norm": isnorm,
                                                         "confirmed": confirmed,
                                                         "status_key": str(saved) + str(confirmed) + str(
                                                             issledovaniye.deferred and not confirmed),
                                                         "not_received_tubes": ", ".join(not_received_tubes_list),
                                                         "not_received_why": ", ".join(not_received_why),
                                                         "tube": {"pk": tb,
                                                                  "title": ' | '.join(titles)},
                                                         "template": str(issledovaniye.research.template),
                                                         "deff": issledovaniye.deferred and not confirmed,
                                                         "doc_save_fio": doc_save_fio,
                                                         "doc_save_id": doc_save_id,
                                                         "current_doc_save": current_doc_save,
                                                         "allow_disable_confirm": ((
                                                                                           ctime - ctp < rt and cdid == request.user.doctorprofile.pk) or request.user.is_superuser or "Сброс подтверждений результатов" in [
                                                                                       str(x) for x in
                                                                                       request.user.groups.all()]) and confirmed,
                                                         "ctp": ctp,
                                                         "ctime": ctime,
                                                         "ctime_ctp": ctime - ctp,
                                                         "ctime_ctp_t": ctime - ctp < rt,
                                                         "period_sec": rt,
                                                         "group": groups[tb]
                                                         })
                    import collections
                    result = collections.defaultdict(lambda: collections.defaultdict(list))

                    for d in res["issledovaniya"]:
                        result[d['status_key']][d['group']].append(d)
                        result[d['status_key']][d['group']] = sorted(result[d['status_key']][d['group']],
                                                                     key=lambda k: k['sort'])

                    res["issledovaniya"] = []

                    def concat(dic):
                        t = [dic[x] for x in dic.keys()]
                        import itertools
                        return itertools.chain(*t)

                    if "FalseFalseFalse" in result.keys():
                        res["issledovaniya"] += concat(result["FalseFalseFalse"])

                    if "TrueFalseFalse" in result.keys():
                        res["issledovaniya"] += concat(result["TrueFalseFalse"])

                    if "FalseFalseTrue" in result.keys():
                        res["issledovaniya"] += concat(result["FalseFalseTrue"])

                    if "TrueFalseTrue" in result.keys():
                        res["issledovaniya"] += concat(result["TrueFalseTrue"])

                    if "FalseTrueFalse" in result.keys():
                        res["issledovaniya"] += concat(result["FalseTrueFalse"])

                    if "TrueTrueFalse" in result.keys():
                        res["issledovaniya"] += concat(result["TrueTrueFalse"])
            if napr:
                res["napr_pk"] = napr.pk
                res["client_fio"] = napr.client.individual.fio()
                res["client_sex"] = napr.client.individual.sex
                res["client_cardnum"] = napr.client.number + " " + napr.client.base.title
                res["client_hisnum"] = napr.history_num
                res["client_vozrast"] = napr.client.individual.age_s(direction=napr)
                res["imported_from_rmis"] = napr.imported_from_rmis
                res["imported_org"] = "" if not napr.imported_org else napr.imported_org.title
                res["directioner"] = "" if napr.imported_from_rmis else napr.doc.fio
                res["otd"] = "" if napr.imported_from_rmis else napr.doc.podrazdeleniye.title
                res["fin_source"] = "" if napr.imported_from_rmis else napr.istochnik_f.title
                res["ok"] = True
                res["in_rmis"] = napr.result_rmis_send
            res["q"] = {"text": id, "type": t}

    return JsonResponse(res)


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
            CustomResearchOrdering(research=directory.Researches.objects.get(pk=order[i]),
                                   user=request.user.doctorprofile, weight=w).save()

    return JsonResponse(1, safe=False)


@login_required
def resend(request):
    t = request.GET.get("type", "directions")
    pks = json.loads(request.GET.get("pks", "[]"))
    from rmis_integration.client import Client
    c = Client()
    d = []
    r = []
    for direction in Napravleniya.objects.filter(pk__in=pks):
        if t in ["directions", "full"]:
            d.append(c.directions.delete_direction(direction=direction, user=request.user.doctorprofile))
        if t in ["results", "full"]:
            r.append(c.directions.delete_services(direction=direction, user=request.user.doctorprofile))
    return JsonResponse(all(d) if t == "directions" else [d, r], safe=False)


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


def form38001(c: Canvas, d: Napravleniya):
    def printForm(offset):
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.2 * mm)
        c.setFont('TimesNewRoman', 8)
        topw1 = pxr(61.5)
        c.drawString(topw1, py(19.6 + offset), "Приложение 5")
        c.drawString(topw1, py(22.74 + offset), "к приказу министерства")
        c.drawString(topw1, py(25.88 + offset), "здравоохранения Иркутской области")
        c.drawString(topw1, py(29.02 + offset), "от 17.08.2009 г. № 1027-мпр.")

        c.setFont('TimesNewRoman', 11)
        c.drawString(px(18.5), py(34 + offset),
                     "Наименование учереждения здравоохранения: " + SettingManager.get("org_title"))
        c.line(px(95.5), py(35.2 + offset), pxr(18), py(35.2 + offset))
        c.drawString(px(18.5), py(43 + offset), "Отделение, палата")
        c.line(px(50), py(44.2 + offset), pxr(18), py(44.2 + offset))
        c.drawCentredString(w / 2, py(53 + offset), "НАПРАВЛЕНИЕ БИОЛОГИЧЕСКОГО МАТЕРИАЛА ДЛЯ ИССЛЕДОВАНИЯ")
        c.drawCentredString(w / 2, py(58 + offset), "НА ВИЧ № {}".format(d.pk))

        c.drawString(px(18.5), py(68 + offset), "Фамилия: " + d.client.individual.family)
        c.line(px(34.8), py(69.2 + offset), pxr(97.5), py(69.2 + offset))
        c.drawString(pxr(97), py(68 + offset), "Имя: " + d.client.individual.name)
        c.line(pxr(88.7), py(69.2 + offset), pxr(18), py(69.2 + offset))

        c.drawString(px(18.5), py(73 + offset), "Отчество: " + d.client.individual.patronymic)
        c.line(px(35), py(74.2 + offset), pxr(114.5), py(74.2 + offset))
        c.drawString(pxr(114), py(73 + offset),
                     "Дата рождения(число,месяц,год): " + d.client.individual.birthday.strftime("%d.%m.%Y"))
        c.line(pxr(58.5), py(74.2 + offset), pxr(18), py(74.2 + offset))

        c.drawString(px(18.5), py(78 + offset), "Адрес регистрации(прописки): " + d.client.main_address)
        c.line(px(71), py(79.2 + offset), pxr(18), py(79.2 + offset))

        c.drawString(px(18.5), py(83 + offset), "Адрес фактического места проживания: " + d.client.fact_address)
        c.line(px(85), py(84.2 + offset), pxr(18), py(84.2 + offset))

        c.drawString(px(18.5), py(88 + offset), "Социальный статус: ")
        c.line(px(52.3), py(89.2 + offset), pxr(18), py(89.2 + offset))

        c.drawString(px(18.5), py(93 + offset), "Код: " + d.vich_code)
        c.line(px(26.3), py(94.2 + offset), px(52), py(94.2 + offset))
        c.drawString(px(53), py(93 + offset), "Диагноз: ")
        c.line(px(68), py(94.2 + offset), pxr(18), py(94.2 + offset))

        c.drawString(px(18.5), py(98 + offset), "ФИО врача, направившего на обследование: {}".format(d.doc.fio))
        c.line(pxr(117.5), py(99.2 + offset), pxr(18), py(99.2 + offset))

        c.drawString(px(18.5), py(103 + offset), "ФИО процедурной м/с: ")
        c.line(px(57.3), py(104.2 + offset), pxr(18), py(104.2 + offset))

        c.drawString(px(18.5), py(108 + offset), "Дата забора крови: «_____»_________________20____г.")

        c.drawString(px(18.5), py(113 + offset),
                     "Дата доставки крови в ИОЦ СПИД: «_____»_________________20____г. (заполняется ИОЦ СПИД)")

        c.drawString(px(18.5), py(123 + offset), "РЕЗУЛЬТАТ ИССЛЕДОВАНИЯ")

        c.drawString(px(18.5), py(133 + offset),
                     "Дата выдачи результата: «_____»_________________20____г.  Подпись ____________________________")

        c.setFont('TimesNewRoman', 8)
        c.drawString(px(18.5), py(139 + offset), "ИС L2. Форма 38001")

    printForm(0)

    c.setStrokeColorRGB(*([0.8] * 3))
    c.line(px(0), h / 2, pxr(0), h / 2)

    printForm(h / 2 / mm)
