from laboratory.decorators import group_required
from django.contrib.auth.decorators import login_required

import simplejson as json
from django.http import JsonResponse

from podrazdeleniya.models import Chamber, Bed, PatientToBed, PatientStationarWithoutBeds
from directions.models import Napravleniya
from users.models import DoctorProfile

from utils.response import status_response

import datetime
from .sql_func import patients_stationar_unallocated_sql


@login_required
@group_required("Управления палатами")
def get_unallocated_patients(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    patients = [
        {
            "fio": f'{patient.family} {patient.name} {patient.patronymic if patient.patronymic else None}',
            "age": patient.age,
            "short_fio": f'{patient.family} {patient.name[0]}. {patient.patronymic[0] if patient.patronymic else None}.',
            "sex": patient.sex,
            "direction_pk": patient.napravleniye_id,
        }
        for patient in patients_stationar_unallocated_sql(department_pk)
    ]
    return JsonResponse({"data": patients})


@login_required
@group_required("Управления палатами")
def get_chambers_and_beds(request):
    request_data = json.loads(request.body)
    chambers = []
    for ward in Chamber.objects.filter(podrazdelenie_id=request_data.get('department_pk', -1)):
        chamber = {
            "pk": ward.pk,
            "label": ward.title,
            "beds": [],
        }
        for bed in Bed.objects.filter(chamber_id=ward.pk).prefetch_related('chamber'):
            chamber["beds"].append({"pk": bed.pk, "bed_number": bed.bed_number, "doctor": [], "patient": []})
            history = PatientToBed.objects.filter(bed_id=bed.pk, date_out__isnull=True).last()
            if history:
                direction_obj = Napravleniya.objects.get(pk=history.direction.pk)
                ind_card = direction_obj.client
                patient_data = ind_card.get_data_individual()
                chamber["beds"][-1]["patient"] = [
                    {"fio": patient_data["fio"], "short_fio": patient_data["short_fio"], "age": patient_data["age"], "sex": patient_data["sex"], "direction_pk": history.direction_id}
                ]
                if history.doctor:
                    chamber["beds"][-1]["doctor"] = [{
                        "fio": history.doctor.get_full_fio(),
                        "pk": history.doctor.pk,
                        "highlight": False,
                        "short_fio": history.doctor.get_fio(),
                    }]
        chambers.append(chamber)
    return JsonResponse({"data": chambers})


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
    doctors = [{'fio': doctor.get_full_fio(), 'pk': doctor.pk, 'highlight': False, 'short_fio': doctor.get_fio()} for doctor in DoctorProfile.objects.filter(podrazdeleniye_id=department_pk)]
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
    patients = []
    for patient in PatientStationarWithoutBeds.objects.filter(department_id=department_pk):
        direction_obj = Napravleniya.objects.get(pk=patient.direction.pk)
        ind_card = direction_obj.client
        patient_data = ind_card.get_data_individual()
        patients.append(
            {
                "fio": patient_data["fio"],
                "short_fio": patient_data["short_fio"],
                "age": patient_data["age"],
                "sex": patient_data["sex"],
                "direction_pk": patient.direction_id
            }
        )
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
