import collections
from copy import deepcopy

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
from reportlab.platypus import PageBreak

import directory.models as directory
import slog.models as slog
import users.models as users
from appconf.manager import SettingManager
from clients.models import CardBase, Card
from directions.models import TubesRegistration, Issledovaniya, Result, Napravleniya, IstochnikiFinansirovaniya
from laboratory.decorators import group_required
from laboratory.settings import FONTS_FOLDER
from podrazdeleniya.models import Podrazdeleniya


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
                tmp_d["date"] = "не подтверждено" if tc is None else tc.strftime('%d.%m.%Y')
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
                tmp_d["date"] = d.data_sozdaniya.strftime('%d.%m.%Y')
                result["other_dirs"].append(tmp_d)
        return HttpResponse(json.dumps(result), content_type="application/json")

    from podrazdeleniya.models import Podrazdeleniya
    labs = Podrazdeleniya.objects.filter(isLab=True)
    return render(request, 'dashboard/results_search.html', {"labs": labs})


@login_required
@group_required("Врач-лаборант", "Лаборант")
def enter(request):
    """ Представление для страницы ввода результатов """
    from podrazdeleniya.models import Podrazdeleniya
    lab = Podrazdeleniya.objects.get(pk=request.GET.get("lab_pk", request.user.doctorprofile.podrazdeleniye.pk))
    labs = Podrazdeleniya.objects.filter(isLab=True, hide=False).order_by("title")
    if not lab.isLab:
        lab = labs[0]
    podrazdeleniya = Podrazdeleniya.objects.filter(isLab=False, hide=False).order_by("title")
    return render(request, 'dashboard/resultsenter.html', {"podrazdeleniya": podrazdeleniya,
                                                           "ist_f": IstochnikiFinansirovaniya.objects.all().order_by("pk").order_by("base"),
                                                           "groups": directory.ResearchGroup.objects.filter(lab=lab),
                                                           "lab": lab,
                                                           "labs": labs})


@login_required
@group_required("Врач-лаборант", "Лаборант")
def result_conformation(request):
    """ Представление для страницы подтверждения и печати результатов """
    if "Зав. Лаб." in request.user.groups.values_list('name', flat=True):  # Если пользователь "Зав.Лаб."
        labs = users.Podrazdeleniya.objects.filter(isLab=True)  # Загрузка всех подразделений
    else:
        labs = [request.user.doctorprofile.podrazdeleniye, request.user.doctorprofile.podrazdeleniye]
    researches = directory.Researches.objects.filter(podrazdeleniye=request.user.doctorprofile.podrazdeleniye)  # Загрузка списка анализов
    return render(request, 'dashboard/conformation.html', {"researches": researches, "labs": labs})


import datetime


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

    date_start = datetime.date(int(date_start.split(".")[2]), int(date_start.split(".")[1]),
                               int(date_start.split(".")[0]))
    date_end = datetime.date(int(date_end.split(".")[2]), int(date_end.split(".")[1]),
                             int(date_end.split(".")[0])) + datetime.timedelta(1)
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
                fraction_result.value = bleach.clean(fractions[key], tags=['sup', 'sub', 'br', 'b', 'i', 'strong', 'a', 'img', 'font', 'p', 'span', 'div']).replace("<br>", "<br/>")  # Установка значения
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
                    fraction_result.save()
                    fraction_result.get_ref(re_save=True)
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
            from statistic.models import Uet
            from directions.models import Result
            for r in Result.objects.filter(issledovaniye=issledovaniye):
                r.get_ref()
            issledovaniye.time_confirmation = timezone.now()  # Время подтверждения
            issledovaniye.save()
            slog.Log(key=request.POST["pk"], type=14, body="", user=request.user.doctorprofile).save()
            Uet.add(request.user.doctorprofile, issledovaniye.research, issledovaniye.napravleniye.pk)

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
def get_full_result(request):
    """ Получение результатов для направления """
    result = {"ok": False}
    if request.method == "GET":
        pk = int(request.GET["pk"])  # ID направления
        napr = Napravleniya.objects.get(pk=pk)  # Выборка направления из базы
        dates = {}
        for iss in Issledovaniya.objects.filter(napravleniye=napr, time_save__isnull=False):
            if iss.time_save:
                dt = str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                if dt not in dates.keys():
                    dates[dt] = 0
                dates[dt] += 1

        import operator
        maxdate = ""
        if dates != {}:
            maxdate = max(dates.items(), key=operator.itemgetter(1))[0]

        iss_list = Issledovaniya.objects.filter(napravleniye=napr)  # Выборка списка исследований из базы по направлению
        kint = 0
        t = 0
        if not iss_list.filter(doc_confirmation__isnull=True).exists() or iss_list.filter(
                deferred=False).exists():  # Если для направления все исследования подтверждены

            result["direction"] = {}  # Направление
            result["direction"]["pk"] = napr.pk  # ID
            result["direction"]["doc"] = ""
            result["full"] = False
            if iss_list.filter(doc_confirmation__isnull=False).exists():
                result["direction"]["doc"] = iss_list.filter(doc_confirmation__isnull=False)[
                    0].doc_confirmation.get_fio()  # ФИО подтвердившего
                if iss_list.filter(doc_confirmation__isnull=True, deferred=False).exists():
                    result["direction"]["doc"] = result["direction"]["doc"] + " (выполнено не полностью)"
                else:
                    result["full"] = True
            else:
                result["direction"]["doc"] = "Не подтверждено"
            result["direction"]["date"] = maxdate  # Дата подтверждения

            result["client"] = {}  # Пациент
            result["client"]["sex"] = napr.client.individual.sex  # Пол
            result["client"]["fio"] = napr.client.individual.fio()  # ФИО
            result["client"]["age"] = napr.client.individual.age_s(direction=napr)  # Возраст
            result["client"]["cardnum"] = napr.client.number_with_type()  # Номер карты
            result["client"]["dr"] = napr.client.individual.bd()  # Дата рождения

            result["results"] = collections.OrderedDict()  # Результаты
            isses = []
            for issledovaniye in iss_list.order_by("tubes__id", "research__sort_weight"):  # Перебор списка исследований
                if issledovaniye.pk in isses:
                    continue
                isses.append(issledovaniye.pk)
                t += 1
                kint = "%s_%s_%s_%s" % (t,
                                        "-1" if not issledovaniye.research.direction else issledovaniye.research.direction.pk,
                                        issledovaniye.research.sort_weight,
                                        issledovaniye.research.pk)
                result["results"][kint] = {"title": issledovaniye.research.title,
                                           "fractions": collections.OrderedDict(),
                                           "sort": issledovaniye.research.sort_weight,
                                           "tube_time_get": ""}  # Словарь результата
                if not issledovaniye.deferred or issledovaniye.doc_confirmation:
                    for isstube in issledovaniye.tubes.all():
                        if isstube.time_get:
                            result["results"][kint]["tube_time_get"] = str(
                                dateformat.format(isstube.time_get, settings.DATE_FORMAT))
                            break

                    results = Result.objects.filter(issledovaniye=issledovaniye).order_by(
                        "fraction__sort_weight")  # Выборка результатов из базы

                    n = 0
                    for res in results:  # Перебор результатов
                        pk = res.fraction.sort_weight
                        if not pk or pk <= 0:
                            pk = res.fraction.pk
                        if res.fraction.render_type == 0:
                            if pk not in result["results"][kint]["fractions"].keys():
                                result["results"][kint]["fractions"][pk] = {}

                            result["results"][kint]["fractions"][pk]["result"] = result_normal(res.value)  # Значение
                            # if maxdate != str(dateformat.format(issledovaniye.time_save, settings.DATE_FORMAT)):
                            #    result["results"][kint]["fractions"][pk]["result"] += "<br/>" + str(
                            #        dateformat.format(iss.time_save, settings.DATE_FORMAT))
                            result["results"][kint]["fractions"][pk][
                                "title"] = res.fraction.title  # Название фракции
                            result["results"][kint]["fractions"][pk][
                                "units"] = res.fraction.units  # Еденицы измерения
                            refs = res.get_ref(full=True)
                            ref_m = refs["m"]
                            ref_f = refs["f"]
                            if not isinstance(ref_m, str):
                                ref_m = json.dumps(ref_m)
                            if not isinstance(ref_f, str):
                                ref_f = json.dumps(ref_f)
                            result["results"][kint]["fractions"][pk]["ref_m"] = ref_m  # Референсы М
                            result["results"][kint]["fractions"][pk]["ref_f"] = ref_f  # Референсы Ж
                        else:
                            try:
                                tmp_results = json.loads("{}" if not res.value else res.value).get("rows", {})
                            except Exception:
                                tmp_results = {}

                            n = 0
                            for row in tmp_results.values():
                                n += 1
                                tmp_pk = "%d_%d" % (pk, n)
                                if tmp_pk not in result["results"][kint]["fractions"].keys():
                                    result["results"][kint]["fractions"][tmp_pk] = {}
                                result["results"][kint]["fractions"][tmp_pk]["title"] = "Выделенная культура"
                                result["results"][kint]["fractions"][tmp_pk]["result"] = row["title"]
                                result["results"][kint]["fractions"][tmp_pk]["ref_m"] = "{}"
                                result["results"][kint]["fractions"][tmp_pk]["ref_f"] = "{}"
                                result["results"][kint]["fractions"][tmp_pk]["units"] = ""
                                for subrow in row["rows"].values():
                                    if "null" in subrow["value"]:
                                        continue
                                    n += 1
                                    tmp_pk = "%d_%d" % (pk, n)
                                    if tmp_pk not in result["results"][kint]["fractions"].keys():
                                        result["results"][kint]["fractions"][tmp_pk] = {}
                                    result["results"][kint]["fractions"][tmp_pk]["title"] = subrow["title"]
                                    result["results"][kint]["fractions"][tmp_pk]["result"] = subrow["value"]
                                    result["results"][kint]["fractions"][tmp_pk]["ref_m"] = "{}"
                                    result["results"][kint]["fractions"][tmp_pk]["ref_f"] = "{}"
                                    result["results"][kint]["fractions"][tmp_pk]["units"] = ""

                            n += 1
                            tmp_pk = "%d_%d" % (pk, n)
                            if tmp_pk not in result["results"][kint]["fractions"].keys():
                                result["results"][kint]["fractions"][tmp_pk] = {}
                            result["results"][kint]["fractions"][tmp_pk][
                                "title"] = "S - чувствителен; R - резистентен; I - промежуточная чувствительность;"
                            result["results"][kint]["fractions"][tmp_pk]["result"] = ""
                            result["results"][kint]["fractions"][tmp_pk]["ref_m"] = "{}"
                            result["results"][kint]["fractions"][tmp_pk]["ref_f"] = "{}"
                            result["results"][kint]["fractions"][tmp_pk]["units"] = ""
                    if issledovaniye.lab_comment and issledovaniye.lab_comment != "":
                        n += 1
                        tmp_pk = "%d_%d" % (pk, n)
                        if tmp_pk not in result["results"][kint]["fractions"].keys():
                            result["results"][kint]["fractions"][tmp_pk] = {}
                        result["results"][kint]["fractions"][tmp_pk]["title"] = "Комментарий"
                        result["results"][kint]["fractions"][tmp_pk]["result"] = issledovaniye.lab_comment.replace("\n",
                                                                                                                   "<br/>")
                        result["results"][kint]["fractions"][tmp_pk]["ref_m"] = "{}"
                        result["results"][kint]["fractions"][tmp_pk]["ref_f"] = "{}"
                        result["results"][kint]["fractions"][tmp_pk]["units"] = ""
                else:
                    fr_list = directory.Fractions.objects.filter(research=issledovaniye.research)
                    for fr in fr_list:
                        pk = fr.sort_weight
                        if not pk or pk <= 0:
                            pk = fr.pk
                        if pk not in result["results"][kint]["fractions"].keys():
                            result["results"][kint]["fractions"][pk] = {}

                        result["results"][kint]["fractions"][pk]["result"] = "отложен"  # Значение
                        result["results"][kint]["fractions"][pk][
                            "title"] = fr.title  # Название фракции
                        result["results"][kint]["fractions"][pk][
                            "units"] = fr.units  # Еденицы измерения
                        ref_m = {"": ""}  # fr.ref_m
                        ref_f = {"": ""}  # fr.ref_f
                        if not isinstance(ref_m, str):
                            ref_m = json.dumps(ref_m)
                        if not isinstance(ref_f, str):
                            ref_f = json.dumps(ref_f)
                        result["results"][kint]["fractions"][pk]["ref_m"] = ref_m  # Референсы М
                        result["results"][kint]["fractions"][pk]["ref_f"] = ref_f  # Референсы Ж

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
    return s


@login_required
def result_html(request):
    pk = json.loads(request.GET["pk"])
    results_rows = []
    for dpk in pk:
        if not Napravleniya.objects.filter(pk=dpk).exists():
            continue
        dir = Napravleniya.objects.get(pk=dpk)
        if not dir.has_confirm(): continue
        dates = {}
        date_t = ""
        for iss in Issledovaniya.objects.filter(napravleniye=dir, time_save__isnull=False):
            if iss.time_save:
                dt = str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                if dt not in dates.keys():
                    dates[dt] = 0
                dates[dt] += 1
            if iss.tubes.exists() and iss.tubes.first().time_get:
                date_t = iss.tubes.first().time_get.strftime('%d.%m.%Y')

        import operator
        maxdate = ""
        if dates != {}:
            maxdate = max(dates.items(), key=operator.itemgetter(1))[0]

        iss_list = Issledovaniya.objects.filter(napravleniye=dir).order_by("research__direction_id", "research__pk",
                                                                           "research__sort_weight")
        result = {"pk": dpk, "date": maxdate,
                  "patient": {"cardnum": dir.client.number, "fio": dir.client.fio(), "sex": dir.client.sex,
                              "age": dir.client.age_s(direction=dir)}, "results": collections.OrderedDict()}

        kint = 0
        for issledovaniye in iss_list:  # Перебор списка исследований
            kint += 1
            result["results"][kint] = {"title": issledovaniye.research.title,
                                       "fractions": collections.OrderedDict(),
                                       "sort": issledovaniye.research.sort_weight}  # Словарь результата
            if not issledovaniye.deferred or issledovaniye.doc_confirmation:
                results = Result.objects.filter(issledovaniye=issledovaniye).order_by(
                    "fraction__sort_weight")  # Выборка результатов из базы
                for res in results:  # Перебор результатов
                    pk = res.fraction.sort_weight
                    if not pk or pk <= 0:
                        pk = res.fraction.pk
                    if res.fraction.render_type == 0:
                        if pk not in result["results"][kint]["fractions"].keys():
                            result["results"][kint]["fractions"][pk] = {}

                        result["results"][kint]["fractions"][pk]["result"] = res.value  # Значение
                        # if maxdate != str(dateformat.format(issledovaniye.time_save, settings.DATE_FORMAT)):
                        #    result["results"][kint]["fractions"][pk]["result"] += "<br/>" + str(
                        #        dateformat.format(iss.time_save, settings.DATE_FORMAT))
                        result["results"][kint]["fractions"][pk][
                            "title"] = res.fraction.title  # Название фракции
                        result["results"][kint]["fractions"][pk][
                            "units"] = res.fraction.units  # Еденицы измерения
                        ref_m = res.fraction.ref_m
                        ref_f = res.fraction.ref_f
                        if not isinstance(ref_m, str):
                            ref_m = json.dumps(ref_m)
                        if not isinstance(ref_f, str):
                            ref_f = json.dumps(ref_f)
                        result["results"][kint]["fractions"][pk]["ref_m"] = ref_m  # Референсы М
                        result["results"][kint]["fractions"][pk]["ref_f"] = ref_f  # Референсы Ж
                    else:
                        try:
                            tmp_results = json.loads("{}" if not res.value else res.value).get("rows", {})
                        except Exception:
                            tmp_results = {}

                        n = 0
                        for row in tmp_results.values():
                            n += 1
                            tmp_pk = "%d_%d" % (pk, n)
                            if tmp_pk not in result["results"][kint]["fractions"].keys():
                                result["results"][kint]["fractions"][tmp_pk] = {}
                            result["results"][kint]["fractions"][tmp_pk]["title"] = "Выделенная культура"
                            result["results"][kint]["fractions"][tmp_pk]["result"] = row["title"]
                            result["results"][kint]["fractions"][tmp_pk]["ref_m"] = "{}"
                            result["results"][kint]["fractions"][tmp_pk]["ref_f"] = "{}"
                            result["results"][kint]["fractions"][tmp_pk]["units"] = ""
                            for subrow in row["rows"].values():
                                if "null" in subrow["value"]:
                                    continue
                                n += 1
                                tmp_pk = "%d_%d" % (pk, n)
                                if tmp_pk not in result["results"][kint]["fractions"].keys():
                                    result["results"][kint]["fractions"][tmp_pk] = {}
                                result["results"][kint]["fractions"][tmp_pk]["title"] = subrow["title"]
                                result["results"][kint]["fractions"][tmp_pk]["result"] = subrow["value"]
                                result["results"][kint]["fractions"][tmp_pk]["ref_m"] = "{}"
                                result["results"][kint]["fractions"][tmp_pk]["ref_f"] = "{}"
                                result["results"][kint]["fractions"][tmp_pk]["units"] = ""

                        n += 1
                        tmp_pk = "%d_%d" % (pk, n)
                        if tmp_pk not in result["results"][kint]["fractions"].keys():
                            result["results"][kint]["fractions"][tmp_pk] = {}
                        result["results"][kint]["fractions"][tmp_pk][
                            "title"] = "S - чувствителен; R - резистентен; I - промежуточная чувствительность;"
                        result["results"][kint]["fractions"][tmp_pk]["result"] = ""
                        result["results"][kint]["fractions"][tmp_pk]["ref_m"] = "{}"
                        result["results"][kint]["fractions"][tmp_pk]["ref_f"] = "{}"
                        result["results"][kint]["fractions"][tmp_pk]["units"] = ""
            else:
                fr_list = directory.Fractions.objects.filter(research=issledovaniye.research)
                for fr in fr_list:
                    pk = fr.sort_weight
                    if not pk or pk <= 0:
                        pk = fr.pk
                    if pk not in result["results"][kint]["fractions"].keys():
                        result["results"][kint]["fractions"][pk] = {}

                    result["results"][kint]["fractions"][pk]["result"] = "отложен"  # Значение
                    result["results"][kint]["fractions"][pk][
                        "title"] = fr.title  # Название фракции
                    result["results"][kint]["fractions"][pk][
                        "units"] = fr.units  # Еденицы измерения
                    ref_m = fr.ref_m
                    ref_f = fr.ref_f
                    if not isinstance(ref_m, str):
                        ref_m = json.dumps(ref_m)
                    if not isinstance(ref_f, str):
                        ref_f = json.dumps(ref_f)
                    result["results"][kint]["fractions"][pk]["ref_m"] = ref_m  # Референсы М
                    result["results"][kint]["fractions"][pk]["ref_f"] = ref_f  # Референсы Ж
        results_rows.append(result)

    return render(request, "dashboard/results_html.html", {"results": results_rows})


from rmis_integration.client import Client
@login_required
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
    from django.core.paginator import Paginator
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
        TTFont('Consolas', os.path.join(FONTS_FOLDER, 'consolas.ttf')))
    pdfmetrics.registerFont(
        TTFont('Consolas-Bold', os.path.join(FONTS_FOLDER, 'Consolas-Bold.ttf')))

    buffer = BytesIO()

    type = request.GET.get("format", "ng")
    split = request.GET.get("split", "1") == "1"

    if type == "a4":

        c = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4
        lmargin = 55 * mm
        marginx = 5 * mm
        marginy = 10 * mm

        pw = w - marginx - lmargin
        ph = h - marginy * 2

        def py(y=0.0):
            y *= mm
            return h - y - marginy

        def px(x=0.0):
            x *= mm
            return x + lmargin

        def pxc(x=0.0):
            x *= mm
            return w / 2 + x

        def pxr(x=0.0):
            x *= mm
            return pw - x + marginx

        def lj(s, ln=13):
            return s.ljust(ln)

        for dpk in pk:
            if not Napravleniya.objects.filter(pk=dpk).exists():
                continue
            direction = Napravleniya.objects.get(pk=dpk)
            if not direction.has_confirm(): continue
            dates = {}
            date_t = ""
            for iss in Issledovaniya.objects.filter(napravleniye=direction, time_save__isnull=False):
                if iss.time_save:
                    dt = str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                    if dt not in dates.keys():
                        dates[dt] = 0
                    dates[dt] += 1
                if iss.tubes.exists() and iss.tubes.first().time_get:
                    date_t = timezone.localtime(iss.tubes.first().time_get).strftime('%d.%m.%Y')

            import operator
            maxdate = ""
            if dates != {}:
                maxdate = max(dates.items(), key=operator.itemgetter(1))[0]

            iss_list = Issledovaniya.objects.filter(napravleniye=direction)

            c.drawImage(os.path.join(FONTS_FOLDER, '..', 'static', 'img', 'cliches.jpg'), pxr(3.5), py(18), preserveAspectRatio=True, height=20 * mm, anchor="nw")

            c.setFont('OpenSans', 7)
            c.drawString(pxr(5.5), py(21), SettingManager.get("org_title"))
            c.drawString(pxr(-5.5), py(23.7), SettingManager.get("org_www"))
            c.drawString(pxr(-8.5), py(26.4), SettingManager.get("org_phones"))

            c.setFont('Consolas', 10)

            c.drawString(px(), py(), lj('Номер:') + str(direction.pk))

            c.drawString(px(), py(4), lj('Пациент:'))
            c.setFont('Consolas-Bold', 10)
            c.drawString(px(25), py(4), direction.client.fio())
            c.setFont('Consolas', 10)

            c.drawString(px(), py(8), lj('Пол:') + direction.client.sex)
            c.drawString(px(), py(12), lj('Возраст:') + direction.client.age_s(direction=direction))
            c.drawString(px(), py(16), lj('Дата забора:') + date_t)

            c.drawString(px(), py(24), lj('Карта:') + str(direction.client.number_with_type()))
            c.drawString(px(), py(28), lj('Врач:') + direction.doc.get_fio())
            c.drawString(px(), py(32), lj(' ') + direction.doc.podrazdeleniye.title)

            '''
            c.setFont('OpenSans', 18)
            c.drawRightString(pxr(), py(2), "Результаты анализов")
            c.setFont('OpenSans', 12)
            c.drawRightString(pxr(), py(6), "Направление № " + str(dir.pk))
            c.drawRightString(pxr(), py(10), "Пациент: %s" % dir.client.fio())
            c.drawRightString(pxr(), py(15), "Пол: %s" % dir.client.sex + ", " + dir.client.age_s() + " " + "(д.р. " + str(
                              dateformat.format(dir.client.bd(), settings.DATE_FORMAT)) + ")")
            c.drawRightString(pxr(), py(20), "Номер карты: %d" % dir.client.num)
            c.drawRightString(pxr(), py(25), "Лечащий врач: " + dir.doc.get_fio())
            c.drawRightString(pxr(), py(30), "Отделение: " + dir.doc.podrazdeleniye.title)

            c.setFont('OpenSans', 8)
            c.drawString(px(), py(25), SettingManager.get("org_title"))
            c.drawString(px(), py(28), "г. Иркутск, б-р. Гагарина, 18. тел: 280-808, 280-809")
            c.drawString(px(), py(31), SettingManager.get("org_www"))
            '''
            # iss_list = Issledovaniya.objects.filter(napravleniye=dir).order_by("research__pk", "research__sort_weight")

            # c.setFont('OpenSans', 9)
            # c.drawString(px(), py(35), iss_list.first().research.get_podrazdeleniye().title)

            c.setFont('OpenSans', 8)
            from reportlab.platypus import Table, TableStyle
            from reportlab.lib import colors
            from reportlab.platypus import Paragraph
            from reportlab.lib.styles import getSampleStyleSheet

            styleSheet = getSampleStyleSheet()
            styleSheet["BodyText"].wordWrap = 'CJK'
            stl = deepcopy(styleSheet["BodyText"])
            from reportlab.lib.enums import TA_CENTER
            stl.alignment = TA_CENTER
            tw = pw

            data = []
            tmp = [Paragraph('<font face="OpenSansBold" size="8">Исследование</font>', styleSheet["BodyText"]),
                   Paragraph(
                       '<font face="OpenSansBold" size="8">Результат</font><br/><font face="OpenSans" size="8">(# - не норма)</font>',
                       styleSheet["BodyText"])]

            if direction.client.sex.lower() == "м":
                tmp.append(
                    Paragraph('<font face="OpenSansBold" size="8">Референсные значения (М)</font>',
                              styleSheet["BodyText"]))
            else:
                tmp.append(
                    Paragraph('<font face="OpenSansBold" size="8">Референсные значения (Ж)</font>',
                              styleSheet["BodyText"]))

            tmp.append(
                Paragraph('<font face="OpenSansBold" size="8">Единицы<br/>измерения</font>', styleSheet["BodyText"]))
            tmp.append(Paragraph('<font face="OpenSansBold" size="8">Исполнитель</font>', styleSheet["BodyText"]))
            # tmp.append(Paragraph('<font face="OpenSans" size="8">Дата заб.</font>', styleSheet["BodyText"]))
            tmp.append(Paragraph('<font face="OpenSansBold" size="8">Дата</font>', styleSheet["BodyText"]))
            data.append(tmp)
            cw = [int(tw * 0.26), int(tw * 0.178), int(tw * 0.17), int(tw * 0.134), int(tw * 0.178), int(tw * 0.08)]
            t = Table(data, colWidths=cw)
            style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                ('TOPPADDING', (0, 0), (-1, -1), 2),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                                ])
            style.add('BOTTOMPADDING', (0, 0), (-1, 0), 1)
            style.add('TOPPADDING', (0, 0), (-1, 0), 0)

            t.setStyle(style)

            t.canv = c
            wt, ht = t.wrap(0, 0)
            pos = py(38)
            has0 = directory.Fractions.objects.filter(
                research__pk__in=[x.research.pk for x in Issledovaniya.objects.filter(napravleniye=direction)],
                hide=False,
                render_type=0).exists()
            if has0:
                t.drawOn(c, px(), py(45))
                pos = py(45)

            prev_conf = ""
            prev_date_conf = ""

            def print_vtype(data, f, iss, j, style, styleSheet):

                import operator
                tmp = []
                if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
                    result = Result.objects.get(issledovaniye=iss, fraction=f).value
                    # try:
                    jo = json.loads(result)["rows"]
                    style.add('LINEBELOW', (0, j - 1), (-1, j - 1), 2, colors.black)
                    for key, val in jo.items():
                        style.add('SPAN', (0, j), (-1, j))
                        j += 1

                        norm_vals = []
                        for rowk, rowv in val["rows"].items():
                            if rowv["value"] not in ["", "null"]:
                                norm_vals.insert(0, {"title": rowv["title"], "value": rowv["value"], "k": int(rowk)})
                        if len(norm_vals) > 0:
                            style.add('SPAN', (0, j), (-1, j))
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

            pks = []
            for iss in iss_list.order_by("research__direction_id", "research__pk", "tubes__id",
                                         "research__sort_weight"):
                if iss.pk in pks:
                    continue
                pks.append(iss.pk)
                data = []
                fractions = directory.Fractions.objects.filter(research=iss.research, hide=False,
                                                               render_type=0).order_by("pk").order_by("sort_weight")
                if fractions.count() > 0:
                    if fractions.count() == 1:
                        tmp = [Paragraph('<font face="OpenSans" size="8">' + iss.research.title + "</font>",
                                         styleSheet["BodyText"])]
                        result = "не завершено"
                        norm = "none"
                        ref = {"": ""}
                        if Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).exists():
                            r = Result.objects.get(issledovaniye=iss, fraction=fractions[0])
                            ref = r.get_ref()
                            if show_norm:
                                norm = r.get_is_norm(recalc=True)
                            result = result_normal(r.value)

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
                                tmp.append(Paragraph('<font face="ChampB" size="8">' + result + "</font>", stl))
                            elif norm == "maybe":
                                tmp.append(Paragraph('<font face="CalibriBold" size="8">' + result + "</font>", stl))
                            else:
                                tmp.append(Paragraph('<font face="CalibriBold" size="8"># ' + result + "</font>", stl))

                            tmp.append(
                                Paragraph('<font face="OpenSans" size="7">' + get_r(ref) + "</font>",
                                          stl))

                            tmp.append(
                                Paragraph('<font face="OpenSans" size="7">' + fractions[0].units + "</font>", stl))

                            if iss.doc_confirmation:
                                if prev_conf != iss.doc_confirmation.get_fio():
                                    prev_conf = iss.doc_confirmation.get_fio()
                                    prev_date_conf = ""
                                    tmp.append(Paragraph('<font face="OpenSans" size="7">%s</font>' % prev_conf,
                                                         styleSheet["BodyText"]))
                                else:
                                    tmp.append("")
                                if prev_date_conf != iss.time_confirmation.strftime('%d.%m.%y'):
                                    prev_date_conf = iss.time_confirmation.strftime('%d.%m.%y')
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
                                    "" if not iss.tubes.exists() or not iss.tubes.first().time_get else iss.tubes.first().time_get.strftime(
                                        '%d.%m.%Y')), styleSheet["BodyText"]))
                                tmp.append(Paragraph(
                                    '<font face="OpenSansBold" size="7">%s</font>' % iss.time_confirmation.strftime(
                                        '%d.%m.%Y'), styleSheet["BodyText"]))
                            else:
                                tmp.append("")
                                tmp.append(Paragraph(
                                    '<font face="OpenSansBold" size="7">%s</font>' % timezone.localtime(
                                        iss.tubes.first().time_get).strftime(
                                        '%d.%m.%Y'), styleSheet["BodyText"]))
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
                    else:
                        tmp = [Paragraph('<font face="OpenSansBold" size="8">' + iss.research.title + '</font>' +
                                         (
                                             "" if iss.comment == "" or True else '<font face="OpenSans" size="8"><br/>Материал - ' + iss.comment + '</font>'),
                                         styleSheet["BodyText"]), '', '', '']

                        if iss.doc_confirmation:
                            if prev_conf != iss.doc_confirmation.get_fio():
                                prev_conf = iss.doc_confirmation.get_fio()
                                prev_date_conf = ""
                                tmp.append(Paragraph('<font face="OpenSans" size="7">%s</font>' % prev_conf,
                                                     styleSheet["BodyText"]))
                            else:
                                tmp.append("")
                            if prev_date_conf != iss.time_confirmation.strftime('%d.%m.%y'):
                                prev_date_conf = iss.time_confirmation.strftime('%d.%m.%y')
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

                        style = TableStyle(ts)
                        j = 0

                        for f in fractions:
                            j += 1

                            tmp = []
                            if f.render_type == 0:
                                tmp.append(Paragraph('<font face="OpenSans" size="8">' + f.title + "</font>",
                                                     styleSheet["BodyText"]))
                                result = "не завершено"
                                norm = "none"
                                ref = {"": ""}
                                if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
                                    r = Result.objects.get(issledovaniye=iss, fraction=f)
                                    if show_norm:
                                        norm = r.get_is_norm(recalc=True)
                                    result = result_normal(r.value)
                                    ref = r.get_ref()
                                if not iss.doc_confirmation and iss.deferred:
                                    result = "отложен"
                                # elif iss.time_save and maxdate != str(dateformat.format(iss.time_save, settings.DATE_FORMAT)):
                                #    result += "<br/>" + str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                                if norm in ["none", "normal"]:
                                    tmp.append(Paragraph('<font face="ChampB" size="8">' + result + "</font>", stl))
                                elif norm == "maybe":
                                    tmp.append(
                                        Paragraph('<font face="CalibriBold" size="8">' + result + "</font>", stl))
                                else:
                                    tmp.append(
                                        Paragraph('<font face="CalibriBold" size="8"># ' + result + "</font>", stl))

                                tmp.append(Paragraph('<font face="OpenSans" size="7">' + get_r(ref) + "</font>",
                                                     stl))

                                tmp.append(Paragraph('<font face="OpenSans" size="7">' + f.units + "</font>", stl))
                                tmp.append("")
                                tmp.append("")
                                data.append(tmp)
                            elif f.render_type == 1:
                                jp = j
                                j = print_vtype(data, f, iss, j, style, styleSheet)

                                if j - jp > 2:
                                    data.append([Paragraph(
                                        '<font face="OpenSans" size="8">S - чувствителен; R - резистентен; I - промежуточная чувствительность;</font>',
                                        styleSheet["BodyText"])])
                                    style.add('SPAN', (0, j), (-1, j))
                                    style.add('BOX', (0, j), (-1, j), 1, colors.white)
                                    j -= 1

                        for k in range(0, 6):
                            style.add('INNERGRID', (k, 0),
                                      (k, j), 0.1, colors.black)
                            style.add('BOX', (k, 0), (k, j),
                                      0.8, colors.black)

                        style.add('BOTTOMPADDING', (0, 0), (0, -1), 0)
                        style.add('TOPPADDING', (0, 0), (0, -1), 0)

                        t = Table(data, colWidths=cw)
                        t.setStyle(style)
                    t.canv = c
                    wt, ht = t.wrap(0, 0)
                    t.drawOn(c, px(), pos - ht)
                    pos = pos - ht

                fractions = directory.Fractions.objects.filter(research=iss.research, hide=False,
                                                               render_type=1).order_by("pk").order_by("sort_weight")
                if fractions.count() > 0:
                    pos = pos - 3 * mm
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
                                   "" if not iss.tubes.exists() or not iss.tubes.first().time_get else iss.tubes.first().time_get.strftime(
                                       '%d.%m.%Y'), "" if not iss.comment else "<br/>" + iss.comment,),
                                         styleSheet["BodyText"]),
                               Paragraph('<font face="OpenSans" size="8">%s</font>' % (
                                   "Не подтверждено" if not iss.time_confirmation else iss.time_confirmation.strftime(
                                       '%d.%m.%Y')),
                                         styleSheet["BodyText"]),
                               Paragraph('<font face="OpenSans" size="8">%s</font>' % (
                                   "Не подтверждено" if not iss.doc_confirmation else iss.doc_confirmation.get_fio()),
                                         styleSheet["BodyText"])]
                        data.append(tmp)

                        cw = [int(tw * 0.332), int(tw * 0.24), int(tw * 0.2), int(tw * 0.22)]
                        t = Table(data, colWidths=cw)
                        style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                            ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                            ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                            ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                            ('TOPPADDING', (0, 0), (-1, -1), 0),
                                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                                            ])

                        style.add('LINEBELOW', (0, -1), (-1, -1), 2, colors.black)
                        t.setStyle(style)
                        t.canv = c
                        wt, ht = t.wrap(0, 0)
                        t.drawOn(c, px(), pos - ht)
                        pos = pos - ht

                    has_anti = False
                    for f in fractions:
                        j = 0
                        tmp = []
                        if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
                            result = Result.objects.get(issledovaniye=iss, fraction=f).value
                            if result == "":
                                continue
                            jo = json.loads(result)["rows"]
                            for key, val in jo.items():
                                if val["title"] != "":
                                    data = []
                                    style.add('SPAN', (0, j), (-1, j))
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
                                          int(tw * 0.27), int(tw * 0.06)]
                                    t = Table(data, colWidths=cw)

                                    style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                                        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                                        ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                                        ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                                        ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                                                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                                        ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                                                        ])

                                    style.add('BOTTOMPADDING', (0, 0), (-1, -1), 1)
                                    style.add('TOPPADDING', (0, 0), (-1, -1), 2)

                                    style.add('SPAN', (0, 0), (-1, 0))
                                    style.add('SPAN', (0, 1), (-1, 1))

                                    t.setStyle(style)
                                    t.canv = c
                                    wt, ht = t.wrap(0, 0)
                                    t.drawOn(c, px(), pos - ht)
                                    pos = pos - ht
                    if has_anti:
                        data = []
                        tmp = [[Paragraph(
                            '<font face="OpenSans" size="8">S - чувствителен; R - резистентен; I - промежуточная чувствительность;</font>',
                            styleSheet["BodyText"])], "", "", "", "", ""]
                        data.append(tmp)
                        cw = [int(tw * 0.23), int(tw * 0.11), int(tw * 0.22), int(tw * 0.11), int(tw * 0.22),
                              int(tw * 0.112)]
                        t = Table(data, colWidths=cw)
                        style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                            ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                            ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                            ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                            ('TOPPADDING', (0, 0), (-1, -1), 2),
                                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                            ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                                            ])
                        style.add('BOTTOMPADDING', (0, 0), (-1, 0), 1)
                        style.add('TOPPADDING', (0, 0), (-1, 0), 0)
                        style.add('SPAN', (0, 0), (-1, 0))

                        t.setStyle(style)
                        t.canv = c
                        wt, ht = t.wrap(0, 0)
                        t.drawOn(c, px(), pos - ht - 1 * mm)
                        pos = pos - ht
                    pos -= 2 * mm
                if iss.lab_comment and iss.lab_comment != "":
                    data = []
                    tmp = [[Paragraph(
                        '<font face="OpenSans" size="8">Комментарий</font>',
                        styleSheet["BodyText"])], [Paragraph(
                        '<font face="OpenSans" size="8">%s</font>' % (iss.lab_comment.replace("\n", "<br/>")),
                        styleSheet["BodyText"])], "", "", "", ""]
                    data.append(tmp)
                    cw = [int(tw * 0.26), int(tw * 0.178), int(tw * 0.17), int(tw * 0.134), int(tw * 0.178),
                          int(tw * 0.08)]
                    t = Table(data, colWidths=cw)
                    style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                        ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                        ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                        ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                        ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                                        ])
                    style.add('BOTTOMPADDING', (0, 0), (-1, 0), 1)
                    style.add('TOPPADDING', (0, 0), (-1, 0), 0)
                    style.add('SPAN', (1, 0), (-1, 0))

                    t.setStyle(style)
                    t.canv = c
                    wt, ht = t.wrap(0, 0)
                    t.drawOn(c, px(), pos - ht)
                    pos = pos - ht
            if not direction.is_printed:
                direction.is_printed = True
                from datetime import datetime

                direction.time_print = datetime.now()
                direction.doc_print = request.user.doctorprofile
                direction.save()

            dp = request.user.doctorprofile
            if not request.user.is_superuser and dp.podrazdeleniye != \
                    Issledovaniya.objects.filter(napravleniye=direction)[
                        0].research.get_podrazdeleniye() and dp != direction.doc and dp.podrazdeleniye != direction.doc.podrazdeleniye:
                slog.Log(key=dpk, type=998, body=json.dumps(
                    {"lab": str(
                        Issledovaniya.objects.filter(napravleniye=direction)[0].research.get_podrazdeleniye()),
                        "doc": str(direction.doc), "print_otd": str(dp.podrazdeleniye),
                        "patient": str(direction.client.fio())}),
                         user=request.user.doctorprofile).save()

            c.showPage()

        c.save()
    elif type == "ng":
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
                                bottomMargin=5 * mm, allowSplitting=1 if split else 0)

        naprs = []
        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = "OpenSans"
        style.fontSize = 9
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
        logo_path = os.path.join(img_path, 'logo.jpg')
        if request.GET.get("update_logo", "0") == "1" or not os.path.isfile(logo_path):
            with open(logo_path, "wb") as fh:
                fh.write(base64.decodebytes(SettingManager.get("logo_base64_img").split(",")[1].encode()))

        i = Image(logo_path)
        nw = 158
        i.drawHeight = i.drawHeight * (nw / i.drawWidth)
        i.drawWidth = nw
        logo_col = [i, '', '', '', '', Paragraph(
            '%s<br/>%s<br/>%s' % (
                SettingManager.get("org_title"), SettingManager.get("org_www"), SettingManager.get("org_phones")),
            styleAb), '', '', '']
        pw = doc.width
        import operator
        def print_vtype(data, f, iss, j, style, styleSheet):

            import operator
            tmp = []
            if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
                result = Result.objects.get(issledovaniye=iss, fraction=f).value
                # try:
                jo = json.loads(result)["rows"]
                style.add('LINEBELOW', (0, j - 1), (-1, j - 1), 2, colors.black)
                for key, val in jo.items():
                    style.add('SPAN', (0, j), (-1, j))
                    j += 1

                    norm_vals = []
                    for rowk, rowv in val["rows"].items():
                        if rowv["value"] not in ["", "null"]:
                            norm_vals.insert(0, {"title": rowv["title"], "value": rowv["value"], "k": int(rowk)})
                    if len(norm_vals) > 0:
                        style.add('SPAN', (0, j), (-1, j))
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
        #cl = Client()
        normis = request.GET.get("normis", "0") == "1"
        for direction in sorted(Napravleniya.objects.filter(pk__in=pk).distinct(), key=lambda dir: dir.client.individual.pk*100000000 + Result.objects.filter(issledovaniye__napravleniye=dir).count()*10000000 + dir.pk):
            dpk = direction.pk
            if not direction.is_all_confirm():
                continue
            #if not normis:
            #    cl.directions.check_send_results(direction)
            dates = {}
            date_t = ""
            for iss in Issledovaniya.objects.filter(napravleniye=direction, time_save__isnull=False):
                if iss.time_save:
                    dt = str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                    if dt not in dates.keys():
                        dates[dt] = 0
                    dates[dt] += 1
                if iss.tubes.exists() and iss.tubes.first().time_get:
                    date_t = timezone.localtime(iss.tubes.first().time_get).strftime('%d.%m.%Y')

            maxdate = ""
            if dates != {}:
                maxdate = max(dates.items(), key=operator.itemgetter(1))[0]

            fwb = []
            data = [
                ["Номер:", str(dpk)],
                ["Пациент:", Paragraph(direction.client.individual.fio(), styleTableMonoBold)],
                ["Пол:", direction.client.individual.sex],
                ["Возраст:", direction.client.individual.age_s(direction=direction)],
                ["Дата забора:", date_t],
                [Paragraph('&nbsp;', styleTableSm), Paragraph('&nbsp;', styleTableSm)],
                ["№ карты:", str(direction.client.number) + (" - архив" if direction.client.is_archive else "")],
                ["Врач:", "<font>%s<br/>%s</font>" % (direction.doc.get_fio(), direction.doc.podrazdeleniye.title)]
            ]

            data = [[Paragraph(y, styleTableMono) if isinstance(y, str) else y for y in data[xi]] + [logo_col[xi]] for
                    xi in
                    range(len(data))]

            t = Table(data, colWidths=[doc.width * 0.16, doc.width - 158 - doc.width * 0.16, 158])
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

            tw = pw

            data = []
            tmp = [Paragraph('<font face="OpenSansBold" size="8">Исследование</font>', styleSheet["BodyText"]),
                   Paragraph(
                       '<font face="OpenSansBold" size="8">Результат</font><br/><font face="OpenSans" size="8">(# - не норма)</font>',
                       styleSheet["BodyText"])]

            if direction.client.individual.sex.lower() == "м":
                tmp.append(
                    Paragraph('<font face="OpenSansBold" size="8">Референсные значения (М)</font>',
                              styleSheet["BodyText"]))
            else:
                tmp.append(
                    Paragraph('<font face="OpenSansBold" size="8">Референсные значения (Ж)</font>',
                              styleSheet["BodyText"]))

            tmp.append(
                Paragraph('<font face="OpenSansBold" size="8">Единицы<br/>измерения</font>', styleSheet["BodyText"]))
            tmp.append(Paragraph('<font face="OpenSansBold" size="8">Исполнитель</font>', styleSheet["BodyText"]))
            # tmp.append(Paragraph('<font face="OpenSans" size="8">Дата заб.</font>', styleSheet["BodyText"]))
            tmp.append(Paragraph('<font face="OpenSansBold" size="8">Дата</font>', styleSheet["BodyText"]))
            data.append(tmp)
            cw = [int(tw * 0.26), int(tw * 0.178), int(tw * 0.17), int(tw * 0.134), int(tw * 0.178)]
            cw = cw + [tw - sum(cw)]
            t = Table(data, colWidths=cw)
            style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                ('TOPPADDING', (0, 0), (-1, -1), 2),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                                ])
            style.add('BOTTOMPADDING', (0, 0), (-1, 0), 1)
            style.add('TOPPADDING', (0, 0), (-1, 0), 0)

            t.setStyle(style)
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

            pks = []
            for iss in iss_list.order_by("research__direction_id", "research__pk", "tubes__id",
                                         "research__sort_weight"):
                if iss.pk in pks:
                    continue
                pks.append(iss.pk)
                data = []
                fractions = directory.Fractions.objects.filter(research=iss.research, hide=False,
                                                               render_type=0).order_by("pk").order_by("sort_weight")
                if fractions.count() > 0:
                    if fractions.count() == 1:
                        tmp = [Paragraph('<font face="OpenSans" size="8">' + iss.research.title + "</font>",
                                         styleSheet["BodyText"])]
                        result = "не завершено"
                        norm = "none"
                        ref = {"": ""}
                        if Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).exists():
                            r = Result.objects.get(issledovaniye=iss, fraction=fractions[0])
                            ref = r.get_ref()
                            if show_norm:
                                norm = r.get_is_norm(recalc=True)
                            result = result_normal(r.value)

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
                                tmp.append(Paragraph('<font face="ChampB" size="8">' + result + "</font>", stl))
                            elif norm == "maybe":
                                tmp.append(Paragraph('<font face="CalibriBold" size="8">' + result + "</font>", stl))
                            else:
                                tmp.append(Paragraph('<font face="CalibriBold" size="8"># ' + result + "</font>", stl))

                            tmp.append(
                                Paragraph('<font face="OpenSans" size="7">' + get_r(ref) + "</font>",
                                          stl))

                            tmp.append(
                                Paragraph('<font face="OpenSans" size="7">' + fractions[0].units + "</font>", stl))

                            if iss.doc_confirmation:
                                if prev_conf != iss.doc_confirmation.get_fio():
                                    prev_conf = iss.doc_confirmation.get_fio()
                                    prev_date_conf = ""
                                    tmp.append(Paragraph('<font face="OpenSans" size="7">%s</font>' % prev_conf,
                                                         styleSheet["BodyText"]))
                                else:
                                    tmp.append("")
                                if prev_date_conf != iss.time_confirmation.strftime('%d.%m.%y'):
                                    prev_date_conf = iss.time_confirmation.strftime('%d.%m.%y')
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
                                    "" if not iss.tubes.exists() or not iss.tubes.first().time_get else iss.tubes.first().time_get.strftime(
                                        '%d.%m.%Y')), styleSheet["BodyText"]))
                                tmp.append(Paragraph(
                                    '<font face="OpenSansBold" size="7">%s</font>' % iss.time_confirmation.strftime(
                                        '%d.%m.%Y'), styleSheet["BodyText"]))
                            else:
                                tmp.append("")
                                tmp.append(Paragraph(
                                    '<font face="OpenSansBold" size="7">%s</font>' % timezone.localtime(
                                        iss.tubes.first().time_get).strftime(
                                        '%d.%m.%Y'), styleSheet["BodyText"]))
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
                                         styleSheet["BodyText"]), '', '', '']

                        if iss.doc_confirmation:
                            if prev_conf != iss.doc_confirmation.get_fio():
                                prev_conf = iss.doc_confirmation.get_fio()
                                prev_date_conf = ""
                                tmp.append(Paragraph('<font face="OpenSans" size="7">%s</font>' % prev_conf,
                                                     styleSheet["BodyText"]))
                            else:
                                tmp.append("")
                            if prev_date_conf != iss.time_confirmation.strftime('%d.%m.%y'):
                                prev_date_conf = iss.time_confirmation.strftime('%d.%m.%y')
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

                        style = TableStyle(ts)
                        j = 0

                        for f in fractions:
                            j += 1

                            tmp = []
                            if f.render_type == 0:
                                tmp.append(Paragraph('<font face="OpenSans" size="8">' + f.title + "</font>",
                                                     styleSheet["BodyText"]))
                                result = "не завершено"
                                norm = "none"
                                ref = {"": ""}
                                if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
                                    r = Result.objects.get(issledovaniye=iss, fraction=f)
                                    if show_norm:
                                        norm = r.get_is_norm(recalc=True)
                                    result = result_normal(r.value)
                                    ref = r.get_ref()
                                if not iss.doc_confirmation and iss.deferred:
                                    result = "отложен"
                                # elif iss.time_save and maxdate != str(dateformat.format(iss.time_save, settings.DATE_FORMAT)):
                                #    result += "<br/>" + str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                                if norm in ["none", "normal"]:
                                    tmp.append(Paragraph('<font face="ChampB" size="8">' + result + "</font>", stl))
                                elif norm == "maybe":
                                    tmp.append(
                                        Paragraph('<font face="CalibriBold" size="8">' + result + "</font>", stl))
                                else:
                                    tmp.append(
                                        Paragraph('<font face="CalibriBold" size="8"># ' + result + "</font>", stl))

                                tmp.append(Paragraph('<font face="OpenSans" size="7">' + get_r(ref) + "</font>",
                                                     stl))

                                tmp.append(Paragraph('<font face="OpenSans" size="7">' + f.units + "</font>", stl))
                                tmp.append("")
                                tmp.append("")
                                data.append(tmp)
                            elif f.render_type == 1:
                                jp = j
                                j = print_vtype(data, f, iss, j, style, styleSheet)

                                if j - jp > 2:
                                    data.append([Paragraph(
                                        '<font face="OpenSans" size="8">S - чувствителен; R - резистентен; I - промежуточная чувствительность;</font>',
                                        styleSheet["BodyText"])])
                                    style.add('SPAN', (0, j), (-1, j))
                                    style.add('BOX', (0, j), (-1, j), 1, colors.white)
                                    j -= 1

                        for k in range(0, 6):
                            style.add('INNERGRID', (k, 0),
                                      (k, j), 0.1, colors.black)
                            style.add('BOX', (k, 0), (k, j),
                                      0.8, colors.black)

                        style.add('BOTTOMPADDING', (0, 0), (0, -1), 0)
                        style.add('TOPPADDING', (0, 0), (0, -1), 0)

                        t = Table(data, colWidths=cw)
                        t.setStyle(style)
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
                                   "" if not iss.tubes.exists() or not iss.tubes.first().time_get else iss.tubes.first().time_get.strftime(
                                       '%d.%m.%Y'), "" if not iss.comment else "<br/>" + iss.comment,),
                                         styleSheet["BodyText"]),
                               Paragraph('<font face="OpenSans" size="8">%s</font>' % (
                                   "Не подтверждено" if not iss.time_confirmation else iss.time_confirmation.strftime(
                                       '%d.%m.%Y')),
                                         styleSheet["BodyText"]),
                               Paragraph('<font face="OpenSans" size="8">%s</font>' % (
                                   "Не подтверждено" if not iss.doc_confirmation else iss.doc_confirmation.get_fio()),
                                         styleSheet["BodyText"])]
                        data.append(tmp)

                        cw = [int(tw * 0.34), int(tw * 0.24), int(tw * 0.2)]
                        cw = cw + [tw - sum(cw)]
                        t = Table(data, colWidths=cw)
                        style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                            ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                            ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                            ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                            ('TOPPADDING', (0, 0), (-1, -1), 0),
                                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                                            ])

                        style.add('LINEBELOW', (0, -1), (-1, -1), 2, colors.black)
                        t.setStyle(style)
                        t.spaceBefore = 3 * mm
                        t.spaceAfter = 0
                        fwb.append(t)

                    has_anti = False
                    for f in fractions:
                        j = 0
                        tmp = []
                        if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
                            result = Result.objects.get(issledovaniye=iss, fraction=f).value
                            if result == "":
                                continue
                            jo = json.loads(result)["rows"]
                            for key, val in jo.items():
                                if val["title"] != "":
                                    data = []
                                    style.add('SPAN', (0, j), (-1, j))
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

                                    style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                                        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                                        ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                                        ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                                        ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                                                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                                        ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                                                        ])

                                    style.add('BOTTOMPADDING', (0, 0), (-1, -1), 1)
                                    style.add('TOPPADDING', (0, 0), (-1, -1), 2)

                                    style.add('SPAN', (0, 0), (-1, 0))
                                    style.add('SPAN', (0, 1), (-1, 1))

                                    t.setStyle(style)
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
                        style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                            ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                            ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                            ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                            ('TOPPADDING', (0, 0), (-1, -1), 2),
                                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                            ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                                            ])
                        style.add('BOTTOMPADDING', (0, 0), (-1, 0), 1)
                        style.add('TOPPADDING', (0, 0), (-1, 0), 0)
                        style.add('SPAN', (0, 0), (-1, 0))

                        t.setStyle(style)
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
                    style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                        ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                        ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                        ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                        ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                                        ])
                    style.add('BOTTOMPADDING', (0, 0), (-1, 0), 1)
                    style.add('TOPPADDING', (0, 0), (-1, 0), 0)
                    style.add('SPAN', (1, 0), (-1, 0))

                    t.setStyle(style)
                    fwb.append(t)
            if client_prev == direction.client.individual.pk and not split:
                naprs.append(HRFlowable(width=pw, spaceAfter=2.5 * mm, spaceBefore=1.5 * mm, color=colors.lightgrey))
            elif client_prev > -1:
                naprs.append(PageBreak())
            naprs.append(PTOContainer(fwb))
            client_prev = direction.client.individual.pk

        doc.build(naprs)
    elif type == "a5":
        c = canvas.Canvas(buffer, pagesize=landscape(A4))
        pages = Paginator(pk, 2)
        w, h = landscape(A4)
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
            if Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).exists():
                r = Result.objects.get(issledovaniye=iss, fraction=fractions[0])
                ref = r.get_ref()
                result = r.value

            if not iss.doc_confirmation and iss.deferred:
                result = "отложен"
            elif iss.time_save and maxdate != str(dateformat.format(iss.time_save, settings.DATE_FORMAT)):
                result += "<br/>" + str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
            tmp.append(Paragraph('<font face="ChampB" size="8">' + result + "</font>", styleSheet["BodyText"]))
            tmp.append(
                Paragraph('<font face="OpenSans" size="7">&nbsp;&nbsp;&nbsp;' + fractions[0].units + "</font>",
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
                tmp = [Paragraph('&nbsp;&nbsp;&nbsp;&nbsp;<font face="OpenSans" size="7">' + f.title + "</font>",
                                 styleSheet["BodyText"])]
                result = "не завершено"
                ref = {"": ""}
                if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
                    r = Result.objects.get(issledovaniye=iss, fraction=f)
                    ref = r.get_ref()
                    result = r.value
                if not iss.doc_confirmation and iss.deferred:
                    result = "отложен"
                elif iss.time_save and maxdate != str(dateformat.format(iss.time_save, settings.DATE_FORMAT)):
                    result += "<br/>" + str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                tmp.append(Paragraph('<font face="ChampB" size="8">' + result + "</font>", styleSheet["BodyText"]))
                tmp.append(Paragraph('<font face="OpenSans" size="7">&nbsp;&nbsp;&nbsp;' + f.units + "</font>",
                                     styleSheet["BodyText"]))
                tmp.append(Paragraph('<font face="OpenSans" size="7">' + get_r(ref) + "</font>",
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
    if not napr.is_printed:
        napr.is_printed = True
        from datetime import datetime

        napr.time_print = datetime.now()
        napr.doc_print = doctorprofile
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
    ph = h - marginy * 2

    def py(y=0.0):
        y *= mm
        return h - y - marginy

    def pyb(y=0.0):
        y *= mm
        return y + marginy

    def pxc(x=0.0):
        x *= mm
        return w / 2 + x

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
            tmp = []
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
    paddingx = 30
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
    styleSheet = getSampleStyleSheet()
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
                                  "fio": iss.napravleniye.client.individual.fio(short=True, dots=True) + "<br/>Карта: " + iss.napravleniye.client.number_with_type() +
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
        data = data_header = []
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
    s = ""
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
            iss_list = []

            iss_list = Issledovaniya.objects.filter(
                research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)
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


@csrf_exempt
@login_required
def results_search_directions(request):
    data = {}
    if request.method == "POST":
        data = request.POST
    else:
        data = request.GET

    period = json.loads(data.get("period", "{}"))
    type = period.get("type", "d")
    type_patient = int(data.get("type_patient", "-1"))
    query = data.get("query", "").strip()
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
    elif bool(re.compile(r'^([a-zA-Zа-яА-Я]+)( [a-zA-Zа-яА-Я]+)?( [a-zA-Zа-яА-Я]+)?( \d{2}\.\d{2}\.\d{4})?$').match(
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
            bdate = split[3]
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
    except ValueError:
        return JsonResponse({"rows": [], "grouping": grouping, "len": 0, "next_offset": 0, "all_rows": 0, "error_message": "Некорректная дата"})
    collection = Napravleniya.objects.filter(issledovaniya__time_confirmation__range=(day1, day2),
                                             issledovaniya__time_confirmation__isnull=False,
                                             client__is_archive=archive)
    if otd_search != -1:
        collection = collection.filter(doc__podrazdeleniye__pk=otd_search)

    if doc_search != -1:
        collection = collection.filter(doc__pk=doc_search)

    client_base = None
    if type_patient != -1:
        client_base = CardBase.objects.get(pk=type_patient)
    if filter_type == "fio":
        collection = collection.filter(client__individual__family__contains=family,
                                       client__individual__name__contains=name,
                                       client__individual__patronymic__contains=twoname,
                                       client__individual__birthday__contains=bdate)
    if filter_type == "fio_short":
        collection = collection.filter(client__individual__family__istartswith=family,
                                       client__individual__name__istartswith=name,
                                       client__individual__patronymic__istartswith=twoname,
                                       client__individual__birthday=bdate)

    if filter_type == "card_number":
        filter = dict(client__number__iexact=query)
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
    sort_types = {}
    if sorting_direction == "up":
        sort_types = {"confirm-date": ("issledovaniya__time_confirmation",),
                      "patient": ("issledovaniya__time_confirmation", "client__individual__family", "client__individual__name", "client__individual__patronymic",)}
    else:
        sort_types = {"confirm-date": ("-issledovaniya__time_confirmation",),
                      "patient": ("-issledovaniya__time_confirmation", "-client__individual__family", "-client__individual__name", "-client__individual__patronymic",)}
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
        for r in direction.issledovaniya_set.all():
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

        tmp_dir = {"pk": direction.pk,
                   "laboratory": direction.issledovaniya_set.first().research.get_podrazdeleniye().title,
                   "otd": direction.doc.podrazdeleniye.title,
                   "doc": direction.doc.get_fio(),
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
                                               "doc_search": doc_search}), user=request.user.doctorprofile).save()

    return JsonResponse({"rows": rows, "grouping": grouping, "len": n-offset, "next_offset": n, "all_rows": cnt, "error_message": ""})
