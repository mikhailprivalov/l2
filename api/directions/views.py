import collections
import re
import time
from datetime import datetime, time as dtime
from operator import itemgetter

import simplejson as json
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch
from django.http import HttpRequest
from django.http import JsonResponse
from django.utils import dateformat
from django.utils import timezone

from api import sql_func
from api.dicom import search_dicom_study
from api.patients.views import save_dreg
from api.sql_func import get_fraction_result, get_field_result
from api.stationar.stationar_func import forbidden_edit_dir
from api.views import get_reset_time_vars
from appconf.manager import SettingManager
from clients.models import Card, Individual, DispensaryReg, BenefitReg
from directions.models import Napravleniya, Issledovaniya, Result, ParaclinicResult, Recipe, MethodsOfTaking, \
    ExternalOrganization, MicrobiologyResultCulture, \
    MicrobiologyResultCultureAntibiotic
from directory.models import Fractions, ParaclinicInputGroups, ParaclinicTemplateName, ParaclinicInputField
from laboratory import settings
from laboratory import utils
from laboratory.decorators import group_required
from laboratory.settings import DICOM_SERVER
from laboratory.utils import strdatetime, strdate, tsdatetime, start_end_year, strfdatetime, current_time
from results.views import result_normal
from rmis_integration.client import Client, get_direction_full_data_cache
from slog.models import Log
from statistics_tickets.models import VisitPurpose, ResultOfTreatment, Outcomes
from utils.dates import normalize_date
from utils.dates import try_parse_range
from .sql_func import get_history_dir

TADP = SettingManager.get("tadp", default='Температура', default_type='s')


@login_required
@group_required("Лечащий врач", "Оператор лечащего врача")
def directions_generate(request):
    result = {"ok": False, "directions": [], "message": ""}
    if request.method == "POST":
        p = json.loads(request.body)
        type_card = Card.objects.get(pk=p.get("card_pk"))
        if type_card.base.forbidden_create_napr:
            result["message"] = "Для данного типа карт нельзя создать направления"
            return JsonResponse(result)
        args = [
            p.get("card_pk"),
            p.get("diagnos"),
            p.get("fin_source"),
            p.get("history_num"),
            p.get("ofname_pk"),
            request.user.doctorprofile,
            p.get("researches"),
            p.get("comments"),
            p.get("for_rmis"),
            p.get("rmis_data", {}),
        ]
        kwargs = dict(
            vich_code=p.get("vich_code", ""),
            count=p.get("count", 1),
            discount=p.get("discount", 0),
            parent_iss=p.get("parent_iss", None),
            parent_slave_hosp=p.get("parent_slave_hosp", None),
            counts=p.get("counts", {}),
            localizations=p.get("localizations", {}),
            service_locations=p.get("service_locations", {}),
            direction_purpose=p.get("direction_purpose", "NONE"),
            external_organization=p.get("external_organization", "NONE"),
        )
        for _ in range(p.get("directions_count", 1)):
            rc = Napravleniya.gen_napravleniya_by_issledovaniya(*args, **kwargs)
            result["ok"] = rc["r"]
            if "message" in rc:
                result["message"] = rc["message"]
            result["directions"].extend(rc["list_id"])
            if not result["ok"]:
                break
    return JsonResponse(result)


@login_required
def directions_history(request):
    # SQL-query
    res = {"directions": []}
    request_data = json.loads(request.body)
    pk = request_data.get("patient", -1)
    req_status = request_data.get("type", 4)
    iss_pk = request_data.get("iss_pk", None)
    for_slave_hosp = request_data.get("forHospSlave", False)
    services = request_data.get("services", [])
    services = list(map(int, services or []))

    date_start, date_end = try_parse_range(request_data["date_from"], request_data["date_to"])
    date_start = datetime.combine(date_start, dtime.min)
    date_end = datetime.combine(date_end, dtime.max)
    user_creater = -1
    patient_card = -1
    # status: 4 - выписано пользователем,   0 - только выписанные, 1 - Материал получен лабораторией. 2 - результат подтвержден, 3 - направления пациента,  -1 - отменено,
    if req_status == 4:
        user_creater = request.user.doctorprofile.pk
    if req_status in [0, 1, 2, 3]:
        patient_card = pk

    is_service = False
    if services:
        is_service = True

    if not is_service:
        services = [-1]

    is_parent = False
    if iss_pk:
        is_parent = True

    result_sql = get_history_dir(date_start, date_end, patient_card, user_creater, services, is_service, iss_pk, is_parent, for_slave_hosp)
    # napravleniye_id, cancel, iss_id, tubesregistration_id, res_id, res_title, date_create,
    # doc_confirmation_id, time_recive, ch_time_save, podr_title, is_hospital, maybe_onco, can_has_pacs,
    # is_slave_hospital, is_treatment, is_stom, is_doc_refferal, is_paraclinic, is_microbiology, parent_id, study_instance_uid, parent_slave_hosp_id
    researches_pks = []
    researches_titles = ''
    final_result = []
    last_dir, dir, status, date, cancel, pacs, has_hosp, has_descriptive = None, None, None, None, None, None, None, None
    maybe_onco = False
    parent_obj = {"iss_id": "", "parent_title": "", "parent_is_hosp": "", "parent_is_doc_refferal": ""}
    status_set = {-2}
    lab = set()
    lab_title = None

    type_service = request_data.get("type_service", None)
    for i in result_sql:
        if i[14]:
            continue
        elif type_service == 'is_paraclinic' and not i[18]:
            continue
        elif type_service == 'is_doc_refferal' and not i[17]:
            continue
        elif type_service == 'is_lab' and (i[11] or i[14] or i[15] or i[16] or i[17] or i[18] or i[19]):
            continue
        if i[0] != last_dir:
            status = min(status_set)
            if len(lab) > 0:
                lab_title = ', '.join(lab)
            if (req_status == 2 and status == 2) or (req_status in [3, 4] and status != -2) or (req_status == 1 and status == 1) or (req_status == 0 and status == 0):
                final_result.append({'pk': dir, 'status': status, 'researches': researches_titles, "researches_pks": researches_pks, 'date': date, 'cancel': cancel, 'checked': False,
                                     'pacs': pacs, 'has_hosp': has_hosp, 'has_descriptive': has_descriptive, 'maybe_onco': maybe_onco, 'lab': lab_title,
                                     'parent': parent_obj})
            dir = i[0]
            researches_titles = ''
            date = i[6]
            status_set = set()
            researches_pks = []
            pacs = None
            maybe_onco = False
            parent_obj = {"iss_id": "", "parent_title": "", "parent_is_hosp": "", "parent_is_doc_refferal": ""}
            if i[13]:
                if i[21]:
                    pacs = f'{DICOM_SERVER}/osimis-viewer/app/index.html?study={i[21]}'
                else:
                    pacs = search_dicom_study(int(dir))
            has_hosp = False
            if i[11]:
                has_hosp = True
            lab = set()

        if researches_titles:
            researches_titles = f'{researches_titles} | {i[5]}'
        else:
            researches_titles = i[5]

        status_val = 0
        has_descriptive = False
        if i[8] or i[9]:
            status_val = 1
        if i[7]:
            status_val = 2
        if i[1]:
            status_val = -1
        status_set.add(status_val)
        researches_pks.append(i[4])
        if i[12]:
            maybe_onco = True
        if i[20]:
            parent_obj = get_data_parent(i[20])
        last_dir = dir
        cancel = i[1]
        title_podr = i[10]
        if title_podr is None:
            title_podr = ''
        if title_podr not in lab:
            lab.add(title_podr)
        if i[14] or i[15] or i[16] or i[17] or i[18] or i[19]:
            has_descriptive = True

    status = min(status_set)
    if len(lab) > 0:
        lab_title = ', '.join(lab)
    if (req_status == 2 and status == 2) or (req_status in [3, 4] and status != -2) or (req_status == 1 and status == 1) or (req_status == 0 and status == 0):
        final_result.append({'pk': dir, 'status': status, 'researches': researches_titles, "researches_pks": researches_pks, 'date': date, 'cancel': cancel, 'checked': False,
                             'pacs': pacs, 'has_hosp': has_hosp, 'has_descriptive': has_descriptive, 'maybe_onco': maybe_onco, 'lab': lab_title,
                             'parent': parent_obj})

    res['directions'] = final_result
    return JsonResponse(res)


def get_data_parent(parent_id):
    iss_obj = Issledovaniya.objects.get(pk=parent_id)
    research_title = iss_obj.research.title
    research_is_hosp = iss_obj.research.is_hospital
    research_is_doc_refferal = iss_obj.research.is_doc_refferal
    direction = iss_obj.napravleniye_id
    is_confirm = False
    if iss_obj.doc_confirmation:
        is_confirm = True

    return {"iss_id": parent_id, "pk": direction, "parent_title": research_title, "parent_is_hosp": research_is_hosp,
            "parent_is_doc_refferal": research_is_doc_refferal, "is_confirm": is_confirm}


@login_required
@group_required("Врач стационара")
def hosp_set_parent(request):
    # SQL-query
    date_end = utils.current_time()
    days_ago = SettingManager.get("days_before_hosp", default='30', default_type='i')
    date_start = (date_end + relativedelta(days=-days_ago))
    date_start = datetime.combine(date_start, dtime.min)
    date_end = datetime.combine(date_end, dtime.max)
    request_data = json.loads(request.body)
    patient_card = request_data.get("patient", -1)
    user_creater = -1
    iss_pk = None
    for_slave_hosp = False

    is_service = False
    services = [-1]
    is_parent = False

    result_sql = get_history_dir(date_start, date_end, patient_card, user_creater, services, is_service, iss_pk, is_parent, for_slave_hosp)
    # napravleniye_id, cancel, iss_id, tubesregistration_id, res_id, res_title, date_create,
    # doc_confirmation_id, time_recive, ch_time_save, podr_title, is_hospital, maybe_onco, can_has_pacs,
    # is_slave_hospital, is_treatment, is_stom, is_doc_refferal, is_paraclinic, is_microbiology, parent_id, study_instance_uid
    res = {"directions": []}

    for i in result_sql:
        if i[11]:
            if forbidden_edit_dir(i[0]):
                continue
            researche_title = i[5]
            dir = i[0]
            iss_id = i[2]
            date_create = i[6]
            res['directions'].append({'dir_num': dir, 'iss_id': iss_id, 'researche_titles': researche_title, 'date': date_create})

    return JsonResponse(res)


@login_required
@group_required("Врач стационара")
def update_parent(request):
    request_data = json.loads(request.body)
    parent = request_data.get("parent")
    slave_dirs = request_data.get("slave_dirs", [])
    parent_iss = None
    if parent > -1:
        parent_iss = Issledovaniya.objects.get(pk=parent)
        Napravleniya.objects.filter(pk__in=slave_dirs).update(parent=parent_iss)
    if parent == -1:
        Napravleniya.objects.filter(pk__in=slave_dirs).update(parent=None)

    dir_parent = ""
    if parent_iss:
        dir_parent = parent_iss.napravleniye.pk

    for i in slave_dirs:
        Log(key=i, type=5003, body=json.dumps({"dir": i, "parent_dir": dir_parent, "parent_iss_id": parent}),
            user=request.user.doctorprofile).save()

    result = {"ok": True, "message": ""}

    return JsonResponse(result)


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
        Log(key=pk, type=5002, body="да" if direction.cancel else "нет", user=request.user.doctorprofile).save()
    return JsonResponse(response)


@login_required
def directions_results(request):
    result = {"ok": False,
              "desc": False,
              "direction": {"pk": -1, "doc": "", "date": ""},
              "client": {},
              "full": False}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    if Napravleniya.objects.filter(pk=pk).exists():
        napr = Napravleniya.objects.get(pk=pk)
        dates = {}
        for iss in Issledovaniya.objects.filter(napravleniye=napr):
            if iss.research.desc:
                result["desc"] = True
                if not request_data.get("force", False):
                    return JsonResponse(result)
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
            result["pacs"] = None if not iss_list[0].research.podrazdeleniye or not iss_list[0].research.podrazdeleniye.can_has_pacs else search_dicom_study(pk)
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
            receive_datetime = None
            for i in Issledovaniya.objects.filter(napravleniye=n).filter(
                Q(research__is_paraclinic=True) | Q(research__is_doc_refferal=True) | Q(
                    research__is_microbiology=True)).distinct():
                researches.append({"title": i.research.title,
                                   "department": ""
                                   if not i.research.podrazdeleniye
                                   else i.research.podrazdeleniye.get_title(),
                                   "is_microbiology": i.research.is_microbiology,
                                   "comment": i.localization.title if i.localization else i.comment})
                if i.research.is_microbiology:
                    has_microbiology = True
                    tubes.append({
                        "title": i.research.microbiology_tube.title,
                        "color": i.research.microbiology_tube.color,
                    })

            if has_microbiology:
                receive_datetime = None if not n.time_microbiology_receive else strdatetime(n.time_microbiology_receive)

            response["direction_data"] = {
                "date": strdate(n.data_sozdaniya),
                "client": n.client.individual.fio(full=True),
                "card": n.client.number_with_type(),
                "diagnos": n.diagnos,
                "tubes": tubes,
                "has_microbiology": has_microbiology,
                "receive_datetime": receive_datetime,
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
        if Issledovaniya.objects.filter(Q(research__is_paraclinic=True) | Q(research__is_doc_refferal=True)).exists():
            if not cancel:
                n.visit_date = timezone.now()
                n.visit_who_mark = request.user.doctorprofile
                n.save()
                cdid, ctime, ctp, rt = get_reset_time_vars(n)
                allow_reset_confirm = bool(((ctime - ctp < rt and cdid == request.user.doctorprofile.pk) or request.user.is_superuser or "Сброс подтверждений результатов" in [
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
                allow_reset_confirm = bool(((ctime - ctp < rt and cdid == request.user.doctorprofile.pk) or request.user.is_superuser or "Сброс подтверждений результатов" in [
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


@group_required("Получатель биоматериала микробиологии")
def directions_receive_material(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    cancel = request_data.get("cancel", False)
    dn = Napravleniya.objects.filter(pk=pk)
    f = False
    if dn.exists():
        n = dn[0]
        if not cancel:
            if not n.time_microbiology_receive:
                n.time_microbiology_receive = timezone.now()
                n.doc_microbiology_receive = request.user.doctorprofile
                n.save()
                response["ok"] = True
                response["receive_datetime"] = strdatetime(n.time_microbiology_receive)
            else:
                response["message"] = "Материал уже принят"
        else:
            n.time_microbiology_receive = None
            n.doc_microbiology_receive = None
            n.save()
            response["ok"] = True
            response["receive_datetime"] = None
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


@group_required("Врач параклиники", "Посещения по направлениям", "Врач консультаций")
def directions_recv_journal(request):
    response = {"data": []}
    request_data = json.loads(request.body)
    date_start, date_end = try_parse_range(request_data["date"])
    for v in Napravleniya.objects.filter(time_microbiology_receive__range=(date_start, date_end,),
                                         doc_microbiology_receive=request.user.doctorprofile).order_by("-time_microbiology_receive"):
        tubes = []
        for i in Issledovaniya.objects.filter(napravleniye=v, research__microbiology_tube__isnull=False):
            tube = i.research.microbiology_tube
            tubes.append({
                "color": tube.color,
                "title": tube.title,
            })
        response["data"].append({
            "pk": v.pk,
            "client": v.client.individual.fio(full=True),
            "datetime": strdatetime(v.time_microbiology_receive),
            "tubes": tubes,
        })
    return JsonResponse(response)


@login_required
def directions_last_result(request):
    response = {"ok": False, "data": {}, "type": "result", "has_last_result": False}
    request_data = json.loads(request.body)
    individual = request_data.get("individual", -1)
    research = request_data.get("research", -1)
    parent_iss = request_data.get("parentIss", None)
    filter = {
        "napravleniye__client__individual__pk": individual,
        "research__pk": research,
    }
    if parent_iss:
        filter["napravleniye__parent__pk"] = parent_iss
    i = Issledovaniya.objects.filter(**filter,
                                     time_confirmation__isnull=False).order_by("-time_confirmation").first()
    u = Issledovaniya.objects.filter(**filter,
                                     time_confirmation__isnull=True).order_by(
        "-napravleniye__data_sozdaniya").first()
    v = Issledovaniya.objects.filter(**filter,
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
                            res.append((r.field.get_title(force_type=r.get_field_type()) + ": " if r.field.get_title(force_type=r.get_field_type()) != "" else "") + r.value)

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
                                                   issledovaniye__time_confirmation__range=(date_start, date_end)):
                        if r.value == "":
                            continue
                        is_norm, ref_sign = r.get_is_norm()
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


@group_required("Врач параклиники", "Врач консультаций", "Врач стационара", "t, ad, p")
def directions_paraclinic_form(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1) or -1
    force_form = request_data.get("force", False)
    if pk >= 4600000000000:
        pk -= 4600000000000
        pk //= 10
    add_fr = {}
    f = False
    g = [str(x) for x in request.user.groups.all()]
    if not request.user.is_superuser:
        add_fr = dict(research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)

    dn = Napravleniya.objects \
        .filter(pk=pk) \
        .select_related('client', 'client__base', 'client__individual', 'doc', 'doc__podrazdeleniye') \
        .prefetch_related(
            Prefetch(
                'issledovaniya_set',
                queryset=(
                    Issledovaniya.objects.all() if force_form else Issledovaniya.objects.filter(Q(research__is_paraclinic=True, **add_fr) | Q(research__is_doc_refferal=True)
                                                                                                | Q(research__is_treatment=True) | Q(research__is_stom=True) | Q(
                        research__is_microbiology=True))
                ).select_related('research', 'research__microbiology_tube', 'research__podrazdeleniye')
                .prefetch_related(
                    Prefetch(
                        'research__paraclinicinputgroups_set',
                        queryset=ParaclinicInputGroups.objects.filter(hide=False).order_by("order").prefetch_related(
                            Prefetch(
                                'paraclinicinputfield_set',
                                queryset=ParaclinicInputField.objects.filter(hide=False).order_by("order")
                            )
                        )
                    ),
                    Prefetch(
                        'recipe_set',
                        queryset=Recipe.objects.all().order_by('pk')
                    ),
                )
                .distinct()
            )
        )

    if dn.exists():
        d = dn[0]
        df = d.issledovaniya_set.all()

        if df.exists():
            response["ok"] = True
            response["has_doc_referral"] = False
            response["has_paraclinic"] = False
            response["has_microbiology"] = False
            response["card_internal"] = d.client.base.internal_type
            response["patient"] = {
                "fio_age": d.client.individual.fio(full=True),
                "age": d.client.individual.age(),
                "sex": d.client.individual.sex.lower(),
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
                "fin_source": d.fin_title,
                "fin_source_id": d.istochnik_f_id,
                "tube": None,
                "amd": d.amd_status,
                "amd_number": d.amd_number
            }

            response["researches"] = []
            i: Issledovaniya
            for i in df:
                if i.research.is_doc_refferal:
                    response["has_doc_referral"] = True
                if i.research.is_paraclinic:
                    response["has_paraclinic"] = True
                if i.research.is_microbiology and not response["has_microbiology"]:
                    response["has_microbiology"] = True
                    if i.research.microbiology_tube:
                        response["direction"]["tube"] = {
                            "type": i.research.microbiology_tube.title,
                            "color": i.research.microbiology_tube.color,
                            "get": i.get_visit_date(force=True),
                            "n": d.microbiology_n,
                        }
                transfer_d = Napravleniya.objects.filter(parent_auto_gen=i, cancel=False).first()
                forbidden_edit = forbidden_edit_dir(d.pk)
                more_forbidden = "Врач параклиники" not in g and "Врач консультаций" not in g and "Врач стационара" not in g and "t, ad, p" in g
                iss = {
                    "pk": i.pk,
                    "research": {
                        "title": i.research.title,
                        "version": i.pk * 10000,
                        "is_paraclinic": i.research.is_paraclinic,
                        "is_doc_refferal": i.research.is_doc_refferal,
                        "is_microbiology": i.research.is_microbiology,
                        "is_treatment": i.research.is_treatment,
                        "is_stom": i.research.is_stom,
                        "wide_headers": i.research.wide_headers,
                        "comment": i.localization.title if i.localization else i.comment,
                        "groups": [],
                        "can_transfer": i.research.can_transfer,
                        "is_extract": i.research.is_extract,
                        "transfer_direction": None if not transfer_d else transfer_d.pk,
                        "transfer_direction_iss": [] if not transfer_d else [r.research.title for r in
                                                                             Issledovaniya.objects.filter(
                                                                                 napravleniye=transfer_d.pk)
                                                                             ],
                        "r_type": i.research.r_type,
                    },
                    "pacs": None if not i.research.podrazdeleniye or not i.research.podrazdeleniye.can_has_pacs else
                    search_dicom_study(d.pk),
                    "examination_date": i.get_medical_examination(),
                    "templates": [],
                    "saved": i.time_save is not None,
                    "confirmed": i.time_confirmation is not None,
                    "allow_reset_confirm": i.allow_reset_confirm(request.user) and (not more_forbidden or TADP in i.research.title),
                    "more": [x.research_id for x in Issledovaniya.objects.filter(parent=i)],
                    "sub_directions": [],
                    "recipe": [],
                    "lab_comment": i.lab_comment,
                    "forbidden_edit": forbidden_edit,
                    "maybe_onco": i.maybe_onco,
                }

                if i.research.is_microbiology:
                    iss["microbiology"] = {
                        "bacteries": [],
                        "conclusion": i.microbiology_conclusion,
                    }

                    for br in MicrobiologyResultCulture.objects.filter(issledovaniye=i):
                        bactery = {
                            "resultPk": br.pk,
                            "bacteryPk": br.culture.pk,
                            "bacteryTitle": br.culture.title,
                            "bacteryGroupTitle": br.culture.group_culture.title if br.culture.group_culture else '',
                            "koe": br.koe,
                            "antibiotics": [],
                            "selectedGroup": {},
                            "selectedAntibiotic": {},
                            "selectedSet": {},
                        }

                        for ar in MicrobiologyResultCultureAntibiotic.objects.filter(result_culture=br):
                            bactery["antibiotics"].append({
                                "pk": ar.antibiotic.pk,
                                "resultPk": ar.pk,
                                "sri": ar.sensitivity,
                                "dia": ar.dia,
                            })

                        iss["microbiology"]["bacteries"].append(bactery)

                if not force_form:
                    for sd in Napravleniya.objects.filter(parent=i):
                        iss["sub_directions"].append({
                            "pk": sd.pk,
                            "cancel": sd.cancel,
                            "researches": [
                                x.research.title for x in Issledovaniya.objects.filter(napravleniye=sd)
                            ],
                        })

                if not force_form and iss["research"]["is_doc_refferal"]:
                    iss = {
                        **iss,
                        "purpose": i.purpose_id,
                        "first_time": i.first_time,
                        "result": i.result_reception_id,
                        "outcome": i.outcome_illness_id,
                        "diagnos": i.diagnos,

                        "purpose_list": [{"pk": x.pk, "title": x.title} for x in
                                         VisitPurpose.objects.filter(hide=False).order_by("pk")],
                        "result_list": [{"pk": x.pk, "title": x.title} for x in
                                        ResultOfTreatment.objects.filter(hide=False).order_by("pk")],
                        "outcome_list": [{"pk": x.pk, "title": x.title} for x in
                                         Outcomes.objects.filter(hide=False).order_by("pk")]
                    }

                    if not force_form:
                        for rp in i.recipe_set.all():
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

                for group in i.research.paraclinicinputgroups_set.all():
                    g = {"pk": group.pk, "order": group.order, "title": group.title, "show_title": group.show_title,
                         "hide": group.hide, "display_hidden": False, "fields": [], "visibility": group.visibility}
                    for field in group.paraclinicinputfield_set.all():
                        result_field: ParaclinicResult = ParaclinicResult.objects.filter(issledovaniye=i, field=field).first()
                        field_type = field.field_type if not result_field else result_field.get_field_type()
                        g["fields"].append({
                            "pk": field.pk,
                            "order": field.order,
                            "lines": field.lines,
                            "title": field.title,
                            "hide": field.hide,
                            "values_to_input": ([] if not field.required or field_type not in [10, 12] else
                                                ['- Не выбрано']) + json.loads(field.input_templates),
                            "value": ((field.default_value if field_type not in [3, 11, 13, 14] else '') if not result_field else result_field.value) if field_type not in [1, 20] else
                            (get_default_for_field(field_type) if not result_field else result_field.value),
                            "field_type": field_type,
                            "default_value": field.default_value,
                            "visibility": field.visibility,
                            "required": field.required,
                            "helper": field.helper,
                        })
                    iss["research"]["groups"].append(g)
                response["researches"].append(iss)
            if not force_form and response["has_doc_referral"]:
                response["anamnesis"] = d.client.anamnesis_of_life

                d1, d2 = start_end_year()
                disp_data = sql_func.dispensarization_research(d.client.individual.sex,
                                                               d.client.individual.age_for_year(),
                                                               d.client_id, d1, d2)
                status_disp = 'finished'
                if not disp_data:
                    status_disp = 'notneed'
                else:
                    for i in disp_data:
                        if not i[4]:
                            status_disp = 'need'
                            break
                response["status_disp"] = status_disp
                response["disp_data"] = disp_data

            f = True
    if not f:
        response["message"] = "Направление не найдено"
    return JsonResponse(response)


def get_default_for_field(field_type):
    if field_type == 1:
        return strfdatetime(current_time(), '%Y-%m-%d')
    if field_type == 20:
        return strfdatetime(current_time(), '%H:%M')
    return ''


@group_required("Врач параклиники", "Врач консультаций", "Врач стационара", "t, ad, p")
def directions_anesthesia_result(request):
    response = {"ok": False, "message": ""}
    rb = json.loads(request.body)
    temp_result = rb.get("temp_result", {})
    research_data = rb.get("research_data", {})
    result = ParaclinicResult.anesthesia_value_save(research_data['iss_pk'], research_data['field_pk'], temp_result)
    if result:
        response = {"ok": True, "message": ""}
    return JsonResponse(response)


@group_required("Врач параклиники", "Врач консультаций", "Врач стационара", "t, ad, p")
def directions_anesthesia_load(request):
    rb = json.loads(request.body)
    research_data = rb.get("research_data", '')
    if research_data is None:
        return JsonResponse({'data': 'Ошибка входных данных'})
    anesthesia_data = ParaclinicResult.anesthesia_value_get(research_data['iss_pk'], research_data["field_pk"])
    if anesthesia_data and len(anesthesia_data) > 0:
        tb_data = []
        result = eval(anesthesia_data)
        cols_template = ['' for i in range(len(result['times']) + 1)]

        times_row = [' ']
        times_row.extend(result['times'])

        def made_structure(type):
            for i in result[type]:
                current_param = ['' for i in cols_template]
                current_param[0] = i
                for k, v in result[i].items():
                    if k in times_row:
                        index = times_row.index(k)
                        current_param[index] = v
                tb_data.append(current_param)
        tb_data.append(times_row)
        made_structure('patient_params')
        made_structure('potent_drugs')
        made_structure('narcotic_drugs')

    return JsonResponse({'data': tb_data})


@group_required("Врач параклиники", "Врач консультаций", "Врач стационара", "t, ad, p")
def directions_paraclinic_result(request):
    response = {"ok": False, "message": ""}
    rb = json.loads(request.body)
    request_data = rb.get("data", {})
    pk = request_data.get("pk", -1)
    stationar_research = request_data.get("stationar_research", -1)
    with_confirm = rb.get("with_confirm", False)
    visibility_state = rb.get("visibility_state", {})
    v_g = visibility_state.get("groups", {})
    v_f = visibility_state.get("fields", {})
    recipe = request_data.get("recipe", [])
    tube = request_data.get("direction", {}).get("tube", {})
    force = rb.get("force", False)
    diss = Issledovaniya.objects.filter(pk=pk, time_confirmation__isnull=True)
    if force or diss.filter(Q(research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)
                            | Q(research__is_doc_refferal=True) | Q(research__is_treatment=True)
                            | Q(research__is_stom=True)).exists() or request.user.is_staff:
        iss = Issledovaniya.objects.get(pk=pk)

        g = [str(x) for x in request.user.groups.all()]
        tadp = TADP in iss.research.title
        more_forbidden = "Врач параклиники" not in g and "Врач консультаций" not in g and "Врач стационара" not in g and "t, ad, p" in g

        if forbidden_edit_dir(iss.napravleniye_id) or (more_forbidden and not tadp):
            response["message"] = "Редактирование запрещено"
            return JsonResponse(response)

        if tube:
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
                f_result.field_type = f.field_type
                f_result.save()
                if f.field_type in [16, 17] and iss.napravleniye.parent and iss.napravleniye.parent.research.is_hospital:
                    try:
                        val = json.loads(str(field["value"]))
                    except Exception:
                        val = None

                    if f.field_type == 16:
                        if with_confirm:
                            if isinstance(val, list):
                                iss.napravleniye.parent.aggregate_lab = val
                            elif isinstance(val, dict) and val.get("directions"):
                                iss.napravleniye.parent.aggregate_lab = val["directions"]
                            else:
                                iss.napravleniye.parent.aggregate_lab = None
                        else:
                            iss.napravleniye.parent.aggregate_lab = None
                    elif f.field_type == 17:
                        if with_confirm:
                            if isinstance(val, list):
                                iss.napravleniye.parent.aggregate_desc = val
                            elif isinstance(val, dict) and val.get("directions"):
                                iss.napravleniye.parent.aggregate_desc = val["directions"]
                            else:
                                iss.napravleniye.parent.aggregate_desc = None
                        else:
                            iss.napravleniye.parent.aggregate_desc = None
                    iss.napravleniye.parent.save()

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
        if iss.research.is_microbiology:
            mb = request_data.get("microbiology", {})
            if mb:
                iss.microbiology_conclusion = mb.get('conclusion')

                has_bacteries = []
                has_anti = []

                for br in mb.get('bacteries', []):
                    if br['resultPk'] == -1:
                        bactery = MicrobiologyResultCulture(
                            issledovaniye=iss,
                            culture_id=br['bacteryPk'],
                            koe=br['koe']
                        )
                    else:
                        bactery = MicrobiologyResultCulture.objects.get(pk=br['resultPk'])
                        bactery.culture_id = br['bacteryPk']
                        bactery.koe = br['koe']
                    bactery.save()
                    has_bacteries.append(bactery.pk)

                    for ar in br['antibiotics']:
                        if ar['resultPk'] == -1:
                            anti = MicrobiologyResultCultureAntibiotic(
                                result_culture=bactery,
                                antibiotic_id=ar['pk'],
                                sensitivity=ar['sri'],
                                dia=ar['dia']
                            )
                        else:
                            anti = MicrobiologyResultCultureAntibiotic.objects.get(pk=ar['resultPk'])
                            anti.antibiotic_id = ar['pk']
                            anti.sensitivity = ar['sri']
                            anti.dia = ar['dia']
                        anti.save()
                        has_anti.append(anti.pk)
                MicrobiologyResultCulture.objects.filter(issledovaniye=iss).exclude(pk__in=has_bacteries).delete()
                MicrobiologyResultCultureAntibiotic.objects.filter(result_culture__issledovaniye=iss).exclude(pk__in=has_anti).delete()

        iss.purpose_id = request_data.get("purpose")
        iss.first_time = request_data.get("first_time", False)
        iss.result_reception_id = request_data.get("result")
        iss.outcome_illness_id = request_data.get("outcome")
        iss.maybe_onco = request_data.get("maybe_onco", False)
        iss.diagnos = request_data.get("diagnos", "")
        iss.lab_comment = request_data.get("lab_comment", "")

        if stationar_research != -1:
            iss.gen_direction_with_research_after_confirm_id = stationar_research

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
        response["amd"] = iss.napravleniye.amd_status
        response["amd_number"] = iss.napravleniye.amd_number
        Log(key=pk, type=13, body="", user=request.user.doctorprofile).save()
        if with_confirm:
            iss.gen_after_confirm(request.user)
            transfer_d = Napravleniya.objects.filter(parent_auto_gen=iss, cancel=False).first()
            response["transfer_direction"] = None if not transfer_d else transfer_d.pk
            response["transfer_direction_iss"] = [] if not transfer_d else [r.research.title for r in
                                                                            Issledovaniya.objects.filter(
                                                                                napravleniye=transfer_d.pk)
                                                                            ]
            if iss.maybe_onco:
                card_pk = iss.napravleniye.client.pk
                dstart_onco = strdate(current_time(only_date=True))
                dispensery_onco = json.dumps(
                    {'card_pk': card_pk, 'pk': -1, 'data': {'date_start': dstart_onco, 'date_end': '', 'why_stop': '', 'close': False, 'diagnos': 'U999 Онкоподозрение', 'illnes': ''}})
                dispensery_obj = HttpRequest()
                dispensery_obj._body = dispensery_onco
                dispensery_obj.user = request.user
                save_dreg(dispensery_obj)

            Log(key=pk, type=14, body="", user=request.user.doctorprofile).save()
        forbidden_edit = forbidden_edit_dir(iss.napravleniye_id)
        response["forbidden_edit"] = forbidden_edit or more_forbidden
        response["soft_forbidden"] = not forbidden_edit
    return JsonResponse(response)


@group_required("Врач параклиники", "Врач консультаций", "Врач стационара", "t, ad, p")
def directions_paraclinic_confirm(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("iss_pk", -1)
    diss = Issledovaniya.objects.filter(pk=pk, time_confirmation__isnull=True)
    if diss.filter(Q(research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)
                   | Q(research__is_doc_refferal=True) | Q(research__is_treatment=True)
                   | Q(research__is_slave_hospital=True)
                   | Q(research__is_stom=True)).exists():
        iss = Issledovaniya.objects.get(pk=pk)
        g = [str(x) for x in request.user.groups.all()]
        tadp = TADP in iss.research.title
        more_forbidden = "Врач параклиники" not in g and "Врач консультаций" not in g and "Врач стационара" not in g and "t, ad, p" in g
        if forbidden_edit_dir(iss.napravleniye_id) or (more_forbidden and not tadp):
            response["message"] = "Редактирование запрещено"
            return JsonResponse(response)
        t = timezone.now()
        if not iss.napravleniye.visit_who_mark or not iss.napravleniye.visit_date:
            iss.napravleniye.visit_who_mark = request.user.doctorprofile
            iss.napravleniye.visit_date = t
            iss.napravleniye.save()
        iss.doc_confirmation = request.user.doctorprofile
        iss.time_confirmation = t
        iss.save()
        iss.gen_after_confirm(request.user)
        for i in Issledovaniya.objects.filter(parent=iss):
            i.doc_confirmation = request.user.doctorprofile
            i.time_confirmation = t
            i.save()
        response["ok"] = True
        response["amd"] = iss.napravleniye.amd_status
        response["amd_number"] = iss.napravleniye.amd_number
        response["forbidden_edit"] = forbidden_edit_dir(iss.napravleniye_id)
        Log(key=pk, type=14, body=json.dumps(request_data), user=request.user.doctorprofile).save()
    return JsonResponse(response)


@group_required("Врач параклиники", "Сброс подтверждений результатов", "Врач консультаций",
                "Врач стационара", "Сброс подтверждения переводного эпикриза", "Сброс подтверждения выписки", "t, ad, p")
def directions_paraclinic_confirm_reset(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("iss_pk", -1)

    if Issledovaniya.objects.filter(pk=pk).exists():
        iss = Issledovaniya.objects.get(pk=pk)
        is_transfer = iss.research.can_transfer
        is_extract = iss.research.is_extract

        g = [str(x) for x in request.user.groups.all()]
        tadp = TADP in iss.research.title
        more_forbidden = "Врач параклиники" not in g and "Врач консультаций" not in g and "Врач стационара" not in g and "t, ad, p" in g

        allow_reset = iss.allow_reset_confirm(request.user) and (not more_forbidden or tadp)

        if not allow_reset:
            response["message"] = "Редактирование запрещено. Запросите сброс подтверждения у администратора"
            return JsonResponse(response)

        if allow_reset:
            predoc = {"fio": iss.doc_confirmation.get_fio(), "pk": iss.doc_confirmation_id,
                      "direction": iss.napravleniye_id}
            iss.doc_confirmation = iss.time_confirmation = None
            iss.save()
            transfer_d = Napravleniya.objects.filter(parent_auto_gen=iss, cancel=False).first()
            if transfer_d:
                transfer_d.cancel = True
                transfer_d.save()
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
            response["message"] = "Сброс подтверждения разрешен в течении %s минут" % (str(SettingManager.get("lab_reset_confirm_time_min")))
        response["amd"] = iss.napravleniye.amd_status
        response["amd_number"] = iss.napravleniye.amd_number
        response["is_transfer"] = is_transfer
        response["is_extract"] = is_extract
        if is_transfer:
            response["forbidden_edit"] = forbidden_edit_dir(iss.napravleniye_id)
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
                Q(issledovaniya__time_save__range=(date_start, date_end))).order_by("-issledovaniya__time_save", "-issledovaniya__time_confirmation"):
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
            "all_saved": True,
            "amd": direction.amd_status,
            "amd_number": direction.amd_number,
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
    filtered = Issledovaniya.objects.filter(time_confirmation__isnull=False,
                                            research=iss.research,
                                            napravleniye__client__individual=iss.napravleniye.client.individual)

    is_same_parent = request_data.get("isSameParent", False)

    if is_same_parent:
        filtered = filtered.filter(napravleniye__parent=iss.napravleniye.parent)

    for i in filtered.order_by('-time_confirmation').exclude(pk=request_data["pk"]):
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


@login_required
def last_fraction_result(request):
    request_data = json.loads(request.body)
    client_pk = request_data["clientPk"]
    fraction_pk = int(request_data["fractionPk"])
    rows = get_fraction_result(client_pk, fraction_pk)
    result = None
    if rows:
        row = rows[0]
        result = {
            "direction": row[1],
            "date": row[4],
            "value": row[5]
        }
    return JsonResponse({"result": result})


@login_required
def last_field_result(request):
    request_data = json.loads(request.body)
    client_pk = request_data["clientPk"]
    field_pk = int(request_data["fieldPk"])
    rows = get_field_result(client_pk, field_pk)
    result = None
    if rows:
        row = rows[0]
        value = row[5]
        match = re.fullmatch(r'\d{4}-\d\d-\d\d', value)
        if match:
            value = normalize_date(value)
        result = {
            "direction": row[1],
            "date": row[4],
            "value": value
        }
    return JsonResponse({"result": result})


@group_required("Врач параклиники", "Врач консультаций")
def send_amd(request):
    request_data = json.loads(request.body)
    for direction in Napravleniya.objects.filter(pk__in=request_data["pks"]):
        if direction.amd_status in ['error', 'need']:
            direction.need_resend_amd = True
            direction.amd_number = None
            direction.error_amd = False
            direction.save()
    return JsonResponse({"ok": True})


@group_required("Управление отправкой в АМД")
def reset_amd(request):
    request_data = json.loads(request.body)
    for direction in Napravleniya.objects.filter(pk__in=request_data["pks"]):
        direction.need_resend_amd = False
        direction.amd_number = None
        direction.error_amd = False
        direction.save()
    return JsonResponse({"ok": True})


def purposes(request):
    result = [
        {"pk": "NONE", "title": " – Не выбрано"}
    ]
    for p in Napravleniya.PURPOSES:
        result.append({
            "pk": p[0],
            "title": p[1],
        })
    return JsonResponse({"purposes": result})


def external_organizations(request):
    result = [
        {"pk": "NONE", "title": " – Не выбрано"},
    ]
    for e in ExternalOrganization.objects.filter(hide=False).order_by('pk'):
        result.append({
            "pk": e.pk,
            "title": e.title,
        })
    return JsonResponse({"organizations": result})
