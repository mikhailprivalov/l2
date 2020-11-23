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
        ProcedureList.objects.filter(history_id=request_data["direction"])
        .prefetch_related(Prefetch('procedurelisttimes_set', queryset=ProcedureListTimes.objects.filter(cancel=False)))
    ):
        row = {
            "drug": str(procedure.drug),
            "form_release": str(procedure.form_release.title),
            "method": str(procedure.method.title),
            "dosage": f"{procedure.dosage} {procedure.units}".strip(),
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
                "empty": False,
                "ok": bool(pt.executor),
                "cancel": bool(pt.cancel),
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
    forbidden_edit = forbidden_edit_dir(request_data["history"])
    if forbidden_edit:
        return JsonResponse({"message": "Редактирование запрещено"})
    proc_obj = ProcedureList.objects.filter(pk=request_data["pk"])
    proc_times = ProcedureListTimes.objects.filter(prescription=proc_obj)
    executed = 0
    canceled = 0
    for proc_time in proc_times:
        if proc_time.executor:
            executed += 1
        proc_time.cancel = True
        proc_time.who_cancel = request.user.doctorprofile
        canceled += 1
    if executed == 0:
        ProcedureListTimes.objects.filter(prescription=proc_obj).delete()
        return JsonResponse({"message": "Удалено"})

    return JsonResponse({"message": f"Отменоно время {canceled} записей"})


def params(request):
    return JsonResponse({
        "formReleases": list(FormRelease.objects.all().order_by('title').values('pk', 'title')),
        "methods": list(MethodsReception.objects.all().order_by('title').values('pk', 'title')),
        "times": TIMES,
        "units": [
            "мл", "мг", "мкг", "ед",
        ]
    })
