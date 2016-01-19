# coding=utf-8
from io import BytesIO
from datetime import date, datetime

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import simplejson as json
from reportlab.pdfgen import canvas
from django.core.paginator import Paginator
from reportlab.graphics.barcode import eanbc, code39
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.pagesizes import A4
from django.conf import settings
from django.utils import dateformat

from researches.models import Researches
from directions.models import Napravleniya, Issledovaniya, IstochnikiFinansirovaniya, TubesRegistration
from clients.models import Importedclients
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from laboratory.decorators import group_required
import slog.models as slog
import directory.models as directory
import users.models as umodels

from reportlab.pdfbase import pdfdoc
pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:true,bSilent:false,bShrinkToFit:true}\);)>>'

w, h = A4


@csrf_exempt
@login_required
def dir_save(request):
    """Сохранение направления"""
    res = {}  # Словарь с направлениями, сгруппированными по лабораториям
    result = {"r": False, "list_id": [], "mda": ""}
    """
        r - флаг успешной вставки направлений
        list_id - список сохраненных направлений
        mda - отладка
    """
    if request.method == 'POST':
        dict = json.loads(request.POST['dict'])  # json парсинг принятых данных
        client_id = dict["client_id"]  # установка принятого идентификатора пациента
        diagnos = dict["diagnos"]  # диагноз
        finsource = dict["fin_source"]  # источник финансирования
        researches = dict["researches"]  # исследования
        researches_grouped_by_lab = []  # Лист с выбранными исследованиями по лабораториям
        ofname_id = int(request.POST['ofname'])  # Идентификатор врача для выписывания от его имени
        history_num = request.POST['history_num']  # Номер истории болезни
        ptype = request.POST['type']
        i = 0  # Идентификатор направления
        checklist = []
        if client_id and researches:  # если client_id получен и исследования получены
            ofname = None
            if ofname_id > -1:
                ofname = umodels.DoctorProfile.objects.get(pk=ofname_id)

            no_attach = False
            conflict_list = []
            conflict_keys = []
            for v in researches:  # нормализация исследований
                if v and v not in checklist:
                    # checklist.append(v)
                    researches_grouped_by_lab.append(
                        {i: v})  # добавление словаря в лист, ключом которого является идентификатор исследования
                    # [{5:[0,2,5,7]},{6:[8]}] 5 - id лаборатории, [0,2,5,7] - id исследований из справочника

                    for vv in v:
                        if not vv or not vv.isnumeric():
                            continue
                        research_tmp = directory.Researches.objects.get(pk=int(vv))
                        if research_tmp.no_attach and research_tmp.no_attach > 0:
                            if research_tmp.no_attach not in conflict_keys:
                                conflict_keys.append(research_tmp.no_attach)
                                if not no_attach:
                                    conflict_list = [research_tmp.title]
                            else:
                                no_attach = True
                                conflict_list.append(research_tmp.title)
                i += 1

            for v in researches_grouped_by_lab:  # цикл перевода листа в словарь
                for key in v.keys():
                    res[key] = v[key]
                    # {5:[0,2,5,7],6:[8]}

            if not no_attach:
                # TODO: Обратить внимание!
                # TODO: Нарисовать отдельную блок-схему

                directionsForResearches = {}  # Словарь для временной записи направлений.
                # Исследование привязываются к направлению по группе

                finsource = IstochnikiFinansirovaniya.objects.get(pk=finsource)  # получение источника финансирования
                result["mda"] += json.dumps(res)

                for key in res:  # перебор лабораторий
                    for v in res[key]:  # перебор выбраных исследований в лаборатории
                        research = directory.Researches.objects.get(pk=v)  # получение объекта исследования по id

                        dir_group = -1
                        if research.direction:
                            dir_group = research.direction.pk  # получение группы исследования
                        # Если группа == 0, исследование не группируется с другими в одно направление
                        if dir_group >= 0 and dir_group not in directionsForResearches.keys():
                            # Если исследование может группироваться и направление для группы не создано

                            # Создание направления для группы
                            directionsForResearches[dir_group] = Napravleniya(
                                client=Importedclients.objects.get(pk=client_id),
                                # Привязка пациента к направлению
                                doc=request.user.doctorprofile,
                                # Привязка врача к направлению
                                istochnik_f=finsource,
                                # Установка источника финансирования
                                diagnos=diagnos, cancel=False)  # Установка диагноза
                            if ofname_id > -1 and ofname:
                                directionsForResearches[dir_group].doc = ofname
                                directionsForResearches[dir_group].doc_who_create = request.user.doctorprofile
                            if ptype == "stat":
                                directionsForResearches[dir_group].history_num = history_num

                            directionsForResearches[dir_group].save()  # Сохранение направления

                            result["mda"] += str(dir_group)  # Отладка
                            result["list_id"].append(
                                directionsForResearches[dir_group].pk)  # Добавление ID в список созданых направлений
                        if dir_group < 0:  # если исследование не должно группироваться
                            dir_group = "id" + str(
                                research.pk)  # формирование ключа (группы) для негруппируемого исследования

                            # Создание направления для исследования
                            directionsForResearches[dir_group] = Napravleniya(
                                client=Importedclients.objects.get(pk=client_id),
                                # Привязка пациента к направлению
                                doc=request.user.doctorprofile,
                                # Привязка врача к направлению
                                istochnik_f=finsource,
                                # Установка источника финансирования
                                diagnos=diagnos)  # Установка диагноза
                            if ofname_id > -1 and ofname:
                                directionsForResearches[dir_group].doc = ofname
                                directionsForResearches[dir_group].doc_who_create = request.user.doctorprofile
                            if ptype == "stat":
                                directionsForResearches[dir_group].history_num = history_num
                            directionsForResearches[dir_group].save()  # Сохранение направления
                            result["list_id"].append(
                                directionsForResearches[dir_group].pk)  # Добавление ID в список созданых направлений
                            result["mda"] += str(dir_group) + " | "  # Добавление в отладочный вывод
                        issledovaniye = Issledovaniya(napravleniye=directionsForResearches[dir_group],
                                                      # Установка направления для группы этого исследования
                                                      research=research, deferred=False)  # Создание направления на исследование
                        issledovaniye.save()  # Сохранение направления на исследование

                result["r"] = True  # Флаг успешной вставки в True
                result["list_id"] = json.dumps(result["list_id"])  # Перевод списка созданых направлений в JSON строку
                slog.Log(key=json.dumps(result["list_id"]), user=request.user.doctorprofile, type=21,
                         body=request.POST['dict']).save()

            else:
                result["r"] = False
                result["message"] = "Следующие анализы не могут быть назначены вместе: " + ", ".join(conflict_list)
    return HttpResponse(json.dumps((result,)), content_type="application/json")

@login_required
def get_xls_dir(request):
    import xlwt
    response = HttpResponse(content_type='application/ms-excel')
    direction_id = json.loads(request.GET["napr_id"])
    symbols = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
           u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")
    tr = {ord(a):ord(b) for a, b in zip(*symbols)}
    response['Content-Disposition'] = str.translate("attachment; filename='Направления_сводная_таблица_{0}.xls'".format(request.user.doctorprofile.get_fio()), tr)
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
    import  directory.models as dirmodels


    for dir in Napravleniya.objects.filter(pk__in=direction_id).order_by("client__family"):
        fresearches = set()
        fuppers = set()
        flowers = set()
        for iss in Issledovaniya.objects.filter(napravleniye=dir):
            for fr in iss.research.fractions_set.all():
                absor = dirmodels.Absorption.objects.filter(fupper=fr)
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
            for fraction in dirmodels.Fractions.objects.filter(research=isobj.research).order_by("sort_weight"):
                rpk = fraction.relation.pk
                if fraction.research.pk in fresearches and fraction.pk in flowers:
                    absor = dirmodels.Absorption.objects.filter(flower__pk=fraction.pk).first()
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
from reportlab.lib.pagesizes import inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

import random
@login_required
def gen_pdf_execlist(request):
    type = int(request.GET["type"])
    date_start = request.GET["datestart"]
    date_end = request.GET["dateend"]
    if type != 2:
        import datetime
        date_start = datetime.date(int(date_start.split(".")[2]), int(date_start.split(".")[1]),int(date_start.split(".")[0]))
        date_end = datetime.date(int(date_end.split(".")[2]), int(date_end.split(".")[1]), int(date_end.split(".")[0])) + datetime.timedelta(1)

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
    import numpy as np
    import os.path
    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
    pdfmetrics.registerFont(
        TTFont('OpenSans', PROJECT_ROOT + '/../static/fonts/OpenSans.ttf'))
    elements = []
    hb = False
    for res in directory.Researches.objects.filter(pk__in=researches):
        if type != 2:
            iss_list = Issledovaniya.objects.filter(tubes__doc_recive_id__isnull=False, tubes__time_recive__range=(date_start, date_end), doc_confirmation_id__isnull=True, research__pk=res.pk, deferred=False)
        else:
            iss_list = Issledovaniya.objects.filter(research__pk=res.pk, deferred=True, doc_confirmation__isnull=True, tubes__doc_recive__isnull=False)

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
                #if not tube.doc_recive:
                #    pass
                #else:
                tubes.append(tube)
        if len(tubes) == 0:
            continue
        data = []
        pn += 1
        p = Paginator(tubes, xsize*(ysize-1))

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
                    data[-1].append(inobj.issledovaniya_set.first().napravleniye.client.family + " " + inobj.issledovaniya_set.first().napravleniye.client.name[0] + "." + inobj.issledovaniya_set.first().napravleniye.client.twoname[0] + "., " + str(inobj.issledovaniya_set.first().napravleniye.client.age()) + "<br/>№ напр.: " + str(inobj.issledovaniya_set.first().napravleniye.pk) + "<br/>" + "№ пробирки.: " + str(inobj.pk) + "<br/><br/><br/>")
            if len(data) < ysize:
                for i in range(len(data), ysize):
                    data.append([])
            for y in range(0, ysize):
                if len(data[y]) < xsize:
                    for i in range(len(data[y]), xsize):
                        data[y].append("<br/><br/><br/><br/><br/>")
            style = TableStyle([('ALIGN',(0,0),(-1,-1),'LEFT'),
                                   ('INNERGRID', (0,0), (-1,-1), 0.3, colors.black),
                                   ('BOX', (0,0), (-1,-1), 0.3, colors.black),
                                   ])

            s = getSampleStyleSheet()
            s = s["BodyText"]
            s.wordWrap = 'LTR'
            data = np.array(data).T
            data2 = [[Paragraph('<font face="OpenSans" size="7">' + cell + "</font>", s) for cell in row] for row in data]
            tw = lw - 90
            t=Table(data2, colWidths=[int(tw / 8), int(tw / 8), int(tw / 8), int(tw / 8), int(tw / 8), int(tw / 8), int(tw / 8), int(tw / 8)])
            t.setStyle(style)
            st = ""
            if type == 2:
                st = ", отложенные"
            elements.append(Paragraph('<font face="OpenSans" size="10">' + res.title + st + ", " +  str(pg_num) + " стр<br/><br/></font>", s))
            elements.append(t)
            elements.append(PageBreak())

    doc.build(elements)
    pdf = buffer.getvalue()  # Получение данных из буфера
    buffer.close()  # Закрытие буфера
    response.write(pdf)  # Запись PDF в ответ
    return response


def frameOctahedralPage(canvas, lw, lh, xsize, ysize, padding, lpadding):
    n = 0
    fam = ["Касъяненко", "Привалов", "Михайлов", "Селиверстов", "Красильников", "Овчинников"]
    initials = ["С.Н.", "М.С.", "И.И.", "С.А.", "А.С."]
    canvas.setFont('OpenSans', 7)
    for y in reversed(range(1,ysize+1)):
        canvas.line(lpadding + padding, (lh - padding)/ysize*y, lw - padding, (lh - padding)/ysize*y)
        for x in range(1, xsize+1):
            n += 1
            canvas.line((lw-padding-lpadding)/xsize*x + lpadding, padding, (lw-padding-lpadding)/xsize*x + lpadding, lh - padding)
            tx = (lw-padding-lpadding)/xsize*x + lpadding + 2 - (lw-padding-lpadding)/xsize
            ty = (lh - padding)/ysize*y
            if x == 1:
                tx += 16
            canvas.setFont('OpenSans', 7)
            canvas.drawString(tx, ty - 11, random.choice(fam) + " " + random.choice(initials) + ", " + str(random.randrange(10,99)) + " л")
            canvas.drawString(tx, ty - 22, "№ напр.: " + str(random.randrange(6600, 150000)))
            canvas.drawString(tx, ty - 33, "№ пробирки.: " + str(random.randrange(10000, 400000)))
            #canvas.circle(tx + (lw - padding)/xsize - 23, ty - 12, 9, fill=0)
            #canvas.drawCentredString(tx + (lw - padding)/xsize - 23, ty - 16, str(n))

    canvas.line(lpadding + padding, padding, lw - padding, padding)
    canvas.line(lpadding + padding, padding, lpadding + padding, lh - padding)

@cache_page(60 * 15)
@login_required
def gen_pdf_dir(request):
    """Генерация PDF направлений"""
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
                           Napravleniya.objects.get(pk=int(obj)))  # Вызов функции печати направления на указанную позицию
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
                        "Клиники ГБОУ ВПО ИГМУ Минздрава России")

    c.setFont('OpenSans', 8)
    c.drawCentredString(w / 2 - w / 4 + (w / 2 * xn), (h / 2 - height - 15) + (h / 2) * yn,
                        "(г. Иркутск, б-р. Гагарина, 18. тел: 280-808, 280-809)")

    c.setFont('OpenSans', 14)
    c.drawCentredString(w / 2 - w / 4 + (w / 2 * xn), (h / 2 - height - 30) + (h / 2) * yn, "Направление")

    renderPDF.draw(d, c, w / 2 - width + (w / 2 * xn) - paddingx / 3, (h / 2 - height - 57) + (h / 2) * yn)

    c.setFont('OpenSans', 20)
    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height) + (h / 2) * yn - 57, "№ " + str(dir.pk))  # Номер направления

    c.setFont('OpenSans', 9)
    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 70) + (h / 2) * yn,
                 "Дата: " + str(dateformat.format(dir.data_sozdaniya.date(), settings.DATE_FORMAT)))
    if dir.history_num and len(dir.history_num) > 0:
        c.drawRightString(w / 2 * (xn + 1) - paddingx, (h / 2 - height - 70) + (h / 2) * yn, "№ истории: " + dir.history_num)

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 80) + (h / 2) * yn,
                 "ФИО: " + dir.client.family + " " + dir.client.name + " " + dir.client.twoname)

    c.drawRightString(w / 2 * (xn + 1) - paddingx, (h / 2 - height - 90) + (h / 2) * yn,
                      "Возраст: " + dir.client.age_s())

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 90) + (h / 2) * yn, "Номер карты: " + str(dir.client.num))

    c.drawCentredString(w / 2 - w / 4 + (w / 2 * xn), (h / 2 - height - 90) + (h / 2) * yn, "Пол: " + dir.client.sex)

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 100) + (h / 2) * yn, "Диагноз: " + dir.diagnos)

    d = {"poli": "Поликлиника", "stat": "Стационар"}

    if dir.istochnik_f:
        c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 110) + (h / 2) * yn,
                     "Источник финансирования: " + d[dir.istochnik_f.istype] + " - " + dir.istochnik_f.tilie)
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
    font_size = max_f - (max_off * (all_iss/max_res))


    styleSheet["BodyText"].leading = font_size+0.5
    data = []

    values = []

    for v in issledovaniya:
        values.append({"title": v.research.title, "sw": v.research.sort_weight, "g": v.research.fractions_set.first().relation.pk})

    values.sort(key=lambda l: (l["g"], l["sw"]))

    n_rows = int(len(values)/2)

    normvars = []
    c_cnt = nc_cnt = 0
    for i in range(0, len(values)+1):
        if (i+1) % 2 == 0:
            nc_cnt += 1
            if nc_cnt+n_rows < len(values):
                normvars.append(values[nc_cnt+n_rows])
        else:
            normvars.append(values[c_cnt])
            c_cnt += 1


    p = Paginator(normvars, 2)

    for pg_num in p.page_range:
        pg = p.page(pg_num)
        tmp = []
        for obj in pg.object_list:
            tmp.append(Paragraph('<font face="OpenSans" size="'+str(font_size)+'">' + obj["title"] + "</font>",
                                 styleSheet["BodyText"]))
        if len(pg.object_list) < 2:
            tmp.append(Paragraph('<font face="OpenSans" size="'+str(font_size)+'"></font>', styleSheet["BodyText"]))
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
                                         "date": str(dateformat.format(tmp2.data_sozdaniya.date(), settings.DATE_FORMAT)),
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
                    s = False  # Статус взятия материала для исследований
                    if tube.time_get and tube.doc_get:  # Проверка статуса пробирки
                        s = True  # Установка статуса для вывода в интерфейс
                    response["tubes"][tube.id]["status"] = s  # Установка статуса в объект пробирки

                response["client"] = {"fio": tmp2.client.family + " " + tmp2.client.name + " " + tmp2.client.twoname,
                                      "sx": tmp2.client.sex, "bth": str(
                    dateformat.format(datetime.strptime(tmp2.client.birthday.split(" ")[0], "%d.%m.%Y").date(),
                                      settings.DATE_FORMAT))}  # Добавление информации о пациенте в вывод
            response["ok"] = True
    return HttpResponse(json.dumps(response), content_type="application/json")  # Создание JSON


@csrf_exempt
@login_required
def setdef(request):
    response = {"ok": False}
    if "pk" in request.REQUEST.keys():
        status = False
        if "status" in request.REQUEST.keys():
            status = request.REQUEST["status"]
            if isinstance(status, str):
                status = status == "true"
        response["s"] = status
        pk = request.REQUEST["pk"]
        iss = Issledovaniya.objects.get(pk=int(pk))
        iss.deferred = status
        iss.save()
    return HttpResponse(json.dumps(response), content_type="application/json")  # Создание JSON

@csrf_exempt
@login_required
def cancel_direction(request):
    """Функция отмены направления"""

    response = {"ok": False}
    if "pk" in request.REQUEST.keys():
        cancel = False
        if "status" in request.REQUEST.keys():
            cancel = request.REQUEST["status"]
            if isinstance(cancel, str):
                cancel = cancel == "true"
        response["s"] = cancel
        pk = request.REQUEST["pk"]
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
                val.doc_get = request.user.doctorprofile  # Привязка профиля к пробирке
                val.time_get = timezone.now()  # Установка времени
                val.barcode = statuses["statuses"][k]  # Установка штрих-кода или номера пробирки
                val.save()  # Сохранение пробирки
                res["o"].append(val.id)
                slog.Log(key=str(val.pk), type=9, body="", user=request.user.doctorprofile).save()
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
            t.doc_get = request.user.doctorprofile
            t.time_get = timezone.now()
            t.save()

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
    date_start = datetime.now() - timedelta(days=1)
    date_end = datetime.now()
    if date_start.weekday() == 6: date_start -= timedelta(days=2)
    if date_start.weekday() == 5: date_start -= timedelta(days=1)
    naps = Napravleniya.objects.filter(Q(data_sozdaniya__range=(date_start, date_end), doc_who_create=request.user.doctorprofile, cancel=False)
                                                                | Q(data_sozdaniya__range=(date_start, date_end), doc=request.user.doctorprofile, cancel=False))
    for n in naps:
        for i in Issledovaniya.objects.filter(napravleniye=n):
            for t in i.tubes.filter(doc_get__isnull=True):
                tmprows[t.pk] = {"direction": n.pk, "patient": n.client.shortfio(), "title": t.type.tube.title, "pk": t.pk, "color": t.type.tube.color}
    for pk in tmprows.keys():
        res["rows"].append(tmprows[pk])
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

    # from pymongo import MongoClient
    '''client = MongoClient('mongodb://localhost:27017/')
    db = client['reports-db']
    collection = db['tubes']

    def get_next_id(collection_name):
        result = db.counters.find_and_modify(query={"_id": collection_name},
                                         update={"$inc": {"next": 1}},
                                         upsert=True, new=True)
        return result["next"]'''

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
        k = iss[0].napravleniye.doc.podrazileniye.title + "@" + str(iss[
                                                                        0].research.subgroup.title)  # Формирование ключа для группировки по подгруппе лаборатории и названию подразделения направившего на анализ врача
        for val in iss:  # Цикл перевода полученных исследований в список
            iss_list.append(val.research.title)
        if k not in labs.keys():  # Добавление списка в словарь если по ключу k нету ничего в словаре labs
            labs[k] = []
        for value in iss_list:  # Перебор списка исследований
            labs[k].append(
                {"type": v.type.tube.title, "researches": value,
                 "client-type": iss[0].napravleniye.client.type,
                 "lab_title": iss[0].research.subgroup.title,
                 "time": v.time_get.astimezone(local_tz).strftime("%H:%M:%S"), "dir_id": iss[0].napravleniye.pk,
                 "podr": iss[0].napravleniye.doc.podrazileniye.title,
                 "reciver": None,
                 "tube_id": str(v.id),
                 "history_num": iss[0].napravleniye.history_num,
                    "fio": iss[0].napravleniye.client.family + " " + iss[0].napravleniye.client.name[0] + "." + iss[0].napravleniye.client.twoname[0] + "."})  # Добавление в список исследований и пробирок по ключу k в словарь labs
    labs = collections.OrderedDict(sorted(labs.items()))  # Сортировка словаря
    c.setFont('OpenSans', 20)

    paddingx = 17
    data_header = ["№", "ФИО, № истории", "№ емкости", "Тип емкости", "Наименования исследований", "Емкость не принята (замечания)"]
    tw = w - paddingx * 4.5
    tx = paddingx * 3
    ty = 90
    c.setFont('OpenSans', 9)
    styleSheet["BodyText"].fontName = "OpenSans"
    styleSheet["BodyText"].fontSize = 7
    doc_num = 0

    # mongo_cache = {"date": str(dateformat.format(date.today(), settings.DATE_FORMAT)), "user": request.user.id, "docs": {}}
    # if collection.find_one({"date": mongo_cache["date"], "user": mongo_cache["user"]}):
    #    collection.remove({"date": mongo_cache["date"], "user": mongo_cache["user"]})
    for key in labs:
        doc_num += 1
        p = Paginator(labs[key], 47)
        i = 0
        if doc_num >= 2:
            c.showPage()
        # tubes_cache = {}
        # mongo_cache["docs"][str(doc_num)] = {"tubes": [], "lab": key, "id": get_next_id("reports-db")}
        for pg_num in p.page_range:
            pg = p.page(pg_num)
            if pg_num >= 0:
                # drawTituls(c, mongo_cache["docs"][str(doc_num)]["id"], user, p.num_pages, pg_num, paddingx, pg[0])
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
                # if obj["tube_id"] not in tubes_cache.keys():
                #    tubes_cache[str(obj["tube_id"])] = {"researches": [], "reciver": obj["reciver"]}
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
                # tubes_cache[obj["tube_id"]]["researches"].append(research_tmp)
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
            t = Table(data, colWidths=[int(tw * 0.03), int(tw * 0.23), int(tw * 0.08), int(tw * 0.23), int(tw * 0.31), int(tw * 0.14)],
                      style=style)

            t.canv = c
            wt, ht = t.wrap(0, 0)
            t.drawOn(c, tx, h - ht - ty)
            if pg.has_next():
                c.showPage()
                # mongo_cache["docs"][str(doc_num)]["tubes"] = tubes_cache
    # collection.insert_one(mongo_cache)
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

    c.drawCentredString(w / 2, h - 30, "Клиники ГБОУ ВПО ИГМУ Минздрава России")
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
    res = {"issledovaniya": [], "ok": False}
    if request.method == "GET":
        iss = []
        napr = None
        id = request.GET["id"]
        res["all_confirmed"] = True
        if id.isnumeric():
            if request.GET["type"] == "0":
                if TubesRegistration.objects.filter(pk=id).count() == 1:
                    tube = TubesRegistration.objects.get(pk=id)
                    if tube.doc_recive:
                        iss = Issledovaniya.objects.filter(tubes__id=id, research__subgroup__podrazdeleniye__pk=request.user.doctorprofile.podrazileniye.pk).order_by("deferred", "-doc_save",
                                                                                     "-doc_confirmation",
                                                                                  "research__sort_weight").all()
                        napr = iss.first().napravleniye
                elif TubesRegistration.objects.filter(pk=id).count() > 1:
                    tubes = TubesRegistration.objects.filter(pk=id)
                    for tube in tubes:
                        if tube.doc_recive:
                            lit = Issledovaniya.objects.filter(tubes__id=id, research__subgroup__podrazdeleniye__pk=request.user.doctorprofile.podrazileniye.pk).order_by("deferred", "-doc_save",
                                                                                     "-doc_confirmation",
                                                                                      "research__sort_weight").all()
                            if lit.count() != 0:
                                iss = []
                            for i in lit:
                                iss.append(i)
                    if len(iss) > 0:
                        napr = iss[0].napravleniye
            elif request.GET["type"] == "2":
                try:
                    napr = Napravleniya.objects.get(pk=id)
                    iss = Issledovaniya.objects.filter(napravleniye__pk=id, research__subgroup__podrazdeleniye__pk=request.user.doctorprofile.podrazileniye.pk).order_by("deferred", "-doc_save",
                                                                                     "-doc_confirmation",
                                                                                     "research__sort_weight").all()
                except Napravleniya.DoesNotExist:
                    napr = None
                    iss = []
            else:
                try:
                    napr = Napravleniya.objects.get(pk=id)
                    iss = Issledovaniya.objects.filter(napravleniye__pk=id, research__subgroup__podrazdeleniye__pk=request.user.doctorprofile.podrazileniye.pk).order_by("deferred", "-doc_save",
                                                                                     "-doc_confirmation",
                                                                                     "research__sort_weight").all()
                except Napravleniya.DoesNotExist:
                    napr = None
                    iss = []
            if len(iss) > 0:
                for issledovaniye in iss:
                    if True:  # issledovaniye.research.hide == 0:

                        tubes_list = issledovaniye.tubes.exclude(doc_recive__isnull=True).all()
                        tubes = []
                        titles = []
                        for tube_o in tubes_list:
                            tubes.append(tube_o.pk)
                            titles.append(tube_o.type.tube.title)
                        saved = True
                        confirmed = True
                        if not issledovaniye.doc_save:
                            saved = False
                        if not issledovaniye.doc_confirmation:
                            confirmed = False
                            if not issledovaniye.deferred:
                                res["all_confirmed"] = False
                        res["issledovaniya"].append({"pk": issledovaniye.pk, "title": issledovaniye.research.title,
                                                     "sort": issledovaniye.research.sort_weight,
                                                     "saved": saved, "confirmed": confirmed,
                                                     "tube": {"pk": ', '.join(str(v) for v in tubes),
                                                              "title": ' | '.join(titles)},
                                                     "template": str(issledovaniye.research.template),
                                                     "deff": issledovaniye.deferred})
            if napr:
                res["napr_pk"] = napr.pk
                res["client_fio"] = napr.client.family + " " + napr.client.name + " " + napr.client.twoname
                res["client_sex"] = napr.client.sex
                res["client_cardnum"] = napr.client.num
                res["client_hisnum"] = napr.history_num
                res["client_vozrast"] = napr.client.age_s()
                res["directioner"] = napr.doc.fio
                res["fin_source"] = napr.istochnik_f.tilie
                res["ok"] = True

    return HttpResponse(json.dumps(res), content_type="application/json")  # Создание JSON


from django.db.models import Q

@login_required
def get_client_directions(request):
    """ Получение направлений для пациента """
    import datetime
    res = {"directions": [], "ok": False}
    if request.method == "GET":
        pk = int(request.GET["pk"])
        req_status = int(request.GET["status"])
        date_start = request.GET["date[start]"]  # начальная дата назначения
        date_end = request.GET["date[end]"]  # конечная дата назначения

        date_start = datetime.date(int(date_start.split(".")[2]), int(date_start.split(".")[1]),
                                   int(date_start.split(".")[0]))
        date_end = datetime.date(int(date_end.split(".")[2]), int(date_end.split(".")[1]),
                                 int(date_end.split(".")[0])) + datetime.timedelta(1)
        if pk >= 0 or req_status == 4:
            if req_status == 4:
                for napr in Napravleniya.objects.filter(Q(data_sozdaniya__range=(date_start, date_end), doc_who_create=request.user.doctorprofile)
                                                                | Q(data_sozdaniya__range=(date_start, date_end), doc=request.user.doctorprofile)).order_by("-data_sozdaniya"):
                    status = 0
                    iss_list = Issledovaniya.objects.filter(napravleniye=napr)
                    if iss_list.exists():
                        res["directions"].append(
                            {"pk": napr.pk, "status": status, "researches": ' | '.join(v.research.title for v in iss_list),
                             "date": str(dateformat.format(napr.data_sozdaniya.date(), settings.DATE_FORMAT)),
                             "lab": iss_list[0].research.subgroup.podrazdeleniye.title, "cancel": napr.cancel})
            else:
                for napr in Napravleniya.objects.filter(data_sozdaniya__range=(date_start, date_end), client__pk=pk).order_by("-data_sozdaniya"):
                    status = 2  # 0 - выписано. 1 - Материал получен лабораторией. 2 - результат подтвержден
                    iss_list = Issledovaniya.objects.filter(napravleniye=napr)
                    if not iss_list.exists():
                        continue
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
                        status = min(iss_status, status)
                        tmpiss = v

                    if req_status == 3 or req_status == status:
                        res["directions"].append(
                            {"pk": napr.pk, "status": status, "researches": ' | '.join(v.research.title for v in iss_list),
                             "date": str(dateformat.format(napr.data_sozdaniya.date(), settings.DATE_FORMAT)),
                             "lab": iss_list[0].research.subgroup.podrazdeleniye.title, "cancel": napr.cancel})
            res["ok"] = True
    return HttpResponse(json.dumps(res), content_type="application/json")  # Создание JSON


