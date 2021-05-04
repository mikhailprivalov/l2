import threading
import time
import re
from collections import defaultdict
from typing import Union

import simplejson as json
import yaml
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.db import connections
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

import api.models as models
import directions.models as directions
import users.models as users
from api import fias
from appconf.manager import SettingManager
from barcodes.views import tubes
from clients.models import CardBase, Individual, Card, Document, District
from directory.models import Fractions, ParaclinicInputField, ResearchSite, Culture, Antibiotic, ResearchGroup
from directory.models import Researches as DResearches
from doctor_call.models import DoctorCall
from external_system.models import FsliRefbookTest
from hospitals.models import Hospitals
from laboratory.decorators import group_required
from laboratory.utils import strdatetime
from pharmacotherapy.models import Drugs
from podrazdeleniya.models import Podrazdeleniya
from slog import models as slog
from slog.models import Log
from statistics_tickets.models import VisitPurpose, ResultOfTreatment, StatisticsTicket, Outcomes, ExcludePurposes
from tfoms.integration import match_enp
from utils.common import non_selected_visible_type
from utils.dates import try_parse_range, try_strptime
from .sql_func import users_by_group
from laboratory.settings import URL_RMIS_AUTH, URL_ELN_MADE, URL_SCHEDULE


def translit(locallangstring):
    """
    Translit func
    :param locallangstring: orign
    :return: translit of locallangstring
    """
    conversion = {
        u'\u0410': 'A',
        u'\u0430': 'a',
        u'\u0411': 'B',
        u'\u0431': 'b',
        u'\u0412': 'V',
        u'\u0432': 'v',
        u'\u0413': 'G',
        u'\u0433': 'g',
        u'\u0414': 'D',
        u'\u0434': 'd',
        u'\u0415': 'E',
        u'\u0435': 'e',
        u'\u0401': 'Yo',
        u'\u0451': 'yo',
        u'\u0416': 'Zh',
        u'\u0436': 'zh',
        u'\u0417': 'Z',
        u'\u0437': 'z',
        u'\u0418': 'I',
        u'\u0438': 'i',
        u'\u0419': 'Y',
        u'\u0439': 'y',
        u'\u041a': 'K',
        u'\u043a': 'k',
        u'\u041b': 'L',
        u'\u043b': 'l',
        u'\u041c': 'M',
        u'\u043c': 'm',
        u'\u041d': 'N',
        u'\u043d': 'n',
        u'\u041e': 'O',
        u'\u043e': 'o',
        u'\u041f': 'P',
        u'\u043f': 'p',
        u'\u0420': 'R',
        u'\u0440': 'r',
        u'\u0421': 'S',
        u'\u0441': 's',
        u'\u0422': 'T',
        u'\u0442': 't',
        u'\u0423': 'U',
        u'\u0443': 'u',
        u'\u0424': 'F',
        u'\u0444': 'f',
        u'\u0425': 'H',
        u'\u0445': 'h',
        u'\u0426': 'Ts',
        u'\u0446': 'ts',
        u'\u0427': 'Ch',
        u'\u0447': 'ch',
        u'\u0428': 'Sh',
        u'\u0448': 'sh',
        u'\u0429': 'Sch',
        u'\u0449': 'sch',
        u'\u042a': '',
        u'\u044a': '',
        u'\u042b': 'Y',
        u'\u044b': 'y',
        u'\u042c': '',
        u'\u044c': '',
        u'\u042d': 'E',
        u'\u044d': 'e',
        u'\u042e': 'Yu',
        u'\u044e': 'yu',
        u'\u042f': 'Ya',
        u'\u044f': 'ya',
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
        app = models.Application.objects.filter(key=appkey, active=True).first()

        resdict["pk"] = int(resdict.get("pk", -111))
        if "LYMPH%" in resdict["result"]:
            resdict["orders"] = {}

        dpk = -1

        if ("bydirection" in request.POST or "bydirection" in request.GET) and not app.tube_work:
            dpk = resdict["pk"]

            if dpk >= 4600000000000:
                dpk -= 4600000000000
                dpk //= 10
            tubes(request, direction_implict_id=dpk)
            if directions.TubesRegistration.objects.filter(issledovaniya__napravleniye__pk=dpk, issledovaniya__time_confirmation__isnull=True).exists():
                resdict["pk"] = directions.TubesRegistration.objects.filter(issledovaniya__napravleniye__pk=dpk, issledovaniya__time_confirmation__isnull=True).order_by("pk").first().pk
            else:
                resdict["pk"] = False
        result["A"] = appkey

        direction = None
        if resdict["pk"] and app:
            if app.tube_work:
                direction = directions.Napravleniya.objects.filter(issledovaniya__tubes__pk=resdict["pk"]).first()
            elif directions.TubesRegistration.objects.filter(pk=resdict["pk"]).exists():
                tubei = directions.TubesRegistration.objects.get(pk=resdict["pk"])
                direction = tubei.issledovaniya_set.first().napravleniye
            pks = []
            for key in resdict["result"].keys():
                if models.RelationFractionASTM.objects.filter(astm_field=key).exists():
                    fractionRels = models.RelationFractionASTM.objects.filter(astm_field=key)
                    for fractionRel in fractionRels:
                        fraction = fractionRel.fraction
                        if directions.Issledovaniya.objects.filter(napravleniye=direction, research=fraction.research, time_confirmation__isnull=True).exists():
                            issled = directions.Issledovaniya.objects.filter(napravleniye=direction, research=fraction.research, time_confirmation__isnull=True).order_by("pk")[0]
                            if directions.Result.objects.filter(issledovaniye=issled, fraction=fraction).exists():
                                fraction_result = directions.Result.objects.filter(issledovaniye=issled, fraction__pk=fraction.pk).order_by("-pk")[0]
                            else:
                                fraction_result = directions.Result(issledovaniye=issled, fraction=fraction)
                            fraction_result.value = str(resdict["result"][key]).strip()  # Установка значения

                            if 'Non-React' in fraction_result.value:
                                fraction_result.value = 'Отрицательно'

                            if fraction_result.value.isdigit():
                                fraction_result.value = "%s.0" % fraction_result.value

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
    result = {"answer": False, "body": "", "patientData": {}}
    data = json.loads(request.POST.get("result", request.GET.get("result", "{}")))
    api_key = request.POST.get("key", request.GET.get("key", ""))
    message_type = data.get("message_type", "C")
    pk_s = str(data.get("pk", "")).strip()
    iss_s = str(data.get("iss_pk", "-1")).strip()
    pk = -1 if not pk_s.isdigit() else int(pk_s)
    iss_pk = -1 if not iss_s.isdigit() else int(iss_s)
    data["app_name"] = "API key is incorrect"
    # pid = data.get("processing_id", "P")
    if models.Application.objects.filter(key=api_key).exists():
        astm_user = users.DoctorProfile.objects.filter(user__username="astm").first()
        if astm_user is None:
            astm_user = users.DoctorProfile.objects.filter(user__is_staff=True).order_by("pk").first()
        app = models.Application.objects.get(key=api_key)
        if app.active:
            data["app_name"] = app.name
            if message_type == "R" or data.get("result") or message_type == "R_BAC":
                if pk != -1 or iss_pk != -1:
                    direction: Union[directions.Napravleniya, None] = None
                    dw = app.direction_work or message_type == "R_BAC"
                    if pk >= 4600000000000:
                        pk -= 4600000000000
                        pk //= 10
                        dw = True
                    if pk == -1:
                        iss = directions.Issledovaniya.objects.filter(pk=iss_pk)
                        if iss.exists():
                            direction = iss[0].napravleniye
                    elif dw:
                        direction = directions.Napravleniya.objects.filter(pk=pk).first()
                    else:
                        direction = directions.Napravleniya.objects.filter(issledovaniya__tubes__pk=pk).first()

                    pks = []
                    oks = []
                    if direction is not None:
                        if message_type == "R" or (data.get("result") and message_type == 'C'):
                            result["patientData"] = {
                                "fio": direction.client.individual.fio(short=True),
                                "card": direction.client.number_with_type(),
                            }

                            result["patientData"]["fioTranslit"] = translit(result["patientData"]["fio"])
                            result["patientData"]["cardTranslit"] = translit(result["patientData"]["card"])

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
                                        for issled in directions.Issledovaniya.objects.filter(
                                            napravleniye=direction, research=fraction_rel.fraction.research, time_confirmation__isnull=True
                                        ):
                                            if directions.Result.objects.filter(issledovaniye=issled, fraction=fraction_rel.fraction).exists():
                                                fraction_result = directions.Result.objects.filter(issledovaniye=issled, fraction=fraction_rel.fraction).order_by("-pk")[0]
                                            else:
                                                fraction_result = directions.Result(issledovaniye=issled, fraction=fraction_rel.fraction)
                                            fraction_result.value = str(results[key]).strip()

                                            if 'Non-React' in fraction_result.value:
                                                fraction_result.value = 'Отрицательно'

                                            find = re.findall(r"\d+.\d+", fraction_result.value)
                                            if len(find) == 0 and fraction_result.value.isdigit():
                                                find = [fraction_result.value]
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
                                            save_state.append({"fraction": fraction_result.fraction.title, "value": fraction_result.value})
                                            issleds.append({"pk": issled.pk, "title": issled.research.title})

                                            if issled not in pks:
                                                pks.append(issled)
                                oks.append(ok)
                        elif message_type == "R_BAC":
                            mo = data.get('mo')
                            if mo:
                                code = mo.get('code')
                                name = mo.get('name')
                                anti = data.get('anti', {})
                                comments = data.get('comments', [])
                                if code:
                                    culture = Culture.objects.filter(lis=code).first()
                                    iss = directions.Issledovaniya.objects.filter(napravleniye=direction, time_confirmation__isnull=True, research__is_microbiology=True)
                                    if iss.filter(pk=iss_pk).exists():
                                        iss = iss.filter(pk=iss_pk)
                                    iss = iss.first()
                                    if not culture:
                                        print('NO CULTURE', code, name)  # noqa: T001
                                    elif not iss:
                                        print('IGNORED')  # noqa: T001
                                    else:
                                        directions.MicrobiologyResultCulture.objects.filter(issledovaniye=iss, culture=culture).delete()

                                        comments = '\n'.join(
                                            [c["text"] for c in comments if not c["text"].startswith('S:') and not c["text"].startswith('R:') and not c["text"].startswith('I:')]
                                        )
                                        culture_result = directions.MicrobiologyResultCulture(issledovaniye=iss, culture=culture, comments=comments)
                                        culture_result.save()

                                        for a in anti:
                                            anti_r = anti[a]
                                            anti_obj = Antibiotic.objects.filter(lis=a).first()
                                            if anti_obj and anti_r.get('RSI'):
                                                a_name = anti_r.get('name', '').replace('µg', 'мг')
                                                a_name_parts = a_name.split()
                                                a_name = a_name_parts[-2] + ' ' + a_name_parts[-1]
                                                anti_result = directions.MicrobiologyResultCultureAntibiotic(
                                                    result_culture=culture_result,
                                                    antibiotic=anti_obj,
                                                    sensitivity=anti_r.get('RSI'),
                                                    dia=anti_r.get('dia', ''),
                                                    antibiotic_amount=a_name,
                                                )
                                                anti_result.save()
                    result["body"] = "{} {} {} {} {}".format(dw, pk, iss_pk, json.dumps(oks), direction is not None)
                else:
                    result["body"] = "pk '{}' is not exists".format(pk_s)
            elif message_type == "Q":
                result["answer"] = True
                pks = [int(x) for x in data.get("query", [])]
                researches = defaultdict(list)
                for row in app.get_issledovaniya(pks):
                    k = row["pk"]
                    i = row["iss"]
                    result["patientData"] = {
                        "fio": i.napravleniye.client.individual.fio(short=True),
                        "card": i.napravleniye.client.number_with_type(),
                    }

                    result["patientData"]["fioTranslit"] = translit(result["patientData"]["fio"])
                    result["patientData"]["cardTranslit"] = translit(result["patientData"]["card"])
                    for fraction in Fractions.objects.filter(research=i.research, hide=False):
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
    req = json.loads(request.body)
    method = req.get('method', 'GET')
    without_default = req.get('withoutDefault', False)
    current_user_hospital_id = request.user.doctorprofile.get_hospital_id() or -1
    hospital_pk = req.get('hospital', current_user_hospital_id)

    su = request.user.is_superuser

    if hospital_pk == -1:
        hospital_pk = None

    if hospital_pk != current_user_hospital_id and not su:
        return JsonResponse({"ok": False})

    can_edit = su or request.user.doctorprofile.has_group('Создание и редактирование пользователей')

    if method == "GET":
        if without_default:
            qs = Podrazdeleniya.objects.filter(hospital_id=hospital_pk).order_by("pk")
        else:
            qs = Podrazdeleniya.objects.filter(Q(hospital_id=hospital_pk) | Q(hospital__isnull=True)).order_by("pk")
        deps = [{"pk": x.pk, "title": x.get_title(), "type": str(x.p_type), "oid": x.oid} for x in qs]
        en = SettingManager.en()
        more_types = []
        if SettingManager.is_morfology_enabled(en):
            more_types.append({"pk": str(Podrazdeleniya.MORFOLOGY), "title": "Морфология"})
        data = {
            "departments": deps,
            "can_edit": can_edit,
            "types": [*[{"pk": str(x[0]), "title": x[1]} for x in Podrazdeleniya.TYPES if x[0] not in [8, 12] and en.get(x[0], True)], *more_types],
        }
        if hasattr(request, 'plain_response') and request.plain_response:
            return data
        return JsonResponse(data)

    if can_edit:
        ok = False
        message = ""
        try:
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
                        department.hospital_id = hospital_pk
                        department.oid = row.get("oid", '')
                        department.save()
                        ok = True
            elif data_type == "insert":
                ok = False
                for row in rows:
                    title = row["title"].strip()
                    if len(title) > 0:
                        department = Podrazdeleniya(title=title, p_type=int(row["type"]), hospital_id=hospital_pk, oid=row.get("oid", ''))
                        department.save()
                        ok = True
        finally:
            return JsonResponse({"ok": ok, "message": message})
    return JsonResponse(0)


@login_required
def otds(request):
    return JsonResponse(
        {"rows": [{"id": -1, "label": "Все отделения"}, *[{"id": x.pk, "label": x.title} for x in Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.DEPARTMENT).order_by("title")]]}
    )


@login_required
def laboratory_journal_params(request):
    return JsonResponse(
        {
            "fin": [{"id": x.pk, "label": f"{x.base.title} – {x.title}"} for x in directions.IstochnikiFinansirovaniya.objects.all().order_by("pk").order_by("base")],
            "groups": [
                {"id": -2, "label": "Все исследования"},
                {"id": -1, "label": "Без группы"},
                *[{"id": x.pk, "label": f"{x.lab.get_title()} – {x.title}"} for x in ResearchGroup.objects.all()],
            ],
        }
    )


def bases(request):
    k = f'view:bases:{request.user.pk}'
    ret = cache.get(k)
    if not ret:
        ret = {
            "bases": [
                {
                    "pk": x.pk,
                    "title": x.title,
                    "code": x.short_title,
                    "hide": x.hide,
                    "history_number": x.history_number,
                    "internal_type": x.internal_type,
                    "fin_sources": [{"pk": y.pk, "title": y.title, "default_diagnos": y.default_diagnos} for y in x.istochnikifinansirovaniya_set.all()],
                }
                for x in CardBase.objects.all()
                .prefetch_related(Prefetch('istochnikifinansirovaniya_set', directions.IstochnikiFinansirovaniya.objects.filter(hide=False).order_by('-order_weight')))
                .order_by('-order_weight')
            ]
        }
        cache.set(k, ret, 100)
    if hasattr(request, 'plain_response') and request.plain_response:
        return ret
    return JsonResponse(ret)


def current_user_info(request):
    user = request.user
    ret = {
        "auth": user.is_authenticated,
        "doc_pk": -1,
        "username": "",
        "fio": "",
        "department": {"pk": -1, "title": ""},
        "groups": [],
        "eds_token": None,
        "modules": SettingManager.l2_modules(),
        "user_services": [],
    }
    if ret["auth"]:
        def fill_user_data():
            doctorprofile = users.DoctorProfile.objects.prefetch_related(
                Prefetch(
                    'restricted_to_direct',
                    queryset=DResearches.objects.only('pk'),
                ),
                Prefetch(
                    'users_services',
                    queryset=DResearches.objects.only('pk'),
                ),
            ).select_related(
                'podrazdeleniye'
            ).get(user_id=user.pk)

            ret["fio"] = doctorprofile.fio
            ret["doc_pk"] = doctorprofile.pk
            ret["rmis_location"] = doctorprofile.rmis_location
            ret["rmis_login"] = doctorprofile.rmis_login
            ret["rmis_password"] = doctorprofile.rmis_password
            ret["department"] = {"pk": doctorprofile.podrazdeleniye_id, "title": doctorprofile.podrazdeleniye.title}
            ret["restricted"] = [x.pk for x in doctorprofile.restricted_to_direct.all()]
            ret["user_services"] = [x.pk for x in doctorprofile.users_services.all() if x not in ret["restricted"]]
            ret["hospital"] = doctorprofile.get_hospital_id()
            ret["all_hospitals_users_control"] = doctorprofile.all_hospitals_users_control
            ret["eds_token"] = doctorprofile.get_eds_token()

            try:
                connections.close_all()
            except Exception as e:
                print(f"Error closing connections {e}")  # noqa: T001

        def fill_settings():
            ret["groups"] = list(user.groups.values_list('name', flat=True))
            ret["su"] = user.is_superuser
            ret["username"] = user.username
            if user.is_superuser:
                ret["groups"].append("Admin")

            ret["modules"] = SettingManager.l2_modules()
            ret["rmis_enabled"] = SettingManager.get("rmis_enabled", default='false', default_type='b')
            ret["directions_params_org_form_default_pk"] = SettingManager.get("directions_params_org_form_default_pk", default='', default_type='s')

            en = SettingManager.en()
            ret["extended_departments"] = {}

            st_base = ResearchSite.objects.filter(hide=False).order_by('order', 'title')

            sites_by_types = {}
            for s in st_base:
                if s.site_type not in sites_by_types:
                    sites_by_types[s.site_type] = []
                sites_by_types[s.site_type].append({"pk": s.pk, "title": s.title, "type": s.site_type, "extended": True, 'e': s.site_type + 4})

            for e in en:
                if e < 4 or not en[e]:
                    continue

                t = e - 4
                has_def = DResearches.objects.filter(hide=False, site_type__isnull=True, **DResearches.filter_type(e)).exists()

                if has_def and e != 12:
                    d = [{"pk": None, "title": 'Общие', 'type': t, "extended": True}]
                else:
                    d = []

                ret["extended_departments"][e] = [*d, *sites_by_types.get(t, [])]

            if SettingManager.is_morfology_enabled(en):
                ret["extended_departments"][Podrazdeleniya.MORFOLOGY] = []
                if en.get(8):
                    ret["extended_departments"][Podrazdeleniya.MORFOLOGY].append(
                        {"pk": Podrazdeleniya.MORFOLOGY + 1, "title": "Микробиология", "type": Podrazdeleniya.MORFOLOGY, "extended": True, "e": Podrazdeleniya.MORFOLOGY}
                    )
                if en.get(9):
                    ret["extended_departments"][Podrazdeleniya.MORFOLOGY].append(
                        {"pk": Podrazdeleniya.MORFOLOGY + 2, "title": "Цитология", "type": Podrazdeleniya.MORFOLOGY, "extended": True, "e": Podrazdeleniya.MORFOLOGY}
                    )
                if en.get(10):
                    ret["extended_departments"][Podrazdeleniya.MORFOLOGY].append(
                        {"pk": Podrazdeleniya.MORFOLOGY + 3, "title": "Гистология", "type": Podrazdeleniya.MORFOLOGY, "extended": True, "e": Podrazdeleniya.MORFOLOGY}
                    )
            try:
                connections.close_all()
            except Exception as e:
                print(f"Error closing connections {e}")  # noqa: T001

        t1 = threading.Thread(target=fill_user_data)
        t2 = threading.Thread(target=fill_settings)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

    if hasattr(request, 'plain_response') and request.plain_response:
        return ret
    return JsonResponse(ret)


@login_required
def directive_from(request):
    data = []
    hospital = request.user.doctorprofile.hospital
    for dep in (
        Podrazdeleniya.objects.filter(
            p_type__in=(Podrazdeleniya.DEPARTMENT, Podrazdeleniya.HOSP, Podrazdeleniya.PARACLINIC),
            hospital__in=(hospital, None)
        )
        .prefetch_related(
            Prefetch(
                'doctorprofile_set',
                queryset=(
                    users.DoctorProfile.objects.filter(user__groups__name__in=["Лечащий врач", "Врач параклиники"])
                    .distinct('fio', 'pk')
                    .filter(
                        Q(hospital=hospital) | Q(hospital__isnull=True)
                    )
                    .order_by("fio")
                ),
            )
        )
        .order_by('title')
        .only('pk', 'title')
    ):
        d = {
            "pk": dep.pk,
            "title": dep.title,
            "docs": [{"pk": x.pk, "fio": x.fio} for x in dep.doctorprofile_set.all()],
        }
        data.append(d)

    result = {"data": data}
    if hasattr(request, 'plain_response') and request.plain_response:
        return result
    return JsonResponse(result)


@group_required("Оформление статталонов", "Лечащий врач", "Оператор лечащего врача")
def statistics_tickets_types(request):
    result = {
        "visit": non_selected_visible_type(VisitPurpose),
        "result": non_selected_visible_type(ResultOfTreatment),
        "outcome": non_selected_visible_type(Outcomes),
        "exclude": non_selected_visible_type(ExcludePurposes),
    }
    return JsonResponse(result)


@group_required("Оформление статталонов", "Лечащий врач", "Оператор лечащего врача")
def statistics_tickets_send(request):
    response = {"ok": True}
    rd = json.loads(request.body)
    ofname = rd.get("ofname") or -1
    doc = None
    if ofname > -1 and users.DoctorProfile.objects.filter(pk=ofname).exists():
        doc = users.DoctorProfile.objects.get(pk=ofname)
    t = StatisticsTicket(
        card=Card.objects.get(pk=rd["card_pk"]),
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
        date_ticket=rd.get("date_ticket", None),
    )
    t.save()
    Log(key="", type=7000, body=json.dumps(rd), user=request.user.doctorprofile).save()
    return JsonResponse(response)


@group_required("Оформление статталонов", "Лечащий врач", "Оператор лечащего врача")
def statistics_tickets_get(request):
    response = {"data": []}
    request_data = json.loads(request.body)
    date_start, date_end = try_parse_range(request_data["date"])
    n = 0
    for row in (
        StatisticsTicket.objects.filter(Q(doctor=request.user.doctorprofile) | Q(creator=request.user.doctorprofile))
        .filter(
            date__range=(
                date_start,
                date_end,
            )
        )
        .order_by('pk')
    ):
        if not row.invalid_ticket:
            n += 1
        response["data"].append(
            {
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
                "disp": (
                    row.get_dispensary_registration_display()
                    + (" (" + row.dispensary_diagnos + ")" if row.dispensary_diagnos != "" else "")
                    + (" (" + row.dispensary_exclude_purpose.title + ")" if row.dispensary_exclude_purpose else "")
                ),
                "result": row.result.title if row.result else "",
                "outcome": row.outcome.title if row.outcome else "",
                "invalid": row.invalid_ticket,
                "can_invalidate": row.can_invalidate(),
            }
        )
    return JsonResponse(response)


@group_required("Оформление статталонов", "Лечащий врач", "Оператор лечащего врача")
def statistics_tickets_invalidate(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    if StatisticsTicket.objects.filter(Q(doctor=request.user.doctorprofile) | Q(creator=request.user.doctorprofile)).filter(pk=request_data.get("pk", -1)).exists():
        if StatisticsTicket.objects.get(pk=request_data["pk"]).can_invalidate():
            for s in StatisticsTicket.objects.filter(pk=request_data["pk"]):
                s.invalid_ticket = request_data.get("invalid", False)
                s.save()
            response["ok"] = True
            Log(key=str(request_data["pk"]), type=7001, body=json.dumps(request_data.get("invalid", False)), user=request.user.doctorprofile).save()
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
    d = (
        directions.Napravleniya.objects.filter(istochnik_f__rmis_auto_send=False, force_rmis_send=False, issledovaniya__time_confirmation__range=(date_start, date_end))
        .exclude(issledovaniya__time_confirmation__isnull=True)
        .distinct()
        .order_by("pk")
    )
    data["directions"] = [{"pk": x.pk, "patient": {"fiodr": x.client.individual.fio(full=True), "card": x.client.number_with_type()}, "fin": x.fin_title} for x in d]
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
        for r in users.AssignmentTemplates.objects.filter(title__istartswith=q, global_template=False).order_by('title')[:10]:
            result.append({"pk": r.pk, "title": r.title, "researches": [x.research.pk for x in users.AssignmentResearches.objects.filter(template=r, research__hide=False)]})
    return JsonResponse({"result": result, "q": q})


def load_templates(request):
    result = []
    t = request.GET.get('type', '1')
    for r in users.AssignmentTemplates.objects.filter(global_template=t == '1').order_by('title'):
        result.append({"pk": r.pk, "title": r.title, "researches": [x.research.pk for x in users.AssignmentResearches.objects.filter(template=r, research__hide=False)]})
    return JsonResponse({"result": result})


def get_template(request):
    title = ''
    researches = []
    global_template = False
    pk = request.GET.get('pk')
    if pk:
        t = users.AssignmentTemplates.objects.get(pk=pk)
        title = t.title
        researches = [x.research_id for x in users.AssignmentResearches.objects.filter(template=t, research__hide=False)]
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
                to_add = [x for x in researches if not users.AssignmentResearches.objects.filter(template=t, research__pk=x).exists()]
                for ta in to_add:
                    if DResearches.objects.filter(pk=ta).exists():
                        users.AssignmentResearches(template=t, research=DResearches.objects.get(pk=ta)).save()
                response["ok"] = True
    return JsonResponse(response)


def modules_view(request):
    return JsonResponse({"l2_cards": SettingManager.get("l2_cards_module", default='false', default_type='b')})


def autocomplete(request):
    t = request.GET.get("type")
    v = request.GET.get("value", "")
    limit = int(request.GET.get("limit", 10))
    data = []
    if v != "" and limit > 0:
        if t == "harmful":
            p = Card.objects.filter(harmful_factor__istartswith=v).distinct('harmful_factor')[:limit]
            if p.exists():
                data = [x.harmful_factor for x in p]
        elif t == "fias":
            data = fias.suggest(v)
        elif t == "name":
            p = Individual.objects.filter(name__istartswith=v).distinct('name')[:limit]
            if p.exists():
                data = [x.name for x in p]
        elif t == "family":
            p = Individual.objects.filter(family__istartswith=v).distinct('family')[:limit]
            if p.exists():
                data = [x.family for x in p]
        elif t == "patronymic":
            p = Individual.objects.filter(patronymic__istartswith=v).distinct('patronymic')[:limit]
            if p.exists():
                data = [x.patronymic for x in p]
        elif t == "work_place":
            p = Card.objects.filter(work_place__istartswith=v).distinct('work_place')[:limit]
            if p.exists():
                data = [x.work_place for x in p]
        elif t == "main_diagnosis":
            p = Card.objects.filter(main_diagnosis__istartswith=v).distinct('main_diagnosis')[:limit]
            if p.exists():
                data = [x.main_diagnosis for x in p]
        elif t == "work_position":
            p = Card.objects.filter(work_position__istartswith=v).distinct('work_position')[:limit]
            if p.exists():
                data = [x.work_position for x in p]
        elif "who_give:" in t:
            tpk = t.split(":")[1]
            p = Document.objects.filter(document_type__pk=tpk, who_give__istartswith=v).distinct('who_give')[:limit]
            if p.exists():
                data = [x.who_give for x in p]
        elif t == "fsli":
            if v == "HGB":
                p = FsliRefbookTest.objects.filter(
                    Q(code_fsli__startswith=v) | Q(title__icontains=v) | Q(english_title__icontains=v) | Q(short_title__icontains=v) | Q(synonym__istartswith=v) | Q(synonym='Hb')
                )
            else:
                p = FsliRefbookTest.objects.filter(
                    Q(code_fsli__startswith=v) | Q(title__icontains=v) | Q(english_title__icontains=v) | Q(short_title__icontains=v) | Q(synonym__istartswith=v)
                )

            p = p.filter(active=True).distinct('code_fsli').order_by('code_fsli', 'ordering')[:limit]
            if p.exists():
                data = [{"code_fsli": x.code_fsli, "short_title": x.short_title, "title": x.title, "sample": x.sample, "synonym": x.synonym, "nmu": x.code_nmu} for x in p]
        elif t == "drugs":
            data = [
                {
                    "title": str(x),
                    "pk": x.pk,
                }
                for x in Drugs.objects.filter(Q(mnn__istartswith=v) | Q(trade_name__istartswith=v)).order_by('mnn', 'trade_name').distinct('mnn', 'trade_name')[:limit]
            ]
    return JsonResponse({"data": data})


def laborants(request):
    data = []
    if SettingManager.l2('results_laborants'):
        data = [{"pk": '-1', "fio": 'Не выбрано'}]
        for d in users.DoctorProfile.objects.filter(user__groups__name="Лаборант", podrazdeleniye__p_type=users.Podrazdeleniya.LABORATORY).order_by('fio'):
            data.append({"pk": str(d.pk), "fio": d.fio})
    return JsonResponse({"data": data, "doc": request.user.doctorprofile.has_group("Врач-лаборант")})


@login_required
def load_docprofile_by_group(request):
    request_data = json.loads(request.body)
    users = users_by_group(request_data['group'])
    users_grouped = {}
    for row in users:
        if row[2] not in users_grouped:
            users_grouped[row[2]] = {'id': f"pord-{row[2]}", 'label': row[4] or row[3], 'children': []}
        users_grouped[row[2]]['children'].append({'id': str(row[0]), 'label': row[1], 'podr': row[4] or row[3]})

    return JsonResponse({"users": list(users_grouped.values())})


@login_required
@group_required("Создание и редактирование пользователей")
def users_view(request):
    request_data = json.loads(request.body)
    user_hospital_pk = request.user.doctorprofile.get_hospital_id()
    hospital_pk = request_data.get('selected_hospital', user_hospital_pk)

    can_edit = request.user.is_superuser or request.user.doctorprofile.all_hospitals_users_control or hospital_pk == user_hospital_pk

    data = []

    if can_edit:
        podr = Podrazdeleniya.objects.filter(Q(hospital_id=hospital_pk) | Q(hospital__isnull=True)).exclude(p_type=Podrazdeleniya.HIDDEN, hospital__isnull=True).order_by("title")
        for x in podr:
            otd = {"pk": x.pk, "title": x.title, "users": []}
            docs = users.DoctorProfile.objects.filter(podrazdeleniye=x, hospital_id=hospital_pk).order_by('fio')
            if not request.user.is_superuser:
                docs = docs.filter(user__is_superuser=False)
            for y in docs:
                otd["users"].append({"pk": y.pk, "fio": y.get_fio(), "username": y.user.username})
            data.append(otd)

    spec = users.Speciality.objects.all().order_by("title")
    spec_data = []
    for s in spec:
        spec_data.append({"pk": s.pk, "title": s.title})

    return JsonResponse({"departments": data, "specialities": spec_data})


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
            "rmis_resource_id": '',
            "doc_pk": -1,
            "doc_code": -1,
            "rmis_employee_id": '',
            "rmis_service_id_time_table": '',
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
            "rmis_resource_id": doc.rmis_resource_id or '',
            "rmis_password": '',
            "doc_pk": doc.user.pk,
            "personal_code": doc.personal_code,
            "speciality": doc.specialities_id,
            "rmis_employee_id": doc.rmis_employee_id,
            "rmis_service_id_time_table": doc.rmis_service_id_time_table,
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
    rmis_employee_id = str(ud["rmis_employee_id"]).strip() or None
    rmis_service_id_time_table = str(ud["rmis_service_id_time_table"]).strip() or None
    rmis_login = ud["rmis_login"].strip() or None
    rmis_password = ud["rmis_password"].strip() or None
    personal_code = ud.get("personal_code", 0)
    rmis_resource_id = ud["rmis_resource_id"].strip() or None
    user_hospital_pk = request.user.doctorprofile.get_hospital_id()
    hospital_pk = request_data.get('hospital_pk', user_hospital_pk)

    can_edit = request.user.is_superuser or request.user.doctorprofile.all_hospitals_users_control or hospital_pk == user_hospital_pk

    if not can_edit:
        return JsonResponse({"ok": False})

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
            doc.specialities_id = ud.get('speciality', None)
            doc.fio = ud["fio"]
            doc.rmis_location = rmis_location
            doc.rmis_employee_id = rmis_employee_id
            doc.rmis_service_id_time_table = rmis_service_id_time_table
            doc.personal_code = personal_code
            doc.rmis_resource_id = rmis_resource_id
            doc.hospital_id = hospital_pk
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
            return JsonResponse({**d, "datetime": d["datetime"].strftime('%d.%m.%Y %H:%M'), "patient_uid": patient_uid, "pk": int(str(pk)[1:])})
    return JsonResponse({})


@login_required
def user_fill_slot(request):
    slot = json.loads(request.body).get('slot', {})
    slot_data = slot.get('data', {})
    if directions.Napravleniya.objects.filter(rmis_slot_id=slot["id"]).exists():
        direction = directions.Napravleniya.objects.filter(rmis_slot_id=slot["id"])[0].pk
    else:
        result = directions.Napravleniya.gen_napravleniya_by_issledovaniya(
            slot["card_pk"],
            "",
            "ОМС",
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
            rmis_slot=slot["id"],
        )
        direction = result["list_id"][0]
    return JsonResponse({"direction": direction})


@login_required
def job_types(request):
    types = [{"pk": x.pk, "title": x.title} for x in directions.TypeJob.objects.filter(hide=False)]
    g = Group.objects.filter(name="Зав. лабораторией").first()
    is_zav_lab = (g and g in request.user.groups.all()) or request.user.is_superuser
    users_list = [request.user.doctorprofile.get_data()]
    if is_zav_lab:
        for user in users.DoctorProfile.objects.filter(user__groups__name__in=["Лаборант", "Врач-лаборант"]).exclude(pk=request.user.doctorprofile.pk).order_by("fio").distinct():
            users_list.append(user.get_data())
    return JsonResponse({"types": types, "is_zav_lab": is_zav_lab, "users": users_list})


@login_required
def job_save(request):
    data = json.loads(request.body)
    ej = directions.EmployeeJob(type_job_id=data["type"], count=data["count"], doc_execute_id=data["executor"], date_job=try_strptime(data["date"]).date())
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
        for user in users.DoctorProfile.objects.filter(user__groups__name__in=["Лаборант", "Врач-лаборант"]).exclude(pk=request.user.doctorprofile.pk).order_by("fio").distinct():
            users_list.append(user)
    result = []
    for j in directions.EmployeeJob.objects.filter(doc_execute__in=users_list, date_job=date).order_by("doc_execute", "-time_save"):
        result.append({"pk": j.pk, "executor": j.doc_execute.get_fio(), "type": j.type_job.title, "count": j.count, "saved": strdatetime(j.time_save), "canceled": bool(j.who_do_cancel)})
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


def reader_status(request):
    data = json.loads(request.body)
    reader_id = data.get('readerId', 'null')
    data = json.loads(cache.get(f'reader-status:{reader_id}', '{"status": "none"}'))
    return JsonResponse({"status": data.get('status'), "polis": data.get('polis'), "fio": data.get('fio'), 'details': data.get('details', {})})


def reader_status_update(request):
    data = json.loads(request.body)
    reader_id = data.get('readerId')

    if not reader_id:
        return JsonResponse({"ok": True})

    status = data['status']

    if status == 'inserted':
        polis = data['polis']
        fio = data['fio']
        cache.set(f'reader-status:{reader_id}', json.dumps({"status": 'inserted', "polis": polis, "fio": fio, "details": data['details']}), 10)
    else:
        cache.set(f'reader-status:{reader_id}', '{"status": "wait"}', 10)

    return JsonResponse({"ok": True})


def actual_districts(request):
    data = json.loads(request.body)
    card_pk = data.get('card_pk')
    rows = District.objects.all().order_by('-sort_weight', '-id').values('pk', 'title', 'is_ginekolog')
    rows = [{"id": -1, "label": "НЕ ВЫБРАН"}, *[{"id": x['pk'], "label": x["title"] if not x['is_ginekolog'] else "Гинекология: {}".format(x['title'])} for x in rows]]

    users = users_by_group(['Лечащий врач'])
    users = [{"id": -1, "label": "НЕ ВЫБРАН"}, *[{'id': row[0], 'label': row[1]} for row in users]]

    purposes = DoctorCall.PURPOSES
    purposes = [{'id': row[0], 'label': row[1]} for row in purposes]

    hospitals = Hospitals.objects.filter(hide=False).order_by('short_title').values('pk', 'short_title', 'title', 'code_tfoms')
    hospitals = [{"id": -1, "label": "НЕ ВЫБРАНО"}, *[{"id": x['pk'], "label": x["short_title"] or x["title"], "code_tfoms": x["code_tfoms"]} for x in hospitals]]

    if card_pk is not None:
        card_hospital_id = -1
        if SettingManager.l2('tfoms'):
            card = Card.objects.get(pk=data['card_pk'])
            enp = card.individual.get_enp()
            if enp:
                from_tfoms = match_enp(card.individual.get_enp())

                if from_tfoms and from_tfoms.get('unit_code'):
                    card_hospital_id = {x['code_tfoms']: x['id'] for x in hospitals if x.get("code_tfoms")}.get(from_tfoms['unit_code']) or -1
    else:
        card_hospital_id = -1

    if card_hospital_id == -1 and len(hospitals) == 2:
        card_hospital_id = hospitals[1]['id']

    data = {'rows': rows, 'docs': users, 'purposes': purposes, 'hospitals': hospitals, 'hospitalId': card_hospital_id}
    return JsonResponse(data)


def hospitals(request):
    data = json.loads(request.body)
    any_hospital = request.user.doctorprofile.all_hospitals_users_control
    filters = {}
    if data.get('filterByUserHospital') and not any_hospital:
        filters['pk'] = request.user.doctorprofile.get_hospital_id()
    rows = Hospitals.objects.filter(hide=False, **filters).order_by('-is_default', 'short_title').values('pk', 'short_title', 'title', 'code_tfoms')
    default_hospital = []
    if any_hospital:
        default_hospital = [
            {
                "id": -1,
                "label": "Все",
                "code_tfoms": "000000",
            },
            {
                "id": -2,
                "label": "Не выбрано",
                "code_tfoms": "000001",
            },
        ]
    result = {
        "hospitals": [
            *[
                {
                    "id": x['pk'],
                    "label": x["short_title"] or x["title"],
                    "code_tfoms": x["code_tfoms"],
                }
                for x in rows
            ],
            *default_hospital,
        ]
    }
    if hasattr(request, 'plain_response') and request.plain_response:
        return result
    return JsonResponse(result)


def rmis_link(request):
    d = request.user.doctorprofile
    auth_param = URL_RMIS_AUTH.replace('userlogin', d.rmis_login).replace('userpassword', d.rmis_password)
    url_schedule = URL_SCHEDULE.replace('organization_param', d.hospital.rmis_org_id).replace('service_param', d.rmis_service_id_time_table).replace('employee_param', d.rmis_employee_id)
    return JsonResponse({'auth_param': auth_param, 'url_eln': URL_ELN_MADE,
                         'url_schedule': url_schedule})
