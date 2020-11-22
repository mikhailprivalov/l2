from datetime import datetime, time as dtime

import pytz
import simplejson as json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from clients.models import Card
from directions.models import Napravleniya
from forms.forms_func import primary_reception_get_data
from laboratory.settings import TIME_ZONE
from laboratory.utils import strdate, current_time, strfdatetime
from pharmacotherapy.models import ProcedureList, Drugs, FormRelease, MethodsReception, ProcedureListTimes
from plans.models import PlanOperations
from clients.models import Card
from .sql_func import get_plans_by_params_sql

from ..sql_func import users_by_group
from slog.models import Log
from ..stationar.stationar_func import hosp_get_hosp_direction


def procedure_save(request):
    request_data = json.loads(request.body)
    user_timezone = pytz.timezone(TIME_ZONE)
    created = 0
    for data in request_data:
        if data['pk'] == -1:
            history = Napravleniya.objects.filter(pk=data["history"]).first()
            diary = Napravleniya.objects.filter(pk=data["diary"]).first()
            card = Card.objects.filter(pk=data["card"]).first()
            drug = Drugs.objects.filter(pk=data["drug"]).first()
            form_release = FormRelease.objects.filter(pk=data["form_release"]).first()
            method = MethodsReception.objects.filter(pk=data["method"]).first()
            dosage = data["dosage"]
            units = data["units"]
            date_start = datetime.strptime(data['date_start'], '%Y-%m-%d'),
            date_end = datetime.strptime(data['date_end'], '%Y-%m-%d'),
            proc_obj = ProcedureList(
                history=history,
                diary=diary,
                card=card,
                drug=drug,
                form_release=form_release,
                method=method,
                dosage=dosage,
                units=units,
                date_start=date_start,
                date_end=date_end,
                doc_create=request.user.doctorprofile,
            )
            proc_obj.save()
            for time in data["times"]:
                ProcedureListTimes(
                    prescription=proc_obj,
                    times_medication=datetime.strptime(time, '%Y-%m-%d %H:%M').astimezone(user_timezone)
                )
            created += 1

    return JsonResponse({"создано": f"Назначений {created}"})


def get_procedure_by_dir(request):
    request_data = json.loads(request.body)
    result = []
    procedures_obj = None
    if request_data["histoty"] > -1:
        history = Napravleniya.objects.filter(pk=request_data["histoty"]).first()
        procedures_obj = ProcedureList.objects.filter(pk=history)
    if request_data["diary"] > -1:
        diary = Napravleniya.objects.filter(pk=request_data["diary"]).first()
        procedures_obj = ProcedureList.objects.filter(diary=diary)
    if procedures_obj:
        for procedure in procedures_obj:
            drug = procedure.drug.mnn if procedure.drug.mnn else procedure.trade_name
            form_release = procedure.form_release.title,
            method = procedure.method.title,
            dosage = procedure.dosage,
            units = procedure.units,
            procedure_times = ProcedureListTimes.objects.filter(prescription=procedure)
            times = []
            for proc_time in procedure_times:
                times.append({"time": proc_time.times_medication, "executor": proc_time.executor, "cancel": proc_time.cancel})
            result.append({"drug": drug, "form_release": form_release, "method": method, "dosage": dosage, "units": units, "times": times.copy()})

    return JsonResponse({"result": result})


def procedure_cancel(request):
    request_data = json.loads(request.body)
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
        return JsonResponse({"messege": "Удалено"})

    return JsonResponse({"messege": f"Отменоно время {canceled} записей"})
