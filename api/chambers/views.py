from laboratory.decorators import group_required
from django.contrib.auth.decorators import login_required
import simplejson as json
from django.http import JsonResponse
from podrazdeleniya.models import Chamber, Bed, PatientToBed, PatientStationarWithoutBeds
from utils.response import status_response
import datetime
from .sql_func import load_patient_without_bed_by_department, load_attending_doctor_by_department, load_patients_stationar_unallocated_sql, load_chambers_and_beds_by_department


@login_required
@group_required("Управления палатами")
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
@group_required("Управления палатами")
def get_chambers_and_beds(request):
    request_data = json.loads(request.body)
    department_id = request_data.get('department_pk', -1)
    chambers = {}

    chambers_beds = load_chambers_and_beds_by_department(department_id)
    for chamber in chambers_beds:
        if chambers.get(chamber.chamber_id):
            chambers[chamber.chamber_id]["beds"][chamber.bed_id] = Bed.to_json(chamber)
            if chamber.direction_id:
                chambers[chamber.chamber_id]["beds"][chamber.bed_id]["patient"].append(PatientToBed.patient_to_json(chamber))
            if chamber.doctor_id:
                chambers[chamber.chamber_id]["beds"][chamber.bed_id]["doctor"].append(PatientToBed.doctor_to_json(chamber))
        else:
            chambers[chamber.chamber_id] = Chamber.to_json(chamber)
            if chamber.bed_id:
                chambers[chamber.chamber_id]["beds"][chamber.bed_id] = Bed.to_json(chamber)
                if chamber.direction_id:
                    chambers[chamber.chamber_id]["beds"][chamber.bed_id]["patient"].append(PatientToBed.patient_to_json(chamber))
                if chamber.doctor_id:
                    chambers[chamber.chamber_id]["beds"][chamber.bed_id]["doctor"].append(
                        PatientToBed.doctor_to_json(chamber)
                    )
    result = []
    for chamber in chambers.values():
        chamber["beds"] = [val for val in chamber["beds"].values()]
        result.append(chamber)

    return JsonResponse({"data": result})


@login_required
@group_required("Управления палатами")
def entrance_patient_to_bed(request):
    request_data = json.loads(request.body)
    bed_id = request_data.get('bed_id')
    direction_id = request_data.get('direction_id')
    if not PatientToBed.objects.filter(bed_id=bed_id, date_out=None).exists():
        PatientToBed(direction_id=direction_id, bed_id=bed_id).save()
    return status_response(True)


@login_required
@group_required("Управления палатами")
def extract_patient_bed(request):
    request_data = json.loads(request.body)
    direction_pk = request_data.get('patient')
    patient = PatientToBed.objects.filter(direction_id=direction_pk, date_out=None).first()
    patient.date_out = datetime.datetime.today()
    patient.save()
    return status_response(True)


@login_required
@group_required("Управления палатами")
def get_attending_doctors(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    attending_doctors = load_attending_doctor_by_department(department_pk)
    doctors = [
        {
            "pk": doctor.id,
            "fio": f'{doctor.family} {doctor.name} {doctor.patronymic if doctor.patronymic else ""}',
            "short_fio": f'{doctor.family} {doctor.name[0]}. {doctor.patronymic[0] if doctor.patronymic else ""}.',
            "highlight": False
        }
        for doctor in attending_doctors
    ]
    return JsonResponse({"data": doctors})


@login_required
@group_required("Управления палатами")
def update_doctor_to_bed(request):
    request_data = json.loads(request.body)
    doctor_obj = request_data.get('doctor')
    result = PatientToBed.update_doctor(doctor_obj)
    return status_response(result)


@login_required
@group_required("Управления палатами")
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
@group_required("Управления палатами")
def save_patient_without_bed(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk')
    patient_obj = request_data.get('patient_obj')
    PatientStationarWithoutBeds(direction_id=patient_obj["direction_pk"], department_id=department_pk).save()
    return status_response(True)


@login_required
@group_required("Управления палатами")
def delete_patient_without_bed(request):
    request_data = json.loads(request.body)
    patient_obj = request_data.get('patient_obj')
    PatientStationarWithoutBeds.objects.get(direction_id=patient_obj["direction_pk"]).delete()
    return status_response(True)
