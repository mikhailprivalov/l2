import datetime
import re
from collections import defaultdict

import simplejson as json
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils import dateformat
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

import directory.models as directory
import podrazdeleniya.models as pod
import slog.models as slog
from appconf.manager import SettingManager
from clients.models import CardBase
from directions.models import IstochnikiFinansirovaniya, TubesRegistration, Issledovaniya, Napravleniya
from laboratory import VERSION, settings
from laboratory.decorators import group_required
from laboratory.utils import strdatetime
from podrazdeleniya.models import Podrazdeleniya
from rmis_integration.client import Client
from users.models import DoctorProfile
from utils.dates import try_parse_range


@login_required
@ensure_csrf_cookie
def dashboard(request):
    if not request.is_ajax():
        return redirect('/ui/menu')
    return HttpResponse(f"OK:{request.user.username}:{VERSION}")


@login_required
@group_required("Просмотр журнала")
@ensure_csrf_cookie
def view_log(request):
    import slog.models as slog

    types = []
    for t in slog.Log.TYPES:
        types.append({"pk": t[0], "val": t[1]})
    return render(request, 'dashboard/manage_view_log.html', {"users": DoctorProfile.objects.all().order_by("fio"), "types": types})


@login_required
@group_required("Создание и редактирование пользователей")
@ensure_csrf_cookie
def profiles(request):
    return redirect('/ui/profiles')


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
        rows = obj.order_by("-pk")[offset : size + offset]
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


def researches_control(request):
    return redirect('/ui/biomaterial/get')


@login_required
@group_required("Получатель биоматериала")
@ensure_csrf_cookie
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


@csrf_exempt
@login_required
@group_required("Создание и редактирование пользователей")
def create_pod(request):
    return redirect('/ui/departments')


@login_required
@staff_member_required
@ensure_csrf_cookie
def ldap_sync(request):
    """Страница синхронизации с LDAP"""
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
@ensure_csrf_cookie
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
@ensure_csrf_cookie
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
    """Получение количества пользователей"""
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
    """Получение отделений и кол-ва пробирок"""
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
    """Страница пакетной печати направлений"""
    return render(request, 'dashboard/dir_multiprint.html')


@login_required
def researches_from_directions(request):
    pk = json.loads(request.GET.get("pk", "[]"))
    data = defaultdict(list)
    for i in Issledovaniya.objects.filter(napravleniye__pk__in=pk, research__hide=False):
        data[i.research.podrazdeleniye_id or -2].append(i.research_id)
    return JsonResponse(data)


def get_userdata(doc: DoctorProfile):
    if doc is None:
        return ""
    return "%s (%s) - %s" % (doc.fio, doc.user.username, doc.podrazdeleniye.title)


def ratelimited(request, e):
    return render(request, 'dashboard/error.html', {"message": "Запрос выполняется слишком часто, попробуйте позднее", "update": True})


def v404(request, exception=None):
    return render(request, 'dashboard/error.html', {"message": "Ошибка 404 - страница не найдена", "update": False, "to_home": True}, status=404)


def v500(request, exception=None):
    return render(request, 'dashboard/error.html', {"message": "Ошибка 500 - проблемы на сервере. Сообщите администратору или попробуйте позднее", "update": True, "no_nt": True}, status=500)


@login_required
@group_required("Врач параклиники", "Врач консультаций", "Заполнение мониторингов")
@ensure_csrf_cookie
def results_paraclinic(request):
    q = request.GET.urlencode()
    return redirect(f'/ui/results/descriptive{("?" + q) if q else ""}')


@login_required
@group_required("Врач параклиники", "Посещения по направлениям", "Врач консультаций")
@ensure_csrf_cookie
def direction_visit(request):
    return redirect('/ui/direction-visit')


@login_required
@group_required("Лечащий врач", "Оператор лечащего врача", "Врач-лаборант", "Лаборант", "Врач параклиники")
@ensure_csrf_cookie
def results_report(request):
    return redirect('/ui/results-report')


@login_required
@group_required("Врач параклиники", "Врач консультаций")
@ensure_csrf_cookie
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


@ensure_csrf_cookie
def l2queue(request):
    return render(request, 'dashboard/l2queue.html')


@login_required
@ensure_csrf_cookie
def directions(request):
    q = request.GET.urlencode()
    return redirect(f'/ui/directions{("?" + q) if q else ""}')


@ensure_csrf_cookie
def ui(request, path):
    return render(request, 'vuebase.html')


@login_required
def results_department(request):
    return redirect('/ui/results-by-department-or-doctor')


@login_required
def doc_call(request):
    return redirect('/ui/doc-call')


@login_required
def list_wait(request):
    return redirect('/ui/list-wait')
