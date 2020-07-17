from datetime import datetime, time as dtime
import simplejson as json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from clients.models import Card
from laboratory.utils import strdate, current_time
from plans.models import PlanOperations
from django.http import HttpRequest
from api.views import load_docprofile_by_group


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
    start_date = datetime.combine(request_data['start'], dtime.min)
    end_date = datetime.combine(request_data['end'], dtime.max)
    # doc_operate =
    docs = json.dumps({'group': ['Оперирует']})
    docs_obj = HttpRequest()
    docs_obj._body = docs
    docs_obj.user = request.user
    docs_can_operate = load_docprofile_by_group(docs_obj)

    # doc_anesthetist =
    docs = json.dumps({'group': ['Анестезиолог']})
    docs_obj = HttpRequest()
    docs_obj._body = docs
    docs_obj.user = request.user
    docs_can_anesthetist = load_docprofile_by_group(docs_obj)

    return JsonResponse({"data": True})
