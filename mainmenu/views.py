import datetime
import re
from collections import defaultdict
from urllib.parse import urljoin

import simplejson as json
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import dateformat
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

import directory.models as directory
import podrazdeleniya.models as pod
import slog.models as slog
from api.prefetch import prefetch
from appconf.manager import SettingManager
from clients.models import CardBase
from directions.models import IstochnikiFinansirovaniya, TubesRegistration, Issledovaniya, Napravleniya
from laboratory import settings
from laboratory.decorators import group_required
from laboratory.utils import strdatetime
from mainmenu.rproxy import proxy_view
from podrazdeleniya.models import Podrazdeleniya
from researches.models import Tubes
from rmis_integration.client import Client
from users.models import DoctorProfile
from utils.dates import try_parse_range


@login_required
def dashboard(request):
    if not request.is_ajax():
        return render(
            request,
            'dashboard.html',
            {
                "rmis": SettingManager.get("rmis_enabled", default='false', default_type='b'),
                "mis_module": SettingManager.get("mis_module", default='false', default_type='b'),
                "paraclinic": SettingManager.get("paraclinic_module", default='false', default_type='b'),
                "region": SettingManager.get("region", default='38', default_type='s'),
            },
        )
    return HttpResponse("OK")


@login_required
@group_required("Просмотр журнала")
def view_log(request):
    import slog.models as slog

    types = []
    for t in slog.Log.TYPES:
        types.append({"pk": t[0], "val": t[1]})
    return render(request, 'dashboard/manage_view_log.html', {"users": DoctorProfile.objects.all().order_by("fio"), "types": types})


@login_required
@group_required("Создание и редактирование пользователей")
def profiles(request):
    return render(request, 'dashboard/profiles.html')


@csrf_exempt
@login_required
@group_required("Создание и редактирование пользователей")
def change_password(request):
    if request.method == "POST":
        if not request.user.is_superuser:
            doc = DoctorProfile.objects.get(pk=request.POST["pk"], user__is_superuser=False)
        else:
            doc = DoctorProfile.objects.get(pk=request.POST["pk"])
        if request.POST.get("apply_groups") == "1":
            doc.user.groups.clear()
            for g in json.loads(request.POST.get("groups", "[]")) or []:
                group = Group.objects.get(pk=g)
                doc.user.groups.add(group)
        elif request.POST.get("update_fio") == "1":
            doc.fio = request.POST.get("fio", "ФИО")
            doc.save()
        elif request.POST.get("update_username") == "1":
            un = request.POST.get("username", "").strip()
            if un:
                try:
                    doc.user.username = un
                    doc.user.save()
                except IntegrityError:
                    return JsonResponse({"ok": False, "msg": "Имя пользователя занято"})

        else:
            doc.podrazdeleniye = Podrazdeleniya.objects.get(pk=request.POST["podr"])
            doc.save()
        return JsonResponse({"ok": True})
    if request.is_ajax():
        doc = DoctorProfile.objects.get(pk=request.GET["pk"])
        groups = [{"pk": str(x.pk), "title": x.name} for x in doc.user.groups.all()]
        return HttpResponse(json.dumps({"groups": groups, "fio": doc.fio, "username": doc.user.username, "user_pk": doc.user_id}), content_type="application/json")
    otds = {}
    podr = Podrazdeleniya.objects.all().order_by("title")
    for x in podr:
        otds[x.title] = []
        docs = DoctorProfile.objects.filter(podrazdeleniye=x).order_by('fio')
        if not request.user.is_superuser:
            docs = docs.filter(user__is_superuser=False)
        for y in docs:
            otds[x.title].append({"pk": y.pk, "fio": y.get_fio(), "username": y.user.username, "podr": y.podrazdeleniye_id})
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
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False})


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
    if states["user"] > -1:
        obj = obj.filter(user__pk=states["user"])
    if states["user"] == -2:
        obj = obj.filter(user__isnull=True)

    if states["type"] != -1:
        obj = obj.filter(type=states["type"])
    if states["pk"] != "-1":
        obj = obj.filter(key__contains=states["pk"])

    if check_new == 0:
        offset = int(request.POST.get("offset", request.GET.get("offset", 0)))
        size = int(request.POST.get("size", request.GET.get("size", 0)))
        rows = obj.order_by("-pk")[offset:size + offset]
    else:
        pkgt = int(request.POST.get("last_n", request.GET.get("last_n", 0)))
        rows = obj.filter(pk__gt=pkgt).order_by("pk")
    for row in rows:
        tmp_object = {
            "id": row.pk,
            "user_fio": "Система" if not row.user else (row.user.get_fio() + ", " + row.user.user.username),
            "user_pk": row.user_id or "",
            "key": row.key,
            "body": row.body,
            "type": row.get_type_display(),
            "time": strdatetime(row.time),
        }
        result["data"].append(tmp_object)

    result["s"] = states
    return JsonResponse(result)


# @cache_page(60 * 15)
@login_required
@group_required("Заборщик биоматериала")
def researches_control(request):
    tubes = Tubes.objects.all()
    return render(request, 'dashboard/get_biomaterial.html', {"tubes": tubes})


@login_required
@group_required("Получатель биоматериала")
def receive_journal_form(request):
    p = request.GET.get("lab_pk")
    if p != '-2':
        lab = Podrazdeleniya.objects.get(pk=p or request.user.doctorprofile.podrazdeleniye_id)
    else:
        lab = None
    labs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY).exclude(title="Внешние организации").order_by("title")
    if not lab or lab.p_type != Podrazdeleniya.LABORATORY:
        lab = labs[0]
    groups = directory.ResearchGroup.objects.filter(lab=lab)
    podrazdeleniya = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.DEPARTMENT).filter(Q(hospital=request.user.doctorprofile.hospital) | Q(hospital__isnull=True)).order_by("title")
    return render(request, 'dashboard/receive_journal.html', {"groups": groups, "podrazdeleniya": podrazdeleniya, "labs": labs, "lab": lab})


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

            ctp = int(0 if not iss.time_confirmation else int(time.mktime(timezone.localtime(iss.time_confirmation).timetuple())))
            ctime = int(time.time())
            cdid = iss.doc_confirmation_id or -1
            if (
                (ctime - ctp < SettingManager.get("lab_reset_confirm_time_min") * 60 and cdid == request.user.doctorprofile.pk)
                or request.user.is_superuser
                or "Сброс подтверждений результатов" in [str(x) for x in request.user.groups.all()]
            ):
                predoc = {"fio": iss.doc_confirmation_fio or 'не подтверждено', "pk": cdid, "direction": iss.napravleniye_id}
                iss.doc_confirmation = iss.time_confirmation = None
                iss.save()
                if iss.napravleniye.result_rmis_send:
                    c = Client()
                    c.directions.delete_services(iss.napravleniye, request.user.doctorprofile)
                result = {"ok": True}
                slog.Log(key=pk, type=24, body=json.dumps(predoc), user=request.user.doctorprofile).save()
            else:
                result["msg"] = "Сброс подтверждения разрешен в течении %s минут" % (str(SettingManager.get("lab_reset_confirm_time_min")))
    return JsonResponse(result)


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
                slog.Log(key=str(profile.pk), user=request.user.doctorprofile, type=16, body=json.dumps({"username": username, "password": "(скрыт)", "podr": podrpost, "fio": fio})).save()
            else:
                return render(
                    request,
                    'dashboard/create_user.html',
                    {
                        'error': True,
                        'mess': 'Пользователь с таким именем пользователя уже существует',
                        'uname': username,
                        'fio': fio,
                        'status': registered,
                        'podr': podr,
                        'podrpost': podrpost,
                        'g': groups,
                    },
                )  # Вывод
        else:
            return render(
                request,
                'dashboard/create_user.html',
                {'error': True, 'mess': 'Данные введены неверно', 'uname': username, 'fio': fio, 'status': registered, 'podr': podr, 'podrpost': podrpost, 'g': groups},
            )  # Вывод

    return render(request, 'dashboard/create_user.html', {'error': False, 'mess': '', 'uname': '', 'fio': '', 'status': registered, 'podr': podr, 'podrpost': podrpost, 'g': groups})  # Вывод


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
            return JsonResponse({})
        title = request.POST['title']  # Получение названия
        if title:  # Если название есть
            if not Podrazdeleniya.objects.filter(title=title).exists():  # Если название не существует
                pd = Podrazdeleniya.objects.create()  # Создание подразделения
                pd.title = title
                pd.save()  # Сохранение подразделения
                p = True
                e = False
                slog.Log(key=str(pd.pk), user=request.user.doctorprofile, type=17, body=json.dumps({"title": title})).save()
            else:
                mess = "Такое подразделение уже есть"
        else:
            mess = "Название заполнено некорректно"
    else:
        e = False
    return render(request, 'dashboard/create_podr.html', {'error': e, 'mess': mess, 'title': '', 'status': p, 'podr': podr, 'types': Podrazdeleniya.TYPES})


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


@login_required
@group_required("Лечащий врач", "Оператор лечащего врача", "Врач-лаборант", "Лаборант", "Врач параклиники", "Врач консультаций")
def results_history(request):
    podr = Podrazdeleniya.objects.filter(p_type__in=[Podrazdeleniya.LABORATORY, Podrazdeleniya.PARACLINIC]).order_by("title")

    podrazdeleniya = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.DEPARTMENT).order_by("title")
    users = []
    for p in podrazdeleniya:
        pd = {"pk": p.pk, "title": p.title, "docs": []}
        for d in DoctorProfile.objects.filter(podrazdeleniye=p, user__groups__name="Лечащий врач"):
            pd["docs"].append({"pk": d.pk, "fio": d.get_fio()})
        users.append(pd)
    return render(
        request,
        'dashboard/results_history.html',
        {
            'fin': get_fin(),
            "notlabs": podrazdeleniya,
            "users": json.dumps(users),
            "labs": [
                {
                    "title": x.get_title(),
                    "researches": [{"pk": y.pk, "title": y.get_full_short_title()} for y in directory.Researches.objects.filter(hide=False, podrazdeleniye=x).order_by("title")],
                }
                for x in podr
            ],
        },
    )


@login_required
@group_required("Лечащий врач", "Загрузка выписок", "Поиск выписок")
def discharge(request):
    podr = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY).exclude(title="Внешние организации")

    podrazdeleniya = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.DEPARTMENT).order_by("title")
    users = []
    for p in podrazdeleniya:
        pd = {"pk": p.pk, "title": p.title, "docs": []}
        for d in DoctorProfile.objects.filter(podrazdeleniye=p, user__groups__name="Лечащий врач"):
            pd["docs"].append({"pk": d.pk, "fio": d.fio})
        users.append(pd)
    return render(
        request,
        'dashboard/discharge.html',
        {
            'labs': podr,
            'fin_poli': [],
            # IstochnikiFinansirovaniya.objects.filter(istype="poli"),
            'fin_stat': [],
            # IstochnikiFinansirovaniya.objects.filter(istype="stat"),
            "notlabs": podrazdeleniya,
            "users": json.dumps(users),
        },
    )


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
            obj = discharge.Discharge(
                client_surname=client_surname,
                client_name=client_name,
                client_patronymic=client_patronymic,
                client_birthday=client_birthday,
                client_sex=client_sex,
                client_cardnum=client_cardnum,
                client_historynum=client_historynum,
                otd=otd,
                doc_fio=doc_fio,
                creator=request.user.doctorprofile,
                file=request.FILES["file"],
            )
            obj.save()
            slog.Log(
                key=obj.pk,
                type=1000,
                body=json.dumps(
                    {
                        "client_surname": client_surname,
                        "client_name": client_name,
                        "client_patronymic": client_patronymic,
                        "client_birthday": client_birthday,
                        "client_sex": client_sex,
                        "client_cardnum": client_cardnum,
                        "client_historynum": client_historynum,
                        "otd": otd.title + ", " + str(otd.pk),
                        "doc_fio": doc_fio,
                        "file": obj.file.name,
                    }
                ),
                user=request.user.doctorprofile,
            ).save()
    return JsonResponse(r)


@csrf_exempt
@login_required
@group_required("Лечащий врач", "Поиск выписок")
def discharge_search(request):
    r = {"rows": []}
    if request.method == "GET":
        import discharge.models as discharge

        date_start = request.GET["date_start"]
        date_end = request.GET["date_end"]
        date_start, date_end = try_parse_range(date_start, date_end)
        query = request.GET.get("q", "")
        otd_pk = int(request.GET.get("otd", "-1"))
        doc_fio = request.GET.get("doc_fio", "")

        slog.Log(
            key=query,
            type=1001,
            body=json.dumps({"date_start": request.GET["date_start"], "date_end": request.GET["date_end"], "otd_pk": otd_pk, "doc_fio": doc_fio}),
            user=request.user.doctorprofile,
        ).save()

        filter_type = "any"
        family = ""
        name = ""
        twoname = ""
        bdate = ""

        if query.isdigit():
            filter_type = "card_number"
        elif bool(re.compile(r'^([a-zA-Zа-яА-Я]+)( [a-zA-Zа-яА-Я]+)?( [a-zA-Zа-яА-Я]+)?( \d{2}\.\d{2}\.\d{4})?$').match(query)):
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
                spq = split[3]
                bdate = "%s-%s-%s" % (spq[4:8], spq[2:4], spq[0:2])

        rows = discharge.Discharge.objects.filter(
            created_at__range=(
                date_start,
                date_end,
            ),
            doc_fio__icontains=doc_fio,
        )

        if otd_pk > -1:
            rows = rows.filter(otd__pk=otd_pk)

        if filter_type == "fio":
            rows = rows.filter(client_surname__contains=family, client_name__contains=name, client_patronymic__contains=twoname)
            if bdate != "":
                rows = rows.filter(client_birthday=bdate)

        if filter_type == "card_number":
            rows = rows.filter(client_cardnum=int(query))
        import os

        for row in rows.order_by("-created_at"):
            r["rows"].append(
                {
                    "date": str(dateformat.format(row.created_at.date(), settings.DATE_FORMAT)),
                    "client": {"surname": row.client_surname, "name": row.client_name, "patronymic": row.client_patronymic, "sex": row.client_sex, "birthday": row.client_birthday},
                    "otd": row.otd.title,
                    "doc_fio": row.doc_fio,
                    "filename": os.path.basename(row.file.name),
                    "fileurl": row.file.url,
                }
            )

    return JsonResponse(r)


@login_required
@group_required("Создание и редактирование пользователей")
def users_count(request):
    """ Получение количества пользователей """
    result = {"all": User.objects.all().count(), "ldap": DoctorProfile.objects.filter(isLDAP_user=True).count()}

    return JsonResponse(result)


@login_required
@group_required("Лечащий врач", "Оператор лечащего врача", "Врач-лаборант", "Лаборант")
def results_history_search(request):
    type = request.GET.get("type", "otd")
    day = request.GET.get("date", datetime.datetime.today().strftime('%d.%m.%Y'))

    day1 = datetime.date(int(day.split(".")[2]), int(day.split(".")[1]), int(day.split(".")[0]))
    day2 = day1 + datetime.timedelta(days=1)

    if type == "otd":
        collect = Napravleniya.objects.filter(
            issledovaniya__time_confirmation__isnull=False,
            issledovaniya__time_confirmation__range=(day1, day2),
            doc__podrazdeleniye=request.user.doctorprofile.podrazdeleniye,
            issledovaniya__research__is_doc_refferal=False,
            issledovaniya__research__is_slave_hospital=False,
        )
    else:
        collect = Napravleniya.objects.filter(issledovaniya__time_confirmation__isnull=False, issledovaniya__time_confirmation__range=(day1, day2), doc=request.user.doctorprofile)

    result = list(collect.order_by("doc", "client").exclude(issledovaniya__time_confirmation__isnull=True).values_list('pk', flat=True))

    return JsonResponse(result, safe=False)


@login_required
@group_required("Получатель биоматериала")
def dashboard_from(request):
    """ Получение отделений и кол-ва пробирок """
    date_start = request.GET["datestart"]
    date_end = request.GET["dateend"]
    filter_type = request.GET.get("type", "wait")
    result = {}
    try:
        date_start, date_end = try_parse_range(date_start, date_end)
        if request.GET.get("get_labs", "false") == "true":
            for lab in (
                Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY)
                .filter(Q(hospital=request.user.doctorprofile.hospital) | Q(hospital__isnull=True))
                .exclude(title="Внешние организации")
            ):
                tubes_list = TubesRegistration.objects.filter(
                    doc_get__podrazdeleniye__p_type=Podrazdeleniya.DEPARTMENT, time_get__range=(date_start, date_end), issledovaniya__research__podrazdeleniye=lab
                ).filter(Q(issledovaniya__napravleniye__hospital=request.user.doctorprofile.hospital) | Q(issledovaniya__napravleniye__hospital__isnull=True))
                if filter_type == "not_received":
                    tubes_list = tubes_list.filter(doc_recive__isnull=True).exclude(notice="")
                elif filter_type == "received":
                    tubes_list = tubes_list.filter(doc_recive__isnull=False)
                else:
                    tubes_list = tubes_list.filter(notice="", doc_recive__isnull=True)
                tubes = tubes_list.distinct().count()
                result[lab.pk] = tubes
            return JsonResponse(result)
        podrazdeleniya = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.DEPARTMENT).filter(Q(hospital=request.user.doctorprofile.hospital) | Q(hospital__isnull=True)).order_by("title")
        lab = Podrazdeleniya.objects.get(pk=request.GET["lab"])
        i = 0
        for podrazledeniye in podrazdeleniya:
            i += 1
            tubes_list = get_tubes_list_in_receive_ui(date_end, date_start, filter_type, lab, podrazledeniye, request.user.doctorprofile)
            result[i] = {"tubes": tubes_list.distinct().count(), "title": podrazledeniye.title, "pk": podrazledeniye.pk}
    except ValueError:
        pass

    return JsonResponse(result)


def get_tubes_list_in_receive_ui(date_end, date_start, filter_type, lab, podrazledeniye, doctorprofile):
    tubes_list = TubesRegistration.objects.filter(doc_get__podrazdeleniye=podrazledeniye, time_get__range=(date_start, date_end), issledovaniya__research__podrazdeleniye=lab).filter(
        Q(issledovaniya__napravleniye__hospital=doctorprofile.hospital) | Q(issledovaniya__napravleniye__hospital__isnull=True)
    )
    if filter_type == "not_received":
        tubes_list = tubes_list.filter(doc_recive__isnull=True).exclude(notice="")
    elif filter_type == "received":
        tubes_list = tubes_list.filter(doc_recive__isnull=False)
    else:
        tubes_list = tubes_list.filter(notice="", doc_recive__isnull=True)
    return tubes_list


@login_required
def dir_multiprint(request):
    """ Страница пакетной печати направлений """
    return render(request, 'dashboard/dir_multiprint.html')


@login_required
def researches_from_directions(request):
    pk = json.loads(request.GET.get("pk", "[]"))
    data = defaultdict(list)
    for i in Issledovaniya.objects.filter(napravleniye__pk__in=pk, research__hide=False):
        data[i.research.podrazdeleniye_id or -2].append(i.research_id)
    return JsonResponse(data)


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
            data.append(
                {
                    'type': "Направление №%s" % pk,
                    'events': [
                        [
                            ["title", strdatetime(dir.data_sozdaniya) + " Направление создано"],
                            ["Создатель", get_userdata(dir.doc_who_create)],
                            ["От имени", "" if not dir.doc else get_userdata(dir.doc)],
                            ["Пациент", "%s, %s, Пол: %s" % (dir.client.individual.fio(), dir.client.individual.bd(), dir.client.individual.sex)],
                            ["Карта", "%s %s" % (dir.client.number, dir.client.base.title)],
                            ["Архив", yesno[dir.client.is_archive]],
                            ["Источник финансирования", dir.fin_title],
                            ["Диагноз", dir.diagnos],
                            ["Направление создано на основе направления из РМИС", yesno[dir.imported_from_rmis]],
                            ["Направивляющая организация из РМИС", "" if not dir.imported_org else dir.imported_org.title],
                            ["Направление отправлено в РМИС", yesno[dir.imported_directions_rmis_send if dir.imported_from_rmis else dir.rmis_number not in ["", None, "NONERMIS"]]],
                            ["Номер РМИС направления", dir.rmis_number if dir.rmis_number not in [None, "NONERMIS"] else ""],
                            ["Направление привязано к случаю РМИС", yesno[dir.rmis_case_id not in ["", None, "NONERMIS"]]],
                            ["Направление привязано к записи отделения госпитализации РМИС", yesno[dir.rmis_hosp_id not in ["", None, "NONERMIS"]]],
                            ["Результат отправлен в РМИС", yesno[dir.result_rmis_send]],
                        ]
                    ],
                }
            )
            if dir.visit_date and dir.visit_who_mark:
                d = {
                    "type": "Посещение по направлению",
                    "events": [
                        [
                            ["title", strdatetime(dir.visit_date) + " Регистрация посещения"],
                            ["Регистратор", dir.visit_who_mark.fio + ", " + dir.visit_who_mark.podrazdeleniye.title],
                        ]
                    ],
                }
                data.append(d)
            for lg in slog.Log.objects.filter(key=str(pk), type__in=(5002,)):
                data[0]["events"].append([["title", "{}, {}".format(strdatetime(lg.time), lg.get_type_display())], ["Отмена", "{}, {}".format(lg.body, get_userdata(lg.user))]])
            for lg in slog.Log.objects.filter(key=str(pk), type__in=(60000, 60001, 60002, 60003)):
                data[0]["events"].append([["title", lg.get_type_display()], ["Дата и время", strdatetime(lg.time)]])
            for tube in TubesRegistration.objects.filter(issledovaniya__napravleniye=dir).distinct():
                d = {"type": "Ёмкость №%s" % tube.pk, "events": []}
                if tube.time_get is not None:
                    d["events"].append([["title", strdatetime(tube.time_get) + " Забор"], ["Заборщик", get_userdata(tube.doc_get)]])
                for lg in slog.Log.objects.filter(key=str(tube.pk), type__in=(4000, 12, 11)).distinct():
                    tdata = [["Приёмщик", get_userdata(lg.user)], ["title", strdatetime(lg.time) + " " + lg.get_type_display() + " (#%s)" % lg.pk]]
                    if lg.body and lg.body != "":
                        tdata.append(["json_data", lg.body])
                    d["events"].append(tdata)
                data.append(d)
            for iss in Issledovaniya.objects.filter(napravleniye=dir):
                d = {'type': "Исследование: %s (#%s)" % (iss.research.title, iss.pk), 'events': []}
                for lg in slog.Log.objects.filter(key=str(iss.pk), type__in=(13, 14, 24)).distinct():
                    tdata = [["Исполнитель", get_userdata(lg.user)], ["title", strdatetime(lg.time) + " " + lg.get_type_display() + " (#%s)" % lg.pk]]
                    if lg.body and lg.body != "" and lg.type != 24:
                        tdata.append(["json_data", lg.body])
                    d["events"].append(tdata)
                data.append(d)
            slog.Log(key=str(pk), type=5000, body="", user=request.user.doctorprofile).save()
        return JsonResponse(data, safe=False)
    return render(request, 'dashboard/direction_info.html')


def get_userdata(doc: DoctorProfile):
    if doc is None:
        return ""
    return "%s (%s) - %s" % (doc.fio, doc.user.username, doc.podrazdeleniye.title)


def ratelimited(request, e):
    return render(request, 'dashboard/error.html', {"message": "Запрос выполняется слишком часто, попробуйте позднее", "update": True})


def cards(request):
    if not SettingManager.get("mis_module", default='false', default_type='b'):
        from django.http import Http404

        raise Http404()
    return render(request, 'dashboard/cards.html')


def v404(request, exception=None):
    return render(request, 'dashboard/error.html', {"message": "Ошибка 404 - страница не найдена", "update": False, "to_home": True}, status=404)


def v500(request, exception=None):
    return render(request, 'dashboard/error.html', {"message": "Ошибка 500 - проблемы на сервере. Сообщите администратору или попробуйте позднее", "update": True, "no_nt": True}, status=500)


@login_required
@group_required("Госпитализация")
def hosp(request):
    return render(request, 'dashboard/hosp.html')


@login_required
@group_required("Врач параклиники", "Врач консультаций")
def results_paraclinic(request):
    return render(request, 'dashboard/results_paraclinic.html')


@login_required
@group_required("Врач параклиники", "Посещения по направлениям", "Врач консультаций")
def direction_visit(request):
    return render(request, 'dashboard/direction_visit.html')


@login_required
@group_required("Лечащий врач", "Оператор лечащего врача", "Врач-лаборант", "Лаборант", "Врач параклиники")
def results_report(request):
    return render(request, 'dashboard/results_report.html')


@login_required
@group_required("Врач параклиники", "Врач консультаций")
def results_paraclinic_blanks(request):
    researches = directory.Researches.objects.filter(hide=False, is_paraclinic=True, podrazdeleniye=request.user.doctorprofile.podrazdeleniye).order_by("title")
    return render(request, 'dashboard/results_paraclinic_blanks.html', {"researches": researches})


@staff_member_required
def rmq_messages(request):
    from mq.publisher import get_queue_messages_count

    data = {"count": get_queue_messages_count()}
    return JsonResponse(data)


@staff_member_required
def rmq_count(request):
    model = request.GET["model"].split(".")
    from django.apps import apps

    m = apps.get_model(app_label=model[0], model_name=model[1])
    i = m.objects.all().order_by("-pk").first()
    return JsonResponse({"count": 0 if not i else i.pk})


@staff_member_required
def rmq_send(request):
    model = request.GET["model"].split(".")
    from mq.publisher import mq_send

    mq_send("updated", "{}.models.{}".format(model[0], model[1]), str(request.GET["pk"]))
    return JsonResponse({"ok": True})


@login_required
@group_required("Подтверждение отправки результатов в РМИС")
def rmis_confirm(request):
    return render(request, 'dashboard/rmis_confirm.html')


def l2queue(request):
    return render(request, 'dashboard/l2queue.html')


@login_required
def directions(request):
    prefetched = prefetch(request, {
        'researches.get_researches': {
            'url': 'researches/all',
        },
        'departments': {
            'data': {'method': 'GET'},
        },
        'bases': {},
        'current_user_info': {
            'url': 'current-user-info',
        },
        'hospitals': {},
        'researches.by_direction_params': {
            'url': 'researches/by-direction-params',
        },
        'procedure_list.get_suitable_departments': {
            'url': 'procedural-list/suitable-departments',
        },
        'directive_from': {
            'url': 'directive-from',
        },
        'directions.purposes': {
            'url': 'directions/purposes',
        },
        'directions.external_organizations': {
            'url': 'directions/external-organizations',
        },
        'researches.get_researches_templates': {
            'url': 'researches/templates',
        },
    })
    return render(request, 'dashboard/directions_ng.html', {"prefetched": prefetched})


def eds(request, path):
    return proxy_view(request, urljoin(SettingManager.get_eds_base_url(), path))
