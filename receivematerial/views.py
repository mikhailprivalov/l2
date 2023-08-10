# coding=utf8
from datetime import datetime, date

import simplejson as json
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import dateformat
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from reportlab.lib.pagesizes import A4

import directory.models as directory
import slog.models as slog
import users.models as users
from appconf.manager import SettingManager
from directions.models import Issledovaniya, TubesRegistration, Result
from laboratory import settings
from laboratory.decorators import group_required
from laboratory.settings import FONTS_FOLDER
from laboratory.utils import strtime
from podrazdeleniya.models import Podrazdeleniya
from utils.dates import try_parse_range

w, h = A4


@csrf_exempt
@login_required
@group_required("Получатель биоматериала")
@ensure_csrf_cookie
def receive(request):
    """Представление для приемщика материала в лаборатории"""

    if request.method == "GET":
        podrazdeleniya = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.DEPARTMENT).filter(Q(hospital=request.user.doctorprofile.hospital) | Q(hospital__isnull=True)).order_by("title")
        labs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY).exclude(title="Внешние организации").order_by("title")
        return render(request, 'dashboard/receive.html', {"labs": labs, "podrazdeleniya": podrazdeleniya})
    else:
        tubes = json.loads(request.POST["data"])
        for tube_get in tubes:
            tube = TubesRegistration.objects.get(number=tube_get["id"])
            if tube_get["status"] and (tube_get["notice"] == "" or (tube.notice not in [None, ""] and tube_get["notice"] == tube.notice)):
                cleared = tube.notice not in [None, ""]
                if cleared:
                    tube.clear_notice(request.user.doctorprofile)
                if tube_get["notice"] == "" or cleared:
                    tube.set_r(request.user.doctorprofile)
                elif not tube.issledovaniya_set.exists() or not tube.issledovaniya_set.all()[0].napravleniye.is_all_confirm():
                    tube.doc_recive = None
                    tube.time_recive = None
                    tube.save()
                    tube.set_notice(request.user.doctorprofile, tube_get["notice"])
            elif tube_get["notice"] != "":
                tube.set_notice(request.user.doctorprofile, tube_get["notice"])

        result = {"r": True}
        return JsonResponse(result)


@csrf_exempt
@login_required
@group_required("Получатель биоматериала", "Лаборант", "Врач-лаборант")
def receive_execlist(request):
    import datetime
    import directory.models as directory
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import landscape
    from reportlab.pdfbase import pdfdoc
    from django.core.paginator import Paginator
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.units import mm
    import os.path
    from io import BytesIO
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph

    pdfmetrics.registerFont(TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSansB', os.path.join(FONTS_FOLDER, 'OpenSans-Bold.ttf')))

    w, h = landscape(A4)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="execlist.pdf"'
    pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:true,bSilent:false,bShrinkToFit:true}\);)>>'
    t = request.GET.get("type", "received")
    researches = json.loads(request.GET["researches"])
    buffer = BytesIO()

    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    marginx = 15 * mm
    marginy = 10 * mm

    pw = w - marginx * 2

    from datetime import timedelta

    if t == "received":
        date = request.GET["date"].split(".")
        date = datetime.date(int(date[2]), int(date[1]), int(date[0]))
        date1 = date
        date2 = date1 + timedelta(days=1)
        dates = request.GET["date"]
    else:
        date1 = request.GET["datestart"].split(".")
        date1 = datetime.date(int(date1[2]), int(date1[1]), int(date1[0]))
        date2 = request.GET["dateend"].split(".")
        date2 = datetime.date(int(date2[2]), int(date2[1]), int(date2[0])) + timedelta(days=1)
        if request.GET["datestart"] != request.GET["dateend"]:
            dates = "{} - {}".format(request.GET["datestart"], request.GET["dateend"])
        else:
            dates = request.GET["datestart"]

    def py(y=0):
        y *= mm
        return h - y - marginy

    def px(x=0):
        x *= mm
        return x + marginx

    def pxr(x=0):
        x *= mm
        return pw - x + marginx

    for pk in researches:
        if directory.Researches.objects.filter(pk=pk).exists() and (
            Issledovaniya.objects.filter(research__pk=pk, tubes__time_recive__range=(date1, date2), time_confirmation__isnull=True)
            .filter(Q(napravleniye__hospital=request.user.doctorprofile.hospital) | Q(napravleniye__hospital__isnull=True))
            .exists()
        ):
            research = directory.Researches.objects.get(pk=pk)
            fractions_o = directory.Fractions.objects.filter(research=research, hide=False).order_by("sort_weight")
            fractions = [x.title for x in fractions_o]
            if t == "received":
                tubes = [
                    x.number
                    for x in TubesRegistration.objects.filter(time_recive__range=(date1, date2), doc_recive=request.user.doctorprofile, issledovaniya__research=research)
                    .order_by("daynum")
                    .distinct()
                ]
            else:
                tubes = [
                    x.number
                    for x in (
                        TubesRegistration.objects.filter(time_recive__range=(date1, date2), issledovaniya__time_confirmation__isnull=True, issledovaniya__research=research)
                        .filter(Q(issledovaniya__napravleniye__hospital=request.user.doctorprofile.hospital) | Q(issledovaniya__napravleniye__hospital__isnull=True))
                        .order_by("issledovaniya__napravleniye__client__individual__family", "issledovaniya__napravleniye__client__individual__name")
                        .distinct()
                    )
                ]
            pages = Paginator(tubes, 16)
            nn = 0
            for pg_num in pages.page_range:
                c.setFont('OpenSans', 12)
                c.drawString(px(), py(), "Лист исполнения - %s за %s" % (research.title, dates))
                c.drawRightString(pxr(), py(), research.get_podrazdeleniye().title)
                c.drawString(px(), 6 * mm, "Страница %d из %d" % (pg_num, pages.num_pages))

                styleSheet = getSampleStyleSheet()

                tw = pw

                data = []
                tmp = [
                    Paragraph('<font face="OpenSansB" size="8">№</font>', styleSheet["BodyText"]),
                    Paragraph('<font face="OpenSansB" size="8">ФИО, № истории<br/>отделение</font>', styleSheet["BodyText"]),
                    Paragraph('<font face="OpenSansB" size="8">№ напр.</font>', styleSheet["BodyText"]),
                    Paragraph('<font face="OpenSansB" size="8">№ мат.</font>', styleSheet["BodyText"]),
                ]
                for fraction in fractions:
                    fraction = fraction[: int(100 / len(fractions))]
                    tmp.append(Paragraph('<font face="OpenSansB" size="6">%s</font>' % fraction, styleSheet["BodyText"]))
                data.append(tmp)

                pg = pages.page(pg_num)
                for tube_pk in pg.object_list:
                    nn += 1
                    tube = TubesRegistration.objects.get(number=tube_pk)
                    napravleniye = Issledovaniya.objects.filter(tubes__number=tube_pk)[0].napravleniye
                    tmp = [
                        Paragraph('<font face="OpenSans" size="8">%d</font>' % (tube.daynum if t == "received" else nn), styleSheet["BodyText"]),
                        Paragraph(
                            '<font face="OpenSans" size="8">%s</font>'
                            % (
                                napravleniye.client.individual.fio()
                                + ("" if not napravleniye.history_num or napravleniye.history_num == "" else ", " + napravleniye.history_num)
                                + "<br/>"
                                + napravleniye.doc.podrazdeleniye.title
                            ),
                            styleSheet["BodyText"],
                        ),
                        Paragraph('<font face="OpenSans" size="8">%d</font>' % napravleniye.pk, styleSheet["BodyText"]),
                        Paragraph('<font face="OpenSans" size="8">%d</font>' % tube_pk, styleSheet["BodyText"]),
                    ]
                    for f in fractions_o:
                        res = Result.objects.filter(fraction=f, issledovaniye__napravleniye=napravleniye)
                        tmp.append(Paragraph('<font face="OpenSans" size="8">{}</font>'.format("" if t == "received" or not res.exists() else res[0].value), styleSheet["BodyText"]))
                    data.append(tmp)

                cw = [int(tw * 0.07), int(tw * 0.245), int(tw * 0.055), int(tw * 0.045)]
                lw = tw * 0.615
                for _ in range(0, len(fractions) + 1):
                    cw.append(lw / len(fractions))
                t = Table(data, colWidths=cw)
                t.setStyle(
                    TableStyle(
                        [
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                            ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                            ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                            ('LEFTPADDING', (0, 0), (-1, -1), 2),
                            ('TOPPADDING', (0, 0), (-1, -1), 9),
                            ('TOPPADDING', (1, 0), (1, -1), 3),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
                            ('BOTTOMPADDING', (1, 0), (1, -1), 3),
                        ]
                    )
                )
                t.canv = c
                wt, ht = t.wrap(0, 0)
                t.drawOn(c, px(), py(5) - ht)

                c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


@login_required
def tubes_get(request):
    """Получение списка не принятых пробирок"""
    result = []
    k = set()
    if (
        request.method == "GET"
        and "lab" in request.GET
        and request.GET["lab"].isdigit()
        and "from" in request.GET
        and request.GET["from"].isdigit()
        and "datestart" in request.GET
        and "dateend" in request.GET
    ):
        filter_type = request.GET.get("type", "wait")
        lab = Podrazdeleniya.objects.get(pk=request.GET["lab"])
        podrazledeniye = Podrazdeleniya.objects.get(pk=request.GET["from"])
        date_start = request.GET["datestart"]
        date_end = request.GET["dateend"]
        date_start, date_end = try_parse_range(date_start, date_end)
        from mainmenu.views import get_tubes_list_in_receive_ui

        tubes_list = get_tubes_list_in_receive_ui(date_end, date_start, filter_type, lab, podrazledeniye, request.user.doctorprofile)

        for tube in tubes_list:
            if tube.getbc() in k or (tube.rstatus() and filter_type != "received"):
                continue
            issledovaniya_tmp = []
            for iss in Issledovaniya.objects.filter(tubes__number=tube.number, research__podrazdeleniye=lab, tubes__time_get__range=(date_start, date_end)):
                issledovaniya_tmp.append(iss.research.title)
            if len(issledovaniya_tmp) > 0:
                k.add(tube.getbc())
                result.append(
                    {
                        "researches": ' | '.join(issledovaniya_tmp),
                        "direction": tube.issledovaniya_set.first().napravleniye_id,
                        "tube": {"type": tube.type.tube.title, "id": tube.getbc(), "status": tube.rstatus(), "color": tube.type.tube.color, "notice": tube.notice},
                    }
                )

    return JsonResponse(list(result), safe=False)


@login_required
def receive_journal(request):
    """Печать истории принятия материала за день"""
    lab = Podrazdeleniya.objects.get(pk=request.GET.get("lab_pk", request.user.doctorprofile.podrazdeleniye_id))
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    styleSheet = getSampleStyleSheet()
    import os.path
    import collections
    import copy

    start = str(request.GET.get("start", "1"))
    group = str(request.GET.get("group", "-2"))
    return_type = str(request.GET.get("return", "pdf"))
    otd = str(request.GET.get("otd", "[]"))

    start = 1 if not start.isdigit() else int(start)
    group = -2 if group not in ["-2", "-1"] and (not group.isdigit() or not directory.ResearchGroup.objects.filter(pk=int(group)).exists()) else int(group)
    otd = [int(x) for x in json.loads(otd)]

    pdfmetrics.registerFont(TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))  # Загрузка шрифта

    response = HttpResponse(content_type='application/pdf')  # Формирование ответа
    response['Content-Disposition'] = 'inline; filename="zhurnal_priema_materiala.pdf"'  # Content-Disposition inline для показа PDF в браузере
    from io import BytesIO

    buffer = BytesIO()  # Буфер
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(buffer, pagesize=A4)  # Холст

    if return_type == "directions":
        tubes = (
            TubesRegistration.objects.filter(
                issledovaniya__research__podrazdeleniye=lab, time_recive__gte=datetime.now().date(), doc_get__podrazdeleniye__pk__in=otd, doc_recive__isnull=False
            )
            .filter(Q(issledovaniya__napravleniye__hospital=request.user.doctorprofile.hospital) | Q(issledovaniya__napravleniye__hospital__isnull=True))
            .order_by('time_recive', 'daynum')
        )
    else:
        tubes = (
            TubesRegistration.objects.filter(
                issledovaniya__research__podrazdeleniye=lab, time_recive__gte=datetime.now().date(), doc_get__podrazdeleniye__pk__in=otd, doc_recive__isnull=False
            )
            .filter(Q(issledovaniya__napravleniye__hospital=request.user.doctorprofile.hospital) | Q(issledovaniya__napravleniye__hospital__isnull=True))
            .order_by('issledovaniya__napravleniye__client__pk')
        )

    labs = {}  # Словарь с пробирками, сгруппироваными по лаборатории
    directions = []
    vids = set()

    perpage = 47

    n_dict = {}

    n = 1
    for v in tubes:
        idv = v.number
        if idv in vids:
            continue
        vids.add(idv)
        iss = Issledovaniya.objects.filter(tubes__number=v.number)  # Получение исследований для пробирки

        if group == -1:
            iss = iss.filter(research__groups__isnull=True)
        elif group >= 0:
            iss = iss.filter(research__groups__pk=group)

        iss_list = collections.OrderedDict()  # Список исследований
        if v.doc_get:
            k = str(v.doc_get.podrazdeleniye_id) + "@" + str(v.doc_get.podrazdeleniye)
        else:
            k = str(iss.first().napravleniye.doc.podrazdeleniye_id) + "@" + str(iss.first().napravleniye.doc.podrazdeleniye)
        if k not in n_dict.keys():
            n_dict[k] = 0
        for val in iss.order_by("research__sort_weight"):  # Цикл перевода полученных исследований в список
            iss_list[val.research.sort_weight] = val.research.title

        if len(iss_list) == 0:
            continue
        '''
        if n < start:
            n += 1
            continue'''
        if return_type == "pdf":
            n_dict[k] += 1
            if n_dict[k] >= start:
                if k not in labs.keys():  # Добавление списка в словарь если по ключу k нет ничего в словаре labs
                    labs[k] = []

                if perpage - len(labs[k]) % perpage < len(iss_list):
                    pre = copy.deepcopy(labs[k][len(labs[k]) - 1])
                    pre["researches"] = ""
                    for x in range(0, perpage - len(labs[k]) % perpage):
                        labs[k].append(pre)
                for value in iss_list:  # Перебор списка исследований
                    labs[k].append(
                        {
                            "type": v.type.tube.title,
                            "researches": iss_list[value],
                            "client-type": iss[0].napravleniye.client.base.short_title,
                            "lab_title": iss[0].research.get_podrazdeleniye().title,
                            "time": strtime(v.time_recive),
                            "dir_id": iss[0].napravleniye_id,
                            "podr": iss[0].napravleniye.doc.podrazdeleniye.title,
                            "receive_n": str(n),
                            "tube_id": str(v.number),
                            "direction": str(iss[0].napravleniye_id),
                            "history_num": iss[0].napravleniye.history_num,
                            "n": n_dict[k],
                            "fio": iss[0].napravleniye.client.individual.fio(short=True, dots=True),
                        }
                    )  # Добавление в список исследований и пробирок по ключу k в словарь labs
        elif iss[0].napravleniye_id not in directions:
            directions += [iss[0].napravleniye_id]
        n += 1
    if return_type == "directions":
        return JsonResponse(directions, safe=False)

    labs = collections.OrderedDict(sorted(labs.items()))  # Сортировка словаря
    c.setFont('OpenSans', 20)

    paddingx = 17
    data_header = ["№", "ФИО, № истории", "№ Напр", "№ емкости", "Тип емкости", "Наименования исследований"]
    tw = w - paddingx * 3.5
    tx = paddingx * 2
    ty = 90
    c.setFont('OpenSans', 9)
    styleSheet["BodyText"].fontName = "OpenSans"
    styleSheet["BodyText"].fontSize = 7
    doc_num = 0

    for key in labs:
        doc_num += 1
        p = Paginator(labs[key], perpage)
        i = 0
        if doc_num >= 2:
            c.showPage()

        nn = 0
        gid = "-1"
        for pg_num in p.page_range:
            pg = p.page(pg_num)
            if len(pg) == 0:
                continue
            if pg_num >= 0:
                draw_tituls(c, p.num_pages, pg_num, paddingx, lab=lab.title, group=group, otd=key.split("@")[1], hospital_title=request.user.doctorprofile.hospital_safe_title)
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
                    if gid != obj["tube_id"]:
                        i += 1
                    lastid = gid = obj["tube_id"]
                    shownum = True
                else:
                    shownum = False
                    if lastid not in merge_list.keys():
                        merge_list[lastid] = []
                    merge_list[lastid].append(num)
                if shownum:
                    nn += 1
                    tmp.append(Paragraph(str(obj["n"]), styleSheet["BodyText"]))  # "--" if obj["receive_n"] == "0" else obj["receive_n"], styleSheet["BodyText"]))
                    fio = obj["fio"]
                    if obj["history_num"] and len(obj["history_num"]) > 0:
                        fio += ", " + obj["history_num"]
                    tmp.append(Paragraph(fio, styleSheet["BodyText"]))
                    tmp.append(Paragraph(obj["direction"], styleSheet["BodyText"]))
                    tmp.append(Paragraph(obj["tube_id"], styleSheet["BodyText"]))
                    tmp.append(Paragraph(obj["type"], styleSheet["BodyText"]))
                else:
                    tmp.append("")
                    tmp.append("")
                    tmp.append("")
                    tmp.append("")
                    tmp.append("")
                research_tmp = obj["researches"]
                if len(research_tmp) > 44:
                    research_tmp = research_tmp[0 : -(len(research_tmp) - 44)] + "..."
                tmp.append(Paragraph(research_tmp, styleSheet["BodyText"]))

                data.append(tmp)
                num += 1

            style = TableStyle(
                [
                    ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                    ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
                    ('LEFTPADDING', (0, 0), (-1, -1), 1),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                    ('TOPPADDING', (0, 0), (-1, -1), 1),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                ]
            )
            for span in merge_list:  # Цикл объединения ячеек
                for pos in range(0, 6):
                    style.add('INNERGRID', (pos, merge_list[span][0]), (pos, merge_list[span][0] + len(merge_list[span])), 0.28, colors.white)
                    style.add('BOX', (pos, merge_list[span][0]), (pos, merge_list[span][0] + len(merge_list[span])), 0.2, colors.black)
            t = Table(data, colWidths=[int(tw * 0.03), int(tw * 0.23), int(tw * 0.09), int(tw * 0.09), int(tw * 0.23), int(tw * 0.35)], style=style)

            t.canv = c
            wt, ht = t.wrap(0, 0)
            t.drawOn(c, tx, h - ht - ty)
            if pg.has_next():
                c.showPage()
    c.setTitle("Журнал приёма материала - " + lab.title)
    c.save()

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    if group >= 0:
        group_str = directory.ResearchGroup.objects.get(pk=group).title
    elif group == -2:
        group_str = "Все исследования"
    else:
        group_str = "Без группы"

    slog.Log(
        key="",
        type=25,
        body=json.dumps({"group": group_str, "start": start, "otds": ["%s, %s" % (users.Podrazdeleniya.objects.get(pk=int(x)).title, x) for x in otd]}),
        user=request.user.doctorprofile,
    ).save()
    return response


def draw_tituls(c, pages, page, paddingx, lab, otd="", group=-2, hospital_title=None):
    """Функция рисования шапки и подвала страницы pdf"""
    c.setFont('OpenSans', 9)
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)

    c.drawCentredString(w / 2, h - 30, hospital_title or SettingManager.get("org_title"))
    c.setFont('OpenSans', 12)
    c.drawCentredString(w / 2, h - 50, "Журнал приёма материала - " + lab)

    if group >= 0:
        group_str = directory.ResearchGroup.objects.get(pk=group).title
    elif group == -2:
        group_str = "Все исследования"
    else:
        group_str = "Без группы"

    c.drawString(paddingx, h - 65, "Группа: %s" % group_str)

    c.drawString(paddingx, h - 78, "Отделение: %s" % otd)

    c.setFont('OpenSans', 10)
    # c.drawString(paddingx * 3, h - 70, "№ " + str(doc_num))
    c.drawRightString(w - paddingx, h - 65, "Дата: " + str(dateformat.format(date.today(), settings.DATE_FORMAT)))

    c.drawRightString(w - paddingx, 20, "Страница " + str(page) + " из " + str(pages))
