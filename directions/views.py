# coding=utf-8
from datetime import date, datetime
from io import BytesIO

import simplejson as json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.utils import dateformat
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import eanbc
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfdoc
from reportlab.pdfgen import canvas

import directory.models as directory
import slog.models as slog
from directions.models import Napravleniya, Issledovaniya, IstochnikiFinansirovaniya, TubesRegistration
from appconf.manager import SettingManager


w, h = A4


@csrf_exempt
@login_required
def dir_save(request):
    """Сохранение направления
    :param request: запрос
    """
    result = {"r": False, "list_id": []}
    """
        r - флаг успешной вставки направлений
        list_id - список сохраненных направлений
    """
    if request.method == 'POST':
        dict_post = json.loads(request.POST['dict'])  # json парсинг принятых данных
        comments = json.loads(request.POST['comments'])  # json парсинг принятых комментариев
        client_id = dict_post["client_id"]  # установка принятого идентификатора пациента
        diagnos = dict_post["diagnos"]  # диагноз
        finsource = dict_post["fin_source"]  # источник финансирования
        researches = dict_post["researches"]  # исследования
        ofname_id = int(request.POST['ofname'])  # Идентификатор врача для выписывания от его имени
        history_num = request.POST['history_num']  # Номер истории болезни
        # is_hospital = request.POST.get('is_hospital', 'false') == "true"
        result = Napravleniya.gen_napravleniya_by_issledovaniya(client_id, diagnos, finsource, history_num, ofname_id,
                                                                request.user.doctorprofile,
                                                                researches, comments)

    return HttpResponse(json.dumps((result,)), content_type="application/json")


@login_required
def get_xls_dir(request):
    """
    Сводная таблица направлений
    :param request:
    :return:
    """
    import xlwt
    response = HttpResponse(content_type='application/ms-excel')
    direction_id = json.loads(request.GET["napr_id"])
    symbols = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
               u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")
    tr = {ord(a): ord(b) for a, b in zip(*symbols)}
    response['Content-Disposition'] = str.translate(
        "attachment; filename='Направления_сводная_таблица_{0}.xls'".format(request.user.doctorprofile.get_fio()), tr)
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("Направления")
    first_color = "light_yellow"
    second_color = "light_green"
    head_color = "ice_blue"
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = xlwt.Style.colour_map[head_color]
    font_style.pattern = pattern
    columns = [
        (u"ФИО", 10000),
        (u"Лаборатория", 8000),
        (u"№ напр.", 2500),
        (u"Пробирка", 8000),
        (u"Исследования", 65535),
    ]
    for col_num in range(len(columns)):
        ws.write(0, col_num, columns[col_num][0], font_style)
        ws.col(col_num).width = columns[col_num][1]
    font_style = xlwt.XFStyle()
    i = 1
    lastfio = ""
    nn = 0

    for dir in Napravleniya.objects.filter(pk__in=direction_id).order_by("client__family"):
        fresearches = set()
        fuppers = set()
        flowers = set()
        for iss in Issledovaniya.objects.filter(napravleniye=dir):
            for fr in iss.research.fractions_set.all():
                absor = directory.Absorption.objects.filter(fupper=fr)
                if absor.exists():
                    fuppers.add(fr.pk)
                    fresearches.add(fr.research.pk)
                    for absor_obj in absor:
                        flowers.add(absor_obj.flower.pk)
                        fresearches.add(absor_obj.flower.research.pk)
        iss = Issledovaniya.objects.filter(napravleniye=dir)
        if lastfio != dir.client.fio():
            nn += 1
            ncolor = first_color
            if nn % 2 == 0:
                ncolor = second_color
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            pattern.pattern_fore_colour = xlwt.Style.colour_map[ncolor]
            font_style.pattern = pattern
            lastfio = dir.client.fio()
            ws.write(i, 0, lastfio, font_style)
        else:
            ws.write(i, 0, "", font_style)
        ws.write(i, 1, iss.first().research.subgroup.podrazdeleniye.title, font_style)
        ws.write(i, 2, dir.pk, font_style)
        fractiontubes = {}
        hasoak = False
        relpk = -1
        for isobj in iss:
            for fraction in directory.Fractions.objects.filter(research=isobj.research).order_by("sort_weight"):
                rpk = fraction.relation.pk
                if fraction.research.pk in fresearches and fraction.pk in flowers:
                    absor = directory.Absorption.objects.filter(flower__pk=fraction.pk).first()
                    if absor.fupper.pk in fuppers:
                        rpk = absor.fupper.relation.pk
                        if rpk not in fractiontubes.keys():
                            fractiontubes[rpk] = {"tt": absor.fupper.relation.tube.title, "researches": set()}
                elif rpk not in fractiontubes.keys():
                    fractiontubes[rpk] = {"tt": fraction.relation.tube.title, "researches": set()}
                fractiontubes[rpk]["researches"].add(isobj.research.title)
        prei = i
        for key in fractiontubes.keys():
            if i - prei > 0:
                ws.write(i, 0, "", font_style)
            if i - prei > 0:
                ws.write(i, 1, "", font_style)
                ws.write(i, 2, "", font_style)
            ws.write(i, 3, fractiontubes[key]["tt"], font_style)
            ws.write(i, 4, ", ".join(fractiontubes[key]["researches"]), font_style)
            i += 1
    wb.save(response)
    return response


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
        import datetime
        date_start = datetime.date(int(date_start.split(".")[2]), int(date_start.split(".")[1]),
                                   int(date_start.split(".")[0]))
        date_end = datetime.date(int(date_end.split(".")[2]), int(date_end.split(".")[1]),
                                 int(date_end.split(".")[0])) + datetime.timedelta(1)

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
    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
    pdfmetrics.registerFont(
        TTFont('OpenSans', PROJECT_ROOT + '/../static/fonts/OpenSans.ttf'))
    elements = []
    hb = False
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
            hb = True
            continue
        hb = False
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
        data = []
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
                                    inobj.issledovaniya_set.first().napravleniye.client.individual.age_s(iss=inobj.issledovaniya_set.first()) + "<br/>№ напр.: " + str(
                        inobj.issledovaniya_set.first().napravleniye.pk) + "<br/>" + "№ пробирки.: " + str(
                        inobj.pk) + "<br/>" + Truncator(
                        inobj.issledovaniya_set.first().napravleniye.doc.podrazileniye.title).chars(19) + "<br/><br/>")
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
@login_required
def gen_pdf_dir(request):
    """Генерация PDF направлений"""
    if SettingManager.get("pdf_auto_print", "true", "b"):
        pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:true,bSilent:false,bShrinkToFit:true}\);)>>'
    direction_id = json.loads(request.GET["napr_id"])  # Перевод JSON строки в объект

    response = HttpResponse(content_type='application/pdf')  # Формирование ответа типа PDF
    response['Content-Disposition'] = 'inline; filename="napr.pdf"'  # Включение режима вывода PDF в браузер

    buffer = BytesIO()  # Буфер
    c = canvas.Canvas(buffer, pagesize=A4)  # Создание холста для PDF размера А4
    framePage(c)  # Рисование разделительных линий для страницы

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os.path

    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))  # Путь до текущего скрипта

    pdfmetrics.registerFont(
        TTFont('OpenSans', PROJECT_ROOT + '/../static/fonts/OpenSans.ttf'))  # Загрузка шрифта из файла

    p = Paginator(direction_id, 4)  # Деление списка направлений по 4

    for pg_num in p.page_range:  # Перебор страниц
        pg = p.page(pg_num)  # Выбор страницы по номеру
        i = 4  # Номер позиции направления на странице (4..1)
        for obj in pg.object_list:  # Перебор номеров направлений на странице
            printDirection(c, i,
                           Napravleniya.objects.get(
                               pk=int(obj)))  # Вызов функции печати направления на указанную позицию
            i -= 1
        if pg.has_next():  # Если есть следующая страница
            c.showPage()  # Создание новой страницы
            framePage(c)  # Рисование разделительных линий для страницы
    c.save()  # Сохранение отрисованного на PDF

    pdf = buffer.getvalue()  # Получение данных из буфера
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


def printDirection(c, n, dir):
    # Нанесение одного направления на документ на свою зону
    xn = 0
    if n % 2 != 0: xn = 1
    yn = 0
    if n > 2: yn = 1
    barcode = eanbc.Ean13BarcodeWidget(dir.pk + 460000000000, humanReadable=0,
                                       barHeight=17)  # Генерация штрих-кода с номером вида 460000001005
    bounds = barcode.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    d = Drawing(width, height)
    d.add(barcode)
    paddingx = 15

    c.setFont('OpenSans', 10)
    c.drawCentredString(w / 2 - w / 4 + (w / 2 * xn), (h / 2 - height - 5) + (h / 2) * yn,
                        SettingManager.get("org_title"))

    c.setFont('OpenSans', 8)
    c.drawCentredString(w / 2 - w / 4 + (w / 2 * xn), (h / 2 - height - 15) + (h / 2) * yn,
                        "(%s. %s)" % (SettingManager.get("org_address"), SettingManager.get("org_phones"),))

    c.setFont('OpenSans', 14)
    c.drawCentredString(w / 2 - w / 4 + (w / 2 * xn), (h / 2 - height - 30) + (h / 2) * yn, "Направление")

    renderPDF.draw(d, c, w / 2 - width + (w / 2 * xn) - paddingx / 3, (h / 2 - height - 57) + (h / 2) * yn)

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
                      "Возраст: " + dir.client.individual.age_s(direction=dir))

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 90) + (h / 2) * yn,
                 "Номер карты: " + dir.client.number_with_type())

    if dir.diagnos.strip() != "":
        c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 100) + (h / 2) * yn, "Диагноз: " + dir.diagnos)

    if dir.istochnik_f:
        c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 110) + (h / 2) * yn,
                     "Источник финансирования: " + dir.client.base.title + " - " + dir.istochnik_f.tilie)
    else:
        c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 110) + (h / 2) * yn, "Источник финансирования: ")

    issledovaniya = Issledovaniya.objects.filter(napravleniye=dir)

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 120) + (h / 2) * yn,
                 "Лаборатория: " + issledovaniya[0].research.subgroup.podrazdeleniye.title)

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 134) + (h / 2) * yn, "Наименования исследований: ")
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)

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
        values.append({"title": v.research.title, "sw": v.research.sort_weight,
                       "g": v.research.fractions_set.first().relation.pk})

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
            tmp.append(Paragraph('<font face="OpenSans" size="' + str(font_size) + '">' + obj["title"] + "</font>",
                                 styleSheet["BodyText"]))
        if len(pg.object_list) < 2:
            tmp.append(Paragraph('<font face="OpenSans" size="' + str(font_size) + '"></font>', styleSheet["BodyText"]))
        data.append(tmp)

    tw = w / 2 - paddingx * 2
    t = Table(data, colWidths=[int(tw / 2), int(tw / 2)])
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
    t.drawOn(c, paddingx + (w / 2 * xn), ((h / 2 - height - 138) + (h / 2) * yn - ht))

    c.setFont('OpenSans', 8)
    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 138) + (h / 2) * yn - ht - 10,
                 "Всего назначено: " + str(len(issledovaniya)))

    c.drawString(paddingx + (w / 2 * xn), 27 + (h / 2) * yn, "Отделение: " + dir.doc.podrazileniye.title)
    c.drawString(paddingx + (w / 2 * xn), 15 + (h / 2) * yn, "Врач: " + dir.doc.get_fio())
    c.setFont('OpenSans', 7)
    c.setLineWidth(0.25)
    c.line(w / 2 * (xn + 1) - paddingx, 23 + (h / 2) * yn, w / 2 * (xn + 1) - 82, 23 + (h / 2) * yn)
    c.drawRightString(w / 2 * (xn + 1) - paddingx - paddingx, 15 + (h / 2) * yn, "(подпись)")


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
    if request.method == 'GET':  # Проверка типа запроса
        id = int(request.GET['id'])  # Получение идентификатора направления
        if Napravleniya.objects.filter(pk=id).exists():  # Проверка на существование направления
            if "check" not in request.GET.keys():
                tmp2 = Napravleniya.objects.get(pk=id)
                tmp = Issledovaniya.objects.filter(napravleniye=tmp2).order_by("research__title")
                response["direction"] = {"pk": tmp2.pk,
                                         "cancel": tmp2.cancel,
                                         "date": str(
                                             dateformat.format(tmp2.data_sozdaniya.date(), settings.DATE_FORMAT)),
                                         "doc": {"fio": tmp2.doc.get_fio(), "otd": tmp2.doc.podrazileniye.title},
                                         "lab": tmp[0].research.subgroup.podrazdeleniye.title}  # Формирование вывода
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
    return HttpResponse(json.dumps(response), content_type="application/json")  # Создание JSON


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
    return HttpResponse(json.dumps(response), content_type="application/json")  # Создание JSON


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
    return HttpResponse(json.dumps(response), content_type="application/json")  # Создание JSON


@csrf_exempt
@login_required
def update_direction(request):
    """Функция обновления исследований в направлении"""
    from django.utils import timezone

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

    return HttpResponse(json.dumps(res), content_type="application/json")  # Создание JSON


@csrf_exempt
@login_required
def group_confirm_get(request):
    """Функция группового подтвержения взятия материала"""
    from django.utils import timezone
    res = {"r": False}
    if request.method == 'POST':  # Проверка типа запроса
        checked = json.loads(request.POST["checked"])

        for t in TubesRegistration.objects.filter(pk__in=checked, doc_get__isnull=True):
            t.set_get(request.user.doctorprofile)

    return HttpResponse(json.dumps(res), content_type="application/json")  # Создание JSON


@login_required
def load_history(request):
    """Получение истории заборов материала за текущий день"""
    import pytz

    res = {"rows": []}
    tubes = TubesRegistration.objects.filter(doc_get=request.user.doctorprofile).order_by('time_get').exclude(
        time_get__lt=datetime.now().date())  # Выборка материала за сегодня
    local_tz = pytz.timezone(settings.TIME_ZONE)  # Формирование временной зоны

    for v in tubes:  # Перебор пробирки
        iss = Issledovaniya.objects.filter(tubes__id=v.id)  # Выборка исследований по пробирке
        iss_list = []
        for val in iss:  # Перебор выбранных исследований
            iss_list.append(val.research.title)  # Добавление в список исследований по пробирке
        res["rows"].append({"type": v.type.tube.title, "researches": ', '.join(str(x) for x in iss_list),
                            "time": v.time_get.astimezone(local_tz).strftime("%H:%M:%S"),
                            "dir_id": iss[0].napravleniye.pk, "tube_id": v.id})  # Добавление пробирки с исследованиями
        # в вывод
    return HttpResponse(json.dumps(res), content_type="application/json")  # Создание JSON


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

    return HttpResponse(json.dumps(res), content_type="application/json")  # Создание JSON


@login_required
def print_history(request):
    """Печать истории забора материала за день"""
    user = request.user.doctorprofile  # Профиль текущего пользователя
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    styleSheet = getSampleStyleSheet()
    import os.path
    import collections
    import pytz

    filter = False
    filterArray = []
    if "filter" in request.GET.keys():
        filter = True
        filterArray = json.loads(request.GET["filter"])

    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))  # Директория Django
    pdfmetrics.registerFont(TTFont('OpenSans', PROJECT_ROOT + '/../static/fonts/OpenSans.ttf'))  # Загрузка шрифта

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
    local_tz = pytz.timezone(settings.TIME_ZONE)  # Локальная временная зона
    labs = {}  # Словарь с пробирками, сгруппироваными по лаборатории
    for v in tubes:  # Перебор пробирок
        idv = v.id
        iss = Issledovaniya.objects.filter(tubes__id=v.id)  # Получение исследований для пробирки
        iss_list = []  # Список исследований
        k = v.doc_get.podrazileniye.title + "@" + str(iss[
                                                          0].research.subgroup.title)  # Формирование ключа для группировки по подгруппе лаборатории и названию подразделения направившего на анализ врача
        for val in iss:  # Цикл перевода полученных исследований в список
            iss_list.append(val.research.title)
        if k not in labs.keys():  # Добавление списка в словарь если по ключу k нету ничего в словаре labs
            labs[k] = []
        for value in iss_list:  # Перебор списка исследований
            labs[k].append(
                {"type": v.type.tube.title, "researches": value,
                 "client-type": iss[0].napravleniye.client.base.short_title,
                 "lab_title": iss[0].research.subgroup.title,
                 "time": v.time_get.astimezone(local_tz).strftime("%H:%M:%S"), "dir_id": iss[0].napravleniye.pk,
                 "podr": v.doc_get.podrazileniye.title,
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
                drawTituls(c, user, p.num_pages, pg_num, paddingx, pg[0])
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


def drawTituls(c, user, pages, page, paddingx, obj, lab=""):
    """Функция рисования шапки и подвала страницы pdf"""
    c.setFont('OpenSans', 9)
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)

    c.drawCentredString(w / 2, h - 30, SettingManager.get("org_title"))
    c.setFont('OpenSans', 12)
    c.drawCentredString(w / 2, h - 50, "АКТ приема-передачи емкостей с биоматериалом")

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
    res = {"issledovaniya": [], "ok": False}
    if request.method == "GET":
        iss = []
        napr = None
        id = request.GET["id"]
        res["all_confirmed"] = True
        su = request.user.is_superuser
        if id.isnumeric():
            if request.GET["type"] == "0":
                if TubesRegistration.objects.filter(pk=id).count() == 1:
                    tube = TubesRegistration.objects.get(pk=id)
                    if tube.doc_recive:
                        iss = Issledovaniya.objects.filter(tubes__id=id)
                        if iss:
                            napr = iss.first().napravleniye
                elif TubesRegistration.objects.filter(pk=id).count() > 1:
                    tubes = TubesRegistration.objects.filter(pk=id)
                    for tube in tubes:
                        if tube.doc_recive:
                            lit = Issledovaniya.objects.filter(tubes__id=id)
                            if lit.count() != 0:
                                iss = []
                            for i in lit:
                                iss.append(i)
                    if len(iss) > 0:
                        napr = iss[0].napravleniye
            elif request.GET["type"] == "2":
                try:
                    napr = Napravleniya.objects.get(pk=id)
                    iss = Issledovaniya.objects.filter(napravleniye__pk=id)
                except Napravleniya.DoesNotExist:
                    napr = None
                    iss = []
            else:
                try:
                    napr = Napravleniya.objects.get(pk=id)
                    iss = Issledovaniya.objects.filter(napravleniye__pk=id)
                except Napravleniya.DoesNotExist:
                    napr = None
                    iss = []
            if len(iss) > 0:
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
                                                   issledovaniye.tubes.exclude(doc_recive__isnull=False).all()]

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
                            time.mktime(issledovaniye.time_confirmation.timetuple()))) + 8 * 60 * 60
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
                                                     "tube": {"pk": tb,
                                                              "title": ' | '.join(titles)},
                                                     "template": str(issledovaniye.research.template),
                                                     "deff": issledovaniye.deferred and not confirmed,
                                                     "doc_save_fio": doc_save_fio,
                                                     "doc_save_id": doc_save_id,
                                                     "current_doc_save": current_doc_save,
                                                     "allow_disable_confirm": ((ctime - ctp < rt and cdid == request.user.doctorprofile.pk) or request.user.is_superuser or "Сброс подтверждений результатов" in [str(x) for x in request.user.groups.all()]) and confirmed,
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
                res["directioner"] = napr.doc.fio
                res["otd"] = napr.doc.podrazileniye.title
                res["fin_source"] = napr.istochnik_f.tilie
                res["ok"] = True
                res["in_rmis"] = napr.result_rmis_send

    return HttpResponse(json.dumps(res), content_type="application/json")  # Создание JSON


from django.db.models import Q


@login_required
def get_client_directions(request):
    """ Получение направлений для пациента """
    import datetime
    res = {"directions": [], "ok": False}
    if request.method == "GET":
        try:
            pk = int(request.GET["pk"])
            req_status = int(request.GET["status"])
            date_start = request.GET["date[start]"]  # начальная дата назначения
            date_end = request.GET["date[end]"]  # конечная дата назначения

            date_start = datetime.date(int(date_start.split(".")[2]), int(date_start.split(".")[1]),
                                       int(date_start.split(".")[0]))
            date_end = datetime.date(int(date_end.split(".")[2]), int(date_end.split(".")[1]),
                                     int(date_end.split(".")[0])) + datetime.timedelta(1)
            if pk >= 0 or req_status == 4:
                rows = []
                if req_status != 4:
                    rows = Napravleniya.objects.filter(data_sozdaniya__range=(date_start, date_end),
                                                       client__pk=pk).order_by("-data_sozdaniya").prefetch_related()
                else:
                    rows = Napravleniya.objects.filter(Q(data_sozdaniya__range=(date_start, date_end),
                                                         doc_who_create=request.user.doctorprofile)
                                                       | Q(data_sozdaniya__range=(date_start, date_end),
                                                           doc=request.user.doctorprofile)).order_by(
                        "-data_sozdaniya").prefetch_related()

                for napr in rows:
                    iss_list = Issledovaniya.objects.filter(napravleniye=napr)
                    if not iss_list.exists():
                        continue
                    status = 2  # 0 - выписано. 1 - Материал получен лабораторией. 2 - результат подтвержден. -1 - отменено
                    has_conf = False
                    for v in iss_list:
                        iss_status = 1
                        if not v.doc_confirmation and not v.doc_save and not v.deferred:
                            iss_status = 1
                            if v.tubes.count() == 0:
                                iss_status = 0
                            for t in v.tubes.all():
                                if not t.time_recive:
                                    iss_status = 0
                        elif v.doc_confirmation or v.deferred:
                            iss_status = 2
                        if v.doc_confirmation and not has_conf:
                            has_conf = True
                        status = min(iss_status, status)
                        tmpiss = v
                    if status == 2 and not has_conf:
                        status = 1
                    if req_status in [3, 4] or req_status == status:
                        res["directions"].append(
                            {"pk": napr.pk, "status": status,
                             "researches": ' | '.join(v.research.title for v in iss_list),
                             "date": str(dateformat.format(napr.data_sozdaniya.date(), settings.DATE_FORMAT)),
                             "lab": iss_list[0].research.subgroup.podrazdeleniye.title, "cancel": napr.cancel})
                res["ok"] = True
        except ValueError:
            pass
    return HttpResponse(json.dumps(res), content_type="application/json")  # Создание JSON


@csrf_exempt
@login_required
def order_researches(request):
    from directions.models import CustomResearchOrdering
    if request.method == "POST":
        order = json.loads(request.POST.get("order", "[]"))
        lab = request.POST.get("lab")
        CustomResearchOrdering.objects.filter(research__subgroup__podrazdeleniye_id=lab).delete()
        for i in range(len(order)):
            w = len(order) - i
            CustomResearchOrdering(research=directory.Researches.objects.get(pk=order[i]),
                                   user=request.user.doctorprofile, weight=w).save()

    return HttpResponse(1, content_type="application/json")


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
            d.append(c.directions.delete_direction(direction, user=request.user.doctorprofile))
        if t in ["results", "full"]:
            r.append(c.directions.delete_services(direction, user=request.user.doctorprofile))
    return HttpResponse(json.dumps(all(d) if t == "directions" else [d, r]), content_type="application/json")
