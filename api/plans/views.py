from datetime import datetime, time as dtime
import simplejson as json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from clients.models import Card
from laboratory.utils import strdate, current_time
from plans.models import PlanOperations


@login_required
def plan_operations_save(request):
    request_data = json.loads(request.body)
    print(request_data)
    PlanOperations.save_data(request_data, request.user.doctorprofile)

    return JsonResponse({"data": ''})


@login_required
def get_plan_operations_by_patient(request):
    request_data = json.loads(request.body)
    print(request_data)
    start_date = datetime.combine(current_time(), dtime.min)
    patient_card = Card.objects.filter(pk=request_data['card_pk'])[0]
    result = PlanOperations.objects.filter(patient_card=patient_card, date__gte=start_date).order_by('date')
    data = [{'direction': i.direction, 'hirurg': i.doc_operate.get_fio(), 'date': strdate(i.date), 'type_operation': i.type_operation} for i in result]

    return JsonResponse({"data": data})

