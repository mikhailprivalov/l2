import datetime
from collections import defaultdict

import simplejson as json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from clients.models import CardBase

import directory.models as directory
from directions.models import IstochnikiFinansirovaniya, TubesRegistration, Issledovaniya, Napravleniya
from laboratory import VERSION
from laboratory.decorators import group_required
from laboratory.utils import strdatetime
from podrazdeleniya.models import Podrazdeleniya
from users.models import DoctorProfile
from utils.dates import try_parse_range


@login_required
@ensure_csrf_cookie
def dashboard(request):
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
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
@group_required("Создание и редактирование пользователей")
def users_count(request):
    """Получение количества пользователей"""
    result = {"all": User.objects.all().count()}

    return JsonResponse(result)


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


def v404(request, exception=None):
    if request.path.startswith("/api/") or request.path.startswith("/static/"):
        return render(request, 'dashboard/error.html', {"message": "Страница не найдена"}, status=404)
    return redirect("/ui/404")


def v500(request, exception=None):
    return render(request, 'dashboard/error.html', {"message": "Ошибка 500 - проблемы на сервере. Сообщите администратору или попробуйте позднее"}, status=500)


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
