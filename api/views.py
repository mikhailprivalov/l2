import logging
import threading
import time
import re
from collections import defaultdict
from typing import Optional, Union

import pytz_deprecation_shim as pytz

from api.models import ManageDoctorProfileAnalyzer, Analyzer
from directions.views import create_case_by_cards
from directory.models import Researches, SetResearch, SetOrderResearch, PatientControlParam
from doctor_schedule.models import ScheduleResource
from ecp_integration.integration import get_reserves_ecp, get_slot_ecp
from laboratory.settings import (
    SYSTEM_AS_VI,
    SOME_LINKS,
    DISABLED_FORMS,
    DISABLED_STATISTIC_CATEGORIES,
    DISABLED_STATISTIC_REPORTS,
    TIME_ZONE,
    TITLE_REPORT_FILTER_STATTALON_FIELDS,
    SEARCH_PAGE_STATISTIC_PARAMS,
    UNLIMIT_PERIOD_STATISTIC_GROUP,
    TITLE_REPORT_FILTER_HAS_ALL_FIN_SOURCE,
    STATISTIC_TYPE_DEPARTMENT,
    USE_TFOMS_DISTRICT,
    TYPE_COMPANY_SET_DIRECTION_PDF,
    MEDEXAM_FIN_SOURCE_TITLE,
)
from utils.response import status_response

from django.core.validators import validate_email
from django.db.utils import IntegrityError
from utils.data_verification import as_model, data_parse

import simplejson as json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.db import connections, transaction
from django.db.models import Prefetch, Q, Exists, OuterRef
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

import api.models as models
import directions.models as directions
import users.models as users
from contracts.models import Company, PriceCategory, PriceName, PriceCoast, Contract, CompanyDepartment, MedicalExamination
from api import fias
from appconf.manager import SettingManager
from barcodes.views import tubes
from clients.models import CardBase, Individual, Card, Document, District, HarmfulFactor
from context_processors.utils import menu
from directory.models import (
    Fractions,
    ParaclinicInputField,
    ParaclinicUserInputTemplateField,
    ResearchSite,
    Culture,
    Antibiotic,
    ResearchGroup,
    Researches as DResearches,
    ScreeningPlan,
    Phenotype,
)
from doctor_call.models import DoctorCall
from external_system.models import FsliRefbookTest
from hospitals.models import Hospitals, DisableIstochnikiFinansirovaniya
from laboratory.decorators import group_required
from laboratory.utils import strdatetime
from pharmacotherapy.models import Drugs
from podrazdeleniya.models import Podrazdeleniya, Room
from slog import models as slog
from slog.models import Log
from statistics_tickets.models import VisitPurpose, ResultOfTreatment, StatisticsTicket, Outcomes, ExcludePurposes
from tfoms.integration import match_enp
from utils.common import non_selected_visible_type
from utils.dates import try_parse_range, try_strptime
from utils.nsi_directories import NSI
from utils.xh import get_all_hospitals, simple_join_two_pdf_files, simple_save_pdf_file, correspondence_set_file_hash
from .dicom import search_dicom_study
from .directions.sql_func import get_lab_podr
from .sql_func import users_by_group, users_all, get_diagnoses, get_resource_researches, search_data_by_param, search_text_stationar
from laboratory.settings import URL_RMIS_AUTH, URL_ELN_MADE, URL_SCHEDULE
import urllib.parse
from django.utils.module_loading import import_string

logger = logging.getLogger("API")


def translit(locallangstring):
    """
    Translit func
    :param locallangstring: orign
    :return: translit of locallangstring
    """
    conversion = {
        "\u0410": "A",
        "\u0430": "a",
        "\u0411": "B",
        "\u0431": "b",
        "\u0412": "V",
        "\u0432": "v",
        "\u0413": "G",
        "\u0433": "g",
        "\u0414": "D",
        "\u0434": "d",
        "\u0415": "E",
        "\u0435": "e",
        "\u0401": "Yo",
        "\u0451": "yo",
        "\u0416": "Zh",
        "\u0436": "zh",
        "\u0417": "Z",
        "\u0437": "z",
        "\u0418": "I",
        "\u0438": "i",
        "\u0419": "Y",
        "\u0439": "y",
        "\u041a": "K",
        "\u043a": "k",
        "\u041b": "L",
        "\u043b": "l",
        "\u041c": "M",
        "\u043c": "m",
        "\u041d": "N",
        "\u043d": "n",
        "\u041e": "O",
        "\u043e": "o",
        "\u041f": "P",
        "\u043f": "p",
        "\u0420": "R",
        "\u0440": "r",
        "\u0421": "S",
        "\u0441": "s",
        "\u0422": "T",
        "\u0442": "t",
        "\u0423": "U",
        "\u0443": "u",
        "\u0424": "F",
        "\u0444": "f",
        "\u0425": "H",
        "\u0445": "h",
        "\u0426": "Ts",
        "\u0446": "ts",
        "\u0427": "Ch",
        "\u0447": "ch",
        "\u0428": "Sh",
        "\u0448": "sh",
        "\u0429": "Sch",
        "\u0449": "sch",
        "\u042a": "",
        "\u044a": "",
        "\u042b": "Y",
        "\u044b": "y",
        "\u042c": "",
        "\u044c": "",
        "\u042d": "E",
        "\u044d": "e",
        "\u042e": "Yu",
        "\u044e": "yu",
        "\u042f": "Ya",
        "\u044f": "ya",
    }
    translitstring = []
    for c in locallangstring:
        translitstring.append(conversion.setdefault(c, c))
    return "".join(translitstring)


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
            resdict = json.loads(request.POST["result"])
            appkey = request.POST.get("key", "")
        else:
            resdict = json.loads(request.GET["result"])
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
                resdict["pk"] = (
                    directions.TubesRegistration.objects.filter(issledovaniya__napravleniye__pk=dpk, issledovaniya__time_confirmation__isnull=True).order_by("number").first().number
                )
            else:
                resdict["pk"] = False
        result["A"] = appkey

        direction = None
        if resdict["pk"] and app:
            if app.tube_work:
                direction = directions.Napravleniya.objects.filter(issledovaniya__tubes__number=resdict["pk"]).first()
            elif directions.TubesRegistration.objects.filter(number=resdict["pk"]).exists():
                tubei = directions.TubesRegistration.objects.get(number=resdict["pk"])
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

                            if "Non-React" in fraction_result.value:
                                fraction_result.value = "Отрицательно"

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
        elif not directions.TubesRegistration.objects.filter(number=resdict["pk"]).exists():
            if dpk > -1:
                resdict["pk"] = dpk
            slog.Log(key=resdict["pk"], type=23, body=json.dumps(resdict), user=None).save()
    except Exception as e:
        logger.exception(e)
        result = {"ok": False, "message": "Серверная ошибка"}
    return JsonResponse(result)


@csrf_exempt
def endpoint(request):
    result = {"answer": False, "body": "", "patientData": {}, "ok": False}
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
                    by_tube = False
                    if pk == -1:
                        iss = directions.Issledovaniya.objects.filter(pk=iss_pk)
                        if iss.exists():
                            direction = iss[0].napravleniye
                    elif dw:
                        direction = directions.Napravleniya.objects.filter(pk=pk).first()
                    else:
                        direction = directions.Napravleniya.objects.filter(issledovaniya__tubes__number=pk).first()
                        by_tube = True

                    pks = []
                    oks = []
                    if direction is not None:
                        if message_type == "R" or (data.get("result") and message_type == "C"):
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
                                        iss_q = directions.Issledovaniya.objects.filter(napravleniye=direction, research=fraction_rel.fraction.research, time_confirmation__isnull=True)
                                        for issled in iss_q:
                                            if by_tube and not issled.tubes.filter(number=pk).exists() and issled.tubes.all().count() > 0:
                                                continue
                                            if directions.Result.objects.filter(issledovaniye=issled, fraction=fraction_rel.fraction).exists():
                                                fraction_result = directions.Result.objects.filter(issledovaniye=issled, fraction=fraction_rel.fraction).order_by("-pk")[0]
                                            else:
                                                fraction_result = directions.Result(issledovaniye=issled, fraction=fraction_rel.fraction)
                                            tmp_replace_value = {}
                                            if fraction_rel.replace_value:
                                                try:
                                                    tmp_replace_value = json.loads(fraction_rel.replace_value)
                                                    if not isinstance(tmp_replace_value, dict):
                                                        tmp_replace_value = {}
                                                except Exception:
                                                    tmp_replace_value = {}
                                            if str(results[key]).strip() in tmp_replace_value:
                                                fraction_result.value = str(tmp_replace_value[str(results[key]).strip()])
                                            else:
                                                fraction_result.value = str(results[key]).strip()

                                            if "Non-React" in fraction_result.value:
                                                fraction_result.value = "Отрицательно"

                                            find = re.findall(r"\d+.\d+", fraction_result.value)
                                            if len(find) == 0 and fraction_result.value.isdigit():
                                                find = [fraction_result.value]
                                            if len(find) > 0:
                                                val_str = fraction_result.value
                                                for f in find:
                                                    try:
                                                        val = float(f) * fraction_rel.get_multiplier_display()
                                                        val = app.auto_set_places(fraction_rel, val)
                                                        val_str = val_str.replace(f, str(val))
                                                    except Exception as e:
                                                        logger.exception(e)
                                                fraction_result.value = val_str

                                            fraction_result.iteration = 1
                                            ref = fraction_rel.default_ref
                                            if ref:
                                                fraction_result.ref_title = ref.title
                                                fraction_result.ref_about = ref.about
                                                fraction_result.ref_m = ref.m
                                                fraction_result.ref_f = ref.f
                                            fraction_result.save()
                                            result["ok"] = True
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
                            mo = data.get("mo")
                            if mo:
                                code = mo.get("code")
                                name = mo.get("name")
                                anti = data.get("anti", {})
                                phenotype = data.get("phen", [])
                                comments = [c if not isinstance(c, str) else {"text": c} for c in data.get("comments", [])]
                                if code:
                                    culture = Culture.objects.filter(Q(lis=code) | Q(title=name)).filter(hide=False).first()
                                    if not culture:
                                        culture = models.RelationCultureASTM.objects.filter(Q(astm_field=code) | Q(astm_field=name)).first()
                                    iss = directions.Issledovaniya.objects.filter(napravleniye=direction, time_confirmation__isnull=True, research__is_microbiology=True)
                                    if iss.filter(pk=iss_pk).exists():
                                        iss = iss.filter(pk=iss_pk)
                                    iss = iss.first()
                                    if not culture:
                                        print("NO CULTURE", code, name)  # noqa: T001
                                    elif not iss:
                                        print("IGNORED")  # noqa: T001
                                    else:
                                        directions.MicrobiologyResultCulture.objects.filter(issledovaniye=iss, culture=culture).delete()

                                        comments = "\n".join(
                                            [c["text"] for c in comments if not c["text"].startswith("S:") and not c["text"].startswith("R:") and not c["text"].startswith("I:")]
                                        )
                                        culture_result = directions.MicrobiologyResultCulture(issledovaniye=iss, culture=culture, comments=comments)
                                        culture_result.save()

                                        for a in anti:
                                            anti_r = anti[a]
                                            anti_obj = Antibiotic.objects.filter(lis=a).first()
                                            if anti_obj and anti_r.get("RSI"):
                                                a_name = anti_r.get("name", "").replace("µg", "мг")
                                                a_name_parts = a_name.split()
                                                a_name = a_name_parts[-2] + " " + a_name_parts[-1]
                                                anti_result = directions.MicrobiologyResultCultureAntibiotic(
                                                    result_culture=culture_result,
                                                    antibiotic=anti_obj,
                                                    sensitivity=anti_r.get("RSI"),
                                                    dia=anti_r.get("dia", ""),
                                                    antibiotic_amount=a_name,
                                                )
                                                anti_result.save()
                                        for ph in phenotype:
                                            phen_obj = Phenotype.objects.filter(lis=ph["code"], hide=False).first()
                                            if phen_obj and not directions.MicrobiologyResultPhenotype.objects.filter(result_culture=culture_result, phenotype=phen_obj).exists():
                                                phen_result = directions.MicrobiologyResultPhenotype(
                                                    result_culture=culture_result,
                                                    phenotype=phen_obj,
                                                )
                                                phen_result.save()
                    result["body"] = "{} {} {} {} {}".format(dw, pk, iss_pk, json.dumps(oks), direction is not None)
                else:
                    result["body"] = "pk '{}' is not exists".format(pk_s)
            elif message_type == "Q":
                result["answer"] = True
                pks = [int(x) for x in data.get("query", []) if isinstance(x, int) or (isinstance(x, str) and x.isdigit())]
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
    method = req.get("method", "GET")
    without_default = req.get("withoutDefault", False)
    current_user_hospital_id = request.user.doctorprofile.get_hospital_id() or -1
    hospital_pk = req.get("hospital", current_user_hospital_id)

    su = request.user.is_superuser or request.user.doctorprofile.all_hospitals_users_control

    if hospital_pk == -1:
        hospital_pk = None

    if hospital_pk != current_user_hospital_id and not su:
        return JsonResponse({"ok": False})

    can_edit = su or request.user.doctorprofile.has_group("Создание и редактирование пользователей")

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
            "types": [*[{"pk": str(x[0]), "title": x[1]} for x in Podrazdeleniya.TYPES if x[0] not in [8, 12, 16] and en.get(x[0], True)], *more_types],
        }
        if hasattr(request, "plain_response") and request.plain_response:
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
                        department.oid = row.get("oid", "")
                        department.save()
                        ok = True
            elif data_type == "insert":
                ok = False
                for row in rows:
                    title = row["title"].strip()
                    if len(title) > 0:
                        department = Podrazdeleniya(title=title, p_type=int(row["type"]), hospital_id=hospital_pk, oid=row.get("oid", ""))
                        department.save()
                        ok = True
        finally:
            return JsonResponse({"ok": ok, "message": message})
    return JsonResponse(0)


@login_required
def otds(request):
    req = json.loads(request.body)
    return JsonResponse(
        {
            "rows": [
                *([] if req.get("withoutDefault", False) else [{"id": -1, "label": "Все отделения"}]),
                *[
                    {"id": x.pk, "label": x.title}
                    for x in Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.DEPARTMENT)
                    .filter(Q(hospital__isnull=True) | Q(hospital=request.user.doctorprofile.hospital))
                    .order_by("title")
                ],
            ]
        }
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
    k = f"view:bases:{request.user.pk}"
    disabled_fin_source = (
        [i.fin_source.pk for i in DisableIstochnikiFinansirovaniya.objects.filter(hospital_id=request.user.doctorprofile.hospital_id)] if request.user.is_authenticated else []
    )
    user_disabled_fin_source = (
        [x for x in users.DoctorProfile.objects.values_list("disabled_fin_source", flat=True).filter(pk=request.user.doctorprofile.pk) if x is not None]
        if request.user.is_authenticated
        else []
    )
    disabled_fin_source.extend(user_disabled_fin_source)
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
                .prefetch_related(
                    Prefetch("istochnikifinansirovaniya_set", directions.IstochnikiFinansirovaniya.objects.filter(hide=False).exclude(pk__in=disabled_fin_source).order_by("-order_weight"))
                )
                .order_by("-order_weight")
            ]
        }

        cache.set(k, ret, 100)
    if hasattr(request, "plain_response") and request.plain_response:
        return ret
    return JsonResponse(ret)


@ensure_csrf_cookie
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
        "loading": False,
    }
    if ret["auth"]:
        request.user.doctorprofile.mark_as_online()

        def fill_user_data():
            doctorprofile = (
                users.DoctorProfile.objects.prefetch_related(
                    Prefetch(
                        "restricted_to_direct",
                        queryset=DResearches.objects.only("pk"),
                    ),
                    Prefetch(
                        "users_services",
                        queryset=DResearches.objects.only("pk"),
                    ),
                )
                .select_related("podrazdeleniye")
                .get(user_id=user.pk)
            )

            ret["fio"] = doctorprofile.get_full_fio()
            ret["shortFio"] = doctorprofile.get_fio(with_space=False)
            ret["hasTOTP"] = doctorprofile.totp_secret is not None
            ret["email"] = doctorprofile.email or ""
            ret["doc_pk"] = doctorprofile.pk
            ret["rmis_location"] = doctorprofile.rmis_location
            ret["max_age_patient_registration"] = doctorprofile.max_age_patient_registration
            ret["rmis_login"] = doctorprofile.rmis_login
            ret["rmis_password"] = doctorprofile.rmis_password
            ret["department"] = {"pk": doctorprofile.podrazdeleniye_id, "title": doctorprofile.podrazdeleniye.title}
            ret["restricted"] = [x.pk for x in doctorprofile.restricted_to_direct.all()]
            ret["user_services"] = [x.pk for x in doctorprofile.users_services.all() if x not in ret["restricted"]]
            ret["hospital"] = doctorprofile.get_hospital_id()
            ret["hospital_title"] = doctorprofile.get_hospital_title()
            ret["all_hospitals_users_control"] = doctorprofile.all_hospitals_users_control
            ret["specialities"] = [] if not doctorprofile.specialities else [doctorprofile.specialities.title]
            ret["groups"] = list(user.groups.values_list("name", flat=True))
            if SYSTEM_AS_VI:
                for i in range(len(ret["groups"])):
                    if ret["groups"][i] == "Картотека L2":
                        ret["groups"][i] = "Картотека"
            if user.is_superuser:
                ret["groups"].append("Admin")
            ret["eds_allowed_sign"] = doctorprofile.get_eds_allowed_sign() if ret["modules"].get("l2_eds") else []
            ret["can_edit_all_department"] = doctorprofile.all_hospitals_users_control

            try:
                connections.close_all()
            except Exception as e:
                print(f"Error closing connections {e}")  # noqa: T001

        def fill_settings():
            ret["su"] = user.is_superuser
            ret["username"] = user.username

            ret["modules"] = SettingManager.l2_modules()
            ret["rmis_enabled"] = SettingManager.get("rmis_enabled", default="false", default_type="b")
            ret["directions_params_org_form_default_pk"] = SettingManager.get("directions_params_org_form_default_pk", default="", default_type="s")
            ret["priceCategories"] = [{"pk": -1, "title": " – Не выбрано"}, *[{"pk": x.pk, "title": x.title} for x in PriceCategory.objects.filter(hide=False).order_by("title")]]

            en = SettingManager.en()
            ret["extended_departments"] = {}

            st_base = ResearchSite.objects.filter(hide=False).order_by("order", "title")

            sites_by_types = {}
            for s in st_base:
                if s.site_type not in sites_by_types:
                    sites_by_types[s.site_type] = []
                sites_by_types[s.site_type].append({"pk": s.pk, "title": s.title, "type": s.site_type, "extended": True, "e": s.site_type + 4})

            # Тут 13 – заявления, 11 – формы, 7 – формы минус 4
            if 13 in en and 11 in en:
                if 7 not in sites_by_types:
                    sites_by_types[7] = []
                if SettingManager.get("l2_applications"):
                    sites_by_types[7].append(
                        {
                            "pk": -13,
                            "title": "Заявления",
                            "type": 7,
                            "extended": True,
                            "e": 11,
                        }
                    )

            for e in en:
                if e < 4 or not en[e] or e == 13:
                    continue

                t = e - 4
                has_def = DResearches.objects.filter(hide=False, site_type__isnull=True, **DResearches.filter_type(e)).exists()

                if has_def and e != 12:
                    d = [{"pk": None, "title": "Общие", "type": t, "extended": True}]
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

    if hasattr(request, "plain_response") and request.plain_response:
        return ret
    return JsonResponse(ret)


def get_menu(request):
    data = menu(request)

    return JsonResponse(
        {
            "buttons": data["mainmenu"],
            "version": data["version"],
            "region": SettingManager.get("region", default="38", default_type="s"),
        }
    )


@login_required
def directive_from(request):
    data = []
    hospital = request.user.doctorprofile.hospital
    for dep in (
        Podrazdeleniya.objects.filter(p_type__in=(Podrazdeleniya.DEPARTMENT, Podrazdeleniya.HOSP, Podrazdeleniya.PARACLINIC, Podrazdeleniya.CASE), hospital__in=(hospital, None))
        .prefetch_related(
            Prefetch(
                "doctorprofile_set",
                queryset=(
                    users.DoctorProfile.objects.filter(user__groups__name__in=["Лечащий врач", "Врач параклиники"])
                    .distinct("fio", "pk")
                    .filter(Q(hospital=hospital) | Q(hospital__isnull=True))
                    .order_by("fio")
                ),
            )
        )
        .order_by("title")
        .only("pk", "title")
    ):
        d = {
            "pk": dep.pk,
            "title": dep.title,
            "docs": [{"pk": x.pk, "fio": x.get_full_fio()} for x in dep.doctorprofile_set.all()],
        }
        data.append(d)

    result = {"data": data}
    if hasattr(request, "plain_response") and request.plain_response:
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
        purpose=VisitPurpose.objects.filter(pk=rd["visit"]).first(),
        result=ResultOfTreatment.objects.filter(pk=rd["result"]).first(),
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
        .order_by("pk")
    ):
        if not row.invalid_ticket:
            n += 1
        response["data"].append(
            {
                "pk": row.pk,
                "n": n if not row.invalid_ticket else "",
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
    rt = SettingManager.get("visit_reset_time_min", default="20.0", default_type="f") * 60
    return cdid, ctime, ctp, rt


def mkb10(request):
    kw = request.GET.get("keyword", "").split(" ")[0]
    data = []
    for d in directions.Diagnoses.objects.filter(d_type="mkb10.4", code__istartswith=kw, hide=False).order_by("code").distinct()[:11]:
        data.append({"pk": d.pk, "code": d.code, "title": d.title})
    return JsonResponse({"data": data})


def mkb10_dict(request, raw_response=False):
    q = (request.GET.get("query", "") or "").strip()
    if not q:
        if raw_response:
            return []
        return JsonResponse({"data": []})

    if q == "-":
        empty = {"code": "-", "title": "", "id": "-"}
        if raw_response:
            return [empty]
        return JsonResponse({"data": [empty]})

    d = request.GET.get("dictionary", "mkb10.4")
    parts = q.split(" ", 1)
    code = "-1"
    diag_title = "-1"
    if len(parts) == 2:
        if re.search(r"^[a-zA-Z0-9]", parts[0]):
            code = parts[0]
            diag_title = f"{parts[1]}"
        else:
            diag_title = f"{parts[0]} {parts[1]}"
    else:
        if re.search(r"^[a-zA-Z0-9]", parts[0]):
            code = parts[0]
        else:
            diag_title = parts[0]

    if diag_title != "-1":
        diag_title = f"{diag_title}."
    if d != "mkb10.combined":
        diag_query = get_diagnoses(d_type=d, diag_title=f"{diag_title}", diag_mkb=code)
    else:
        diag_query = get_diagnoses(d_type="mkb10.5", diag_title=f"{diag_title}", diag_mkb=code, limit=50)
        diag_query.extend(get_diagnoses(d_type="mkb10.6", diag_title=f"{diag_title}", diag_mkb=code, limit=50))

    data = []
    for d in diag_query:
        data.append({"code": d.code, "title": d.title, "id": d.nsi_id})
    if raw_response:
        return data
    return JsonResponse({"data": data})


def companies_find(request):
    q = (request.GET.get("query", "") or "").strip()
    type_company = (request.GET.get("subType", "") or "").strip()
    if type_company == "Заказчик" or type_company == "Внешний исполнитель":
        companies_data = Hospitals.search_hospital(q)
    else:
        companies_data = Company.search_company(q)
    return JsonResponse({"data": companies_data})


def company_departments_find(request):
    request_data = json.loads(request.body)
    company_departments = CompanyDepartment.search_departments(request_data["company_db"])
    return JsonResponse({"data": company_departments})


@login_required
def search_dicom(request):
    request_data = json.loads(request.body)
    pk = request_data.get("pk")
    link_study = search_dicom_study(int(pk))
    return JsonResponse({"url": link_study})


def doctorprofile_search(request):
    q = request.GET["query"].strip()
    if not q:
        return JsonResponse({"data": []})

    q = q.split()
    sign_org = request.GET.get("signOrg", "")
    if sign_org == "true":
        d_qs = users.DoctorProfile.objects.filter(hospital=request.user.doctorprofile.get_hospital(), family__istartswith=q[0], user__groups__name__in=["ЭЦП Медицинской организации"])
    else:
        d_qs = users.DoctorProfile.objects.filter(hospital=request.user.doctorprofile.get_hospital(), family__istartswith=q[0])
    if len(q) > 1:
        d_qs = d_qs.filter(name__istartswith=q[1])

    if len(q) > 2:
        d_qs = d_qs.filter(patronymic__istartswith=q[2])

    data = []

    d: users.DoctorProfile
    for d in d_qs.order_by("fio")[:15]:
        data.append(
            {
                "id": d.pk,
                "fio": str(d),
                "department": d.podrazdeleniye.title if d.podrazdeleniye else "",
                **d.dict_data,
            }
        )

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
    for d in directions.Diagnoses.objects.filter(code__istartswith=kw, d_type="vc", hide=False).order_by("code")[:11]:
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
    dpk = int(request.POST["directionId"])
    content = request.POST["content"]
    date = try_strptime(request.POST["date"])
    doc_f = request.POST["doc"].lower()
    if dpk >= 4600000000000:
        dpk -= 4600000000000
        dpk //= 10
    ds = directions.Napravleniya.objects.filter(pk=dpk)
    if ds.exists():
        d = ds[0]
        iss = directions.Issledovaniya.objects.filter(napravleniye=d, research__code="A06.09.006")
        if iss.exists():
            i = iss[0]
            doc = None
            gi = None
            for u in users.DoctorProfile.objects.filter(podrazdeleniye=i.research.podrazdeleniye):
                if doc_f in u.get_fio().lower() or (not doc and u.has_group("Врач параклиники")):
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
                    if i.napravleniye:
                        i.napravleniye.qr_check_token = None
                        i.napravleniye.save(update_fields=["qr_check_token"])
                        i.napravleniye.post_confirmation()
                    i.save()

                if not i.napravleniye.visit_who_mark or not i.napravleniye.visit_date:
                    i.napravleniye.visit_who_mark = doc
                    i.napravleniye.visit_date = date
                    i.napravleniye.save()
            if i.napravleniye:
                i.napravleniye.sync_confirmed_fields()
    slog.Log(key=dpk, type=13, body=json.dumps({"content": content, "doc_f": doc_f}), user=None).save()
    return JsonResponse({"ok": ok})


def search_template(request):
    result = []
    q = request.GET.get("q", "")
    if q != "":
        for r in users.AssignmentTemplates.objects.filter(title__istartswith=q, global_template=False).order_by("title")[:10]:
            result.append({"pk": r.pk, "title": r.title, "researches": [x.research.pk for x in users.AssignmentResearches.objects.filter(template=r, research__hide=False)]})
    return JsonResponse({"result": result, "q": q})


def load_templates(request):
    result = []
    t = request.GET.get("type", "1")
    for r in users.AssignmentTemplates.objects.filter(global_template=t == "1").order_by("title"):
        result.append({"pk": r.pk, "title": r.title, "researches": [x.research.pk for x in users.AssignmentResearches.objects.filter(template=r, research__hide=False)]})
    return JsonResponse({"result": result})


def get_template(request):
    title = ""
    researches = []
    global_template = False
    pk = request.GET.get("pk")
    department = None
    departments = []
    departments_paraclinic = []
    site_types = {}
    show_in_research_picker = False
    show_type = None
    site_type = None
    if pk:
        t: users.AssignmentTemplates = users.AssignmentTemplates.objects.get(pk=pk)
        title = t.title
        researches = [x.research_id for x in users.AssignmentResearches.objects.filter(template=t, research__hide=False)]
        global_template = t.global_template
        show_in_research_picker = t.show_in_research_picker
        show_type = t.get_show_type()
        site_type = t.site_type_id
        department = t.podrazdeleniye_id

    departments = [{"id": x["id"], "label": x["title"]} for x in Podrazdeleniya.objects.filter(hide=False, p_type=Podrazdeleniya.LABORATORY).values("id", "title")]
    departments_paraclinic = [{"id": x["id"], "label": x["title"]} for x in Podrazdeleniya.objects.filter(hide=False, p_type=Podrazdeleniya.PARACLINIC).values("id", "title")]

    for st in users.AssignmentTemplates.SHOW_TYPES_SITE_TYPES_TYPE:
        site_types[st] = [
            {"id": None, "label": "Общие"},
            *[
                {"id": x["id"], "label": x["title"]}
                for x in ResearchSite.objects.filter(site_type=users.AssignmentTemplates.SHOW_TYPES_SITE_TYPES_TYPE[st], hide=False).order_by("order", "title").values("id", "title")
            ],
        ]

    return JsonResponse(
        {
            "title": title,
            "researches": researches,
            "global_template": global_template,
            "department": department,
            "departments": departments,
            "departmentsParaclinic": departments_paraclinic,
            "siteTypes": site_types,
            "showInResearchPicker": show_in_research_picker,
            "type": show_type,
            "siteType": site_type,
        }
    )


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
            elif users.AssignmentTemplates.objects.filter(pk=pk).exists():
                t = users.AssignmentTemplates.objects.get(pk=pk)
                t.title = title
                t.global_template = global_template
                t.save()
            if t:
                t.show_in_research_picker = bool(request_data.get("showInResearchPicker"))
                tp = request_data.get("type")
                t.podrazdeleniye_id = request_data.get("department") if tp in ("lab", "paraclinic") else None
                t.is_paraclinic = tp == "paraclinic"
                t.is_doc_refferal = tp == "consult"
                t.is_treatment = tp == "treatment"
                t.is_stom = tp == "stom"
                t.is_hospital = tp == "hospital"
                t.is_microbiology = tp == "microbiology"
                t.is_citology = tp == "citology"
                t.is_gistology = tp == "gistology"
                t.site_type_id = request_data.get("siteType") if tp in users.AssignmentTemplates.SHOW_TYPES_SITE_TYPES_TYPE else None
                t.save()
                users.AssignmentResearches.objects.filter(template=t).exclude(research__pk__in=researches).delete()
                to_add = [x for x in researches if not users.AssignmentResearches.objects.filter(template=t, research__pk=x).exists()]
                for ta in to_add:
                    if DResearches.objects.filter(pk=ta).exists():
                        users.AssignmentResearches(template=t, research=DResearches.objects.get(pk=ta)).save()
                response["ok"] = True
    return JsonResponse(response)


def modules_view(request):
    return JsonResponse({"l2_cards": SettingManager.get("l2_cards_module", default="false", default_type="b")})


def autocomplete(request):
    t = request.GET.get("type")
    v = request.GET.get("value", "")
    limit = int(request.GET.get("limit", 10))
    data = []
    if v != "" and limit > 0:
        if t == "harmful":
            p = Card.objects.filter(harmful_factor__istartswith=v).distinct("harmful_factor")[:limit]
            if p.exists():
                data = [x.harmful_factor for x in p]
        elif t == "fias":
            data = fias.suggest(v)
        elif t == "fias-extended":
            data = fias.suggest(v, count=limit, detalized=True)
        elif t == "name":
            p = Individual.objects.filter(name__istartswith=v).distinct("name")[:limit]
            if p.exists():
                data = [x.name for x in p]
        elif t == "family":
            p = Individual.objects.filter(family__istartswith=v).distinct("family")[:limit]
            if p.exists():
                data = [x.family for x in p]
        elif t == "patronymic":
            p = Individual.objects.filter(patronymic__istartswith=v).distinct("patronymic")[:limit]
            if p.exists():
                data = [x.patronymic for x in p]
        elif t == "work_place":
            p = Card.objects.filter(work_place__istartswith=v).distinct("work_place")[:limit]
            if p.exists():
                data = [x.work_place for x in p]
        elif t == "main_diagnosis":
            p = Card.objects.filter(main_diagnosis__istartswith=v).distinct("main_diagnosis")[:limit]
            if p.exists():
                data = [x.main_diagnosis for x in p]
        elif t == "work_position":
            p = Card.objects.filter(work_position__istartswith=v).distinct("work_position")[:limit]
            if p.exists():
                data = [x.work_position for x in p]
        elif t == "work_department":
            p = Card.objects.filter(work_department__istartswith=v).distinct("work_department")[:limit]
            if p.exists():
                data = [x.work_department for x in p]
        elif "who_give:" in t:
            tpk = t.split(":")[1]
            p = Document.objects.filter(document_type__pk=tpk, who_give__istartswith=v).distinct("who_give")[:limit]
            if p.exists():
                data = [x.who_give for x in p]
        elif t == "fsli":
            if v == "HGB":
                p = FsliRefbookTest.objects.filter(
                    Q(code_fsli__startswith=v) | Q(title__icontains=v) | Q(english_title__icontains=v) | Q(short_title__icontains=v) | Q(synonym__istartswith=v) | Q(synonym="Hb")
                )
            else:
                p = FsliRefbookTest.objects.filter(
                    Q(code_fsli__startswith=v) | Q(title__icontains=v) | Q(english_title__icontains=v) | Q(short_title__icontains=v) | Q(synonym__istartswith=v)
                )

            p = p.filter(active=True).distinct("code_fsli").order_by("code_fsli", "ordering")[:limit]
            if p.exists():
                data = [{"code_fsli": x.code_fsli, "short_title": x.short_title, "title": x.title, "sample": x.sample, "synonym": x.synonym, "nmu": x.code_nmu} for x in p]
        elif t == "drugs":
            data = [
                {
                    "title": str(x),
                    "pk": x.pk,
                }
                for x in Drugs.objects.filter(Q(mnn__istartswith=v) | Q(trade_name__istartswith=v)).order_by("mnn", "trade_name").distinct("mnn", "trade_name")[:limit]
            ]
    return JsonResponse({"data": data})


def laborants(request):
    data = []
    if SettingManager.l2("results_laborants"):
        data = [{"pk": "-1", "fio": "Не выбрано"}]
        for d in users.DoctorProfile.objects.filter(user__groups__name="Лаборант", podrazdeleniye__p_type=users.Podrazdeleniya.LABORATORY).order_by("fio"):
            data.append({"pk": str(d.pk), "fio": d.get_full_fio()})
    return JsonResponse({"data": data, "doc": request.user.doctorprofile.has_group("Врач-лаборант")})


@login_required
def load_docprofile_by_group(request):
    request_data = json.loads(request.body)
    if request_data["group"] == "*":
        users_data = users_all(request.user.doctorprofile.get_hospital_id())
    else:
        users_data = users_by_group(request_data["group"], request.user.doctorprofile.get_hospital_id())
    users_grouped = {}
    position = request_data.get("position") or None
    positions_data = []
    control_position = False
    if position and len(position) > 0:
        control_position = True
        for p_title in position:
            positions = users.Position.objects.values_list("id", flat=True).filter(title__icontains=p_title)
            for k in positions:
                if k not in positions_data:
                    positions_data.append(k)
    for row in users_data:
        if control_position and row[5] not in positions_data:
            continue
        if row[2] not in users_grouped:
            users_grouped[row[2]] = {"id": f"{row[2]}", "label": row[4] or row[3], "children": []}
        users_grouped[row[2]]["children"].append({"id": str(row[0]), "label": row[1], "podr": row[4] or row[3]})

    return JsonResponse({"users": list(users_grouped.values())})


@login_required
@group_required("Создание и редактирование пользователей")
def users_view(request):
    request_data = json.loads(request.body)
    user_hospital_pk = request.user.doctorprofile.get_hospital_id()
    hospital_pk = request_data.get("selected_hospital", user_hospital_pk)

    can_edit = request.user.is_superuser or request.user.doctorprofile.all_hospitals_users_control or hospital_pk == user_hospital_pk

    data = []

    if can_edit:
        podr = Podrazdeleniya.objects.filter(Q(hospital_id=hospital_pk) | Q(hospital__isnull=True)).exclude(p_type=Podrazdeleniya.HIDDEN, hospital__isnull=True).order_by("title")
        for x in podr:
            otd = {"pk": x.pk, "title": x.title, "users": []}
            docs = users.DoctorProfile.objects.filter(podrazdeleniye=x, hospital_id=hospital_pk).order_by("fio")
            if not request.user.is_superuser:
                docs = docs.filter(user__is_superuser=False)
            for y in docs:
                otd["users"].append({"pk": y.pk, "fio": y.get_fio(), "username": y.user.username})
            data.append(otd)

    spec = users.Speciality.objects.filter(hide=False).order_by("title")
    spec_data = [{"id": -1, "label": "Не выбрано"}, *[{"id": s.pk, "label": f"{s.n3_id} - {s.title}"} for s in spec]]

    positions_qs = users.Position.objects.filter(hide=False).order_by("title")
    positions = [{"id": -1, "label": "Не выбрано"}, *[{"id": s.pk, "label": f"{s.n3_id} - {s.title}"} for s in positions_qs]]

    distrits_qs = District.objects.all().order_by("title")
    districts = [{"pk": -1, "title": "Не выбрано"}, *[{"pk": s.pk, "title": s.title} for s in distrits_qs]]

    return JsonResponse({"departments": data, "specialities": spec_data, "positions": positions, "districts": districts})


@login_required
@group_required("Создание и редактирование пользователей")
def user_view(request):
    request_data = json.loads(request.body)
    pk = request_data["pk"]
    resource_researches = []
    if pk == -1:
        data = {
            "family": "",
            "name": "",
            "patronymic": "",
            "username": "",
            "department": "",
            "email": "",
            "groups": [],
            "restricted_to_direct": [],
            "users_services": [],
            "groups_list": [{"pk": x.pk, "title": x.name} for x in Group.objects.all()],
            "rooms": [],
            "rooms_list": [{"id": x.pk, "label": x.title} for x in Room.objects.all()],
            "password": "",
            "rmis_location": "",
            "rmis_login": "",
            "rmis_password": "",
            "rmis_resource_id": "",
            "doc_pk": -1,
            "max_age_patient_registration": -1,
            "doc_code": -1,
            "rmis_employee_id": "",
            "rmis_service_id_time_table": "",
            "snils": "",
            "available_quotas_time": "",
            "cabinet": "",
            "position": -1,
            "district": -1,
            "sendPassword": False,
            "external_access": False,
            "date_stop_external_access": None,
            "date_extract_employee": None,
            "date_stop_certificate": None,
            "resource_schedule": resource_researches,
            "notControlAnketa": False,
            "additionalInfo": "{}",
        }
    else:
        doc: users.DoctorProfile = users.DoctorProfile.objects.get(pk=pk)
        fio_parts = doc.get_fio_parts()
        doc_schedule_obj = ScheduleResource.objects.filter(executor=doc)
        resource_researches_temp = {}
        doc_resource_pk_title = {k.pk: k.title for k in doc_schedule_obj}
        doc_schedule = [i.pk for i in doc_schedule_obj]
        if doc_schedule_obj:
            researches_pks = get_resource_researches(tuple(doc_schedule))
            for i in researches_pks:
                if not resource_researches_temp.get(i.scheduleresource_id, None):
                    resource_researches_temp[i.scheduleresource_id] = [i.researches_id]
                else:
                    temp_result = resource_researches_temp[i.scheduleresource_id]
                    temp_result.append(i.researches_id)
                    resource_researches_temp[i.scheduleresource_id] = temp_result.copy()
        resource_researches = [{"pk": k, "researches": v, "title": doc_resource_pk_title[k]} for k, v in resource_researches_temp.items()]
        department_doctors = users.DoctorProfile.objects.filter(podrazdeleniye_id=doc.podrazdeleniye_id)
        data = {
            "family": fio_parts[0],
            "name": fio_parts[1],
            "patronymic": fio_parts[2],
            "username": doc.user.username,
            "department": doc.podrazdeleniye_id,
            "email": doc.email or "",
            "groups": [x.pk for x in doc.user.groups.all()],
            "restricted_to_direct": [x.pk for x in doc.restricted_to_direct.all()],
            "users_services": [x.pk for x in doc.users_services.all()],
            "groups_list": [{"pk": x.pk, "title": x.name} for x in Group.objects.all()],
            "rooms": [x.pk for x in doc.room_access.all()],
            "rooms_list": [{"id": x.pk, "label": x.title} for x in Room.objects.all()],
            "password": "",
            "rmis_location": doc.rmis_location or "",
            "max_age_patient_registration": doc.max_age_patient_registration or -1,
            "rmis_login": doc.rmis_login or "",
            "rmis_resource_id": doc.rmis_resource_id or "",
            "rmis_password": "",
            "doc_pk": doc.user.pk,
            "personal_code": doc.personal_code,
            "speciality": doc.specialities_id or -1,
            "rmis_employee_id": doc.rmis_employee_id,
            "rmis_service_id_time_table": doc.rmis_service_id_time_table,
            "snils": doc.snils,
            "available_quotas_time": doc.available_quotas_time,
            "cabinet": doc.cabinet,
            "position": doc.position_id or -1,
            "district": doc.district_group_id or -1,
            "sendPassword": False,
            "external_access": doc.external_access,
            "date_stop_external_access": doc.date_stop_external_access,
            "date_stop_certificate": doc.date_stop_certificate,
            "date_extract_employee": doc.date_extract_employee,
            "resource_schedule": resource_researches,
            "notControlAnketa": doc.not_control_anketa,
            "replace_doctor_cda": doc.replace_doctor_cda_id if doc.replace_doctor_cda_id else -1,
            "department_doctors": [{"id": x.pk, "label": f"{x.get_fio()}"} for x in department_doctors],
            "additionalInfo": doc.additional_info,
        }

    return JsonResponse({"user": data})


@login_required
@group_required("Создание и редактирование пользователей")
def user_save_view(request):
    request_data = json.loads(request.body)
    group_analyzer = request_data["groupsAnalyzer"]
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
    snils = ud.get("snils").strip() or ""
    available_quotas_time = ud.get("available_quotas_time").strip() or ""
    cabinet = (ud.get("cabinet") or "").strip()
    email = ud.get("email").strip() or None
    position = ud.get("position", -1)
    district = ud.get("district", -1)
    max_age_patient_registration = ud.get("max_age_patient_registration", -1)
    send_password = ud.get("sendPassword", False)
    external_access = ud.get("external_access", False)
    not_control_anketa = ud.get("notControlAnketa", False)
    date_stop_external_access = ud.get("date_stop_external_access")
    additional_info = ud.get("additionalInfo", "{}")

    if date_stop_external_access == "":
        date_stop_external_access = None
    date_extract_employee = ud.get("date_extract_employee")
    if date_extract_employee == "":
        date_extract_employee = None
    date_stop_certificate = ud.get("date_stop_certificate")
    replace_doctor_cda = ud.get("replace_doctor_cda")
    if replace_doctor_cda == -1:
        replace_doctor_cda = None
    if date_stop_certificate == "":
        date_stop_certificate = None

    if position == -1:
        position = None
    if district == -1:
        district = None
    user_hospital_pk = request.user.doctorprofile.get_hospital_id()
    hospital_pk = request_data.get("hospital_pk", user_hospital_pk)

    can_edit = request.user.is_superuser or request.user.doctorprofile.all_hospitals_users_control or hospital_pk == user_hospital_pk

    if not can_edit:
        return JsonResponse({"ok": False})

    npk = pk
    if pk == -1:
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(username)
            user.is_active = True
            user.save()
            doc = users.DoctorProfile(user=user, fio=f'{ud["family"]} {ud["name"]} {ud["patronymic"]}')
            doc.save()
            doc.get_fio_parts()
            npk = doc.pk
        else:
            ok = False
            message = "Имя пользователя уже занято"
            doc = None
    else:
        doc = users.DoctorProfile.objects.get(pk=pk)
    if pk and doc and (not doc.user.is_superuser or request.user.is_superuser):
        if ud["password"] != "":
            doc.user.set_password(ud["password"])
            doc.user.save()
        if pk != -1 and doc.user.username != ud["username"]:
            if not User.objects.filter(username=username).exists():
                doc.user.username = username
                doc.user.save()
            else:
                ok = False
                message = "Имя пользователя уже занято"
        if email:
            email = email.strip()
            try:
                if email:
                    validate_email(email)
            except:
                ok = False
                message = f"Email {email} некорректный"
            if users.DoctorProfile.objects.filter(email__iexact=email).exclude(pk=pk).exists():
                ok = False
                message = f"Email {email} уже занят"

        if ok:
            doc.user.groups.clear()
            for g in ud["groups"]:
                group = Group.objects.get(pk=g)
                doc.user.groups.add(group)
            doc.room_access.clear()
            for r in ud["rooms"]:
                room = Room.objects.get(pk=r)
                doc.room_access.add(room)

            ManageDoctorProfileAnalyzer.objects.filter(doctor_profile_id=doc.pk).delete()
            for g in group_analyzer:
                analyzer = Analyzer.objects.get(pk=g)
                ManageDoctorProfileAnalyzer(analyzer_id=analyzer.pk, doctor_profile_id=doc.pk).save()
            doc.user.save()

            doc.restricted_to_direct.clear()
            for r in ud["restricted_to_direct"]:
                doc.restricted_to_direct.add(DResearches.objects.get(pk=r))

            doc.users_services.clear()
            for r in ud["users_services"]:
                doc.users_services.add(DResearches.objects.get(pk=r))

            spec = ud.get("speciality", None)
            if spec == -1:
                spec = None
            doc.podrazdeleniye_id = ud["department"]
            doc.specialities_id = spec
            doc.family = ud["family"]
            doc.name = ud["name"]
            doc.patronymic = ud["patronymic"]
            doc.fio = f'{ud["family"]} {ud["name"]} {ud["patronymic"]}'
            doc.rmis_location = rmis_location
            doc.max_age_patient_registration = max_age_patient_registration
            doc.rmis_employee_id = rmis_employee_id
            doc.rmis_service_id_time_table = rmis_service_id_time_table
            doc.personal_code = personal_code
            doc.rmis_resource_id = rmis_resource_id
            doc.hospital_id = hospital_pk
            doc.snils = snils
            doc.available_quotas_time = available_quotas_time
            doc.cabinet = cabinet
            doc.email = email
            doc.position_id = position
            doc.district_group_id = district
            doc.external_access = external_access
            doc.not_control_anketa = not_control_anketa
            doc.date_stop_external_access = date_stop_external_access
            doc.date_extract_employee = date_extract_employee
            doc.date_stop_certificate = date_stop_certificate
            doc.replace_doctor_cda_id = replace_doctor_cda
            doc.additional_info = additional_info
            if rmis_login:
                doc.rmis_login = rmis_login
                if rmis_password:
                    doc.rmis_password = rmis_password
            else:
                doc.rmis_login = None
                doc.rmis_password = None
            doc.save()
            if doc.email and send_password:
                doc.reset_password()

    data_doc_profile = {key: value for key, value in doc.dict_data.items()}
    data_doc_profile["id"] = doc.pk
    Log(key=doc.pk, type=120004, body=json.dumps(data_doc_profile), user=request.user.doctorprofile).save()
    return JsonResponse({"ok": ok, "npk": npk, "message": message})


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


@login_required
def user_location(request):
    request_data = json.loads(request.body)
    date = request_data["date"]
    d = {}
    rl = request.user.doctorprofile.rmis_location
    if rl and SettingManager.get("l2_rmis_queue", default="false", default_type="b"):
        if rl == 1337 and request.user.is_superuser:
            from rmis_integration.client import Patients

            d = Patients.get_fake_reserves()
        else:
            d = get_reserves_ecp(date, rl)

        d = list(map(lambda x: {**x, "status": slot_status(x)}, d))
    return JsonResponse({"data": d})


@login_required
def user_get_reserve(request):
    request_data = json.loads(request.body)
    pk = request_data["pk"]
    patient_uid = request_data["patient"]
    rl = request.user.doctorprofile.rmis_location
    if rl:
        if rl == 1337 and request.user.is_superuser:
            from rmis_integration.client import Patients

            d = Patients.get_fake_slot()
        else:
            d = get_slot_ecp(patient_uid, pk)
        n = directions.Napravleniya.objects.filter(rmis_slot_id=pk).first()
        d["direction"] = n.pk if n else None
        ds = directions.Issledovaniya.objects.filter(napravleniye=n, napravleniye__isnull=False).first()
        d["direction_service"] = ds.research_id if ds else -1
        if d:
            return JsonResponse({**d, "datetime": d["datetime"], "patient_uid": patient_uid, "pk": int(str(pk)[1:]) if str(pk).isdigit() else str(pk)})
    return JsonResponse({})


@login_required
def user_fill_slot(request):
    slot = json.loads(request.body).get("slot", {})
    slot_data = slot.get("data", {})
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


@csrf_exempt
def reader_status(request):
    data = json.loads(request.body)
    reader_id = data.get("readerId", "null")
    data = json.loads(cache.get(f"reader-status:{reader_id}", '{"status": "none"}'))
    return JsonResponse({"status": data.get("status"), "polis": data.get("polis"), "fio": data.get("fio"), "details": data.get("details", {})})


@csrf_exempt
def reader_status_update(request):
    data = json.loads(request.body)
    reader_id = data.get("readerId")

    if not reader_id:
        return JsonResponse({"ok": True})

    status = data["status"]

    if status == "inserted":
        polis = data["polis"]
        fio = data["fio"]
        cache.set(f"reader-status:{reader_id}", json.dumps({"status": "inserted", "polis": polis, "fio": fio, "details": data["details"]}), 10)
    else:
        cache.set(f"reader-status:{reader_id}", '{"status": "wait"}', 10)

    return JsonResponse({"ok": True})


def actual_districts(request):
    data = json.loads(request.body)
    card_pk = data.get("card_pk")
    rows = District.objects.all().order_by("-sort_weight", "-id").values("pk", "title", "is_ginekolog")
    rows = [{"id": -1, "label": "НЕ ВЫБРАН"}, *[{"id": x["pk"], "label": x["title"] if not x["is_ginekolog"] else "Гинекология: {}".format(x["title"])} for x in rows]]

    users = users_by_group(["Лечащий врач"], request.user.doctorprofile.get_hospital_id())
    users = [{"id": -1, "label": "НЕ ВЫБРАН"}, *[{"id": row[0], "label": row[1]} for row in users]]

    purposes = DoctorCall.PURPOSES
    purposes = [{"id": row[0], "label": row[1]} for row in purposes]

    hospitals = Hospitals.objects.filter(hide=False).order_by("short_title").values("pk", "short_title", "title", "code_tfoms")
    hospitals = [{"id": -1, "label": "НЕ ВЫБРАНО"}, *[{"id": x["pk"], "label": x["short_title"] or x["title"], "code_tfoms": x["code_tfoms"]} for x in hospitals]]

    if card_pk is not None:
        card_hospital_id = -1
        if SettingManager.l2("tfoms") and USE_TFOMS_DISTRICT:
            card = Card.objects.get(pk=data["card_pk"])
            enp = card.individual.get_enp()
            if enp:
                from_tfoms = match_enp(card.individual.get_enp())

                if from_tfoms and from_tfoms.get("unit_code"):
                    card_hospital_id = {x["code_tfoms"]: x["id"] for x in hospitals if x.get("code_tfoms")}.get(from_tfoms["unit_code"]) or -1
    else:
        card_hospital_id = -1

    if card_hospital_id == -1 and len(hospitals) == 2:
        card_hospital_id = hospitals[1]["id"]

    data = {"rows": rows, "docs": users, "purposes": purposes, "hospitals": hospitals, "hospitalId": card_hospital_id}
    return JsonResponse(data)


def hospitals(request):
    data = json.loads(request.body)
    if request.user.is_authenticated and request.user.doctorprofile:
        any_hospital = request.user.doctorprofile.all_hospitals_users_control
    else:
        any_hospital = False
    filters = {}
    if request.user.is_authenticated and request.user.doctorprofile:
        if data.get("filterByUserHospital") and not any_hospital:
            filters["pk"] = request.user.doctorprofile.get_hospital_id()
        if data.get("filterByNeedSendResult"):
            filters["need_send_result"] = True
        rows = Hospitals.objects.filter(hide=False, **filters).order_by("-is_default", "short_title")
        if data.get("filterByNeedSendResult"):
            rows = rows.exclude(pk=request.user.doctorprofile.get_hospital_id())
        rows = rows.values("pk", "short_title", "title", "code_tfoms", "email")
    else:
        rows = []
    default_hospital = []
    strict_mode = data.get("strictMode")
    if not strict_mode and (any_hospital or data.get("filterByNeedSendResult")):
        default_hospital.append(
            {
                "id": -1,
                "label": "Все",
                "code_tfoms": "000000",
            }
        )
    if not strict_mode and any_hospital and not data.get("filterByNeedSendResult"):
        default_hospital.append(
            {
                "id": -2,
                "label": "Не выбрано",
                "code_tfoms": "000001",
            }
        )
    result = {
        "hospitals": [
            *[
                {
                    "id": x["pk"],
                    "label": x["short_title"] or x["title"],
                    "code_tfoms": x["code_tfoms"],
                    "email": x["email"],
                }
                for x in rows
            ],
            *default_hospital,
        ]
    }
    if hasattr(request, "plain_response") and request.plain_response:
        return result
    return JsonResponse(result)


@login_required
def get_hospitals(request):
    hospitals = get_all_hospitals()
    return JsonResponse({"hospitals": hospitals})


def rmis_link(request):
    d = request.user.doctorprofile
    d_pass = urllib.parse.quote(d.rmis_password or "")
    d_login = d.rmis_login or ""
    auth_param = URL_RMIS_AUTH.replace("userlogin", d_login).replace("userpassword", d_pass)
    if d.hospital.rmis_org_id and d.rmis_service_id_time_table and d.rmis_employee_id:
        url_schedule = URL_SCHEDULE.replace("organization_param", d.hospital.rmis_org_id).replace("service_param", d.rmis_service_id_time_table).replace("employee_param", d.rmis_employee_id)
    else:
        url_schedule = None
    return JsonResponse({"auth_param": auth_param, "url_eln": URL_ELN_MADE, "url_schedule": url_schedule})


@login_required
def get_permanent_directory(request):
    request_data = json.loads(request.body)
    oid = request_data.get("oid", "")
    return JsonResponse(NSI.get(oid, {}))


@login_required
@group_required("Конструктор: Настройка скрининга")
def screening_get_directory(request):
    rows = list(ScreeningPlan.objects.all().order_by("sort_weight").values("pk", "age_start_control", "age_end_control", "sex_client", "research_id", "period", "sort_weight", "hide"))
    n = 0
    for r in rows:
        if r["sort_weight"] != n:
            r["sort_weight"] = n
            p = ScreeningPlan.objects.get(pk=r["pk"])
            p.sort_weight = n
            p.save(update_fields=["sort_weight"])
        n += 1
        r["hasChanges"] = False
    return JsonResponse({"rows": rows})


@login_required
@group_required("Конструктор: Настройка скрининга")
def screening_save(request):
    parse_params = {
        "screening": as_model(ScreeningPlan),
        "service": as_model(DResearches),
        "sex": str,
        "ageFrom": int,
        "ageTo": int,
        "period": int,
        "sortWeight": int,
        "hide": bool,
    }

    data = data_parse(request.body, parse_params, {"screening": None, "hide": False})
    screening: Optional[ScreeningPlan] = data[0]
    service: Optional[DResearches] = data[1]
    sex: str = data[2]
    age_from: int = data[3]
    age_to: int = data[4]
    period: int = data[5]
    sort_weight: int = data[6]
    hide: bool = data[7]

    if not service:
        return status_response(False, "Не передана услуга или исследование")

    try:
        if not screening:
            screening = ScreeningPlan.objects.create(research=service, sex_client=sex, age_start_control=age_from, age_end_control=age_to, period=period, sort_weight=sort_weight, hide=hide)
        else:
            screening.research = service
            screening.sex_client = sex
            screening.age_start_control = age_from
            screening.age_end_control = age_to
            screening.period = period
            screening.sort_weight = sort_weight
            screening.hide = hide
            screening.save()
    except IntegrityError:
        return status_response(False, "Такой скрининг уже есть!")

    return status_response(True)


@login_required
def companies(request):
    rows = [{"id": x.pk, "label": x.short_title or x.title} for x in Company.objects.filter(active_status=True).order_by("short_title")]

    return JsonResponse({"rows": rows})


@login_required
def purposes(request):
    rows = non_selected_visible_type(VisitPurpose, for_treeselect=True)
    return JsonResponse({"rows": rows})


@login_required
def result_of_treatment(request):
    rows = non_selected_visible_type(ResultOfTreatment, for_treeselect=True)
    return JsonResponse({"rows": rows})


@login_required
def title_report_filter_stattalon_fields(request):
    has_stattalon_filter = TITLE_REPORT_FILTER_STATTALON_FIELDS
    has_all_fin_source = TITLE_REPORT_FILTER_HAS_ALL_FIN_SOURCE
    return JsonResponse({"hasStattalonFilter": has_stattalon_filter, "allFinSource": has_all_fin_source})


@login_required
def input_templates_add(request):
    data = json.loads(request.body)
    pk = data["pk"]
    value = str(data["value"]).strip()
    value_lower = value.lower()
    doc = request.user.doctorprofile
    if ParaclinicUserInputTemplateField.objects.filter(field_id=pk, doc=doc, value=value).exists():
        t = ParaclinicUserInputTemplateField.objects.filter(field_id=pk, doc=doc, value=value)[0]
        if t.value_lower != value_lower:
            t.value_lower = value_lower
            t.save()
        return JsonResponse({"ok": False})

    t = ParaclinicUserInputTemplateField.objects.create(field_id=pk, doc=doc, value=value, value_lower=value_lower)

    return JsonResponse({"ok": True, "pk": t.pk})


@login_required
def input_templates_get(request):
    data = json.loads(request.body)
    pk = data["pk"]
    doc = request.user.doctorprofile
    rows = [{"pk": x.pk, "value": x.value} for x in ParaclinicUserInputTemplateField.objects.filter(field_id=pk, doc=doc).order_by("pk")]

    return JsonResponse({"rows": rows})


@login_required
def input_templates_delete(request):
    data = json.loads(request.body)
    pk = data["pk"]
    doc = request.user.doctorprofile

    ParaclinicUserInputTemplateField.objects.filter(pk=pk, doc=doc).delete()

    return JsonResponse({"ok": True})


@login_required
def input_templates_suggests(request):
    data = json.loads(request.body)
    pk = data["pk"]
    value = str(data["value"]).strip().lower()
    doc = request.user.doctorprofile
    rows = list(
        ParaclinicUserInputTemplateField.objects.filter(field_id=pk, doc=doc, value_lower__startswith=value)
        .exclude(value_lower=value)
        .order_by("value_lower")
        .values_list("value", flat=True)[:4]
    )

    return JsonResponse({"rows": rows, "value": data["value"]})


@login_required
def construct_menu_data(request):
    groups = [str(x) for x in request.user.groups.all()]
    pages = [
        {"url": "/construct/tubes", "title": "Ёмкости для биоматериала", "access": ["Конструктор: Ёмкости для биоматериала"], "module": None},
        {"url": "/construct/researches", "title": "Лабораторные исследования", "access": ["Конструктор: Лабораторные исследования"], "module": None},
        {"url": "/ui/construct/laboratory", "title": "Лабораторные исследования(н)", "access": ["Конструктор: Лабораторные исследования"], "module": None},
        {
            "url": "/ui/construct/descriptive",
            "title": "Описательные протоколы и консультации",
            "access": ["Конструктор: Параклинические (описательные) исследования"],
            "module": "paraclinic_module",
        },
        {"url": "/construct/directions_group", "title": "Группировка исследований по направлениям", "access": ["Конструктор: Группировка исследований по направлениям"], "module": None},
        {"url": "/construct/uets", "title": "Настройка УЕТов", "access": ["Конструктор: Настройка УЕТов"], "module": None},
        {"url": "/ui/construct/templates", "title": "Настройка шаблонов", "access": ["Конструктор: Настройка шаблонов"], "module": None},
        {"url": "/ui/construct/bacteria", "title": "Бактерии и антибиотики", "access": ["Конструктор: Бактерии и антибиотики"], "module": None},
        {"url": "/ui/construct/dispensary-plan", "title": "Д-учет", "access": ["Конструктор: Д-учет"], "module": None},
        {"url": "/ui/construct/screening", "title": "Настройка скрининга", "access": ["Конструктор: Настройка скрининга"], "module": None},
        {"url": "/ui/construct/org", "title": "Настройка организации", "access": ["Конструктор: Настройка организации"], "module": None},
        {"url": "/ui/construct/employees", "title": "Управление сотрудниками", "access": ["Конструктор: Настройка организации"], "module": None},
        {"url": "/ui/construct/district", "title": "Участки организации", "access": ["Конструктор: Настройка организации"], "module": None},
        {"url": "/ui/construct/price", "title": "Настройка прайсов", "access": ["Конструктор: Настройка организации"], "module": None},
        {"url": "/ui/construct/company", "title": "Настройка компаний", "access": ["Конструктор: Настройка организации"], "module": None},
        {"url": "/ui/construct/harmful-factor", "title": "Факторы вредности", "access": ["Конструктор: Факторы вредности"], "module": None},
        {"url": "/ui/construct/research-sets", "title": "Наборы исследований", "access": ["Конструктор: Настройка организации"], "module": None},
        {"url": "/ui/construct/patient-control-param", "title": "Контролируемые параметры пациентов", "access": ["Конструктор: Контролируемые параметры пациентов"], "module": None},
        {"url": "/ui/construct/route-perform-service", "title": "Маршрут исследований", "access": ["Конструктор: Маршрут исследований"], "module": None},
    ]

    from context_processors.utils import make_menu

    menu = make_menu(pages, groups, request.user.is_superuser)

    return JsonResponse(
        {
            "menu": menu,
        }
    )


@login_required
def organization_data(request):
    request_data = json.loads(request.body)

    hospital: Hospitals = request.user.doctorprofile.get_hospital()

    hospital_pk = request_data.get("hospitalId")
    if hospital_pk is not None and hospital_pk != hospital.pk:
        if not request.user.doctorprofile.has_group("Конструктор: Настройка всех организаций"):
            return status_response(False, "Доступ запрещен")
        hospital = Hospitals.objects.get(pk=hospital_pk)

    org = {
        "pk": hospital.pk,
        "title": hospital.title,
        "shortTitle": hospital.short_title,
        "address": hospital.address,
        "phones": hospital.phones,
        "ogrn": hospital.ogrn,
        "www": hospital.www,
        "email": hospital.email,
        "licenseData": hospital.license_data,
        "currentManager": hospital.current_manager,
        "okpo": hospital.okpo,
    }

    if SettingManager.l2("ftp") and request.user.doctorprofile.has_group("Конструктор: Настройка всех организаций"):
        org["ordersPullFtpServerUrl"] = hospital.orders_pull_by_numbers or ""
        org["ordersPushFtpServerUrl"] = hospital.orders_push_by_numbers or ""
        org["resultPullFtpServerUrl"] = hospital.result_pull_by_numbers or ""
        org["isExternalPerformingOrganization"] = hospital.is_external_performing_organization
        org["strictTubeNumbers"] = hospital.strict_tube_numbers
        org["strictDataOwnership"] = hospital.strict_data_ownership
        org["strictExternalNumbers"] = hospital.strict_external_numbers
        org["hl7SenderApplication"] = hospital.hl7_sender_application
        org["hl7ReceiverAapplication"] = hospital.hl7_receiver_appplication
        org["isAutotransfer"] = hospital.is_auto_transfer_hl7_file

    return JsonResponse({"org": org})


@login_required
@group_required("Конструктор: Настройка организации", "Конструктор: Настройка всех организаций")
def organization_data_update(request):
    parse_params = {
        "title": str,
        "shortTitle": str,
        "address": str,
        "phones": str,
        "ogrn": str,
        "currentManager": str,
        "licenseData": str,
        "www": str,
        "email": str,
        "okpo": str,
        "pk": int,
        "ordersPullFtpServerUrl": str,
        "ordersPushFtpServerUrl": str,
        "isExternalPerformingOrganization": bool,
        "strictTubeNumbers": bool,
        "strictDataOwnership": bool,
        "strictExternalNumbers": bool,
        "resultPullFtpServerUrl": str,
        "hl7SenderApplication": str,
        "hl7ReceiverAapplication": str,
        "isAutotransfer": bool,
    }

    data = data_parse(
        request.body,
        parse_params,
        {
            "screening": None,
            "hide": False,
            "pk": None,
            "ordersPullFtpServerUrl": None,
            "ordersPushFtpServerUrl": None,
            "isExternalPerformingOrganization": False,
            "strictTubeNumbers": False,
            "strictDataOwnership": False,
            "strictExternalNumbers": False,
            "resultPullFtpServerUrl": None,
            "hl7SenderApplication": None,
            "hl7ReceiverAapplication": None,
            "isAutotransfer": False,
        },
    )

    title: str = data[0].strip()
    short_title: str = data[1].strip()
    address: str = data[2].strip()
    phones: str = data[3].strip()
    ogrn: str = data[4].strip()
    current_manager: str = data[5].strip()
    license_data: str = data[6].strip()
    www: str = data[7].strip()
    email: str = data[8].strip()
    okpo: str = data[9].strip()
    hospital_pk: Optional[int] = data[10]
    orders_pull_by_numbers: Optional[str] = data[11] or None
    orders_push_by_numbers: Optional[str] = data[12] or None
    is_external_performing_organization: bool = data[13]
    strict_tube_numbers: bool = data[14]
    strict_data_ownership: bool = data[15]
    strict_external_numbers: bool = data[16]
    result_pull_by_numbers: Optional[str] = data[17] or None
    hl7_sender_application: Optional[str] = data[18] or None
    hl7_receiver_appplication: Optional[str] = data[19] or None
    is_auto_transfer = data[20] if data[20] else False

    if not title:
        return status_response(False, "Название не может быть пустым")

    hospital: Hospitals = request.user.doctorprofile.get_hospital()
    if hospital_pk is not None and hospital_pk != hospital.pk:
        if not request.user.doctorprofile.has_group("Конструктор: Настройка всех организаций"):
            return status_response(False, "Доступ запрещен")
        hospital = Hospitals.objects.get(pk=hospital_pk)

    has_full_ftp_access = SettingManager.l2("ftp") and request.user.doctorprofile.has_group("Конструктор: Настройка всех организаций")

    old_data = {
        "title": hospital.title,
        "short_title": hospital.short_title,
        "address": hospital.address,
        "phones": hospital.phones,
        "ogrn": hospital.ogrn,
        "current_manager": hospital.current_manager,
        "license_data": hospital.license_data,
        "www": hospital.www,
        "email": hospital.email,
        "okpo": hospital.okpo,
        **(
            {
                "orders_pull_by_numbers": hospital.orders_pull_by_numbers,
                "orders_push_by_numbers": hospital.orders_push_by_numbers,
                "is_external_performing_organization": hospital.is_external_performing_organization,
                "strict_tube_numbers": hospital.strict_tube_numbers,
                "strict_data_ownership": hospital.strict_data_ownership,
                "strict_external_numbers": hospital.strict_external_numbers,
                "result_pull_by_numbers": hospital.result_pull_by_numbers,
            }
            if has_full_ftp_access
            else {}
        ),
    }

    new_data = {
        "title": title,
        "short_title": short_title,
        "address": address,
        "phones": phones,
        "ogrn": ogrn,
        "current_manager": current_manager,
        "license_data": license_data,
        "www": www,
        "email": email,
        "okpo": okpo,
        **(
            {
                "orders_pull_by_numbers": orders_pull_by_numbers,
                "orders_push_by_numbers": orders_push_by_numbers,
                "is_external_performing_organization": is_external_performing_organization,
                "strict_tube_numbers": strict_tube_numbers,
                "strict_data_ownership": strict_data_ownership,
                "strict_external_numbers": strict_external_numbers,
                "result_pull_by_numbers": result_pull_by_numbers,
                "hl7_sender_application": hl7_sender_application,
                "hl7_receiver_appplication": hl7_receiver_appplication,
            }
            if has_full_ftp_access
            else {}
        ),
    }

    hospital.title = title
    hospital.short_title = short_title
    hospital.address = address
    hospital.phones = phones
    hospital.ogrn = ogrn
    hospital.current_manager = current_manager
    hospital.license_data = license_data
    hospital.www = www
    hospital.email = email
    hospital.okpo = okpo
    hospital.hl7_receiver_appplication = hl7_receiver_appplication
    hospital.hl7_sender_application = hl7_sender_application
    hospital.is_auto_transfer_hl7_file = is_auto_transfer

    if has_full_ftp_access:
        hospital.orders_pull_by_numbers = orders_pull_by_numbers
        hospital.orders_push_by_numbers = orders_push_by_numbers
        hospital.is_external_performing_organization = is_external_performing_organization
        hospital.strict_tube_numbers = strict_tube_numbers
        hospital.strict_data_ownership = strict_data_ownership
        hospital.strict_external_numbers = strict_external_numbers
        hospital.result_pull_by_numbers = result_pull_by_numbers
    hospital.save()

    Log.log(
        hospital.pk,
        110000,
        request.user.doctorprofile,
        {
            "oldData": old_data,
            "newData": new_data,
        },
    )

    return status_response(True)


@login_required
def get_links(request):
    if not SOME_LINKS:
        return JsonResponse({"rows": []})

    return JsonResponse({"rows": SOME_LINKS})


@login_required
def get_disabled_forms(request):
    user_disabled_forms = request.user.doctorprofile.disabled_forms.split(",")
    user_disabled_forms.extend(DISABLED_FORMS)
    result_disabled_forms = set(user_disabled_forms)
    if len(result_disabled_forms) == 0:
        return JsonResponse({"rows": []})

    return JsonResponse({"rows": list(result_disabled_forms)})


@login_required
def get_disabled_categories(request):
    disabled_statistic_categories = request.user.doctorprofile.disabled_statistic_categories.split(",")
    disabled_statistic_categories.extend(DISABLED_STATISTIC_CATEGORIES)
    result_disabled_statistic_categories = set(disabled_statistic_categories)
    if len(result_disabled_statistic_categories) == 0:
        return JsonResponse({"rows": []})

    return JsonResponse({"rows": list(result_disabled_statistic_categories)})


@login_required
def get_disabled_reports(request):
    disabled_statistic_reports = request.user.doctorprofile.disabled_statistic_reports.split(",")
    disabled_statistic_reports.extend(DISABLED_STATISTIC_REPORTS)
    result_disabled_statistic_reports = set(disabled_statistic_reports)
    if len(result_disabled_statistic_reports) == 0:
        return JsonResponse({"rows": []})

    return JsonResponse({"rows": list(result_disabled_statistic_reports)})


@login_required
def unlimit_period_statistic_groups(request):
    return JsonResponse({"rows": UNLIMIT_PERIOD_STATISTIC_GROUP})


@login_required
def org_generators(request):
    hospital: Hospitals = request.user.doctorprofile.get_hospital()

    request_data = json.loads(request.body)
    hospital_pk = request_data.get("hospitalId")

    if hospital_pk is not None and hospital_pk != hospital.pk:
        if not request.user.doctorprofile.has_group("Конструктор: Настройка всех организаций"):
            return status_response(False, "Доступ запрещен", data={"rows": []})
        hospital = Hospitals.objects.get(pk=hospital_pk)

    rows = []

    g: directions.NumberGenerator
    for g in directions.NumberGenerator.objects.filter(hospital=hospital).order_by("pk"):
        rows.append(
            {
                "pk": g.pk,
                "key": g.key,
                "keyDisplay": g.get_key_display(),
                "year": g.year,
                "isActive": g.is_active,
                "start": g.start,
                "end": g.end,
                "last": g.last,
                "prependLength": g.prepend_length,
            }
        )

    return JsonResponse({"rows": rows})


@login_required
@group_required("Конструктор: Настройка организации", "Конструктор: Настройка всех организаций")
def org_generators_add(request):
    parse_params = {
        "key": str,
        "year": int,
        "start": int,
        "end": int,
        "prependLength": int,
        "hospitalId": int,
    }

    data = data_parse(request.body, parse_params, {"end": None, "prependLength": None, "hospitalId": None, "year": None})

    key: str = data[0]
    year: Optional[int] = data[1]
    start: int = data[2]
    end: Optional[int] = data[3]
    prepend_length: Optional[int] = data[4]
    hospital_pk: Optional[int] = data[5]

    hospital: Hospitals = request.user.doctorprofile.get_hospital()

    if hospital_pk is not None and hospital_pk != hospital.pk:
        if not request.user.doctorprofile.has_group("Конструктор: Настройка всех организаций"):
            return status_response(False, "Доступ запрещен")
        hospital = Hospitals.objects.get(pk=hospital_pk)

    if hospital.is_default:
        return status_response(False, "Такой генератор создать невозможно")

    is_simple_generator = key == "tubeNumber" or key == "externalOrderNumber"

    if is_simple_generator:
        year = -1
        prepend_length = 0
    else:
        if year is None:
            return status_response(False, "Год не может быть пустым")
        if prepend_length is None:
            return status_response(False, "prepend_length не может быть пустым")
        if end is None:
            return status_response(False, "end не может быть пустым")

    try:
        with transaction.atomic():
            if is_simple_generator:
                directions.NumberGenerator.objects.filter(hospital=hospital, key=key).update(is_active=False)
            else:
                directions.NumberGenerator.objects.filter(hospital=hospital, key=key, year=year).update(is_active=False)

            if is_simple_generator and key != "externalOrderNumber":
                if (
                    directions.NumberGenerator.objects.filter(key=key)
                    .filter(Q(start__lte=start, end__lte=end, end__gte=start) | Q(start__gte=start, start__lte=end, end__gte=end) | Q(start__gte=start, end__lte=end))
                    .exists()
                ):
                    raise directions.GeneratorOverlap("Уже существуют генераторы, включающие указанные интервалы")

                if directions.TubesRegistration.objects.filter(number__gte=start, number__lte=end).exists():
                    raise directions.GeneratorOverlap("Указанный интервал пересекается с уже существующими номерами ёмкостей")

            directions.NumberGenerator.objects.create(hospital=hospital, key=key, year=year, start=start, end=end, prepend_length=prepend_length, is_active=True)

            Log.log(
                hospital.pk,
                110000,
                request.user.doctorprofile,
                {
                    "key": key,
                    "year": year,
                    "start": start,
                    "end": end,
                    "prepend_length": prepend_length,
                },
            )

        return status_response(True)
    except directions.GeneratorOverlap as e:
        return status_response(False, str(e))

    return status_response(False)


def current_time(request):
    now = timezone.now().astimezone(pytz.timezone(TIME_ZONE))
    return JsonResponse(
        {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%X"),
        }
    )


def search_param(request):
    data = json.loads(request.body)
    year_period = data.get("year_period") or -1
    research_id = data.get("research_id") or -1
    profile_research_id = data.get("profile_research_id") or -1
    date_create_start = f"{year_period}-01-01 00:00:00"
    date_create_end = f"{year_period}-12-31 23:59:59"
    case_number = data.get("case_number") or "-1"
    hospital_id = int(data.get("hospitalId") or -1)
    direction_number = int(data.get("directionNumber") or -1)

    date_examination_start = data.get("dateExaminationStart") or "1900-01-01"
    date_examination_end = data.get("dateExaminationEnd") or "1900-01-01"

    doc_confirm = data.get("docConfirm") or -1

    date_registred_start = data.get("dateRegistredStart") or "1900-01-01"
    date_registred_start = f"{date_registred_start} 00:00:00"
    date_registred_end = data.get("dateRegistredEnd") or "1900-01-01"
    date_registred_end = f"{date_registred_end} 23:59:59"

    search_stationar = data.get("searchStationar") or False

    date_recieve = data.get("dateReceive") or "1900-01-01"
    date_recieve_start = f"{date_recieve} 00:00:00"
    date_recieve_end = f"{date_recieve} 23:59:59"

    if data.get("dateCreateStart", None):
        date_create_start = data.get("dateCreateStart")
        date_create_start = f"{date_create_start} 00:00:00"

    if data.get("dateCreateEnd", None):
        date_create_end = data.get("dateCreateEnd") or "1900-01-01"
        date_create_end = f"{date_create_end} 23:59:59"

    # из проткола
    date_get = data.get("dateGet") or "1900-01-01"
    final_text = data.get("finalText") or ""
    rows = []
    created_document_only_user_hosp = SettingManager.get("created_document_only_user_hosp", default="false", default_type="b")
    user_groups = [str(x) for x in request.user.groups.all()]
    if created_document_only_user_hosp and "Направления-все МО" not in user_groups:
        hospital_id = request.user.doctorprofile.hospital_id
    research_id = (research_id,)
    if profile_research_id > 0:
        data_researches = Researches.objects.values_list("pk", flat=True).filter(speciality_id=profile_research_id)
        research_id = tuple(data_researches)

    if not search_stationar:
        result = search_data_by_param(
            date_create_start,
            date_create_end,
            research_id,
            case_number,
            hospital_id,
            date_registred_start,
            date_registred_end,
            date_examination_start,
            date_examination_end,
            doc_confirm,
            date_recieve_start,
            date_recieve_end,
            date_get,
            final_text,
            direction_number,
        )
        rows = [
            {
                "patient_fio": i.patient_fio,
                "patient_birthday": i.patient_birthday,
                "patient_age": i.patient_age,
                "hosp_title": i.hosp_short_title,
                "doc_fio": i.doc_fio,
                "direction_number": f"{i.direction_number}",
                "field_value": i.field_value,
                "patient_sex": i.patient_sex,
                "registered_date": i.registered_date,
                "time_gistology_receive": i.time_gistology_receive,
                "date_confirm": i.date_confirm,
                "medical_examination": i.medical_examination,
                "doc_plan_fio": i.doc_plan_fio,
                "additional_number": f"{i.additional_number}" if i.additional_number else "",
            }
            for i in result
        ]
    elif search_stationar and final_text:
        result = search_text_stationar(date_create_start, date_create_end, final_text)
        rows = [
            {
                "patient_fio": i.patient_fio,
                "patient_birthday": i.patient_birthday,
                "patient_age": i.patient_age,
                "hosp_title": "",
                "doc_fio": i.doc_fio,
                "direction_number": i.direction_number,
                "field_value": i.field_value,
                "patient_sex": i.patient_sex,
                "research_title": i.research_title,
                "history_num": i.history_num,
                "date_confirm": i.date_confirm,
                "additional_number": "",
            }
            for i in result
        ]

    return JsonResponse({"rows": rows, "count": len(rows)})


def statistic_params_search(request):
    user_groups = [str(x) for x in request.user.groups.all()]
    result = []
    has_param = False
    for k, v in SEARCH_PAGE_STATISTIC_PARAMS.items():
        if k in user_groups:
            result.extend(v)
    if len(result) > 0:
        has_param = True
    return JsonResponse({"rows": result, "hasParam": has_param})


@login_required
@group_required("Конструктор: Настройка организации")
def get_prices(request):
    request_data = json.loads(request.body)
    prices = None
    if request_data.get("searchTypesObject") == "Работодатель":
        prices = [{"id": price.pk, "label": price.title} for price in PriceName.objects.filter(subcontract=False, external_performer=False).order_by("title")]
    elif request_data.get("searchTypesObject") == "Заказчик":
        prices = [{"id": price.pk, "label": price.title} for price in PriceName.objects.filter(subcontract=True).order_by("title")]
    elif request_data.get("searchTypesObject") == "Внешний исполнитель":
        prices = [{"id": price.pk, "label": price.title} for price in PriceName.objects.filter(external_performer=True).order_by("title")]

    return JsonResponse({"data": prices})


@login_required
@group_required("Конструктор: Настройка организации")
def get_price_data(request):
    request_data = json.loads(request.body)
    current_price = PriceName.objects.get(pk=request_data["id"])
    price_data = current_price.as_json(current_price)
    return JsonResponse({"data": price_data})


@login_required
@group_required("Конструктор: Настройка организации")
def update_price(request):
    request_data = json.loads(request.body)
    current_price = None
    if request_data["id"] == -1:
        if request_data.get("typePrice") == "Работодатель":
            current_price = PriceName(
                title=request_data["title"], symbol_code=request_data["code"], date_start=request_data["start"], date_end=request_data["end"], company_id=request_data["company"]
            )
        elif request_data.get("typePrice") == "Заказчик":
            hospital = Hospitals.objects.filter(pk=int(request_data["company"])).first()
            current_price = PriceName(
                title=request_data["title"], symbol_code=request_data["code"], date_start=request_data["start"], date_end=request_data["end"], hospital=hospital, subcontract=True
            )
        elif request_data.get("typePrice") == "Внешний исполнитель":
            hospital = Hospitals.objects.filter(pk=int(request_data["company"])).first()
            current_price = PriceName(
                title=request_data["title"], symbol_code=request_data["code"], date_start=request_data["start"], date_end=request_data["end"], hospital=hospital, external_performer=True
            )
        if current_price:
            current_price.save()
            Log.log(
                current_price.pk,
                130007,
                request.user.doctorprofile,
                current_price.as_json(current_price),
            )
    else:
        current_price = PriceName.objects.get(pk=request_data["id"])
        current_price.title = request_data["title"]
        current_price.symbol_code = request_data["code"]
        current_price.date_start = request_data["start"]
        current_price.date_end = request_data["end"]
        if request_data.get("typePrice") == "Заказчик" or request_data.get("typePrice") == "Работодатель":
            current_price.company_id = request_data["company"]
        else:
            hospital = Hospitals.objects.filter(pk=int(request_data["company"])).first()
            current_price.hospital = hospital
        current_price.save()
        Log.log(
            current_price.pk,
            130006,
            request.user.doctorprofile,
            current_price.as_json(current_price),
        )
    return status_response(True)


@login_required
@group_required("Конструктор: Настройка организации")
def copy_price(request):
    request_data = json.loads(request.body)
    if request_data["id"]:
        current_price = PriceName.objects.get(pk=request_data["id"])
        new_price = PriceName(
            title=f"{current_price.title} - новый прайс",
            symbol_code=f"{current_price.symbol_code} - новый",
            date_start=current_price.date_start,
            date_end=current_price.date_end,
            company=current_price.company,
            hospital=current_price.hospital,
            external_performer=current_price.external_performer,
            subcontract=current_price.subcontract,
        )
        new_price.save()
        price_coast = PriceCoast.objects.filter(price_name=current_price)
        for pc in price_coast:
            new_price_coast = PriceCoast(price_name=new_price, research=pc.research, coast=pc.coast, number_services_by_contract=pc.number_services_by_contract)
            new_price_coast.save()

        Log.log(current_price.pk, 130006, request.user.doctorprofile, {"source_price": current_price.pk, "sour_title": current_price.title, "new_price": new_price.pk})

    return status_response(True)


@login_required
@group_required("Конструктор: Настройка организации")
def check_price_active(request):
    request_data = json.loads(request.body)
    current_price = PriceName.objects.get(pk=request_data["id"])
    return status_response(current_price.active_status)


@login_required
@group_required("Конструктор: Настройка организации")
def get_coasts_researches_in_price(request):
    request_data = json.loads(request.body)
    coast_research = [
        {"id": data.pk, "research": {"title": data.research.title, "id": data.research.pk}, "coast": f"{data.coast}", "numberService": data.number_services_by_contract}
        for data in PriceCoast.objects.filter(price_name_id=request_data["id"]).prefetch_related("research").order_by("research__title")
    ]
    return JsonResponse({"data": coast_research})


@login_required
@group_required("Конструктор: Настройка организации")
def update_coast_research_in_price(request):
    request_data = json.loads(request.body)
    current_coast_research = PriceCoast.objects.get(id=request_data["coastResearchId"])
    if not current_coast_research.price_name.active_status:
        return JsonResponse({"ok": False, "message": "Прайс неактивен"})
    elif float(request_data["coast"]) <= 0:
        return JsonResponse({"ok": False, "message": "Неверная цена"})
    old_coast = current_coast_research.coast
    old_number = current_coast_research.number_services_by_contract
    current_coast_research.coast = request_data["coast"]
    current_coast_research.number_services_by_contract = request_data.get("numberService", 0)
    current_coast_research.save()
    Log.log(
        current_coast_research.pk,
        130000,
        request.user.doctorprofile,
        {
            "pk": current_coast_research.pk,
            "price": {"pk": current_coast_research.price_name.pk, "title": current_coast_research.price_name.title},
            "research": {"pk": current_coast_research.research.pk, "title": current_coast_research.research.title},
            "old_coast": old_coast,
            "new_coast": current_coast_research.coast,
            "old_number": old_number,
            "new_number": current_coast_research.number_services_by_contract,
        },
    )
    return JsonResponse({"ok": "ok"})


@login_required
@group_required("Конструктор: Настройка организации")
def get_research_list(request):
    researches = Researches.objects.filter(hide=False)
    res_list = {
        "Лаборатория": {},
        "Параклиника": {},
        "Консультации": {"Общие": []},
        "Формы": {"Общие": []},
        "Лечение": {"Общие": []},
        "Морфология": {"Микробиология": [], "Гистология": [], "Цитология": []},
        "Стоматология": {"Общие": []},
    }
    lab_podr = get_lab_podr()
    lab_podr = [podr[0] for podr in lab_podr]
    for research in researches:
        if research.is_doc_refferal:
            if research.site_type is None:
                res_list["Консультации"]["Общие"].append({"id": research.pk, "label": research.title})
            elif not res_list["Консультации"].get(research.site_type.title):
                res_list["Консультации"][research.site_type.title] = [{"id": research.pk, "label": research.title}]
            else:
                res_list["Консультации"][research.site_type.title].append({"id": research.pk, "label": research.title})
        elif research.is_citology:
            res_list["Морфология"]["Цитология"].append({"id": research.pk, "label": research.title})
        elif research.is_gistology:
            res_list["Морфология"]["Гистология"].append({"id": research.pk, "label": research.title})
        elif research.is_microbiology:
            res_list["Морфология"]["Микробиология"].append({"id": research.pk, "label": research.title})
        elif research.is_stom:
            if research.site_type is None:
                res_list["Стоматология"]["Общие"].append({"id": research.pk, "label": research.title})
            elif not res_list["Стоматология"].get(research.site_type.title):
                res_list["Стоматология"][research.site_type.title] = [{"id": research.pk, "label": research.title}]
            else:
                res_list["Стоматология"][research.site_type.title].append({"id": research.pk, "label": research.title})
        elif research.is_form:
            if research.site_type is None:
                res_list["Формы"]["Общие"].append({"id": research.pk, "label": research.title})
            elif not res_list["Формы"].get(research.site_type.title):
                res_list["Формы"][research.site_type.title] = [{"id": research.pk, "label": research.title}]
            else:
                res_list["Формы"][research.site_type.title].append({"id": research.pk, "label": research.title})
        elif research.is_treatment:
            if research.site_type is None:
                res_list["Лечение"]["Общие"].append({"id": research.pk, "label": research.title})
            elif not res_list["Лечение"].get(research.site_type.title):
                res_list["Лечение"][research.site_type.title] = [{"id": research.pk, "label": research.title}]
            else:
                res_list["Лечение"][research.site_type.title].append({"id": research.pk, "label": research.title})
        elif research.is_paraclinic:
            if research.podrazdeleniye is None:
                pass
            elif not res_list["Параклиника"].get(research.podrazdeleniye.title):
                res_list["Параклиника"][research.podrazdeleniye.title] = [{"id": research.pk, "label": research.title}]
            else:
                res_list["Параклиника"][research.podrazdeleniye.title].append({"id": research.pk, "label": research.title})
        elif research.podrazdeleniye is None:
            pass
        elif research.podrazdeleniye.pk in lab_podr:
            if not res_list["Лаборатория"].get(research.podrazdeleniye.title):
                res_list["Лаборатория"][research.podrazdeleniye.title] = [{"id": research.pk, "label": research.title}]
            else:
                res_list["Лаборатория"][research.podrazdeleniye.title].append({"id": research.pk, "label": research.title})

    result_list = []
    count = 0
    for key, value in res_list.items():
        count += 1
        current_researches = {"id": f"а{count}", "label": key, "children": []}
        for k, v in value.items():
            count += 1
            current_researches["children"].append({"id": f"а{count}", "label": k, "children": v})
        result_list.append(current_researches)
    return JsonResponse({"data": result_list})


@login_required
@group_required("Конструктор: Настройка организации")
def add_research_in_price(request):
    request_data = json.loads(request.body)
    if not PriceName.objects.get(pk=request_data["priceId"]).active_status:
        return JsonResponse({"ok": False, "message": "Прайс неактивен"})
    elif float(request_data["coast"]) <= 0:
        return JsonResponse({"ok": False, "message": "Неверная цена"})
    current_coast_research = PriceCoast(
        price_name_id=request_data["priceId"], research_id=request_data["researchId"], coast=request_data["coast"], number_services_by_contract=request_data.get("numberService", 0)
    )
    current_coast_research.save()
    Log.log(
        current_coast_research.pk,
        130000,
        request.user.doctorprofile,
        {
            "pk": current_coast_research.pk,
            "price": {"pk": current_coast_research.price_name.pk, "title": current_coast_research.price_name.title},
            "research": {"pk": current_coast_research.research.pk, "title": current_coast_research.research.title},
            "coast": current_coast_research.coast,
        },
    )
    return JsonResponse({"ok": "ok"})


@login_required
@group_required("Конструктор: Настройка организации")
def delete_research_in_price(request):
    request_data = json.loads(request.body)
    current_coast_research = PriceCoast.objects.get(pk=request_data["coastResearchId"])
    if not current_coast_research.price_name.active_status:
        return JsonResponse({"ok": False, "message": "Прайс неактивен"})
    data = {
        "pk": current_coast_research.pk,
        "data_json": {
            "pk": current_coast_research.pk,
            "price": {"pk": current_coast_research.price_name.pk, "title": current_coast_research.price_name.title},
            "research": {"pk": current_coast_research.research.pk, "title": current_coast_research.research.title},
            "coast": current_coast_research.coast,
        },
    }
    current_coast_research.delete()
    Log.log(data["pk"], 130001, request.user.doctorprofile, data["data_json"])
    return JsonResponse({"ok": "ok"})


@login_required
@group_required("Конструктор: Настройка организации")
def get_companies(request):
    company_data = [
        {
            "pk": company.pk,
            "title": company.title,
        }
        for company in Company.objects.filter(active_status=True).order_by("title")
    ]
    return JsonResponse({"data": company_data})


@login_required
@group_required("Конструктор: Настройка организации")
def get_contracts(request):
    contract_data = [
        {
            "value": contract.pk,
            "label": contract.title,
        }
        for contract in Contract.objects.filter(~Exists(Company.objects.filter(contract=OuterRef("pk")))).order_by("title")
    ]
    return JsonResponse({"data": contract_data})


@login_required
@group_required("Конструктор: Настройка организации")
def get_company(request):
    request_data = json.loads(request.body)
    company = Company.objects.get(pk=request_data["pk"])
    company_data = Company.as_json(company)
    if company_data["contractId"]:
        company_data["contractData"] = {"value": company.contract.pk, "label": company.contract.title}
    return JsonResponse({"data": company_data})


@login_required
@group_required("Конструктор: Настройка организации")
def update_company(request):
    request_data = json.loads(request.body)
    if request_data.get("pk"):
        if Company.objects.filter(title=request_data["title"]).exclude(pk=request_data["pk"]):
            return JsonResponse({"ok": False, "message": "Такое название уже есть"})
        elif Company.objects.filter(inn=request_data["inn"]).exclude(pk=request_data["pk"]):
            return JsonResponse({"ok": False, "message": "Такой ИНН уже есть"})
        company_data = Company.objects.get(pk=request_data["pk"])
        old_company_data = Company.as_json(company_data)
        company_data.title = request_data["title"]
        company_data.short_title = request_data["shortTitle"]
        company_data.legal_address = request_data["legalAddress"]
        company_data.fact_address = request_data["factAddress"]
        company_data.inn = request_data["inn"]
        company_data.ogrn = request_data["ogrn"]
        company_data.kpp = request_data["kpp"]
        company_data.bik = request_data["bik"]
        company_data.contract_id = request_data.get("contractId") or None
        company_data.cpp_send = request_data.get("cppSend", False)
        company_data.save()
        new_company_data = Company.as_json(company_data)
        Log.log(
            company_data.pk,
            130002,
            request.user.doctorprofile,
            {"old_company_data": str(old_company_data), "new_company_data": str(new_company_data)},
        )
        return JsonResponse({"ok": True})
    else:
        if Company.objects.filter(title=request_data["title"]):
            return JsonResponse({"ok": False, "message": "Такое название уже есть"})
        elif Company.objects.filter(inn=request_data["inn"]):
            return JsonResponse({"ok": False, "message": "Такой ИНН уже есть"})
        company_data = Company(
            title=request_data["title"],
            short_title=request_data.get("shortTitle") or "",
            legal_address=request_data.get("legalAddress") or "",
            fact_address=request_data.get("factAddress") or "",
            inn=request_data["inn"],
            ogrn=request_data.get("ogrn") or "",
            kpp=request_data.get("kpp") or "",
            bik=request_data.get("bik") or "",
            contract_id=request_data.get("contractId") or None,
        )
        company_data.save()
        Log.log(
            company_data.pk,
            130003,
            request.user.doctorprofile,
            {"company_data": Company.as_json(company_data)},
        )
        return JsonResponse({"ok": True})


def update_department(request):
    request_data = json.loads(request.body)
    if len(request_data["label"]) == 0:
        return JsonResponse({"ok": False, "message": "Название не заполнено"})
    if CompanyDepartment.objects.filter(title=request_data["label"]).exclude(pk=request_data["id"]):
        return JsonResponse({"ok": False, "message": "Такое название уже есть"})
    department = CompanyDepartment.objects.get(pk=request_data["id"])
    department.title = request_data["label"]
    department.save()
    Log.log(
        department.pk,
        130005,
        request.user.doctorprofile,
        {"department": department.title, "company_id": department.company_id},
    )
    return JsonResponse({"ok": True})


def add_department(request):
    request_data = json.loads(request.body)
    if len(request_data["department"]) == 0:
        return JsonResponse({"ok": False, "message": "Название не заполнено"})
    if CompanyDepartment.objects.filter(title=request_data["department"]):
        return JsonResponse({"ok": False, "message": "Такое название уже есть"})
    if not Company.objects.get(pk=request_data["company_id"]):
        return JsonResponse({"ok": False, "message": "Нет такой компании"})
    department = CompanyDepartment(title=request_data["department"], hide=False, company_id=request_data["company_id"])
    department.save()
    Log.log(
        department.pk,
        130004,
        request.user.doctorprofile,
        {"department": department.title, "company_id": department.company_id},
    )
    return JsonResponse({"ok": True})


def get_harmful_factors(request):
    rows = [
        {
            "id": factor.pk,
            "label": f"{factor.title}",
            "title": factor.title,
            "description": factor.description,
            "template_id": factor.template_id,
            "cpp_key": factor.cpp_key,
        }
        for factor in HarmfulFactor.objects.all().order_by("title")
    ]
    return JsonResponse(rows, safe=False)


def get_template_researches_pks(request):
    request_data = json.loads(request.body)
    template_pks = HarmfulFactor.get_template_by_factor(request_data["harmful_factor_pks"])
    rows = users.AssignmentResearches.get_researches_by_template(template_pks)
    return JsonResponse(rows, safe=False)


def get_templates(request):
    template_data = [{"id": template.pk, "label": template.title} for template in users.AssignmentTemplates.objects.all().order_by("title")]
    return JsonResponse({"data": template_data})


@login_required
@group_required("Конструктор: Факторы вредности")
def update_factor(request):
    request_data = json.loads(request.body)
    result = {"ok": True}
    if not re.fullmatch("^[0-9.]+$", request_data["title"]):
        result["ok"] = False
        result["message"] = "Название не соответствует правилам"
    elif not HarmfulFactor.objects.filter(pk=request_data["id"]).exists():
        result["ok"] = False
        result["message"] = "Нет такого фактора"
    elif not users.AssignmentTemplates.objects.filter(pk=request_data["template_id"]).exists():
        result["ok"] = False
        result["message"] = "Нет такого шаблона"
    elif HarmfulFactor.objects.filter(title=request_data["title"]).exclude(pk=request_data["id"]).exists():
        result["ok"] = False
        result["message"] = "Такое название уже есть"
    if result["ok"]:
        factor = HarmfulFactor.objects.get(pk=request_data["id"])
        factor.title = request_data["title"]
        factor.description = request_data["description"]
        factor.template_id = request_data["template_id"]
        factor.save()
        Log.log(
            factor.pk,
            150000,
            request.user.doctorprofile,
            {"factor": factor.as_json(factor)},
        )
    return JsonResponse(result)


@login_required
@group_required("Конструктор: Факторы вредности")
def add_factor(request):
    request_data = json.loads(request.body)
    result = {"ok": True}
    if not re.fullmatch("^[0-9.]+$", request_data["title"]):
        result["ok"] = False
        result["message"] = "Название не соответствует правилам"
    elif not users.AssignmentTemplates.objects.filter(pk=request_data["templateId"]).exists():
        result["ok"] = False
        result["message"] = "Нет такого шаблона"
    elif HarmfulFactor.objects.filter(title=request_data["title"]).exists():
        result["ok"] = False
        result["message"] = "Такое название уже есть"
    if result["ok"]:
        factor = HarmfulFactor(title=request_data["title"], description=request_data["description"], template_id=request_data["templateId"])
        factor.save()
        Log.log(
            factor.pk,
            150001,
            request.user.doctorprofile,
            {"factor": factor.as_json(factor)},
        )
    return JsonResponse(result)


@login_required
@group_required("Конструктор: Настройка организации")
def get_research_sets(request):
    sets = [{"id": set_research.pk, "label": set_research.title} for set_research in SetResearch.objects.all().order_by("title")]
    return JsonResponse({"data": sets})


@login_required
@group_required("Конструктор: Настройка организации", "")
def get_type_departments(request):
    res = [{"id": t[0], "label": t[1]} for t in Podrazdeleniya.TYPES if t[0] in STATISTIC_TYPE_DEPARTMENT]
    return JsonResponse({"data": res})


@login_required
@group_required("Конструктор: Настройка организации")
def get_researches_in_set(request):
    request_data = json.loads(request.body)
    researches = [
        {
            "id": i.pk,
            "research": {"id": i.research_id, "label": i.research.title},
            "order": i.order,
        }
        for i in SetOrderResearch.objects.filter(set_research=request_data).order_by("-order")
    ]
    return JsonResponse({"data": researches})


@login_required
@group_required("Конструктор: Настройка организации")
def add_research_in_set(request):
    request_data = json.loads(request.body)
    if not SetOrderResearch.objects.filter(set_research_id=request_data["set"]).exists():
        offset = 0
    else:
        offset = 1
    current_research_in_set = SetOrderResearch(set_research_id=request_data["set"], research_id=request_data["research"], order=request_data["minOrder"] - offset)
    current_research_in_set.save()
    Log.log(
        current_research_in_set.pk,
        170000,
        request.user.doctorprofile,
        {"set": current_research_in_set.set_research_id, "research": current_research_in_set.research_id, "order": current_research_in_set.order},
    )
    return status_response(True)


@login_required
@group_required("Конструктор: Настройка организации")
def update_order_in_set(request):
    request_data = json.loads(request.body)
    if request_data["action"] == "inc_order":
        next_research_in_set = SetOrderResearch.objects.filter(set_research=request_data["set"], order=request_data["order"] + 1).first()
        if next_research_in_set:
            current_research_in_set = SetOrderResearch.objects.get(pk=request_data["id"])
            next_research_in_set.order -= 1
            current_research_in_set.order += 1
            next_research_in_set.save()
            current_research_in_set.save()
        else:
            return status_response(False, "Исследование первое в наборе")
    elif request_data["action"] == "dec_order":
        prev_research_in_set = SetOrderResearch.objects.filter(set_research=request_data["set"], order=request_data["order"] - 1).first()
        if prev_research_in_set:
            current_research_in_set = SetOrderResearch.objects.get(pk=request_data["id"])
            prev_research_in_set.order += 1
            current_research_in_set.order -= 1
            prev_research_in_set.save()
            current_research_in_set.save()
        else:
            return status_response(False, "Исследование последнее в наборе")
    return status_response(True)


@login_required
@group_required("Конструктор: Настройка организации")
def update_research_set(request):
    request_data = json.loads(request.body)
    if request_data["id"] == -1:
        current_set = SetResearch(title=request_data["label"])
        current_set.save()
        Log.log(
            current_set.pk,
            170001,
            request.user.doctorprofile,
            {"pk": current_set.pk, "title": current_set.title},
        )
    else:
        current_set = SetResearch.objects.get(pk=request_data["id"])
        current_set.title = request_data["label"]
        current_set.save()
        Log.log(
            current_set.pk,
            170002,
            request.user.doctorprofile,
            {"pk": current_set.pk, "title": current_set.title},
        )
    return status_response(True)


@login_required
@group_required("Конструктор: Настройка организации")
def update_set_hiding(request):
    request_data = json.loads(request.body)
    current_set = SetResearch.objects.get(pk=request_data)
    if current_set.hide:
        current_set.hide = False
    else:
        current_set.hide = True
    current_set.save()
    Log.log(
        current_set.pk,
        170002,
        request.user.doctorprofile,
        {"pk": current_set.pk, "title": current_set.title, "hide": current_set.hide},
    )
    return status_response(True)


@login_required
@group_required("Конструктор: Настройка организации")
def check_set_hidden(request):
    request_data = json.loads(request.body)
    current_set = SetResearch.objects.get(pk=request_data)
    return status_response(current_set.hide)


@login_required
@group_required("Конструктор: Контролируемые параметры пациентов")
def get_control_params(request):
    params_data = [PatientControlParam.as_json(param) for param in PatientControlParam.objects.all().order_by("order")]
    return JsonResponse({"data": params_data})


@login_required
@group_required("Конструктор: Контролируемые параметры пациентов")
def update_control_param(request):
    request_data = json.loads(request.body)
    param_data = PatientControlParam.objects.get(pk=request_data["pk"])
    param_data.title = request_data["title"]
    param_data.code = request_data["code"]
    param_data.all_patient_contol = request_data["all_patient_control"]
    param_data.save()
    Log.log(param_data.pk, 160000, request.user.doctorprofile, {"param_data": PatientControlParam.as_json(param_data)})
    return status_response(True)


@login_required
@group_required("Конструктор: Контролируемые параметры пациентов")
def add_control_param(request):
    request_data = json.loads(request.body)
    if not PatientControlParam.objects.all().exists():
        offset = 0
    else:
        offset = 1
    param_data = PatientControlParam(title=request_data["title"], code=request_data["code"], all_patient_contol=request_data["allPatientControl"], order=request_data["maxOrder"] + offset)
    param_data.save()
    Log.log(
        param_data.pk,
        160001,
        request.user.doctorprofile,
        {"param_data": PatientControlParam.as_json(param_data)},
    )
    return status_response(True)


@login_required
@group_required("Конструктор: Контролируемые параметры пациентов")
def update_order_param(request):
    request_data = json.loads(request.body)
    if request_data["action"] == "inc_order":
        next_param = PatientControlParam.objects.filter(order=request_data["order"] + 1).first()
        if next_param:
            current_param = PatientControlParam.objects.get(pk=request_data["id"])
            next_param.order -= 1
            current_param.order += 1
            next_param.save()
            current_param.save()
        else:
            return status_response(False, "Параметр первый")
    elif request_data["action"] == "dec_order":
        prev_param = PatientControlParam.objects.filter(order=request_data["order"] - 1).first()
        if prev_param:
            current_param = PatientControlParam.objects.get(pk=request_data["id"])
            prev_param.order += 1
            current_param.order -= 1
            prev_param.save()
            current_param.save()
        else:
            return status_response(False, "Параметр последний")
    return status_response(True)


@login_required
@group_required("Конструктор: Настройка организации")
def get_examination_list(request):
    request_data = json.loads(request.body)
    examination_list = MedicalExamination.get_by_date(request_data["date"], request_data["company"], request_data["month"])
    return JsonResponse({"data": examination_list})


@login_required
@group_required("Конструктор: Настройка организации")
def print_medical_examination_data(request):
    request_data = json.loads(request.body)
    cards = request_data.get("cards")
    card_directions = create_case_by_cards(cards)
    files_data = []
    if TYPE_COMPANY_SET_DIRECTION_PDF:
        additional_page = import_string('forms.forms112.' + TYPE_COMPANY_SET_DIRECTION_PDF.split(".")[0])
        for card, directions_data in card_directions.items():
            if len(directions_data) > 1:
                directions_data = [str(i) for i in directions_data]
                napr_id = ", ".join(directions_data)
            else:
                napr_id = directions_data[0]
            napr_id = f"[{napr_id}]"
            fc = additional_page(
                request_data={
                    **dict(request.GET.items()),
                    "user": request.user,
                    "card_pk": card,
                    "hospital": request.user.doctorprofile.get_hospital() if hasattr(request.user, "doctorprofile") else Hospitals.get_default_hospital(),
                    "type_additional_pdf": TYPE_COMPANY_SET_DIRECTION_PDF.split(".")[1],
                    "fin_title": MEDEXAM_FIN_SOURCE_TITLE,
                    "napr_id": napr_id,
                }
            )
            saved_file_pdf = simple_save_pdf_file(fc)
            files_data.append(saved_file_pdf)

    buffer = simple_join_two_pdf_files(files_data)
    id_file = simple_save_pdf_file(buffer)
    hash_file = correspondence_set_file_hash(id_file)
    return JsonResponse({"id": hash_file})


@login_required
def get_date_medical_examination(request):
    request_data = json.loads(request.body)
    current_exam = MedicalExamination.get_date(request_data["card_pk"])
    return JsonResponse({"data": current_exam})
