from collections import defaultdict

import datetime
import re

from django.db.models import Func
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User, Group
from django.utils import dateformat

from appconf.manager import SettingManager
from clients.models import CardBase
from laboratory import settings
from rmis_integration.client import Client
from users.models import DoctorProfile
from podrazdeleniya.models import Podrazdeleniya
from directions.models import IstochnikiFinansirovaniya, TubesRegistration, Issledovaniya, Napravleniya
from django.views.decorators.csrf import csrf_exempt
from researches.models import Tubes
from laboratory.decorators import group_required
import slog.models as slog
from django.http import HttpResponse
import simplejson as json
import directory.models as directory


@login_required
def dashboard(request):  # Представление панели управления
    if not request.is_ajax():
        from laboratory import settings
        dt = ""
        menu = []
        groups = [str(x) for x in request.user.groups.all()]
        pages = [
            {"url": "/mainmenu/directions", "title": "Направления", "nt": False,
             "access": ["Лечащий врач", "Оператор лечащего врача"]},
            {"url": "/mainmenu/direction/info", "title": "История направления", "nt": False,
             "access": ["Лечащий врач", "Оператор лечащего врача", "Лаборант", "Врач-лаборант", "Просмотр журнала"]},
            {"url": "/mainmenu/results_fastprint", "title": "Печать результатов", "nt": False,
             "access": ["Лечащий врач", "Оператор лечащего врача"]},
            {"url": "/mainmenu/biomaterial/get", "title": "Забор биоматериала", "nt": False,
             "access": ["Заборщик биоматериала"]},
            {"url": "/mainmenu/receive", "title": "Приём биоматериала", "nt": False,
             "access": ["Получатель биоматериала"]},
            {"url": "/mainmenu/receive/one_by_one", "title": "Приём биоматериала по одному", "nt": False,
             "access": ["Получатель биоматериала"]},
            {"url": "/mainmenu/receive/journal_form", "title": "Журнал приёма", "nt": False,
             "access": ["Получатель биоматериала"]},
            {"url": "/results/enter", "title": "Ввод результатов", "nt": False,
             "access": ["Врач-лаборант", "Лаборант", "Сброс подтверждений результатов"]},
            {"url": "/construct/menu", "title": "Конструктор справочника", "nt": False, "access": []},
            {"url": "/statistic", "title": "Статистика", "nt": False,
             "access": ["Просмотр статистики", "Врач-лаборант"]},
            {"url": "/mainmenu/results_history", "title": "Поиск", "nt": False,
             "access": ["Лечащий врач", "Оператор лечащего врача", "Врач-лаборант", "Лаборант"]},
            {"url": "/mainmenu/discharge", "title": "Выписки", "nt": False,
             "access": ["Загрузка выписок", "Поиск выписок"]},
            {"url": "/mainmenu/create_user", "title": "Создать пользователя", "nt": False,
             "access": ["Создание и редактирование пользователей"]},
            {"url": "/mainmenu/change_password", "title": "Настройка профилей пользователей", "nt": False,
             "access": ["Создание и редактирование пользователей"]},
            {"url": "/mainmenu/create_podr", "title": "Управление подразделениями", "nt": False,
             "access": ["Создание и редактирование пользователей"]},
            {"url": "/mainmenu/view_log", "title": "Просмотр журнала", "nt": False, "access": ["Просмотр журнала"]},
            {"url": "/admin", "title": "Администрирование L2", "nt": False, "access": []},
            {"url": "/silk/", "title": "Профилирование", "nt": False, "access": []},
        ]

        if settings.LDAP and settings.LDAP["enable"]:
            pages.append({"url": "/mainmenu/ldap_sync", "title": "Синхронизация с LDAP", "nt": False, "access": []})
        pages.append({"url": "/mainmenu/utils", "title": "Инструменты", "keys": "Alt+l", "nt": False, "access": []})

        if SettingManager.get("home_page", default="http://home") != "false":
            pages.append(
                {"url": SettingManager.get(key="home_page", default="http://home"), "title": "Домашняя страница",
                 "nt": True, "access": ["*"]})

        groups_set = set(groups)
        for page in pages:
            if not request.user.is_superuser and "*" not in page["access"] and len(
                            groups_set & set(page["access"])) == 0:
                continue
            menu.append(page)

        menu_st = [menu[i:i + 4] for i in range(0, len(menu), 4)]
        return render(request, 'dashboard.html', {"menu": menu_st})
    return HttpResponse("OK")


@login_required
@group_required("Просмотр журнала")
def view_log(request):
    import slog.models as slog
    types = []
    for t in slog.Log.TYPES:
        types.append({"pk": t[0], "val": t[1]})
    return render(request, 'dashboard/manage_view_log.html',
                  {"users": DoctorProfile.objects.all().order_by("fio"), "types": types})


@csrf_exempt
@login_required
@group_required("Создание и редактирование пользователей")
def change_password(request):
    if request.method == "POST":
        doc = DoctorProfile.objects.get(pk=request.POST["pk"])
        if request.POST.get("apply_groups") == "1":
            doc.user.groups.clear()
            for g in json.loads(request.POST.get("groups", "[]")):
                group = Group.objects.get(pk=g)
                doc.user.groups.add(group)
        elif request.POST.get("update_fio") == "1":
            doc.fio = request.POST.get("fio", "ФИО")
            doc.save()
        else:
            doc.podrazdeleniye = Podrazdeleniya.objects.get(pk=request.POST["podr"])
            doc.save()
        return HttpResponse(json.dumps({"ok": True}), content_type="application/json")
    if request.is_ajax():
        doc = DoctorProfile.objects.get(pk=request.GET["pk"])
        groups = [{"pk": str(x.pk), "title": x.name} for x in doc.user.groups.all()]
        return HttpResponse(json.dumps({"groups": groups, "fio": doc.fio, "username": doc.user.username}),
                            content_type="application/json")
    otds = {}
    podr = Podrazdeleniya.objects.all().order_by("title")
    for x in podr:
        otds[x.title] = []
        for y in DoctorProfile.objects.filter(podrazdeleniye=x).order_by('fio'):
            otds[x.title].append(
                {"pk": y.pk, "fio": y.get_fio(), "username": y.user.username, "podr": y.podrazdeleniye.pk})
    return render(request, 'dashboard/change_password.html', {"otds": otds, "podrs": podr, "g": Group.objects.all()})


@csrf_exempt
@login_required
@group_required("Создание и редактирование пользователей")
def update_pass(request):
    userid = int(request.POST.get("pk", "-1"))
    password = request.POST.get("pass", "")
    if request.method == "POST" and userid >= 0 and len(password) > 0:
        user = DoctorProfile.objects.get(pk=userid).user
        user.set_password(password)
        user.save()
        return HttpResponse(json.dumps({"ok": True}), content_type="application/json")
    return HttpResponse(json.dumps({"ok": False}), content_type="application/json")


from django.utils import timezone


@csrf_exempt
@login_required
@group_required("Просмотр журнала")
def load_logs(request):
    import slog.models as slog
    result = {"data": []}

    if request.method == "POST":
        check_new = int(request.POST["checknew"])
        states = json.loads(request.POST["searchdata"])
    else:
        check_new = int(request.GET["checknew"])
        states = json.loads(request.GET["searchdata"])

    obj = slog.Log.objects.all()
    if states["user"] != -1:
        obj = obj.filter(user__pk=states["user"])
    if states["type"] != -1:
        obj = obj.filter(type=states["type"])
    if states["pk"] != "-1":
        obj = obj.filter(key__contains=states["pk"])

    if check_new == 0:
        if request.method == "POST":
            offset = int(request.POST["offset"])
            size = int(request.POST["size"])
        else:
            offset = int(request.GET["offset"])
            size = int(request.GET["size"])
        for row in obj.order_by("-pk")[offset:size + offset]:
            tmp_object = {"id": row.pk, "user_fio": row.user.get_fio() + ", " + row.user.user.username,
                          "user_pk": row.user.pk, "key": row.key, "body": row.body, "type": row.get_type_display(),
                          "time": timezone.localtime(row.time).strftime("%d.%m.%Y %X")}
            result["data"].append(tmp_object)
    else:
        if request.method == "POST":
            pkgt = int(request.POST["last_n"])
        else:
            pkgt = int(request.GET["last_n"])

        for row in obj.filter(pk__gt=pkgt).order_by("pk"):
            tmp_object = {"id": row.pk, "user_fio": row.user.get_fio() + ", " + row.user.user.username,
                          "user_pk": row.user.pk, "key": row.key, "body": row.body, "type": row.get_type_display(),
                          "time": timezone.localtime(row.time).strftime("%d.%m.%Y %X")}
            result["data"].append(tmp_object)

    result["s"] = states
    return HttpResponse(json.dumps(result), content_type="application/json")


# @cache_page(60 * 15)
@login_required
@group_required("Заборщик биоматериала")
def researches_control(request):
    tubes = Tubes.objects.all()
    return render(request, 'dashboard/get_biomaterial.html', {"tubes": tubes})


@login_required
@group_required("Получатель биоматериала")
def receive_journal_form(request):
    lab = Podrazdeleniya.objects.get(pk=request.GET.get("lab_pk", request.user.doctorprofile.podrazdeleniye.pk))
    labs = Podrazdeleniya.objects.filter(isLab=True, hide=False).order_by("title")
    if not lab.isLab:
        lab = labs[0]
    groups = directory.ResearchGroup.objects.filter(lab=lab)
    podrazdeleniya = Podrazdeleniya.objects.filter(isLab=False, hide=False).order_by("title")
    return render(request, 'dashboard/receive_journal.html',
                  {"groups": groups, "podrazdeleniya": podrazdeleniya, "labs": labs, "lab": lab})


@csrf_exempt
@login_required
@group_required("Сброс подтверждений результатов", "Врач-лаборант", "Лаборант")
def confirm_reset(request):
    result = {"ok": False, "msg": "Ошибка"}

    if "pk" in request.POST.keys() or "pk" in request.GET.keys():
        if request.method == "POST":
            pk = int(request.POST["pk"])
        else:
            pk = int(request.GET["pk"])

        if Issledovaniya.objects.filter(pk=pk).exists():
            iss = Issledovaniya.objects.get(pk=pk)

            import time
            ctp = int(
                0 if not iss.time_confirmation else int(time.mktime(iss.time_confirmation.timetuple()))) + 8 * 60 * 60
            ctime = int(time.time())
            cdid = -1 if not iss.doc_confirmation else iss.doc_confirmation.pk
            if (ctime - ctp < SettingManager.get(
                    "lab_reset_confirm_time_min") * 60 and cdid == request.user.doctorprofile.pk) or request.user.is_superuser or "Сброс подтверждений результатов" in [
                str(x) for x in request.user.groups.all()]:
                predoc = {"fio": iss.doc_confirmation.get_fio(), "pk": iss.doc_confirmation.pk,
                          "direction": iss.napravleniye.pk}
                iss.doc_confirmation = iss.time_confirmation = None
                iss.save()
                if iss.napravleniye.result_rmis_send:
                    c = Client()
                    c.directions.delete_services(iss.napravleniye, request.user.doctorprofile)
                result = {"ok": True}
                slog.Log(key=pk, type=24, body=json.dumps(predoc), user=request.user.doctorprofile).save()
            else:
                result["msg"] = "Сброс подтверждения разрешен в течении %s минут" % (
                    str(SettingManager.get("lab_reset_confirm_time_min")))
    return HttpResponse(json.dumps(result), content_type="application/json")


@login_required
@group_required("Создание и редактирование пользователей")
def create_user(request):  # Страница создания пользователя
    registered = False
    podr = Podrazdeleniya.objects.filter(hide=False).order_by("title")  # Получение всех подразделений
    podrpost = 0
    groups = Group.objects.all()  # Получение всех групп
    if request.method == 'POST':
        username = request.POST['username']  # Имя пользователя
        password = request.POST['password']  # Пароль
        podrpost = request.POST['podr']  # Подразделение
        fio = request.POST['fio']  # ФИО
        groups_user = request.POST.getlist('groups')  # Группы

        if username and password and fio:  # Проверка наличия всех полей
            if not User.objects.filter(username=username).exists():  # Проверка существования пользователя
                user = User.objects.create_user(username)  # Создание пользователя
                user.set_password(password)  # Установка пароля
                user.is_active = True  # Активация пользователя
                user.save()  # Сохранение пользователя
                for g in groups_user:  # Перебор выбранных групп
                    gTmp = Group.objects.get(pk=g)  # Выбор группы
                    gTmp.user_set.add(user)  # Установка группы
                profile = DoctorProfile.objects.create()  # Создание профиля
                profile.user = user  # Привязка профиля к пользователю
                profile.fio = fio  # ФИО
                profile.podrazdeleniye = podr.get(pk=podrpost)  # Привязка подразделения
                profile.isLDAP_user = False
                profile.save()  # Сохранение профиля
                registered = True
                slog.Log(key=str(profile.pk), user=request.user.doctorprofile, type=16, body=json.dumps(
                    {"username": username, "password": "(скрыт)", "podr": podrpost, "fio": fio})).save()
            else:
                return render(request, 'dashboard/create_user.html',
                              {'error': True, 'mess': 'Пользователь с таким именем пользователя уже существует',
                               'uname': username, 'fio': fio, 'status': registered, 'podr': podr, 'podrpost': podrpost,
                               'g': groups})  # Вывод
        else:
            return render(request, 'dashboard/create_user.html',
                          {'error': True, 'mess': 'Данные введены неверно', 'uname': username, 'fio': fio,
                           'status': registered, 'podr': podr, 'podrpost': podrpost, 'g': groups})  # Вывод

    return render(request, 'dashboard/create_user.html',
                  {'error': False, 'mess': '', 'uname': '', 'fio': '', 'status': registered, 'podr': podr,
                   'podrpost': podrpost, 'g': groups})  # Вывод


@csrf_exempt
@login_required
@group_required("Создание и редактирование пользователей")
def create_pod(request):
    """ Создание подразделения """
    p = False
    e = True
    mess = ''
    podr = Podrazdeleniya.objects.all().order_by("pk")  # Выбор подразделения
    if request.method == 'POST':  # Проверка типа запроса
        if request.POST.get("update_podr", "0") == "1":
            pd = Podrazdeleniya.objects.get(pk=request.POST.get("pk"))
            if "title" in request.POST:
                pd.title = request.POST["title"]
            if "hide" in request.POST:
                pd.hide = request.POST["hide"] == "true"
            if "is_lab" in request.POST:
                pd.isLab = request.POST["is_lab"] == "true"
            pd.save()
            return HttpResponse("{}", content_type="application/json")
        title = request.POST['title']  # Получение названия
        if title:  # Если название есть
            if not Podrazdeleniya.objects.filter(title=title).exists():  # Если название не существует
                pd = Podrazdeleniya.objects.create()  # Создание подразделения
                pd.title = title
                pd.save()  # Сохранение подразделения
                p = True
                e = False
                slog.Log(key=str(pd.pk), user=request.user.doctorprofile, type=17,
                         body=json.dumps({"title": title})).save()
            else:
                mess = "Такое подразделение уже есть"
        else:
            mess = "Название заполнено некорректно"
    else:
        e = False
    return render(request, 'dashboard/create_podr.html',
                  {'error': e, 'mess': mess, 'title': '', 'status': p, 'podr': podr})


@login_required
@staff_member_required
def ldap_sync(request):
    """ Страница синхронизации с LDAP """
    return render(request, 'dashboard/ldap_sync.html')


def get_fin():
    fin = []
    for b in CardBase.objects.filter(hide=False):
        o = {"pk": b.pk, "sources": []}
        for f in IstochnikiFinansirovaniya.objects.filter(base=b, hide=False):
            o["sources"].append({"pk": f.pk, "title": f.title})
        fin.append(o)
    return fin


# @cache_page(60 * 15)
@login_required
@group_required("Лечащий врач", "Оператор лечащего врача")
def directions(request):
    """ Страница создания направлений """
    from users.models import AssignmentTemplates, AssignmentResearches
    from django.db.models import Q
    podr = Podrazdeleniya.objects.filter(isLab=True)
    oper = "Оператор лечащего врача" in request.user.groups.values_list('name', flat=True)
    docs = list()
    podrazdeleniya = Podrazdeleniya.objects.filter(isLab=False, hide=False).order_by("title")
    if oper:
        p = podrazdeleniya.first()
        if not request.user.doctorprofile.podrazdeleniye.isLab and not request.user.doctorprofile.podrazdeleniye.hide:
            p = request.user.doctorprofile.podrazdeleniye
        docs = DoctorProfile.objects.filter(podrazdeleniye=p,
                                            user__groups__name="Лечащий врач").order_by("fio")
    users = []
    for p in podrazdeleniya:
        pd = {"pk": p.pk, "title": p.title, "docs": []}
        for d in DoctorProfile.objects.filter(podrazdeleniye=p,
                                              user__groups__name="Лечащий врач").order_by("fio"):
            pd["docs"].append({"pk": d.pk, "fio": d.get_fio()})
        users.append(pd)
    rmis_base = CardBase.objects.filter(is_rmis=True, hide=False)
    rid = -1 if not rmis_base.exists() else rmis_base[0].pk
    templates = {}
    for t in AssignmentTemplates.objects.filter(Q(doc__isnull=True, podrazdeleniye__isnull=True) |
                                                        Q(doc=request.user.doctorprofile) |
                                                        Q(podrazdeleniye=request.user.doctorprofile.podrazdeleniye)):
        tmp_template = defaultdict(list)
        for r in AssignmentResearches.objects.filter(template=t):
            tmp_template[r.research.get_podrazdeleniye().pk].append(r.research.pk)
        templates[t.pk] = {"values": tmp_template, "title": t.title, "for_doc": t.doc is not None,
                           "for_podr": t.podrazdeleniye is not None}
    return render(request, 'dashboard/directions.html', {'labs': podr,
                                                         'fin': get_fin(),
                                                         "operator": oper, "docs": docs, "notlabs": podrazdeleniya,
                                                         "rmis_uid": request.GET.get("rmis_uid", ""),
                                                         "rmis_base_id": rid,
                                                         "users": json.dumps(users),
                                                         "templates": json.dumps(templates),
                                                         "material_types": directory.MaterialVariants.objects.all()})


@login_required
@group_required("Лечащий врач", "Оператор лечащего врача", "Врач-лаборант", "Лаборант")
def results_history(request):
    podr = Podrazdeleniya.objects.filter(isLab=True)

    podrazdeleniya = Podrazdeleniya.objects.filter(isLab=False, hide=False).order_by("title")
    users = []
    for p in podrazdeleniya:
        pd = {"pk": p.pk, "title": p.title, "docs": []}
        for d in DoctorProfile.objects.filter(podrazdeleniye=p,
                                              user__groups__name="Лечащий врач"):
            pd["docs"].append({"pk": d.pk, "fio": d.get_fio()})
        users.append(pd)
    return render(request, 'dashboard/results_history.html', {'labs': podr,
                                                              'fin': get_fin(),
                                                              "notlabs": podrazdeleniya,
                                                              "users": json.dumps(users)})


@login_required
@group_required("Лечащий врач", "Загрузка выписок", "Поиск выписок")
def discharge(request):
    podr = Podrazdeleniya.objects.filter(isLab=True)

    podrazdeleniya = Podrazdeleniya.objects.filter(isLab=False, hide=False).order_by("title")
    users = []
    for p in podrazdeleniya:
        pd = {"pk": p.pk, "title": p.title, "docs": []}
        for d in DoctorProfile.objects.filter(podrazdeleniye=p,
                                              user__groups__name="Лечащий врач"):
            pd["docs"].append({"pk": d.pk, "fio": d.fio})
        users.append(pd)
    return render(request, 'dashboard/discharge.html', {'labs': podr,
                                                        'fin_poli': IstochnikiFinansirovaniya.objects.filter(
                                                            istype="poli"),
                                                        'fin_stat': IstochnikiFinansirovaniya.objects.filter(
                                                            istype="stat"),
                                                        "notlabs": podrazdeleniya,
                                                        "users": json.dumps(users)})


import podrazdeleniya.models as pod


@csrf_exempt
@login_required
@group_required("Лечащий врач", "Загрузка выписок")
def discharge_add(request):
    r = {"ok": True}
    if request.method == "POST":
        import discharge.models as discharge
        client_surname = request.POST.get("client_surname", "").strip()
        client_name = request.POST.get("client_name", "").strip()
        client_patronymic = request.POST.get("client_patronymic", "").strip()
        client_birthday = request.POST.get("client_birthday", "").strip()
        client_sex = request.POST.get("client_sex", "").strip()
        client_cardnum = request.POST.get("client_cardnum", "").strip()
        client_historynum = request.POST.get("client_historynum", "").strip()

        otd = pod.Podrazdeleniya.objects.get(pk=int(request.POST.get("otd", "-1")))
        doc_fio = request.POST.get("doc_fio", "").strip()

        if "" not in [client_surname, client_name, client_patronymic] and request.FILES.get('file', "") != "":
            obj = discharge.Discharge(client_surname=client_surname,
                                      client_name=client_name,
                                      client_patronymic=client_patronymic,
                                      client_birthday=client_birthday,
                                      client_sex=client_sex,
                                      client_cardnum=client_cardnum,
                                      client_historynum=client_historynum,
                                      otd=otd,
                                      doc_fio=doc_fio,
                                      creator=request.user.doctorprofile,
                                      file=request.FILES["file"])
            obj.save()
            slog.Log(key=obj.pk, type=1000, body=json.dumps({"client_surname": client_surname,
                                                             "client_name": client_name,
                                                             "client_patronymic": client_patronymic,
                                                             "client_birthday": client_birthday,
                                                             "client_sex": client_sex,
                                                             "client_cardnum": client_cardnum,
                                                             "client_historynum": client_historynum,
                                                             "otd": otd.title + ", " + str(otd.pk),
                                                             "doc_fio": doc_fio,
                                                             "file": obj.file.name}),
                     user=request.user.doctorprofile).save()
    return HttpResponse(json.dumps(r), content_type="application/json")


@csrf_exempt
@login_required
@group_required("Лечащий врач", "Поиск выписок")
def discharge_search(request):
    r = {"rows": []}
    if request.method == "GET":
        import discharge.models as discharge
        date_start = request.GET["date_start"]
        date_end = request.GET["date_end"]
        date_start = datetime.date(int(date_start.split(".")[2]), int(date_start.split(".")[1]),
                                   int(date_start.split(".")[0]))
        date_end = datetime.date(int(date_end.split(".")[2]), int(date_end.split(".")[1]),
                                 int(date_end.split(".")[0])) + datetime.timedelta(1)
        query = request.GET.get("q", "")
        otd_pk = int(request.GET.get("otd", "-1"))
        doc_fio = request.GET.get("doc_fio", "")

        slog.Log(key=query, type=1001, body=json.dumps({"date_start": request.GET["date_start"],
                                                        "date_end": request.GET["date_end"],
                                                        "otd_pk": otd_pk,
                                                        "doc_fio": doc_fio}),
                 user=request.user.doctorprofile).save()

        filter_type = "any"
        family = ""
        name = ""
        twoname = ""
        bdate = ""

        if query.isdigit():
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

        rows = discharge.Discharge.objects.filter(created_at__range=(date_start, date_end,),
                                                  doc_fio__icontains=doc_fio)

        if otd_pk > -1:
            rows = rows.filter(otd__pk=otd_pk)

        if filter_type == "fio":
            rows = rows.filter(client_surname__contains=family,
                               client_name__contains=name,
                               client_patronymic__contains=twoname,
                               client_birthday__contains=bdate)

        if filter_type == "card_number":
            rows = rows.filter(client_cardnum=int(query))
        import os
        for row in rows.order_by("-created_at"):
            r["rows"].append({"date": str(dateformat.format(row.created_at.date(), settings.DATE_FORMAT)),
                              "client": {
                                  "surname": row.client_surname,
                                  "name": row.client_name,
                                  "patronymic": row.client_patronymic,
                                  "sex": row.client_sex,
                                  "birthday": row.client_birthday
                              },
                              "otd": row.otd.title,
                              "doc_fio": row.doc_fio,
                              "filename": os.path.basename(row.file.name),
                              "fileurl": row.file.url})

    return HttpResponse(json.dumps(r), content_type="application/json")


@login_required
@group_required("Создание и редактирование пользователей")
def users_count(request):
    """ Получение количества пользователей """
    result = {"all": User.objects.all().count(), "ldap": DoctorProfile.objects.filter(isLDAP_user=True).count()}

    return HttpResponse(json.dumps(result), content_type="application/json")


@login_required
@group_required("Лечащий врач", "Оператор лечащего врача", "Врач-лаборант", "Лаборант")
def results_history_search(request):
    result = []
    type = request.GET.get("type", "otd")
    day = request.GET.get("date", datetime.datetime.today().strftime('%d.%m.%Y'))

    day1 = datetime.date(int(day.split(".")[2]), int(day.split(".")[1]), int(day.split(".")[0]))
    day2 = day1 + datetime.timedelta(days=1)

    import directions.models as d
    if type == "otd":
        collect = d.Napravleniya.objects.filter(issledovaniya__doc_confirmation__isnull=False,
                                                issledovaniya__time_confirmation__range=(day1, day2),
                                                doc__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)
    else:
        collect = d.Napravleniya.objects.filter(issledovaniya__doc_confirmation__isnull=False,
                                                issledovaniya__time_confirmation__range=(day1, day2),
                                                doc=request.user.doctorprofile)

    for dir in collect.order_by("doc", "client"):
        dpk = dir.pk
        if all([x.doc_confirmation is not None for x in d.Issledovaniya.objects.filter(napravleniye__pk=dpk)]):
            if dpk not in result:
                result.append(dpk)

    return HttpResponse(json.dumps(result), content_type="application/json")


@login_required
@group_required("Получатель биоматериала")
def dashboard_from(request):
    """ Получение отделений и кол-ва пробирок """
    date_start = request.GET["datestart"]
    date_end = request.GET["dateend"]
    filter_type = request.GET.get("type", "wait")
    import datetime
    date_start = datetime.date(int(date_start.split(".")[2]), int(date_start.split(".")[1]),
                               int(date_start.split(".")[0]))
    date_end = datetime.date(int(date_end.split(".")[2]), int(date_end.split(".")[1]),
                             int(date_end.split(".")[0])) + datetime.timedelta(1)
    if request.GET.get("get_labs", "false") == "true":
        result = {}
        for lab in Podrazdeleniya.objects.filter(isLab=True, hide=False):
            tubes_list = TubesRegistration.objects.filter(doc_get__podrazdeleniye__hide=False,
                                                          doc_get__podrazdeleniye__isLab=False,
                                                          time_get__range=(date_start, date_end),
                                                          issledovaniya__research__podrazdeleniye=lab)
            if filter_type == "not_received":
                tubes_list = tubes_list.filter(doc_recive__isnull=True).exclude(notice="")
            elif filter_type == "received":
                tubes_list = tubes_list.filter(doc_recive__isnull=False)
            else:
                tubes_list = tubes_list.filter(notice="", doc_recive__isnull=True)
            tubes = tubes_list.distinct().count()
            result[lab.pk] = tubes
        return HttpResponse(json.dumps(result), content_type="application/json")
    result = {}
    podrazdeleniya = Podrazdeleniya.objects.filter(isLab=False, hide=False).order_by("title")
    lab = Podrazdeleniya.objects.get(pk=request.GET["lab"])
    i = 0
    for podr in podrazdeleniya:
        i += 1
        tubes_list = TubesRegistration.objects.filter(doc_get__podrazdeleniye=podr,
                                                      time_get__range=(date_start, date_end),
                                                      issledovaniya__research__podrazdeleniye=lab)
        if filter_type == "not_received":
            tubes_list = tubes_list.filter(doc_recive__isnull=True).exclude(notice="")
        elif filter_type == "received":
            tubes_list = tubes_list.filter(doc_recive__isnull=False)
        else:
            tubes_list = tubes_list.filter(notice="", doc_recive__isnull=True)
        result[i] = {"tubes": tubes_list.distinct().count(),
                     "title": podr.title, "pk": podr.pk}

    return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
@login_required
@staff_member_required
def users_dosync(request):
    """ Выполнение синхронизации с LDAP """
    from ldap3 import Server, Connection, SIMPLE, SYNC, ALL_ATTRIBUTES, SUBTREE, ALL
    from laboratory import settings

    result = {}

    s = Server(settings.LDAP["server"]["host"], port=settings.LDAP["server"]["port"], get_info=ALL)
    c = Connection(s, auto_bind=True, user=settings.LDAP["server"]["user"],
                   password=settings.LDAP["server"]["password"], client_strategy=SYNC, authentication=SIMPLE,
                   check_names=True)

    result_t = ""

    groups = {}
    c.search(search_base=settings.LDAP["base"],
             search_filter='(&(objectClass=person))',
             search_scope=SUBTREE,
             attributes=ALL_ATTRIBUTES,
             get_operational_attributes=True)
    resp = json.loads(c.response_to_json())
    i = 0
    for ldap_user in resp["entries"]:
        if "uidNumber" not in ldap_user["attributes"].keys() or "uid" not in ldap_user[
            "attributes"].keys() or "userPassword" not in ldap_user["attributes"].keys() or "displayName" not in \
                ldap_user["attributes"].keys():
            continue

        if Podrazdeleniya.objects.filter(gid_n=int(ldap_user["attributes"]["gidNumber"])).exists():
            pod = Podrazdeleniya.objects.get(gid_n=int(ldap_user["attributes"]["gidNumber"]))
            pod.title = ldap_user["attributes"]["ou"][0]
            pod.save()
        else:
            pod = Podrazdeleniya(title=ldap_user["attributes"]["ou"][0],
                                 gid_n=int(ldap_user["attributes"]["gidNumber"]))
            pod.save()

        i += 1
        active = False
        if ldap_user["attributes"]["accountStatus"] == "active":
            active = True
        dn = ldap_user["attributes"]["displayName"]

        username = ldap_user["attributes"]["uid"][0]
        password = ldap_user["attributes"]["userPassword"][0]

        if not User.objects.filter(username=username).exists():  # Проверка существования пользователя
            user = User.objects.create_user(username)  # Создание пользователя
            user.set_password(password)  # Установка пароля
            user.is_active = active
            user.save()  # Сохранение пользователя

            profile = DoctorProfile.objects.create()  # Создание профиля
            profile.user = user  # Привязка профиля к пользователю
            profile.podrazdeleniye = pod

        else:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_active = active
            user.save()
            profile = DoctorProfile.objects.get(user=user)
        emp = ldap_user["attributes"]["employeeType"][0].lower()
        profile.isLDAP_user = True
        profile.fio = dn
        profile.save()
    c.unbind()
    return HttpResponse(json.dumps(groups), content_type="application/json")


@login_required
def dir_multiprint(request):
    """ Страница пакетной печати направлений """
    return render(request, 'dashboard/dir_multiprint.html')


@login_required
def researches_from_directions(request):
    pk = json.loads(request.GET.get("pk", "[]"))
    data = defaultdict(list)
    for i in Issledovaniya.objects.filter(napravleniye__pk__in=pk, research__hide=False):
        data[i.research.podrazdeleniye.pk].append(i.research.pk)
    return HttpResponse(json.dumps(data), content_type="application/json")


@login_required
def direction_info(request):
    if request.is_ajax():
        yesno = {True: "да", False: "нет"}
        data = []
        pk = request.GET.get("pk", "-1")

        try:
            pk = int(pk)
        except ValueError:
            pk = -1

        if pk != -1 and Napravleniya.objects.filter(pk=pk).exists():
            dir = Napravleniya.objects.get(pk=pk)
            data.append({'type': "Направление №%s" % pk, 'events': [
                [
                    ["title", timezone.localtime(dir.data_sozdaniya).strftime("%d.%m.%Y %X") + " Направление создано"],
                    ["Создатель", get_userdata(dir.doc_who_create)],
                    ["От имени", get_userdata(dir.doc)],
                    ["Пациент", "%s, %s, Пол: %s" % (dir.client.individual.fio(), dir.client.individual.bd(), dir.client.individual.sex)],
                    ["Карта", "%s %s" % (dir.client.number, dir.client.base.title)],
                    ["Архив", yesno[dir.client.is_archive]],
                    ["Источник финансирования", dir.istochnik_f.title],
                    ["Диагноз", dir.diagnos],
                    ["Направление отправлено в РМИС", yesno[dir.rmis_number not in ["", None, "NONERMIS"]]],
                    ["Направление привязано к случаю РМИС", yesno[dir.rmis_case_id not in ["", None, "NONERMIS"]]],
                    ["Направление привязано к записи отделения госпитализации РМИС", yesno[dir.rmis_hosp_id not in ["", None, "NONERMIS"]]],
                    ["Результат отправлен в РМИС", yesno[dir.result_rmis_send]]
                ]
            ]})
            for tube in TubesRegistration.objects.filter(issledovaniya__napravleniye=dir).distinct():
                d = {"type": "Пробирка №%s" % tube.pk, "events": []}
                if tube.time_get is not None:
                    d["events"].append([
                        ["title", timezone.localtime(tube.time_get).strftime("%d.%m.%Y %X") + " Забор"],
                        ["Заборщик", get_userdata(tube.doc_get)]
                    ])
                for l in slog.Log.objects.filter(key=str(tube.pk), type__in=(4000, 12, 11)).distinct():
                    tdata = [["Приёмщик", get_userdata(l.user)], ["title", timezone.localtime(l.time).strftime("%d.%m.%Y %X") + " " + l.get_type_display() + " (#%s)" % l.pk]]
                    if l.body and l.body != "":
                        tdata.append(["json_data", l.body])
                    d["events"].append(tdata)
                data.append(d)
            for iss in Issledovaniya.objects.filter(napravleniye=dir):
                d = {'type': "Исследование: %s (#%s)" % (iss.research.title, iss.pk), 'events': []}
                for l in slog.Log.objects.filter(key=str(iss.pk), type__in=(13, 14, 24)).distinct():
                    tdata = [["Исполнитель", get_userdata(l.user)], ["title", timezone.localtime(l.time).strftime("%d.%m.%Y %X") + " " + l.get_type_display() + " (#%s)" % l.pk]]
                    if l.body and l.body != "" and l.type != 24:
                        tdata.append(["json_data", l.body])
                    d["events"].append(tdata)
                data.append(d)
        return HttpResponse(json.dumps(data), content_type="application/json")
    return render(request, 'dashboard/direction_info.html')


def get_userdata(doc: DoctorProfile):
    if doc is None:
        return ""
    return "%s (%s) - %s" % (doc.fio, doc.user.username, doc.podrazdeleniye.title)
