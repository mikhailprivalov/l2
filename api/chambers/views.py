from laboratory.decorators import group_required
from django.contrib.auth.decorators import login_required
import simplejson as json
from django.http import JsonResponse

from laboratory.settings import CHAMBER_DOCTOR_GROUP_ID
from podrazdeleniya.models import Chamber, Bed, PatientToBed, PatientStationarWithoutBeds
from slog.models import Log
from utils.response import status_response
import datetime
from django.contrib.auth.models import Group
from .sql_func import load_patient_without_bed_by_department, load_attending_doctor_by_department, load_patients_stationar_unallocated_sql, load_chambers_and_beds_by_department


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def get_unallocated_patients(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    patients = [
        {
            "fio": f'{patient.family} {patient.name} {patient.patronymic if patient.patronymic else ""}',
            "age": patient.age,
            "short_fio": f'{patient.family} {patient.name[0]}. {patient.patronymic[0] if patient.patronymic else ""}.',
            "sex": patient.sex,
            "direction_pk": patient.napravleniye_id,
        }
        for patient in load_patients_stationar_unallocated_sql(department_pk)
    ]
    return JsonResponse({"data": patients})


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def get_chambers_and_beds(request):
    request_data = json.loads(request.body)
    department_id = request_data.get('department_pk', -1)
    chambers = {}
    chambers_beds = load_chambers_and_beds_by_department(department_id)
    for chamber in chambers_beds:
        if not chambers.get(chamber.chamber_id):
            chambers[chamber.chamber_id] = {
                "pk": chamber.chamber_id,
                "label": chamber.chamber_title,
                "beds": {},
            }
        if not chamber.bed_id:
            continue
        chambers[chamber.chamber_id]["beds"][chamber.bed_id] = {
            "pk": chamber.bed_id,
            "bed_number": chamber.bed_number,
            "doctor": [],
            "patient": [],
        }
        if chamber.direction_id:
            chambers[chamber.chamber_id]["beds"][chamber.bed_id]["patient"].append(
                {
                    "direction_pk": chamber.direction_id,
                    "fio": f"{chamber.patient_family} {chamber.patient_name} {chamber.patient_patronymic if chamber.patient_patronymic else ''}",
                    "short_fio": f"{chamber.patient_family} {chamber.patient_name[0]}. {chamber.patient_patronymic[0] if chamber.patient_patronymic else ''}.",
                    "age": chamber.patient_age,
                    "sex": chamber.patient_sex,
                }
            )
        if chamber.doctor_id:
            chambers[chamber.chamber_id]["beds"][chamber.bed_id]["doctor"].append(
                {
                    "pk": chamber.doctor_id,
                    "fio": f"{chamber.doctor_family} {chamber.doctor_name} {chamber.doctor_patronymic if chamber.doctor_patronymic else ''}",
                    "short_fio": f"{chamber.doctor_family} {chamber.doctor_name[0]}. {chamber.doctor_patronymic[0] if chamber.doctor_patronymic else ''}.",
                    "highlight": False,
                }
            )

    result = []
    for chamber in chambers.values():
        chamber["beds"] = [val for val in chamber["beds"].values()]
        result.append(chamber)

    return JsonResponse({"data": result})


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def entrance_patient_to_bed(request):
    request_data = json.loads(request.body)
    bed_id = request_data.get('bed_id')
    direction_id = request_data.get('direction_id')
    user = request.user
    bed: Bed = Bed.objects.filter(pk=bed_id).select_related('chamber').first()
    if not bed:
        return status_response(False, "ID кровати обязателен")
    bed_department_id = bed.chamber.podrazdelenie_id
    user_can_edit = Chamber.check_user(user, bed_department_id)
    if not user_can_edit:
        return status_response(False, "Пользователь не принадлежит к данному подразделению")
    if not PatientToBed.objects.filter(bed_id=bed_id, date_out=None).exists():
        patient_to_bed = PatientToBed(direction_id=direction_id, bed_id=bed_id)
        patient_to_bed.save()
        Log.log(direction_id, 230000, user.doctorprofile, {"direction_id": direction_id, "bed_id": bed_id, "department_id": bed_department_id, "patient_to_bed": patient_to_bed.pk})
    return status_response(True)


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def extract_patient_bed(request):
    request_data = json.loads(request.body)
    direction_pk = request_data.get('patient')
    user = request.user
    patient: PatientToBed = PatientToBed.objects.filter(direction_id=direction_pk, date_out=None).select_related('bed__chamber').first()
    if not patient:
        return status_response(False, "ID истории болезни обязателен")
    bed_department_id = patient.bed.chamber.podrazdelenie_id
    user_can_edit = Chamber.check_user(user, bed_department_id)
    if not user_can_edit:
        return status_response(False, "Пользователь не принадлежит к данному подразделению")
    patient.date_out = datetime.datetime.today()
    patient.save()
    Log.log(
        direction_pk,
        230001,
        user.doctorprofile,
        {
            "direction_id": direction_pk,
            "bed_id": patient.bed_id,
            "department_id": bed_department_id,
        },
    )
    return status_response(True)


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def get_attending_doctors(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    if CHAMBER_DOCTOR_GROUP_ID:
        group_id = CHAMBER_DOCTOR_GROUP_ID
        attending_doctors = load_attending_doctor_by_department(department_pk, group_id)
        doctors = [
            {
                "pk": doctor.id,
                "fio": f'{doctor.family} {doctor.name} {doctor.patronymic if doctor.patronymic else ""}',
                "short_fio": f'{doctor.family} {doctor.name[0]}. {doctor.patronymic[0] if doctor.patronymic else ""}.',
                "highlight": False,
            }
            for doctor in attending_doctors
        ]
        result = {"ok": True, "message": "", "data": doctors}
    else:
        result = {"ok": False, "message": "Группа прав для врачей не настроена", "data": []}
    return JsonResponse(result)


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def update_doctor_to_bed(request):
    request_data = json.loads(request.body)
    user = request.user
    doctor_obj = request_data.get('doctor')
    doctor_id = doctor_obj.get('doctor_pk')
    direction_id = doctor_obj.get('direction_id')
    is_assign = doctor_obj.get('is_assign')
    patient_to_bed = PatientToBed.objects.filter(direction_id=direction_id, date_out=None).select_related('bed__chamber').first()
    bed_department_id = patient_to_bed.bed.chamber.podrazdelenie_id
    user_can_edit = Chamber.check_user(user, bed_department_id)
    if not user_can_edit:
        result = {"ok": False, "message": "Пользователь не принадлежит к данному подразделению"}
        return result
    result = PatientToBed.update_doctor(doctor_id, patient_to_bed, is_assign)
    if result:
        if is_assign:
            type_log = 230002
        else:
            type_log = 230003
        Log.log(
            direction_id,
            type_log,
            user.doctorprofile,
            {
                "direction_id": direction_id,
                "bed_id": patient_to_bed.bed_id,
                "department_id": bed_department_id,
            },
        )
    return JsonResponse({"ok": result, "message": ""})


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def get_patients_without_bed(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    patient_to_bed = load_patient_without_bed_by_department(department_pk)

    patients = [
        {
            "fio": f"{patient.family} {patient.name} {patient.patronymic if patient.patronymic else ''}",
            "short_fio": f"{patient.family} {patient.name[0]}. {patient.patronymic[0] if patient.patronymic else ''}.",
            "age": patient.age,
            "sex": patient.sex,
            "direction_pk": patient.direction_id,
        }
        for patient in patient_to_bed
    ]
    return JsonResponse({"data": patients})


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def save_patient_without_bed(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk')
    patient_obj = request_data.get('patient_obj')
    user = request.user
    user_can_edit = Chamber.check_user(user, department_pk)
    if not user_can_edit:
        return status_response(False, "Пользователь не принадлежит к данному подразделению")
    patient_without_bed = PatientStationarWithoutBeds(direction_id=patient_obj["direction_pk"], department_id=department_pk)
    patient_without_bed.save()
    Log.log(
        patient_obj["direction_pk"],
        230004,
        user.doctorprofile,
        {
            "direction_id": patient_obj["direction_pk"],
            "department_id": department_pk,
        },
    )
    return status_response(True)


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def delete_patient_without_bed(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk')
    patient_obj = request_data.get('patient_obj')
    user = request.user
    user_can_edit = Chamber.check_user(user, department_pk)
    if not user_can_edit:
        return status_response(False, "Пользователь не принадлежит к данному подразделению")
    patient_without_bed = PatientStationarWithoutBeds.objects.get(direction_id=patient_obj["direction_pk"])
    patient_without_bed.delete()
    Log.log(
        patient_obj["direction_pk"],
        230005,
        user.doctorprofile,
        {
            "direction_id": patient_obj["direction_pk"],
            "department_id": department_pk,
        },
    )
    return status_response(True)
