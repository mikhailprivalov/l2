from users.models import DoctorProfile
from podrazdeleniya.models import Chamber, Bed, PatienToBed

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
                "sex": i.napravleniye.client.individual.sex,
                "pk": i.napravleniye.client.individual.pk} for i in Issledovaniya.objects.filter(research_id__in=researches_pk, hospital_department_override_id=department_pk)]
    # print(clients)
    return JsonResponse({"data": clients})


def get_chambers_and_bed(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    chambers = []
    for i in Chamber.objects.filter(podrazdelenie_id=int(department_pk)):
        chamber = {
            "pk": i.pk,
            "label": i.title,
            "beds": [],
        }
        for j in Bed.objects.filter(chamber=i.pk):
            history = PatienToBed.objects.filter(bed=j.pk, status=True).first()
            if history:
                chamber["beds"].append(
                    {
                        "pk": j.pk,
                        "bed_number": j.bed_number,
                        "statusSex": '',
                        "contents": [{"sex": history.patient.napravleniye.client.individual.sex, "age": history.patient.napravleniye.client.individual.age()}]
                    })
            else:
                chamber["beds"].append(
                    {
                        "pk": j.pk,
                        "bed_number": j.bed_number,
                        "statusSex": '',
                        "contents": []
                    }
                )
        chambers.append(chamber)
    # print(chambers)
    # chambers = [{'label': g.title, 'pk': g.pk} for g in Chamber.objects.filter(podrazdelenie_id=int(department_pk))]
    return JsonResponse({"data": chambers})


# def get_beds(request):
#     request_data = json.loads(request.body)
#     department_pk = request_data.get('department_pk', -1)
#     # print(department_pk)
#     chambers_pk = list(Chamber.objects.values_list('pk', flat=True).filter(podrazdelenie_id=int(department_pk)))
#     # print(chambers_pk)
#     beds = [{'bedNumber': bed.bed_number,
#              'pk': bed.pk,
#              'pkChamber': bed.chamber_id,
#              'status': bed.status_bed,
#              'sexStatus': '',
#              'ageStatus': '',
#              'contents': []} for bed in Bed.objects.filter(chamber_id__in=chambers_pk)]
#     for i in beds:
#         patient = PatienToBed.objects.filter(bed=i["pk"], status=True).first()
#         if patient:
#             i["sexStatus"] = patient.napravleniye.client.individual.sex
#             i["ageStatus"] = patient.napravleniye.client.individual.age()
#
#     return JsonResponse({"data": beds})

#
def load_data_bed(request):
    request_data = json.loads(request.body)
    chambers = get_color_and_status(request_data.get('chambers'))
    # print(beds)
    return JsonResponse({"data": chambers})


def get_color_and_status(chambers):
    # print(chambers)
    for g in chambers:
        # print(g)
        for i in g["beds"]:
            # print(i)
            if i["contents"]:
                for j in i["contents"]:
                    print(j)
                    if j["sex"] == 'м':
                        i["statusSex"] = 'man'
                    else:
                        i["statusSex"] = 'women'
    print(chambers)
    return chambers
    # for g in beds:
    #     if g['contents']:
    #         g['status'] = False
    #         res = g['contents']
    #         # print(res)
    #         for key in res:
    #             if key['age'] > 7:
    #                 g['ageStatus'] = True
    #             else:
    #                 g['ageStatus'] = False
    #             if key['sex'] == 'м':
    #                 g['sexStatus'] = 'man'
    #             else:
    #                 g['sexStatus'] = 'women'
    #     else:
    #         g['status'] = True
    #         g['sexStatus'] = ''
    # return beds


# def get_color_and_status(beds):
#     for g in beds:
#         if g['contents']:
#             g['status'] = False
#             res = g['contents']
#             # print(res)
#             for key in res:
#                 if key['sex'] == 'м':
#                     g['sexStatus'] = 'man'
#                 else:
#                     g['sexStatus'] = 'women'
#         else:
#             g['status'] = True
#             g['sexStatus'] = ''
#     return beds
#
#
# def check_age(key):
#     # print(key)
#     age = []
#     for g in key:
#         # print(g)
#         if not g['status']:
#             # print(g)
#             result = g['contents']
#             # print(result)
#             for i in result:
#                 # print(i)
#                 age.append(i['age'])
#     # print(age)
#     if not len(age) == 1:
#         min_age = min(age)
#         print(min_age)
#         max_age = max(age)
#         print(max_age)
#         if min_age == max_age:
#             key.append('OK')
#         else:
#             key.append('Ошибка: Девочка и мальчик в одной палате')
#         print(key)
#     return 'hello'
