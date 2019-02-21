import collections
from copy import deepcopy
import datetime
import bleach
import simplejson as json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import dateformat
from django.views.decorators.csrf import csrf_exempt
from reportlab.pdfbase import pdfdoc
from reportlab.platypus import PageBreak, Spacer, KeepInFrame, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet

import directory.models as directory
import slog.models as slog
import users.models as users
from appconf.manager import SettingManager
from clients.models import CardBase
from directions.models import TubesRegistration, Issledovaniya, Result, Napravleniya, IstochnikiFinansirovaniya, \
    ParaclinicResult
from laboratory.decorators import group_required, logged_in_or_token
from laboratory.settings import FONTS_FOLDER
from laboratory.utils import strdate
from podrazdeleniya.models import Podrazdeleniya
from utils.dates import try_parse_range


@login_required
@group_required("Лечащий врач", "Зав. отделением")
@csrf_exempt
def results_search(request):
    """ Представление для поиска результатов исследований у пациента """
    if request.method == "POST":
        dirs = set()
        result = {"directions": [], "client_id": int(request.POST["client_id"]),
                  "research_id": int(request.POST["research_id"]), "other_dirs": []}
        for r in Result.objects.filter(fraction__research_id=result["research_id"],
                                       issledovaniye__napravleniye__client_id=result["client_id"],
                                       issledovaniye__doc_confirmation__isnull=False):
            dirs.add(r.issledovaniye.napravleniye.pk)
        for d in Napravleniya.objects.filter(client_id=result["client_id"],
                                             issledovaniya__research_id=result["research_id"]):
            tmp_d = {"pk": d.pk}
            if d.pk in dirs:
                tc = Issledovaniya.objects.filter(napravleniye=d).first().time_confirmation
                tmp_d["date"] = "не подтверждено" if tc is None else strdate(tc)
                result["directions"].append(tmp_d)
            else:
                tmp_d["get_material"] = all([x.is_get_material() for x in Issledovaniya.objects.filter(napravleniye=d)])
                tmp_d["is_receive_material"] = all(
                    [x.is_receive_material() for x in Issledovaniya.objects.filter(napravleniye=d)])
                tmp_d["is_has_deff"] = d.is_has_deff()
                tmp_d["type"] = 0
                if tmp_d["get_material"]:
                    tmp_d["type"] = 1
                if tmp_d["is_receive_material"]:
                    tmp_d["type"] = 2
                if tmp_d["is_has_deff"]:
                    tmp_d["type"] = 3
                tmp_d["date"] = strdate(d.data_sozdaniya)
                result["other_dirs"].append(tmp_d)
        return HttpResponse(json.dumps(result), content_type="application/json")

    from podrazdeleniya.models import Podrazdeleniya
    labs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY).exclude(title="Внешние организации")
    return render(request, 'dashboard/results_search.html', {"labs": labs})


@login_required
@group_required("Врач-лаборант", "Лаборант")
def enter(request):
    """ Представление для страницы ввода результатов """
    from podrazdeleniya.models import Podrazdeleniya
    lab = Podrazdeleniya.objects.get(pk=request.GET.get("lab_pk", request.user.doctorprofile.podrazdeleniye.pk))
    labs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY).exclude(title="Внешние организации").order_by("title")
    if lab.p_type != Podrazdeleniya.LABORATORY:
        lab = labs[0]
    podrazdeleniya = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.DEPARTMENT).order_by("title")
    return render(request, 'dashboard/resultsenter.html', {"podrazdeleniya": podrazdeleniya,
                                                           "ist_f": IstochnikiFinansirovaniya.objects.all().order_by(
                                                               "pk").order_by("base"),
                                                           "groups": directory.ResearchGroup.objects.filter(lab=lab),
                                                           "lab": lab,
                                                           "labs": labs})


# from django.db import connection

@csrf_exempt
@login_required
def loadready(request):
    """ Представление, возвращающее JSON со списками пробирок и направлений, принятых в лабораторию """
    result = {"tubes": [], "directions": []}
    if request.method == "POST":
        date_start = request.POST["datestart"]
        date_end = request.POST["dateend"]
        deff = int(request.POST["def"])
        lab = Podrazdeleniya.objects.get(pk=request.POST.get("lab", request.user.doctorprofile.podrazdeleniye.pk))
    else:
        date_start = request.GET["datestart"]
        date_end = request.GET["dateend"]
        deff = int(request.GET["def"])
        lab = Podrazdeleniya.objects.get(pk=request.GET.get("lab", request.user.doctorprofile.podrazdeleniye.pk))

    date_start, date_end = try_parse_range(date_start, date_end)
    # with connection.cursor() as cursor:
    dates_cache = {}
    tubes = set()
    dirs = set()

    # if deff == 0:
    #     cursor.execute("SELECT * FROM loadready WHERE time_receive BETWEEN %s AND %s AND podr_id = %s", [date_start, date_end, request.user.doctorprofile.podrazdeleniye.pk])
    # else:
    #     cursor.execute("SELECT * FROM loadready WHERE deff = TRUE AND podr_id = %s", [request.user.doctorprofile.podrazdeleniye.pk])
    # for row in cursor.fetchall():
    #     if row[1].date() not in dates_cache:
    #         dates_cache[row[1].date()] = dateformat.format(row[1], 'd.m.y')
    #     dicttube = {"id": row[0], "direction": row[3], "date": dates_cache[row[1].date()]}
    #     result["tubes"].append(dicttube)
    #     if row[3] not in dirs:
    #         if row[2].date() not in dates_cache:
    #             dates_cache[row[2].date()] = dateformat.format(row[2], 'd.m.y')
    #         dirs.add(row[3])
    #         dictdir = {"id": row[3], "date": dates_cache[row[2].date()]}
    #         result["directions"].append(dictdir)

    if deff == 0:
        tlist = TubesRegistration.objects.filter(doc_recive__isnull=False, time_recive__range=(date_start, date_end),
                                                 # issledovaniya__napravleniye__is_printed=False,
                                                 issledovaniya__doc_confirmation__isnull=True,
                                                 issledovaniya__research__podrazdeleniye=lab,
                                                 issledovaniya__isnull=False)
    else:
        tlist = TubesRegistration.objects.filter(doc_recive__isnull=False, time_get__isnull=False,
                                                 # issledovaniya__napravleniye__is_printed=False,
                                                 issledovaniya__doc_confirmation__isnull=True,
                                                 issledovaniya__research__podrazdeleniye=lab,
                                                 issledovaniya__deferred=True, issledovaniya__isnull=False)
    # tubes =   # Загрузка пробирок,
    # лаборатория исследования которых равна лаборатории
    # текущего пользователя, принятых лабораторией и результаты для которых не напечатаны

    for tube in tlist.prefetch_related('issledovaniya_set__napravleniye'):  # перебор результатов выборки
        # iss_set = tube.issledovaniya_set.all()  # Получение списка исследований для пробирки
        # if tube.issledovaniya_set.count() == 0: continue  # пропуск пробирки, если исследований нет
        # complete = False  # Завершен ли анализ
        direction = None
        if tube.pk not in tubes:
            if not direction:
                direction = tube.issledovaniya_set.first().napravleniye
            if tube.time_recive.date() not in dates_cache:
                dates_cache[tube.time_recive.date()] = dateformat.format(tube.time_recive, 'd.m.y')
            tubes.add(tube.pk)
            dicttube = {"id": tube.pk, "direction": direction.pk,
                        "date": dates_cache[tube.time_recive.date()],
                        "tube": {"title": tube.type.tube.title,
                                 "color": tube.type.tube.color}}  # Временный словарь с информацией о пробирке
            result["tubes"].append(dicttube)  # Добавление временного словаря к ответу

        if tube.issledovaniya_set.first().napravleniye.pk not in dirs:
            if not direction:
                direction = tube.issledovaniya_set.first().napravleniye
            if direction.data_sozdaniya.date() not in dates_cache:
                dates_cache[direction.data_sozdaniya.date()] = dateformat.format(direction.data_sozdaniya, 'd.m.y')
            dirs.add(direction.pk)
            dictdir = {"id": direction.pk, "date": dates_cache[
                direction.data_sozdaniya.date()]}  # Временный словарь с информацией о направлении
            result["directions"].append(dictdir)  # Добавление временного словаря к ответу

    result["tubes"].sort(key=lambda k: k['id'])
    result["directions"].sort(key=lambda k: k['id'])
    return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
@login_required
def results_save(request):
    """ Сохранение результатов """
    result = {"ok": False}
    if request.method == "POST":
        fractions = json.loads(request.POST["fractions"])  # Загрузка фракций из запроса
        fractions_ref = json.loads(request.POST.get("fractions_ref", "{}"))  # Загрузка фракций из запроса
        issledovaniye = Issledovaniya.objects.get(
            pk=int(request.POST["issledovaniye"]))  # Загрузка исследования из запроса и выборка из базы данных
        if issledovaniye:  # Если исследование найдено

            for t in TubesRegistration.objects.filter(issledovaniya=issledovaniye):
                if not t.rstatus():
                    t.set_r(request.user.doctorprofile)

            for key in fractions.keys():  # Перебор фракций из запроса
                created = False
                if Result.objects.filter(issledovaniye=issledovaniye,
                                         fraction__pk=key).exists():  # Если результат для фракции существует
                    fraction_result = Result.objects.filter(issledovaniye=issledovaniye,
                                                            fraction__pk=key).order_by("-pk")[0]
                else:
                    fraction_result = Result(issledovaniye=issledovaniye,
                                             fraction=directory.Fractions.objects.get(
                                                 pk=key))  # Создание нового результата
                    created = True
                tv = bleach.clean(fractions[key],
                                  tags=['sup', 'sub', 'br', 'b', 'i', 'strong', 'a', 'img', 'font',
                                        'p', 'span', 'div']).replace("<br>",
                                                                     "<br/>")  # Установка значения
                fv = "" if created else fraction_result.value
                fraction_result.value = tv
                need_save = True
                if fraction_result.value == "":
                    need_save = False
                    if not created:
                        fraction_result.delete()
                elif tv == fv:
                    need_save = False
                if need_save:
                    fraction_result.get_units(needsave=False)
                    fraction_result.iteration = 1  # Установка итерации
                    if key in fractions_ref:
                        r = fractions_ref[key]
                        fraction_result.ref_title = r["title"]
                        fraction_result.ref_about = r["about"]
                        fraction_result.ref_m = r["m"]
                        fraction_result.ref_f = r["f"]
                        fraction_result.save()
                    else:
                        fraction_result.ref_title = "Default"
                        fraction_result.ref_about = ""
                        fraction_result.ref_m = None
                        fraction_result.ref_f = None
                        fraction_result.get_ref(re_save=True, needsave=False)
                        fraction_result.save()
            issledovaniye.doc_save = request.user.doctorprofile  # Кто сохранил
            from django.utils import timezone

            issledovaniye.time_save = timezone.now()  # Время сохранения
            issledovaniye.lab_comment = request.POST.get("comment", "")
            issledovaniye.save()
            result = {"ok": True}

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
            from django.utils import timezone
            from directions.models import Result
            for r in Result.objects.filter(issledovaniye=issledovaniye):
                r.get_ref()
            issledovaniye.time_confirmation = timezone.now()  # Время подтверждения
            issledovaniye.save()
            slog.Log(key=request.POST["pk"], type=14, body=json.dumps({"dir": issledovaniye.napravleniye.pk}),
                     user=request.user.doctorprofile).save()

    return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
@login_required
def result_confirm_list(request):
    """ Пакетное подтверждение результатов """
    result = {"ok": False}
    if request.method == "POST":
        iss_pks = json.loads(request.POST["list"])
        for pk in iss_pks:
            issledovaniye = Issledovaniya.objects.get(pk=int(pk))
            if issledovaniye.doc_save and not issledovaniye.doc_confirmation:  # Если исследование сохранено
                from directions.models import Result
                for r in Result.objects.filter(issledovaniye=issledovaniye):
                    r.get_ref()
                issledovaniye.doc_confirmation = request.user.doctorprofile  # Кто подтвердил
                from django.utils import timezone
                issledovaniye.time_confirmation = timezone.now()  # Время подтверждения
                issledovaniye.save()
                slog.Log(key=pk, type=14, body="", user=request.user.doctorprofile).save()
        result["ok"] = True
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
import re


def lr(s, l=7, r=17):
    if not s:
        s = ""
    return s.ljust(l).rjust(r)


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


@logged_in_or_token
def result_print(request):
    """ Печать результатов """
    inline = request.GET.get("inline", "1") == "1"
    response = HttpResponse(content_type='application/pdf')

    if inline:
        if SettingManager.get("pdf_auto_print", "true", "b"):
            pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:true,bSilent:false,bShrinkToFit:true}\);)>>'
        response['Content-Disposition'] = 'inline; filename="results.pdf"'
    else:
        response['Content-Disposition'] = 'attachment; filename="results.pdf"'

    pk = json.loads(request.GET["pk"])
    show_norm = True  # request.GET.get("show_norm", "0") == "1"

    from io import BytesIO
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.units import mm
    from django.utils import timezone
    import os.path

    pdfmetrics.registerFont(
        TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))
    pdfmetrics.registerFont(
        TTFont('Champ', os.path.join(FONTS_FOLDER, 'Champ.ttf')))
    pdfmetrics.registerFont(
        TTFont('ChampB', os.path.join(FONTS_FOLDER, 'Calibri.ttf')))
    pdfmetrics.registerFont(
        TTFont('CalibriBold', os.path.join(FONTS_FOLDER, 'calibrib.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansBold', os.path.join(FONTS_FOLDER, 'OpenSans-Bold.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansItalic', os.path.join(FONTS_FOLDER, 'OpenSans-Italic.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansBoldItalic', os.path.join(FONTS_FOLDER, 'OpenSans', 'OpenSans-BoldItalic.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansLight', os.path.join(FONTS_FOLDER, 'OpenSans', 'OpenSans-Light.ttf')))
    pdfmetrics.registerFont(
        TTFont('Consolas', os.path.join(FONTS_FOLDER, 'consolas.ttf')))
    pdfmetrics.registerFont(
        TTFont('Consolas-Bold', os.path.join(FONTS_FOLDER, 'Consolas-Bold.ttf')))

    buffer = BytesIO()

    split = request.GET.get("split", "1") == "1"
    protocol_plain_text = request.GET.get("protocol_plain_text", "0") == "1"

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, PTOContainer, Image
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib import colors
    # c = canvas.Canvas(buffer, pagesize=A4)
    # w, h = A4

    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=(54 if request.GET.get("leftnone", "0") == "0" else 5) * mm,
                            rightMargin=5 * mm, topMargin=5 * mm,
                            bottomMargin=5 * mm, allowSplitting=1,
                            title="Результаты для направлений {}".format(", ".join([str(x) for x in pk])))

    naprs = []
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "OpenSans"
    style.fontSize = 9
    style_ml = deepcopy(style)
    style_ml.leftIndent = 5 * mm
    styleBold = deepcopy(style)
    styleBold.fontName = "OpenSansBold"
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

    styleSheet["BodyText"].wordWrap = 'CJK'
    stl = deepcopy(styleSheet["BodyText"])
    from reportlab.lib.enums import TA_CENTER
    stl.alignment = TA_CENTER

    import base64
    img_path = os.path.join(FONTS_FOLDER, '..', 'static', 'img')
    if not os.path.exists(img_path):
        os.makedirs(img_path)
    logo_path = os.path.join(img_path, 'logo.png')
    if request.GET.get("update_logo", "0") == "1" or not os.path.isfile(logo_path):
        with open(logo_path, "wb") as fh:
            fh.write(base64.decodebytes(SettingManager.get("logo_base64_img").split(",")[1].encode()))

    i = Image(logo_path)
    nw = 158
    i.drawHeight = i.drawHeight * (nw / i.drawWidth)
    i.drawWidth = nw
    logo_col = [i, '', '', '', '', Paragraph(
        'Результат из <font face="OpenSansBoldItalic">L²</font>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<font face="OpenSansLight">(L2-irk.ru)</font><br/><br/>%s<br/>%s<br/>%s' % (
            SettingManager.get("org_title"), SettingManager.get("org_www"), SettingManager.get("org_phones")),
        styleAb), '', '', '']
    pw = doc.width
    ph = doc.height
    import operator

    def print_vtype(data, f, iss, j, style_t, styleSheet):

        import operator
        if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
            result = Result.objects.filter(issledovaniye=iss, fraction=f).order_by("-pk")[0].value.replace("<br>",
                                                                                                           "<br/>")
            #my start
            print("Из результата")
            print(result)
            for fr in range(len(result)):
                print(result[fr])
            #my end

            # try:
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

                tmp = [Paragraph(
                    '&nbsp;&nbsp;&nbsp;&nbsp;<font face="OpenSans" size="8">' + (
                        "" if len(norm_vals) == 0 else f.title + ": ") + val["title"] + "</font>",
                    styleSheet["BodyText"]), "", "", "", "", ""]
                data.append(tmp)
                if len(norm_vals) > 0:
                    li = 0
                    norm_vals.sort(key=operator.itemgetter('k'))
                    for idx, rowv in enumerate(norm_vals):
                        li = idx
                        if li % 2 == 0:
                            tmp = [Paragraph('<font face="OpenSans" size="8">' + rowv["title"] + "</font>",
                                             styleSheet["BodyText"]),
                                   Paragraph('<font face="OpenSans" size="8">' + rowv["value"] + "</font>",
                                             styleSheet["BodyText"]), ""]
                        else:
                            tmp.append(Paragraph('<font face="OpenSans" size="8">' + rowv["title"] + "</font>",
                                                 styleSheet["BodyText"]))
                            tmp.append(Paragraph('<font face="OpenSans" size="8">' + rowv["value"] + "</font>",
                                                 styleSheet["BodyText"]))
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
    # cl = Client()
    for direction in sorted(Napravleniya.objects.filter(pk__in=pk).distinct(),
                            key=lambda dir: dir.client.individual.pk * 100000000 + Result.objects.filter(
                                issledovaniye__napravleniye=dir).count() * 10000000 + dir.pk):
        dpk = direction.pk
        if not direction.is_all_confirm():
            continue
        # if not normis:
        #    cl.directions.check_send_results(direction)
        dates = {}
        date_t = ""
        has_paraclinic = False
        for iss in Issledovaniya.objects.filter(napravleniye=direction, time_save__isnull=False):
            if iss.time_save:
                dt = str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                if dt not in dates.keys():
                    dates[dt] = 0
                dates[dt] += 1
            if iss.tubes.exists() and iss.tubes.first().time_get:
                date_t = strdate(iss.tubes.first().time_get)
            if iss.research.is_paraclinic:
                has_paraclinic = True
        maxdate = ""
        if dates != {}:
            maxdate = max(dates.items(), key=operator.itemgetter(1))[0]

        if not has_paraclinic and date_t == "":
            date_t = maxdate

        fwb = []
        data = [
            ["Номер:", str(dpk)],
            ["Пациент:", Paragraph(direction.client.individual.fio(), styleTableMonoBold)],
            ["Пол:", direction.client.individual.sex],
            ["Возраст:", direction.client.individual.age_s(direction=direction)],
        ]
        data += [["Дата забора:", date_t]] if not has_paraclinic else [["Диагноз:", direction.diagnos]]
        data += [[Paragraph('&nbsp;', styleTableSm), Paragraph('&nbsp;', styleTableSm)],
                 ["РМИС ID:" if direction.client.base.is_rmis else "№ карты:",
                  direction.client.number_with_type() + (" - архив" if direction.client.is_archive else "")]]
        if not direction.imported_from_rmis:
            data.append(
                ["Врач:", "<font>%s<br/>%s</font>" % (direction.doc.get_fio(), direction.doc.podrazdeleniye.title)])
        elif direction.imported_org:
            data.append(["<font>Направляющая<br/>организация:</font>", direction.imported_org.title])

        data = [[Paragraph(y, styleTableMono) if isinstance(y, str) else y for y in data[xi]] + [logo_col[xi]] for
                xi in
                range(len(data))]

        t = Table(data, colWidths=[doc.width * 0.165, doc.width - 158 - doc.width * 0.165, 158])
        t.setStyle(TableStyle([
            ('ALIGN', (-1, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('VALIGN', (-1, 0), (-1, 0), 'BOTTOM'),
            ('VALIGN', (-1, 5), (-1, 5), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (-1, 0), (-1, -1), 0),
            ('TOPPADDING', (-1, 0), (-1, -1), 0),
            ('TOPPADDING', (-1, 5), (-1, 5), 3),
            ('TOPPADDING', (0, 5), (1, 5), 0),
            ('TOPPADDING', (0, 6), (1, 6), -6),
            ('BOTTOMPADDING', (0, 5), (1, 5), 0),
            ('LEFTPADDING', (0, 5), (1, 5), 0),
            ('RIGHTPADDING', (0, 5), (1, 5), 0),
            ('SPAN', (-1, 0), (-1, 4)),
            ('SPAN', (-1, 5), (-1, -1))

        ]))
        fwb.append(t)
        if not has_paraclinic:
            tw = pw

            no_units_and_ref = any(
                [x.research.no_units_and_ref for x in Issledovaniya.objects.filter(napravleniye=direction)])

            data = []
            tmp = [Paragraph('<font face="OpenSansBold" size="8">Исследование</font>', styleSheet["BodyText"]),
                   Paragraph(
                       '<font face="OpenSansBold" size="8">Результат</font>' + (
                           '' if no_units_and_ref else '<br/><font face="OpenSans" size="8">(# - не норма)</font>'),
                       styleSheet["BodyText"])]
            if not no_units_and_ref:
                if direction.client.individual.sex.lower() == "м":
                    tmp.append(
                        Paragraph('<font face="OpenSansBold" size="8">Референсные значения (М)</font>',
                                  styleSheet["BodyText"]))
                else:
                    tmp.append(
                        Paragraph('<font face="OpenSansBold" size="8">Референсные значения (Ж)</font>',
                                  styleSheet["BodyText"]))
                tmp.append(
                    Paragraph('<font face="OpenSansBold" size="8">Единицы<br/>измерения</font>',
                              styleSheet["BodyText"]))

            tmp.append(Paragraph('<font face="OpenSansBold" size="8">Исполнитель</font>', styleSheet["BodyText"]))
            # tmp.append(Paragraph('<font face="OpenSans" size="8">Дата заб.</font>', styleSheet["BodyText"]))
            tmp.append(Paragraph('<font face="OpenSansBold" size="8">Дата</font>', styleSheet["BodyText"]))
            data.append(tmp)
            if no_units_and_ref:
                cw = [int(tw * 0.26), int(tw * 0.482), int(tw * 0.178)]
            else:
                cw = [int(tw * 0.26), int(tw * 0.178), int(tw * 0.17), int(tw * 0.134), int(tw * 0.178)]
            cw = cw + [tw - sum(cw)]
            t = Table(data, colWidths=cw)
            style_t = TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                  ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                  ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                  ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                  ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                  ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                  ('TOPPADDING', (0, 0), (-1, -1), 2),
                                  ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                  ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                                  ])
            style_t.add('BOTTOMPADDING', (0, 0), (-1, 0), 1)
            style_t.add('TOPPADDING', (0, 0), (-1, 0), 0)

            t.setStyle(style_t)
            t.spaceBefore = 3 * mm
            t.spaceAfter = 0

            prev_conf = ""
            prev_date_conf = ""

            has0 = directory.Fractions.objects.filter(
                research__pk__in=[x.research.pk for x in Issledovaniya.objects.filter(napravleniye=direction)],
                hide=False,
                render_type=0).exists()

            if has0:
                fwb.append(t)

            iss_list = Issledovaniya.objects.filter(napravleniye=direction)
            result_style = styleSheet["BodyText"] if no_units_and_ref else stl
            pks = []
            for iss in iss_list.order_by("research__direction_id", "research__pk", "tubes__id",
                                         "research__sort_weight"):
                if iss.pk in pks:
                    continue
                pks.append(iss.pk)
                data = []
                fractions = directory.Fractions.objects.filter(research=iss.research, hide=False,
                                                               render_type=0).order_by("pk").order_by("sort_weight")
                # my start

                print("Фракции 2")

                for fr in range(len(fractions)):
                    print(fractions[fr])

                print(fractions[0])
                #my end
                if fractions.count() > 0:
                    if fractions.count() == 1:
                        tmp = [Paragraph('<font face="OpenSans" size="8">' + iss.research.title + "</font>",
                                         styleSheet["BodyText"])]
                        norm = "none"
                        if Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).exists():
                            r = Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).order_by("-pk")[0]
                            ref = r.get_ref()
                            if show_norm:
                                norm = r.get_is_norm(recalc=True)
                            result = result_normal(r.value)
                            f_units = r.get_units()
                        else:
                            continue
                        if not iss.doc_confirmation and iss.deferred:
                            result = "отложен"
                        elif iss.time_save and maxdate != str(dateformat.format(iss.time_save, settings.DATE_FORMAT)):
                            pass  # result += "<br/>" + str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                        f = fractions[0]
                        st = TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                         ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                         ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                         ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                         ('BOX', (0, 0), (-1, -1), 0.8, colors.black),

                                         ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                         ('TOPPADDING', (0, 0), (-1, -1), 3),
                                         ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                         ('BOTTOMPADDING', (0, 0), (-1, -1), -1),
                                         ])

                        if f.render_type == 0:
                            if norm in ["none", "normal"]:
                                tmp.append(
                                    Paragraph('<font face="ChampB" size="8">' + result + "</font>", result_style))
                            elif norm == "maybe":
                                tmp.append(
                                    Paragraph('<font face="CalibriBold" size="8">' + result + "</font>", result_style))
                            else:
                                tmp.append(
                                    Paragraph('<font face="CalibriBold" size="8"># ' + result + "</font>",
                                              result_style))
                            if not no_units_and_ref:
                                tmp.append(
                                    Paragraph('<font face="OpenSans" size="7">' + get_r(ref) + "</font>",
                                              stl))

                                tmp.append(
                                    Paragraph('<font face="OpenSans" size="7">' + f_units + "</font>", stl))

                            if iss.doc_confirmation:
                                if prev_conf != iss.doc_confirmation.get_fio():
                                    prev_conf = iss.doc_confirmation.get_fio()
                                    prev_date_conf = ""
                                    tmp.append(Paragraph('<font face="OpenSans" size="7">%s</font>' % prev_conf,
                                                         styleSheet["BodyText"]))
                                else:
                                    tmp.append("")
                                if prev_date_conf != strdate(iss.time_confirmation, short_year=True):
                                    prev_date_conf = strdate(iss.time_confirmation, short_year=True)
                                    tmp.append(Paragraph('<font face="OpenSans" size="7">%s</font>' % prev_date_conf,
                                                         styleSheet["BodyText"]))
                                else:
                                    tmp.append("")
                            else:
                                tmp.append("")
                                tmp.append("")

                            data.append(tmp)
                        elif f.render_type == 1:
                            tmp.append("")
                            tmp.append("")
                            tmp.append("")

                            if iss.doc_confirmation:
                                tmp.append(Paragraph(
                                    '<font face="OpenSansBold" size="7">%s</font>' % iss.doc_confirmation.get_fio(),
                                    styleSheet["BodyText"]))
                                tmp.append(Paragraph('<font face="OpenSansBold" size="7">%s</font>' % (
                                    "" if not iss.tubes.exists() or not iss.tubes.first().time_get else strdate(
                                        iss.tubes.first().time_get)), styleSheet["BodyText"]))
                                tmp.append(Paragraph(
                                    '<font face="OpenSansBold" size="7">%s</font>' % strdate(iss.time_confirmation),
                                    styleSheet["BodyText"]))
                            else:
                                tmp.append("")
                                tmp.append(Paragraph(
                                    '<font face="OpenSansBold" size="7">%s</font>' % strdate(
                                        iss.tubes.first().time_get), styleSheet["BodyText"]))
                                tmp.append("")
                            data.append(tmp)

                            j = print_vtype(data, f, iss, 1, st, styleSheet)
                            data.append([Paragraph(
                                '<font face="OpenSans" size="8">S - чувствителен; R - резистентен; I - промежуточная чувствительность;</font>',
                                styleSheet["BodyText"])])
                            st.add('SPAN', (0, j), (-1, j))
                            st.add('BOX', (0, j), (-1, j), 1, colors.white)
                            st.add('BOX', (0, j - 1), (-1, j - 1), 1, colors.black)

                        t = Table(data, colWidths=cw)
                        t.setStyle(st)
                        t.spaceBefore = 0
                    else:
                        tmp = [Paragraph('<font face="OpenSansBold" size="8">' + iss.research.title + '</font>' +
                                         (
                                             "" if iss.comment == "" or True else '<font face="OpenSans" size="8"><br/>Материал - ' + iss.comment + '</font>'),
                                         styleSheet["BodyText"]), '']
                        if not no_units_and_ref:
                            tmp.append("")
                            tmp.append("")

                        if iss.doc_confirmation:
                            if prev_conf != iss.doc_confirmation.get_fio():
                                prev_conf = iss.doc_confirmation.get_fio()
                                prev_date_conf = ""
                                tmp.append(Paragraph('<font face="OpenSans" size="7">%s</font>' % prev_conf,
                                                     styleSheet["BodyText"]))
                            else:
                                tmp.append("")
                            if prev_date_conf != strdate(iss.time_confirmation, short_year=True):
                                prev_date_conf = strdate(iss.time_confirmation, short_year=True)
                                tmp.append(Paragraph('<font face="OpenSans" size="7">%s</font>' % prev_date_conf,
                                                     styleSheet["BodyText"]))
                            else:
                                tmp.append("")
                        else:
                            tmp.append("")
                            tmp.append("")

                        data.append(tmp)
                        ts = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                              # ('SPAN',(0,0),(-1,0)),
                              ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                              ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                              ('INNERGRID', (0, 0), (-1, -1), 0.1, colors.white),
                              ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                              ('LEFTPADDING', (0, 0), (-1, -1), 4),
                              ('TOPPADDING', (0, 0), (-1, -1), 3),
                              ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                              ('BOTTOMPADDING', (0, 0), (-1, -1), -1),
                              ]

                        style_t = TableStyle(ts)
                        j = 0

                        for f in fractions:
                            j += 1

                            tmp = []
                            if f.render_type == 0:
                                tmp.append(Paragraph('<font face="OpenSans" size="8">' + f.title + "</font>",
                                                     styleSheet["BodyText"]))

                                norm = "none"
                                # if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
                                if Result.objects.filter(issledovaniye=iss, fraction=f).exists() and f.print_title==False:
                                    r = Result.objects.filter(issledovaniye=iss, fraction=f).order_by("-pk")[0]
                                    if show_norm:
                                        norm = r.get_is_norm(recalc=True)
                                    result = result_normal(r.value)
                                    ref = r.get_ref()
                                    f_units = r.get_units()
                                elif f.print_title:
                                    # tmp=[]
                                    tmp[0]=(Paragraph('<font face="CalibriBold" size="10">{}</font>'.format(f.title),
                                                         styleSheet["BodyText"]))
                                    data.append(tmp)
                                    continue
                                else:
                                    continue
                                if not iss.doc_confirmation and iss.deferred:
                                    result = "отложен"
                                # elif iss.time_save and maxdate != str(dateformat.format(iss.time_save, settings.DATE_FORMAT)):
                                #    result += "<br/>" + str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                                if norm in ["none", "normal"]:
                                    tmp.append(
                                        Paragraph('<font face="ChampB" size="8">' + result + "</font>", result_style))
                                elif norm == "maybe":
                                    tmp.append(
                                        Paragraph('<font face="CalibriBold" size="8">' + result + "</font>",
                                                  result_style))
                                else:
                                    tmp.append(
                                        Paragraph('<font face="CalibriBold" size="8"># ' + result + "</font>",
                                                  result_style))
                                if not no_units_and_ref:
                                    tmp.append(Paragraph('<font face="OpenSans" size="7">' + get_r(ref) + "</font>",
                                                         stl))

                                    tmp.append(Paragraph('<font face="OpenSans" size="7">' + f_units + "</font>", stl))
                                tmp.append("")
                                tmp.append("")
                                data.append(tmp)
                            elif f.render_type == 1:
                                jp = j
                                j = print_vtype(data, f, iss, j, style_t, styleSheet)

                                if j - jp > 2:
                                    data.append([Paragraph(
                                        '<font face="OpenSans" size="8">S - чувствителен; R - резистентен; I - промежуточная чувствительность;</font>',
                                        styleSheet["BodyText"])])
                                    style_t.add('SPAN', (0, j), (-1, j))
                                    style_t.add('BOX', (0, j), (-1, j), 1, colors.white)
                                    j -= 1

                        for k in range(0, 6):
                            style_t.add('INNERGRID', (k, 0),
                                        (k, j), 0.1, colors.black)
                            style_t.add('BOX', (k, 0), (k, j),
                                        0.8, colors.black)

                            style_t.add('BOTTOMPADDING', (0, 0), (0, -1), 0)
                            style_t.add('TOPPADDING', (0, 0), (0, -1), 0)

                        t = Table(data, colWidths=cw)
                        t.setStyle(style_t)
                    fwb.append(t)

                fractions = directory.Fractions.objects.filter(research=iss.research, hide=False,
                                                               render_type=1).order_by("pk").order_by("sort_weight")
                if fractions.count() > 0:
                    data = []
                    if not has0:
                        tmp = [Paragraph('<font face="OpenSansBold" size="8">Исследование</font>',
                                         styleSheet["BodyText"]),
                               Paragraph('<font face="OpenSansBold" size="8">Дата сбора материала</font>',
                                         styleSheet["BodyText"]),
                               Paragraph('<font face="OpenSansBold" size="8">Дата исполнения</font>',
                                         styleSheet["BodyText"]),
                               Paragraph('<font face="OpenSansBold" size="8">Исполнитель</font>',
                                         styleSheet["BodyText"])]
                        data.append(tmp)

                        tmp = [Paragraph('<font face="OpenSansBold" size="8">%s</font>' % iss.research.title,
                                         styleSheet["BodyText"]),
                               Paragraph('<font face="OpenSans" size="8">%s%s</font>' % (
                                   "" if not iss.tubes.exists() or not iss.tubes.first().time_get else strdate(
                                       iss.tubes.first().time_get), "" if not iss.comment else "<br/>" + iss.comment,),
                                         styleSheet["BodyText"]),
                               Paragraph('<font face="OpenSans" size="8">%s</font>' % (
                                   "Не подтверждено" if not iss.time_confirmation else strdate(iss.time_confirmation)),
                                         styleSheet["BodyText"]),
                               Paragraph('<font face="OpenSans" size="8">%s</font>' % (
                                   "Не подтверждено" if not iss.doc_confirmation else iss.doc_confirmation.get_fio()),
                                         styleSheet["BodyText"])]
                        data.append(tmp)

                        cw = [int(tw * 0.34), int(tw * 0.24), int(tw * 0.2)]
                        cw = cw + [tw - sum(cw)]
                        t = Table(data, colWidths=cw)
                        style_t = TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                              ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                              ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                              ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                              ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                              ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                              ('TOPPADDING', (0, 0), (-1, -1), 0),
                                              ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                              ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                                              ])

                        style_t.add('LINEBELOW', (0, -1), (-1, -1), 2, colors.black)
                        t.setStyle(style_t)
                        t.spaceBefore = 3 * mm
                        t.spaceAfter = 0
                        fwb.append(t)

                    has_anti = False
                    for f in fractions:
                        j = 0
                        if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
                            result = Result.objects.filter(issledovaniye=iss, fraction=f).order_by("-pk")[0].value

                            if result == "":
                                continue
                            jo = json.loads(result)["rows"]
                            for key, val in jo.items():
                                if val["title"] != "":
                                    data = []
                                    style_t.add('SPAN', (0, j), (-1, j))
                                    j += 1

                                    norm_vals = []
                                    for rowk, rowv in val["rows"].items():
                                        if rowv["value"] not in ["", "null"]:
                                            norm_vals.insert(0, {"title": rowv["title"], "value": rowv["value"],
                                                                 "k": int(rowk)})
                                    tmp = [Paragraph(
                                        '<font face="OpenSansBold" size="8">' + (
                                            val["title"] if len(norm_vals) == 0 else "Выделенная культура: " + val[
                                                "title"]) + "</font>",
                                        styleSheet["BodyText"]), "", "", "", "", ""]
                                    data.append(tmp)

                                    if len(norm_vals) > 0:
                                        has_anti = True

                                        tmp = [Paragraph(
                                            '<font face="OpenSansBold" size="8">%s</font>' % f.title,
                                            styleSheet["BodyText"]), "", "", "", "", ""]
                                        data.append(tmp)
                                        j += 1

                                        li = 0
                                        norm_vals.sort(key=operator.itemgetter('k'))
                                        for idx, rowv in enumerate(norm_vals):
                                            li = idx
                                            if li % 3 == 0:
                                                tmp = []

                                            tmp.append(
                                                Paragraph('<font face="OpenSans" size="8">' + rowv["title"] + "</font>",
                                                          styleSheet["BodyText"]))
                                            tmp.append(
                                                Paragraph('<font face="OpenSans" size="8">' + rowv["value"] + "</font>",
                                                          styleSheet["BodyText"]))
                                            if li % 3 == 2:
                                                data.append(tmp)
                                                j += 1

                                        if li % 3 == 0:
                                            tmp.append("")
                                            tmp.append("")
                                            tmp.append("")
                                            tmp.append("")
                                        if li % 3 == 1:
                                            tmp.append("")
                                            tmp.append("")
                                        if li % 3 < 2:
                                            data.append(tmp)
                                            j += 1
                                    cw = [int(tw * 0.28), int(tw * 0.06),
                                          int(tw * 0.27), int(tw * 0.06),
                                          int(tw * 0.27)]
                                    cw = cw + [tw - sum(cw)]
                                    t = Table(data, colWidths=cw)

                                    style_t = TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                                          ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                                          ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                                          ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                                          ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                                          ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                                          ('TOPPADDING', (0, 0), (-1, -1), 2),
                                                          ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                                          ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                                                          ])

                                    style_t.add('BOTTOMPADDING', (0, 0), (-1, -1), 1)
                                    style_t.add('TOPPADDING', (0, 0), (-1, -1), 2)

                                    style_t.add('SPAN', (0, 0), (-1, 0))
                                    style_t.add('SPAN', (0, 1), (-1, 1))

                                    t.setStyle(style_t)
                                    fwb.append(t)
                    if has_anti:
                        data = []
                        tmp = [[Paragraph(
                            '<font face="OpenSans" size="8">S - чувствителен; R - резистентен; I - промежуточная чувствительность;</font>',
                            styleSheet["BodyText"])], "", "", "", "", ""]
                        data.append(tmp)
                        cw = [int(tw * 0.23), int(tw * 0.11), int(tw * 0.22), int(tw * 0.11), int(tw * 0.22)]
                        cw = cw + [tw - sum(cw)]
                        t = Table(data, colWidths=cw)
                        style_t = TableStyle([('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                              ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                              ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                              ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                              ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                              ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                              ('TOPPADDING', (0, 0), (-1, -1), 2),
                                              ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                              ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                                              ])
                        style_t.add('BOTTOMPADDING', (0, 0), (-1, 0), 1)
                        style_t.add('TOPPADDING', (0, 0), (-1, 0), 0)
                        style_t.add('SPAN', (0, 0), (-1, 0))

                        t.setStyle(style_t)
                        fwb.append(t)
                if iss.lab_comment and iss.lab_comment != "":
                    data = []
                    tmp = [[Paragraph(
                        '<font face="OpenSans" size="8">Комментарий</font>',
                        styleSheet["BodyText"])], [Paragraph(
                        '<font face="OpenSans" size="8">%s</font>' % (iss.lab_comment.replace("\n", "<br/>")),
                        styleSheet["BodyText"])], "", "", "", ""]
                    data.append(tmp)
                    cw = [int(tw * 0.26), int(tw * 0.178), int(tw * 0.17), int(tw * 0.134), int(tw * 0.178)]
                    cw = cw + [tw - sum(cw)]
                    t = Table(data, colWidths=cw)
                    style_t = TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                          ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                          ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                          ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                          ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                          ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                          ('TOPPADDING', (0, 0), (-1, -1), 2),
                                          ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                          ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                                          ])
                    style_t.add('BOTTOMPADDING', (0, 0), (-1, 0), 1)
                    style_t.add('TOPPADDING', (0, 0), (-1, 0), 0)
                    style_t.add('SPAN', (1, 0), (-1, 0))

                    t.setStyle(style_t)
                    fwb.append(t)
        else:
            for iss in Issledovaniya.objects.filter(napravleniye=direction).order_by("research__pk"):
                fwb.append(Spacer(1, 5 * mm))
                if iss.doc_confirmation.podrazdeleniye.vaccine:
                    fwb.append(Paragraph("Вакцина: " + iss.research.title, styleBold))
                else:
                    fwb.append(Paragraph("Исследование: " + iss.research.title, styleBold))
                if not protocol_plain_text:
                    for group in directory.ParaclinicInputGroups.objects.filter(research=iss.research).order_by(
                            "order"):
                        results = ParaclinicResult.objects.filter(issledovaniye=iss, field__group=group).exclude(
                            value="").order_by("field__order")
                        group_title = False
                        if results.exists():
                            fwb.append(Spacer(1, 1 * mm))
                            if group.show_title and group.show_title != "":
                                fwb.append(Paragraph(group.title, styleBold))
                                fwb.append(Spacer(1, 0.25 * mm))
                                group_title = True
                            for r in results:
                                if r.field.title != "":
                                    fwb.append(Paragraph(
                                        "<font face=\"OpenSansBold\">{}:</font> {}".format(r.field.title,
                                                                                           r.value.replace("\n",
                                                                                                           "<br/>")),
                                        style_ml if group_title else style))
                                else:
                                    fwb.append(Paragraph(r.value.replace("\n", "<br/>"), style))
                else:
                    txt = ""
                    for group in directory.ParaclinicInputGroups.objects.filter(research=iss.research).order_by(
                            "order"):
                        results = ParaclinicResult.objects.filter(issledovaniye=iss, field__group=group).exclude(
                            value="").order_by("field__order")
                        if results.exists():
                            if group.show_title and group.title != "":
                                txt += "<font face=\"OpenSansBold\">{}:</font>&nbsp;".format(group.title)
                            vals = []
                            for r in results:
                                if r.field.title != "":
                                    vals.append("{}:&nbsp;{}".format(r.field.title, r.value))
                                else:
                                    vals.append(r.value)
                            txt += "; ".join(vals)
                            txt = txt.strip()
                            if len(txt) > 0 and txt.strip()[-1] != ".":
                                txt += ". "
                            elif len(txt) > 0:
                                txt += " "

                    fwb.append(Paragraph(txt, style))
                fwb.append(Spacer(1, 2.5 * mm))
                t1 = iss.get_visit_date()
                t2 = strdate(iss.time_confirmation)
                fwb.append(Paragraph("Дата оказания услуги: {}".format(t1), styleBold))
                fwb.append(Paragraph("Дата формирования протокола: {}".format(t2), styleBold))
                if iss.doc_confirmation.podrazdeleniye.vaccine:
                    fwb.append(Paragraph("Исполнитель: {}, {}".format(iss.doc_confirmation.fio,
                                                                      iss.doc_confirmation.podrazdeleniye.title),
                                         styleBold))
                else:
                    fwb.append(Paragraph("Исполнитель: врач {}, {}".format(iss.doc_confirmation.fio,
                                                                       iss.doc_confirmation.podrazdeleniye.title),
                                         styleBold))
                fwb.append(Spacer(1, 2.5 * mm))

        if client_prev == direction.client.individual.pk and not split:
            naprs.append(HRFlowable(width=pw, spaceAfter=3 * mm, spaceBefore=3 * mm, color=colors.lightgrey))
        elif client_prev > -1:
            naprs.append(PageBreak())
        naprs.append(KeepTogether([KeepInFrame(content=fwb, maxWidth=pw, maxHeight=ph - 6 * mm, hAlign='RIGHT')]))
        client_prev = direction.client.individual.pk

    doc.build(naprs)

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    slog.Log(key=request.GET["pk"],
             type=15,
             body=json.dumps({"leftnone": request.GET.get("leftnone", "0"), "split": request.GET.get("split", "1")}),
             user=request.user.doctorprofile if request.user.is_authenticated else None).save()

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

    import operator
    maxdate = max(dates.items(), key=operator.itemgetter(1))[0]

    last_iss = napr.issledovaniya_set.filter(time_confirmation__isnull=False).order_by("-time_confirmation").first()

    c.setFont('OpenSans', 10)
    c.drawCentredString(w / 4 + s, h - 18, SettingManager.get("org_title"))
    c.setFont('OpenSans', 8)
    c.drawCentredString(w / 4 + s, h - 28, "(%s. %s)" % (SettingManager.get("org_address"), SettingManager.get(
        "org_phones"),))  # "(г. Иркутск, б-р. Гагарина, 18. тел: 280-808, 280-809)")
    c.setFont('OpenSans', 10)
    c.drawString(paddingx + s, h - 42, "Результаты анализов")

    c.setFont('OpenSans', 20)
    c.drawString(paddingx + s, h - 28, "№ " + str(obj))

    c.setFont('OpenSans', 10)
    c.drawRightString(s + w / 2 - paddingx, h - 42, "Лечащий врач: " + napr.doc.get_fio())
    c.drawRightString(s + w / 2 - paddingx, h - 54,
                      "Дата: " + maxdate)

    c.drawString(s + paddingx, h - 54, "ФИО пациента: " + napr.client.fio())
    c.drawString(s + paddingx, h - 64, "Карта: " + napr.client.number_with_type())
    c.drawCentredString(w / 4 + s, h - 64, "Пол: " + napr.client.sex)

    # c.drawRightString(s + w/2 - paddingx, h-97, "Дата рождения: " + str(dateformat.format(napr.client.bd(), settings.DATE_FORMAT)) + " (" + str(napr.client.age()) + " лет)")

    c.drawRightString(s + w / 2 - paddingx, h - 64, napr.client.age_s(direction=napr) + " " + "(д.р. " + str(
        dateformat.format(napr.client.bd(), settings.DATE_FORMAT)) + ")")
    if last_iss and last_iss.doc_confirmation:
        c.drawString(s + paddingx, 18, "Врач (лаборант): " + last_iss.doc_confirmation.fio.split(" ")[0] + " " +
                     last_iss.doc_confirmation.fio.split(" ")[1][0] + "." + last_iss.doc_confirmation.fio.split(" ")[2][
                         0] + ".   ____________________   (подпись)")
    else:
        c.drawString(s + paddingx, 18, "Результат не подтвержден")
    c.setFont('OpenSans', 8)

    iss_list = Issledovaniya.objects.filter(napravleniye=napr).order_by("research__pk", "research__sort_weight")
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    styleSheet = getSampleStyleSheet()

    tw = w / 2 - paddingx * 2
    pos = h - 64 - paddingx / 2

    data = []
    tmp = [Paragraph('<font face="OpenSans" size="7">Исследование</font>', styleSheet["BodyText"]),
           Paragraph('<font face="OpenSans" size="7">Значение</font>', styleSheet["BodyText"]),
           Paragraph('<font face="OpenSans" size="7">Ед. изм.</font>', styleSheet["BodyText"])]
    if napr.client.sex.lower() == "м":
        tmp.append(
            Paragraph('<font face="OpenSans" size="7">Референсы (М)</font>', styleSheet["BodyText"]))
    else:
        tmp.append(
            Paragraph('<font face="OpenSans" size="7">Референсы (Ж)</font>', styleSheet["BodyText"]))
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
        fractions = directory.Fractions.objects.filter(research=iss.research).order_by("pk").order_by("sort_weight")
        if fractions.count() == 1:
            tmp = [Paragraph('<font face="OpenSansBold" size="7">' + iss.research.title + '</font>' +
                             '<font face="OpenSansBold" size="7">' + (
                                 "" if not iss.comment else "<br/>" + iss.comment) + "</font>",
                             styleSheet["BodyText"])]
            result = "не завершено"
            ref = {"": ""}
            f_units = fractions[0].units
            if Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).exists():
                r = Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).order_by("-pk")[0]
                ref = r.get_ref()
                result = r.value
                f_units = r.get_units()
            if not iss.doc_confirmation and iss.deferred:
                result = "отложен"
            elif iss.time_save and maxdate != str(dateformat.format(iss.time_save, settings.DATE_FORMAT)):
                result += "<br/>" + str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
            tmp.append(Paragraph('<font face="ChampB" size="8">' + result + "</font>", styleSheet["BodyText"]))
            tmp.append(
                Paragraph('<font face="OpenSans" size="7">&nbsp;&nbsp;&nbsp;' + f_units + "</font>",
                          styleSheet["BodyText"]))

            tmp.append(Paragraph('<font face="OpenSans" size="7">' + get_r(ref) + "</font>",
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
            tmp = [Paragraph('<font face="OpenSansBold" size="7">' + iss.research.title + "</font>" +
                             '<font face="OpenSansBold" size="7">' + (
                                 "" if not iss.comment else "<br/>" + iss.comment) + "</font>",
                             styleSheet["BodyText"]), '', '', '']
            data.append(tmp)
            style_t = TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
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
                tmp = [Paragraph('&nbsp;&nbsp;&nbsp;&nbsp;<font face="OpenSans" size="7">' + f.title + "</font>",
                                 styleSheet["BodyText"])]
                result = "не завершено"
                ref = {"": ""}
                f_units = f.units
                if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
                    r = Result.objects.filter(issledovaniye=iss, fraction=f).order_by("-pk")[0]
                    ref = r.get_ref()
                    result = r.value
                    f_units = r.get_units()
                if not iss.doc_confirmation and iss.deferred:
                    result = "отложен"
                elif iss.time_save and maxdate != str(dateformat.format(iss.time_save, settings.DATE_FORMAT)):
                    result += "<br/>" + str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                tmp.append(Paragraph('<font face="ChampB" size="8">' + result + "</font>", styleSheet["BodyText"]))
                tmp.append(Paragraph('<font face="OpenSans" size="7">&nbsp;&nbsp;&nbsp;' + f_units + "</font>",
                                     styleSheet["BodyText"]))
                tmp.append(Paragraph('<font face="OpenSans" size="7">' + get_r(ref) + "</font>",
                                     styleSheet["BodyText"]))

                data.append(tmp)

            for k in range(0, 4):
                style_t.add('INNERGRID', (k, 0),
                            (k, j), 0.01, colors.black)
                style_t.add('BOX', (k, 0), (k, j),
                            0.8, colors.black)

            t = Table(data, colWidths=cw)
            t.setStyle(style_t)
        t.canv = c
        wt, ht = t.wrap(0, 0)
        t.drawOn(c, paddingx + s, pos - ht)
        pos = pos - ht
    napr.save()


@login_required
def result_journal_table_print(request):
    import datetime
    dateo = request.GET["date"]
    date = datetime.date(int(dateo.split(".")[2]), int(dateo.split(".")[1]), int(dateo.split(".")[0]))
    end_date = date + datetime.timedelta(days=1)
    onlyjson = False

    ist_f = json.loads(request.GET.get("ist_f", "[]"))
    lab = Podrazdeleniya.objects.get(pk=request.GET.get("lab_pk", request.user.doctorprofile.podrazdeleniye.pk))

    iss_list = Issledovaniya.objects.filter(time_confirmation__gte=date, time_confirmation__lt=end_date,
                                            research__podrazdeleniye=lab,
                                            napravleniye__cancel=False, napravleniye__istochnik_f__pk__in=ist_f)
    patients = {}
    researches_pks = set()
    for iss in iss_list.order_by("napravleniye__client__individual__family").order_by("research__direction_id",
                                                                                      "research__pk",
                                                                                      "tubes__id",
                                                                                      "research__sort_weight"):
        d = iss.napravleniye
        otd = d.doc.podrazdeleniye
        k = "%d_%s" % (otd.pk, iss.napravleniye.istochnik_f.title)
        if k not in patients:
            patients[k] = {"title": otd.title, "ist_f": iss.napravleniye.istochnik_f.title, "patients": {}}
        if d.client.pk not in patients[k]["patients"]:
            patients[k]["patients"][d.client.pk] = {"fio": d.client.individual.fio(short=True, dots=True),
                                                    "card": d.client.number_with_type(),
                                                    "history": d.history_num,
                                                    "researches": {}}
        if iss.research.pk not in patients[k]["patients"][d.client.pk]["researches"]:
            patients[k]["patients"][d.client.pk]["researches"][iss.research.pk] = {"title": iss.research.title,
                                                                                   "fractions": {}}
            # researches_pks.add(iss.research.pk)
        for fr in iss.research.fractions_set.all():
            fres = Result.objects.filter(issledovaniye=iss, fraction=fr)
            if fres.exists():
                fres = fres.first()
                patients[k]["patients"][d.client.pk]["researches"][iss.research.pk]["fractions"][fr.pk] = {
                    "title": fr.title, "result": result_normal(fres.value)}
    if onlyjson:
        return HttpResponse(json.dumps(patients), content_type="application/json")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="table_results.pdf"'

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from django.core.paginator import Paginator
    from reportlab.lib.units import mm
    from io import BytesIO
    import os

    pdfmetrics.registerFont(TTFont('Calibri', os.path.join(FONTS_FOLDER, 'Calibri.ttf')))
    pdfmetrics.registerFont(TTFont('CalibriBold', os.path.join(FONTS_FOLDER, 'calibrib.ttf')))

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

    from reportlab.platypus import Flowable

    def truncate_chars(value, max_length):
        if len(value) > max_length and "</" not in value:
            truncd_val = value[:max_length]
            if not len(value) == max_length + 1 and value[max_length + 1] != " ":
                truncd_val = truncd_val[:truncd_val.rfind(" ")]
            return truncd_val
        return value

    class TTR(Flowable):
        def __init__(self, text, fontname="Calibri", fontsize=9, lenmin=16, domin=False):
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

    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    styleSheet = getSampleStyleSheet()
    styleSheet["BodyText"].wordWrap = 'CJK'
    stl = deepcopy(styleSheet["BodyText"])
    from reportlab.lib.enums import TA_CENTER
    stl.alignment = TA_CENTER

    tw = pw - marginx * 2 - 3 * mm

    max_patients = 13
    style = TableStyle([('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                        ('TOPPADDING', (0, 0), (-1, -1), 0.3),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.4),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                        ('LEFTPADDING', (0, 0), (0, -2), 1.3),
                        ('LEFTPADDING', (1, 0), (-1, -2), 1.3),
                        ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                        ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                        ])
    from collections import OrderedDict

    ordered = {}
    from django.db.models import Q
    for f in directory.Fractions.objects.filter(Q(research__podrazdeleniye=lab, hide=False,
                                                  research__hide=False) | Q(research__podrazdeleniye=lab,
                                                                            hide=False,
                                                                            research__hide=True,
                                                                            research__pk__in=researches_pks)):
        k = (
                9999 if not f.research.direction else f.research.direction.pk) * 1000000 + f.relation.pk * 100000 + f.research.sort_weight * 10000 + f.sort_weight * 100 + f.pk
        d = dict(pk=f.pk, title=f.title)
        ordered[k] = d

    researches_results = OrderedDict(
        [(x[1]['pk'], [x[1]['title']]) for x in sorted(ordered.items(), key=lambda t: t[0])])

    for otd in patients.values():
        p = Paginator(list(otd["patients"].values()), max_patients)
        for pagenum in p.page_range:
            resilts_cp = deepcopy(researches_results)
            c.setFont('Calibri', 10)
            c.rotate(90)
            c.drawString(300, -22,
                         "Журнал: %s - %s за %s (источник - %s)" % (lab.title, otd["title"], dateo, otd["ist_f"]))
            c.rotate(-90)
            c.drawRightString(pxr(marginx / 2), pyb(-1), "Страница %d из %d" % (pagenum, p.num_pages))
            data = []
            tmp2 = [Paragraph('<font face="Calibri" size="8">Исследования<br/><br/><br/><br/><br/><br/><br/></font>',
                              styleSheet["BodyText"])]
            for patient in p.page(pagenum).object_list:
                tmp2.append(TTR("%s\nКарта: %s\n%s" % (patient["fio"], patient["card"],
                                                       "" if not patient["history"] or patient["history"] in ["None",
                                                                                                              ""] else "История: %s" %
                                                                                                                       patient[
                                                                                                                           "history"]),
                                domin=True))
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
                    tmp.append(
                        Paragraph('<font face="Calibri" size="%d">%s</font>' % (s, data_str), styleSheet["BodyText"]))
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
    slog.Log(key="", type=28, body=json.dumps({"date": dateo, "lab": lab.title}),
             user=request.user.doctorprofile).save()

    return response


@login_required
def result_journal_print(request):
    """ Печать журнала подтверждений """
    pw, ph = A4
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="journal.pdf"'
    import datetime
    dateo = request.GET["date"]
    date = datetime.date(int(dateo.split(".")[2]), int(dateo.split(".")[1]), int(dateo.split(".")[0]))
    lab = Podrazdeleniya.objects.get(pk=request.GET.get("lab_pk", request.user.doctorprofile.podrazdeleniye.pk))

    ist_f = json.loads(request.GET.get("ist_f", "[]"))
    group = int(request.GET.get("group", "-2"))

    codes = request.GET.get("codes", "-1") == "1"
    group_to_otd = request.GET.get("group_to_otd", "1") == "1"

    end_date = date + datetime.timedelta(days=1)
    iss_list = Issledovaniya.objects.filter(time_confirmation__gte=date, time_confirmation__lt=end_date,
                                            research__podrazdeleniye=lab,
                                            napravleniye__cancel=False, napravleniye__istochnik_f__pk__in=ist_f)
    group_str = "Все исследования"
    if group != -2:
        if group == -1:
            group_str = "Без группы"
            iss_list = iss_list.filter(research__groups__isnull=True)
        else:
            g = directory.ResearchGroup.objects.get(pk=group)
            group_str = g.title
            iss_list = iss_list.filter(research__groups=g)

    from io import BytesIO
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os.path
    from django.utils.text import Truncator
    from django.utils import timezone
    from reportlab.lib.styles import getSampleStyleSheet
    styles = getSampleStyleSheet()
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.units import mm
    import collections

    pdfmetrics.registerFont(
        TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))
    pdfmetrics.registerFont(
        TTFont('Champ', os.path.join(FONTS_FOLDER, 'Champ.ttf')))
    pdfmetrics.registerFont(
        TTFont('ChampB', os.path.join(FONTS_FOLDER, 'ChampB.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansBold', os.path.join(FONTS_FOLDER, 'OpenSans-Bold.ttf')))
    pdfmetrics.registerFont(
        TTFont('cour', os.path.join(FONTS_FOLDER, 'cour.ttf')))

    buffer = BytesIO()
    elements = []
    doc = SimpleDocTemplate(buffer, rightMargin=5 * mm, leftMargin=20 * mm, topMargin=15 * mm, bottomMargin=17 * mm,
                            pagesize=A4)

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
            self.setFont('OpenSans', 12)
            self.drawCentredString((A4[0] - 25 * mm) / 2 + 20 * mm, ph - 12 * mm,
                                   "%s - %s, %s" % (request.user.doctorprofile.podrazdeleniye.title, group_str, dateo))
            self.saveState()
            if not codes:
                self.setStrokeColorRGB(0, 0, 0)
                self.setLineWidth(0.5)
                self.line(20 * mm, 22, A4[0] - 5 * mm, 22)
            self.setFont('OpenSans', 8)
            self.drawRightString(A4[0] - 8 * mm, 16, "Страница %s из %s" % (self._pageNumber, page_count))
            if codes:
                self.drawCentredString(A4[0] / 2, 16,
                                       "Проверил: ____________________________ (подпись)")
            if codes:
                self.drawString(23 * mm, 16, "Распечатано: " + str(dateformat.format(
                    timezone.now(),
                    settings.DATE_FORMAT)))
                self.drawString(23 * mm, 8, "Распечатал: " + request.user.doctorprofile.get_fio(dots=True))
            else:
                self.drawString(23 * mm, 16, dateo)
            self.restoreState()

    styles["Normal"].fontName = "OpenSans"
    styles["Normal"].fontSize = 12

    from collections import defaultdict
    from reportlab.platypus import PageBreak

    otds = defaultdict(dict)
    clientresults = {}
    for iss in iss_list.order_by("napravleniye__client__individual__family"):
        key = iss.napravleniye.client.individual.family + "-" + str(iss.napravleniye.client.pk)
        if key not in clientresults.keys():
            clientresults[key] = {"directions": {},
                                  "ist_f": iss.napravleniye.istochnik_f.title,
                                  "fio": iss.napravleniye.client.individual.fio(short=True,
                                                                                dots=True) + "<br/>Карта: " + iss.napravleniye.client.number_with_type() +
                                         ((
                                                  "<br/>История: " + iss.napravleniye.history_num) if iss.napravleniye.history_num and iss.napravleniye.history_num != "" else "")}
        if iss.napravleniye.pk not in clientresults[key]["directions"]:
            clientresults[key]["directions"][iss.napravleniye.pk] = {"researches": {}}
        # results = Result.objects.filter(issledovaniye=iss)
        if iss.research.pk not in clientresults[key]["directions"][iss.napravleniye.pk]["researches"]:
            clientresults[key]["directions"][iss.napravleniye.pk]["researches"][iss.research.pk] = {
                "title": iss.research.title, "res": [], "code": iss.research.code, "fail": False}
        # for result in results:
        #    pass
        for fr in iss.research.fractions_set.all():
            fres = Result.objects.filter(issledovaniye=iss, fraction=fr)
            if fres.exists():
                tres = {"value": fr.title + ": " + fres.first().value, "v": fres.first().value, "code": fr.code,
                        "title": fr.title, "fail": False}
                if codes:
                    tmpval = tres["v"].lower().strip()
                    tres["fail"] = not (all([x not in tmpval for x in
                                             ["забор", "тест", "неправ", "ошибк", "ошибочный", "кров", "брак", "мало",
                                              "недостаточно", "реактив"]]) and tmpval != "" and tmpval != "-")
                    if tmpval == "":
                        tres["v"] = "пустой результат"
                    if tres["fail"]:
                        clientresults[key]["directions"][iss.napravleniye.pk]["researches"][iss.research.pk][
                            "fail"] = True
                clientresults[key]["directions"][iss.napravleniye.pk]["researches"][iss.research.pk]["res"].append(tres)
        if not group_to_otd:
            otds[iss.napravleniye.doc.podrazdeleniye.title + " - " + iss.napravleniye.istochnik_f.title][key] = \
                clientresults[key]
        else:
            otds[iss.napravleniye.istochnik_f.title][key] = clientresults[key]
    j = 0
    # clientresults = collections.OrderedDict(sorted(clientresults.items()))
    for otd in otds.keys():
        data = []
        if not codes:
            data = [[Paragraph('<font face="OpenSans" size="12">' + otd + "</font>", styles["Normal"])]]
            data_header = ["№", "ФИО", "Направление: Результаты"]
            tmp = []
            for v in data_header:
                tmp.append(Paragraph(str(v), styles["Normal"]))
            data.append(tmp)
        else:
            data.append([Paragraph("№", styles["Normal"]), Paragraph("Пациент", styles["Normal"]),
                         Paragraph('<font face="cour" size="9">' + "Код".ljust(16, '.') + "исследование" + "</font>",
                                   styles["Normal"])])

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
                            data_tmp += research_obj["title"] + ":" + "; ".join(
                                [x["value"] for x in research_obj["res"]])
                        # data_tmp += ". "
                        data_tmp += "<br/>"
                else:
                    for research_pk in dir["researches"].keys():
                        research_obj = dir["researches"][research_pk]
                        if research_obj["code"] != '':
                            if research_obj["fail"]:
                                for code_res in research_obj["code"].split(";"):
                                    data_tmp += "%s%s%s<br/>" % (Truncator("Ошибка результ").chars(15).ljust(16, '.'),
                                                                 code_res, Truncator(research_obj["title"]).chars(30))
                            else:
                                for code_res in research_obj["code"].split(";"):
                                    data_tmp += "%s%s<br/>" % (
                                        code_res.ljust(16, '.'), Truncator(research_obj["title"]).chars(48))
                        else:
                            for res in research_obj["res"]:
                                if res["fail"]:
                                    for code_res in res["code"].split(";"):
                                        data_tmp += "%s%s%s<br/>" % (Truncator(res["v"]).chars(15).ljust(16, '.'),
                                                                     code_res.ljust(16, '.'),
                                                                     Truncator(res["title"]).chars(32))
                                else:
                                    for code_res in res["code"].split(";"):
                                        data_tmp += "%s%s<br/>" % (
                                            code_res.ljust(16, '.'), Truncator(res["title"]).chars(48))
                                '''data_tmp += "%s%s<br/>" % (
                                    res["code"].ljust(16, '.'), Truncator(res["title"]).chars(48))'''
            j += 1
            if not codes:
                data.append([Paragraph('<font face="OpenSans" size="8">' + str(j) + "</font>", styles["Normal"]),
                             Paragraph('<font face="OpenSans" size="8">' + client["fio"] + "</font>", styles["Normal"]),
                             Paragraph('<font face="ChampB" size="8">' + data_tmp + "</font>", styles["Normal"])])
            else:
                data.append([Paragraph('<font face="OpenSans" size="8">' + str(j) + "</font>", styles["Normal"]),
                             Paragraph('<font face="OpenSans" size="8">' + client["fio"] + "<br/>" + client[
                                 "ist_f"] + "</font>", styles["Normal"]),
                             Paragraph('<font face="cour" size="9">' + data_tmp + "</font>", styles["Normal"])])
        sta = [('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
               ('VALIGN', (0, 0), (-1, -1), 'TOP'),
               ('BOX', (0, 0), (-1, -1), 1, colors.black),
               ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
               ('LEFTPADDING', (0, 0), (-1, -1), 3),
               ('TOPPADDING', (0, 2), (-1, -1), 0),
               ('TOPPADDING', (0, 0), (-1, 1), 2),
               ('BOTTOMPADDING', (0, 0), (-1, 1), 3),
               ('RIGHTPADDING', (0, 0), (-1, -1), 1),
               ('BOTTOMPADDING', (0, 2), (-1, -1), 1), ]
        if not codes:
            sta.append(('SPAN', (0, 0), (-1, 0),))
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
            # t2.append(lr(ttt).replace(" ", "&nbsp;"))
            t2.append(ttt)
        else:
            t2.append(ttt)
    t2.sort()
    s = "<br/>".join(t2)
    if s == " : ":
        s = ""
    return s


@csrf_exempt
@login_required
def result_get(request):
    """ Получение результатов для исследования """
    result = {"results": {}, "norms": {}, "refs": {}, "comment": ""}
    if request.method == "GET":
        issledovaniye = Issledovaniya.objects.get(pk=int(request.GET["iss_id"]))
        results = Result.objects.filter(issledovaniye=issledovaniye)
        for v in results:
            result["results"][str(v.fraction.pk)] = v.value
            result["norms"][str(v.fraction.pk)] = v.get_is_norm(recalc=True)
            result["refs"][str(v.fraction.pk)] = v.get_ref(full=True)
        if issledovaniye.lab_comment:
            result["comment"] = issledovaniye.lab_comment.strip()
    return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
@login_required
def get_day_results(request):
    import datetime
    from datetime import timedelta
    from collections import defaultdict
    if request.method == "POST":
        researches = json.loads(request.POST["researches"])
        day = request.POST["date"]
        otd = request.POST.get("otd", "-1")
    else:
        researches = json.loads(request.GET["researches"])
        day = request.GET["date"]
        otd = request.GET.get("otd", "-1")

    day1 = datetime.date(int(day.split(".")[2]), int(day.split(".")[1]), int(day.split(".")[0]))
    day2 = day1 + timedelta(days=1)
    directions = defaultdict(list)
    otd = int(otd)

    if otd == -1:
        for dir in Napravleniya.objects.filter(issledovaniya__time_confirmation__range=(day1, day2),
                                               issledovaniya__research_id__in=researches).order_by("client__pk"):

            if dir.pk not in directions[dir.doc.podrazdeleniye.title]:
                directions[dir.doc.podrazdeleniye.title].append(dir.pk)
    else:
        for dir in Napravleniya.objects.filter(issledovaniya__time_confirmation__range=(day1, day2),
                                               issledovaniya__research_id__in=researches,
                                               doc__podrazdeleniye__pk=otd).order_by("client__pk"):
            if dir.pk not in directions[dir.doc.podrazdeleniye.title]:
                directions[dir.doc.podrazdeleniye.title].append(dir.pk)

    return HttpResponse(json.dumps({"directions": directions}), content_type="application/json")


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

            iss_list = Issledovaniya.objects.filter(
                research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)
            if dir_pk == "" and status != 3:
                date_start, date_end = try_parse_range(date_start, date_end)
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
    # page = int(data.get("page", "1"))
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
    elif bool(
            re.compile(r'^([a-zA-Zа-яА-ЯёЁ]+)( [a-zA-Zа-яА-ЯёЁ]+)?( [a-zA-Zа-яА-ЯёЁ]+)?( \d{2}\.\d{2}\.\d{4})?$').match(
                query)):
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
        return JsonResponse({"rows": [], "grouping": grouping, "len": 0, "next_offset": 0, "all_rows": 0,
                             "error_message": "Некорректная дата"})
    collection = Napravleniya.objects.filter(issledovaniya__time_confirmation__range=(day1, day2),
                                             issledovaniya__time_confirmation__isnull=False,
                                             client__is_archive=archive)
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
        collection = collection.filter(client__individual__family__istartswith=family,
                                       client__individual__name__istartswith=name,
                                       client__individual__patronymic__istartswith=twoname)
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

    import collections
    rows = collections.OrderedDict()
    n = 0
    directions_pks = []
    if sorting_direction == "up":
        sort_types = {"confirm-date": ("issledovaniya__time_confirmation",),
                      "patient": (
                          "issledovaniya__time_confirmation", "client__individual__family", "client__individual__name",
                          "client__individual__patronymic",)}
    else:
        sort_types = {"confirm-date": ("-issledovaniya__time_confirmation",),
                      "patient": (
                          "-issledovaniya__time_confirmation", "-client__individual__family",
                          "-client__individual__name",
                          "-client__individual__patronymic",)}
    filtered = []
    cnt = 0
    for direction in collection.order_by(*sort_types.get(sorting, ("issledovaniya__time_confirmation",))):
        if direction.pk in directions_pks or not direction.is_all_confirm():
            continue
        datec = str(dateformat.format(direction.issledovaniya_set.filter(time_confirmation__isnull=False).order_by(
            "-time_confirmation").first().time_confirmation.date(), settings.DATE_FORMAT))
        key = "%s_%s@%s" % (datec, direction.client.number, direction.client.base.pk)
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
            rows[key] = {"fio": direction.client.individual.fio(),
                         "birthdate": direction.client.individual.age_s(direction=direction),
                         "sex": direction.client.individual.sex,
                         "cardnum": direction.client.number,
                         "type": direction.client.base.title,
                         "date": datec,
                         "directions_cnt": 0,
                         "directions": [],
                         "is_normal": "none"}
        rows[key]["directions_cnt"] += 1
        researches = []

        row_normal = "none"
        iss_dir = direction.issledovaniya_set.all()
        if len(rq_researches) > 0:
            iss_dir = iss_dir.filter(research__pk__in=rq_researches)

        for r in iss_dir:
            if not r.research.is_paraclinic:
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
        l = direction.issledovaniya_set.first().research.get_podrazdeleniye()
        tmp_dir = {"pk": direction.pk,
                   "laboratory": "Консультации" if not l else l.title,
                   "otd": ("" if not direction.imported_org else direction.imported_org.title) if direction.imported_from_rmis else direction.doc.podrazdeleniye.title,
                   "doc": "" if direction.imported_from_rmis else direction.doc.get_fio(),
                   "researches": researches, "is_normal": row_normal}

        if rows[key]["is_normal"] != "not_normal":
            if rows[key]["is_normal"] == "maybe":
                if row_normal == "not_normal":
                    rows[key]["is_normal"] = row_normal
            else:
                rows[key]["is_normal"] = row_normal
        rows[key]["directions"].append(tmp_dir)
        directions_pks.append(direction.pk)
    if offset == 0:
        slog.Log(key="", type=27, body=json.dumps({"query": query,
                                                   "period": period,
                                                   "type_patient": type_patient,
                                                   "perform_norms": perform_norms,
                                                   "grouping": grouping,
                                                   "otd_search": otd_search,
                                                   "doc_search": doc_search,
                                                   "researches": rq_researches}),
                 user=request.user.doctorprofile).save()

    return JsonResponse(
        {"rows": rows, "grouping": grouping, "len": n - offset, "next_offset": n, "all_rows": cnt, "error_message": ""})
