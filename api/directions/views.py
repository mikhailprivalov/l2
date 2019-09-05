import collections
import time
from operator import itemgetter

import simplejson as json
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.utils import dateformat, timezone

from api.views import get_reset_time_vars
from appconf.manager import SettingManager
from clients.models import Card, Individual, DispensaryReg, BenefitReg
from directions.models import Napravleniya, Issledovaniya, Result, ParaclinicResult, Recipe, MethodsOfTaking
from directory.models import Fractions, ParaclinicInputGroups, ParaclinicTemplateName, ParaclinicInputField
from laboratory import settings
from laboratory.decorators import group_required
from laboratory.utils import strdatetime, strdate, tsdatetime, localtime
from results.views import result_normal
from rmis_integration.client import Client, get_direction_full_data_cache
from slog.models import Log
from statistics_tickets.models import VisitPurpose, ResultOfTreatment, Outcomes
from utils.dates import try_parse_range


@login_required
@group_required("Лечащий врач", "Оператор лечащего врача")
def directions_generate(request):
    result = {"ok": False, "directions": [], "message": ""}
    if request.method == "POST":
        p = json.loads(request.body)
        type_card = Card.objects.get(pk = p.get("card_pk"))
        if type_card.base.forbidden_create_napr:
            result["message"] = "Для данного типа карт нельзя создать направления"
            return JsonResponse(result)
        rc = Napravleniya.gen_napravleniya_by_issledovaniya(p.get("card_pk"),
                                                            p.get("diagnos"),
                                                            p.get("fin_source"),
                                                            p.get("history_num"),
                                                            p.get("ofname_pk"),
                                                            request.user.doctorprofile,
                                                            p.get("researches"),
                                                            p.get("comments"),
                                                            p.get("for_rmis"),
                                                            p.get("rmis_data", {}),
                                                            vich_code=p.get("vich_code", ""),
                                                            count=p.get("count", 1),
                                                            discount=p.get("discount", 0),
                                                            parent_iss=p.get("parent_iss", None),
                                                            counts=p.get("counts", {}))
        result["ok"] = rc["r"]
        result["directions"] = rc["list_id"]
        if "message" in rc:
            result["message"] = rc["message"]
    return JsonResponse(result)


@login_required
def directions_history(request):
    res = {"directions": []}
    request_data = json.loads(request.body)

    pk = request_data.get("patient", -1)
    req_status = request_data.get("type", 4)
    iss_pk = request_data.get("iss_pk", None)
    services = request_data.get("services", [])
    services = list(map(int, services or []))

    date_start, date_end = try_parse_range(request_data["date_from"], request_data["date_to"])
    try:
        if pk >= 0 or req_status == 4 or iss_pk:
            if iss_pk:
                rows = Napravleniya.objects.filter(parent_id=iss_pk).order_by("data_sozdaniya").prefetch_related()
            elif req_status != 4:
                rows = Napravleniya.objects.filter(data_sozdaniya__range=(date_start, date_end),
                                                   client__pk=pk).order_by(
                    "-data_sozdaniya").prefetch_related()
            else:
                rows = Napravleniya.objects.filter(Q(data_sozdaniya__range=(date_start, date_end),
                                                     doc_who_create=request.user.doctorprofile)
                                                   | Q(data_sozdaniya__range=(date_start, date_end),
                                                       doc=request.user.doctorprofile)).order_by(
                    "-data_sozdaniya")

            if services:
                rows = rows.filter(issledovaniya__research__pk__in=services)

            for napr in rows.values("pk", "data_sozdaniya", "cancel"):
                iss_list = Issledovaniya.objects.filter(napravleniye__pk=napr["pk"]).prefetch_related(
                    "tubes", "research", "research__podrazdeleniye")
                if not iss_list.exists():
                    continue
                status = 2  # 0 - выписано. 1 - Материал получен лабораторией. 2 - результат подтвержден. -1 - отменено
                has_conf = False
                researches_list = []
                researches_pks = []
                has_descriptive = False
                for v in iss_list:
                    if not has_descriptive and v.research.desc:
                        has_descriptive = True
                    researches_list.append(v.research.title)
                    researches_pks.append(v.research_id)
                    iss_status = 1
                    if not v.doc_confirmation and not v.doc_save and not v.deferred:
                        iss_status = 1
                        if v.tubes.count() == 0:
                            iss_status = 0
                        else:
                            for t in v.tubes.all():
                                if not t.time_recive:
                                    iss_status = 0
                    elif v.doc_confirmation or v.deferred:
                        iss_status = 2
                    if v.doc_confirmation and not has_conf:
                        has_conf = True
                    status = min(iss_status, status)
                if status == 2 and not has_conf:
                    status = 1
                if req_status in [3, 4] or req_status == status or iss_pk:
                    res["directions"].append(
                        {"pk": napr["pk"], "status": -1 if status == 0 and napr["cancel"] else status,
                         "researches": ' | '.join(researches_list),
                         "researches_pks": researches_pks,
                         "date": str(dateformat.format(localtime(napr["data_sozdaniya"]).date(), settings.DATE_FORMAT_SHORT)),
                         "lab": "Консультации" if not iss_list[0].research.get_podrazdeleniye() or iss_list[
                             0].research.is_doc_refferal
                         else iss_list[0].research.get_podrazdeleniye().title, "cancel": napr["cancel"],
                         "checked": False,
                         "has_descriptive": has_descriptive})
    except (ValueError, IndexError) as e:
        res["message"] = str(e)
    return JsonResponse(res)


@login_required
def directions_rmis_directions(request):
    request_data = json.loads(request.body)
    pk = request_data.get("pk")
    rows = []
    if pk and Card.objects.filter(pk=pk, base__is_rmis=True).exists():
        c = Client(modules=["directions", "services"])
        sd = c.directions.get_individual_active_directions(Card.objects.get(pk=pk).number)
        dirs_data = [c.directions.get_direction_full_data(x) for x in sd if
                     not Napravleniya.objects.filter(rmis_number=x).exists()]
        rows = [x for x in dirs_data if x]
    return JsonResponse({"rows": rows})


@login_required
def directions_rmis_direction(request):
    request_data = json.loads(request.body)
    data = {}
    pk = request_data.get("pk")
    if pk and not Napravleniya.objects.filter(rmis_number=pk).exists():
        data = get_direction_full_data_cache(pk)
        if not data:
            c = Client(modules=["directions", "services"])
            data = c.directions.get_direction_full_data(pk)
    return JsonResponse(data)


@login_required
def directions_cancel(request):
    response = {"cancel": False}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    if Napravleniya.objects.filter(pk=pk).exists():
        direction = Napravleniya.objects.get(pk=pk)
        direction.cancel = not direction.cancel
        direction.save()
        response["cancel"] = direction.cancel
    return JsonResponse(response)


@login_required
def directions_results(request):
    result = {"ok": False,
              "direction": {"pk": -1, "doc": "", "date": ""},
              "client": {},
              "full": False}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    if Napravleniya.objects.filter(pk=pk).exists():
        napr = Napravleniya.objects.get(pk=pk)
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

        iss_list = Issledovaniya.objects.filter(napravleniye=napr)
        t = 0
        if not iss_list.filter(doc_confirmation__isnull=True).exists() or iss_list.filter(deferred=False).exists():
            result["direction"]["pk"] = napr.pk
            result["full"] = False
            result["ok"] = True
            if iss_list.filter(doc_confirmation__isnull=False).exists():
                result["direction"]["doc"] = iss_list.filter(doc_confirmation__isnull=False)[
                    0].doc_confirmation.get_fio()
                if iss_list.filter(doc_confirmation__isnull=True, deferred=False).exists():
                    result["direction"]["doc"] = result["direction"]["doc"] + " (выполнено не полностью)"
                else:
                    result["full"] = True
            else:
                result["direction"]["doc"] = "Не подтверждено"
            result["direction"]["date"] = maxdate

            result["client"]["sex"] = napr.client.individual.sex
            result["client"]["fio"] = napr.client.individual.fio()
            result["client"]["age"] = napr.client.individual.age_s(direction=napr)
            result["client"]["cardnum"] = napr.client.number_with_type()
            result["client"]["dr"] = napr.client.individual.bd()

            result["results"] = collections.OrderedDict()
            isses = []
            for issledovaniye in iss_list.order_by("tubes__id", "research__sort_weight"):
                if issledovaniye.pk in isses:
                    continue
                isses.append(issledovaniye.pk)
                t += 1
                kint = "%s_%s_%s_%s" % (t,
                                        "-1" if not issledovaniye.research.direction else issledovaniye.research.direction_id,
                                        issledovaniye.research.sort_weight,
                                        issledovaniye.research_id)
                result["results"][kint] = {"title": issledovaniye.research.title,
                                           "fractions": collections.OrderedDict(),
                                           "sort": issledovaniye.research.sort_weight,
                                           "tube_time_get": ""}
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
                            pk = res.fraction_id
                        if res.fraction.render_type == 0:
                            if pk not in result["results"][kint]["fractions"].keys():
                                result["results"][kint]["fractions"][pk] = {}

                            result["results"][kint]["fractions"][pk]["result"] = result_normal(res.value)
                            result["results"][kint]["fractions"][pk]["title"] = res.fraction.title
                            result["results"][kint]["fractions"][pk]["units"] = res.get_units()
                            refs = res.get_ref(full=True)
                            ref_m = refs["m"]
                            ref_f = refs["f"]
                            if isinstance(ref_m, str):
                                ref_m = json.loads(ref_m)
                            if isinstance(ref_f, str):
                                ref_f = json.loads(ref_f)
                            result["results"][kint]["fractions"][pk]["ref_m"] = ref_m
                            result["results"][kint]["fractions"][pk]["ref_f"] = ref_f
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
                                result["results"][kint]["fractions"][tmp_pk]["ref_m"] = {}
                                result["results"][kint]["fractions"][tmp_pk]["ref_f"] = {}
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
                                    result["results"][kint]["fractions"][tmp_pk]["ref_m"] = {}
                                    result["results"][kint]["fractions"][tmp_pk]["ref_f"] = {}
                                    result["results"][kint]["fractions"][tmp_pk]["units"] = ""

                            n += 1
                            tmp_pk = "%d_%d" % (pk, n)
                            if tmp_pk not in result["results"][kint]["fractions"].keys():
                                result["results"][kint]["fractions"][tmp_pk] = {}
                            result["results"][kint]["fractions"][tmp_pk][
                                "title"] = "S - чувствителен; R - резистентен; I - промежуточная чувствительность;"
                            result["results"][kint]["fractions"][tmp_pk]["result"] = ""
                            result["results"][kint]["fractions"][tmp_pk]["ref_m"] = {}
                            result["results"][kint]["fractions"][tmp_pk]["ref_f"] = {}
                            result["results"][kint]["fractions"][tmp_pk]["units"] = ""
                    if issledovaniye.lab_comment and issledovaniye.lab_comment != "":
                        n += 1
                        tmp_pk = "%d_%d" % (pk, n)
                        if tmp_pk not in result["results"][kint]["fractions"].keys():
                            result["results"][kint]["fractions"][tmp_pk] = {}
                        result["results"][kint]["fractions"][tmp_pk]["title"] = "Комментарий"
                        result["results"][kint]["fractions"][tmp_pk]["result"] = issledovaniye.lab_comment.replace("\n",
                                                                                                                   "<br/>")
                        result["results"][kint]["fractions"][tmp_pk]["ref_m"] = {}
                        result["results"][kint]["fractions"][tmp_pk]["ref_f"] = {}
                        result["results"][kint]["fractions"][tmp_pk]["units"] = ""
                else:
                    fr_list = Fractions.objects.filter(research=issledovaniye.research)
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
                            ref_m = json.loads(ref_m)
                        if not isinstance(ref_f, str):
                            ref_f = json.loads(ref_f)
                        result["results"][kint]["fractions"][pk]["ref_m"] = ref_m  # Референсы М
                        result["results"][kint]["fractions"][pk]["ref_f"] = ref_f  # Референсы Ж

    return JsonResponse(result)


@group_required("Врач параклиники", "Посещения по направлениям", "Врач консультаций")
def directions_services(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    if pk >= 4600000000000:
        pk -= 4600000000000
        pk //= 10
    f = False
    dn = Napravleniya.objects.filter(pk=pk)
    if dn.exists():
        n = dn[0]
        if Issledovaniya.objects.filter(
                Q(research__is_paraclinic=True) | Q(research__is_doc_refferal=True) | Q(
                    research__is_microbiology=True)).exists():
            cdid, ctime, ctp, rt = get_reset_time_vars(n)

            response["ok"] = True
            researches = []
            tubes = []
            has_microbiology = False
            for i in Issledovaniya.objects.filter(napravleniye=n).filter(
                    Q(research__is_paraclinic=True) | Q(research__is_doc_refferal=True) | Q(
                        research__is_microbiology=True)).distinct():
                researches.append({"title": i.research.title,
                                   "department": "" if not i.research.podrazdeleniye else i.research.podrazdeleniye.get_title(),
                                   "is_microbiology": i.research.is_microbiology})
                if i.research.is_microbiology:
                    has_microbiology = True
                    tubes.append({
                        "title": i.research.microbiology_tube.title,
                        "color": i.research.microbiology_tube.color,
                    })
            response["direction_data"] = {
                "date": strdate(n.data_sozdaniya),
                "client": n.client.individual.fio(full=True),
                "card": n.client.number_with_type(),
                "diagnos": n.diagnos,
                "tubes": tubes,
                "has_microbiology": has_microbiology,
                "doc": "" if not n.doc else "{}, {}".format(n.doc.get_fio(), n.doc.podrazdeleniye.title),
                "imported_from_rmis": n.imported_from_rmis,
                "imported_org": "" if not n.imported_org else n.imported_org.title,
                "visit_who_mark": "" if not n.visit_who_mark else "{}, {}".format(n.visit_who_mark.get_fio(),
                                                                                  n.visit_who_mark.podrazdeleniye.title),
                "fin_source": "" if not n.istochnik_f else "{} - {}".format(n.istochnik_f.base.title,
                                                                            n.istochnik_f.title),
            }
            response["researches"] = researches
            response["loaded_pk"] = pk
            response["visit_status"] = n.visit_date is not None
            response["visit_date"] = "" if not n.visit_date else strdatetime(n.visit_date)
            response["allow_reset_confirm"] = bool(((ctime - ctp < rt and cdid == request.user.doctorprofile.pk)
                                                     or request.user.is_superuser or "Сброс подтверждений результатов" in [
                                                     str(x) for x in
                                                     request.user.groups.all()]) and n.visit_date)
            f = True
    if not f:
        response["message"] = "Направление не найдено"
    return JsonResponse(response)


@group_required("Врач параклиники", "Посещения по направлениям", "Врач консультаций")
def directions_mark_visit(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    cancel = request_data.get("cancel", False)
    dn = Napravleniya.objects.filter(pk=pk)
    f = False
    if dn.exists():
        n = dn[0]
        if Issledovaniya.objects.filter(
                Q(research__is_paraclinic=True) | Q(research__is_doc_refferal=True)).exists():
            if not cancel:
                n.visit_date = timezone.now()
                n.visit_who_mark = request.user.doctorprofile
                n.save()
                cdid, ctime, ctp, rt = get_reset_time_vars(n)
                allow_reset_confirm = bool(((
                                                    ctime - ctp < rt and cdid == request.user.doctorprofile.pk) or request.user.is_superuser or "Сброс подтверждений результатов" in [
                                                str(x) for x in
                                                request.user.groups.all()]) and n.visit_date)
                response["visit_status"] = n.visit_date is not None
                response["visit_date"] = strdatetime(n.visit_date)
                response["allow_reset_confirm"] = allow_reset_confirm
                response["ok"] = True
            else:
                ctp = int(0 if not n.visit_date else int(time.mktime(timezone.localtime(n.visit_date).timetuple())))
                ctime = int(time.time())
                cdid = -1 if not n.visit_who_mark else n.visit_who_mark_id
                rtm = SettingManager.get("visit_reset_time_min", default="20.0", default_type='f')
                rt = rtm * 60
                allow_reset_confirm = bool(((
                                                    ctime - ctp < rt and cdid == request.user.doctorprofile.pk) or request.user.is_superuser or "Сброс подтверждений результатов" in [
                                                str(x) for x in
                                                request.user.groups.all()]) and n.visit_date)
                if allow_reset_confirm:
                    response["ok"] = True
                    response["visit_status"] = None
                    response["visit_date"] = ''
                    response["allow_reset_confirm"] = False
                    n.visit_date = None
                    n.visit_who_mark = None
                    n.save()
                else:
                    response["message"] = "Отмена посещения возможна только в течении {} мин.".format(rtm)
            Log(key=pk, type=5001,
                body=json.dumps(
                    {"Посещение": "отмена" if cancel else "да", "Дата и время": response["visit_date"]}),
                user=request.user.doctorprofile).save()
            f = True
    if not f:
        response["message"] = "Направление не найдено"
    return JsonResponse(response)


@group_required("Врач параклиники", "Посещения по направлениям", "Врач консультаций")
def directions_visit_journal(request):
    response = {"data": []}
    request_data = json.loads(request.body)
    date_start, date_end = try_parse_range(request_data["date"])
    for v in Napravleniya.objects.filter(visit_date__range=(date_start, date_end,),
                                         visit_who_mark=request.user.doctorprofile).order_by("-visit_date"):
        response["data"].append({
            "pk": v.pk,
            "client": v.client.individual.fio(full=True),
            "card": v.client.number_with_type(),
            "datetime": strdatetime(v.visit_date)
        })
    return JsonResponse(response)


@login_required
def directions_last_result(request):
    response = {"ok": False, "data": {}, "type": "result", "has_last_result": False}
    request_data = json.loads(request.body)
    individual = request_data.get("individual", -1)
    research = request_data.get("research", -1)
    i = Issledovaniya.objects.filter(napravleniye__client__individual__pk=individual,
                                     research__pk=research,
                                     time_confirmation__isnull=False).order_by("-time_confirmation").first()
    u = Issledovaniya.objects.filter(napravleniye__client__individual__pk=individual,
                                     research__pk=research,
                                     time_confirmation__isnull=True).order_by(
        "-napravleniye__data_sozdaniya").first()
    v = Issledovaniya.objects.filter(napravleniye__client__individual__pk=individual,
                                     research__pk=research,
                                     research__is_paraclinic=True,
                                     time_confirmation__isnull=True,
                                     napravleniye__visit_date__isnull=False).order_by(
        "-napravleniye__visit_date").first()
    if i:
        if not u or i.time_confirmation >= u.napravleniye.data_sozdaniya:
            response["ok"] = True
            if v and v.napravleniye.visit_date > i.time_confirmation:
                response["type"] = "visit"
                response["data"] = {"direction": u.napravleniye_id, "datetime": strdate(v.napravleniye.visit_date),
                                    "is_desc": i.research.desc,
                                    "ts": tsdatetime(v.napravleniye.visit_date)}
                response["has_last_result"] = True
                response["last_result"] = {"direction": i.napravleniye_id, "datetime": strdate(i.time_confirmation),
                                           "ts": tsdatetime(i.time_confirmation),
                                           "is_desc": i.research.desc,
                                           "is_doc_referral": i.research.is_doc_referral,
                                           "is_paraclinic": i.research.is_paraclinic}
            else:
                response["data"] = {"direction": i.napravleniye_id, "datetime": strdate(i.time_confirmation),
                                    "is_desc": i.research.desc,
                                    "is_doc_referral": i.research.is_doc_referral,
                                    "ts": tsdatetime(i.time_confirmation), "is_paraclinic": i.research.is_paraclinic}
        elif u:
            response["ok"] = True
            if v and v.napravleniye.visit_date > u.napravleniye.data_sozdaniya:
                response["type"] = "visit"
                response["data"] = {"direction": u.napravleniye_id, "datetime": strdate(v.napravleniye.visit_date),
                                   "is_desc": i.research.desc,
                                    "ts": tsdatetime(v.napravleniye.visit_date)}
            else:
                response["type"] = "direction"
                response["data"] = {"direction": u.napravleniye_id, "datetime": strdate(u.napravleniye.data_sozdaniya),
                                   "is_desc": i.research.desc,
                                    "ts": tsdatetime(u.napravleniye.data_sozdaniya)}
            response["has_last_result"] = True
            response["last_result"] = {"direction": i.napravleniye_id, "datetime": strdate(i.time_confirmation),
                                       "is_doc_referral": i.research.is_doc_referral,
                                       "ts": tsdatetime(i.time_confirmation), "is_paraclinic": i.research.is_paraclinic}
    elif u:
        response["ok"] = True
        if v and v.napravleniye.visit_date > u.napravleniye.data_sozdaniya:
            response["type"] = "visit"
            response["data"] = {"direction": u.napravleniye_id, "datetime": strdate(v.napravleniye.visit_date),
                                "ts": tsdatetime(v.napravleniye.visit_date)}
        else:
            response["type"] = "direction"
            response["data"] = {"direction": u.napravleniye_id, "datetime": strdate(u.napravleniye.data_sozdaniya),
                                "ts": tsdatetime(u.napravleniye.data_sozdaniya)}
    return JsonResponse(response)


@login_required
def directions_results_report(request):
    import re
    data = []
    request_data = json.loads(request.body)
    individual_pk = request_data.get("individual", -1)
    Log(key=str(individual_pk), type=20000, body=json.dumps(request_data), user=request.user.doctorprofile).save()
    params = request_data.get("params", [])

    date_start, date_end = try_parse_range(request_data.get("date_start"), request_data.get("date_end"))
    pat = re.compile(r"^\d+(.\d+)?-\d+(.\d+)?$")

    if Individual.objects.filter(pk=individual_pk).exists():
        i = Individual.objects.get(pk=individual_pk)
        for param in params:
            ppk = param["pk"]
            if param["is_paraclinic"]:
                if ParaclinicInputGroups.objects.filter(pk=ppk).exists():
                    g = ParaclinicInputGroups.objects.get(pk=ppk)
                    for i in Issledovaniya.objects.filter(research__paraclinicinputgroups=g,
                                                          time_confirmation__isnull=False):
                        res = []
                        for r in ParaclinicResult.objects.filter(field__group=g,
                                                                 issledovaniye=i).order_by("field__order"):
                            if r.value == "":
                                continue
                            res.append((r.field.title + ": " if r.field.title != "" else "") + r.value)

                        if len(res) == 0:
                            continue

                        paramdata = {"research": i.research_id,
                                     "pk": ppk,
                                     "order": g.order,
                                     "date": strdate(i.time_confirmation),
                                     "timestamp": tsdatetime(i.time_confirmation),
                                     "value": "; ".join(res),
                                     "units": "",
                                     "is_norm": "normal",
                                     "not_norm_dir": "",
                                     "delta": 0,
                                     "active_ref": {},
                                     "direction": i.napravleniye_id}
                        data.append(paramdata)
            else:
                if Fractions.objects.filter(pk=ppk).exists():
                    f = Fractions.objects.get(pk=ppk)
                    for r in Result.objects.filter(issledovaniye__napravleniye__client__individual=i,
                                                   fraction=f,
                                                   issledovaniye__time_confirmation__range=(
                                                           date_start, date_end)):
                        if r.value == "":
                            continue
                        is_norm = r.get_is_norm()
                        not_norm_dir = ""
                        delta = ""
                        active_ref = r.calc_normal(fromsave=False, only_ref=True)
                        if "r" in active_ref and re.match(r"^\d+(\.\d+)?$", r.value.replace(",", ".").strip()):
                            x = float(r.value.replace(",", ".").strip())
                            spl = r.calc_normal(fromsave=False, only_ref=True, raw_ref=False)
                            if (isinstance(spl, list) or isinstance(spl, tuple)) and len(spl) == 2:
                                if spl[0] >= x:
                                    not_norm_dir = "down"
                                    nx = spl[0] - x
                                    n10 = spl[0] * 0.2
                                    if nx <= n10:
                                        not_norm_dir = "n_down"
                                    delta = nx
                                elif spl[1] <= x:
                                    not_norm_dir = "up"
                                    nx = x - spl[1]
                                    n10 = spl[1] * 0.2
                                    if nx <= n10:
                                        not_norm_dir = "n_up"
                                    delta = nx

                        paramdata = {"research": f.research_id,
                                     "pk": ppk,
                                     "order": f.sort_weight,
                                     "date": strdate(r.issledovaniye.time_confirmation),
                                     "timestamp": tsdatetime(r.issledovaniye.time_confirmation),
                                     "value": r.value,
                                     "units": r.get_units(),
                                     "is_norm": is_norm,
                                     "not_norm_dir": not_norm_dir,
                                     "delta": delta,
                                     "active_ref": active_ref,
                                     "direction": r.issledovaniye.napravleniye_id}
                        data.append(paramdata)
    data.sort(key=itemgetter("timestamp"), reverse=True)
    data.sort(key=itemgetter("pk"))
    data.sort(key=itemgetter("order"))
    data.sort(key=itemgetter("research"))
    return JsonResponse({"data": data})


@group_required("Врач параклиники", "Врач консультаций")
def directions_paraclinic_form(request):
    import time
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1) or -1
    if pk >= 4600000000000:
        pk -= 4600000000000
        pk //= 10
    add_fr = {}
    f = False
    if not request.user.is_superuser:
        add_fr = dict(research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)

    dn = Napravleniya.objects.filter(pk=pk)
    if dn.exists():
        d = dn[0]
        df = Issledovaniya.objects.filter(napravleniye=d)
        df = df.filter(Q(research__is_paraclinic=True, **add_fr) | Q(research__is_doc_refferal=True)
                       | Q(research__is_treatment=True) | Q(research__is_stom=True) | Q(research__is_microbiology=True))
        df = df.distinct()

        if df.exists():
            response["ok"] = True
            response["has_doc_referral"] = False
            response["has_microbiology"] = False
            response["card_internal"] = d.client.base.internal_type
            response["patient"] = {
                "fio_age": d.client.individual.fio(full=True),
                "card": d.client.number_with_type(),
                "card_pk": d.client_id,
                "individual_pk": d.client.individual_id,
                "has_dreg": DispensaryReg.objects.filter(date_end__isnull=True, card=d.client).exists(),
                "has_benefit": BenefitReg.objects.filter(date_end__isnull=True, card=d.client).exists(),
                "doc": "" if not d.doc else (d.doc.get_fio(dots=True) + ", " + d.doc.podrazdeleniye.title),
                "imported_from_rmis": d.imported_from_rmis,
                "imported_org": "" if not d.imported_org else d.imported_org.title,
                "base": d.client.base_id,
            }
            response["direction"] = {
                "pk": d.pk,
                "date": strdate(d.data_sozdaniya),
                "diagnos": d.diagnos,
                "fin_source": "" if not d.istochnik_f else d.istochnik_f.title,
                "fin_source_id": d.istochnik_f_id,
                "tube": None,
            }

            response["researches"] = []
            for i in df:
                if i.research.is_doc_refferal:
                    response["has_doc_referral"] = True
                if i.research.is_microbiology and not response["has_microbiology"]:
                    response["has_microbiology"] = True
                    if i.research.microbiology_tube:
                        response["direction"]["tube"] = {
                            "type": i.research.microbiology_tube.title,
                            "color": i.research.microbiology_tube.color,
                            "get": i.get_visit_date(force=True),
                            "n": d.microbiology_n,
                        }
                ctp = int(0 if not i.time_confirmation else int(
                    time.mktime(timezone.localtime(i.time_confirmation).timetuple())))
                ctime = int(time.time())
                cdid = -1 if not i.doc_confirmation else i.doc_confirmation_id
                rt = SettingManager.get("lab_reset_confirm_time_min") * 60
                iss = {
                    "pk": i.pk,
                    "research": {
                        "title": i.research.title,
                        "is_paraclinic": i.research.is_paraclinic,
                        "is_doc_refferal": i.research.is_doc_refferal,
                        "is_treatment": i.research.is_treatment,
                        "is_stom": i.research.is_stom,
                        "groups": []
                    },
                    "examination_date": i.get_medical_examination(),
                    "templates": [],
                    "saved": i.time_save is not None,
                    "confirmed": i.time_confirmation is not None,
                    "allow_reset_confirm": ((ctime - ctp < rt and cdid == request.user.doctorprofile.pk)
                                             or request.user.is_superuser or "Сброс подтверждений результатов" in [
                                             str(x) for x in
                                             request.user.groups.all()]) and i.time_confirmation is not None,
                    "more": [x.research_id for x in Issledovaniya.objects.filter(parent=i)],
                    "sub_directions": [],
                    "recipe": [],
                    "microbiology": [],
                    "lab_comment": i.lab_comment,
                }

                if i.research.is_microbiology:
                    pass  # TODO: Fill microbiology results

                for sd in Napravleniya.objects.filter(parent=i):
                    iss["sub_directions"].append({
                        "pk": sd.pk,
                        "cancel": sd.cancel,
                        "researches": [
                            x.research.title for x in Issledovaniya.objects.filter(napravleniye=sd)
                        ],
                    })

                if iss["research"]["is_doc_refferal"]:
                    iss = {
                        **iss,
                        "purpose": i.purpose_id,
                        "first_time": i.first_time,
                        "result": i.result_reception_id,
                        "outcome": i.outcome_illness_id,
                        "maybe_onco": i.maybe_onco,
                        "diagnos": i.diagnos,

                        "purpose_list": [{"pk": x.pk, "title": x.title} for x in
                                         VisitPurpose.objects.filter(hide=False).order_by("pk")],
                        "result_list": [{"pk": x.pk, "title": x.title} for x in
                                        ResultOfTreatment.objects.filter(hide=False).order_by("pk")],
                        "outcome_list": [{"pk": x.pk, "title": x.title} for x in
                                         Outcomes.objects.filter(hide=False).order_by("pk")]
                    }

                    for rp in Recipe.objects.filter(issledovaniye=i).order_by('pk'):
                        iss["recipe"].append({
                            "pk": rp.pk,
                            "prescription": rp.drug_prescription,
                            "taking": rp.method_of_taking,
                            "comment": rp.comment,
                        })

                ParaclinicTemplateName.make_default(i.research)

                rts = ParaclinicTemplateName.objects.filter(research=i.research, hide=False)

                for rt in rts.order_by('title'):
                    iss["templates"].append({
                        "pk": rt.pk,
                        "title": rt.title,
                    })

                for group in ParaclinicInputGroups.objects.filter(research=i.research, hide=False).order_by("order"):
                    g = {"pk": group.pk, "order": group.order, "title": group.title, "show_title": group.show_title,
                         "hide": group.hide, "fields": [], "visibility": group.visibility}
                    for field in ParaclinicInputField.objects.filter(group=group, hide=False).order_by("order"):
                        g["fields"].append({
                            "pk": field.pk,
                            "order": field.order,
                            "lines": field.lines,
                            "title": field.title,
                            "hide": field.hide,
                            "values_to_input": json.loads(field.input_templates),
                            "value": (field.default_value if field.field_type != 3 else '')
                            if not ParaclinicResult.objects.filter(
                                issledovaniye=i, field=field).exists() else
                            ParaclinicResult.objects.filter(issledovaniye=i, field=field)[0].value,
                            "field_type": field.field_type,
                            "default_value": field.default_value,
                            "visibility": field.visibility,
                            "required": field.required,
                            "helper": field.helper,
                        })
                    iss["research"]["groups"].append(g)
                response["researches"].append(iss)
            if response["has_doc_referral"]:
                response["anamnesis"] = d.client.anamnesis_of_life
            f = True
    if not f:
        response["message"] = "Направление не найдено"
    return JsonResponse(response)


@group_required("Врач параклиники", "Врач консультаций")
def directions_paraclinic_result(request):
    response = {"ok": False, "message": ""}
    rb = json.loads(request.body)
    request_data = rb.get("data", {})
    pk = request_data.get("pk", -1)
    with_confirm = rb.get("with_confirm", False)
    visibility_state = rb.get("visibility_state", {})
    v_g = visibility_state.get("groups", {})
    v_f = visibility_state.get("fields", {})
    recipe = request_data.get("recipe", [])
    tube = request_data.get("direction", {}).get("tube", {})
    diss = Issledovaniya.objects.filter(pk=pk, time_confirmation__isnull=True)
    if diss.filter(Q(research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)
                   | Q(research__is_doc_refferal=True) | Q(research__is_treatment=True)
                   | Q(research__is_stom=True)).exists() or request.user.is_staff:
        iss = Issledovaniya.objects.get(pk=pk)

        iss.napravleniye.microbiology_n = tube.get("n", "")
        iss.napravleniye.save()

        recipe_no_remove = []

        for r in recipe:
            if r.get("remove", False):
                continue
            if r.get("isNew", False):
                rn = Recipe(issledovaniye=iss, drug_prescription=r["prescription"], method_of_taking=r["taking"],
                            comment=r["comment"])
                rn.save()
            else:
                rn = Recipe.objects.get(pk=r["pk"])
                MethodsOfTaking.dec(rn.drug_prescription, rn.method_of_taking)
                rn.drug_prescription = r["prescription"]
                rn.method_of_taking = r["taking"]
                rn.comment = r["comment"]
                rn.save()
            if rn.method_of_taking:
                MethodsOfTaking.inc(rn.drug_prescription, rn.method_of_taking)
            recipe_no_remove.append(rn.pk)

        Recipe.objects.filter(issledovaniye=iss).exclude(pk__in=recipe_no_remove).delete()

        for group in request_data["research"]["groups"]:
            if not v_g.get(str(group["pk"]), True):
                ParaclinicResult.objects.filter(issledovaniye=iss, field__group__pk=group["pk"]).delete()
                continue
            for field in group["fields"]:
                if not v_f.get(str(field["pk"]), True):
                    ParaclinicResult.objects.filter(issledovaniye=iss, field__pk=field["pk"]).delete()
                    continue
                if not ParaclinicInputField.objects.filter(pk=field["pk"]).exists():
                    continue
                f = ParaclinicInputField.objects.get(pk=field["pk"])
                if not ParaclinicResult.objects.filter(issledovaniye=iss, field=f).exists():
                    f_result = ParaclinicResult(issledovaniye=iss, field=f, value="")
                else:
                    f_result = ParaclinicResult.objects.filter(issledovaniye=iss, field=f)[0]
                f_result.value = field["value"]
                f_result.save()
        iss.doc_save = request.user.doctorprofile
        iss.time_save = timezone.now()
        if iss.research.is_doc_refferal:
            iss.medical_examination = request_data.get("examination_date", timezone.now().date())
        if with_confirm:
            iss.doc_confirmation = request.user.doctorprofile
            iss.time_confirmation = timezone.now()

        if not iss.napravleniye.visit_who_mark or not iss.napravleniye.visit_date:
            iss.napravleniye.visit_who_mark = request.user.doctorprofile
            iss.napravleniye.visit_date = timezone.now()
            iss.napravleniye.save()

        iss.purpose_id = request_data.get("purpose")
        iss.first_time = request_data.get("first_time", False)
        iss.result_reception_id = request_data.get("result")
        iss.outcome_illness_id = request_data.get("outcome")
        iss.maybe_onco = request_data.get("maybe_onco", False)
        iss.diagnos = request_data.get("diagnos", "")
        iss.lab_comment = request_data.get("lab_comment", "")

        iss.save()

        more = request_data.get("more", [])
        h = []
        for m in more:
            if not Issledovaniya.objects.filter(parent=iss, doc_save=request.user.doctorprofile, research_id=m):
                i = Issledovaniya.objects.create(parent=iss, research_id=m)
                i.doc_save = request.user.doctorprofile
                i.time_save = timezone.now()
                i.creator = request.user.doctorprofile
                if with_confirm:
                    i.doc_confirmation = request.user.doctorprofile
                    i.time_confirmation = timezone.now()
                i.save()
                h.append(i.pk)
            else:
                for i2 in Issledovaniya.objects.filter(parent=iss, doc_save=request.user.doctorprofile,
                                                       research_id=m):
                    i2.time_save = timezone.now()
                    if with_confirm:
                        i2.doc_confirmation = request.user.doctorprofile
                        i2.time_confirmation = timezone.now()
                    i2.save()
                    h.append(i2.pk)

        Issledovaniya.objects.filter(parent=iss).exclude(pk__in=h).delete()

        response["ok"] = True
        Log(key=pk, type=13, body="", user=request.user.doctorprofile).save()
    return JsonResponse(response)


@group_required("Врач параклиники", "Врач консультаций")
def directions_paraclinic_confirm(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("iss_pk", -1)
    diss = Issledovaniya.objects.filter(pk=pk, time_confirmation__isnull=True)
    if diss.filter(Q(research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)
                   | Q(research__is_doc_refferal=True) | Q(research__is_treatment=True)
                   | Q(research__is_stom=True)).exists():
        iss = Issledovaniya.objects.get(pk=pk)
        t = timezone.now()
        if not iss.napravleniye.visit_who_mark or not iss.napravleniye.visit_date:
            iss.napravleniye.visit_who_mark = request.user.doctorprofile
            iss.napravleniye.visit_date = t
            iss.napravleniye.save()
        iss.doc_confirmation = request.user.doctorprofile
        iss.time_confirmation = t
        iss.save()
        for i in Issledovaniya.objects.filter(parent=iss):
            i.doc_confirmation = request.user.doctorprofile
            i.time_confirmation = t
            i.save()
        response["ok"] = True
        Log(key=pk, type=14, body=json.dumps(request_data), user=request.user.doctorprofile).save()
    return JsonResponse(response)


@group_required("Врач параклиники", "Сброс подтверждений результатов", "Врач консультаций")
def directions_paraclinic_confirm_reset(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("iss_pk", -1)

    if Issledovaniya.objects.filter(pk=pk).exists():
        iss = Issledovaniya.objects.get(pk=pk)

        import time
        ctp = int(
            0 if not iss.time_confirmation else int(time.mktime(timezone.localtime(iss.time_confirmation).timetuple())))
        ctime = int(time.time())
        cdid = -1 if not iss.doc_confirmation else iss.doc_confirmation_id
        if (ctime - ctp < SettingManager.get(
                "lab_reset_confirm_time_min") * 60 and cdid == request.user.doctorprofile.pk) or request.user.is_superuser or "Сброс подтверждений результатов" in [
            str(x) for x in request.user.groups.all()]:
            predoc = {"fio": iss.doc_confirmation.get_fio(), "pk": iss.doc_confirmation_id,
                      "direction": iss.napravleniye_id}
            iss.doc_confirmation = iss.time_confirmation = None
            iss.save()
            if iss.napravleniye.result_rmis_send:
                c = Client()
                c.directions.delete_services(iss.napravleniye, request.user.doctorprofile)
            response["ok"] = True
            for i in Issledovaniya.objects.filter(parent=iss):
                i.doc_confirmation = None
                i.time_confirmation = None
                i.save()
            Log(key=pk, type=24, body=json.dumps(predoc), user=request.user.doctorprofile).save()
        else:
            response["message"] = "Сброс подтверждения разрешен в течении %s минут" % (
                str(SettingManager.get("lab_reset_confirm_time_min")))
    return JsonResponse(response)


@group_required("Врач параклиники", "Врач консультаций")
def directions_paraclinic_history(request):
    response = {"directions": []}
    request_data = json.loads(request.body)
    date_start, date_end = try_parse_range(request_data["date"])
    has_dirs = []
    for direction in Napravleniya.objects.filter(Q(issledovaniya__doc_save=request.user.doctorprofile) |
                                                 Q(issledovaniya__doc_confirmation=request.user.doctorprofile)) \
            .filter(Q(issledovaniya__time_confirmation__range=(date_start, date_end)) |
                    Q(issledovaniya__time_save__range=(date_start, date_end))) \
            .order_by("-issledovaniya__time_save", "-issledovaniya__time_confirmation"):
        if direction.pk in has_dirs:
            continue
        has_dirs.append(direction.pk)
        d = {
            "pk": direction.pk,
            "date": strdate(direction.data_sozdaniya),
            "patient": direction.client.individual.fio(full=True, direction=direction),
            "card": direction.client.number_with_type(),
            "iss": [],
            "all_confirmed": True,
            "all_saved": True
        }
        for i in Issledovaniya.objects.filter(napravleniye=direction).order_by("pk"):
            iss = {"title": i.research.get_title(),
                   "saved": i.time_save is not None,
                   "confirmed": i.time_confirmation is not None}
            d["iss"].append(iss)
            if not iss["saved"]:
                d["all_saved"] = False
            if not iss["confirmed"]:
                d["all_confirmed"] = False
        response["directions"].append(d)
    return JsonResponse(response)


def directions_patient_history(request):
    data = []
    request_data = json.loads(request.body)

    iss = Issledovaniya.objects.get(pk=request_data["pk"])

    for i in Issledovaniya.objects.filter(time_confirmation__isnull=False,
                                          research=iss.research,
                                          napravleniye__client__individual=iss.napravleniye.client.individual).order_by(
        '-time_confirmation').exclude(pk=request_data["pk"]):
        data.append({
            "pk": i.pk,
            "direction": i.napravleniye_id,
            "date": strdate(i.time_confirmation)
        })

    return JsonResponse({"data": data})


def directions_data_by_fields(request):
    data = {}
    request_data = json.loads(request.body)

    i = Issledovaniya.objects.get(pk=request_data["pk"])
    if i.time_confirmation:
        for field in ParaclinicInputField.objects.filter(group__research=i.research, group__hide=False, hide=False):
            if ParaclinicResult.objects.filter(issledovaniye=i, field=field).exists():
                data[field.pk] = ParaclinicResult.objects.filter(issledovaniye=i, field=field)[0].value
    return JsonResponse({"data": data})
