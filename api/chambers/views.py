from users.models import DoctorProfile
from podrazdeleniya.models import Chamber, Bed

import simplejson as json
from django.http import JsonResponse

from directory.models import Researches
from directions.models import Issledovaniya


def get_list_patients(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    # print(department_pk)
    researches_pk = list(Researches.objects.values_list('pk', flat=True).filter(podrazdeleniye_id=int(department_pk)))
    # print(researches_pk)
    if not researches_pk:
        return JsonResponse({"result": []})
    clients = [{"fio": i.napravleniye.client.individual.fio(),
                "age": i.napravleniye.client.individual.age(),
                "pk": i.napravleniye.client.individual.pk} for i in Issledovaniya.objects.filter(research_id__in=researches_pk, hospital_department_override_id=department_pk)]
    # print(clients)
    return JsonResponse({"data": clients})


def get_chambers(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    # print(department_pk)
    chambers = [{'label': g.title, 'pk': g.pk} for g in Chamber.objects.filter(podrazdelenie_id=int(department_pk))]
    # print(chambers)
    return JsonResponse({"data": chambers})


def get_beds(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    print(department_pk)
    chambers_pk = list(Chamber.objects.values_list('pk', flat=True).filter(podrazdelenie_id=int(department_pk)))
    print(chambers_pk)
    beds = [{'bed_number': bed.bed_number, 'pk': bed.pk, 'pk_chamber': bed.chamber_id} for bed in Bed.objects.filter(chamber_id__in=chambers_pk)]
    print(beds)
    return JsonResponse({"data": beds})
