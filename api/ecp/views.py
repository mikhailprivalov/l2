import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from api.schedule.views import save_slot_fact
from appconf.manager import SettingManager
from clients.models import Card
from doctor_schedule.models import SlotPlan
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
        request.user,
    )

    return JsonResponse({"data": data})


@login_required
def get_available_slots(request):
    request_data = json.loads(request.body)
    slots = get_doctor_ecp_free_slots_by_date(
        request_data['doctor_pk'],
        request_data['date'],
        time='08:00:00',
        research_pk=request_data['research_pk'],
        user_data=request.user,
    )
    return JsonResponse({"result": slots})


@login_required
def fill_slot(request):
    request_data = json.loads(request.body)
    card_pk = request_data['card_pk']
    slot_id = request_data['slot_id']
    type_slot = request_data['type_slot']
    slot_type_id = request_data.get('slot_type_id')
    slot_title = request_data.get('slot_title')
    doctor_pk = request_data['doctor_pk']
    research_pk = request_data['research_pk']
    direction_id = request_data.get('directionId')
    date = request_data['date']
    card = Card.objects.get(pk=card_pk)
    ecp_id = None
    if type_slot != "InternalTimeTableResource_id":
        ecp_id = card.get_ecp_id()

    doctor_data = DoctorProfile.objects.filter(rmis_location=doctor_pk).first()
    age_target_patient = card.individual.age(days_monthes_years=True, target_date=date)
    age_month = age_target_patient[2] * 12 + age_target_patient[1]
    allow_patient_registration = SettingManager.get("allow_patient_registration", default='true', default_type='b')
    r = {"register": False, "message": "Ошибка - обратитесь к Администратору"}

    if doctor_pk.find("@L") > -1:
        s: SlotPlan = SlotPlan.objects.filter(pk=slot_id).first()
        save_slot = save_slot_fact(s, card_pk, "reserved", research_pk, False, None, None, False, direction_id)
        if save_slot:
            r = {'register': True}
        else:
            r = {"register": False, "message": "Ошибка записи"}
    else:
        if not ecp_id:
            r = {"register": False, "message": "Пациент не найден в ЕЦП"}
        elif doctor_data.max_age_patient_registration != -1 and (age_month > doctor_data.max_age_patient_registration):
            r = {"register": False, "message": "Запись ограничена по возрасту"}
        elif slot_type_id == "13":
            r = {"register": False, "message": "Запись на данный слот запрещена"}
        elif slot_type_id == "10" and doctor_data != request.user.doctorprofile:
            r = {"register": False, "message": "Записать может только сам врач"}
        elif slot_type_id == "1":
            r = register_patient_ecp_slot(ecp_id, slot_id, type_slot)
        elif slot_type_id == "8" and not allow_patient_registration:
            available_quotas_time = doctor_data.available_quotas_time
            try:
                quotas_time = json.loads(available_quotas_time)
            except Exception:
                quotas_time = {}
            if quotas_time.get(str(request.user.doctorprofile.podrazdeleniye.pk)):
                times = quotas_time.get(str(request.user.doctorprofile.podrazdeleniye.pk))
                data_times = times.split("-")
                if slot_title >= data_times[0] and slot_title <= data_times[1]:
                    r = register_patient_ecp_slot(ecp_id, slot_id, type_slot)
                else:
                    r = {"register": False, "message": "Запись на это время у вас ограничена"}
        else:
            r = register_patient_ecp_slot(ecp_id, slot_id, type_slot)

    return JsonResponse(r)


@login_required
def cancel_slot(request):
    request_data = json.loads(request.body)
    slot_id = request_data['slotId']
    patent_pk = request_data['patentPk']
    rmis_location = request_data['rmisLocation']
    type_slot = request_data['typeSlot']
    result = cancel_ecp_patient_record(slot_id, type_slot)
    if result:
        card_patient = Card.objects.filter(pk=patent_pk).first()
        Log.log(
            key=patent_pk,
            type=140001,
            user=request.user.doctorprofile,
            body={"slot_id": slot_id, "type_slot": type_slot, "rmis_location": rmis_location, "patient": card_patient.get_fio_w_card()},
        )
    return JsonResponse({"result": result})
