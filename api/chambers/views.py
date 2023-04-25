from podrazdeleniya.models import Chamber, Bed, PatientToBed, PatientStationarWithoutBeds

import simplejson as json
from django.http import JsonResponse

from directions.models import Napravleniya

from clients.models import Individual
from users.models import DoctorProfile

from utils.response import status_response

import datetime
from datetime import date
from .sql_func import get_patients_stationar


def get_unallocated_patients(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    today = date.today()
    patients = [
        {
            "fio": f'{patient.family} {patient.name} {patient.patronymic}',
            "age": today.year - patient.birthday.year,
            "short_fio": f'{patient.family} {patient.name[0]}. {patient.patronymic[0]}.',
            "sex": patient.sex,
            "direction_pk": patient.napravleniye_id,
        } for patient in get_patients_stationar(department_pk)
    ]
    patients_beds = [patient.direction.pk for patient in PatientToBed.objects.filter(date_out=None)]
    patients_without_beds = [patient.direction.pk for patient in PatientStationarWithoutBeds.objects.filter(department=department_pk)]
    filtered_patients = []
    for i in patients:
        if i["direction_pk"] not in patients_beds and i["direction_pk"] not in patients_without_beds:
            filtered_patients.append(i)
    return JsonResponse({"data": filtered_patients})


def get_chambers_and_beds(request):
    request_data = json.loads(request.body)
    chambers = []
    for i in Chamber.objects.filter(podrazdelenie_id=request_data.get('department_pk', -1)):
        chamber = {
            "pk": i.pk,
            "label": i.title,
            "beds": [],
        }
        for j in Bed.objects.filter(chamber=i.pk):
            chamber["beds"].append(
                {
                    "pk": j.pk,
                    "bed_number": j.bed_number,
                    "doctor": [],
                    "patient": []
                }
            )
            history = PatientToBed.objects.filter(bed=j.pk, date_out__isnull=True).last()
            if history:
                direction_obj = Napravleniya.objects.get(pk=history.direction.pk)
                ind_card = direction_obj.client
                patient_data = ind_card.get_data_individual()
                individual_obj = Individual.objects.get(family=patient_data["family"])
                short_fio = individual_obj.fio(short=True, dots=True)
                chamber["beds"][-1]["patient"].append(
                    {
                        "fio": patient_data["fio"],
                        "short_fio": short_fio,
                        "age": patient_data["age"],
                        "sex": patient_data["sex"],
                        "direction_pk": history.direction_id
                    }
                )
                if history.doctor:
                    chamber["beds"][-1]["doctor"].append(
                        {
                            "fio": history.doctor.get_full_fio(),
                            "pk": history.doctor.pk,
                            "highlight": False,
                            "short_fio": history.doctor.get_fio(),
                        }
                    )
        chambers.append(chamber)
    return JsonResponse({"data": chambers})


def entrance_patient_to_bed(request):
    request_data = json.loads(request.body)
    bed_id = request_data.get('bed_id')
    direction_id = request_data.get('direction_id')
    if not PatientToBed.objects.filter(bed_id=bed_id, date_out=None).exists():
        PatientToBed(direction_id=direction_id, bed_id=bed_id).save()
    return status_response(True)


def extract_patient_bed(request):
    request_data = json.loads(request.body)
    patient_obj = request_data.get('patient')
    patient = PatientToBed.objects.filter(direction_id=patient_obj["direction_pk"], date_out=None).first()
    patient.date_out = datetime.datetime.today()
    patient.save()
    return status_response(True)


def get_attending_doctors(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    doctors = [{'fio': g.get_full_fio(), 'pk': g.pk, 'highlight': False, 'short_fio': g.get_fio()} for g in DoctorProfile.objects.filter(podrazdeleniye_id=department_pk)]
    return JsonResponse({"data": doctors})


def doctor_assigned_patient(request):
    request_data = json.loads(request.body)
    doctor_obj = request_data.get('doctor')
    direction_id = request_data.get('direction_id')
    doctor = PatientToBed.objects.filter(direction_id=direction_id, doctor=None, date_out=None).first()
    doctor.doctor_id = doctor_obj["pk"]
    doctor.save()
    return status_response(True)


def doctor_detached_patient(request):
    request_data = json.loads(request.body)
    doctor_obj = request_data.get('doctor')
    direction_id = request_data.get('direction_id')
    doctor = PatientToBed.objects.filter(doctor_id=doctor_obj["pk"], direction_id=direction_id, date_out=None).first()
    doctor.doctor = None
    doctor.save()
    return status_response(True)


def get_patients_without_bed(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    patients = []
    for patient in PatientStationarWithoutBeds.objects.filter(department_id=department_pk):
        direction_obj = Napravleniya.objects.get(pk=patient.direction.pk)
        ind_card = direction_obj.client
        patient_data = ind_card.get_data_individual()
        individual_obj = Individual.objects.get(family=patient_data["family"])
        short_fio = individual_obj.fio(short=True, dots=True)
        patients.append(
            {
                "fio": patient_data["fio"],
                "short_fio": short_fio,
                "age": patient_data["age"],
                "sex": patient_data["sex"],
                "direction_pk": patient.direction_id
            }
        )
    return JsonResponse({"data": patients})


def save_patient_without_bed(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    patient_obj = request_data.get('patient_obj')
    if department_pk != -1:
        PatientStationarWithoutBeds(direction_id=patient_obj["direction_pk"], department_id=department_pk).save()
    return status_response(True)


def delete_patient_without_bed(request):
    request_data = json.loads(request.body)
    patient_obj = request_data.get('patient_obj')
    PatientStationarWithoutBeds.objects.get(direction_id=patient_obj["direction_pk"]).delete()
    return status_response(True)
