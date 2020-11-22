import simplejson as json
from django.http import JsonResponse

from api.stationar.stationar_func import forbidden_edit_dir
from directions.models import Napravleniya
from pharmacotherapy.models import ProcedureList, ProcedureListTimes
from django.contrib.auth.decorators import login_required
from laboratory.decorators import group_required


@login_required
@group_required("Врач стационара", "t, ad, p")
def get_procedure_by_dir(request):
    request_data = json.loads(request.body)
    result = []
    procedures_obj = None
    if request_data["histoty"] > -1:
        history = Napravleniya.objects.filter(pk=request_data["histoty"]).first()
        procedures_obj = ProcedureList.objects.filter(pk=history)
    if procedures_obj:
        for procedure in procedures_obj:
            drug = procedure.drug.mnn if procedure.drug.mnn else procedure.trade_name
            form_release = procedure.form_release.title
            method = procedure.method.title
            dosage = procedure.dosage
            units = procedure.units
            procedure_times = ProcedureListTimes.objects.filter(prescription=procedure)
            times = []
            for proc_time in procedure_times:
                times.append({"time": proc_time.times_medication, "executor": proc_time.executor, "cancel": proc_time.cancel})
            result.append({"drug": drug, "form_release": form_release, "method": method, "dosage": dosage, "units": units, "times": times})

    return JsonResponse({"result": result})


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
