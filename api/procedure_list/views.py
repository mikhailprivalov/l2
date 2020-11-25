import simplejson as json
from django.db.models import Prefetch
from django.http import JsonResponse

from api.stationar.stationar_func import forbidden_edit_dir
from laboratory.utils import strfdatetime
from pharmacotherapy.models import ProcedureList, ProcedureListTimes, FormRelease, MethodsReception
from django.contrib.auth.decorators import login_required
from laboratory.decorators import group_required
from utils.dates import date_iter_range


TIMES = [
    f"{8 + x * 4:02d}:00"
    for x in range(4)
]


@login_required
@group_required("Врач стационара", "t, ad, p")
def get_procedure_by_dir(request):
    request_data = json.loads(request.body)
    dates = set()
    rows = []
    procedure: ProcedureList
    for procedure in (
        ProcedureList.objects
        .filter(history_id=request_data["direction"], diary__issledovaniya__time_confirmation__isnull=False)
        .order_by('pk')
        .prefetch_related(Prefetch('procedurelisttimes_set', queryset=ProcedureListTimes.objects.all().order_by('times_medication')))
    ):
        row = {
            "pk": procedure.pk,
            "drug": str(procedure.drug),
            "created_at": strfdatetime(procedure.time_create, "%d.%m.%Y"),
            "form_release": str(procedure.form_release.title),
            "method": str(procedure.method.title),
            "dosage": f"{procedure.dosage} {procedure.units}".strip(),
            "cancel": bool(procedure.cancel),
            "who_cancel": None if not procedure.who_cancel else procedure.who_cancel.get_fio(),
            "dates": {},
        }
        pt: ProcedureListTimes
        for pt in procedure.procedurelisttimes_set.all():
            date_str = strfdatetime(pt.times_medication, "%d.%m.%Y")
            time_str = strfdatetime(pt.times_medication, "%H:%M")
            dates.add(pt.times_medication.date())
            if date_str not in row["dates"]:
                row["dates"][date_str] = {}
            row["dates"][date_str][time_str] = {
                "datetime": f"{date_str} {time_str}",
                "pk": pt.pk,
                "empty": False,
                "ok": bool(pt.executor),
                "executor": None if not pt.executor else pt.executor.get_fio(),
                "cancel": bool(pt.cancel) or row["cancel"],
                "who_cancel": (None if not pt.who_cancel else pt.who_cancel.get_fio()) or row["who_cancel"],
            }
        rows.append(row)

    dates_all = []

    if dates:
        min_date = min(dates)
        max_date = max(dates)

        dates_all = [strfdatetime(x, "%d.%m.%Y") for x in date_iter_range(min_date, max_date, more_1=True)]

        for row in rows:
            for date in dates_all:
                if date not in row["dates"]:
                    row["dates"][date] = {}
                for t in TIMES:
                    if t not in row["dates"][date]:
                        row["dates"][date][t] = {
                            "empty": True,
                        }

    return JsonResponse({"result": rows, "dates": dates_all, "times": TIMES})


@login_required
@group_required("Врач стационара", "t, ad, p")
def procedure_cancel(request):
    request_data = json.loads(request.body)
    proc_obj = ProcedureList.objects.get(pk=request_data["pk"])
    forbidden_edit = forbidden_edit_dir(proc_obj.history_id)
    if forbidden_edit:
        return JsonResponse({"message": "Редактирование запрещено", "ok": False})
    proc_times = ProcedureListTimes.objects.filter(prescription=proc_obj, executor__isnull=True)
    canceled = 0
    for proc_time in proc_times:
        if request_data["cancel"]:
            proc_time.cancel = True
            proc_time.who_cancel = request.user.doctorprofile
            proc_time.save()
        else:
            proc_time.cancel = False
            proc_time.who_cancel = None
            proc_time.save()
        canceled += 1

    if request_data["cancel"]:
        proc_obj.cancel = True
        proc_obj.who_cancel = request.user.doctorprofile
    else:
        proc_obj.cancel = False
        proc_obj.who_cancel = None
    proc_obj.save()

    return JsonResponse({"message": f"{'Отменено' if request_data['cancel'] else 'Возвращено'} {canceled} записей времени", "ok": True})


def params(request):
    return JsonResponse({
        "formReleases": list(FormRelease.objects.all().order_by('title').values('pk', 'title')),
        "methods": list(MethodsReception.objects.all().order_by('title').values('pk', 'title')),
        "times": TIMES,
        "units": [
            "мл", "мг", "мкг", "ед",
        ]
    })


@login_required
@group_required("Врач стационара", "t, ad, p")
def procedure_execute(request):
    request_data = json.loads(request.body)
    proc_obj = ProcedureListTimes.objects.get(pk=request_data["pk"])
    forbidden_edit = forbidden_edit_dir(proc_obj.prescription.history_id)
    if forbidden_edit:
        return JsonResponse({"message": "Редактирование запрещено", "ok": False})
    if not proc_obj.cancel and not proc_obj.prescription.cancel:
        if request_data["status"]:
            proc_obj.executor = request.user.doctorprofile
            proc_obj.save()
            return JsonResponse({"message": "Приём записан", "ok": True})

        proc_obj.executor = None
        proc_obj.save()

        return JsonResponse({"message": "Приём убран", "ok": True})

    return JsonResponse({"message": "Приём не записан", "ok": False})
