import collections
import itertools
from typing import Optional

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
import simplejson as json
from django.utils import dateformat

from directions.models import TubesRegistration, Issledovaniya, Napravleniya, Result
from directory.models import Fractions, Researches, References
from podrazdeleniya.models import Podrazdeleniya
from utils.dates import try_parse_range


@login_required
def fractions(request):
    request_data = json.loads(request.body)
    pk = int(request_data['pk'])
    research = Researches.objects.get(pk=pk)
    fractions_list = []
    for f in Fractions.objects.filter(research=research).order_by("sort_weight"):
        fractions_list.append(
            {
                "pk": f.pk,
                "title": f.title,
                "units": f.units,
                "fsli": f.get_fsli_code(),
            }
        )
    return JsonResponse(
        {
            "fractions": fractions_list,
            "title": research.get_title(),
        }
    )


@login_required
def save_fsli(request):
    request_data = json.loads(request.body)
    fractions = request_data['fractions']
    for fd in fractions:
        f = Fractions.objects.get(pk=fd['pk'])
        nf = fd['fsli'].strip() or None
        if f != f.get_fsli_code():
            f.fsli = nf
            f.save(update_fields=['fsli'])
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


def laboratories(request):
    rows = []
    active = -1
    r: Podrazdeleniya
    for r in Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY).exclude(title="Внешние организации").order_by("title"):
        rows.append({
            "pk": r.pk,
            "title": r.get_title(),
        })
        if active == -1 or request.user.doctorprofile.podrazdeleniye_id == r.pk:
            active = r.pk
    return JsonResponse({"rows": rows, "active": active})


def ready(request):
    request_data = json.loads(request.body)
    dates = request_data['date_range']
    laboratory_pk = request_data['laboratory']
    laboratory = Podrazdeleniya.objects.get(pk=laboratory_pk)
    result = {"tubes": [], "directions": []}

    date_start, date_end = try_parse_range(*dates)
    dates_cache = {}
    tubes = set()
    dirs = set()

    tlist = TubesRegistration.objects.filter(
        doc_recive__isnull=False,
        time_recive__range=(date_start, date_end),
        issledovaniya__time_confirmation__isnull=True,
        issledovaniya__research__podrazdeleniye=laboratory,
        issledovaniya__isnull=False,
    )

    tlist = tlist.filter(
        Q(issledovaniya__napravleniye__hospital=request.user.doctorprofile.hospital) |
        Q(issledovaniya__napravleniye__hospital__isnull=True)
    )

    for tube in tlist.prefetch_related('issledovaniya_set__napravleniye'):
        direction = None
        if tube.pk not in tubes:
            if not direction:
                direction = tube.issledovaniya_set.first().napravleniye
            if tube.time_recive.date() not in dates_cache:
                dates_cache[tube.time_recive.date()] = dateformat.format(tube.time_recive, 'd.m.y')
            tubes.add(tube.pk)
            dicttube = {
                "pk": tube.pk,
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


def search(request):
    result = {"ok": False, "msg": None}

    request_data = json.loads(request.body)

    direction: Optional[Napravleniya] = None
    pk = request_data["q"].strip()
    laboratory_pk = request_data["laboratory"]
    t = request_data["mode"]
    if pk.isdigit():
        issledovaniya = []
        labs = []
        labs_titles = []
        result["all_confirmed"] = True
        pk = int(pk)
        if pk >= 4600000000000:
            pk -= 4600000000000
            pk //= 10
            t = "direction"
        if t == "tube":
            iss = Issledovaniya.objects.filter(tubes__id=pk)
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
        if direction and direction.hospital and direction.hospital != request.user.doctorprofile.hospital:
            direction = None
            iss = None
        mnext = False
        for i in Issledovaniya.objects.filter(napravleniye=direction):
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
                for issledovaniye in iss.order_by("deferred", "-doc_save", "-doc_confirmation", "tubes__pk", "research__sort_weight"):
                    if True:
                        if issledovaniye.pk in researches_chk:
                            continue
                        researches_chk.append(issledovaniye.pk)

                        tubes_list = issledovaniye.tubes.exclude(doc_recive__isnull=True).all()

                        not_received_tubes_list = [str(x.pk) for x in issledovaniye.tubes.exclude(doc_recive__isnull=False).all().order_by("pk")]

                        not_received_why = [x.notice for x in issledovaniye.tubes.exclude(doc_recive__isnull=False).all().order_by("pk") if x.notice]

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
                            if doc_save_id == request.user.doctorprofile.pk:
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
                            if not issledovaniye.deferred:
                                result["all_confirmed"] = False
                        tb = ','.join(str(v.pk) for v in tubes_list)

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
                                "tubes": [{"pk": x.pk, "title": x.type.tube.title, "color": x.type.tube.color} for x in tubes_list],
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
                    "directioner": None if direction.imported_from_rmis or not direction.doc else direction.doc.fio,
                    "otd": None if direction.imported_from_rmis else direction.get_doc_podrazdeleniye_title(),
                    "fin_source": None if direction.imported_from_rmis else direction.fin_title,
                    "in_rmis": direction.result_rmis_send,
                },
                "issledovaniya": issledovaniya,
                "labs": labs,
                "q": {"text": pk, "mode": t},
            }
            result["ok"] = True
    return JsonResponse(result)


def form(request):
    request_data = json.loads(request.body)
    pk = request_data["pk"]
    iss: Issledovaniya = Issledovaniya.objects.get(pk=pk)
    research: Researches = iss.research
    data = {
        "pk": pk,
        "confirmed": bool(iss.time_confirmation),
        "saved": bool(iss.time_save),
        "allow_reset_confirm": iss.allow_reset_confirm(request.user),
        "research": {
            "title": research.title,
            "can_comment": research.can_lab_result_comment,
            "no_units_and_ref": research.no_units_and_ref,
            "co_executor_mode": research.co_executor_mode or 0,
            "co_executor_title": research.co_executor_2_title,
        },
        "result": [],
        "comment": iss.lab_comment or "",
    }

    f: Fractions
    for f in Fractions.objects.filter(research=research).order_by("pk", "sort_weight").prefetch_related('references_set'):
        r: Optional[Result] = Result.objects.filter(issledovaniye=iss, fraction=f).first()

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

        data["result"].append({
            "fraction": {
                "pk": f.pk,
                "title": f.title,
                "units": f.units,
                "render_type": f.render_type,
                "options": f.options,
                "type": f.variants.get_variants() if f.variants else [],
                "type2": f.variants2.get_variants() if f.variants2 else [],
                "references": {
                    **empty_ref,
                    "default": def_ref_pk,
                    "available": av,
                },
            },
            "ref": r.get_ref(full=True) if r else (empty_ref if def_ref_pk == -1 else av.get(def_ref_pk, {})),
            "norm": r.get_is_norm(recalc=True)[0] if r else None,
            "value": r.value if r else '',
        })

    return JsonResponse({
        "data": data,
    })
