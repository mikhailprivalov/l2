from django.shortcuts import render
from django.http import HttpResponse
import simplejson as json
from directions.models import TubesRegistration, Issledovaniya, Result, Napravleniya
from django.contrib.auth.decorators import login_required
from laboratory.decorators import group_required
from django.views.decorators.csrf import csrf_exempt
import directory.models as directory
import users.models as users
from django.views.decorators.cache import cache_page
from django.conf import settings
from django.utils import dateformat
import slog.models as slog


@login_required
@group_required("Врач-лаборант", "Лаборант")
def enter(request):
    """ Представление для страницы ввода результатов """
    return render(request, 'dashboard/resultsenter.html')


@login_required
@group_required("Врач-лаборант", "Лаборант")
def result_conformation(request):
    """ Представление для страницы подтверждения и печати результатов """
    if "Зав. Лаб." in request.user.groups.values_list('name', flat=True):  # Если пользователь "Зав.Лаб."
        labs = users.Podrazdeleniya.objects.filter(isLab=True)  # Загрузка всех подразделений
    else:
        labs = []
        labs.append(request.user.doctorprofile.podrazileniye)  # Загрузка подразделения пользователя
    researches = directory.Researches.objects.filter(
        subgroup__podrazdeleniye=request.user.doctorprofile.podrazileniye)  # Загрузка списка анализов
    return render(request, 'dashboard/conformation.html', {"researches": researches, "labs": labs})


@login_required
def loadready(request):
    """ Представление, возвращающее JSON со списками пробирок и направлений, принятых в лабораторию """
    result = {"tubes": [], "directions": []}
    tubes = TubesRegistration.objects.filter(doc_recive__isnull=False, doc_get__isnull=False,
                                             issledovaniya__napravleniye__is_printed=False,
                                             issledovaniya__research__subgroup__podrazdeleniye=request.user.doctorprofile.podrazileniye)  # Загрузка пробирок,
    # лаборатория исследования которых равна лаборатории
    # текущего пользователя, принятых лабораторией и результаты для которых не напечатаны
    for tube in tubes:  # перебор результатов выборки
        iss_set = tube.issledovaniya_set.all()  # Получение списка исследований для пробирки
        if len(iss_set) == 0: continue  # пропуск пробирки, если исследований нет
        complete = False  # Завершен ли анализ
        direction = iss_set.first().napravleniye  # Выборка направления для пробирки
        dicttube = {"id": tube.pk, "direction": direction.pk}  # Временный словарь с информацией о пробирке
        if not complete and dicttube not in result[
            "tubes"]:  # Если исследования не завершены и информация о пробирке не присутствует в ответе
            result["tubes"].append(dicttube)  # Добавление временного словаря к ответу
        dictdir = {"id": direction.pk}  # Временный словарь с информацией о направлении
        if dictdir not in result["directions"]:  # Если информация о направлении не присутствует в ответе
            result["directions"].append(dictdir)  # Добавление временного словаря к ответу
    result["tubes"] = sorted(result["tubes"], key=lambda k: k['id'])  # Сортировка списка пробирок
    result["directions"] = sorted(result["directions"], key=lambda k: k['id'])  # Сортировка списка направлений
    return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
@login_required
def results_save(request):
    """ Сохранение результатов """
    result = {}
    if request.method == "POST":
        fractions = json.loads(request.POST["fractions"])  # Загрузка фракций из запроса
        issledovaniye = Issledovaniya.objects.get(
            pk=int(request.POST["issledovaniye"]))  # Загрузка исследования из запроса и выборка из базы данных
        if issledovaniye:  # Если исследование найдено
            for key in fractions.keys():  # Перебор фракций из запроса
                fraction_result = None
                if Result.objects.filter(issledovaniye=issledovaniye,
                                         fraction__pk=key).exists():  # Если результат для фракции существует
                    fraction_result = Result.objects.get(issledovaniye=issledovaniye,
                                                         fraction__pk=key)  # Выборка результата из базы
                else:
                    fraction_result = Result(issledovaniye=issledovaniye,
                                             fraction=directory.Fractions.objects.get(
                                                 pk=key))  # Создание нового результата
                fraction_result.value = fractions[key]  # Установка значения
                fraction_result.iteration = 1  # Установка итерации
                fraction_result.save()  # Сохранение
            issledovaniye.doc_save = request.user.doctorprofile  # Кто сохранил
            from datetime import datetime

            issledovaniye.time_save = datetime.now()  # Время сохранения
            issledovaniye.save()

            slog.Log(key=request.POST["issledovaniye"], type=13, body=request.POST["fractions"],
                     user=request.user.doctorprofile).save()
    return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
@login_required
def result_confirm(request):
    """ Подтверждение результатов """
    result = {"ok": False}
    if request.method == "POST":
        issledovaniye = Issledovaniya.objects.get(
            pk=int(request.POST["pk"]))  # Загрузка исследования из запроса и выборка из базы данных
        if issledovaniye.doc_save:  # Если исследование сохранено
            issledovaniye.doc_confirmation = request.user.doctorprofile  # Кто подтвердил
            from datetime import datetime

            issledovaniye.time_confirmation = datetime.now()  # Время подтверждения
            issledovaniye.save()
            slog.Log(key=request.POST["pk"], type=14, body="", user=request.user.doctorprofile).save()

    return HttpResponse(json.dumps(result), content_type="application/json")


@login_required
def get_full_result(request):
    """ Получение результатов для направления """
    result = {"ok": False}
    if request.method == "GET":
        pk = int(request.GET["pk"])  # ID направления
        napr = Napravleniya.objects.get(pk=pk)  # Выборка направления из базы
        iss_list = Issledovaniya.objects.filter(napravleniye=napr)  # Выборка списка исследований из базы по направлению
        if not iss_list.filter(
                doc_confirmation__isnull=True).exists():  # Если для направления все исследования подтверждены

            result["direction"] = {}  # Направление
            result["direction"]["pk"] = napr.pk  # ID
            result["direction"]["doc"] = iss_list[0].doc_confirmation.get_fio()  # ФИО подтвердившего
            result["direction"]["date"] = str(
                dateformat.format(napr.data_sozdaniya.date(), settings.DATE_FORMAT))  # Дата подтверждения

            result["client"] = {}  # Пациент
            result["client"]["sex"] = napr.client.sex  # Пол
            result["client"]["fio"] = napr.client.fio()  # ФИО
            result["client"]["age"] = napr.client.age_s()  # Возраст
            result["client"]["cardnum"] = napr.client.num  # Номер карты
            result["client"]["dr"] = str(dateformat.format(napr.client.bd(), settings.DATE_FORMAT))  # Дата рождения

            result["results"] = {}  # Результаты
            for issledovaniye in iss_list:  # Перебор списка исследований
                result["results"][issledovaniye.pk] = {"title": issledovaniye.research.title,
                                                       "fractions": {}}  # Словарь результата
                results = Result.objects.filter(issledovaniye=issledovaniye)  # Выборка результатов из базы
                for res in results:  # Перебор результатов
                    if res.fraction.pk not in result["results"][issledovaniye.pk]["fractions"].keys():
                        result["results"][issledovaniye.pk]["fractions"][res.fraction.pk] = {}

                    result["results"][issledovaniye.pk]["fractions"][res.fraction.pk]["result"] = res.value  # Значение
                    result["results"][issledovaniye.pk]["fractions"][res.fraction.pk][
                        "title"] = res.fraction.title  # Название фракции
                    result["results"][issledovaniye.pk]["fractions"][res.fraction.pk][
                        "units"] = res.fraction.units  # Еденицы измерения
                    ref_m = res.fraction.ref_m
                    ref_f = res.fraction.ref_f
                    if not isinstance(ref_m, str):
                        ref_m = json.dumps(ref_m)
                    if not isinstance(ref_f, str):
                        ref_f = json.dumps(ref_f)
                    result["results"][issledovaniye.pk]["fractions"][res.fraction.pk]["ref_m"] = ref_m  # Референсы М
                    result["results"][issledovaniye.pk]["fractions"][res.fraction.pk]["ref_f"] = ref_f  # Референсы Ж

    return HttpResponse(json.dumps(result), content_type="application/json")


@login_required
def get_odf_result(request):
    pass
    '''
    from django.shortcuts import redirect
    import os.path
    from relatorio.templates.opendocument import Template
    import hashlib
    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

    result = {}

    pk = int(request.REQUEST["pk"])
    napr = Napravleniya.objects.get(pk=pk)
    iss_list = Issledovaniya.objects.filter(napravleniye=napr)
    class ResultD(dict):
        pass

    if not iss_list.filter(doc_confirmation__isnull=True).exists():

        result["direction"] = {}
        result["direction"]["pk"] = napr.pk
        result["direction"]["doc"] = iss_list[0].doc_confirmation.get_fio()
        result["direction"]["date"] = str(dateformat.format(napr.data_sozdaniya.date(), settings.DATE_FORMAT))

        result["cl"] = {}
        result["cl"]["sex"] = napr.client.sex
        result["cl"]["fio"] = napr.client.fio()
        result["cl"]["ag"] = napr.client.age_s()
        result["cl"]["cn"] = napr.client.num
        result["cl"]["d"] = str(dateformat.format(napr.client.bd(), settings.DATE_FORMAT))

        result["results"] = {}
        for issledovaniye in iss_list:
            result["results"][issledovaniye.pk] = {"title": issledovaniye.research.title, "fractions": {}}
            results = Result.objects.filter(issledovaniye=issledovaniye)
            for res in results:
                if res.fraction.pk not in result["results"][issledovaniye.pk]["fractions"].keys():
                    result["results"][issledovaniye.pk]["fractions"][res.fraction.pk] = {}

                result["results"][issledovaniye.pk]["fractions"][res.fraction.pk]["result"] = res.value
                result["results"][issledovaniye.pk]["fractions"][res.fraction.pk]["title"] = res.fraction.title
                result["results"][issledovaniye.pk]["fractions"][res.fraction.pk]["units"] = res.fraction.units
                ref_m = res.fraction.ref_m
                ref_f = res.fraction.ref_f
                if not isinstance(ref_m, str):
                    ref_m = json.dumps(ref_m)
                if not isinstance(ref_f, str):
                    ref_f = json.dumps(ref_f)
                result["results"][issledovaniye.pk]["fractions"][res.fraction.pk]["ref_m"] = ref_m
                result["results"][issledovaniye.pk]["fractions"][res.fraction.pk]["ref_f"] = ref_f

    basic = Template(source=None, filepath=PROJECT_ROOT+'/../static/tpl1.odt')
    basic_generated = basic.generate(o=ResultD(r=result)).render()
    fn = hashlib.sha256((str(pk)+"_direction").encode('utf-8')).hexdigest()

    file = open(PROJECT_ROOT + r'/../static/tmp/result-'+fn+'.odt', 'wb')
    file.write(basic_generated.getvalue())
    return redirect('/../static/tmp/result-'+fn+'.odt')'''


from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape

w, h = landscape(A4)
# @cache_page(60 * 30)
@login_required
def result_print(request):
    """ Печать результатов """
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="results.pdf"'
    pk = json.loads(request.GET["pk"])

    from io import BytesIO
    from django.core.paginator import Paginator
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os.path

    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))  # Путь до текущего скрипта

    pdfmetrics.registerFont(
        TTFont('OpenSans', PROJECT_ROOT + '/../static/fonts/OpenSans.ttf'))
    pdfmetrics.registerFont(
        TTFont('OpenSansBold', PROJECT_ROOT + '/../static/fonts/OpenSans-Bold.ttf'))

    buffer = BytesIO()
    pages = Paginator(pk, 2)

    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    for pg_num in pages.page_range:
        c.setLineWidth(1)
        c.line(w / 2 - 0.5, 0, w / 2 - 0.5, h)
        pg = pages.page(pg_num)
        i = 0
        for obj in pg.object_list:
            i += 1
            draw_obj(c, obj, i, request.user.doctorprofile)
        if pg.has_next():
            c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    slog.Log(key=request.GET["pk"], type=15, body="", user=request.user.doctorprofile).save()

    return response


def draw_obj(c: canvas.Canvas, obj: int, i: int, doctorprofile):
    napr = Napravleniya.objects.get(pk=obj)
    s = 0
    if i % 2 == 0:
        s = w / 2
    paddingx = 15
    last_iss = napr.issledovaniya_set.filter(time_confirmation__isnull=False).order_by("-time_confirmation").first()

    c.setFont('OpenSans', 10)
    c.drawCentredString(w / 4 + s, h - 20, "Клиники ГБОУ ВПО ИГМУ Минздрава России")
    c.setFont('OpenSans', 8)
    c.drawCentredString(w / 4 + s, h - 30, "(г. Иркутск, б-р. Гагарина, 18. тел: 280-808, 280-809)")
    c.setFont('OpenSans', 14)
    c.drawCentredString(w / 4 + s, h - 50, "Результаты анализов")

    c.setFont('OpenSans', 20)
    c.drawString(paddingx + s, h - 55, "№ " + str(obj))

    c.setFont('OpenSans', 10)
    c.drawString(paddingx + s, h - 70, "Лечащий врач: " + napr.doc.get_fio())
    c.drawRightString(s + w / 2 - paddingx, h - 70,
                      "Дата: " + str(dateformat.format(last_iss.time_confirmation.date(), settings.DATE_FORMAT)))

    c.drawString(s + paddingx, h - 84, "ФИО пациента: " + napr.client.fio())
    c.drawString(s + paddingx, h - 97, "Номер карты: " + str(napr.client.num))
    c.drawCentredString(w / 4 + s, h - 97, "Пол: " + napr.client.sex)
    # c.drawRightString(s + w/2 - paddingx, h-97, "Дата рождения: " + str(dateformat.format(napr.client.bd(), settings.DATE_FORMAT)) + " (" + str(napr.client.age()) + " лет)")

    c.drawRightString(s + w / 2 - paddingx, h - 97, napr.client.age_s() + " " + "(д.р. " + str(
        dateformat.format(napr.client.bd(), settings.DATE_FORMAT)) + ")")
    c.drawString(s + paddingx, 20, "Врач (лаборант): " + last_iss.doc_confirmation.fio.split(" ")[0] + " " +
                 last_iss.doc_confirmation.fio.split(" ")[1][0] + "." + last_iss.doc_confirmation.fio.split(" ")[2][
                     0] + ".   ____________________   (подпись)")
    c.setFont('OpenSans', 8)

    iss_list = Issledovaniya.objects.filter(napravleniye=napr)
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    styleSheet = getSampleStyleSheet()

    tw = w / 2 - paddingx * 2
    pos = h - 95 - paddingx / 2

    data = []
    tmp = []
    tmp.append(Paragraph('<font face="OpenSans" size="8">Исследование</font>', styleSheet["BodyText"]))
    tmp.append(Paragraph('<font face="OpenSans" size="8">Значение</font>', styleSheet["BodyText"]))
    tmp.append(Paragraph('<font face="OpenSans" size="8">Ед. изм.</font>', styleSheet["BodyText"]))
    if napr.client.sex.lower() == "м":
        tmp.append(
            Paragraph('<font face="OpenSans" size="8">Референсы (М)<br/>Условие:значение</font>', styleSheet["BodyText"]))
    else:
        tmp.append(
            Paragraph('<font face="OpenSans" size="8">Референсы (Ж)<br/>Условие:значение</font>', styleSheet["BodyText"]))
    data.append(tmp)
    cw = [int(tw * 0.485), int(tw * 0.164), int(tw * 0.12), int(tw * 0.232)]
    t = Table(data, colWidths=cw)
    t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                           ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                           ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                           ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                           ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                           ('LEFTPADDING', (0, 0), (-1, -1), 4),
                           ('TOPPADDING', (0, 0), (-1, -1), 0),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                           ]))
    t.canv = c
    wt, ht = t.wrap(0, 0)
    t.drawOn(c, paddingx + s, pos - ht)
    pos = pos - ht

    for iss in iss_list:
        data = []
        fractions = directory.Fractions.objects.filter(research=iss.research).order_by("pk")
        if fractions.count() == 1:
            tmp = []
            tmp.append(Paragraph('<font face="OpenSansBold" size="8">' + iss.research.title + "</font>",
                                 styleSheet["BodyText"]))
            result = ""
            if Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).exists():
                result = Result.objects.get(issledovaniye=iss, fraction=fractions[0]).value
            tmp.append(Paragraph('<font face="OpenSans" size="8">' + result + "</font>", styleSheet["BodyText"]))
            tmp.append(
                Paragraph('<font face="OpenSans" size="8">' + fractions[0].units + "</font>", styleSheet["BodyText"]))
            if napr.client.sex.lower() == "м":
                tmp.append(Paragraph('<font face="OpenSans" size="8">' + get_r(fractions[0].ref_m) + "</font>",
                                     styleSheet["BodyText"]))
            else:
                tmp.append(Paragraph('<font face="OpenSans" size="8">' + get_r(fractions[0].ref_f) + "</font>",
                                     styleSheet["BodyText"]))
            data.append(tmp)
            t = Table(data, colWidths=cw)
            t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                   ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                   ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                   ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                   ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                   ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                   ('TOPPADDING', (0, 0), (-1, -1), 0),
                                   ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                   ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                                   ]))
        else:
            tmp = [Paragraph('<font face="OpenSansBold" size="8">' + iss.research.title + "</font>",
                             styleSheet["BodyText"]), '', '', '']
            data.append(tmp)
            style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                # ('SPAN',(0,0),(-1,0)),
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                ('INNERGRID', (0, 0), (-1, -1), 0.2, colors.black),
                                ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                ('TOPPADDING', (0, 0), (-1, -1), 0),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                                ])
            j = 0

            for f in fractions:
                j += 1
                tmp = []
                tmp.append(Paragraph('&nbsp;&nbsp;&nbsp;&nbsp;<font face="OpenSans" size="8">' + f.title + "</font>",
                                     styleSheet["BodyText"]))
                result = ""
                if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
                    result = Result.objects.get(issledovaniye=iss, fraction=f).value

                tmp.append(Paragraph('<font face="OpenSans" size="8">' + result + "</font>", styleSheet["BodyText"]))
                tmp.append(Paragraph('<font face="OpenSans" size="8">' + f.units + "</font>", styleSheet["BodyText"]))
                if napr.client.sex.lower() == "м":
                    tmp.append(Paragraph('<font face="OpenSans" size="8">' + get_r(f.ref_m) + "</font>",
                                         styleSheet["BodyText"]))
                else:
                    tmp.append(Paragraph('<font face="OpenSans" size="8">' + get_r(f.ref_f) + "</font>",
                                         styleSheet["BodyText"]))

                data.append(tmp)

            for k in range(0, 4):
                style.add('INNERGRID', (k, 0),
                          (k, j), 0.01, colors.black)
                style.add('BOX', (k, 0), (k, j),
                          0.8, colors.black)

            t = Table(data, colWidths=cw)
            t.setStyle(style)
        t.canv = c
        wt, ht = t.wrap(0, 0)
        t.drawOn(c, paddingx + s, pos - ht)
        pos = pos - ht
    napr.is_printed = True
    from datetime import datetime

    napr.time_print = datetime.now()
    napr.doc_print = doctorprofile
    napr.save()


def get_r(ref) -> str:
    if isinstance(ref, str):
        r = json.loads(ref)
    else:
        r = ref
    tmp = []
    s = ""
    for k in r.keys():
        if len(r[k]) > 0:
            if k == "Все" and len(r) == 1:
                tmp.append(r[k])
            else:
                tmp.append(k + " : " + r[k])
    tmp.sort()
    s = "<br/>".join(tmp)
    if s == " : ":
        s = ""
    return s


@csrf_exempt
@login_required
def result_get(request):
    """ Получение результатов для исследования """
    result = {"results": {}}
    if request.method == "GET":
        issledovaniye = Issledovaniya.objects.get(pk=int(request.GET["iss_id"]))
        results = Result.objects.filter(issledovaniye=issledovaniye)
        for v in results:
            result["results"][str(v.fraction.pk)] = v.value
    return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
@login_required
def result_filter(request):
    """ Фильтрация списка исследований """
    import datetime

    result = {"ok": False}
    if request.method == "POST":
        research_pk = request.POST["research"]  # ID исследования
        status = int(request.POST["status"])  # Статус
        dir_pk = request.POST["dir_id"]  # Номер направления
        date_start = request.POST["date[start]"]  # Начальная дата
        date_end = request.POST["date[end]"]  # Конечная дата
        if research_pk.isnumeric() or research_pk == "-1":
            iss_list = []

            iss_list = Issledovaniya.objects.filter(
                research__subgroup__podrazdeleniye=request.user.doctorprofile.podrazileniye)
            if dir_pk == "" and status != 3:
                date_start = datetime.date(int(date_start.split(".")[2]), int(date_start.split(".")[1]),
                                           int(date_start.split(".")[0]))
                date_end = datetime.date(int(date_end.split(".")[2]), int(date_end.split(".")[1]),
                                         int(date_end.split(".")[0])) + datetime.timedelta(1)
                if status == 0:
                    iss_list = iss_list.filter(tubes__time_recive__range=(date_start, date_end))
                elif status == 1:
                    iss_list = iss_list.filter(time_save__range=(date_start, date_end), time_save__isnull=False)
                elif status == 2:
                    iss_list = iss_list.filter(napravleniye__time_print__range=(date_start, date_end))
                if int(research_pk) >= 0:
                    iss_list = iss_list.filter(research__pk=int(research_pk))
            elif dir_pk == "" and status == 3:
                iss_list = iss_list.filter(napravleniye__doc_print__isnull=True, doc_confirmation__isnull=False)
                is_tmp = iss_list
                for v in is_tmp:
                    if Issledovaniya.objects.filter(napravleniye=v.napravleniye,
                                                    doc_confirmation__isnull=True).exists():
                        iss_list = iss_list.exclude(napravleniye=v.napravleniye)
            elif dir_pk.isnumeric():
                iss_list = iss_list.filter(napravleniye__pk=int(dir_pk))

            result["list"] = {}
            for v in iss_list:
                status_v = 0
                if v.doc_save and not v.doc_confirmation:
                    status_v = 1
                elif v.doc_save and v.doc_confirmation and v.napravleniye.doc_print:
                    status_v = 2
                elif v.doc_save and v.doc_confirmation and not v.napravleniye.doc_print:
                    status_v = 3
                if v.pk in result["list"].keys() or (status != status_v and not dir_pk.isnumeric()):
                    continue
                if dir_pk.isnumeric():
                    status = status_v
                res = {"status": status_v, "pk": v.pk, "title": v.research.title, "date": "",
                       "direction": v.napravleniye.pk,
                       "tubes": " | ".join(map(str, v.tubes.values_list('pk', flat=True)))}
                if status == 0 and v.tubes.filter(time_recive__isnull=False).exists():  # Не обработаные
                    res["date"] = str(dateformat.format(
                        v.tubes.filter(time_recive__isnull=False).order_by("-time_recive").first().time_recive.date(),
                        settings.DATE_FORMAT))
                elif status == 1:  # Не подтвержденые
                    res["date"] = str(dateformat.format(v.time_save.date(), settings.DATE_FORMAT))
                elif status == 2:  # Распечатаные
                    if v.napravleniye.time_print:
                        res["date"] = str(dateformat.format(v.napravleniye.time_print.date(), settings.DATE_FORMAT))
                elif status == 3:  # Не распечатаные
                    res["date"] = str(dateformat.format(v.time_confirmation.date(), settings.DATE_FORMAT))
                result["list"][v.pk] = res
            result["ok"] = True
    return HttpResponse(json.dumps(result), content_type="application/json")
