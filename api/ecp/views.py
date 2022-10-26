import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from clients.models import Card
from clients.sql_func import get_individual_age
from ecp_integration.integration import get_doctors_ecp_free_dates_by_research, get_doctor_ecp_free_slots_by_date, register_patient_ecp_slot, cancel_ecp_patient_record
from users.models import DoctorProfile
from slog.models import Log


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
    return JsonResponse({"result": slots})


@login_required
def fill_slot(request):
    request_data = json.loads(request.body)
    card_pk = request_data['card_pk']
    slot_id = request_data['slot_id']
    type_slot = request_data['type_slot']
    doctor_pk = request_data['doctor_pk']
    date = request_data['date']
    card = Card.objects.get(pk=card_pk)
    ecp_id = card.get_ecp_id()

    if not ecp_id:
        return JsonResponse({"register": False, "message": "Пациент не найден в ЕЦП"})

    individual_pk = card.individual.pk
    doctor_data = DoctorProfile.objects.filter(rmis_location=doctor_pk).first()
    age_target_patient = get_individual_age(date, individual_pk)
    age_month = -1
    for k in age_target_patient:
        age_month = k.age_year * 12 + k.age_month
        break
    if doctor_data.max_age_patient_registration != -1 and (age_month > doctor_data.max_age_patient_registration):
        return JsonResponse({"register": False, "message": "Запись ограничена по возрасту до "})
    r = register_patient_ecp_slot(ecp_id, slot_id, type_slot)
    return JsonResponse(r)


@login_required
def cancel_slot(request):
    request_data = json.loads(request.body)
    slot_id = request_data['slotId']
    patent_pk = request_data['patentPk']
    rmis_location = request_data['rmisLocation']
    result = cancel_ecp_patient_record(slot_id)
    if result:
        card_patient = Card.objects.filter(pk=patent_pk).first()
        Log.log(key=patent_pk, type=140001, user=request.user.doctorprofile, body={"slot_id": slot_id, "rmis_location": rmis_location, "patient": card_patient.get_fio_w_card()})
    return JsonResponse({"result": result})
