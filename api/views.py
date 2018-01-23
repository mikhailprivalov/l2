import datetime
import re
from collections import defaultdict

import simplejson as json
import yaml
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

import api.models as models
import directions.models as directions
import users.models as users
from api.to_astm import get_iss_astm
from barcodes.views import tubes
from clients.models import CardBase, Individual, Card
from directory.models import AutoAdd
from laboratory.decorators import group_required
from podrazdeleniya.models import Podrazdeleniya
from rmis_integration.client import Client
from slog import models as slog


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


def endpoint(request):
    result = {"answer": False, "body": ""}
    data = json.loads(request.POST.get("data", request.GET.get("data", "{}")))
    api_key = data.get("api_key", "")
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
                result["body"] = [x.decode('ascii') for x in get_iss_astm(app.get_issledovaniya(pks), app)]
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
             "types": [{"pk": str(x[0]), "title": x[1]} for x in Podrazdeleniya.TYPES]})
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
         "fin_sources": [{"pk": y.pk, "title": y.title} for y in
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
        labs_pks = [x.pk for x in Podrazdeleniya.objects.exclude(p_type=Podrazdeleniya.HIDDEN).exclude(
            p_type=Podrazdeleniya.DEPARTMENT)]

        for r in DResearches.objects.filter(hide=False).order_by("title"):
            autoadd = [x.b.pk for x in AutoAdd.objects.filter(a=r)]
            addto = [x.a.pk for x in AutoAdd.objects.filter(b=r)]

            deps[r.podrazdeleniye.pk].append(
                {"pk": r.pk,
                 "onlywith": -1 if not r.onlywith else r.onlywith.pk,
                 "department_pk": r.podrazdeleniye.pk,
                 "title": r.get_title(),
                 "comment_template": "-1" if not r.comment_variants else r.comment_variants.pk,
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

    for row in Card.objects.filter(base=card_type, individual__in=objects, is_archive=False).prefetch_related(
            "individual").distinct():
        data.append({"type_title": card_type.title,
                     "num": row.number,
                     "family": row.individual.family,
                     "name": row.individual.name,
                     "twoname": row.individual.patronymic,
                     "birthday": row.individual.bd(),
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
