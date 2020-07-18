from datetime import datetime, time as dtime
import simplejson as json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from clients.models import Card
from laboratory.utils import strdate, current_time
from plans.models import PlanOperations
from django.http import HttpRequest
from api.views import load_docprofile_by_group
from .sql_func import get_plans_by_params_sql


@login_required
def plan_operations_save(request):
    request_data = json.loads(request.body)
    PlanOperations.save_data(request_data, request.user.doctorprofile)

    return JsonResponse({"data": ''})


@login_required
def get_plan_operations_by_patient(request):
    request_data = json.loads(request.body)
    start_date = datetime.combine(current_time(), dtime.min)
    patient_card = Card.objects.filter(pk=request_data['card_pk'])[0]
    result = PlanOperations.objects.filter(patient_card=patient_card, date__gte=start_date).order_by('date')
    data = [{'direction': i.direction, 'hirurg': i.doc_operate.get_fio(), 'hirurg_pk': i.doc_operate.pk, 'date': strdate(i.date), 'type_operation': i.type_operation, 'pk_plan': i.pk} for i in result]

    return JsonResponse({"data": data})


@login_required
def get_plan_operations_by_params(request):
    request_data = json.loads(request.body)
    start_date = datetime.strptime(request_data['start_date'], '%Y-%m-%d')
    start_date = datetime.combine(start_date, dtime.min)
    end_date = datetime.strptime(request_data['start_date'], '%Y-%m-%d')
    end_date = datetime.combine(end_date, dtime.max)
    doc_operate_pk = request_data['doc_operate_pk']
    doc_anesthetist_pk = request_data['doc_anesthetist_pk']
    department = request_data['department']

    doc_operate_pk = 1940
    doc_anesthetist_pk = -1
    department = -1
    result = get_plans_by_params_sql(start_date, end_date, doc_operate_pk, doc_anesthetist_pk, department)

    data = []
    for i in result:
        fio_patient = f"{i[8]} {i[9][0:1]}.{i[10][0:1]}."
        data.append({"pk_plan": i[0], "patient_card": i[1], "direction": i[2], "date": i[3], "type_operation": i[4], "doc_operate_id": i[5],
         "doc_anesthetist_id": i[6], "canceled": i[7], "fio_patient": fio_patient, "birthday": i[11]})
    print(data)

    return JsonResponse({"result": data})


@login_required
def get_docs_can_operate():
    docs = json.dumps({'group': ['Оперирует']})
    docs_obj = HttpRequest()
    docs_obj._body = docs
    docs_can_operate = load_docprofile_by_group(docs_obj)

    return JsonResponse({"data": docs_can_operate})


@login_required
def docs_can_anesthetist():
    docs = json.dumps({'group': ['Анестезиолог']})
    docs_obj = HttpRequest()
    docs_obj._body = docs
    docs_can_anesthetist = load_docprofile_by_group(docs_obj)

    return JsonResponse({"data": docs_can_anesthetist})
