from podrazdeleniya.models import Chamber, Bed, PatientToBed, PatientStationarWithoutBeds

import simplejson as json
from django.http import JsonResponse

from directory.models import Researches
from directions.models import Issledovaniya, Napravleniya

from clients.models import Individual
from users.models import DoctorProfile

import datetime
from datetime import date
from .sql_func import getting_patient_issledovaniya


def get_unallocated_patients(request):
    request_data = json.loads(request.body)
    patients_obj = get_patients(request_data.get('department_pk', -1))
    patients = filter_patient(patients_obj)
    return JsonResponse({"data": patients})


def get_chambers_and_beds(request):
    request_data = json.loads(request.body)
    chambers = []
    for i in Chamber.objects.filter(podrazdelenie_id=int(request_data.get('department_pk', -1))):
        chamber = {
            "pk": i.pk,
            "label": i.title,
            "beds": [],
        }
        for j in Bed.objects.filter(chamber=i.pk):
            history = PatientToBed.objects.filter(bed=j.pk, date_out__isnull=True).last()
            if history:
                direction_obj = Napravleniya.objects.get(pk=history.direction.pk)
                ind_card = direction_obj.client
                patient_data = ind_card.get_data_individual()
                clients_obj = Individual.objects.get(family=patient_data["family"])
                short_fio = clients_obj.fio(short=True, dots=True)
                doc = PatientToBed.objects.filter(bed=j.pk, date_out__isnull=True, doctor=None).last()
                if not doc:
                    chamber["beds"].append(
                        {
                            "pk": j.pk,
                            "bed_number": j.bed_number,
                            "doctor": [
                                {
                                    "fio": PatientToBed.objects.get(bed=j.pk, date_out__isnull=True).doctor.fio,
                                    "pk": PatientToBed.objects.get(bed=j.pk, date_out__isnull=True).doctor.pk,
                                    "short_fio": PatientToBed.objects.get(bed=j.pk, date_out__isnull=True).doctor.get_fio()
                                }
                            ],
                            "contents": [
                                {
                                    "fio": patient_data["fio"],
                                    "short_fio": short_fio,
                                    "age": patient_data["age"],
                                    "sex": patient_data["sex"],
                                    "pk": history.direction_id
                                }
                            ]
                        }
                    )
                else:
                    chamber["beds"].append(
                        {
                            "pk": j.pk,
                            "bed_number": j.bed_number,
                            "doctor": [],
                            "contents": [
                                {
                                    "fio": patient_data["fio"],
                                    "short_fio": short_fio,
                                    "age": patient_data["age"],
                                    "sex": patient_data["sex"],
                                    "pk": history.direction_id
                                }
                            ]
                        }
                    )
            else:
                chamber["beds"].append(
                    {
                        "pk": j.pk,
                        "bed_number": j.bed_number,
                        "doctor": [],
                        "contents": []
                    }
                )
        chambers.append(chamber)
    return JsonResponse({"data": chambers})


def entrance_patient_to_bed(request):
    request_data = json.loads(request.body)
    bed_obj = request_data.get('beds')
    if not PatientToBed.objects.filter(bed_id=bed_obj["pk"], date_out=None):
        bed = bed_obj["contents"][0]
        PatientToBed(direction_id=bed["pk"], bed_id=bed_obj["pk"]).save()
    return JsonResponse({'ok': True})


def extract_patient_bed(request):
    request_data = json.loads(request.body)
    patient_obj = request_data.get('patient')
    patient = PatientToBed.objects.filter(direction_id=patient_obj["pk"], date_out=None).first()
    patient.date_out = datetime.datetime.today()
    patient.save()
    return JsonResponse({'ok': True})


def get_attending_doctor(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    doctors = [
        {
            'fio': g.fio,
            'pk': g.pk,
            'short_fio': g.get_fio()
        } for g in DoctorProfile.objects.filter(podrazdeleniye_id=department_pk)
    ]
    return JsonResponse({"data": doctors})


def doctor_assigned_patient(request):
    request_data = json.loads(request.body)
    bed_obj = request_data.get('beds')
    doctor = PatientToBed.objects.filter(direction_id=bed_obj["contents"][0]["pk"], doctor=None, date_out=None).first()
    doctor.doctor_id = bed_obj["doctor"][0]["pk"]
    doctor.save()
    return JsonResponse({'ok': True})


def doctor_detached_patient(request):
    request_data = json.loads(request.body)
    doctor_obj = request_data.get('doctor')
    bed_obj = request_data.get('beds')
    doctor = PatientToBed.objects.filter(doctor_id=doctor_obj["pk"], direction_id=bed_obj["contents"][0]["pk"], date_out=None).first()
    doctor.doctor = None
    doctor.save()
    return JsonResponse({'ok': True})


def get_patients_without_bed(request):
    patients = []
    if PatientStationarWithoutBeds.objects.all():
        for patient in PatientStationarWithoutBeds.objects.all():
            direction_obj = Napravleniya.objects.get(pk=patient.direction.pk)
            ind_card = direction_obj.client
            patient_data = ind_card.get_data_individual()
            clients_obj = Individual.objects.get(family=patient_data["family"])
            short_fio = clients_obj.fio(short=True, dots=True)
            patients.append(
                {
                    "fio": patient_data["fio"],
                    "short_fio": short_fio,
                    "age": patient_data["age"],
                    "sex": patient_data["sex"],
                    "pk": patient.direction_id
                }
            )
    return JsonResponse({"data": patients})


def save_patient_without_bed(request):
    request_data = json.loads(request.body)
    patient_obj = request_data.get('patient_obj')
    PatientStationarWithoutBeds(direction_id=patient_obj["pk"]).save()
    return JsonResponse({'ok': True})


def delete_patient_without_bed(request):
    request_data = json.loads(request.body)
    patient_obj = request_data.get('patient_obj')
    entry = PatientStationarWithoutBeds.objects.get(direction_id=patient_obj["pk"])
    entry.delete()
    return JsonResponse({'ok': True})


def filter_patient(patients):
    patients_beds = [patient.direction.pk for patient in PatientToBed.objects.filter(date_out=None)]
    patients_without_beds = [patient.direction.pk for patient in PatientStationarWithoutBeds.objects.all()]
    filtered_patients = []
    for i in patients:
        if i["pk"] not in patients_beds and i["pk"] not in patients_without_beds:
            filtered_patients.append(i)
    return filtered_patients


def get_patients(hosp_id):
    patients = getting_patient_issledovaniya(hosp_id)
    clients_obj = []
    for g in patients:
        clients_obj.append(
            {
                "fio": f'{g.family} {g.name} {g.patronymic}',
                "age": calculate_age(g.birthday),
                "short_fio": f'{g.family} {g.name[0]}. {g.patronymic[0]}.',
                "sex": g.sex,
                "pk": g.napravleniye_id
            }
        )
    return clients_obj


def calculate_age(born):
    today = date.today()
    return today.year - born.year
