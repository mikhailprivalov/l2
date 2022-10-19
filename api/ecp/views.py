import datetime
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from clients.models import Card
from ecp_integration.integration import get_doctors_ecp_free_dates_by_research, get_doctor_ecp_free_slots_by_date, register_patient_ecp_slot, search_patient_ecp_by_fio


@login_required
def get_available_slots_of_dates(request):
    request_data = json.loads(request.body)
    data = get_doctors_ecp_free_dates_by_research(
        request_data['research_pk'],
        request_data['date_start'],
        request_data['date_end'],
        request.user.doctorprofile.get_hospital_id(),
    )
    return JsonResponse({"data": data})


@login_required
def get_available_slots(request):
    request_data = json.loads(request.body)
    slots = get_doctor_ecp_free_slots_by_date(
        request_data['doctor_pk'],
        request_data['date'],
    )
    return JsonResponse({"result": [{"pk": x['TimeTableGraf_id'], "title": datetime.datetime.strptime(x['TimeTableGraf_begTime'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M')} for x in slots]})


@login_required
def get_available_slots(request):
    request_data = json.loads(request.body)
    slots = get_doctor_ecp_free_slots_by_date(
        request_data['doctor_pk'],
        request_data['date'],
    )
    return JsonResponse({"result": [{"pk": x['TimeTableGraf_id'], "title": datetime.datetime.strptime(x['TimeTableGraf_begTime'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M')} for x in slots]})


@login_required
def fill_slot(request):
    request_data = json.loads(request.body)
    card_pk = request_data['card_pk']
    slot_id = request_data['slot_id']

    card = Card.objects.get(pk=card_pk)
    ecp_id = card.get_ecp_id()

    if not ecp_id:
        return JsonResponse({"register": False, "message": "Пациент не найден в ЕЦП"})

    r = register_patient_ecp_slot(ecp_id, slot_id)

    return JsonResponse(r)
