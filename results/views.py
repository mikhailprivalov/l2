from copy import deepcopy

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
from reportlab.pdfbase import pdfdoc
from appconf.manager import SettingManager

pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:true,bSilent:false,bShrinkToFit:true}\);)>>'

@login_required
@group_required("Лечащий врач", "Зав. отделением")
@csrf_exempt
def results_search(request):
    """ Представление для поиска результатов исследований у пациента """
    if request.method == "POST":
        dirs = set()
        result = {"directions": [], "client_id": int(request.POST["client_id"]), "research_id": int(request.POST["research_id"]), "other_dirs": []}
        for r in Result.objects.filter(fraction__research_id=result["research_id"], issledovaniye__napravleniye__client_id=result["client_id"], issledovaniye__doc_confirmation__isnull=False):
            dirs.add(r.issledovaniye.napravleniye.pk)
        for d in Napravleniya.objects.filter(client_id=result["client_id"], issledovaniya__research_id=result["research_id"]):
            tmp_d = {"pk": d.pk}
            if d.pk in dirs:
                tmp_d["date"] = Issledovaniya.objects.filter(napravleniye=d).first().time_confirmation.strftime('%d.%m.%Y')
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


import datetime
@csrf_exempt
@login_required
def loadready(request):
    """ Представление, возвращающее JSON со списками пробирок и направлений, принятых в лабораторию """
    result = {"tubes": [], "directions": []}
    if request.method == "POST":
        date_start = request.POST["datestart"]
        date_end = request.POST["dateend"]
        deff = int(request.POST["def"])
    else:
        date_start = request.GET["datestart"]
        date_end = request.GET["dateend"]
        deff = int(request.GET["def"])

    date_start = datetime.date(int(date_start.split(".")[2]), int(date_start.split(".")[1]),int(date_start.split(".")[0]))
    date_end = datetime.date(int(date_end.split(".")[2]), int(date_end.split(".")[1]), int(date_end.split(".")[0])) + datetime.timedelta(1)
    tlist = []
    if deff == 0:
        tlist = TubesRegistration.objects.filter(doc_recive__isnull=False, time_recive__range=(date_start,date_end),
                                                 # issledovaniya__napravleniye__is_printed=False,
                                                 issledovaniya__doc_confirmation__isnull=True,
                                                 issledovaniya__research__subgroup__podrazdeleniye=request.user.doctorprofile.podrazileniye,
                                                 issledovaniya__isnull=False)
    else:
        tlist = TubesRegistration.objects.filter(doc_recive__isnull=False, time_get__isnull=False,
                                                 # issledovaniya__napravleniye__is_printed=False,
                                                 issledovaniya__doc_confirmation__isnull=True,
                                                 issledovaniya__research__subgroup__podrazdeleniye=request.user.doctorprofile.podrazileniye,
                                                 issledovaniya__deferred=True, issledovaniya__isnull=False)
    # tubes =   # Загрузка пробирок,
    # лаборатория исследования которых равна лаборатории
    # текущего пользователя, принятых лабораторией и результаты для которых не напечатаны
    for tube in tlist:  # перебор результатов выборки
        # iss_set = tube.issledovaniya_set.all()  # Получение списка исследований для пробирки
        # if tube.issledovaniya_set.count() == 0: continue  # пропуск пробирки, если исследований нет
        # complete = False  # Завершен ли анализ
        direction = tube.issledovaniya_set.first().napravleniye  # Выборка направления для пробирки

        date_tmp = dateformat.format(tube.time_recive, settings.DATE_FORMAT).split(".")
        date_tmp = "%s.%s.%s" % (date_tmp[0], date_tmp[1], date_tmp[2][2:4])

        dicttube = {"id": tube.pk, "direction": direction.pk, "date": date_tmp}  # Временный словарь с информацией о пробирке
        # if not complete and dicttube not in result[
        if dicttube not in result[
            "tubes"]:  # Если исследования не завершены и информация о пробирке не присутствует в ответе
            result["tubes"].append(dicttube)  # Добавление временного словаря к ответу

        date_tmp = dateformat.format(direction.data_sozdaniya, settings.DATE_FORMAT).split(".")
        date_tmp = "%s.%s.%s" % (date_tmp[0], date_tmp[1], date_tmp[2][2:4])

        dictdir = {"id": direction.pk, "date": date_tmp}  # Временный словарь с информацией о направлении
        if dictdir not in result["directions"]:  # Если информация о направлении не присутствует в ответе
            result["directions"].append(dictdir)  # Добавление временного словаря к ответу
    result["tubes"] = sorted(result["tubes"], key=lambda k: k['id'])  # Сортировка списка пробирок
    result["directions"] = sorted(result["directions"], key=lambda k: k['id'])  # Сортировка списка направлений
    return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
@login_required
def results_save(request):
    """ Сохранение результатов """
    result = {"ok": False}
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
            from django.utils import timezone

            issledovaniye.time_save = timezone.now()  # Время сохранения
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
            issledovaniye.time_confirmation = timezone.now()  # Время подтверждения
            issledovaniye.save()
            slog.Log(key=request.POST["pk"], type=14, body="", user=request.user.doctorprofile).save()
            Uet.add(request.user.doctorprofile,issledovaniye.research,issledovaniye.napravleniye.pk)


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
                issledovaniye.doc_confirmation = request.user.doctorprofile  # Кто подтвердил
                from django.utils import timezone

                issledovaniye.time_confirmation = timezone.now()  # Время подтверждения
                issledovaniye.save()
        result["ok"] = True
    return HttpResponse(json.dumps(result), content_type="application/json")


@login_required
def get_full_result(request):
    """ Получение результатов для направления """
    from django.db.models import Q
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
        maxdate = max(dates.items(), key=operator.itemgetter(1))[0]

        iss_list = Issledovaniya.objects.filter(napravleniye=napr).order_by("research__direction__pk",
                                                                            "research__sort_weight")  # Выборка списка исследований из базы по направлению
        kint = 0
        if not iss_list.filter(doc_confirmation__isnull=True).exists() or iss_list.filter(
                deferred=False).exists():  # Если для направления все исследования подтверждены

            result["direction"] = {}  # Направление
            result["direction"]["pk"] = napr.pk  # ID
            result["direction"]["doc"] = ""
            if iss_list.filter(doc_confirmation__isnull=False).exists():
                result["direction"]["doc"] = iss_list.filter(doc_confirmation__isnull=False)[0].doc_confirmation.get_fio()  # ФИО подтвердившего
            result["direction"]["date"] = maxdate  # Дата подтверждения

            result["client"] = {}  # Пациент
            result["client"]["sex"] = napr.client.sex  # Пол
            result["client"]["fio"] = napr.client.fio()  # ФИО
            result["client"]["age"] = napr.client.age_s()  # Возраст
            result["client"]["cardnum"] = napr.client.num  # Номер карты
            result["client"]["dr"] = str(dateformat.format(napr.client.bd(), settings.DATE_FORMAT))  # Дата рождения

            result["results"] = {}  # Результаты
            for issledovaniye in iss_list:  # Перебор списка исследований
                kint += 1
                result["results"][kint] = {"title": issledovaniye.research.title,
                                           "fractions": {},
                                           "sort": issledovaniye.research.sort_weight}  # Словарь результата
                if not issledovaniye.deferred or issledovaniye.doc_confirmation:
                    results = Result.objects.filter(issledovaniye=issledovaniye).order_by(
                        "fraction__sort_weight")  # Выборка результатов из базы
                    for res in results:  # Перебор результатов
                        pk = res.fraction.sort_weight
                        if not pk or pk <= 0:
                            pk = res.fraction.pk
                        if pk not in result["results"][kint]["fractions"].keys():
                            result["results"][kint]["fractions"][pk] = {}

                        result["results"][kint]["fractions"][pk]["result"] = res.value  # Значение
                        if maxdate != str(dateformat.format(issledovaniye.time_save, settings.DATE_FORMAT)):
                            result["results"][kint]["fractions"][pk]["result"] += "<br/>" + str(
                                dateformat.format(iss.time_save, settings.DATE_FORMAT))
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
    if re.match(r'\d{1,}\.\d{2,}$', s):
        try:
            s = str(round(float(s), 1))
        except:
            pass
    # s = lr(s).replace(" ", "&nbsp;")
    return s


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
    from reportlab.lib.units import mm
    import os.path

    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))  # Путь до текущего скрипта

    pdfmetrics.registerFont(
        TTFont('OpenSans', PROJECT_ROOT + '/../static/fonts/OpenSans.ttf'))
    pdfmetrics.registerFont(
        TTFont('Champ', PROJECT_ROOT + '/../static/fonts/Champ.ttf'))
    pdfmetrics.registerFont(
        TTFont('ChampB', PROJECT_ROOT + '/../static/fonts/Calibri.ttf'))
    pdfmetrics.registerFont(
        TTFont('OpenSansBold', PROJECT_ROOT + '/../static/fonts/OpenSans-Bold.ttf'))
    pdfmetrics.registerFont(
        TTFont('OpenSansItalic', PROJECT_ROOT + '/../static/fonts/OpenSans-Italic.ttf'))
    pdfmetrics.registerFont(
        TTFont('Consolas', PROJECT_ROOT + '/../static/fonts/consolas.ttf'))
    pdfmetrics.registerFont(
        TTFont('Consolas-Bold', PROJECT_ROOT + '/../static/fonts/Consolas-Bold.ttf'))

    buffer = BytesIO()

    type = "a4"

    if type == "a4":

        c = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4

        marginx = 5 * mm
        marginy = 10*mm

        pw = w - marginx - 55 * mm
        ph = h-marginy*2

        def py(y=0.0):
            y *= mm
            return h-y-marginy

        def px(x=0.0):
            x *= mm
            return x+marginx

        def pxc(x=0.0):
            x *= mm
            return w/2 + x

        def pxr(x=0.0):
            x *= mm
            return pw - x + marginx

        def lj(s, ln=13):
            return s.ljust(ln)

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
            maxdate = max(dates.items(), key=operator.itemgetter(1))[0]

            iss_list = Issledovaniya.objects.filter(napravleniye=dir).order_by("research__direction_id", "research__pk",
                                                                               "research__sort_weight")

            c.drawImage(PROJECT_ROOT + '/../static/img/cliches.jpg', pxr(54), py(18), preserveAspectRatio=True,
                        height=20 * mm, anchor="nw")

            c.setFont('OpenSans', 7)
            c.drawString(pxr(56), py(21), SettingManager.get("org_title"))
            c.drawString(pxr(45), py(23.7), SettingManager.get("org_www"))
            c.drawString(pxr(42), py(26.4), SettingManager.get("org_phones"))

            c.setFont('Consolas', 10)

            c.drawString(px(), py(), lj('Номер:') + str(dir.pk))

            c.drawString(px(), py(4), lj('Пациент:'))
            c.setFont('Consolas-Bold', 10)
            c.drawString(px(25), py(4), dir.client.fio())
            c.setFont('Consolas', 10)

            c.drawString(px(), py(8), lj('Пол:') + dir.client.sex)
            c.drawString(px(), py(12), lj('Возраст:') + dir.client.age_s())
            c.drawString(px(), py(16), lj('Дата забора:') + date_t)

            c.drawString(px(), py(24), lj('№ карты:') + str(dir.client.num))
            c.drawString(px(), py(28), lj('Врач:') + dir.doc.get_fio())
            c.drawString(px(), py(32), lj(' ') + dir.doc.podrazileniye.title)

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
            c.drawRightString(pxr(), py(30), "Отделение: " + dir.doc.podrazileniye.title)

            c.setFont('OpenSans', 8)
            c.drawString(px(), py(25), SettingManager.get("org_title"))
            c.drawString(px(), py(28), "г. Иркутск, б-р. Гагарина, 18. тел: 280-808, 280-809")
            c.drawString(px(), py(31), SettingManager.get("org_www"))
            '''
            #iss_list = Issledovaniya.objects.filter(napravleniye=dir).order_by("research__pk", "research__sort_weight")

            # c.setFont('OpenSans', 9)
            #c.drawString(px(), py(35), iss_list.first().research.subgroup.podrazdeleniye.title)

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
            tmp = []
            tmp.append(Paragraph('<font face="OpenSansBold" size="8">Исследование</font>', styleSheet["BodyText"]))
            tmp.append(Paragraph('<font face="OpenSansBold" size="8">Результат</font>', styleSheet["BodyText"]))

            if dir.client.sex.lower() == "м":
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
            cw = [int(tw * 0.26), int(tw * 0.178), int(tw * 0.164), int(tw * 0.14), int(tw * 0.178), int(tw * 0.08)]
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
            has0 = directory.Fractions.objects.filter(research__pk__in=[x.research.pk for x in Issledovaniya.objects.filter(napravleniye=dir)], hide=False, render_type=0).exists()
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
                            tmp = []
                            tmp.append("")
                            tmp.append("")
                            tmp.append("")
                            tmp.append("")
                            tmp.append("")
                            tmp.append("")
                            data.append(tmp)

                        tmp = []
                        tmp.append(Paragraph(
                            '&nbsp;&nbsp;&nbsp;&nbsp;<font face="OpenSans" size="8">' + (
                            "" if len(norm_vals) == 0 else f.title + ": ") + val["title"] + "</font>",
                            styleSheet["BodyText"]))
                        tmp.append("")
                        tmp.append("")
                        tmp.append("")
                        tmp.append("")
                        tmp.append("")
                        data.append(tmp)
                        if len(norm_vals) > 0:
                            li = 0
                            norm_vals.sort(key=operator.itemgetter('k'))
                            for idx, rowv in enumerate(norm_vals):
                                li = idx
                                if li % 2 == 0:
                                    tmp = []
                                    tmp.append(Paragraph('<font face="OpenSans" size="8">' + rowv["title"] + "</font>",
                                                         styleSheet["BodyText"]))
                                    tmp.append(Paragraph('<font face="OpenSans" size="8">' + rowv["value"] + "</font>",
                                                         styleSheet["BodyText"]))
                                    tmp.append("")
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

            for iss in iss_list:
                data = []
                fractions = directory.Fractions.objects.filter(research=iss.research, hide=False, render_type=0).order_by("pk").order_by("sort_weight")
                if fractions.count() > 0:
                    if fractions.count() == 1:
                        tmp = []
                        tmp.append(Paragraph('<font face="OpenSans" size="8">' + iss.research.title + "</font>",
                                             styleSheet["BodyText"]))
                        result = ""
                        if Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).exists():
                            result = result_normal(Result.objects.get(issledovaniye=iss, fraction=fractions[0]).value)

                        if not iss.doc_confirmation and iss.deferred:
                            result = "отложен"
                        elif iss.time_save and maxdate != str(dateformat.format(iss.time_save, settings.DATE_FORMAT)):
                            pass #result += "<br/>" + str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
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

                            tmp.append(Paragraph('<font face="ChampB" size="8">' + result + "</font>", stl))
                            if dir.client.sex.lower() == "м":
                                tmp.append(Paragraph('<font face="OpenSans" size="7">' + get_r(fractions[0].ref_m) + "</font>",
                                                     stl))
                            else:
                                tmp.append(Paragraph('<font face="OpenSans" size="7">' + get_r(fractions[0].ref_f) + "</font>",
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
                                tmp.append(Paragraph('<font face="OpenSansBold" size="7">%s</font>' % iss.doc_confirmation.get_fio(), styleSheet["BodyText"]))
                                tmp.append(Paragraph('<font face="OpenSansBold" size="7">%s</font>' % ("" if not iss.tubes.exists() or not iss.tubes.first().time_get else iss.tubes.first().time_get.strftime('%d.%m.%Y')), styleSheet["BodyText"]))
                                tmp.append(Paragraph('<font face="OpenSansBold" size="7">%s</font>' % iss.time_confirmation.strftime('%d.%m.%Y'), styleSheet["BodyText"]))
                            else:
                                tmp.append("")
                                tmp.append(Paragraph(
                                    '<font face="OpenSansBold" size="7">%s</font>' % iss.tubes.first().time_get.strftime(
                                        '%d.%m.%Y'), styleSheet["BodyText"]))
                                tmp.append("")
                            data.append(tmp)

                            j = print_vtype(data, f, iss, 1, st, styleSheet)
                            data.append([Paragraph(
                                '<font face="OpenSans" size="8">S - чувствителен; R - резистентен; I - промежуточная чувствительность;</font>',
                                styleSheet["BodyText"])])
                            st.add('SPAN', (0, j), (-1, j))
                            st.add('BOX', (0, j), (-1, j), 1, colors.white)
                            st.add('BOX', (0, j-1), (-1, j-1), 1, colors.black)

                        t = Table(data, colWidths=cw)
                        t.setStyle(st)
                    else:
                        tmp = [Paragraph('<font face="OpenSansBold" size="8">' + iss.research.title + "</font>",
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
                                result = ""
                                if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
                                    result = result_normal(Result.objects.get(issledovaniye=iss, fraction=f).value)
                                if not iss.doc_confirmation and iss.deferred:
                                    result = "отложен"
                                # elif iss.time_save and maxdate != str(dateformat.format(iss.time_save, settings.DATE_FORMAT)):
                                #    result += "<br/>" + str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                                tmp.append(Paragraph('<font face="ChampB" size="8">' + result + "</font>", stl))
                                if dir.client.sex.lower() == "м":
                                    tmp.append(Paragraph('<font face="OpenSans" size="7">' + get_r(f.ref_m) + "</font>",
                                                         stl))
                                else:
                                    tmp.append(Paragraph('<font face="OpenSans" size="7">' + get_r(f.ref_f) + "</font>",
                                                         stl))
                                tmp.append(Paragraph('<font face="OpenSans" size="7">' + f.units + "</font>", stl))
                                tmp.append("")
                                tmp.append("")
                                data.append(tmp)
                            elif f.render_type == 1:
                                jp = j
                                j = print_vtype(data, f, iss, j, style, styleSheet)

                                if j - jp > 2:
                                    data.append([Paragraph('<font face="OpenSans" size="8">S - чувствителен; R - резистентен; I - промежуточная чувствительность;</font>', styleSheet["BodyText"])])
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

                fractions = directory.Fractions.objects.filter(research=iss.research, hide=False, render_type=1).order_by("pk").order_by("sort_weight")
                if fractions.count() > 0:
                    pos = pos - 3 * mm
                    data = []
                    if not has0:
                        tmp = []
                        tmp.append(
                            Paragraph('<font face="OpenSansBold" size="8">Исследование</font>',
                                      styleSheet["BodyText"]))
                        tmp.append(Paragraph('<font face="OpenSansBold" size="8">Дата сбора материала</font>',
                                             styleSheet["BodyText"]))
                        tmp.append(Paragraph('<font face="OpenSansBold" size="8">Дата исполнения</font>',
                                             styleSheet["BodyText"]))
                        tmp.append(Paragraph('<font face="OpenSansBold" size="8">Исполнитель</font>',
                                      styleSheet["BodyText"]))
                        data.append(tmp)

                        tmp = []
                        tmp.append(
                            Paragraph('<font face="OpenSansBold" size="8">%s</font>' % iss.research.title,
                                      styleSheet["BodyText"]))
                        tmp.append(
                            Paragraph('<font face="OpenSans" size="8">%s</font>' % ("" if not iss.tubes.exists() or not iss.tubes.first().time_get else iss.tubes.first().time_get.strftime('%d.%m.%Y')),
                                      styleSheet["BodyText"]))
                        tmp.append(
                            Paragraph('<font face="OpenSans" size="8">%s</font>' % ("Не подтверждено" if not iss.time_confirmation else iss.time_confirmation.strftime('%d.%m.%Y')),
                                      styleSheet["BodyText"]))
                        tmp.append(
                            Paragraph('<font face="OpenSans" size="8">%s</font>' % ("Не подтверждено" if not iss.doc_confirmation else iss.doc_confirmation.get_fio()),
                                      styleSheet["BodyText"]))
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
                                    tmp = []
                                    tmp.append(Paragraph(
                                        '<font face="OpenSansBold" size="8">' + (val["title"] if len(norm_vals) == 0 else "Выделенная культура: " + val["title"]) + "</font>",
                                        styleSheet["BodyText"]))
                                    tmp.append("")
                                    tmp.append("")
                                    tmp.append("")
                                    tmp.append("")
                                    tmp.append("")
                                    data.append(tmp)

                                    if len(norm_vals) > 0:
                                        has_anti = True

                                        tmp = []
                                        tmp.append(Paragraph(
                                            '<font face="OpenSansBold" size="8">%s</font>' % f.title,
                                            styleSheet["BodyText"]))
                                        tmp.append("")
                                        tmp.append("")
                                        tmp.append("")
                                        tmp.append("")
                                        tmp.append("")
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
                                    cw = [int(tw * 0.23),int(tw * 0.11),int(tw * 0.22),int(tw * 0.11),int(tw * 0.22),int(tw * 0.11)]
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
                        tmp = []
                        tmp.append([Paragraph('<font face="OpenSans" size="8">S - чувствителен; R - резистентен; I - промежуточная чувствительность;</font>', styleSheet["BodyText"])])
                        tmp.append("")
                        tmp.append("")
                        tmp.append("")
                        tmp.append("")
                        tmp.append("")
                        data.append(tmp)
                        cw = [int(tw * 0.23), int(tw * 0.11), int(tw * 0.22), int(tw * 0.11), int(tw * 0.22),
                              int(tw * 0.13)]
                        t = Table(data, colWidths=cw)
                        style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                            ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.white),
                                            ('BOX', (0, 0), (-1, -1), 0.8, colors.white),
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
                        t.drawOn(c, px(), pos - ht - 1*mm)
                        pos = pos - ht
                    pos -= 2*mm

            if not dir.is_printed:
                dir.is_printed = True
                from datetime import datetime

                dir.time_print = datetime.now()
                dir.doc_print = request.user.doctorprofile
                dir.save()
            c.showPage()


        c.save()
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
    c.drawCentredString(w / 4 + s, h - 28, "(%s. %s)" % (SettingManager.get("org_address"), SettingManager.get("org_phones"),)) #"(г. Иркутск, б-р. Гагарина, 18. тел: 280-808, 280-809)")
    c.setFont('OpenSans', 10)
    c.drawString(paddingx + s, h - 42, "Результаты анализов")

    c.setFont('OpenSans', 20)
    c.drawString(paddingx + s, h - 28, "№ " + str(obj))

    c.setFont('OpenSans', 10)
    c.drawRightString(s + w / 2 - paddingx, h - 42, "Лечащий врач: " + napr.doc.get_fio())
    c.drawRightString(s + w / 2 - paddingx, h - 54,
                      "Дата: " + maxdate)

    c.drawString(s + paddingx, h - 54, "ФИО пациента: " + napr.client.fio())
    c.drawString(s + paddingx, h - 64, "Номер карты: " + str(napr.client.num))
    c.drawCentredString(w / 4 + s, h - 64, "Пол: " + napr.client.sex)

    # c.drawRightString(s + w/2 - paddingx, h-97, "Дата рождения: " + str(dateformat.format(napr.client.bd(), settings.DATE_FORMAT)) + " (" + str(napr.client.age()) + " лет)")

    c.drawRightString(s + w / 2 - paddingx, h - 64, napr.client.age_s() + " " + "(д.р. " + str(
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
    tmp = []
    tmp.append(Paragraph('<font face="OpenSans" size="7">Исследование</font>', styleSheet["BodyText"]))
    tmp.append(Paragraph('<font face="OpenSans" size="7">Значение</font>', styleSheet["BodyText"]))
    tmp.append(Paragraph('<font face="OpenSans" size="7">Ед. изм.</font>', styleSheet["BodyText"]))
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
            tmp = []
            tmp.append(Paragraph('<font face="OpenSansBold" size="7">' + iss.research.title + "</font>",
                                 styleSheet["BodyText"]))
            result = ""
            if Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).exists():
                result = Result.objects.get(issledovaniye=iss, fraction=fractions[0]).value

            if not iss.doc_confirmation and iss.deferred:
                result = "отложен"
            elif iss.time_save and maxdate != str(dateformat.format(iss.time_save, settings.DATE_FORMAT)):
                result += "<br/>" + str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
            tmp.append(Paragraph('<font face="ChampB" size="8">' + result + "</font>", styleSheet["BodyText"]))
            tmp.append(
                Paragraph('<font face="OpenSans" size="7">&nbsp;&nbsp;&nbsp;' + fractions[0].units + "</font>",
                          styleSheet["BodyText"]))
            if napr.client.sex.lower() == "м":
                tmp.append(Paragraph('<font face="OpenSans" size="7">' + get_r(fractions[0].ref_m) + "</font>",
                                     styleSheet["BodyText"]))
            else:
                tmp.append(Paragraph('<font face="OpenSans" size="7">' + get_r(fractions[0].ref_f) + "</font>",
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
            tmp = [Paragraph('<font face="OpenSansBold" size="7">' + iss.research.title + "</font>",
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
                tmp.append(Paragraph('&nbsp;&nbsp;&nbsp;&nbsp;<font face="OpenSans" size="7">' + f.title + "</font>",
                                     styleSheet["BodyText"]))
                result = ""
                if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
                    result = Result.objects.get(issledovaniye=iss, fraction=f).value
                if not iss.doc_confirmation and iss.deferred:
                    result = "отложен"
                elif iss.time_save and maxdate != str(dateformat.format(iss.time_save, settings.DATE_FORMAT)):
                    result += "<br/>" + str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                tmp.append(Paragraph('<font face="ChampB" size="8">' + result + "</font>", styleSheet["BodyText"]))
                tmp.append(Paragraph('<font face="OpenSans" size="7">&nbsp;&nbsp;&nbsp;' + f.units + "</font>",
                                     styleSheet["BodyText"]))
                if napr.client.sex.lower() == "м":
                    tmp.append(Paragraph('<font face="OpenSans" size="7">' + get_r(f.ref_m) + "</font>",
                                         styleSheet["BodyText"]))
                else:
                    tmp.append(Paragraph('<font face="OpenSans" size="7">' + get_r(f.ref_f) + "</font>",
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
def result_journal_print(request):
    """ Печать журнала подтверждений """
    pw, ph = A4
    paddingx = 30
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="results.pdf"'
    import datetime
    dateo = request.GET["date"]
    date = datetime.date(int(dateo.split(".")[2]), int(dateo.split(".")[1]), int(dateo.split(".")[0]))
    end_date = date + datetime.timedelta(days=1)
    iss_list = Issledovaniya.objects.filter(time_confirmation__gte=date, time_confirmation__lt=end_date,
                                            research__subgroup__podrazdeleniye=request.user.doctorprofile.podrazileniye,
                                            napravleniye__cancel=False)

    from io import BytesIO
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os.path
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    styleSheet = getSampleStyleSheet()
    styles = getSampleStyleSheet()
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Frame, Spacer
    from reportlab.lib.units import mm
    import collections
    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))  # Путь до текущего скрипта

    pdfmetrics.registerFont(
        TTFont('OpenSans', PROJECT_ROOT + '/../static/fonts/OpenSans.ttf'))
    pdfmetrics.registerFont(
        TTFont('Champ', PROJECT_ROOT + '/../static/fonts/Champ.ttf'))
    pdfmetrics.registerFont(
        TTFont('ChampB', PROJECT_ROOT + '/../static/fonts/ChampB.ttf'))
    pdfmetrics.registerFont(
        TTFont('OpenSansBold', PROJECT_ROOT + '/../static/fonts/OpenSans-Bold.ttf'))

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
            self.drawCentredString((A4[0]-25*mm)/2 + 20*mm, ph - 12*mm, request.user.doctorprofile.podrazileniye.title + ", " + dateo)
            page = "Страница %s из %s" % (self._pageNumber, page_count)
            self.saveState()
            self.setStrokeColorRGB(0, 0, 0)
            self.setLineWidth(0.5)
            self.line(20*mm, 24, A4[0] - 5*mm, 24)
            self.setFont('OpenSans', 8)
            self.drawRightString(A4[0]-8*mm, 17, page)
            self.drawString(23*mm, 17, dateo)
            self.restoreState()

    styles["Normal"].fontName = "OpenSans"
    styles["Normal"].fontSize = 12

    from collections import defaultdict
    from reportlab.platypus import PageBreak

    otds = defaultdict(dict)
    clientresults = {}
    for iss in iss_list.order_by("napravleniye__client__family"):
        key = iss.napravleniye.client.family + "-" + str(iss.napravleniye.client.pk)
        if key not in clientresults.keys():
            clientresults[key] = {"directions": {},
                                  "fio": iss.napravleniye.client.shortfio() + "<br/>Карта: " + str(iss.napravleniye.client.num) +
                                         (("<br/>История: " + iss.napravleniye.history_num) if iss.napravleniye.history_num and iss.napravleniye.history_num != "" else "")}
        if iss.napravleniye.pk not in clientresults[key]["directions"]:
            clientresults[key]["directions"][iss.napravleniye.pk] = {"researches": {}}
        # results = Result.objects.filter(issledovaniye=iss)
        if iss.research.pk not in clientresults[key]["directions"][iss.napravleniye.pk]["researches"]:
            clientresults[key]["directions"][iss.napravleniye.pk]["researches"][iss.research.pk] = {
                "title": iss.research.title, "res": []}
        # for result in results:
        #    pass
        for fr in iss.research.fractions_set.all():
            fres = Result.objects.filter(issledovaniye=iss, fraction=fr)
            if fres.exists():
                clientresults[key]["directions"][iss.napravleniye.pk]["researches"][iss.research.pk]["res"].append(
                    fr.title + ": " + fres.first().value)
        otds[iss.napravleniye.doc.podrazileniye.title][key] = clientresults[key]
    i = 0
    # clientresults = collections.OrderedDict(sorted(clientresults.items()))
    for otd in otds.keys():
        data = [[Paragraph('<font face="OpenSans" size="12">' + otd + "</font>", styles["Normal"])]]
        tmp = []
        data_header = ["№", "ФИО", "Направление: Результаты"]
        for v in data_header:
            tmp.append(Paragraph(str(v), styles["Normal"]))
        data.append(tmp)
        clientresults = collections.OrderedDict(sorted(otds[otd].items()))
        for cleint_pk in clientresults.keys():
            client = clientresults[cleint_pk]
            data_tmp = ""
            for dir_pk in client["directions"].keys():
                i += 1
                dir = client["directions"][dir_pk]
                data_tmp += "Направление: " + str(dir_pk) + " | "
                for research_pk in dir["researches"].keys():
                    research_obj = dir["researches"][research_pk]
                    if len(research_obj["res"]) == 1:
                        data_tmp += research_obj["res"][0]
                    else:
                        data_tmp += research_obj["title"] + ":" + "; ".join(research_obj["res"])
                    # data_tmp += ". "
                    data_tmp += "<br/>"
            data.append([Paragraph('<font face="OpenSans" size="8">' + str(i) + "</font>", styles["Normal"]),
                         Paragraph('<font face="OpenSans" size="8">' + client["fio"] + "</font>", styles["Normal"]),
                         Paragraph('<font face="ChampB" size="8">' + data_tmp + "</font>", styles["Normal"])])
        st = TableStyle([('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                         ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                         ('SPAN', (0, 0), (-1, 0)),
                         ('BOX', (0, 0), (-1, -1), 1, colors.black),
                         ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
                         ('LEFTPADDING', (0, 0), (-1, -1), 1),
                         ('TOPPADDING', (0, 2), (-1, -1), 0),
                         ('TOPPADDING', (0, 0), (-1, 1), 2),
                         ('BOTTOMPADDING', (0, 0), (-1, 1), 3),
                         ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                         ('BOTTOMPADDING', (0, 2), (-1, -1), 0), ])
        tw = pw - 25 * mm
        t = Table(data, colWidths=[tw * 0.05, tw * 0.15, tw * 0.8])
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
    result = {"results": {}}
    if request.method == "GET":
        issledovaniye = Issledovaniya.objects.get(pk=int(request.GET["iss_id"]))
        results = Result.objects.filter(issledovaniye=issledovaniye)
        for v in results:
            result["results"][str(v.fraction.pk)] = v.value
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
    else:
        researches = json.loads(request.GET["researches"])
        day = request.GET["date"]
    day1 = datetime.date(int(day.split(".")[2]), int(day.split(".")[1]),int(day.split(".")[0]))
    day2 = day1 + timedelta(days=1)
    directions = defaultdict(list)
    for dir in Napravleniya.objects.filter(issledovaniya__time_confirmation__range=(day1, day2),
                                           issledovaniya__research__subgroup__podrazdeleniye=request.user.doctorprofile.podrazileniye,
                                           issledovaniya__research_id__in=researches).order_by("pk"):

        if dir.pk not in directions[dir.doc.podrazileniye.title]:
            directions[dir.doc.podrazileniye.title].append(dir.pk)
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
