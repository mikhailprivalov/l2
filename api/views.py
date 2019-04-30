import collections
import datetime
import re
import threading
import time
from collections import defaultdict
from operator import itemgetter

import pytz
import simplejson as json
import yaml
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import model_to_dict
from django.http import JsonResponse
from django.utils import timezone, dateformat
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

import api.models as models
import directions.models as directions
import users.models as users
from api.ws import emit
from appconf.manager import SettingManager
from barcodes.views import tubes
from clients.models import CardBase, Individual, Card, Document, DocumentType, CardDocUsage, District, AnamnesisHistory
from contracts.models import Company
from directory.models import AutoAdd, Fractions, ParaclinicInputGroups, ParaclinicInputField
from laboratory import settings
from laboratory.decorators import group_required
from laboratory.utils import strdate, strdatetime, tsdatetime
from podrazdeleniya.models import Podrazdeleniya
from results.views import result_normal
from rmis_integration.client import Client, get_direction_full_data_cache
from slog import models as slog
from slog.models import Log
from statistics_tickets.models import VisitPurpose, ResultOfTreatment, StatisticsTicket, Outcomes, \
    ExcludePurposes
from utils.dates import try_parse_range, try_strptime


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
        if resdict["pk"] and models.Application.objects.filter(key=appkey).exists() and models.Application.objects.get(
                key=appkey).active and directions.TubesRegistration.objects.filter(pk=resdict["pk"]).exists():
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
                                                                fraction=fraction).exists():  # Если результат для фракции существует
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
                            find = re.findall("\d+.\d+", fraction_result.value)
                            if len(find) > 0:
                                val = float(find[0]) * fractionRel.get_multiplier_display()
                                if fractionRel.full_round:
                                    val = round(val)
                                fraction_result.value = fraction_result.value.replace(find[0], str(val))

                            fraction_result.iteration = 1  # Установка итерации
                            ref = fractionRel.default_ref
                            if ref:
                                fraction_result.ref_title = ref.title
                                fraction_result.ref_about = ref.about
                                fraction_result.ref_m = ref.m
                                fraction_result.ref_f = ref.f
                            fraction_result.save()  # Сохранение
                            issled.api_app = models.Application.objects.get(key=appkey)
                            issled.save()
                            fraction_result.get_ref(re_save=True)
                            fraction_result.issledovaniye.doc_save = astm_user  # Кто сохранил
                            from datetime import datetime
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
                                        find = re.findall("\d+.\d+", fraction_result.value)
                                        if len(find) > 0:
                                            val_str = fraction_result.value
                                            for f in find:
                                                val = app.truncate(float(f) * fraction_rel.get_multiplier_display())
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
        return JsonResponse(
            {"departments": [{"pk": x.pk, "title": x.get_title(), "type": str(x.p_type), "updated": False} for
                             x in Podrazdeleniya.objects.all().order_by("pk")],
             "can_edit": can_edit,
             "types": [{"pk": str(x[0]), "title": x[1]} for x in Podrazdeleniya.TYPES if
                       (x[0] == 3 and SettingManager.get("paraclinic_module", default='false', default_type='b'))
                       or (x[0] == 4 and SettingManager.get("consults_module", default='false', default_type='b'))
                       or x[0] not in [3, 4]]})
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


class ResearchesTemplates(View):
    def get(self, request):
        from django.db.models import Q

        templates = []
        for t in users.AssignmentTemplates.objects.filter(global_template=True) \
                .filter(Q(doc__isnull=True, podrazdeleniye__isnull=True) |
                        Q(doc=request.user.doctorprofile) |
                        Q(podrazdeleniye=request.user.doctorprofile.podrazdeleniye)):
            templates.append({"values": [x.research.pk for x in users.AssignmentResearches.objects.filter(template=t)],
                              "pk": t.pk,
                              "title": t.title,
                              "for_current_user": t.doc is not None,
                              "for_users_department": t.podrazdeleniye is not None})
        return JsonResponse({"templates": templates})

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(self.__class__, self).dispatch(request, *args, **kwargs)


from directory.models import Researches as DResearches


class Researches(View):
    def get(self, request):
        deps = defaultdict(list)

        for r in DResearches.objects.filter(hide=False).order_by("title"):
            autoadd = [x.b.pk for x in AutoAdd.objects.filter(a=r)]
            addto = [x.a.pk for x in AutoAdd.objects.filter(b=r)]

            deps[-2 if not r.podrazdeleniye else r.podrazdeleniye.pk].append(
                {"pk": r.pk,
                 "onlywith": -1 if not r.onlywith else r.onlywith.pk,
                 "department_pk": -2 if not r.podrazdeleniye else r.podrazdeleniye.pk,
                 "title": r.get_title(),
                 "full_title": r.title,
                 "doc_refferal": r.is_doc_refferal,
                 "need_vich_code": r.need_vich_code,
                 "comment_variants": [] if not r.comment_variants else r.comment_variants.get_variants(),
                 "autoadd": autoadd,
                 "addto": addto,
                 "code": r.code,
                 "type": "4" if not r.podrazdeleniye else str(r.podrazdeleniye.p_type)
                 })
        return JsonResponse({"researches": deps})

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(self.__class__, self).dispatch(request, *args, **kwargs)


def current_user_info(request):
    ret = {"auth": request.user.is_authenticated, "doc_pk": -1, "username": "", "fio": "",
           "department": {"pk": -1, "title": ""}, "groups": [], "modules": {
            "l2_cards": SettingManager.get("l2_cards_module", default='false', default_type='b'),
        }}
    if ret["auth"]:
        ret["username"] = request.user.username
        ret["fio"] = request.user.doctorprofile.fio
        ret["groups"] = list(request.user.groups.values_list('name', flat=True))
        if request.user.is_superuser:
            ret["groups"].append("Admin")
        ret["doc_pk"] = request.user.doctorprofile.pk
        ret["department"] = {"pk": request.user.doctorprofile.podrazdeleniye.pk,
                             "title": request.user.doctorprofile.podrazdeleniye.title}
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


@login_required
def patients_search_card(request):
    objects = []
    data = []
    d = json.loads(request.body)
    inc_rmis = d.get('inc_rmis')
    card_type = CardBase.objects.get(pk=d['type'])
    query = d['query'].strip()
    p = re.compile(r'[а-яё]{3}[0-9]{8}', re.IGNORECASE)
    p2 = re.compile(r'^([А-яЁё\-]+)( ([А-яЁё\-]+)(( ([А-яЁё\-]*))?( ([0-9]{2}\.[0-9]{2}\.[0-9]{4}))?)?)?$')
    p3 = re.compile(r'^[0-9]{1,15}$')
    p4 = re.compile(r'card_pk:\d+', flags=re.IGNORECASE)
    p4i = bool(re.search(p4, query.lower()))
    pat_bd = re.compile(r"\d{4}-\d{2}-\d{2}")
    c = None
    if not p4i:
        if re.search(p, query.lower()):
            initials = query[0:3].upper()
            btday = query[7:11] + "-" + query[5:7] + "-" + query[3:5]
            if not pat_bd.match(btday):
                return JsonResponse([], safe=False)
            try:
                objects = Individual.objects.filter(family__startswith=initials[0], name__startswith=initials[1],
                                                    patronymic__startswith=initials[2], birthday=btday,
                                                    card__base=card_type)
                if (card_type.is_rmis and len(objects) == 0) or (card_type.internal_type and inc_rmis):
                    c = Client(modules="patients")
                    objects = c.patients.import_individual_to_base(
                        {"surname": query[0] + "%", "name": query[1] + "%", "patrName": query[2] + "%",
                         "birthDate": btday},
                        fio=True)
            except ValidationError:
                objects = []
        elif re.search(p2, query):
            f, n, p, rmis_req, split = full_patient_search_data(p, query)
            objects = Individual.objects.filter(family__istartswith=f, name__istartswith=n,
                                                patronymic__istartswith=p, card__base=card_type)[:10]
            if len(split) > 3:
                objects = Individual.objects.filter(family__istartswith=f, name__istartswith=n,
                                                    patronymic__istartswith=p, card__base=card_type,
                                                    birthday=datetime.datetime.strptime(split[3], "%d.%m.%Y").date())[
                          :10]

            if (card_type.is_rmis and (len(objects) == 0 or (len(split) < 4 and len(objects) < 10))) \
                    or (card_type.internal_type and inc_rmis):
                objects = list(objects)
                try:
                    if not c:
                        c = Client(modules="patients")
                    objects += c.patients.import_individual_to_base(rmis_req, fio=True, limit=10 - len(objects))
                except ConnectionError:
                    pass

        if (re.search(p3, query) and not card_type.is_rmis) \
                or (len(list(objects)) == 0 and len(query) == 16 and card_type.internal_type) \
                or (card_type.is_rmis and not re.search(p3, query)):
            resync = True
            if len(list(objects)) == 0:
                resync = False
                try:
                    objects = Individual.objects.filter(card__number=query.upper(), card__is_archive=False,
                                                        card__base=card_type)
                except ValueError:
                    pass
                if (card_type.is_rmis or card_type.internal_type) and len(list(objects)) == 0 and len(query) == 16:
                    if not c:
                        c = Client(modules="patients")
                    objects = c.patients.import_individual_to_base(query)
                else:
                    resync = True
            if resync and card_type.is_rmis:
                if not c:
                    c = Client(modules="patients")

                sema = threading.BoundedSemaphore(10)
                threads = list()

                def sync_i(o: Individual, client: Client):
                    sema.acquire()
                    try:
                        o.sync_with_rmis(c=client)
                    finally:
                        sema.release()

                for o in objects:
                    thread = threading.Thread(target=sync_i, args=(o, c))
                    threads.append(thread)
                    thread.start()

    if p4i:
        cards = Card.objects.filter(pk=int(query.split(":")[1]))
    else:
        cards = Card.objects.filter(base=card_type, individual__in=objects, is_archive=False)
        if re.match(p3, query):
            cards = cards.filter(number=query)

    for row in cards.filter(is_archive=False).prefetch_related("individual").distinct():
        docs = Document.objects.filter(individual__pk=row.individual.pk, is_active=True,
                                       document_type__title__in=['СНИЛС', 'Паспорт гражданина РФ', 'Полис ОМС'])\
            .distinct("pk", "number", "document_type", "serial").order_by('pk')
        data.append({"type_title": card_type.title,
                     "num": row.number,
                     "is_rmis": row.base.is_rmis,
                     "family": row.individual.family,
                     "name": row.individual.name,
                     "twoname": row.individual.patronymic,
                     "birthday": row.individual.bd(),
                     "age": row.individual.age_s(),
                     "fio_age": row.individual.fio(full=True),
                     "sex": row.individual.sex,
                     "individual_pk": row.individual.pk,
                     "pk": row.pk,
                     "phones": row.get_phones(),
                     "main_diagnosis": row.main_diagnosis,
                     "docs": [{**model_to_dict(x), "type_title": x.document_type.title} for x in docs]})
    return JsonResponse({"results": data})


def full_patient_search_data(p, query):
    dp = re.compile(r'^[0-9]{2}\.[0-9]{2}\.[0-9]{4}$')
    split = str(re.sub(' +', ' ', str(query))).split()
    n = p = ""
    f = split[0]
    rmis_req = {"surname": f + "%"}
    if len(split) > 1:
        n = split[1]
        rmis_req["name"] = n + "%"
    if len(split) > 2:
        if re.search(dp, split[2]):
            split = [split[0], split[1], '', split[2]]
        else:
            p = split[2]
            rmis_req["patrName"] = p + "%"
    if len(split) > 3:
        btday = split[3].split(".")
        btday = btday[2] + "-" + btday[1] + "-" + btday[0]
        rmis_req["birthDate"] = btday
    return f, n, p, rmis_req, split


@login_required
def patients_search_individual(request):
    objects = []
    data = []
    d = json.loads(request.body)
    query = d['query'].strip()
    p = re.compile(r'[а-яё]{3}[0-9]{8}', re.IGNORECASE)
    p2 = re.compile(r'^([А-яЁё\-]+)( ([А-яЁё\-]+)(( ([А-яЁё\-]*))?( ([0-9]{2}\.[0-9]{2}\.[0-9]{4}))?)?)?$')
    p4 = re.compile(r'individual_pk:\d+')
    pat_bd = re.compile(r"\d{4}-\d{2}-\d{2}")
    if re.search(p, query.lower()):
        initials = query[0:3].upper()
        btday = query[7:11] + "-" + query[5:7] + "-" + query[3:5]
        if not pat_bd.match(btday):
            return JsonResponse([], safe=False)
        try:
            objects = Individual.objects.filter(family__startswith=initials[0], name__startswith=initials[1],
                                                patronymic__startswith=initials[2], birthday=btday)
        except ValidationError:
            objects = []
    elif re.search(p2, query):
        f, n, p, rmis_req, split = full_patient_search_data(p, query)
        objects = Individual.objects.filter(family__istartswith=f, name__istartswith=n, patronymic__istartswith=p)
        if len(split) > 3:
            objects = Individual.objects.filter(family__istartswith=f, name__istartswith=n,
                                                patronymic__istartswith=p,
                                                birthday=datetime.datetime.strptime(split[3], "%d.%m.%Y").date())

    if re.search(p4, query):
        objects = Individual.objects.filter(pk=int(query.split(":")[1]))
    n = 0

    if not isinstance(objects, list):
        for row in objects.distinct().order_by("family", "name", "patronymic", "birthday"):
            n += 1
            data.append({"family": row.family,
                         "name": row.name,
                         "patronymic": row.patronymic,
                         "birthday": row.bd(),
                         "age": row.age_s(),
                         "sex": row.sex,
                         "pk": row.pk})
            if n == 25:
                break
    return JsonResponse({"results": data})


@login_required
@group_required("Лечащий врач", "Оператор лечащего врача")
def directions_generate(request):
    result = {"ok": False, "directions": [], "message": ""}
    if request.method == "POST":
        p = json.loads(request.body)
        rc = directions.Napravleniya.gen_napravleniya_by_issledovaniya(p.get("card_pk"),
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
                                                                       discount=p.get("discount", 0))
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

    date_start, date_end = try_parse_range(request_data["date_from"], request_data["date_to"])
    try:
        if pk >= 0 or req_status == 4:
            if req_status != 4:
                rows = directions.Napravleniya.objects.filter(data_sozdaniya__range=(date_start, date_end),
                                                              client__pk=pk).order_by(
                    "-data_sozdaniya").prefetch_related()
            else:
                rows = directions.Napravleniya.objects.filter(Q(data_sozdaniya__range=(date_start, date_end),
                                                                doc_who_create=request.user.doctorprofile)
                                                              | Q(data_sozdaniya__range=(date_start, date_end),
                                                                  doc=request.user.doctorprofile)).order_by(
                    "-data_sozdaniya")

            for napr in rows.values("pk", "data_sozdaniya", "cancel"):
                iss_list = directions.Issledovaniya.objects.filter(napravleniye__pk=napr["pk"]).prefetch_related(
                    "tubes", "research", "research__podrazdeleniye")
                if not iss_list.exists():
                    continue
                status = 2  # 0 - выписано. 1 - Материал получен лабораторией. 2 - результат подтвержден. -1 - отменено
                has_conf = False
                researches_list = []
                researches_pks = []
                has_descriptive = False
                for v in iss_list:
                    if v.research.podrazdeleniye and v.research.podrazdeleniye.p_type == Podrazdeleniya.PARACLINIC:
                        has_descriptive = True
                    researches_list.append(v.research.title)
                    researches_pks.append(v.research.pk)
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
                if req_status in [3, 4] or req_status == status:
                    res["directions"].append(
                        {"pk": napr["pk"], "status": -1 if status == 0 and napr["cancel"] else status,
                         "researches": ' | '.join(researches_list),
                         "researches_pks": researches_pks,
                         "date": str(dateformat.format(napr["data_sozdaniya"].date(), settings.DATE_FORMAT_SHORT)),
                         "lab": "Консультации" if not iss_list[0].research.get_podrazdeleniye() or iss_list[
                             0].research.is_doc_refferal
                         else iss_list[0].research.get_podrazdeleniye().title, "cancel": napr["cancel"],
                         "checked": False,
                         "has_descriptive": has_descriptive})
    except (ValueError, IndexError) as e:
        res["message"] = str(e)
    return JsonResponse(res)


@login_required
def directions_cancel(request):
    response = {"cancel": False}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    if directions.Napravleniya.objects.filter(pk=pk).exists():
        direction = directions.Napravleniya.objects.get(pk=pk)
        direction.cancel = not direction.cancel
        direction.save()
        response["cancel"] = direction.cancel
    return JsonResponse(response)


@login_required
def researches_params(request):
    response = {"researches": []}
    request_data = json.loads(request.body)
    pks = request_data.get("pks", [])
    for research in DResearches.objects.filter(pk__in=pks):
        params = []
        if research.is_paraclinic or research.is_doc_refferal:
            for g in ParaclinicInputGroups.objects.filter(research=research).exclude(title="").order_by("order"):
                params.append({"pk": g.pk, "title": g.title})
        else:
            for f in Fractions.objects.filter(research=research).order_by("sort_weight"):
                params.append({"pk": f.pk, "title": f.title})
        response["researches"].append({"pk": research.pk, "title": research.title,
                                       "short_title": research.get_title(),
                                       "params": params, "is_paraclinic": research.is_paraclinic,
                                       "selected_params": []})
    return JsonResponse(response)


@login_required
@group_required("Оператор", "Конструктор: Параклинические (описательные) исследования")
def researches_by_department(request):
    response = {"researches": []}
    request_data = json.loads(request.body)
    department_pk = int(request_data["department"])
    if department_pk != -1:
        if department_pk == -2:
            q = DResearches.objects.filter(is_doc_refferal=True).order_by("title")
        else:
            q = DResearches.objects.filter(podrazdeleniye__pk=department_pk).order_by("title")

        for research in q:
            response["researches"].append({
                "pk": research.pk,
                "title": research.title,
                "short_title": research.short_title,
                "preparation": research.preparation,
                "hide": research.hide,
                "code": research.code,
            })
    return JsonResponse(response)


@login_required
@group_required("Оператор", "Конструктор: Параклинические (описательные) исследования")
def researches_update(request):
    response = {"ok": False}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -2)
    if pk > -2:
        department_pk = request_data.get("department")
        title = request_data.get("title").strip()
        short_title = request_data.get("short_title").strip()
        code = request_data.get("code").strip()
        info = request_data.get("info").strip()
        hide = request_data.get("hide")
        groups = request_data.get("groups")
        if len(title) > 0 and (department_pk == -2 or Podrazdeleniya.objects.filter(pk=department_pk).exists()):
            department = None if department_pk == -2 else Podrazdeleniya.objects.filter(pk=department_pk)[0]
            res = None
            if pk == -1:
                res = DResearches(title=title, short_title=short_title, podrazdeleniye=department, code=code,
                                  is_paraclinic=department_pk != -2 and department.p_type == 3,
                                  paraclinic_info=info, hide=hide, is_doc_refferal=department_pk == -2)
            elif DResearches.objects.filter(pk=pk).exists():
                res = DResearches.objects.filter(pk=pk)[0]
                res.title = title
                res.short_title = short_title
                res.podrazdeleniye = department
                res.code = code
                res.is_paraclinic = department_pk != -2 and department.p_type == 3
                res.is_doc_refferal = department_pk == -2
                res.paraclinic_info = info
                res.hide = hide
            if res:
                res.save()
                for group in groups:
                    g = None
                    pk = group["pk"]
                    if pk == -1:
                        g = ParaclinicInputGroups(title=group["title"],
                                                  show_title=group["show_title"],
                                                  research=res,
                                                  order=group["order"],
                                                  hide=group["hide"])
                    elif ParaclinicInputGroups.objects.filter(pk=pk).exists():
                        g = ParaclinicInputGroups.objects.get(pk=pk)
                        g.title = group["title"]
                        g.show_title = group["show_title"]
                        g.research = res
                        g.order = group["order"]
                        g.hide = group["hide"]
                    if g:
                        g.save()
                        for field in group["fields"]:
                            f = None
                            pk = field["pk"]
                            if pk == -1:
                                f = ParaclinicInputField(title=field["title"],
                                                         group=g,
                                                         order=field["order"],
                                                         lines=field["lines"],
                                                         hide=field["hide"],
                                                         default_value=field["default"],
                                                         input_templates=json.dumps(field["values_to_input"]),
                                                         field_type=field.get("field_type", 0),
                                                         required=field.get("required", False))
                            elif ParaclinicInputField.objects.filter(pk=pk).exists():
                                f = ParaclinicInputField.objects.get(pk=pk)
                                f.title = field["title"]
                                f.group = g
                                f.order = field["order"]
                                f.lines = field["lines"]
                                f.hide = field["hide"]
                                f.default_value = field["default"]
                                f.input_templates = json.dumps(field["values_to_input"])
                                f.field_type = field.get("field_type", 0)
                                f.required = field.get("required", False)
                            if f:
                                f.save()

                response["ok"] = True
        slog.Log(key=pk, type=10000, body=json.dumps(request_data), user=request.user.doctorprofile).save()
    return JsonResponse(response)


@login_required
@group_required("Оператор", "Конструктор: Параклинические (описательные) исследования")
def researches_details(request):
    response = {"pk": -1, "department": -1, "title": '', "short_title": '', "code": '', "info": '', "hide": False,
                "groups": []}
    request_data = json.loads(request.body)
    pk = request_data.get("pk")
    if DResearches.objects.filter(pk=pk).exists():
        res = DResearches.objects.filter(pk=pk)[0]
        response["pk"] = res.pk
        response["department"] = -2 if not res.podrazdeleniye else res.podrazdeleniye.pk
        response["title"] = res.title
        response["short_title"] = res.short_title
        response["code"] = res.code
        response["info"] = res.paraclinic_info or ""
        response["hide"] = res.hide
        for group in ParaclinicInputGroups.objects.filter(research__pk=pk).order_by("order"):
            g = {"pk": group.pk, "order": group.order, "title": group.title, "show_title": group.show_title,
                 "hide": group.hide, "fields": []}
            for field in ParaclinicInputField.objects.filter(group=group).order_by("order"):
                g["fields"].append({
                    "pk": field.pk,
                    "order": field.order,
                    "lines": field.lines,
                    "title": field.title,
                    "default": field.default_value,
                    "hide": field.hide,
                    "values_to_input": json.loads(field.input_templates),
                    "field_type": field.field_type,
                    "required": field.required,
                    "new_value": ""
                })
            response["groups"].append(g)
    return JsonResponse(response)


@login_required
@group_required("Оператор", "Конструктор: Параклинические (описательные) исследования")
def paraclinic_details(request):
    response = {"groups": []}
    request_data = json.loads(request.body)
    pk = request_data.get("pk")
    for group in ParaclinicInputGroups.objects.filter(research__pk=pk).order_by("order"):
        g = {"pk": group.pk, "order": group.order, "title": group.title, "show_title": group.show_title,
             "hide": group.hide, "fields": []}
        for field in ParaclinicInputField.objects.filter(group=group).order_by("order"):
            g["fields"].append({
                "pk": field.pk,
                "order": field.order,
                "lines": field.lines,
                "title": field.title,
                "default": field.default_value,
                "hide": field.hide,
                "values_to_input": json.loads(field.input_templates),
                "field_type": field.field_type,
                "required": field.required,
            })
        response["groups"].append(g)
    return JsonResponse(response)


@login_required
def directions_results(request):
    result = {"ok": False,
              "direction": {"pk": -1, "doc": "", "date": ""},
              "client": {},
              "full": False}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    if directions.Napravleniya.objects.filter(pk=pk).exists():
        napr = directions.Napravleniya.objects.get(pk=pk)
        dates = {}
        for iss in directions.Issledovaniya.objects.filter(napravleniye=napr, time_save__isnull=False):
            if iss.time_save:
                dt = str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                if dt not in dates.keys():
                    dates[dt] = 0
                dates[dt] += 1

        import operator
        maxdate = ""
        if dates != {}:
            maxdate = max(dates.items(), key=operator.itemgetter(1))[0]

        iss_list = directions.Issledovaniya.objects.filter(napravleniye=napr)
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
                                        "-1" if not issledovaniye.research.direction else issledovaniye.research.direction.pk,
                                        issledovaniye.research.sort_weight,
                                        issledovaniye.research.pk)
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

                    results = directions.Result.objects.filter(issledovaniye=issledovaniye).order_by(
                        "fraction__sort_weight")  # Выборка результатов из базы

                    n = 0
                    for res in results:  # Перебор результатов
                        pk = res.fraction.sort_weight
                        if not pk or pk <= 0:
                            pk = res.fraction.pk
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

    dn = directions.Napravleniya.objects.filter(pk=pk)
    if dn.exists():
        d = dn[0]
        df = directions.Issledovaniya.objects.filter(napravleniye=d)
        df = df.filter(Q(research__is_paraclinic=True, **add_fr) | Q(research__is_doc_refferal=True))
        df = df.distinct()

        if df.exists():
            response["ok"] = True
            response["has_doc_referral"] = False
            response["card_internal"] = d.client.base.internal_type
            response["patient"] = {
                "fio_age": d.client.individual.fio(full=True),
                "card": d.client.number_with_type(),
                "card_pk": d.client.pk,
                "doc": "" if not d.doc else (d.doc.get_fio(dots=True) + ", " + d.doc.podrazdeleniye.title),
                "imported_from_rmis": d.imported_from_rmis,
                "imported_org": "" if not d.imported_org else d.imported_org.title,
            }
            response["direction"] = {
                "pk": d.pk,
                "date": strdate(d.data_sozdaniya),
                "diagnos": d.diagnos,
                "fin_source": "" if not d.istochnik_f else d.istochnik_f.title
            }
            response["researches"] = []
            for i in df:
                if i.research.is_doc_refferal:
                    response["has_doc_referral"] = True
                ctp = int(0 if not i.time_confirmation else int(
                    time.mktime(timezone.localtime(i.time_confirmation).timetuple())))
                ctime = int(time.time())
                cdid = -1 if not i.doc_confirmation else i.doc_confirmation.pk
                rt = SettingManager.get("lab_reset_confirm_time_min") * 60
                iss = {
                    "pk": i.pk,
                    "research": {
                        "title": i.research.title,
                        "groups": []
                    },
                    "saved": i.time_save is not None,
                    "confirmed": i.time_confirmation is not None,
                    "allow_reset_confirm": ((
                                                    ctime - ctp < rt and cdid == request.user.doctorprofile.pk) or request.user.is_superuser or "Сброс подтверждений результатов" in [
                                                str(x) for x in
                                                request.user.groups.all()]) and i.time_confirmation is not None,
                }
                for group in ParaclinicInputGroups.objects.filter(research=i.research, hide=False).order_by("order"):
                    g = {"pk": group.pk, "order": group.order, "title": group.title, "show_title": group.show_title,
                         "hide": group.hide, "fields": []}
                    for field in ParaclinicInputField.objects.filter(group=group, hide=False).order_by("order"):
                        g["fields"].append({
                            "pk": field.pk,
                            "order": field.order,
                            "lines": field.lines,
                            "title": field.title,
                            "hide": field.hide,
                            "values_to_input": json.loads(field.input_templates),
                            "value": (field.default_value if field.field_type != 3 else '')
                                if not directions.ParaclinicResult.objects.filter(
                                issledovaniye=i, field=field).exists() else
                            directions.ParaclinicResult.objects.filter(issledovaniye=i, field=field)[0].value,
                            "field_type": field.field_type,
                            "default_value": field.default_value,
                            "required": field.required,
                        })
                    iss["research"]["groups"].append(g)
                response["researches"].append(iss)
            if response["has_doc_referral"]:
                response["anamnesis"] = d.client.anamnesis_of_life
            f = True
    if not f:
        response["message"] = "Направление не найдено"
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


@group_required("Врач параклиники", "Врач консультаций")
def directions_paraclinic_result(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body).get("data", {})
    pk = request_data.get("pk", -1)
    with_confirm = json.loads(request.body).get("with_confirm", False)
    diss = directions.Issledovaniya.objects.filter(pk=pk, time_confirmation__isnull=True)
    if diss.filter(Q(research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)
                   | Q(research__is_doc_refferal=True)).exists():
        iss = directions.Issledovaniya.objects.get(pk=pk)
        for group in request_data["research"]["groups"]:
            for field in group["fields"]:
                if not ParaclinicInputField.objects.filter(pk=field["pk"]).exists():
                    continue
                f = ParaclinicInputField.objects.get(pk=field["pk"])
                if not directions.ParaclinicResult.objects.filter(issledovaniye=iss, field=f).exists():
                    f_result = directions.ParaclinicResult(issledovaniye=iss, field=f, value="")
                else:
                    f_result = directions.ParaclinicResult.objects.filter(issledovaniye=iss, field=f)[0]
                f_result.value = field["value"]
                f_result.save()
        iss.doc_save = request.user.doctorprofile
        iss.time_save = timezone.now()
        if with_confirm:
            iss.doc_confirmation = request.user.doctorprofile
            iss.time_confirmation = timezone.now()

        if not iss.napravleniye.visit_who_mark or not iss.napravleniye.visit_date:
            iss.napravleniye.visit_who_mark = request.user.doctorprofile
            iss.napravleniye.visit_date = timezone.now()
            iss.napravleniye.save()
        iss.save()
        response["ok"] = True
        slog.Log(key=pk, type=13, body="", user=request.user.doctorprofile).save()
    return JsonResponse(response)


@group_required("Врач параклиники", "Врач консультаций")
def directions_paraclinic_confirm(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("iss_pk", -1)
    diss = directions.Issledovaniya.objects.filter(pk=pk, time_confirmation__isnull=True)
    if diss.filter(Q(research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)
                   | Q(research__is_doc_refferal=True)).exists():
        iss = directions.Issledovaniya.objects.get(pk=pk)
        t = timezone.now()
        if not iss.napravleniye.visit_who_mark or not iss.napravleniye.visit_date:
            iss.napravleniye.visit_who_mark = request.user.doctorprofile
            iss.napravleniye.visit_date = t
            iss.napravleniye.save()
        iss.doc_confirmation = request.user.doctorprofile
        iss.time_confirmation = t
        iss.save()
        response["ok"] = True
        slog.Log(key=pk, type=14, body=json.dumps(request_data), user=request.user.doctorprofile).save()
    return JsonResponse(response)


@group_required("Врач параклиники", "Сброс подтверждений результатов", "Врач консультаций")
def directions_paraclinic_confirm_reset(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("iss_pk", -1)

    if directions.Issledovaniya.objects.filter(pk=pk).exists():
        iss = directions.Issledovaniya.objects.get(pk=pk)

        import time
        ctp = int(
            0 if not iss.time_confirmation else int(time.mktime(timezone.localtime(iss.time_confirmation).timetuple())))
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
            response["ok"] = True
            slog.Log(key=pk, type=24, body=json.dumps(predoc), user=request.user.doctorprofile).save()
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
    for direction in directions. \
            Napravleniya.objects.filter(Q(issledovaniya__doc_save=request.user.doctorprofile) |
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
        for i in directions.Issledovaniya.objects.filter(napravleniye=direction).order_by("pk"):
            iss = {"title": i.research.title,
                   "saved": i.time_save is not None,
                   "confirmed": i.time_confirmation is not None}
            d["iss"].append(iss)
            if not iss["saved"]:
                d["all_saved"] = False
            if not iss["confirmed"]:
                d["all_confirmed"] = False
        response["directions"].append(d)
    return JsonResponse(response)


@group_required("Врач параклиники", "Посещения по направлениям", "Врач консультаций")
def directions_services(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    if pk >= 4600000000000:
        pk -= 4600000000000
        pk //= 10
    f = False
    dn = directions.Napravleniya.objects.filter(pk=pk)
    if dn.exists():
        n = dn[0]
        if directions.Issledovaniya.objects.filter(Q(research__is_paraclinic=True) | Q(research__is_doc_refferal=True)).exists():
            cdid, ctime, ctp, rt = get_reset_time_vars(n)

            response["ok"] = True
            researches = []
            for i in directions.Issledovaniya.objects.filter(napravleniye=n).filter(Q(research__is_paraclinic=True) | Q(research__is_doc_refferal=True)).distinct():
                researches.append({"title": i.research.title,
                                   "department": "" if not i.research.podrazdeleniye else i.research.podrazdeleniye.get_title()})
            response["direction_data"] = {
                "date": strdate(n.data_sozdaniya),
                "client": n.client.individual.fio(full=True),
                "card": n.client.number_with_type(),
                "diagnos": n.diagnos,
                "doc": "" if not n.doc else "{}, {}".format(n.doc.get_fio(), n.doc.podrazdeleniye.title),
                "imported_from_rmis": n.imported_from_rmis,
                "imported_org": "" if not n.imported_org else n.imported_org.title,
                "visit_who_mark": "" if not n.visit_who_mark else "{}, {}".format(n.visit_who_mark.get_fio(),
                                                                                  n.visit_who_mark.podrazdeleniye.title),
                "fin_source": "" if not n.istochnik_f else "{} - {}".format(n.istochnik_f.base.title, n.istochnik_f.title),
            }
            response["researches"] = researches
            response["loaded_pk"] = pk
            response["visit_status"] = n.visit_date is not None
            response["visit_date"] = "" if not n.visit_date else strdatetime(n.visit_date)
            response["allow_reset_confirm"] = bool(((
                                                            ctime - ctp < rt and cdid == request.user.doctorprofile.pk) or request.user.is_superuser or "Сброс подтверждений результатов" in [
                                                        str(x) for x in
                                                        request.user.groups.all()]) and n.visit_date)
            f = True
    if not f:
        response["message"] = "Направление не найдено"
    return JsonResponse(response)


def get_reset_time_vars(n):
    ctp = int(0 if not n.visit_date else int(time.mktime(timezone.localtime(n.visit_date).timetuple())))
    ctime = int(time.time())
    cdid = -1 if not n.visit_who_mark else n.visit_who_mark_id
    rt = SettingManager.get("visit_reset_time_min", default="20.0", default_type='f') * 60
    return cdid, ctime, ctp, rt


@group_required("Врач параклиники", "Посещения по направлениям", "Врач консультаций")
def directions_mark_visit(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    cancel = request_data.get("cancel", False)
    dn = directions.Napravleniya.objects.filter(pk=pk)
    f = False
    if dn.exists():
        n = dn[0]
        if directions.Issledovaniya.objects.filter(Q(research__is_paraclinic=True) | Q(research__is_doc_refferal=True)).exists():
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
            slog.Log(key=pk, type=5001,
                     body=json.dumps({"Посещение": "отмена" if cancel else "да", "Дата и время": response["visit_date"]}),
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
    for v in directions.Napravleniya.objects.filter(visit_date__range=(date_start, date_end,),
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
    i = directions.Issledovaniya.objects.filter(napravleniye__client__individual__pk=individual,
                                                research__pk=research,
                                                time_confirmation__isnull=False).order_by("-time_confirmation").first()
    u = directions.Issledovaniya.objects.filter(napravleniye__client__individual__pk=individual,
                                                research__pk=research,
                                                time_confirmation__isnull=True).order_by(
        "-napravleniye__data_sozdaniya").first()
    v = directions.Issledovaniya.objects.filter(napravleniye__client__individual__pk=individual,
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
                                    "ts": tsdatetime(v.napravleniye.visit_date)}
                response["has_last_result"] = True
                response["last_result"] = {"direction": i.napravleniye_id, "datetime": strdate(i.time_confirmation),
                                           "ts": tsdatetime(i.time_confirmation),
                                           "is_doc_referral": i.research.is_doc_referral,
                                           "is_paraclinic": i.research.is_paraclinic}
            else:
                response["data"] = {"direction": i.napravleniye_id, "datetime": strdate(i.time_confirmation),
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
    slog.Log(key=str(individual_pk), type=20000, body=json.dumps(request_data), user=request.user.doctorprofile).save()
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
                    for i in directions.Issledovaniya.objects.filter(research__paraclinicinputgroups=g,
                                                                     time_confirmation__isnull=False):
                        res = []
                        for r in directions.ParaclinicResult.objects.filter(field__group=g,
                                                                            issledovaniye=i).order_by("field__order"):
                            if r.value == "":
                                continue
                            res.append((r.field.title + ": " if r.field.title != "" else "") + r.value)

                        if len(res) == 0:
                            continue

                        paramdata = {"research": i.research.pk,
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
                                     "direction": i.napravleniye.pk}
                        data.append(paramdata)
            else:
                if Fractions.objects.filter(pk=ppk).exists():
                    f = Fractions.objects.get(pk=ppk)
                    for r in directions.Result.objects.filter(issledovaniye__napravleniye__client__individual=i,
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

                        paramdata = {"research": f.research.pk,
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
                                     "direction": r.issledovaniye.napravleniye.pk}
                        data.append(paramdata)
    data.sort(key=itemgetter("timestamp"), reverse=True)
    data.sort(key=itemgetter("pk"))
    data.sort(key=itemgetter("order"))
    data.sort(key=itemgetter("research"))
    return JsonResponse({"data": data})


def mkb10(request):
    kw = request.GET.get("keyword", "")
    data = []
    for d in directions.Diagnoses.objects.filter(code__istartswith=kw, d_type="mkb10.4").order_by("code")[:11]:
        data.append({"pk": d.pk, "code": d.code, "title": d.title})
    return JsonResponse({"data": data})


def vich_code(request):
    kw = request.GET.get("keyword", "")
    data = []
    for d in directions.Diagnoses.objects.filter(code__istartswith=kw, d_type="vc").order_by("code")[:11]:
        data.append({"pk": d.pk, "code": d.code, "title": {"-": ""}.get(d.title, d.title)})
    return JsonResponse({"data": data})


@login_required
def directions_rmis_directions(request):
    request_data = json.loads(request.body)
    pk = request_data.get("pk")
    rows = []
    if pk and Card.objects.filter(pk=pk, base__is_rmis=True).exists():
        c = Client(modules=["directions", "services"])
        sd = c.directions.get_individual_active_directions(Card.objects.get(pk=pk).number)
        dirs_data = [c.directions.get_direction_full_data(x) for x in sd if
                     not directions.Napravleniya.objects.filter(rmis_number=x).exists()]
        rows = [x for x in dirs_data if x]
    return JsonResponse({"rows": rows})


@login_required
def directions_rmis_direction(request):
    request_data = json.loads(request.body)
    data = {}
    pk = request_data.get("pk")
    if pk and not directions.Napravleniya.objects.filter(rmis_number=pk).exists():
        data = get_direction_full_data_cache(pk)
        if not data:
            c = Client(modules=["directions", "services"])
            data = c.directions.get_direction_full_data(pk)
    return JsonResponse(data)


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
        researches = [x.research.pk for x in
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
        global_template = request_data["global"]
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


def patients_search_l2_card(request):
    data = []
    request_data = json.loads(request.body)

    cards = Card.objects.filter(pk=request_data.get('card_pk', -1))
    if cards.exists():
        card_orig = cards[0]
        Card.add_l2_card(card_orig=card_orig)
        l2_cards = Card.objects.filter(individual=card_orig.individual, base__internal_type=True)

        for row in l2_cards.filter(is_archive=False):
            docs = Document.objects.filter(individual__pk=row.individual.pk, is_active=True,
                                           document_type__title__in=['СНИЛС', 'Паспорт гражданина РФ', 'Полис ОМС'])\
                .distinct("pk", "number", "document_type", "serial").order_by('pk')
            data.append({"type_title": row.base.title,
                         "num": row.number,
                         "is_rmis": row.base.is_rmis,
                         "family": row.individual.family,
                         "name": row.individual.name,
                         "twoname": row.individual.patronymic,
                         "birthday": row.individual.bd(),
                         "age": row.individual.age_s(),
                         "sex": row.individual.sex,
                         "individual_pk": row.individual.pk,
                         "base_pk": row.base.pk,
                         "pk": row.pk,
                         "phones": row.get_phones(),
                         "docs": [{**model_to_dict(x), "type_title": x.document_type.title} for x in docs],
                         "main_diagnosis": row.main_diagnosis})
    return JsonResponse({"results": data})


def patients_get_card_data(request, card_id):
    card = Card.objects.get(pk=card_id)
    c = model_to_dict(card)
    i = model_to_dict(card.individual)
    docs = [{**model_to_dict(x), "type_title": x.document_type.title}
            for x in Document.objects.filter(individual=card.individual).distinct('pk', "number", "document_type", "serial").order_by('pk')]
    rc = Card.objects.filter(base__is_rmis=True, individual=card.individual)
    return JsonResponse({**i, **c,
                         "docs": docs,
                         "main_docs": card.get_card_documents(),
                         "has_rmis_card": rc.exists(),
                         "av_companies": [{"id": -1, "title": "НЕ ВЫБРАНО", "short_title": ""},
                                          *[model_to_dict(x) for x in Company.objects.filter(active_status=True).order_by('title')]],
                         "custom_workplace": card.work_place != "",
                         "work_place_db": card.work_place_db.pk if card.work_place_db else -1,
                         "district": card.district_id or -1,
                         "districts": [{"id": -1, "title": "НЕ ВЫБРАН"},
                                       *[{"id": x.pk, "title": x.title}
                                            for x in District.objects.all().order_by('-sort_weight', '-id')]],
                         "agent_types": [{"key": x[0], "title": x[1]} for x in Card.AGENT_CHOICES if x[0]],
                         "excluded_types": Card.AGENT_CANT_SELECT,
                         "agent_need_doc": Card.AGENT_NEED_DOC,
                         "mother": None if not card.mother else card.mother.get_fio_w_card(),
                         "mother_pk": None if not card.mother else card.mother.pk,
                         "father": None if not card.father else card.father.get_fio_w_card(),
                         "father_pk": None if not card.father else card.father.pk,
                         "curator": None if not card.curator else card.curator.get_fio_w_card(),
                         "curator_pk": None if not card.curator else card.curator.pk,
                         "agent": None if not card.agent else card.agent.get_fio_w_card(),
                         "agent_pk": None if not card.agent else card.agent.pk,
                         "payer": None if not card.payer else card.payer.get_fio_w_card(),
                         "payer_pk": None if not card.payer else card.payer.pk,
                         "rmis_uid": rc[0].number if rc.exists() else None,
                         "doc_types": [{"pk": x.pk, "title": x.title} for x in DocumentType.objects.all()]})


def individual_search(request):
    result = []
    request_data = json.loads(request.body)
    for i in Individual.objects.filter(**request_data):
        result.append({
            "pk": i.pk,
            "fio": i.fio(full=True),
            "docs": [
                {**model_to_dict(x), "type_title": x.document_type.title}
                for x in Document.objects.filter(individual=i, is_active=True)
                    .distinct("number", "document_type", "serial", "date_end", "date_start")
            ],
            "l2_cards": [
                x.number for x in Card.objects.filter(individual=i, base__internal_type=True, is_archive=False)
            ],
        })
    return JsonResponse({"result": result})


def autocomplete(request):
    t = request.GET.get("type")
    v = request.GET.get("value", "")
    l = request.GET.get("limit", 10)
    data = []
    if v != "" and l > 0:
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


def patients_card_save(request):
    request_data = json.loads(request.body)
    result = "fail"
    message = ""
    card_pk = -1
    individual_pk = -1

    if "new_individual" in request_data and (request_data["new_individual"] or not Individual.objects.filter(pk=request_data["individual_pk"])) and request_data["card_pk"] < 0:
        i = Individual(family=request_data["family"],
                       name=request_data["name"],
                       patronymic=request_data["patronymic"],
                       birthday=request_data["birthday"],
                       sex=request_data["sex"])
        i.save()
    else:
        changed = False
        i = Individual.objects.get(pk=request_data["individual_pk"] if request_data["card_pk"] < 0 else Card.objects.get(pk=request_data["card_pk"]).individual.pk)
        if i.family != request_data["family"] \
                or i.name != request_data["name"]\
                or i.patronymic != request_data["patronymic"]\
                or str(i.birthday) != request_data["birthday"]\
                or i.sex != request_data["sex"]:
            changed = True
        i.family = request_data["family"]
        i.name = request_data["name"]
        i.patronymic = request_data["patronymic"]
        i.birthday = request_data["birthday"]
        i.sex = request_data["sex"]
        i.save()
        if Card.objects.filter(individual=i, base__is_rmis=True).exists() and changed:
            c = Client(modules=["individuals", "patients"])
            c.patients.send_patient(Card.objects.filter(individual=i, base__is_rmis=True)[0])

    individual_pk = i.pk

    if request_data["card_pk"] < 0:
        base = CardBase.objects.get(pk=request_data["base_pk"], internal_type=True)
        last_l2 = Card.objects.filter(base__internal_type=True).extra(
            select={'numberInt': 'CAST(number AS INTEGER)'}
        ).order_by("-numberInt").first()
        n = 0
        if last_l2:
            n = int(last_l2.number)
        c = Card(number=n + 1, base=base,
                 individual=i,
                 main_diagnosis="", main_address="",
                 fact_address="")
        c.save()
        card_pk = c.pk
        Log.log(card_pk, 30000, request.user.doctorprofile, request_data)
    else:
        card_pk = request_data["card_pk"]
        c = Card.objects.get(pk=card_pk)
        individual_pk = request_data["individual_pk"]
        Log.log(card_pk, 30001, request.user.doctorprofile, request_data)
    c.main_diagnosis = request_data["main_diagnosis"]
    c.main_address = request_data["main_address"]
    c.fact_address = request_data["fact_address"]
    if request_data["custom_workplace"] or not Company.objects.filter(pk=request_data["work_place_db"]).exists():
        c.work_place_db = None
        c.work_place = request_data["work_place"]
    else:
        c.work_place_db = Company.objects.get(pk=request_data["work_place_db"])
        c.work_place = ''
    c.district = District.objects.filter(pk=request_data["district"]).first()
    c.work_position = request_data["work_position"]
    c.save()
    if c.individual.primary_for_rmis:
        c.individual.sync_with_rmis()
    result = "ok"
    return JsonResponse({"result": result, "message": message, "card_pk": card_pk, "individual_pk": individual_pk})


def get_sex_by_param(request):
    request_data = json.loads(request.body)
    t = request_data.get("t")
    v = request_data.get("v", "")
    r = "м"
    if t == "name":
        p = Individual.objects.filter(name=v)
        r = "м" if p.filter(sex__iexact="м").count() >= p.filter(sex__iexact="ж").count() else "ж"
    if t == "family":
        p = Individual.objects.filter(family=v)
        r = "м" if p.filter(sex__iexact="м").count() >= p.filter(sex__iexact="ж").count() else "ж"
    if t == "patronymic":
        p = Individual.objects.filter(patronymic=v)
        r = "м" if p.filter(sex__iexact="м").count() >= p.filter(sex__iexact="ж").count() else "ж"
    return JsonResponse({"sex": r})


def edit_doc(request):
    request_data = json.loads(request.body)
    pk = request_data["pk"]
    serial = request_data["serial"]
    number = request_data["number"]
    type_o = DocumentType.objects.get(pk=request_data["type"])
    is_active = request_data["is_active"]
    date_start = request_data["date_start"]
    date_start = None if date_start == "" else date_start
    date_end = request_data["date_end"]
    date_end = None if date_end == "" else date_end
    who_give = request_data["who_give"] or ""

    if pk == -1:
        card = Card.objects.get(pk=request_data["card_pk"])
        d = Document(document_type=type_o, number=number, serial=serial, from_rmis=False, date_start=date_start,
                     date_end=date_end, who_give=who_give, is_active=is_active,
                     individual=Individual.objects.get(pk=request_data["individual_pk"]))
        d.save()
        cdu = CardDocUsage.objects.filter(card=card, document__document_type=type_o)
        if not cdu.exists():
            CardDocUsage(card=card, document=d).save()
        else:
            cdu.update(document=d)
        Log.log(d.pk, 30002, request.user.doctorprofile, request_data)
    else:
        Document.objects.filter(pk=pk, from_rmis=False).update(number=number, serial=serial,
                                                               is_active=is_active, date_start=date_start,
                                                               date_end=date_end, who_give=who_give)
        Log.log(pk, 30002, request.user.doctorprofile, request_data)
        d = Document.objects.get(pk=pk)
    d.sync_rmis()

    return JsonResponse({"ok": True})


def update_cdu(request):
    request_data = json.loads(request.body)
    card = Card.objects.get(pk=request_data["card_pk"])
    doc = Document.objects.get(pk=request_data["doc_pk"])
    cdu = CardDocUsage.objects.filter(card=card, document__document_type=doc.document_type)
    if not cdu.exists():
        CardDocUsage(card=card, document=doc).save()
    else:
        cdu.update(document=doc)
    Log.log(card.pk, 30004, request.user.doctorprofile, request_data)

    return JsonResponse({"ok": True})


def sync_rmis(request):
    request_data = json.loads(request.body)
    card = Card.objects.get(pk=request_data["card_pk"])
    card.individual.sync_with_rmis()
    return JsonResponse({"ok": True})


def update_wia(request):
    request_data = json.loads(request.body)
    card = Card.objects.get(pk=request_data["card_pk"])
    key = request_data["key"]
    if key in [x[0] for x in Card.AGENT_CHOICES]:
        card.who_is_agent = key
        card.save()
        Log.log(card.pk, 30006, request.user.doctorprofile, request_data)

    return JsonResponse({"ok": True})


def edit_agent(request):
    request_data = json.loads(request.body)
    key = request_data["key"]
    card = None if not request_data["card_pk"] else Card.objects.get(pk=request_data["card_pk"])
    parent_card = Card.objects.filter(pk=request_data["parent_card_pk"])
    doc = request_data["doc"] or ''
    clear = request_data["clear"]
    need_doc = key in Card.AGENT_NEED_DOC

    upd = {}

    if clear or not card:
        upd[key] = None
        if need_doc:
            upd[key + "_doc_auth"] = ''
        if parent_card[0].who_is_agent == key:
            upd["who_is_agent"] = ''
    else:
        upd[key] = card
        if need_doc:
            upd[key + "_doc_auth"] = doc
        if not key in Card.AGENT_CANT_SELECT:
            upd["who_is_agent"] = key

    parent_card.update(**upd)

    Log.log(parent_card.pk, 30005, request.user.doctorprofile, request_data)

    return JsonResponse({"ok": True})


def load_anamnesis(request):
    request_data = json.loads(request.body)
    card = Card.objects.get(pk=request_data["card_pk"])
    history = []
    for a in AnamnesisHistory.objects.filter(card=card).order_by('-pk'):
        history.append({
            "pk": a.pk,
            "text": a.text,
            "who_save": {
                "fio": a.who_save.get_fio(dots=True),
                "department": a.who_save.podrazdeleniye.get_title(),
            },
            "datetime": a.created_at.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime("%d.%m.%Y %X"),
        })
    data = {
        "text": card.anamnesis_of_life,
        "history": history,
    }
    return JsonResponse(data)


def save_anamnesis(request):
    request_data = json.loads(request.body)
    card = Card.objects.get(pk=request_data["card_pk"])
    if card.anamnesis_of_life != request_data["text"]:
        card.anamnesis_of_life = request_data["text"]
        card.save()
        AnamnesisHistory(card=card, text=request_data["text"], who_save=request.user.doctorprofile).save()
    return JsonResponse({"ok": True})
