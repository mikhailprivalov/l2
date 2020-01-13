import time
from collections import defaultdict

import simplejson as json
import yaml
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

import api.models as models
import directions.models as directions
import users.models as users
from api import fias
from api.ws import emit
from appconf.manager import SettingManager
from barcodes.views import tubes
from clients.models import CardBase, Individual, Card, Document
from directory.models import Fractions, ParaclinicInputField, ResearchSite
from laboratory.decorators import group_required
from laboratory.utils import strdatetime
from podrazdeleniya.models import Podrazdeleniya
from slog import models as slog
from slog.models import Log
from statistics_tickets.models import VisitPurpose, ResultOfTreatment, StatisticsTicket, Outcomes, \
    ExcludePurposes
from utils.dates import try_parse_range, try_strptime
from directory.models import Researches as DResearches


def translit(locallangstring):
    """
    Translit func
    :param locallangstring: orign
    :return: translit of locallangstring
    """
    conversion = {
        u'\u0410': 'A', u'\u0430': 'a',
        u'\u0411': 'B', u'\u0431': 'b',
        u'\u0412': 'V', u'\u0432': 'v',
        u'\u0413': 'G', u'\u0433': 'g',
        u'\u0414': 'D', u'\u0434': 'd',
        u'\u0415': 'E', u'\u0435': 'e',
        u'\u0401': 'Yo', u'\u0451': 'yo',
        u'\u0416': 'Zh', u'\u0436': 'zh',
        u'\u0417': 'Z', u'\u0437': 'z',
        u'\u0418': 'I', u'\u0438': 'i',
        u'\u0419': 'Y', u'\u0439': 'y',
        u'\u041a': 'K', u'\u043a': 'k',
        u'\u041b': 'L', u'\u043b': 'l',
        u'\u041c': 'M', u'\u043c': 'm',
        u'\u041d': 'N', u'\u043d': 'n',
        u'\u041e': 'O', u'\u043e': 'o',
        u'\u041f': 'P', u'\u043f': 'p',
        u'\u0420': 'R', u'\u0440': 'r',
        u'\u0421': 'S', u'\u0441': 's',
        u'\u0422': 'T', u'\u0442': 't',
        u'\u0423': 'U', u'\u0443': 'u',
        u'\u0424': 'F', u'\u0444': 'f',
        u'\u0425': 'H', u'\u0445': 'h',
        u'\u0426': 'Ts', u'\u0446': 'ts',
        u'\u0427': 'Ch', u'\u0447': 'ch',
        u'\u0428': 'Sh', u'\u0448': 'sh',
        u'\u0429': 'Sch', u'\u0449': 'sch',
        u'\u042a': '', u'\u044a': '',
        u'\u042b': 'Y', u'\u044b': 'y',
        u'\u042c': '', u'\u044c': '',
        u'\u042d': 'E', u'\u044d': 'e',
        u'\u042e': 'Yu', u'\u044e': 'yu',
        u'\u042f': 'Ya', u'\u044f': 'ya',
    }
    translitstring = []
    for c in locallangstring:
        translitstring.append(conversion.setdefault(c, c))
    return ''.join(translitstring)


@csrf_exempt
def send(request):
    """
    Sysmex save results
    :param request:
    :return:
    """
    result = {"ok": False}
    try:
        if request.method == "POST":
            resdict = yaml.load(request.POST["result"])
            appkey = request.POST.get("key", "")
        else:
            resdict = yaml.load(request.GET["result"])
            appkey = request.GET.get("key", "")

        astm_user = users.DoctorProfile.objects.filter(user__username="astm").first()
        resdict["pk"] = int(resdict.get("pk", -111))
        if "LYMPH%" in resdict["result"]:
            resdict["orders"] = {}

        dpk = -1
        if "bydirection" in request.POST or "bydirection" in request.GET:
            dpk = resdict["pk"]

            if dpk >= 4600000000000:
                dpk -= 4600000000000
                dpk //= 10
            tubes(request, direction_implict_id=dpk)
            if directions.TubesRegistration.objects.filter(issledovaniya__napravleniye__pk=dpk,
                                                           issledovaniya__doc_confirmation__isnull=True).exists():
                resdict["pk"] = directions.TubesRegistration.objects.filter(
                    issledovaniya__napravleniye__pk=dpk, issledovaniya__doc_confirmation__isnull=True).order_by(
                    "pk").first().pk
            else:
                resdict["pk"] = False
        result["A"] = appkey
        app = models.Application.objects.filter(key=appkey, active=True).first()
        if resdict["pk"] and app and directions.TubesRegistration.objects.filter(pk=resdict["pk"]).exists():
            tubei = directions.TubesRegistration.objects.get(pk=resdict["pk"])
            direction = tubei.issledovaniya_set.first().napravleniye
            pks = []
            for key in resdict["result"].keys():
                if models.RelationFractionASTM.objects.filter(astm_field=key).exists():
                    fractionRels = models.RelationFractionASTM.objects.filter(astm_field=key)
                    for fractionRel in fractionRels:
                        fraction = fractionRel.fraction
                        if directions.Issledovaniya.objects.filter(napravleniye=direction,
                                                                   research=fraction.research,
                                                                   doc_confirmation__isnull=True).exists():
                            issled = directions.Issledovaniya.objects.filter(napravleniye=direction,
                                                                             research=fraction.research,
                                                                             doc_confirmation__isnull=True).order_by(
                                "pk")[0]
                            if directions.Result.objects.filter(issledovaniye=issled,
                                                                fraction=fraction).exists():
                                fraction_result = directions.Result.objects.filter(issledovaniye=issled,
                                                                                   fraction__pk=fraction.pk).order_by(
                                    "-pk")[0]
                            else:
                                fraction_result = directions.Result(issledovaniye=issled,
                                                                    fraction=fraction)
                            fraction_result.value = str(resdict["result"][key]).strip()  # Установка значения
                            if fraction_result.value.isdigit():
                                fraction_result.value = "%s.0" % fraction_result.value
                            import re
                            find = re.findall(r"\d+.\d+", fraction_result.value)
                            if len(find) > 0:
                                val = float(find[0]) * fractionRel.get_multiplier_display()
                                val = app.auto_set_places(fractionRel, val)

                                fraction_result.value = fraction_result.value.replace(find[0], str(val))

                            fraction_result.iteration = 1  # Установка итерации
                            ref = fractionRel.default_ref
                            if ref:
                                fraction_result.ref_title = ref.title
                                fraction_result.ref_about = ref.about
                                fraction_result.ref_m = ref.m
                                fraction_result.ref_f = ref.f
                            fraction_result.save()  # Сохранение
                            issled.api_app = app
                            issled.save()
                            fraction_result.get_ref(re_save=True)
                            fraction_result.issledovaniye.doc_save = astm_user  # Кто сохранил
                            fraction_result.issledovaniye.time_save = timezone.now()  # Время сохранения
                            fraction_result.issledovaniye.save()
                            if issled not in pks:
                                pks.append(issled)
            for pkk in pks:
                emit("results_save", {"pk": pkk, "user": None, "dir": direction.pk})
            slog.Log(key=appkey, type=22, body=json.dumps(resdict), user=None).save()
            result["ok"] = True
        elif not directions.TubesRegistration.objects.filter(pk=resdict["pk"]).exists():
            if dpk > -1:
                resdict["pk"] = dpk
            slog.Log(key=resdict["pk"], type=23, body=json.dumps(resdict), user=None).save()
    except Exception as e:
        result = {"ok": False, "Exception": True, "MSG": str(e)}
    return JsonResponse(result)


@csrf_exempt
def endpoint(request):
    result = {"answer": False, "body": ""}
    data = json.loads(request.POST.get("result", request.GET.get("result", "{}")))
    api_key = request.POST.get("key", request.GET.get("key", ""))
    message_type = data.get("message_type", "C")
    pk_s = str(data.get("pk", ""))
    pk = -1 if not pk_s.isdigit() else int(pk_s)
    data["app_name"] = "API key is incorrect"
    # pid = data.get("processing_id", "P")
    if models.Application.objects.filter(key=api_key).exists():
        astm_user = users.DoctorProfile.objects.filter(user__username="astm").first()
        if astm_user is None:
            astm_user = users.DoctorProfile.objects.filter(user__is_staff=True).order_by("pk").first()
        app = models.Application.objects.get(key=api_key)
        if app.active:
            data["app_name"] = app.name
            if message_type == "R" or data.get("result"):
                if pk != -1:
                    dw = app.direction_work
                    if pk >= 4600000000000:
                        pk -= 4600000000000
                        pk //= 10
                        dw = True
                    if dw:
                        direction = directions.Napravleniya.objects.filter(pk=pk).first()
                    else:
                        direction = directions.Napravleniya.objects.filter(issledovaniya__tubes__pk=pk).first()

                    pks = []
                    oks = []
                    if direction:
                        results = data.get("result", {})
                        for key in results:
                            ok = False
                            q = models.RelationFractionASTM.objects.filter(astm_field=key)
                            if q.filter(application_api=app).exists():
                                q = q.filter(application_api=app)
                                ok = True
                            elif q.filter(application_api__isnull=True).exists():
                                q = q.filter(application_api__isnull=True)
                                ok = True
                            if ok:
                                for fraction_rel in q:
                                    save_state = []
                                    issleds = []
                                    for issled in directions.Issledovaniya.objects.filter(napravleniye=direction,
                                                                                          research=fraction_rel.fraction.research,
                                                                                          doc_confirmation__isnull=True):
                                        if directions.Result.objects.filter(issledovaniye=issled,
                                                                            fraction=fraction_rel.fraction).exists():
                                            fraction_result = directions.Result.objects.filter(issledovaniye=issled,
                                                                                               fraction=fraction_rel.fraction).order_by(
                                                "-pk")[0]
                                        else:
                                            fraction_result = directions.Result(issledovaniye=issled,
                                                                                fraction=fraction_rel.fraction)
                                        fraction_result.value = str(results[key]).strip()
                                        import re
                                        find = re.findall(r"\d+.\d+", fraction_result.value)
                                        if len(find) > 0:
                                            val_str = fraction_result.value
                                            for f in find:
                                                val = float(f) * fraction_rel.get_multiplier_display()
                                                val = app.auto_set_places(fraction_rel, val)
                                                val_str = val_str.replace(f, str(val))
                                            fraction_result.value = val_str

                                        fraction_result.iteration = 1
                                        ref = fraction_rel.default_ref
                                        if ref:
                                            fraction_result.ref_title = ref.title
                                            fraction_result.ref_about = ref.about
                                            fraction_result.ref_m = ref.m
                                            fraction_result.ref_f = ref.f
                                        fraction_result.save()
                                        issled.api_app = app
                                        issled.save()
                                        fraction_result.get_ref(re_save=True)
                                        fraction_result.issledovaniye.doc_save = astm_user
                                        fraction_result.issledovaniye.time_save = timezone.now()
                                        fraction_result.issledovaniye.save()
                                        save_state.append({"fraction": fraction_result.fraction.title,
                                                           "value": fraction_result.value})
                                        issleds.append({"pk": issled.pk, "title": issled.research.title})

                                        if issled not in pks:
                                            pks.append(issled)
                                    # slog.Log(key=json.dumps({"direction": direction.pk, "issleds": str(issleds)}),
                                    #          type=22, body=json.dumps(save_state), user=None).save()
                            oks.append(ok)
                    result["body"] = "{} {} {} {}".format(dw, pk, json.dumps(oks), direction is not None)

                    for pkk in pks:
                        emit("results_save", {"pk": pkk, "user": None, "dir": direction.pk})
                else:
                    result["body"] = "pk '{}' is not exists".format(pk_s)
            elif message_type == "Q":
                result["answer"] = True
                pks = [int(x) for x in data.get("query", [])]
                researches = defaultdict(list)
                for row in app.get_issledovaniya(pks):
                    k = row["pk"]
                    i = row["iss"]
                    for fraction in Fractions.objects.filter(research=i.research,
                                                             hide=False):
                        rel = models.RelationFractionASTM.objects.filter(fraction=fraction, application_api=app)
                        if not rel.exists():
                            continue
                            # rel = models.RelationFractionASTM.objects.filter(fraction=fraction)
                            # if not rel.exists():
                            #     continue
                        rel = rel[0]
                        researches[k].append(rel.astm_field)
                result["body"] = researches
            else:
                pass
        else:
            data["app_name"] = "API app banned " + api_key
            result["body"] = "API app banned " + api_key
    else:
        result["body"] = "API key is incorrect"
    slog.Log(key=pk, type=6000, body=json.dumps({"data": data, "answer": result}), user=None).save()
    return JsonResponse(result)


@login_required
def departments(request):
    from podrazdeleniya.models import Podrazdeleniya
    can_edit = request.user.is_superuser or request.user.doctorprofile.has_group(
        'Создание и редактирование пользователей')
    if request.method == "GET":
        deps = [{"pk": x.pk, "title": x.get_title(), "type": str(x.p_type), "updated": False} for
                x in Podrazdeleniya.objects.all().order_by("pk")]
        en = SettingManager.en()
        return JsonResponse(
            {"departments": deps,
             "can_edit": can_edit,
             "types": [{"pk": str(x[0]), "title": x[1]} for x in Podrazdeleniya.TYPES if en.get(x[0], True)]})
    elif can_edit:
        ok = False
        message = ""
        try:
            req = json.loads(request.body)
            data_type = req.get("type", "update")
            rows = req.get("data", [])
            if data_type == "update":
                ok = False
                for row in rows:
                    title = row["title"].strip()
                    if len(title) > 0:
                        department = Podrazdeleniya.objects.get(pk=row["pk"])
                        department.title = title
                        department.p_type = int(row["type"])
                        department.save()
                        ok = True
            elif data_type == "insert":
                ok = False
                for row in rows:
                    title = row["title"].strip()
                    if len(title) > 0:
                        department = Podrazdeleniya(title=title, p_type=int(row["type"]))
                        department.save()
                        ok = True
        finally:
            return JsonResponse({"ok": ok, "message": message})
    return JsonResponse(0)


def bases(request):
    return JsonResponse({"bases": [
        {"pk": x.pk,
         "title": x.title,
         "code": x.short_title,
         "hide": x.hide,
         "history_number": x.history_number,
         "internal_type": x.internal_type,
         "fin_sources": [{
             "pk": y.pk,
             "title": y.title,
             "default_diagnos": y.default_diagnos
         } for y in directions.IstochnikiFinansirovaniya.objects.filter(base=x, hide=False).order_by('-order_weight')]
         } for x in CardBase.objects.all().order_by('-order_weight')]})


def current_user_info(request):
    ret = {"auth": request.user.is_authenticated, "doc_pk": -1, "username": "", "fio": "",
           "department": {"pk": -1, "title": ""}, "groups": [], "modules": SettingManager.l2_modules(),
           "user_services": [], "rmis_enabled": SettingManager.get("rmis_enabled", default='false', default_type='b')}
    if ret["auth"]:
        ret["username"] = request.user.username
        ret["fio"] = request.user.doctorprofile.fio
        ret["groups"] = list(request.user.groups.values_list('name', flat=True))
        if request.user.is_superuser:
            ret["groups"].append("Admin")
        ret["doc_pk"] = request.user.doctorprofile.pk
        ret["rmis_location"] = request.user.doctorprofile.rmis_location
        ret["rmis_login"] = request.user.doctorprofile.rmis_login
        ret["rmis_password"] = request.user.doctorprofile.rmis_password
        ret["department"] = {"pk": request.user.doctorprofile.podrazdeleniye_id,
                             "title": request.user.doctorprofile.podrazdeleniye.title}
        ret["restricted"] = [x.pk for x in request.user.doctorprofile.restricted_to_direct.all()]
        ret["user_services"] = [x.pk for x in
                                request.user.doctorprofile.users_services.all() if x not in ret["restricted"]]
        ret["su"] = request.user.is_superuser

        en = SettingManager.en()
        ret["extended_departments"] = {}

        st_base = ResearchSite.objects.filter(hide=False).order_by('title')
        for e in en:
            if e < 4 or not en[e]:
                continue

            t = e - 4
            has_def = DResearches.objects.filter(hide=False, site_type__isnull=True,
                                                 **DResearches.filter_type(e)).exists()

            if has_def:
                d = [
                    {
                        "pk": None,
                        "title": 'Общие',
                        'type': t,
                        "extended": True,
                    }
                ]
            else:
                d = []

            ret["extended_departments"][e] = [
                *d,
                *[{
                    "pk": x.pk,
                    "title": x.title,
                    "type": t,
                    "extended": True,
                    'e': e,
                } for x in st_base.filter(site_type=t)]
            ]
    return JsonResponse(ret)


@login_required
def directive_from(request):
    from users.models import DoctorProfile
    data = []
    for dep in Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.DEPARTMENT).order_by('title'):
        d = {"pk": dep.pk,
             "title": dep.title,
             "docs": [{"pk": x.pk, "fio": x.fio} for x in DoctorProfile.objects.filter(podrazdeleniye=dep,
                                                                                       user__groups__name="Лечащий врач").order_by(
                 "fio")]
             }
        data.append(d)

    return JsonResponse({"data": data})


@group_required("Оформление статталонов", "Лечащий врач", "Оператор лечащего врача")
def statistics_tickets_types(request):
    result = {"visit": [{"pk": x.pk, "title": x.title} for x in VisitPurpose.objects.filter(hide=False).order_by("pk")],
              "result": [{"pk": x.pk, "title": x.title} for x in
                         ResultOfTreatment.objects.filter(hide=False).order_by("pk")],
              "outcome": [{"pk": x.pk, "title": x.title} for x in
                          Outcomes.objects.filter(hide=False).order_by("pk")],
              "exclude": [{"pk": x.pk, "title": x.title} for x in
                          ExcludePurposes.objects.filter(hide=False).order_by("pk")]}
    return JsonResponse(result)


@group_required("Оформление статталонов", "Лечащий врач", "Оператор лечащего врача")
def statistics_tickets_send(request):
    response = {"ok": True}
    rd = json.loads(request.body)
    ofname = rd.get("ofname") or -1
    doc = None
    if ofname > -1 and users.DoctorProfile.objects.filter(pk=ofname).exists():
        doc = users.DoctorProfile.objects.get(pk=ofname)
    t = StatisticsTicket(card=Card.objects.get(pk=rd["card_pk"]),
                         purpose=VisitPurpose.objects.get(pk=rd["visit"]),
                         result=ResultOfTreatment.objects.get(pk=rd["result"]),
                         info=rd["info"].strip(),
                         first_time=rd["first_time"],
                         primary_visit=rd["primary_visit"],
                         dispensary_registration=int(rd["disp"]),
                         doctor=doc or request.user.doctorprofile,
                         creator=request.user.doctorprofile,
                         outcome=Outcomes.objects.filter(pk=rd["outcome"]).first(),
                         dispensary_exclude_purpose=ExcludePurposes.objects.filter(pk=rd["exclude"]).first(),
                         dispensary_diagnos=rd["disp_diagnos"],
                         date_ticket=rd.get("date_ticket", None))
    t.save()
    Log(key="", type=7000, body=json.dumps(rd), user=request.user.doctorprofile).save()
    return JsonResponse(response)


@group_required("Оформление статталонов", "Лечащий врач", "Оператор лечащего врача")
def statistics_tickets_get(request):
    response = {"data": []}
    request_data = json.loads(request.body)
    date_start, date_end = try_parse_range(request_data["date"])
    n = 0
    for row in StatisticsTicket.objects.filter(
            Q(doctor=request.user.doctorprofile) | Q(creator=request.user.doctorprofile)).filter(
            date__range=(date_start, date_end,)).order_by('pk'):
        if not row.invalid_ticket:
            n += 1
        response["data"].append({
            "pk": row.pk,
            "n": n if not row.invalid_ticket else '',
            "doc": row.doctor.get_fio(),
            "date_ticket": row.get_date(),
            "department": row.doctor.podrazdeleniye.get_title(),
            "patinet": row.card.individual.fio(full=True),
            "card": row.card.number_with_type(),
            "purpose": row.purpose.title if row.purpose else "",
            "first_time": row.first_time,
            "primary": row.primary_visit,
            "info": row.info,
            "disp": row.get_dispensary_registration_display()
            + (" (" + row.dispensary_diagnos + ")" if row.dispensary_diagnos != "" else "")
            + (" (" + row.dispensary_exclude_purpose.title + ")" if row.dispensary_exclude_purpose else ""),
            "result": row.result.title if row.result else "",
            "outcome": row.outcome.title if row.outcome else "",
            "invalid": row.invalid_ticket,
            "can_invalidate": row.can_invalidate()
        })
    return JsonResponse(response)


@group_required("Оформление статталонов", "Лечащий врач", "Оператор лечащего врача")
def statistics_tickets_invalidate(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    if StatisticsTicket.objects.filter(
            Q(doctor=request.user.doctorprofile) | Q(creator=request.user.doctorprofile)).filter(
            pk=request_data.get("pk", -1)).exists():
        if StatisticsTicket.objects.get(pk=request_data["pk"]).can_invalidate():
            for s in StatisticsTicket.objects.filter(pk=request_data["pk"]):
                s.invalid_ticket = request_data.get("invalid", False)
                s.save()
            response["ok"] = True
            Log(key=str(request_data["pk"]), type=7001, body=json.dumps(request_data.get("invalid", False)),
                user=request.user.doctorprofile).save()
        else:
            response["message"] = "Время на отмену или возврат истекло"
    return JsonResponse(response)


def delete_keys_from_dict(dict_del, lst_keys):
    for k in lst_keys:
        try:
            del dict_del[k]
        except KeyError:
            pass
    for v in dict_del.values():
        if isinstance(v, dict):
            delete_keys_from_dict(v, lst_keys)
        if isinstance(v, list):
            for ll in v:
                delete_keys_from_dict(ll, lst_keys)
    return dict_del


def get_reset_time_vars(n):
    ctp = int(0 if not n.visit_date else int(time.mktime(timezone.localtime(n.visit_date).timetuple())))
    ctime = int(time.time())
    cdid = -1 if not n.visit_who_mark else n.visit_who_mark_id
    rt = SettingManager.get("visit_reset_time_min", default="20.0", default_type='f') * 60
    return cdid, ctime, ctp, rt


def mkb10(request):
    kw = request.GET.get("keyword", "").split(' ')[0]
    data = []
    for d in directions.Diagnoses.objects.filter(d_type="mkb10.4", code__istartswith=kw).order_by("code").distinct()[:11]:
        data.append({"pk": d.pk, "code": d.code, "title": d.title})
    return JsonResponse({"data": data})


def methods_of_taking(request):
    prescription = request.GET.get("prescription", "")
    kw = request.GET.get("keyword", "")
    data = []
    m = directions.MethodsOfTaking.objects.filter(drug_prescription=prescription, method_of_taking__istartswith=kw).order_by("-count").distinct()[:10]
    for d in m:
        data.append({"pk": d.pk, "method_of_taking": d.method_of_taking})
    return JsonResponse({"data": data})


def key_value(request):
    key = request.GET.get("key", "")
    value = request.GET.get("value", "").strip()
    limit = int(request.GET.get("limit", "10"))
    data = []
    for v in directions.KeyValue.objects.filter(key=key, value__istartswith=value).order_by("value").distinct()[:limit]:
        data.append({"pk": v.pk, "key": v.key, "value": v.value})
    return JsonResponse({"data": data})


def vich_code(request):
    kw = request.GET.get("keyword", "")
    data = []
    for d in directions.Diagnoses.objects.filter(code__istartswith=kw, d_type="vc").order_by("code")[:11]:
        data.append({"pk": d.pk, "code": d.code, "title": {"-": ""}.get(d.title, d.title)})
    return JsonResponse({"data": data})


@login_required
@group_required("Подтверждение отправки результатов в РМИС")
def rmis_confirm_list(request):
    request_data = json.loads(request.body)
    data = {"directions": []}
    date_start, date_end = try_parse_range(request_data["date_from"], request_data["date_to"])
    d = directions.Napravleniya.objects.filter(istochnik_f__rmis_auto_send=False,
                                               force_rmis_send=False,
                                               issledovaniya__time_confirmation__range=(date_start, date_end)) \
        .exclude(issledovaniya__time_confirmation__isnull=True).distinct().order_by("pk")
    data["directions"] = [{
        "pk": x.pk,
        "patient": {
            "fiodr": x.client.individual.fio(full=True),
            "card": x.client.number_with_type()
        },
        "fin": x.istochnik_f.title
    } for x in d]
    return JsonResponse(data)


@csrf_exempt
def flg(request):
    ok = False
    dpk = request.POST["directionId"]
    content = request.POST["content"]
    date = try_strptime(request.POST["date"])
    doc_f = request.POST["doc"].lower()
    ds = directions.Napravleniya.objects.filter(pk=dpk)
    if ds.exists():
        d = ds[0]
        iss = directions.Issledovaniya.objects.filter(napravleniye=d, research__code="A06.09.006")
        if iss.exists():
            i = iss[0]
            doc = None
            gi = None
            for u in users.DoctorProfile.objects.filter(podrazdeleniye=i.research.podrazdeleniye):
                if u.get_fio().lower() == doc_f or (not doc and u.has_group('Врач параклиники')):
                    doc = u

                gis = ParaclinicInputField.objects.filter(group__research=i.research, group__title="Заключение")
                if gis.exists():
                    gi = gis[0]
            if doc and gi:
                if not directions.ParaclinicResult.objects.filter(issledovaniye=i, field=gi).exists():
                    f_result = directions.ParaclinicResult(issledovaniye=i, field=gi, value="")
                else:
                    f_result = directions.ParaclinicResult.objects.filter(issledovaniye=i, field=gi)[0]
                if f_result.value != content:
                    f_result.value = content
                    f_result.save()
                if i.doc_save != doc or i.time_save != date or i.doc_confirmation != doc or i.time_confirmation != date:
                    i.doc_save = doc
                    i.time_save = date
                    i.doc_confirmation = doc
                    i.time_confirmation = date
                    i.save()

                if not i.napravleniye.visit_who_mark or not i.napravleniye.visit_date:
                    i.napravleniye.visit_who_mark = doc
                    i.napravleniye.visit_date = date
                    i.napravleniye.save()

    return JsonResponse({"ok": ok})


def search_template(request):
    result = []
    q = request.GET.get('q', '')
    if q != '':
        for r in users.AssignmentTemplates.objects.filter(title__istartswith=q, global_template=False).order_by(
                'title')[:10]:
            result.append({"pk": r.pk, "title": r.title, "researches": [x.research.pk for x in
                                                                        users.AssignmentResearches.objects.filter(
                                                                            template=r, research__hide=False)]})
    return JsonResponse({"result": result, "q": q})


def load_templates(request):
    result = []
    t = request.GET.get('type', '1')
    for r in users.AssignmentTemplates.objects.filter(global_template=t == '1').order_by('title'):
        result.append({"pk": r.pk, "title": r.title, "researches": [x.research.pk for x in
                                                                    users.AssignmentResearches.objects.filter(
                                                                        template=r, research__hide=False)]})
    return JsonResponse({"result": result})


def get_template(request):
    title = ''
    researches = []
    global_template = False
    pk = request.GET.get('pk')
    if pk:
        t = users.AssignmentTemplates.objects.get(pk=pk)
        title = t.title
        researches = [x.research_id for x in
                      users.AssignmentResearches.objects.filter(template=t, research__hide=False)]
        global_template = t.global_template
    return JsonResponse({"title": title, "researches": researches, "global_template": global_template})


@login_required
@group_required("Конструктор: Настройка шаблонов")
def update_template(request):
    response = {"ok": False}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -2)
    if pk > -2:
        title = request_data.get("title").strip()
        researches = request_data["researches"]
        global_template = request_data["global_template"]
        if len(title) > 0 and len(researches) > 0:
            t = None
            if pk == -1:
                t = users.AssignmentTemplates(title=title, global_template=global_template)
                t.save()
                pk = t.pk
            if users.AssignmentTemplates.objects.filter(pk=pk).exists():
                t = users.AssignmentTemplates.objects.get(pk=pk)
                t.title = title
                t.global_template = global_template
                t.save()
            if t:
                users.AssignmentResearches.objects.filter(template=t).exclude(research__pk__in=researches).delete()
                to_add = [x for x in researches if
                          not users.AssignmentResearches.objects.filter(template=t, research__pk=x).exists()]
                for ta in to_add:
                    if DResearches.objects.filter(pk=ta).exists():
                        users.AssignmentResearches(template=t, research=DResearches.objects.get(pk=ta)).save()
                response["ok"] = True
    return JsonResponse(response)


def modules_view(request):
    return JsonResponse({
        "l2_cards": SettingManager.get("l2_cards_module", default='false', default_type='b')
    })


def autocomplete(request):
    t = request.GET.get("type")
    v = request.GET.get("value", "")
    limit = request.GET.get("limit", 10)
    data = []
    if v != "" and limit > 0:
        if t == "fias":
            data = fias.suggest(v)
        if t == "name":
            p = Individual.objects.filter(name__istartswith=v).distinct('name')[:l]
            if p.exists():
                data = [x.name for x in p]
        if t == "family":
            p = Individual.objects.filter(family__istartswith=v).distinct('family')[:l]
            if p.exists():
                data = [x.family for x in p]
        if t == "patronymic":
            p = Individual.objects.filter(patronymic__istartswith=v).distinct('patronymic')[:l]
            if p.exists():
                data = [x.patronymic for x in p]
        if t == "work_place":
            p = Card.objects.filter(work_place__istartswith=v).distinct('work_place')[:l]
            if p.exists():
                data = [x.work_place for x in p]
        if t == "main_diagnosis":
            p = Card.objects.filter(main_diagnosis__istartswith=v).distinct('main_diagnosis')[:l]
            if p.exists():
                data = [x.main_diagnosis for x in p]
        if t == "work_position":
            p = Card.objects.filter(work_position__istartswith=v).distinct('work_position')[:l]
            if p.exists():
                data = [x.work_position for x in p]
        if "who_give:" in t:
            tpk = t.split(":")[1]
            p = Document.objects.filter(document_type__pk=tpk, who_give__istartswith=v).distinct('who_give')[:l]
            if p.exists():
                data = [x.who_give for x in p]
    return JsonResponse({"data": data})


def laborants(request):
    data = []
    if SettingManager.l2('results_laborants'):
        data = [{"pk": '-1', "fio": 'Не выбрано'}]
        for d in users.DoctorProfile.objects.filter(user__groups__name="Лаборант", podrazdeleniye__p_type=users.Podrazdeleniya.LABORATORY).order_by('fio'):
            data.append({"pk": str(d.pk), "fio": d.fio})
    return JsonResponse({"data": data,
                         "doc": request.user.doctorprofile.has_group("Врач-лаборант")})


@login_required
@group_required("Создание и редактирование пользователей")
def users_view(request):
    data = []

    podr = Podrazdeleniya.objects.all().order_by("title")
    for x in podr:
        otd = {"pk": x.pk, "title": x.title, "users": []}
        docs = users.DoctorProfile.objects.filter(podrazdeleniye=x).order_by('fio')
        if not request.user.is_superuser:
            docs = docs.filter(user__is_superuser=False)
        for y in docs:
            otd["users"].append({"pk": y.pk, "fio": y.get_fio(), "username": y.user.username})
        data.append(otd)

    return JsonResponse({"departments": data})


@login_required
@group_required("Создание и редактирование пользователей")
def user_view(request):
    request_data = json.loads(request.body)
    pk = request_data["pk"]
    if pk == -1:
        data = {
            "fio": '',
            "username": '',
            "department": '',
            "groups": [],
            "restricted_to_direct": [],
            "users_services": [],
            "groups_list": [{"pk": x.pk, "title": x.name} for x in Group.objects.all()],
            "password": '',
            "rmis_location": '',
            "rmis_login": '',
            "rmis_password": '',
            "doc_pk": -1,
        }
    else:
        doc = users.DoctorProfile.objects.get(pk=pk)

        data = {
            "fio": doc.fio,
            "username": doc.user.username,
            "department": doc.podrazdeleniye_id,
            "groups": [x.pk for x in doc.user.groups.all()],
            "restricted_to_direct": [x.pk for x in doc.restricted_to_direct.all()],
            "users_services": [x.pk for x in doc.users_services.all()],
            "groups_list": [{"pk": x.pk, "title": x.name} for x in Group.objects.all()],
            "password": '',
            "rmis_location": doc.rmis_location or '',
            "rmis_login": doc.rmis_login or '',
            "rmis_password": '',
            "doc_pk": doc.user.pk,
        }

    return JsonResponse({"user": data})


@login_required
@group_required("Создание и редактирование пользователей")
def user_save_view(request):
    request_data = json.loads(request.body)
    pk = request_data["pk"]
    ok = True
    message = ""
    ud = request_data["user_data"]
    username = ud["username"]
    rmis_location = str(ud["rmis_location"]).strip() or None
    rmis_login = ud["rmis_login"].strip() or None
    rmis_password = ud["rmis_password"].strip() or None
    npk = pk
    if pk == -1:
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(username)
            user.is_active = True
            user.save()
            doc = users.DoctorProfile(user=user, fio=ud["fio"])
            doc.save()
            npk = doc.pk
        else:
            ok = False
            message = "Имя пользователя уже занято"
            doc = None
    else:
        doc = users.DoctorProfile.objects.get(pk=pk)
    if pk and doc and (not doc.user.is_superuser or request.user.is_superuser):
        if ud["password"] != '':
            doc.user.set_password(ud["password"])
            doc.user.save()
        if pk != -1 and doc.user.username != ud['username']:
            if not User.objects.filter(username=username).exists():
                doc.user.username = username
                doc.user.save()
            else:
                ok = False
                message = "Имя пользователя уже занято"

        if ok:
            doc.user.groups.clear()
            for g in ud["groups"]:
                group = Group.objects.get(pk=g)
                doc.user.groups.add(group)
            doc.user.save()

            doc.restricted_to_direct.clear()
            for r in ud["restricted_to_direct"]:
                doc.restricted_to_direct.add(DResearches.objects.get(pk=r))

            doc.users_services.clear()
            for r in ud["users_services"]:
                doc.users_services.add(DResearches.objects.get(pk=r))

            doc.podrazdeleniye_id = ud['department']
            doc.fio = ud["fio"]
            doc.rmis_location = rmis_location
            if rmis_login:
                doc.rmis_login = rmis_login
                if rmis_password:
                    doc.rmis_password = rmis_password
            else:
                doc.rmis_login = None
                doc.rmis_password = None
            doc.save()
    return JsonResponse({"ok": ok, "npk": npk, "message": message})


@login_required
def user_location(request):
    request_data = json.loads(request.body)
    date = request_data["date"]
    d = {}
    rl = request.user.doctorprofile.rmis_location
    if rl and SettingManager.get("l2_rmis_queue", default='false', default_type='b'):
        from rmis_integration.client import Client
        c = Client(modules=['patients'])
        d = c.patients.get_reserves(date, rl)

        def slot_status(x):
            s = 0
            pk = None
            n = directions.Napravleniya.objects.filter(rmis_slot_id=x["slot"]).first()
            if n:
                pk = n.pk
                s = 1
                if n.is_all_confirm():
                    s = 2
            return {"code": s, "direction": pk}

        d = list(map(lambda x: {**x, "status": slot_status(x)}, d))
    return JsonResponse({"data": d})


@login_required
def user_get_reserve(request):
    request_data = json.loads(request.body)
    pk = request_data["pk"]
    patient_uid = request_data["patient"]
    rl = request.user.doctorprofile.rmis_location
    if rl:
        from rmis_integration.client import Client
        c = Client(modules=['patients'])
        d = c.patients.get_slot(pk)
        n = directions.Napravleniya.objects.filter(rmis_slot_id=pk).first()
        d["direction"] = n.pk if n else None
        ds = directions.Issledovaniya.objects.filter(napravleniye=n, napravleniye__isnull=False).first()
        d['direction_service'] = ds.research_id if ds else -1
        if d:
            return JsonResponse({
                **d,
                "datetime": d["datetime"].strftime('%d.%m.%Y %H:%M'),
                "patient_uid": patient_uid,
                "pk": int(str(pk)[1:]),
            })
    return JsonResponse({})


@login_required
def user_fill_slot(request):
    slot = json.loads(request.body).get('slot', {})
    slot_data = slot.get('data', {})
    if directions.Napravleniya.objects.filter(rmis_slot_id=slot["id"]).exists():
        direction = directions.Napravleniya.objects.filter(rmis_slot_id=slot["id"])[0].pk
    else:
        result = directions.Napravleniya.gen_napravleniya_by_issledovaniya(slot["card_pk"],
                                                                           "",
                                                                           None,
                                                                           "",
                                                                           None,
                                                                           request.user.doctorprofile,
                                                                           {-1: [slot_data["direction_service"]]},
                                                                           {},
                                                                           False,
                                                                           {},
                                                                           vich_code="",
                                                                           count=1,
                                                                           discount=0,
                                                                           parent_iss=None,
                                                                           rmis_slot=slot["id"])
        direction = result["list_id"][0]
    return JsonResponse({"direction": direction})


@login_required
def job_types(request):
    types = [{"pk": x.pk, "title": x.title} for x in directions.TypeJob.objects.filter(hide=False)]
    g = Group.objects.filter(name="Зав. лабораторией").first()
    is_zav_lab = (g and g in request.user.groups.all()) or request.user.is_superuser
    users_list = [request.user.doctorprofile.get_data()]
    if is_zav_lab:
        for user in users.DoctorProfile.objects.filter(user__groups__name__in=["Лаборант", "Врач-лаборант"])\
                .exclude(pk=request.user.doctorprofile.pk).order_by("fio").distinct():
            users_list.append(user.get_data())
    return JsonResponse({"types": types, "is_zav_lab": is_zav_lab, "users": users_list})


@login_required
def job_save(request):
    data = json.loads(request.body)
    g = Group.objects.filter(name="Зав. лабораторией").first()
    ej = directions.EmployeeJob(type_job_id=data["type"], count=data["count"],
                                doc_execute_id=data["executor"], date_job=try_strptime(data["date"]).date())
    ej.save()
    return JsonResponse({"ok": True})


@login_required
def job_list(request):
    data = json.loads(request.body)
    date = try_strptime(data["date"]).date()
    g = Group.objects.filter(name="Зав. лабораторией").first()
    is_zav_lab = (g and g in request.user.groups.all()) or request.user.is_superuser
    users_list = [request.user.doctorprofile]
    if is_zav_lab:
        for user in users.DoctorProfile.objects.filter(user__groups__name__in=["Лаборант", "Врач-лаборант"])\
                .exclude(pk=request.user.doctorprofile.pk).order_by("fio").distinct():
            users_list.append(user)
    result = []
    for j in directions.EmployeeJob.objects.filter(doc_execute__in=users_list, date_job=date).order_by("doc_execute", "-time_save"):
        result.append({
            "pk": j.pk,
            "executor": j.doc_execute.get_fio(),
            "type": j.type_job.title,
            "count": j.count,
            "saved": strdatetime(j.time_save),
            "canceled": bool(j.who_do_cancel),
        })
    return JsonResponse({"list": result})


@login_required
def job_cancel(request):
    data = json.loads(request.body)
    j = directions.EmployeeJob.objects.get(pk=data["pk"])
    g = Group.objects.filter(name="Зав. лабораторией").first()
    is_zav_lab = (g and g in request.user.groups.all()) or request.user.is_superuser
    if is_zav_lab or j.doc_execute == request.user.doctorprofile:
        if data["cancel"]:
            j.canceled_at = timezone.now()
            j.who_do_cancel = request.user.doctorprofile
        else:
            j.canceled_at = j.who_do_cancel = None
        j.save()
    return JsonResponse({"ok": True})
