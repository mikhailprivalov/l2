from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from api.stationar.stationar_func import get_direction_attrs
from clients.models import Card
from directions.models import Issledovaniya, Napravleniya
from directory.models import HospitalService
from laboratory.decorators import group_required
import simplejson as json

from laboratory.utils import strdate


@login_required
@group_required("Врач стационара")
def load(request):
    data = json.loads(request.body)
    result = {"ok": False, "message": "Нет данных", "data": {}}
    pk = int(data["pk"])
    if pk >= 4600000000000:
        pk -= 4600000000000
        pk //= 10
    for i in Issledovaniya.objects.filter(napravleniye__pk=pk, research__is_hospital=True):
        direction: Napravleniya = i.napravleniye
        card: Card = direction.client
        result["ok"] = True
        result["message"] = ""
        result["data"] = {
            "direction": direction.pk,
            "fin_pk": direction.istochnik_f.pk,
            "iss": i.pk,
            "iss_title": i.research.title,
            "patient": {
                "fio_age": card.individual.fio(full=True),
                "card": card.number_with_type(),
                "base": card.base_id,
                "card_pk": card.pk,
                "individual_pk": card.individual_id,
            },
        }
        break
    return JsonResponse(result)


@login_required
@group_required("Врач стационара")
def counts(request):
    data = json.loads(request.body)
    pk = int(data["direction"])
    result = {}
    for i in Issledovaniya.objects.filter(napravleniye__pk=pk, research__is_hospital=True):
        by_keys = {}
        for k in HospitalService.TYPES_BY_KEYS:
            hss = HospitalService.objects.filter(
                main_research=i.research,
                site_type=HospitalService.TYPES_BY_KEYS[k]
            )
            nested = Napravleniya.objects.filter(
                parent=i,
                issledovaniya__research__in=[x.slave_research for x in hss]
            ).distinct()
            by_keys[k] = nested.count()
        result = {
            "laboratory": Napravleniya.objects.filter(parent=i,
                                                      issledovaniya__research__podrazdeleniye__p_type=2).distinct().count(),
            "paraclinical": Napravleniya.objects.filter(parent=i,
                                                        issledovaniya__research__is_paraclinic=True).distinct().count(),
            "consultation": Napravleniya.objects.filter(parent=i,
                                                        issledovaniya__research__is_doc_refferal=True).distinct().count(),
            **by_keys,
        }
    return JsonResponse(result)


@login_required
@group_required("Врач стационара")
def hosp_services_by_type(request):
    data = json.loads(request.body)
    base_direction_pk = int(data["direction"])
    r_type = data["r_type"]
    result = []
    type_by_key = HospitalService.TYPES_BY_KEYS.get(r_type, -1)
    for i in Issledovaniya.objects.filter(napravleniye__pk=base_direction_pk, research__is_hospital=True):
        for hs in HospitalService.objects.filter(site_type=type_by_key, main_research=i.research, hide=False):
            result.append({
                "pk": hs.pk,
                "title": hs.slave_research.title,
                "main_title": hs.main_research.title,
            })
    return JsonResponse({"data": result})


@login_required
@group_required("Врач стационара")
def make_service(request):
    data = json.loads(request.body)
    main_direction = Napravleniya.objects.get(pk=data["main_direction"])
    parent_iss = Issledovaniya.objects.filter(napravleniye=main_direction, research__is_hospital=True).first()
    service = HospitalService.objects.get(pk=data["service"])
    result = Napravleniya.gen_napravleniya_by_issledovaniya(main_direction.client.pk,
                                                            "",
                                                            None,
                                                            "",
                                                            None,
                                                            request.user.doctorprofile,
                                                            {-1: [service.slave_research.pk]},
                                                            {},
                                                            False,
                                                            {},
                                                            vich_code="",
                                                            count=1,
                                                            discount=0,
                                                            parent_iss=parent_iss.pk)
    pk = result["list_id"][0]
    return JsonResponse({"pk": pk})


@login_required
@group_required("Врач стационара")
def directions_by_key(request):
    data = json.loads(request.body)
    base_direction_pk = int(data["direction"])
    r_type = data["r_type"]
    type_by_key = HospitalService.TYPES_BY_KEYS.get(r_type, -1)
    if type_by_key == -1:
        type_service = {
            "paraclinical": "is_paraclinic",
            "laboratory": "is_lab",
            "consultation": "is_doc_refferal",
        }.get(r_type, "None")
        result = get_direction_attrs(base_direction_pk, type_service=type_service)
    else:
        result = get_direction_attrs(base_direction_pk, site_type=type_by_key)
    return JsonResponse({"data": list(result)})
