import collections
import datetime
import re
from collections import defaultdict

import simplejson as json
import yaml
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone, dateformat
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

import api.models as models
import directions.models as directions
import users.models as users
from api.to_astm import get_iss_astm
from appconf.manager import SettingManager
from barcodes.views import tubes
from clients.models import CardBase, Individual, Card
from directory.models import AutoAdd, Fractions, ParaclinicInputGroups, ParaclinicInputField
from laboratory import settings
from laboratory.decorators import group_required
from podrazdeleniya.models import Podrazdeleniya
from results.views import result_normal
from rmis_integration.client import Client
from slog import models as slog
from slog.models import Log
from statistics_tickets.models import VisitPurpose, ResultOfTreatment, StatisticsTicket, Outcomes, \
    ExcludePurposes


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
                                fraction_result = directions.Result.objects.get(issledovaniye=issled,
                                                                                fraction__pk=fraction.pk)  # Выборка результата из базы
                            else:
                                fraction_result = directions.Result(issledovaniye=issled,
                                                                    fraction=fraction)  # Создание нового результата
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
    if models.Application.objects.filter(key=api_key).exists():
        astm_user = users.DoctorProfile.objects.filter(user__username="astm").first()
        if astm_user is None:
            astm_user = users.DoctorProfile.objects.filter(user__is_staff=True).order_by("pk").first()
        app = models.Application.objects.get(key=api_key)
        if app.active:
            data["app_name"] = app.name
            if message_type == "R":
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
                                            fraction_result = directions.Result.objects.get(issledovaniye=issled,
                                                                                            fraction=fraction_rel.fraction)
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
                                    slog.Log(key=json.dumps({"direction": direction.pk, "issleds": str(issleds)}),
                                             type=22, body=json.dumps(save_state), user=None).save()
                            oks.append(ok)
                    result["body"] = "{} {} {} {}".format(dw, pk, json.dumps(oks), direction is not None)
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
                            rel = models.RelationFractionASTM.objects.filter(fraction=fraction)
                            if not rel.exists():
                                continue
                        rel = rel[0]
                        researches[k].append(rel.astm_field)
                result["body"] = researches
            else:
                pass
        else:
            data["app_name"] = "API app banned"
            result["body"] = "API app banned"
    else:
        result["body"] = "API key is incorrect"
    slog.Log(key=pk, type=6000, body=json.dumps(data), user=None).save()
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
                       SettingManager.get("paraclinic_module", default='false', default_type='b') or x[0] != 3]})
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


@login_required
def bases(request):
    from clients.models import CardBase
    return JsonResponse({"bases": [
        {"pk": x.pk,
         "title": x.title,
         "code": x.short_title,
         "hide": x.hide,
         "history_number": x.history_number,
         "fin_sources": [{"pk": y.pk, "title": y.title, "default_diagnos": y.default_diagnos} for y in
                         directions.IstochnikiFinansirovaniya.objects.filter(base=x)]
         } for x in CardBase.objects.all()]})


class ResearchesTemplates(View):
    def get(self, request):
        from django.db.models import Q

        templates = []
        for t in users.AssignmentTemplates.objects.filter(Q(doc__isnull=True, podrazdeleniye__isnull=True) |
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

            deps[r.podrazdeleniye.pk].append(
                {"pk": r.pk,
                 "onlywith": -1 if not r.onlywith else r.onlywith.pk,
                 "department_pk": r.podrazdeleniye.pk,
                 "title": r.get_title(),
                 "full_title": r.title,
                 "comment_variants": [] if not r.comment_variants else r.comment_variants.get_variants(),
                 "autoadd": autoadd,
                 "addto": addto,
                 "type": str(r.podrazdeleniye.p_type)
                 })
        return JsonResponse({"researches": deps})

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(self.__class__, self).dispatch(request, *args, **kwargs)


def current_user_info(request):
    ret = {"auth": request.user.is_authenticated, "doc_pk": -1, "username": "", "fio": "",
           "department": {"pk": -1, "title": ""}, "groups": []}
    if ret["auth"]:
        ret["username"] = request.user.username
        ret["fio"] = request.user.doctorprofile.fio
        ret["groups"] = list(request.user.groups.values_list('name', flat=True))
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
    card_type = CardBase.objects.get(pk=d['type'])
    query = d['query'].strip()
    p = re.compile(r'[а-яё]{3}[0-9]{8}', re.IGNORECASE)
    p2 = re.compile(r'^([А-яЕё]+)( ([А-яЕё]+)( ([А-яЕё]*)( ([0-9]{2}\.[0-9]{2}\.[0-9]{4}))?)?)?$')
    p3 = re.compile(r'[0-9]{1,15}')
    p4 = re.compile(r'card_pk:\d+')
    pat_bd = re.compile(r"\d{4}-\d{2}-\d{2}")
    if re.search(p, query.lower()):
        initials = query[0:3].upper()
        btday = query[7:11] + "-" + query[5:7] + "-" + query[3:5]
        if not pat_bd.match(btday):
            return JsonResponse([], safe=False)
        try:
            objects = Individual.objects.filter(family__startswith=initials[0], name__startswith=initials[1],
                                                patronymic__startswith=initials[2], birthday=btday,
                                                card__base=card_type)
            if card_type.is_rmis and len(objects) == 0:
                c = Client()
                objects = c.patients.import_individual_to_base(
                    {"surname": query[0] + "%", "name": query[1] + "%", "patrName": query[2] + "%", "birthDate": btday},
                    fio=True)
        except ValidationError:
            objects = []
    elif re.search(p2, query):
        split = str(query).split()
        n = p = ""
        f = split[0]
        rmis_req = {"surname": f + "%"}
        if len(split) > 1:
            n = split[1]
            rmis_req["name"] = n + "%"
        if len(split) > 2:
            p = split[2]
            rmis_req["patrName"] = p + "%"
        if len(split) > 3:
            btday = split[3].split(".")
            btday = btday[2] + "-" + btday[1] + "-" + btday[0]
            rmis_req["birthDate"] = btday
        objects = Individual.objects.filter(family__istartswith=f, name__istartswith=n,
                                            patronymic__istartswith=p, card__base=card_type)[:10]
        if len(split) > 3:
            objects = Individual.objects.filter(family__istartswith=f, name__istartswith=n,
                                                patronymic__istartswith=p, card__base=card_type,
                                                birthday=datetime.datetime.strptime(split[3], "%d.%m.%Y").date())[:10]

        if card_type.is_rmis and (len(objects) == 0 or (len(split) < 4 and len(objects) < 10)):
            objects = list(objects)
            try:
                c = Client()
                objects += c.patients.import_individual_to_base(rmis_req, fio=True, limit=10 - len(objects))
            except ConnectionError:
                pass

    if re.search(p3, query) or card_type.is_rmis:
        resync = True
        if len(list(objects)) == 0:
            resync = False
            try:
                objects = Individual.objects.filter(card__number=query.upper(), card__is_archive=False,
                                                    card__base=card_type)
            except ValueError:
                pass
            if card_type.is_rmis and len(objects) == 0 and len(query) == 16:
                c = Client()
                objects = c.patients.import_individual_to_base(query)
            else:
                resync = True
        if resync and card_type.is_rmis:
            c = Client()
            for o in objects:
                o.sync_with_rmis(c=c)

    if re.search(p4, query):
        cards = Card.objects.filter(pk=int(query.split(":")[1]))
    else:
        cards = Card.objects.filter(base=card_type, individual__in=objects, is_archive=False)
        if re.match(p3, query):
            cards = cards.filter(number=query)

    for row in cards.prefetch_related("individual").distinct():
        data.append({"type_title": card_type.title,
                     "num": row.number,
                     "family": row.individual.family,
                     "name": row.individual.name,
                     "twoname": row.individual.patronymic,
                     "birthday": row.individual.bd(),
                     "age": row.individual.age_s(),
                     "sex": row.individual.sex,
                     "individual_pk": row.individual.pk,
                     "pk": row.pk})
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
                                                                       p.get("comments"))
        result["ok"] = rc["r"]
        result["directions"] = json.loads(rc["list_id"])
        if "message" in rc:
            result["message"] = rc["message"]
    return JsonResponse(result)


@login_required
def directions_history(request):
    import datetime
    res = {"directions": []}
    request_data = json.loads(request.body)

    pk = request_data.get("patient", -1)
    req_status = request_data.get("type", 4)
    date_start = request_data["date_from"].split(".")
    date_end = request_data["date_to"].split(".")

    date_start = datetime.date(int(date_start[2]), int(date_start[1]), int(date_start[0]))
    date_end = datetime.date(int(date_end[2]), int(date_end[1]), int(date_end[0])) + datetime.timedelta(days=1)
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
                for v in iss_list:
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
                         "lab": iss_list[0].research.get_podrazdeleniye().title, "cancel": napr["cancel"],
                         "checked": False})
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
@group_required("Оператор", "Конструктор: Параклинические (описательные) исследования")
def researches_by_department(request):
    response = {"researches": []}
    request_data = json.loads(request.body)
    department_pk = int(request_data["department"])
    if department_pk != -1:
        for research in DResearches.objects.filter(podrazdeleniye__pk=department_pk).order_by("title"):
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
        if len(title) > 0 and Podrazdeleniya.objects.filter(pk=department_pk).exists():
            department = Podrazdeleniya.objects.filter(pk=department_pk)[0]
            res = None
            if pk == -1:
                res = DResearches(title=title, short_title=short_title, podrazdeleniye=department, code=code,
                                  is_paraclinic=department.p_type == 3, paraclinic_info=info, hide=hide)
            elif DResearches.objects.filter(pk=pk).exists():
                res = DResearches.objects.filter(pk=pk)[0]
                res.title = title
                res.short_title = short_title
                res.podrazdeleniye = department
                res.code = code
                res.is_paraclinic = department.p_type == 3
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
                                                         input_templates=json.dumps(field["values_to_input"]))
                            elif ParaclinicInputField.objects.filter(pk=pk).exists():
                                f = ParaclinicInputField.objects.get(pk=pk)
                                f.title = field["title"]
                                f.group = g
                                f.order = field["order"]
                                f.lines = field["lines"]
                                f.hide = field["hide"]
                                f.default_value = field["default"]
                                f.input_templates = json.dumps(field["values_to_input"])
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
        response["department"] = res.podrazdeleniye.pk
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
                "values_to_input": json.loads(field.input_templates)
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
                            result["results"][kint]["fractions"][pk]["units"] = res.fraction.units
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


@group_required("Оформление статталонов")
def statistics_tickets_types(request):
    result = {"visit": [{"pk": x.pk, "title": x.title} for x in VisitPurpose.objects.filter(hide=False).order_by("pk")],
              "result": [{"pk": x.pk, "title": x.title} for x in
                         ResultOfTreatment.objects.filter(hide=False).order_by("pk")],
              "outcome": [{"pk": x.pk, "title": x.title} for x in
                          Outcomes.objects.filter(hide=False).order_by("pk")],
              "exclude": [{"pk": x.pk, "title": x.title} for x in
                          ExcludePurposes.objects.filter(hide=False).order_by("pk")]}
    return JsonResponse(result)


@group_required("Оформление статталонов")
def statistics_tickets_send(request):
    response = {"ok": True}
    rd = json.loads(request.body)
    t = StatisticsTicket(card=Card.objects.get(pk=rd["card_pk"]),
                         purpose=VisitPurpose.objects.get(pk=rd["visit"]),
                         result=ResultOfTreatment.objects.get(pk=rd["result"]),
                         info=rd["info"].strip(),
                         first_time=rd["first_time"],
                         primary_visit=rd["primary_visit"],
                         dispensary_registration=int(rd["disp"]),
                         doctor=request.user.doctorprofile,
                         outcome=Outcomes.objects.filter(pk=rd["outcome"]).first(),
                         dispensary_exclude_purpose=ExcludePurposes.objects.filter(pk=rd["exclude"]).first(),
                         dispensary_diagnos=rd["disp_diagnos"])
    t.save()
    Log(key="", type=7000, body=json.dumps(rd), user=request.user.doctorprofile).save()
    return JsonResponse(response)


@group_required("Оформление статталонов")
def statistics_tickets_get(request):
    response = {"data": []}
    request_data = json.loads(request.body)
    date_start = request_data["date"].split(".")
    date_start = datetime.date(int(date_start[2]), int(date_start[1]), int(date_start[0]))
    date_end = date_start + datetime.timedelta(1)
    n = 0
    for row in StatisticsTicket.objects.filter(doctor=request.user.doctorprofile,
                                               date__range=(date_start, date_end,)).order_by('pk'):
        if not row.invalid_ticket:
            n += 1
        response["data"].append({
            "pk": row.pk,
            "n": n if not row.invalid_ticket else '',
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


@group_required("Оформление статталонов")
def statistics_tickets_invalidate(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    if StatisticsTicket.objects.filter(doctor=request.user.doctorprofile, pk=request_data.get("pk", -1)).exists():
        if StatisticsTicket.objects.get(pk=request_data["pk"]).can_invalidate():
            StatisticsTicket.objects.filter(pk=request_data["pk"]).update(
                invalid_ticket=request_data.get("invalid", False))
            response["ok"] = True
            Log(key=str(request_data["pk"]), type=7001, body=json.dumps(request_data.get("invalid", False)),
                user=request.user.doctorprofile).save()
        else:
            response["message"] = "Время на отмену или возврат истекло"
    return JsonResponse(response)


@group_required("Врач параклиники")
def directions_paraclinic_form(request):
    import time
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    if pk >= 4600000000000:
        pk -= 4600000000000
        pk //= 10
    add_f = {}
    add_fr = {}
    if not request.user.is_superuser:
        add_f = dict(issledovaniya__research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)
        add_fr = dict(research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)

    if directions.Napravleniya.objects.filter(pk=pk, issledovaniya__research__is_paraclinic=True, **add_f).exists():
        response["ok"] = True
        d = directions.Napravleniya.objects.filter(pk=pk, issledovaniya__research__is_paraclinic=True, **add_f).distinct()[0]
        response["patient"] = {
            "fio_age": d.client.individual.fio(full=True),
            "card": d.client.number_with_type(),
            "doc": d.doc.get_fio(dots=True) + ", " + d.doc.podrazdeleniye.title
        }
        response["direction"] = {
            "pk": d.pk,
            "date": timezone.localtime(d.data_sozdaniya).strftime('%d.%m.%Y'),
            "diagnos": d.diagnos,
            "fin_source": d.istochnik_f.title
        }
        response["researches"] = []
        for i in directions.Issledovaniya.objects.filter(napravleniye=d, research__is_paraclinic=True, **add_fr):
            ctp = int(0 if not i.time_confirmation else int(
                time.mktime(i.time_confirmation.timetuple()))) + 8 * 60 * 60
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
            for group in ParaclinicInputGroups.objects.filter(research=i.research).order_by("order"):
                g = {"pk": group.pk, "order": group.order, "title": group.title, "show_title": group.show_title,
                     "hide": group.hide, "fields": []}
                for field in ParaclinicInputField.objects.filter(group=group).order_by("order"):
                    g["fields"].append({
                        "pk": field.pk,
                        "order": field.order,
                        "lines": field.lines,
                        "title": field.title,
                        "hide": field.hide,
                        "values_to_input": json.loads(field.input_templates),
                        "value": field.default_value if not directions.ParaclinicResult.objects.filter(
                            issledovaniye=i, field=field).exists() else
                        directions.ParaclinicResult.objects.filter(issledovaniye=i, field=field)[0].value,
                    })
                iss["research"]["groups"].append(g)
            response["researches"].append(iss)
    else:
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


@group_required("Врач параклиники")
def directions_paraclinic_result(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body).get("data", {})
    pk = request_data.get("pk", -1)
    with_confirm = json.loads(request.body).get("with_confirm", False)
    if directions.Issledovaniya.objects.filter(pk=pk, time_confirmation__isnull=True,
                                               research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye).exists():
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
        iss.save()
        response["ok"] = True
        slog.Log(key=pk, type=13, body=json.dumps(delete_keys_from_dict(request_data,
                                                                        ["hide", "confirmed", "allow_reset_confirm",
                                                                         "values_to_input", "show_title", "order",
                                                                         "show_title", "lines", "saved", "pk"])),
                 user=request.user.doctorprofile).save()
    return JsonResponse(response)


@group_required("Врач параклиники")
def directions_paraclinic_confirm(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("iss_pk", -1)
    if directions.Issledovaniya.objects.filter(pk=pk, time_confirmation__isnull=True,
                                               research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye).exists():
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


@group_required("Врач параклиники", "Сброс подтверждений результатов")
def directions_paraclinic_confirm_reset(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("iss_pk", -1)

    if directions.Issledovaniya.objects.filter(pk=pk).exists():
        iss = directions.Issledovaniya.objects.get(pk=pk)

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
            response["ok"] = True
            slog.Log(key=pk, type=24, body=json.dumps(predoc), user=request.user.doctorprofile).save()
        else:
            response["message"] = "Сброс подтверждения разрешен в течении %s минут" % (
                str(SettingManager.get("lab_reset_confirm_time_min")))
    return JsonResponse(response)


@group_required("Врач параклиники")
def directions_paraclinic_history(request):
    response = {"directions": []}
    request_data = json.loads(request.body)
    date_start = request_data["date"].split(".")
    date_start = datetime.date(int(date_start[2]), int(date_start[1]), int(date_start[0]))
    date_end = date_start + datetime.timedelta(1)
    has_dirs = []
    for direction in directions.\
            Napravleniya.objects.filter(Q(issledovaniya__doc_save=request.user.doctorprofile) |
                                        Q(issledovaniya__doc_confirmation=request.user.doctorprofile)) \
            .filter(Q(issledovaniya__time_confirmation__range=(date_start, date_end)) |
                    Q(issledovaniya__time_save__range=(date_start, date_end)))\
            .order_by("-issledovaniya__time_save", "-issledovaniya__time_confirmation"):
        if direction.pk in has_dirs:
            continue
        has_dirs.append(direction.pk)
        d = {
            "pk": direction.pk,
            "date": timezone.localtime(direction.data_sozdaniya).strftime('%d.%m.%Y'),
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


@group_required("Врач параклиники", "Посещения по направлениям")
def directions_services(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    if pk >= 4600000000000:
        pk -= 4600000000000
        pk //= 10
    if directions.Napravleniya.objects.filter(pk=pk, issledovaniya__research__is_paraclinic=True).exists():
        n = directions.Napravleniya.objects.filter(pk=pk, issledovaniya__research__is_paraclinic=True)[0]
        response["ok"] = True
        researches = []
        for i in directions.Issledovaniya.objects.filter(napravleniye=n):
            researches.append({"title": i.research.title,
                               "department": i.research.podrazdeleniye.get_title()})
        response["direction_data"] = {
            "date": n.data_sozdaniya.strftime('%d.%m.%Y'),
            "client": n.client.individual.fio(full=True),
            "card": n.client.number_with_type(),
            "diagnos": n.diagnos,
            "doc": "{}, {}".format(n.doc.get_fio(), n.doc.podrazdeleniye.title),
            "visit_who_mark": "" if not n.visit_who_mark else "{}, {}".format(n.visit_who_mark.get_fio(), n.visit_who_mark.podrazdeleniye.title),
            "fin_source": "{} - {}".format(n.istochnik_f.base.title, n.istochnik_f.title)
        }
        response["researches"] = researches
        response["loaded_pk"] = pk
        response["visit_status"] = n.visit_date is not None
        response["visit_date"] = "" if not n.visit_date else timezone.localtime(n.visit_date).strftime('%d.%m.%Y %X')
    else:
        response["message"] = "Направление не найдено"
    return JsonResponse(response)


@group_required("Врач параклиники", "Посещения по направлениям")
def directions_mark_visit(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    if directions.Napravleniya.objects.filter(pk=pk, issledovaniya__research__is_paraclinic=True, visit_date__isnull=True).exists():
        n = directions.Napravleniya.objects.filter(pk=pk, issledovaniya__research__is_paraclinic=True)[0]
        response["ok"] = True
        n.visit_date = timezone.now()
        n.visit_who_mark = request.user.doctorprofile
        n.save()
        response["visit_status"] = n.visit_date is not None
        response["visit_date"] = timezone.localtime(n.visit_date).strftime('%d.%m.%Y %X')
        slog.Log(key=pk, type=5001, body=json.dumps({"Посещение": "да", "Дата и время": response["visit_date"]}), user=request.user.doctorprofile).save()
    else:
        response["message"] = "Направление не найдено"
    return JsonResponse(response)


@group_required("Врач параклиники", "Посещения по направлениям")
def directions_visit_journal(request):
    response = {"data": []}
    request_data = json.loads(request.body)
    date_start = request_data["date"].split(".")
    date_start = datetime.date(int(date_start[2]), int(date_start[1]), int(date_start[0]))
    date_end = date_start + datetime.timedelta(1)
    for v in directions.Napravleniya.objects.filter(visit_date__range=(date_start, date_end,), visit_who_mark=request.user.doctorprofile).order_by("-visit_date"):
        response["data"].append({
            "pk": v.pk,
            "client": v.client.individual.fio(full=True),
            "card": v.client.number_with_type(),
            "datetime": timezone.localtime(v.visit_date).strftime('%d.%m.%Y %X')
        })
    return JsonResponse(response)
