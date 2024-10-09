import collections
import itertools
from decimal import Decimal
import re
from typing import Optional

import bleach
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from django.http import JsonResponse
import simplejson as json
from django.utils import dateformat, timezone
from django.utils import datetime_safe

from appconf.manager import SettingManager
from barcodes.views import tubes
from directions.models import TubesRegistration, Issledovaniya, Napravleniya, Result, IssledovaniyaFiles
from directions.sql_func import get_tube_registration
from directory.models import Fractions, Researches, Unit
from ftp_orders.main import push_result
from laboratory.decorators import group_required
from laboratory.settings import FTP_SETUP_TO_SEND_HL7_BY_RESEARCHES
from laboratory.utils import strdate, strfdatetime
from podrazdeleniya.models import Podrazdeleniya
from rmis_integration.client import Client
from slog.models import Log
from users.models import DoctorProfile
from utils.dates import try_parse_range


@login_required
def fractions(request):
    request_data = json.loads(request.body)
    pk = int(request_data['pk'])
    research = Researches.objects.get(pk=pk)
    fractions_list = []
    for f in Fractions.objects.filter(research=research).order_by("sort_weight"):
        u = f.get_unit()
        fractions_list.append(
            {
                "pk": f.pk,
                "title": f.title,
                "units": f.units,
                "unit": u.pk if u else None,
                "fsli": f.get_fsli_code(),
            }
        )
    return JsonResponse({"fractions": fractions_list, "title": research.get_title(), "actualPeriod": research.actual_period_result})


@login_required
def units(request):
    rows = Unit.objects.filter(hide=False).order_by('title').values('pk', 'code', 'title', 'short_title')
    rows = [{'id': x['pk'], 'label': f"{x['short_title']} — {x['title']} – {x['code']}"} for x in rows]
    return JsonResponse(
        {
            "rows": rows,
        }
    )


@login_required
def save_fsli(request):
    request_data = json.loads(request.body)
    fractions = request_data['fractions']
    for fd in fractions:
        f = Fractions.objects.get(pk=fd['pk'])
        nf = fd['fsli'].strip() or None
        nu = fd.get('unit')
        if nf != f.get_fsli_code():
            f.fsli = nf
            f.save(update_fields=['fsli'])

        if nu != f.unit_id:
            f.unit_id = nu
            f.save(update_fields=['unit'])
    research = Researches.objects.filter(pk=request_data['pk']).first()
    research.actual_period_result = int(request_data['actualPeriod'])
    research.save()

    return JsonResponse({"ok": True})


def fraction(request):
    request_data = json.loads(request.body)
    pk = request_data['pk'] or -1
    if Fractions.objects.filter(pk=pk).exists():
        f = Fractions.objects.get(pk=pk)
        ft = f.title
        rt = f.research.get_title()
        return JsonResponse({"title": f"{rt} – {ft}" if ft != rt and ft else rt})

    return JsonResponse({"title": None})


@login_required
def laboratories(request):
    rows = []
    active = -1
    r: Podrazdeleniya
    for r in Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY).exclude(title="Внешние организации").order_by("title"):
        rows.append(
            {
                "pk": r.pk,
                "title": r.get_title(),
            }
        )
        if active == -1 or request.user.doctorprofile.podrazdeleniye_id == r.pk:
            active = r.pk
    return JsonResponse({"rows": rows, "active": active})


@login_required
@group_required("Врач-лаборант", "Лаборант")
def ready(request):
    request_data = json.loads(request.body)
    dates = request_data['date_range']
    laboratory_pk = request_data.get('laboratory', -1)
    result = {"tubes": [], "directions": []}

    date_start, date_end = try_parse_range(*dates)
    dates_cache = {}
    tubes = set()
    dirs = set()

    tlist = TubesRegistration.objects.filter(
        doc_recive__isnull=False,
        time_recive__range=(date_start, date_end),
        issledovaniya__time_confirmation__isnull=True,
        issledovaniya__research__podrazdeleniye_id=laboratory_pk,
        issledovaniya__isnull=False,
    ).filter(Q(issledovaniya__napravleniye__hospital_id=request.user.doctorprofile.hospital_id) | Q(issledovaniya__napravleniye__hospital__isnull=True))

    for tube in tlist.distinct().prefetch_related('issledovaniya_set__napravleniye').select_related('type', 'type__tube'):
        direction = None
        if tube.number not in tubes:
            if not direction:
                direction = tube.issledovaniya_set.first().napravleniye
            if tube.time_recive.date() not in dates_cache:
                dates_cache[tube.time_recive.date()] = dateformat.format(tube.time_recive, 'd.m.y')
            tubes.add(tube.number)
            dicttube = {
                "pk": tube.number,
                "direction": direction.pk,
                "date": dates_cache[tube.time_recive.date()],
                "tube": {"title": tube.type.tube.title, "color": tube.type.tube.color},
            }
            result["tubes"].append(dicttube)

        if tube.issledovaniya_set.first().napravleniye_id not in dirs:
            if not direction:
                direction = tube.issledovaniya_set.first().napravleniye
            if direction.data_sozdaniya.date() not in dates_cache:
                dates_cache[direction.data_sozdaniya.date()] = dateformat.format(direction.data_sozdaniya, 'd.m.y')
            dirs.add(direction.pk)
            dictdir = {"pk": direction.pk, "date": dates_cache[direction.data_sozdaniya.date()]}
            result["directions"].append(dictdir)

    result["tubes"].sort(key=lambda k: k['pk'])
    result["directions"].sort(key=lambda k: k['pk'])
    return JsonResponse(result)


@login_required
@group_required("Врач-лаборант", "Лаборант")
def search(request):
    result = {"ok": False, "msg": None}

    request_data = json.loads(request.body)

    direction: Optional[Napravleniya] = None
    pk = request_data["q"].strip()
    laboratory_pk = request_data["laboratory"]
    t = request_data["mode"]
    doc = request.user.doctorprofile
    doc_pk = request.user.doctorprofile.pk
    if pk.isdigit():
        issledovaniya = []
        labs = []
        labs_titles = []
        all_confirmed = True
        all_saved = True
        pk = int(pk)
        if pk >= 4600000000000:
            pk -= 4600000000000
            pk //= 10
            t = "direction"
        if t == "tube":
            iss = Issledovaniya.objects.filter(tubes__number=pk)
            if iss.count() != 0:
                direction = iss.first().napravleniye
            iss = iss.filter(research__podrazdeleniye__pk=laboratory_pk)
        else:
            try:
                direction = Napravleniya.objects.get(pk=pk)
                iss = Issledovaniya.objects.filter(napravleniye__pk=pk, research__podrazdeleniye__pk=laboratory_pk)
            except Napravleniya.DoesNotExist:
                direction = None
                iss = None
        user_groups = [str(x) for x in request.user.groups.all()]
        contol_hosp = False
        if "Направления-все МО" not in user_groups:
            contol_hosp = True
        if direction and direction.hospital and direction.hospital != doc.hospital and contol_hosp:
            direction = None
            iss = None
        mnext = False
        for i in Issledovaniya.objects.filter(napravleniye=direction).select_related('research', 'research__podrazdeleniye'):
            po = i.research.podrazdeleniye
            p = "" if not po else po.title
            if p not in labs_titles and po:
                labs_titles.append(p)
                labs.append({"pk": po.pk, "title": p, "islab": po.p_type == 2})
            if po and not i.research.is_paraclinic and not i.research.is_doc_refferal:
                mnext = True
        if iss and iss.count() > 0:
            if not mnext:
                result["msg"] = f"Направление {pk} не предназначено для лаборатории! Проверьте назначения и номер"
            else:
                groups = {}
                cnt = 0
                researches_chk = []
                for issledovaniye in (
                    iss.order_by("deferred", "-doc_save", "-doc_confirmation", "tubes__number", "research__sort_weight")
                    .prefetch_related('tubes', 'result_set')
                    .select_related('research', 'doc_save')
                ):
                    if True:
                        if issledovaniye.pk in researches_chk:
                            continue
                        researches_chk.append(issledovaniye.pk)

                        tubes_list = issledovaniye.tubes.exclude(doc_recive__isnull=True).all()

                        not_received_tubes_list = [str(x.number) for x in issledovaniye.tubes.exclude(doc_recive__isnull=False).all().order_by("number")]

                        not_received_why = [x.notice for x in issledovaniye.tubes.exclude(doc_recive__isnull=False).all().order_by("number") if x.notice]

                        saved = True
                        confirmed = True
                        doc_save_fio = ""
                        doc_save_id = -1
                        current_doc_save = -1
                        isnorm = "unknown"

                        if not issledovaniye.doc_save:
                            saved = False
                        else:
                            doc_save_id = issledovaniye.doc_save_id
                            doc_save_fio = issledovaniye.doc_save.get_fio()
                            if doc_save_id == doc_pk:
                                current_doc_save = 1
                            else:
                                current_doc_save = 0
                            isnorm = "normal"
                            if issledovaniye.result_set.count() > 0:
                                if any([x.get_is_norm()[0] == "not_normal" for x in issledovaniye.result_set.all()]):
                                    isnorm = "not_normal"
                                elif any([x.get_is_norm()[0] == "maybe" for x in issledovaniye.result_set.all()]):
                                    isnorm = "maybe"

                        if not issledovaniye.time_confirmation:
                            confirmed = False
                            if all_confirmed and not issledovaniye.deferred:
                                all_confirmed = False
                        if all_saved and not issledovaniye.time_save and not issledovaniye.deferred:
                            all_saved = False
                        tb = ','.join(str(v.number) for v in tubes_list)

                        if tb not in groups.keys():
                            cnt += 1
                            groups[tb] = cnt
                        issledovaniya.append(
                            {
                                "pk": issledovaniye.pk,
                                "title": issledovaniye.research.title,
                                "research_pk": issledovaniye.research_id,
                                "sort": issledovaniye.research.sort_weight,
                                "saved": saved,
                                "is_norm": isnorm,
                                "confirmed": confirmed,
                                "status_key": str(saved) + str(confirmed) + str(issledovaniye.deferred and not confirmed),
                                "not_received_tubes": ", ".join(not_received_tubes_list),
                                "not_received_why": ", ".join(not_received_why),
                                "tubes": [{"pk": x.number, "title": x.type.tube.title, "color": x.type.tube.color} for x in tubes_list],
                                "template": str(issledovaniye.research.template),
                                "deff": issledovaniye.deferred and not confirmed,
                                "doc_save_fio": doc_save_fio,
                                "doc_save_id": doc_save_id,
                                "current_doc_save": current_doc_save,
                                "allow_reset_confirm": issledovaniye.allow_reset_confirm(request.user),
                                "group": groups[tb],
                            }
                        )

                statuses = collections.defaultdict(lambda: collections.defaultdict(list))

                for d in issledovaniya:
                    statuses[d['status_key']][d['group']].append(d)
                    statuses[d['status_key']][d['group']] = sorted(statuses[d['status_key']][d['group']], key=lambda k: k['sort'])

                issledovaniya = []

                def concat(dic):
                    t = [dic[x] for x in dic.keys()]

                    return itertools.chain(*t)

                if "FalseFalseFalse" in statuses.keys():
                    issledovaniya += concat(statuses["FalseFalseFalse"])

                if "TrueFalseFalse" in statuses.keys():
                    issledovaniya += concat(statuses["TrueFalseFalse"])

                if "FalseFalseTrue" in statuses.keys():
                    issledovaniya += concat(statuses["FalseFalseTrue"])

                if "TrueFalseTrue" in statuses.keys():
                    issledovaniya += concat(statuses["TrueFalseTrue"])

                if "FalseTrueFalse" in statuses.keys():
                    issledovaniya += concat(statuses["FalseTrueFalse"])

                if "TrueTrueFalse" in statuses.keys():
                    issledovaniya += concat(statuses["TrueTrueFalse"])
        if direction:
            result["data"] = {
                "patient": {
                    "fio": direction.client.individual.fio(),
                    "sex": direction.client.individual.sex,
                    "age": direction.client.individual.age_s(direction=direction),
                    "history_num": direction.history_num,
                    "card": direction.client.number_with_type(),
                    "diagnosis": direction.diagnos,
                },
                "direction": {
                    "pk": direction.pk,
                    "imported_from_rmis": direction.imported_from_rmis,
                    "imported_org": None if not direction.imported_org else direction.imported_org.title,
                    "directioner": None if direction.imported_from_rmis or not direction.doc else direction.doc.get_full_fio(),
                    "otd": None if direction.imported_from_rmis else direction.get_doc_podrazdeleniye_title(),
                    "fin_source": None if direction.imported_from_rmis else direction.fin_title,
                    "in_rmis": direction.result_rmis_send,
                    "dirData": {
                        "client_sex": direction.client.individual.sex,
                        "client_vozrast": direction.client.individual.age_s(direction=direction),
                    },
                },
                "issledovaniya": issledovaniya,
                "labs": labs,
                "q": {"text": pk, "mode": t},
                "allConfirmed": all_confirmed,
                "allSaved": all_saved,
            }
            result["ok"] = True
    return JsonResponse(result)


@login_required
@group_required("Врач-лаборант", "Лаборант")
def form(request):
    request_data = json.loads(request.body)
    pk = request_data["pk"]
    iss: Issledovaniya = Issledovaniya.objects.prefetch_related('result_set').get(pk=pk)
    count_files = IssledovaniyaFiles.objects.filter(issledovaniye_id=iss.pk).count()
    research: Researches = Researches.objects.prefetch_related(
        Prefetch('fractions_set', queryset=Fractions.objects.all().order_by("sort_weight", "pk").prefetch_related('references_set'))
    ).get(pk=iss.research_id)
    data = {
        "pk": pk,
        "confirmed": bool(iss.time_confirmation),
        "saved": bool(iss.time_save),
        "execData": {
            "timeSave": strfdatetime(iss.time_save, '%d.%m.%Y %X') or None,
            "docSave": iss.doc_save.get_fio() if iss.doc_save else None,
            "timeConfirm": strfdatetime(iss.time_confirmation, '%d.%m.%Y %X') or None,
            "docConfirmation": iss.doc_confirmation.get_fio() if iss.doc_confirmation else None,
            "app": iss.api_app.name if iss.api_app else None,
        },
        "count_files": count_files,
        "allow_reset_confirm": iss.allow_reset_confirm(request.user),
        "research": {
            "title": research.title,
            "enabled_add_files": research.enabled_add_files,
            "can_comment": research.can_lab_result_comment,
            "no_units_and_ref": research.no_units_and_ref,
            "co_executor_mode": research.co_executor_mode or 0,
            "co_executor_title": research.co_executor_2_title,
            "template": research.template,
        },
        "result": [],
        "comment": iss.lab_comment or "",
        "laborants": (
            [
                {"id": -1, "label": 'Не выбрано'},
                *[
                    {"id": x.pk, "label": x.get_full_fio()}
                    for x in DoctorProfile.objects.filter(user__groups__name="Лаборант", podrazdeleniye__p_type=Podrazdeleniya.LABORATORY).order_by('fio')
                ],
            ]
            if SettingManager.l2('results_laborants')
            else []
        ),
        "legalAuthenticators": (
            [{"id": x.pk, "label": x.get_full_fio()} for x in DoctorProfile.objects.filter(user__groups__name="Подпись от организации").order_by('fio')]
            if SettingManager.get('legal_authenticator', default="false", default_type='b')
            else []
        ),
        "co_executor": iss.co_executor_id or -1,
        "co_executor2": iss.co_executor2_id or -1,
        "legal_authenticator": iss.legal_authenticator_id or SettingManager.get("preselected_legal_authenticator", default='-1', default_type='i') or -1,
    }

    f: Fractions
    for f in research.fractions_set.all():
        r: Optional[Result] = iss.result_set.filter(fraction=f).first()

        if not r and f.hide:
            continue

        ref_m = f.ref_m
        ref_f = f.ref_f
        if isinstance(ref_m, str):
            ref_m = json.loads(ref_m)
        if isinstance(ref_f, str):
            ref_f = json.loads(ref_f)
        av = {}

        def_ref_pk = -1 if not f.default_ref else f.default_ref_id

        for avref in f.references_set.all():
            av[avref.pk] = {
                "title": avref.title,
                "about": avref.about,
                "m": json.loads(avref.ref_m) if isinstance(avref.ref_m, str) else avref.ref_m,
                "f": json.loads(avref.ref_f) if isinstance(avref.ref_f, str) else avref.ref_f,
            }

        empty_ref = {
            "m": ref_m,
            "f": ref_f,
        }

        selected_reference = r.selected_reference if r else def_ref_pk

        current_ref = r.get_ref(full=True) if r else (empty_ref if def_ref_pk == -1 else av.get(def_ref_pk, {}))

        av[-1] = {
            "title": "Основной референс",
            "about": "",
            **empty_ref,
        }

        if selected_reference == -2:
            av[-2] = current_ref

        av[-3] = {
            "title": "Настраиваемый референс",
            "about": "",
            "m": {},
            "f": {},
        }

        data["result"].append(
            {
                "fraction": {
                    "pk": f.pk,
                    "title": f.title,
                    "units": f.get_unit_str(),
                    "render_type": f.render_type,
                    "options": f.options,
                    "formula": f.formula,
                    "type": f.variants.get_variants() if f.variants else [],
                    "type2": f.variants2.get_variants() if f.variants2 else [],
                    "references": {
                        **empty_ref,
                        "default": def_ref_pk,
                        "available": av,
                    },
                },
                "ref": current_ref,
                "selectedReference": selected_reference,
                "norm": r.get_is_norm(recalc=True)[0] if r else None,
                "value": str(r.value if r else '').replace('&lt;', '<').replace('&gt;', '>'),
                "comment": str(r.comment if r else '').replace('&lt;', '<').replace('&gt;', '>'),
            }
        )

    return JsonResponse(
        {
            "data": data,
        }
    )


@login_required
@group_required("Врач-лаборант", "Лаборант")
def save(request):
    request_data = json.loads(request.body)
    pk = request_data["pk"]
    iss: Issledovaniya = Issledovaniya.objects.get(pk=pk)
    if iss.time_confirmation:
        return JsonResponse(
            {
                "ok": False,
                "message": 'Редактирование запрещено. Результат уже подтверждён.',
            }
        )
    for t in TubesRegistration.objects.filter(issledovaniya=iss):
        if not t.rstatus():
            t.set_r(request.user.doctorprofile)
    for r in request_data["result"]:
        result_q = {"issledovaniye": iss, "fraction_id": r["fraction"]["pk"]}
        if Result.objects.filter(**result_q).exists():
            fraction_result = Result.objects.filter(**result_q).order_by("-pk")[0]
            created = False
        else:
            fraction_result = Result(**result_q)
            created = True

        value = bleach.clean(r["value"], tags=['sup', 'sub', 'br', 'b', 'i', 'strong', 'a', 'img', 'font', 'p', 'span', 'div']).replace("<br>", "<br/>")
        comment = bleach.clean(r.get('comment', ''), tags=['sup', 'sub', 'br', 'b', 'i', 'strong', 'a', 'img', 'font', 'p', 'span', 'div']).replace("<br>", "<br/>").strip()

        if not created or value or comment:
            fraction_result.value = value
            fraction_result.comment = comment
            fraction_result.get_units(needsave=False)
            fraction_result.iteration = 1

            ref = r.get("ref", {})
            fraction_result.ref_title = ref.get("title", "Default")
            fraction_result.ref_about = ref.get("about", "")
            fraction_result.ref_m = ref.get("m")
            fraction_result.ref_f = ref.get("f")
            fraction_result.selected_reference = r.get("selectedReference", -2)

            if not fraction_result.ref_m and not fraction_result.ref_f:
                fraction_result.get_ref(re_save=True, needsave=False)

            fraction_result.save()
        elif not created:
            fraction_result.delete()
    iss.doc_save = request.user.doctorprofile
    iss.time_save = timezone.now()
    iss.lab_comment = request_data.get("comment", "")
    iss.def_uet = 0
    iss.co_executor_id = None if request_data.get("co_executor", -1) == -1 else request_data["co_executor"]
    iss.co_executor_uet = 0

    if not request.user.doctorprofile.has_group("Врач-лаборант"):
        for r in Result.objects.filter(issledovaniye=iss):
            iss.def_uet += r.fraction.uet_co_executor_1
    else:
        for r in Result.objects.filter(issledovaniye=iss):
            iss.def_uet += r.fraction.uet_doc
        if iss.co_executor_id:
            for r in Result.objects.filter(issledovaniye=iss):
                iss.co_executor_uet += r.fraction.uet_co_executor_1

    iss.co_executor2_id = None if request_data.get("co_executor2", -1) == -1 else request_data["co_executor2"]
    iss.co_executor2_uet = 0
    if iss.co_executor2_id:
        for r in Result.objects.filter(issledovaniye=iss):
            iss.co_executor2_uet += r.fraction.uet_co_executor_2
    iss.legal_authenticator_id = None if request_data.get("legal_authenticator", -1) == -1 else request_data["legal_authenticator"]
    iss.save()
    Log.log(str(pk), 13, body=request_data, user=request.user.doctorprofile)
    return JsonResponse(
        {
            "ok": True,
        }
    )


@login_required
@group_required("Врач-лаборант", "Лаборант")
def confirm(request):
    request_data = json.loads(request.body)
    pk = request_data["pk"]
    iss: Issledovaniya = Issledovaniya.objects.get(pk=pk)
    if iss.time_confirmation:
        return JsonResponse(
            {
                "ok": False,
                "message": 'Редактирование запрещено. Результат уже подтверждён.',
            }
        )
    if iss.doc_save:
        iss.doc_confirmation = request.user.doctorprofile
        if iss.napravleniye:
            iss.napravleniye.qr_check_token = None
            iss.napravleniye.save(update_fields=['qr_check_token'])
        for r in Result.objects.filter(issledovaniye=iss):
            r.get_ref()
        iss.time_confirmation = timezone.now()
        iss.save()
        if iss.napravleniye:
            iss.napravleniye.sync_confirmed_fields()
        Log.log(str(pk), 14, body={"dir": iss.napravleniye_id}, user=request.user.doctorprofile)
        if iss.research_id in FTP_SETUP_TO_SEND_HL7_BY_RESEARCHES.get("id_researches"):
            push_result(iss)
    else:
        return JsonResponse(
            {
                "ok": False,
                "message": 'Невозможно подтвердить, результат не сохранён',
            }
        )
    return JsonResponse(
        {
            "ok": True,
        }
    )


@login_required
@group_required("Врач-лаборант", "Лаборант")
def confirm_list(request):
    request_data = json.loads(request.body)
    pk = request_data["pk"]
    n: Napravleniya = Napravleniya.objects.prefetch_related('issledovaniya_set').get(pk=pk)
    for iss in n.issledovaniya_set.all():
        if iss.doc_save and not iss.time_confirmation:
            for r in Result.objects.filter(issledovaniye=iss):
                r.get_ref()
            iss.doc_confirmation = request.user.doctorprofile
            iss.time_confirmation = timezone.now()
            if not request.user.doctorprofile.has_group("Врач-лаборант"):
                iss.co_executor = request.user.doctorprofile
                for r in Result.objects.filter(issledovaniye=iss):
                    if iss.def_uet:
                        iss.def_uet += Decimal(r.fraction.uet_co_executor_1)
                    else:
                        iss.def_uet = Decimal(r.fraction.uet_co_executor_1)
            iss.save()
            if iss.napravleniye:
                iss.napravleniye.sync_confirmed_fields()
            Log.log(str(iss.pk), 14, body={"dir": iss.napravleniye_id}, user=request.user.doctorprofile)

            if iss.research_id in FTP_SETUP_TO_SEND_HL7_BY_RESEARCHES.get("id_researches"):
                push_result(iss)
    n.qr_check_token = None
    n.save(update_fields=['qr_check_token'])
    return JsonResponse(
        {
            "ok": True,
        }
    )


@login_required
@group_required("Сброс подтверждений результатов", "Врач-лаборант", "Лаборант")
def reset_confirm(request):
    request_data = json.loads(request.body)
    pk = request_data["pk"]
    result = {"ok": False, "message": "Неизвестная ошибка"}
    if Issledovaniya.objects.filter(pk=pk).exists():
        iss: Issledovaniya = Issledovaniya.objects.get(pk=pk)

        if iss.allow_reset_confirm(request.user):
            predoc = {"fio": iss.doc_confirmation_fio or 'не подтверждено', "pk": pk, "direction": iss.napravleniye_id}
            iss.doc_confirmation = iss.executor_confirmation = iss.time_confirmation = None
            iss.save()
            if iss.napravleniye:
                iss.napravleniye.sync_confirmed_fields()
                if iss.napravleniye.result_rmis_send:
                    c = Client()
                    c.directions.delete_services(iss.napravleniye, request.user.doctorprofile)
                iss.napravleniye.need_resend_amd = False
                iss.napravleniye.need_resend_amd = False
                iss.napravleniye.eds_total_signed = False
                iss.napravleniye.eds_total_signed_at = None
                iss.napravleniye.eds_main_signer_cert_thumbprint = None
                iss.napravleniye.eds_main_signer_cert_details = None
                iss.napravleniye.vi_id = None
                iss.napravleniye.save(update_fields=['eds_total_signed', 'eds_total_signed_at', 'need_resend_amd', 'vi_id'])
            result = {"ok": True}
            Log.log(str(pk), 24, body=predoc, user=request.user.doctorprofile)
        else:
            result["message"] = f"Сброс подтверждения разрешен в течении {str(SettingManager.get('lab_reset_confirm_time_min'))} минут"
    return JsonResponse(result)


@login_required
@group_required("Получатель биоматериала")
def last_received_daynum(request):
    request_data = json.loads(request.body)
    pk = request_data["pk"]

    last_daynum = 0

    date1 = datetime_safe.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    date2 = datetime_safe.datetime.now()

    f = {}

    if pk > -2:
        f = {"issledovaniya__research__podrazdeleniye": pk}

    if TubesRegistration.objects.filter(time_recive__range=(date1, date2), daynum__gt=0, doc_recive=request.user.doctorprofile, **f).exists():
        last_daynum = max([x.daynum for x in TubesRegistration.objects.filter(time_recive__range=(date1, date2), daynum__gt=0, doc_recive=request.user.doctorprofile, **f)])

    return JsonResponse({"lastDaynum": last_daynum})


@login_required
@group_required("Получатель биоматериала")
def receive_one_by_one(request):
    request_data = json.loads(request.body)
    lab_pk = request_data["currentLaboratory"]

    if lab_pk >= 0:
        lab = Podrazdeleniya.objects.get(pk=lab_pk)
    else:
        lab = {"title": "Все лаборатории", "pk": lab_pk}

    pk = re.sub("[^0-9]", "", str(request_data['q']))
    direction = request_data["workMode"] == "direction"
    message = None
    if not direction:
        pks = [pk]
    else:
        resp = tubes(request, direction_implict_id=pk)

        content_type = resp.headers.get("content-type")
        if content_type == 'application/json':
            resp_json = json.loads(resp.content)
            if isinstance(resp_json, dict) and "message" in resp_json:
                message = resp_json["message"]
        user_groups = [str(x) for x in request.user.groups.all()]
        if "Направления-все МО" not in user_groups:
            pks = [
                x.number
                for x in (
                    TubesRegistration.objects.filter(issledovaniya__napravleniye__pk=pk)
                    .filter(Q(issledovaniya__napravleniye__hospital=request.user.doctorprofile.hospital) | Q(issledovaniya__napravleniye__hospital__isnull=True))
                    .distinct()
                )
            ]
        else:
            pks = [x.number for x in (TubesRegistration.objects.filter(issledovaniya__napravleniye__pk=pk).distinct())]

    ok_objects = []
    ok_researches = []
    invalid_objects = []
    last_n = None

    external_order_organization = None
    has_external_order_executor = False

    for p in pks:
        if TubesRegistration.objects.filter(number=p).exists() and Issledovaniya.objects.filter(tubes__number=p).exists():
            tube = TubesRegistration.objects.get(number=p)
            first_iss: Issledovaniya = tube.issledovaniya_set.first()
            if first_iss and first_iss.napravleniye and first_iss.napravleniye.external_executor_hospital:
                podrs = [first_iss.napravleniye.external_executor_hospital.safe_short_title]
                has_external_order_executor = True
            else:
                podrs = sorted(list(set([x.research.podrazdeleniye.get_title() for x in tube.issledovaniya_set.all()])))

            if first_iss and first_iss.napravleniye and first_iss.napravleniye.external_order:
                external_order_organization = first_iss.napravleniye.external_order.organization.safe_short_title

            if lab_pk < 0 or first_iss.research.get_podrazdeleniye() == lab:
                tube.clear_notice(request.user.doctorprofile)
                status = tube.day_num(request.user.doctorprofile, request_data["nextN"])
                if status["new"]:
                    last_n = status["n"]

                ok_objects.append(
                    {
                        "pk": p,
                        "new": status["new"],
                        "labs": podrs,
                        "receivedate": strdate(tube.time_recive),
                    }
                )

                ok_researches.extend([x.research.title for x in Issledovaniya.objects.filter(tubes__number=p)])
            else:
                invalid_objects.append(f"Пробирка {p} для другой лаборатории: {', '.join(podrs)}")
        else:
            invalid_objects.append(f"Пробирка {p} не найдена")
    if direction and Napravleniya.objects.filter(pk=pk).exists():
        d = Napravleniya.objects.get(pk=pk)
        if Issledovaniya.objects.filter(napravleniye_id=pk, research__is_gistology=True).exists():
            is_new = False
            if not d.time_gistology_receive:
                d.time_gistology_receive = timezone.now()
                d.doc_gistology_receive = request.user.doctorprofile
                d.save()
                Log.log(
                    d.pk,
                    122000,
                    request.user.doctorprofile,
                    {
                        'gistology_receive_time': strdate(d.time_gistology_receive),
                    },
                )
                is_new = True
            ok_objects.append(
                {
                    "pk": pk,
                    "new": is_new,
                    "labs": ['Гистология'],
                    "receivedate": strdate(d.time_gistology_receive),
                }
            )
            ok_researches.extend([x.research.get_title() for x in Issledovaniya.objects.filter(napravleniye_id=pk, research__is_gistology=True)])
    if not ok_objects and not invalid_objects:
        invalid_objects.append(f"Ёмкости по запросу {pk} не найдены")
    return JsonResponse(
        {
            "ok": ok_objects,
            "researches": sorted(list(set(ok_researches))),
            "externalOrderOrganization": external_order_organization,
            "hasExternalOrderExecutor": has_external_order_executor,
            "invalid": invalid_objects,
            "lastN": last_n,
            "message": message,
        }
    )


@login_required
@group_required("Получатель биоматериала")
def receive_history(request):
    request_data = json.loads(request.body)
    result = {"rows": []}
    date1 = datetime_safe.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    date2 = datetime_safe.datetime.now()
    lpk = request_data["currentLaboratory"]

    if lpk >= 0:
        lab = Podrazdeleniya.objects.get(pk=lpk)
    else:
        lab = {"title": "Все лаборатории", "pk": lpk}

    t = TubesRegistration.objects.filter(time_recive__range=(date1, date2), doc_recive=request.user.doctorprofile)

    if lpk >= 0:
        t = t.filter(issledovaniya__research__podrazdeleniye=lab)
    elif SettingManager.get("l2_gistology", default='false', default_type='b'):
        ns = Napravleniya.objects.filter(time_gistology_receive__range=(date1, date2), issledovaniya__research__is_gistology=True, doc_gistology_receive=request.user.doctorprofile)
        for n in ns.order_by('-time_gistology_receive'):
            result["rows"].append(
                {
                    "pk": n.pk,
                    "n": 0,
                    "type": 'Гистология',
                    "color": 'FFFFFF',
                    "labs": ['Гистология'],
                    "researches": [x.research.title for x in Issledovaniya.objects.filter(napravleniye_id=n.pk)],
                    'isDirection': True,
                    'defect_text': "",
                    'is_defect': "",
                }
            )

    recieve_by_one_sql_method = SettingManager.get('recieve_by_one_sql_method', default="false", default_type='b')
    if not recieve_by_one_sql_method:
        for row in t.order_by("-daynum").distinct():
            first_iss: Issledovaniya = row.issledovaniya_set.first()
            if first_iss and first_iss.napravleniye and first_iss.napravleniye.external_executor_hospital:
                podrs = [first_iss.napravleniye.external_executor_hospital.safe_short_title]
                lab_titles = sorted(list(set([f"{x.research.get_podrazdeleniye_title_recieve_recieve()}" for x in row.issledovaniya_set.all()])))
                lab_titles = ",".join(lab_titles)
                podrs = [f"{podrs[0]}, {lab_titles}"]
                is_external_executor = True
            else:
                podrs = sorted(list(set([f"{x.research.get_podrazdeleniye_title_recieve_recieve()}" for x in row.issledovaniya_set.all()])))
                is_external_executor = False

            if first_iss and first_iss.napravleniye and first_iss.napravleniye.external_order:
                external_order_organization = first_iss.napravleniye.external_order.organization.safe_short_title
            else:
                external_order_organization = None
            result["rows"].append(
                {
                    "pk": row.number,
                    "n": row.daynum or 0,
                    "type": str(row.type.tube),
                    "color": row.type.tube.color,
                    "labs": podrs,
                    "researches": [x.research.title for x in Issledovaniya.objects.filter(tubes__number=row.number)],
                    'defect_text': row.defect_text,
                    'is_defect': row.is_defect,
                    'isExternalExecutor': is_external_executor,
                    'externalOrderOrganization': external_order_organization,
                }
            )

    if recieve_by_one_sql_method:
        result_sql = get_tube_registration(date1, date2, request.user.doctorprofile.pk)
        old_n = -1
        step = 0
        tmp_researches = []
        old_labs = []
        old_tube_number = ""
        old_tube_title = ""
        old_tube_color = ""
        old_is_defect = None
        old_defect_text = ""
        old_is_external_executor = False
        old_himself_input_external_hosp_title = None

        for row in result_sql:
            if (row.tube_daynum != old_n) and step > 0:
                result["rows"].append(
                    {
                        "pk": old_tube_number,
                        "n": old_n or 0,
                        "type": old_tube_title,
                        "color": old_tube_color,
                        "labs": list(set(old_labs)),
                        "researches": tmp_researches,
                        'defect_text': old_defect_text,
                        'is_defect': old_is_defect,
                        'isExternalExecutor': old_is_external_executor,
                        'externalOrderOrganization': row.himself_input_external_hosp_title,
                    }
                )
                tmp_researches = []
                old_labs = []

            tmp_researches.append(row.research_title)
            old_tube_number = row.tube_number
            old_tube_title = row.tube_title
            old_tube_color = row.tube_color
            old_labs.append(row.department_title)
            old_defect_text = row.tube_defect_text
            old_is_defect = row.tube_is_defect
            old_is_external_executor = True if row.plan_external_perform_org else False
            old_n = row.tube_daynum
            old_himself_input_external_hosp_title = row.himself_input_external_hosp_title
            step += 1
        if step > 0:
            result["rows"].append(
                {
                    "pk": old_tube_number,
                    "n": old_n or 0,
                    "type": old_tube_title,
                    "color": old_tube_color,
                    "labs": list(set(old_labs)),
                    "researches": tmp_researches,
                    'defect_text': old_defect_text,
                    'is_defect': old_is_defect,
                    'isExternalExecutor': old_is_external_executor,
                    'externalOrderOrganization': old_himself_input_external_hosp_title,
                }
            )
    return JsonResponse(result)


@login_required
@group_required("Получатель биоматериала")
def save_defect_tube(request):
    request_data = json.loads(request.body)
    data_row = request_data.get('row')
    t = TubesRegistration.objects.filter(number=int(data_row['pk'])).first()
    t.is_defect = data_row['is_defect']
    t.defect_text = data_row['defect_text']
    t.save()
    message = {"ok": "ok"}
    return JsonResponse(message)


@login_required
@group_required("Получатель биоматериала")
def cancel_receive(request):
    request_data = json.loads(request.body)
    data_row = request_data.get('row')
    t = TubesRegistration.objects.filter(number=int(data_row['pk'])).first()
    t.time_recive = None
    t.doc_recive = None
    t.is_defect = False
    t.defect_text = ""
    t.save()
    Log.log(t.number, 4001, request.user.doctorprofile, {"tubeNumber": t.number, "id": t.pk, "docId": request.user.doctorprofile.pk, "docFio": request.user.doctorprofile.get_fio()})
    message = {"ok": "ok"}
    return JsonResponse(message)
