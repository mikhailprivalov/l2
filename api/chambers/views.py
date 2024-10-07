from laboratory.decorators import group_required
from django.contrib.auth.decorators import login_required
import simplejson as json
from django.http import JsonResponse
from podrazdeleniya.models import Chamber, Bed, PatientToBed, PatientStationarWithoutBeds
from utils.response import status_response
import datetime
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
    user_department_id = request.user.doctorprofile.podrazdeleniye_id
    bed: Bed = Bed.objects.filter(pk=bed_id).select_related('chamber').first()
    if not bed:
        return status_response(False, "ID кровати обязателен")
    bed_department_id = bed.chamber.podrazdelenie_id
    if not user_department_id == bed_department_id:
        return status_response(False, "Пользователь не принадлежит к данному подразделению")
    if not PatientToBed.objects.filter(bed_id=bed_id, date_out=None).exists():
        PatientToBed(direction_id=direction_id, bed_id=bed_id).save()
    return status_response(True)


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def extract_patient_bed(request):
    request_data = json.loads(request.body)
    direction_pk = request_data.get('patient')
    user_department_id = request.user.doctorprofile.podrazdeleniye_id
    patient: PatientToBed = PatientToBed.objects.filter(direction_id=direction_pk, date_out=None).select_related('bed__chamber').first()
    if not patient:
        return status_response(False, "ID истории болезни обязателен")
    bed_department_id = patient.bed.chamber.podrazdelenie_id
    if not user_department_id == bed_department_id:
        return status_response(False, "Пользователь не принадлежит к данному подразделению")
    patient.date_out = datetime.datetime.today()
    patient.save()
    return status_response(True)


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def get_attending_doctors(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    attending_doctors = load_attending_doctor_by_department(department_pk)
    doctors = [
        {
            "pk": doctor.id,
            "fio": f'{doctor.family} {doctor.name} {doctor.patronymic if doctor.patronymic else ""}',
            "short_fio": f'{doctor.family} {doctor.name[0]}. {doctor.patronymic[0] if doctor.patronymic else ""}.',
            "highlight": False,
        }
        for doctor in attending_doctors
    ]
    return JsonResponse({"data": doctors})


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def update_doctor_to_bed(request):
    request_data = json.loads(request.body)
    user_department_id = request.user.doctorprofile.podrazdeleniye_id
    doctor_obj = request_data.get('doctor')
    doctor_id = doctor_obj.get('doctor_pk')
    direction_id = doctor_obj.get('direction_id')
    is_assign = doctor_obj.get('is_assign')
    result = PatientToBed.update_doctor(doctor_id, direction_id, is_assign, user_department_id)
    return JsonResponse(result)


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
    user_department_id = request.user.doctorprofile.podrazdeleniye_id
    if user_department_id != department_pk:
        return status_response(False, "Пользователь не принадлежит к данному подразделению")
    PatientStationarWithoutBeds(direction_id=patient_obj["direction_pk"], department_id=department_pk).save()
    return status_response(True)


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def delete_patient_without_bed(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk')
    patient_obj = request_data.get('patient_obj')
    user_department_id = request.user.doctorprofile.podrazdeleniye_id
    if user_department_id != department_pk:
        return status_response(False, "Пользователь не принадлежит к данному подразделению")
    PatientStationarWithoutBeds.objects.get(direction_id=patient_obj["direction_pk"]).delete()
    return status_response(True)
