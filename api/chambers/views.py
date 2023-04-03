from podrazdeleniya.models import Chamber, Bed, PatientToBed

import simplejson as json
from django.http import JsonResponse

from directory.models import Researches
from directions.models import Issledovaniya, Napravleniya

from clients.models import Individual

import datetime


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
            history = PatientToBed.objects.filter(bed=j.pk, extract__isnull=True).last()
            if history:
                direction_obj = Napravleniya.objects.get(pk=history.patient.pk)
                ind_card = direction_obj.client
                patient_data = ind_card.get_data_individual()
                clients_obj = Individual.objects.get(pk=history.patient.pk)
                short_fio = clients_obj.fio(short=True, dots=True)
                chamber["beds"].append(
                    {
                        "pk": j.pk,
                        "bed_number": j.bed_number,
                        "doc": {
                            'id': direction_obj.doc.pk,
                            'label': direction_obj.doc.fio,
                        },
                        "contents": [
                            {
                                "fio": patient_data["fio"],
                                "short_fio": short_fio,
                                "age": patient_data["age"],
                                "sex": patient_data["sex"],
                                "pk": history.patient_id
                            }
                        ]
                    }
                )
                print(chamber["beds"])
            else:
                chamber["beds"].append(
                    {
                        "pk": j.pk,
                        "bed_number": j.bed_number,
                        'doc': '',
                        "contents": []
                    }
                )
        chambers.append(chamber)
    return JsonResponse({"data": chambers})


def entrance_patient_to_bed(request):
    request_data = json.loads(request.body)
    bed_obj = request_data.get('beds')
    if not PatientToBed.objects.filter(bed_id=bed_obj["pk"], extract=None):
        bed = bed_obj['contents'][0]
        PatientToBed(patient_id=bed["pk"], bed_id=bed_obj["pk"]).save()
        bed_obj["statusSex"] = bed["sex"]
    return JsonResponse({'ok': True})


def extract_patient_bed(request):
    request_data = json.loads(request.body)
    patient_obj = request_data.get('patient')
    patient = PatientToBed.objects.filter(patient_id=patient_obj["pk"], extract=None).first()
    patient.extract = datetime.datetime.today()
    patient.save()
    return JsonResponse({'ok': True})


def filter_patient(patients):
    patients_beds = [patient.patient.pk for patient in PatientToBed.objects.filter(extract=None)]
    filtered_patients = []
    for i in patients:
        if i["pk"] not in patients_beds:
            filtered_patients.append(i)
    return filtered_patients


def get_patients(pk):
    researches_pk = list(Researches.objects.values_list('pk', flat=True).filter(podrazdeleniye_id=pk))
    if not researches_pk:
        return JsonResponse({"result": []})
    clients_obj = [{"fio": i.napravleniye.client.individual.fio(),
                    "age": i.napravleniye.client.individual.age(),
                    "short_fio": i.napravleniye.client.individual.fio(short=True, dots=True),
                    "sex": i.napravleniye.client.individual.sex,
                    "pk": i.napravleniye.client.individual.pk} for i in Issledovaniya.objects.filter(research_id__in=researches_pk, hospital_department_override_id=pk).exclude()]
    return clients_obj

