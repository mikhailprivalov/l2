import base64
import collections
import datetime
import operator
import os.path
import random
import re
from copy import deepcopy
from decimal import Decimal
from io import BytesIO

import bleach
import simplejson as json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils import dateformat
from django.utils import timezone
from django.utils.text import Truncator
from django.views.decorators.csrf import csrf_exempt
from pdfrw import PdfReader, PdfWriter
from reportlab.lib import colors
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
from directions.models import TubesRegistration, Issledovaniya, Result, Napravleniya, ParaclinicResult, Recipe
from laboratory.decorators import group_required, logged_in_or_token
from laboratory.settings import FONTS_FOLDER
from laboratory.utils import strdate, strtime
from podrazdeleniya.models import Podrazdeleniya
from refprocessor.common import RANGE_NOT_IN, RANGE_IN
from utils.dates import try_parse_range, try_strptime
from utils.flowable import InteractiveTextField
from utils.pagenum import PageNumCanvas, PageNumCanvasPartitionAll
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
@group_required("Лечащий врач", "Зав. отделением")
@csrf_exempt
def results_search(request):
    """ Представление для поиска результатов исследований у пациента """
    if request.method == "POST":
        dirs = set()
        result = {"directions": [], "client_id": int(request.POST["client_id"]), "research_id": int(request.POST["research_id"]), "other_dirs": []}
        for r in Result.objects.filter(
            fraction__research_id=result["research_id"], issledovaniye__napravleniye__client_id=result["client_id"], issledovaniye__time_confirmation__isnull=False
        ):
            dirs.add(r.issledovaniye.napravleniye_id)
        for d in Napravleniya.objects.filter(client_id=result["client_id"], issledovaniya__research_id=result["research_id"]):
            tmp_d = {"pk": d.pk}
            if d.pk in dirs:
                tc = Issledovaniya.objects.filter(napravleniye=d).first().time_confirmation
                tmp_d["date"] = "не подтверждено" if tc is None else strdate(tc)
                result["directions"].append(tmp_d)
            else:
                tmp_d["get_material"] = all([x.is_get_material() for x in Issledovaniya.objects.filter(napravleniye=d)])
                tmp_d["is_receive_material"] = all([x.is_receive_material() for x in Issledovaniya.objects.filter(napravleniye=d)])
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

    labs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY).exclude(title="Внешние организации")
    return render(request, 'dashboard/results_search.html', {"labs": labs})


@login_required
@group_required("Врач-лаборант", "Лаборант")
def enter(request):
    """ Представление для страницы ввода результатов """
    # lab = Podrazdeleniya.objects.get(pk=request.GET.get("lab_pk", request.user.doctorprofile.podrazdeleniye_id))
    # labs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY).exclude(title="Внешние организации").order_by("title")
    # if lab.p_type != Podrazdeleniya.LABORATORY:
    #     lab = labs[0]
    # podrazdeleniya = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.DEPARTMENT).order_by("title")
    # return render(
    #     request,
    #     'dashboard/resultsenter.html',
    #     {
    #         "podrazdeleniya": podrazdeleniya,
    #         "ist_f": IstochnikiFinansirovaniya.objects.all().order_by("pk").order_by("base"),
    #         "groups": directory.ResearchGroup.objects.filter(lab=lab),
    #         "lab": lab,
    #         "labs": labs,
    #     },
    # )
    return redirect('/laboratory/results')


@csrf_exempt
@login_required
def loadready(request):
    """ Представление, возвращающее JSON со списками пробирок и направлений, принятых в лабораторию """
    result = {"tubes": [], "directions": []}
    if request.method == "POST":
        date_start = request.POST["datestart"]
        date_end = request.POST["dateend"]
        deff = int(request.POST["def"])
        lab = Podrazdeleniya.objects.get(pk=request.POST.get("lab", request.user.doctorprofile.podrazdeleniye_id))
    else:
        date_start = request.GET["datestart"]
        date_end = request.GET["dateend"]
        deff = int(request.GET["def"])
        lab = Podrazdeleniya.objects.get(pk=request.GET.get("lab", request.user.doctorprofile.podrazdeleniye_id))

    date_start, date_end = try_parse_range(date_start, date_end)
    dates_cache = {}
    tubes = set()
    dirs = set()

    if deff == 0:
        tlist = TubesRegistration.objects.filter(
            doc_recive__isnull=False,
            time_recive__range=(date_start, date_end),
            issledovaniya__time_confirmation__isnull=True,
            issledovaniya__research__podrazdeleniye=lab,
            issledovaniya__isnull=False,
        )
    else:
        tlist = TubesRegistration.objects.filter(
            doc_recive__isnull=False,
            time_get__isnull=False,
            issledovaniya__time_confirmation__isnull=True,
            issledovaniya__research__podrazdeleniye=lab,
            issledovaniya__deferred=True,
            issledovaniya__isnull=False,
        )

    tlist = tlist.filter(Q(issledovaniya__napravleniye__hospital=request.user.doctorprofile.hospital) | Q(issledovaniya__napravleniye__hospital__isnull=True))

    for tube in tlist.prefetch_related('issledovaniya_set__napravleniye'):
        direction = None
        if tube.pk not in tubes:
            if not direction:
                direction = tube.issledovaniya_set.first().napravleniye
            if tube.time_recive.date() not in dates_cache:
                dates_cache[tube.time_recive.date()] = dateformat.format(tube.time_recive, 'd.m.y')
            tubes.add(tube.pk)
            dicttube = {
                "id": tube.pk,
                "direction": direction.pk,
                "date": dates_cache[tube.time_recive.date()],
                "tube": {"title": tube.type.tube.title, "color": tube.type.tube.color},
            }  # Временный словарь с информацией о пробирке
            result["tubes"].append(dicttube)  # Добавление временного словаря к ответу

        if tube.issledovaniya_set.first().napravleniye_id not in dirs:
            if not direction:
                direction = tube.issledovaniya_set.first().napravleniye
            if direction.data_sozdaniya.date() not in dates_cache:
                dates_cache[direction.data_sozdaniya.date()] = dateformat.format(direction.data_sozdaniya, 'd.m.y')
            dirs.add(direction.pk)
            dictdir = {"id": direction.pk, "date": dates_cache[direction.data_sozdaniya.date()]}  # Временный словарь с информацией о направлении
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
        issledovaniye = Issledovaniya.objects.get(pk=int(request.POST["issledovaniye"]))  # Загрузка исследования из запроса и выборка из базы данных
        if issledovaniye:  # Если исследование найдено

            for t in TubesRegistration.objects.filter(issledovaniya=issledovaniye):
                if not t.rstatus():
                    t.set_r(request.user.doctorprofile)

            for key in fractions.keys():  # Перебор фракций из запроса
                created = False
                if Result.objects.filter(issledovaniye=issledovaniye, fraction__pk=key).exists():
                    fraction_result = Result.objects.filter(issledovaniye=issledovaniye, fraction__pk=key).order_by("-pk")[0]
                else:
                    fraction_result = Result(issledovaniye=issledovaniye, fraction_id=key)  # Создание нового результата
                    created = True
                tv = bleach.clean(fractions[key], tags=['sup', 'sub', 'br', 'b', 'i', 'strong', 'a', 'img', 'font', 'p', 'span', 'div']).replace("<br>", "<br/>")  # Установка значения
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

            issledovaniye.time_save = timezone.now()  # Время сохранения
            issledovaniye.lab_comment = request.POST.get("comment", "")
            issledovaniye.co_executor_id = None if request.POST.get("co_executor", '-1') == '-1' else int(request.POST["co_executor"])
            issledovaniye.def_uet = 0
            issledovaniye.co_executor_uet = 0

            if not request.user.doctorprofile.has_group("Врач-лаборант"):
                for r in Result.objects.filter(issledovaniye=issledovaniye):
                    issledovaniye.def_uet += r.fraction.uet_co_executor_1
            else:
                for r in Result.objects.filter(issledovaniye=issledovaniye):
                    issledovaniye.def_uet += r.fraction.uet_doc
                if issledovaniye.co_executor_id:
                    for r in Result.objects.filter(issledovaniye=issledovaniye):
                        issledovaniye.co_executor_uet += r.fraction.uet_co_executor_1

            issledovaniye.co_executor2_id = None if request.POST.get("co_executor2", '-1') == '-1' else int(request.POST["co_executor2"])
            issledovaniye.co_executor2_uet = 0
            if issledovaniye.co_executor2_id:
                for r in Result.objects.filter(issledovaniye=issledovaniye):
                    issledovaniye.co_executor2_uet += r.fraction.uet_co_executor_2
            issledovaniye.save()
            result = {"ok": True}

            slog.Log(key=request.POST["issledovaniye"], type=13, body=request.POST["fractions"], user=request.user.doctorprofile).save()
    return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
@login_required
def result_confirm(request):
    """ Подтверждение результатов """
    result = {"ok": False}
    if request.method == "POST":
        issledovaniye = Issledovaniya.objects.get(pk=int(request.POST["pk"]))
        if issledovaniye.doc_save:  # Если исследование сохранено
            issledovaniye.doc_confirmation = request.user.doctorprofile  # Кто подтвердил
            for r in Result.objects.filter(issledovaniye=issledovaniye):
                r.get_ref()
            issledovaniye.time_confirmation = timezone.now()  # Время подтверждения
            issledovaniye.save()
            slog.Log(key=request.POST["pk"], type=14, body=json.dumps({"dir": issledovaniye.napravleniye_id}), user=request.user.doctorprofile).save()

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
            if issledovaniye.doc_save and not issledovaniye.time_confirmation:  # Если исследование сохранено
                for r in Result.objects.filter(issledovaniye=issledovaniye):
                    r.get_ref()
                issledovaniye.doc_confirmation = request.user.doctorprofile  # Кто подтвердил
                issledovaniye.time_confirmation = timezone.now()  # Время подтверждения
                if not request.user.doctorprofile.has_group("Врач-лаборант"):
                    issledovaniye.co_executor = request.user.doctorprofile
                    for r in Result.objects.filter(issledovaniye=issledovaniye):
                        issledovaniye.def_uet += Decimal(r.fraction.uet_co_executor_1)
                issledovaniye.save()
                slog.Log(key=pk, type=14, body="", user=request.user.doctorprofile).save()
        result["ok"] = True
    return HttpResponse(json.dumps(result), content_type="application/json")


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

    pk = [x for x in json.loads(request.GET["pk"]) if x is not None]

    show_norm = True  # request.GET.get("show_norm", "0") == "1"

    buffer = BytesIO()

    split = request.GET.get("split", "1") == "1"
    protocol_plain_text = request.GET.get("protocol_plain_text", "0") == "1"
    leftnone = request.GET.get("leftnone", "0") == "0"
    hosp = request.GET.get("hosp", "0") == "1"

    doc = BaseDocTemplate(
        buffer,
        leftMargin=(27 if leftnone else 15) * mm,
        rightMargin=12 * mm,
        topMargin=5 * mm,
        bottomMargin=16 * mm,
        allowSplitting=1,
        _pageBreakQuick=1,
        title="Результаты для направлений {}".format(", ".join([str(x) for x in pk])),
        invariant=1
    )
    p_frame = Frame(
        0 * mm, 0 * mm, 210 * mm, 297 * mm, leftPadding=(27 if leftnone else 15) * mm, rightPadding=15 * mm, topPadding=5 * mm, bottomPadding=16 * mm, id='portrait_frame', showBoundary=0
    )
    l_frame = Frame(
        0 * mm, 0 * mm, 297 * mm, 210 * mm, leftPadding=10 * mm, rightPadding=15 * mm, topPadding=(27 if leftnone else 15) * mm, bottomPadding=16 * mm, id='landscape_frame', showBoundary=0
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
                'Результат из <font face="OpenSansBoldItalic">L²</font>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;%s<br/><br/>%s<br/>%s<br/>%s'
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

    count_direction = 0
    previous_size_form = None
    is_page_template_set = False

    def mark_pages(canvas_mark, direction: Napravleniya):
        canvas_mark.saveState()
        canvas_mark.setFont('FreeSansBold', 8)
        if direction.hospital:
            canvas_mark.drawString(55 * mm, 13 * mm, direction.hospital.title)
        else:
            canvas_mark.drawString(55 * mm, 13 * mm, '{}'.format(SettingManager.get("org_title")))
        if direction.is_external:
            canvas_mark.drawString(55 * mm, 9.6 * mm, f'№ карты : {direction.client.number_with_type()}; Номер в организации: {direction.id_in_hospital}; Направление № {direction.pk}')
        else:
            canvas_mark.drawString(55 * mm, 9.6 * mm, '№ карты : {}; Номер: {} {}; Направление № {}'.format(direction.client.number_with_type(), num_card, number_poliklinika, direction.pk))
        canvas_mark.drawString(55 * mm, 7.1 * mm, 'Пациент: {} {}'.format(direction.client.individual.fio(), individual_birthday))
        canvas_mark.line(55 * mm, 12.7 * mm, 181 * mm, 11.5 * mm)
        canvas_mark.restoreState()

    count_pages = 0
    has_page_break = False

    for direction in sorted(dirs, key=lambda dir: dir.client.individual_id * 100000000 + dir.results_count * 10000000 + dir.pk):
        dpk = direction.pk

        if not direction.is_all_confirm():
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
            ):
                has_paraclinic = True
            if directory.HospitalService.objects.filter(slave_research=iss.research).exists():
                has_paraclinic = True
            if iss.link_file:
                link_result.append(iss.link_file)
                link_files = True
            if 'выпис' in iss.research.title.lower():
                is_extract = True
            if iss.research.is_gistology:
                is_gistology = True
            if iss.research.has_own_form_result:
                has_own_form_result = True

            current_size_form = iss.research.size_form
            temp_iss = iss

        def local_mark_pages(c, _):
            if not has_own_form_result:
                mark_pages(c, direction)

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
        if not hosp and not is_gistology and not has_own_form_result or is_extract:
            t = default_title_result_form(direction, doc, date_t, has_paraclinic, individual_birthday, number_poliklinika, logo_col, is_extract)
            fwb.append(t)
            fwb.append(Spacer(1, 5 * mm))
        if not has_paraclinic:
            fwb.append(Spacer(1, 4 * mm))
            fwb.append(InteractiveTextField())
            tw = pw
            no_units_and_ref = any([x.research.no_units_and_ref for x in direction.issledovaniya_set.all()])
            data = []
            tmp = [
                Paragraph('<font face="FreeSansBold" size="8">Исследование</font>', styleSheet["BodyText"]),
                Paragraph('<font face="FreeSansBold" size="8">Результат</font>', styleSheet["BodyText"]),
            ]
            if not no_units_and_ref:
                if direction.client.individual.sex.lower() == "м":
                    tmp.append(Paragraph('<font face="FreeSansBold" size="8">Референсные значения (М)</font>', styleSheet["BodyText"]))
                else:
                    tmp.append(Paragraph('<font face="FreeSansBold" size="8">Референсные значения (Ж)</font>', styleSheet["BodyText"]))
                tmp.append(Paragraph('<font face="FreeSansBold" size="8">Единицы<br/>измерения</font>', styleSheet["BodyText"]))

            tmp.append(Paragraph('<font face="FreeSansBold" size="8">Исполнитель</font>', styleSheet["BodyText"]))
            tmp.append(Paragraph('<font face="FreeSansBold" size="8">Дата</font>', styleSheet["BodyText"]))
            data.append(tmp)
            if no_units_and_ref:
                cw = [int(tw * 0.26), int(tw * 0.482), int(tw * 0.178)]
            else:
                cw = [int(tw * 0.26), int(tw * 0.178), int(tw * 0.17), int(tw * 0.134), int(tw * 0.178)]
            cw = cw + [tw - sum(cw)]
            t = Table(data, repeatRows=1, colWidths=cw)
            style_t = TableStyle(
                [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                    ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                    ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                ]
            )
            style_t.add('BOTTOMPADDING', (0, 0), (-1, 0), 1)
            style_t.add('TOPPADDING', (0, 0), (-1, 0), 0)

            t.setStyle(style_t)
            t.spaceBefore = 3 * mm
            t.spaceAfter = 0

            prev_conf = ""
            prev_date_conf = ""

            has0 = directory.Fractions.objects.filter(research__pk__in=[x.research_id for x in direction.issledovaniya_set.all()], hide=False, render_type=0).exists()

            if has0:
                fwb.append(t)

            iss_list = direction.issledovaniya_set.all()
            result_style = styleSheet["BodyText"] if no_units_and_ref else stl
            pks = []
            for iss in iss_list.order_by("research__direction_id", "research__pk", "tubes__id", "research__sort_weight"):
                if iss.pk in pks:
                    continue
                pks.append(iss.pk)
                data = []
                fractions = directory.Fractions.objects.filter(research=iss.research, hide=False, render_type=0).order_by("pk").order_by("sort_weight")

                if fractions.count() > 0:
                    if fractions.count() == 1:
                        tmp = [Paragraph('<font face="FreeSans" size="8">' + iss.research.title + "</font>", styleSheet["BodyText"])]
                        norm = "none"
                        sign = RANGE_IN
                        if Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).exists():
                            r = Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).order_by("-pk")[0]
                            ref = r.get_ref()
                            if show_norm:
                                norm, sign, ref_res = r.get_is_norm(recalc=True, with_ref=True)
                                ref = ref_res or ref
                            result = result_normal(r.value)
                            f_units = r.get_units()
                        else:
                            continue
                        if not iss.time_confirmation and iss.deferred:
                            result = "отложен"
                        f = fractions[0]
                        st = TableStyle(
                            [
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                ('TOPPADDING', (0, 0), (-1, -1), 3),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), -1),
                            ]
                        )

                        if f.render_type == 0:
                            if norm in ["none", "normal"]:
                                tmp.append(Paragraph('<font face="FreeSans" size="8">' + result + "</font>", result_style))
                            elif norm == "maybe":
                                tmp.append(Paragraph('<font face="FreeSansBold" size="8">' + result + "</font>", result_style))
                            else:
                                tmp.append(Paragraph('<font face="FreeSansBold" size="8">' + result + RANGE_NOT_IN.get(sign, "") + "</font>", result_style))
                            if not no_units_and_ref:
                                tmp.append(Paragraph('<font face="FreeSans" size="7">' + get_r(ref) + "</font>", stl))
                                tmp.append(Paragraph('<font face="FreeSans" size="7">' + f_units + "</font>", stl))

                            if iss.doc_confirmation_fio:
                                if prev_conf != iss.doc_confirmation_fio:
                                    prev_conf = iss.doc_confirmation_fio
                                    prev_date_conf = ""
                                    tmp.append(Paragraph('<font face="FreeSans" size="7">%s</font>' % prev_conf, styleSheet["BodyText"]))
                                else:
                                    tmp.append("")
                                if prev_date_conf != strdate(iss.time_confirmation, short_year=True):
                                    prev_date_conf = strdate(iss.time_confirmation, short_year=True)
                                    tmp.append(Paragraph('<font face="FreeSans" size="7">%s</font>' % prev_date_conf, styleSheet["BodyText"]))
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

                            if iss.doc_confirmation_fio:
                                tmp.append(Paragraph('<font face="FreeSansBold" size="7">%s</font>' % iss.doc_confirmation_fio, styleSheet["BodyText"]))
                                tmp.append(
                                    Paragraph(
                                        '<font face="FreeSansBold" size="7">%s</font>'
                                        % ("" if not iss.tubes.exists() or not iss.tubes.first().time_get else strdate(iss.tubes.first().time_get)),
                                        styleSheet["BodyText"],
                                    )
                                )
                                tmp.append(Paragraph('<font face="FreeSansBold" size="7">%s</font>' % strdate(iss.time_confirmation), styleSheet["BodyText"]))
                            else:
                                tmp.append("")
                                tmp.append(Paragraph('<font face="FreeSansBold" size="7">%s</font>' % strdate(iss.tubes.first().time_get), styleSheet["BodyText"]))
                                tmp.append("")
                            data.append(tmp)

                            j = print_vtype(data, f, iss, 1, st, styleSheet)
                            data.append([Paragraph('<font face="FreeSans" size="8">S - чувствителен; R - резистентен; I - промежуточная чувствительность;</font>', styleSheet["BodyText"])])
                            st.add('SPAN', (0, j), (-1, j))
                            st.add('BOX', (0, j), (-1, j), 1, colors.white)
                            st.add('BOX', (0, j - 1), (-1, j - 1), 1, colors.black)

                        t = Table(data, colWidths=cw)
                        t.setStyle(st)
                        t.spaceBefore = 0
                    else:
                        tmp = [
                            Paragraph(
                                '<font face="FreeSansBold" size="8">'
                                + iss.research.title
                                + '</font>'
                                + ("" if iss.comment == "" or True else '<font face="FreeSans" size="8"><br/>Материал - ' + iss.comment + '</font>'),
                                styleSheet["BodyText"],
                            ),
                            '',
                        ]
                        if not no_units_and_ref:
                            tmp.append("")
                            tmp.append("")

                        if iss.doc_confirmation_fio:
                            if prev_conf != iss.doc_confirmation_fio:
                                prev_conf = iss.doc_confirmation_fio
                                prev_date_conf = ""
                                tmp.append(Paragraph('<font face="FreeSans" size="7">%s</font>' % prev_conf, styleSheet["BodyText"]))
                            else:
                                tmp.append("")
                            if prev_date_conf != strdate(iss.time_confirmation, short_year=True) + '<br/>' + strtime(iss.time_confirmation)[0:5]:
                                prev_date_conf = strdate(iss.time_confirmation, short_year=True) + '<br/>' + strtime(iss.time_confirmation)[0:5]
                                tmp.append(Paragraph('<font face="FreeSans" size="7">%s</font>' % prev_date_conf, styleSheet["BodyText"]))
                            else:
                                tmp.append("")
                        else:
                            tmp.append("")
                            tmp.append("")

                        data.append(tmp)
                        ts = [
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
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
                                tmp.append(Paragraph('<font face="FreeSans" size="8">' + f.title + "</font>", styleSheet["BodyText"]))

                                norm = "none"
                                sign = RANGE_IN
                                if Result.objects.filter(issledovaniye=iss, fraction=f).exists() and not f.print_title:
                                    r = Result.objects.filter(issledovaniye=iss, fraction=f).order_by("-pk")[0]
                                    ref = r.get_ref()
                                    if show_norm:
                                        norm, sign, ref_res = r.get_is_norm(recalc=True, with_ref=True)
                                        ref = ref_res or ref
                                    result = result_normal(r.value)
                                    f_units = r.get_units()
                                elif f.print_title:
                                    tmp[0] = Paragraph('<font face="FreeSansBold" size="10">{}</font>'.format(f.title), styleSheet["BodyText"])
                                    data.append(tmp)
                                    continue
                                else:
                                    continue
                                if not iss.doc_confirmation and iss.deferred:
                                    result = "отложен"
                                if norm in ["none", "normal"]:
                                    tmp.append(Paragraph('<font face="FreeSans" size="8">' + result + "</font>", result_style))
                                elif norm == "maybe":
                                    tmp.append(Paragraph('<font face="FreeSansBold" size="8">' + result + "</font>", result_style))
                                else:
                                    tmp.append(Paragraph('<font face="FreeSansBold" size="8">' + result + RANGE_NOT_IN.get(sign, "") + "</font>", result_style))
                                if not no_units_and_ref:
                                    tmp.append(Paragraph('<font face="FreeSans" size="7">' + get_r(ref) + "</font>", stl))
                                    tmp.append(Paragraph('<font face="FreeSans" size="7">' + f_units + "</font>", stl))
                                tmp.append("")
                                tmp.append("")
                                data.append(tmp)
                            elif f.render_type == 1:
                                jp = j
                                j = print_vtype(data, f, iss, j, style_t, styleSheet)

                                if j - jp > 2:
                                    data.append(
                                        [Paragraph('<font face="FreeSans" size="8">S - чувствителен; R - резистентен; I - промежуточная чувствительность;</font>', styleSheet["BodyText"])]
                                    )
                                    style_t.add('SPAN', (0, j), (-1, j))
                                    style_t.add('BOX', (0, j), (-1, j), 1, colors.white)
                                    j -= 1

                        for k in range(0, 6):
                            style_t.add('INNERGRID', (k, 0), (k, j), 0.1, colors.black)
                            style_t.add('BOX', (k, 0), (k, j), 0.8, colors.black)
                            style_t.add('BOTTOMPADDING', (0, 0), (0, -1), 0)
                            style_t.add('TOPPADDING', (0, 0), (0, -1), 0)

                        t = Table(data, colWidths=cw)
                        t.setStyle(style_t)
                    fwb.append(t)

                fractions = directory.Fractions.objects.filter(research=iss.research, hide=False, render_type=1).order_by("pk").order_by("sort_weight")
                if fractions.count() > 0:
                    data = []
                    if not has0:
                        tmp = [
                            Paragraph('<font face="FreeSansBold" size="8">Исследование</font>', styleSheet["BodyText"]),
                            Paragraph('<font face="FreeSansBold" size="8">Дата сбора материала</font>', styleSheet["BodyText"]),
                            Paragraph('<font face="FreeSansBold" size="8">Дата исполнения</font>', styleSheet["BodyText"]),
                            Paragraph('<font face="FreeSansBold" size="8">Исполнитель</font>', styleSheet["BodyText"]),
                        ]
                        data.append(tmp)

                        tmp = [
                            Paragraph('<font face="FreeSansBold" size="8">%s</font>' % iss.research.title, styleSheet["BodyText"]),
                            Paragraph(
                                '<font face="FreeSans" size="8">%s%s</font>'
                                % ("" if not iss.tubes.exists() or not iss.tubes.first().time_get else strdate(iss.tubes.first().time_get), "" if not iss.comment else "<br/>" + iss.comment),
                                styleSheet["BodyText"],
                            ),
                            Paragraph(
                                '<font face="FreeSans" size="8">%s</font>' % ("Не подтверждено" if not iss.time_confirmation else strdate(iss.time_confirmation)), styleSheet["BodyText"]
                            ),
                            Paragraph('<font face="FreeSans" size="8">%s</font>' % (iss.doc_confirmation_fio or "Не подтверждено"), styleSheet["BodyText"]),
                        ]
                        data.append(tmp)

                        cw = [int(tw * 0.34), int(tw * 0.24), int(tw * 0.2)]
                        cw = cw + [tw - sum(cw)]
                        t = Table(data, colWidths=cw)
                        style_t = TableStyle(
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
                                            norm_vals.insert(0, {"title": rowv["title"], "value": rowv["value"], "k": int(rowk)})
                                    tmp = [
                                        Paragraph(
                                            '<font face="FreeSansBold" size="8">' + (val["title"] if len(norm_vals) == 0 else "Выделенная культура: " + val["title"]) + "</font>",
                                            styleSheet["BodyText"],
                                        ),
                                        "",
                                        "",
                                        "",
                                        "",
                                        "",
                                    ]
                                    data.append(tmp)

                                    if len(norm_vals) > 0:
                                        has_anti = True

                                        tmp = [Paragraph('<font face="FreeSansBold" size="8">%s</font>' % f.title, styleSheet["BodyText"]), "", "", "", "", ""]
                                        data.append(tmp)
                                        j += 1

                                        li = 0
                                        norm_vals.sort(key=operator.itemgetter('k'))
                                        for idx, rowv in enumerate(norm_vals):
                                            li = idx
                                            if li % 3 == 0:
                                                tmp = []

                                            tmp.append(Paragraph('<font face="FreeSans" size="8">' + rowv["title"] + "</font>", styleSheet["BodyText"]))
                                            tmp.append(Paragraph('<font face="FreeSans" size="8">' + rowv["value"] + "</font>", styleSheet["BodyText"]))
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
                                    cw = [int(tw * 0.28), int(tw * 0.06), int(tw * 0.27), int(tw * 0.06), int(tw * 0.27)]
                                    cw = cw + [tw - sum(cw)]
                                    t = Table(data, colWidths=cw)

                                    style_t = TableStyle(
                                        [
                                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                            ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                            ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                            ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                            ('TOPPADDING', (0, 0), (-1, -1), 2),
                                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                            ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                                        ]
                                    )

                                    style_t.add('BOTTOMPADDING', (0, 0), (-1, -1), 1)
                                    style_t.add('TOPPADDING', (0, 0), (-1, -1), 2)

                                    style_t.add('SPAN', (0, 0), (-1, 0))
                                    style_t.add('SPAN', (0, 1), (-1, 1))

                                    t.setStyle(style_t)
                                    fwb.append(t)
                    if has_anti:
                        data = []
                        tmp = [
                            [Paragraph('<font face="FreeSans" size="8">S - чувствителен; R - резистентен; I - промежуточная чувствительность;</font>', styleSheet["BodyText"])],
                            "",
                            "",
                            "",
                            "",
                            "",
                        ]
                        data.append(tmp)
                        cw = [int(tw * 0.23), int(tw * 0.11), int(tw * 0.22), int(tw * 0.11), int(tw * 0.22)]
                        cw = cw + [tw - sum(cw)]
                        t = Table(data, colWidths=cw)
                        style_t = TableStyle(
                            [
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                ('TOPPADDING', (0, 0), (-1, -1), 2),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                            ]
                        )
                        style_t.add('BOTTOMPADDING', (0, 0), (-1, 0), 1)
                        style_t.add('TOPPADDING', (0, 0), (-1, 0), 0)
                        style_t.add('SPAN', (0, 0), (-1, 0))

                        t.setStyle(style_t)
                        fwb.append(t)
                if iss.lab_comment and iss.lab_comment != "":
                    data = []
                    tmp = [
                        [Paragraph('<font face="FreeSans" size="8">Комментарий</font>', styleSheet["BodyText"])],
                        [Paragraph('<font face="FreeSans" size="8">%s</font>' % (iss.lab_comment.replace("\n", "<br/>")), styleSheet["BodyText"])],
                        "",
                        "",
                        "",
                        "",
                    ]
                    data.append(tmp)
                    cw = [int(tw * 0.26), int(tw * 0.178), int(tw * 0.17), int(tw * 0.134), int(tw * 0.178)]
                    cw = cw + [tw - sum(cw)]
                    t = Table(data, colWidths=cw)
                    style_t = TableStyle(
                        [
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                            ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                            ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                            ('LEFTPADDING', (0, 0), (-1, -1), 4),
                            ('TOPPADDING', (0, 0), (-1, -1), 2),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                        ]
                    )
                    style_t.add('BOTTOMPADDING', (0, 0), (-1, 0), 1)
                    style_t.add('TOPPADDING', (0, 0), (-1, 0), 0)
                    style_t.add('SPAN', (1, 0), (-1, 0))

                    t.setStyle(style_t)
                    fwb.append(t)
        else:
            iss: Issledovaniya
            for iss in direction.issledovaniya_set.all().order_by("research__pk"):
                fwb.append(Spacer(1, 5 * mm))
                if not hosp and not is_gistology and not has_own_form_result:
                    fwb.append(InteractiveTextField())
                    fwb.append(Spacer(1, 2 * mm))
                    if (
                        iss.research.is_doc_refferal
                        or iss.research.is_microbiology
                        or iss.research.is_treatment
                        or iss.research.is_microbiology
                        or iss.research.is_citology
                        or iss.research.is_gistology
                    ):
                        iss_title = iss.research.title
                    elif iss.doc_confirmation and iss.doc_confirmation.podrazdeleniye.vaccine:
                        iss_title = "Вакцина: " + iss.research.title
                    else:
                        iss_title = "Услуга: " + iss.research.title
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
                    fwb = form_result(direction, iss, fwb, doc, leftnone, request.user)
                elif not protocol_plain_text:
                    fwb = structure_data_for_result(iss, fwb, doc, leftnone)
                else:
                    fwb = plaint_tex_for_result(iss, fwb, doc, leftnone, protocol_plain_text)

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
                    # Найти все направления где данное исследование родитель
                    napr_child = Napravleniya.objects.filter(parent_slave_hosp=iss, cancel=False)
                    br = ""
                    if not protocol_plain_text:
                        br = '<br/>'
                    if napr_child:
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

                fwb.append(Spacer(1, 3 * mm))
                if not hosp and not iss.research.is_slave_hospital and not iss.research.has_own_form_result:
                    if iss.research.is_doc_refferal:
                        fwb.append(Paragraph("Дата осмотра: {}".format(strdate(iss.get_medical_examination())), styleBold))
                    else:
                        if not is_gistology:
                            fwb.append(Paragraph("Дата оказания услуги: {}".format(t1), styleBold))
                    fwb.append(Paragraph("Дата формирования протокола: {}".format(t2), styleBold))

                if not iss.research.has_own_form_result:
                    if iss.doc_confirmation and iss.doc_confirmation.podrazdeleniye.vaccine:
                        fwb.append(Paragraph("Исполнитель: {}, {}".format(iss.doc_confirmation.fio, iss.doc_confirmation.podrazdeleniye.title), styleBold))
                    else:
                        if iss.doc_confirmation:
                            doc_execute = "фельдшер" if request.user.is_authenticated and request.user.doctorprofile.has_group("Фельдшер") else "врач"
                            fwb.append(Paragraph("Исполнитель: {} {}, {}".format(doc_execute, iss.doc_confirmation.fio, iss.doc_confirmation.podrazdeleniye.title), styleBold))
                        else:
                            fwb.append(
                                Paragraph("Исполнитель: {}, {}".format(iss.doc_confirmation_string, iss.napravleniye.hospital.short_title or iss.napravleniye.hospital.title), styleBold)
                            )

                        if iss.research.is_doc_refferal and SettingManager.get("agree_diagnos", default='True', default_type='b'):
                            fwb.append(Spacer(1, 3.5 * mm))
                            fwb.append(Paragraph("С диагнозом, планом обследования и лечения ознакомлен и согласен _________________________", style))

                        fwb.append(Spacer(1, 2.5 * mm))

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
    elif has_page_break:
        doc.build(naprs, canvasmaker=PageNumCanvasPartitionAll)
    elif fwb:
        doc.build(naprs)

    if len(link_result) > 0:
        date_now1 = datetime.datetime.strftime(datetime.datetime.now(), "%y%m%d%H%M%S")
        date_now_str = str(random.random()) + str(date_now1)
        dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
        file_dir_l2 = os.path.join(dir_param, date_now_str + '_dir.pdf')
        buffer.seek(0)
        save(buffer, filename=file_dir_l2)
        dst_dir = SettingManager.get("root_dir")
        file_dir = [os.path.join(dst_dir, link_f) for link_f in link_result]
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
        os.remove(file_dir_l2)
        return response

    pdf = buffer.getvalue()
    buffer.close()
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
    for iss in iss_list.order_by("napravleniye__client__individual__family").order_by("research__direction_id", "research__pk", "tubes__id", "research__sort_weight"):
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
    """ Печать журнала подтверждений """
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
    """ Получение результатов для исследования """
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
def result_filter(request):
    """ Фильтрация списка исследований """
    result = {"ok": False}
    if request.method == "POST":
        research_pk = request.POST["research"]  # ID исследования
        status = int(request.POST["status"])  # Статус
        dir_pk = request.POST["dir_id"]  # Номер направления
        date_start = request.POST["date[start]"]  # Начальная дата
        date_end = request.POST["date[end]"]  # Конечная дата
        if research_pk.isnumeric() or research_pk == "-1":

            iss_list = Issledovaniya.objects.filter(research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)
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
                    if Issledovaniya.objects.filter(napravleniye=v.napravleniye, time_confirmation__isnull=True).exists():
                        iss_list = iss_list.exclude(napravleniye=v.napravleniye)
            elif dir_pk.isnumeric():
                iss_list = iss_list.filter(napravleniye__pk=int(dir_pk))

            result["list"] = {}
            for v in iss_list:
                status_v = 0
                if v.doc_save and not v.time_confirmation:
                    status_v = 1
                elif v.doc_save and v.time_confirmation and v.napravleniye.doc_print:
                    status_v = 2
                elif v.doc_save and v.time_confirmation and not v.napravleniye.doc_print:
                    status_v = 3
                if v.pk in result["list"].keys() or (status != status_v and not dir_pk.isnumeric()):
                    continue
                if dir_pk.isnumeric():
                    status = status_v
                res = {
                    "status": status_v,
                    "pk": v.pk,
                    "title": v.research.title,
                    "date": "",
                    "direction": v.napravleniye_id,
                    "tubes": " | ".join(map(str, v.tubes.values_list('pk', flat=True))),
                }
                if status == 0 and v.tubes.filter(time_recive__isnull=False).exists():  # Не обработаные
                    res["date"] = str(dateformat.format(v.tubes.filter(time_recive__isnull=False).order_by("-time_recive").first().time_recive.date(), settings.DATE_FORMAT))
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
