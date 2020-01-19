import simplejson as json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from api.stationar.stationar_func import get_direction_attrs, hosp_get_lab_iss, forbidden_edit_dir, hosp_get_hosp_direction, hosp_get_text_iss
from clients.models import Card
from directions.models import Issledovaniya, Napravleniya
from directory.models import HospitalService
from laboratory.decorators import group_required


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
        if direction.cancel:
            result["message"] = "Направление было отменено"
        result["data"] = {
            "direction": direction.pk,
            "cancel": direction.cancel,
            "fin_pk": direction.istochnik_f_id,
            "iss": i.pk,
            "iss_title": i.research.title,
            "forbidden_edit": forbidden_edit_dir(direction.pk),
            "patient": {
                "fio_age": card.individual.fio(full=True),
                "card": card.number_with_type(),
                "base": card.base_id,
                "card_pk": card.pk,
                "individual_pk": card.individual_id,
            },
            "tree": list(filter(
                lambda d: not d["cancel"],
                map(
                    lambda dirc: {
                        **dirc,
                        "research_title": dirc["research_title"].replace("отделение", "отд.").replace("Отделение", "Отд."),
                        "isCurrent": int(dirc["direction"]) == pk,
                        "cancel": Napravleniya.objects.get(pk=dirc["direction"]).cancel,
                    },
                    hosp_get_hosp_direction(pk)
                )
            ))
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
            "all": Napravleniya.objects.filter(parent=i).count(),
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
    result = Napravleniya.gen_napravleniya_by_issledovaniya(main_direction.client_id,
                                                            "",
                                                            None,
                                                            "",
                                                            None,
                                                            request.user.doctorprofile,
                                                            {-1: [service.slave_research_id]},
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
        type_service = HospitalService.TYPES_REVERSED.get(r_type, "None")
        result = get_direction_attrs(base_direction_pk, type_service=type_service, level=2)
    else:
        result = get_direction_attrs(base_direction_pk, site_type=type_by_key, level=2)
    return JsonResponse({"data": list(reversed(result))})


@login_required
@group_required("Врач стационара")
def aggregate_laboratory(request):
    data = json.loads(request.body)
    pk = data.get('pk', -1)
    extract = data.get('extract', False)
    result = hosp_get_lab_iss(pk, extract)
    return JsonResponse(result)


@login_required
@group_required("Врач стационара")
def aggregate_desc(request):
    data = json.loads(request.body)
    pk = data.get('pk', -1)
    extract = data.get('extract', False)
    r_type = data.get("r_type")
    type_service = HospitalService.TYPES_REVERSED.get(r_type, None)
    result = hosp_get_text_iss(pk, extract, mode=type_service)
    return JsonResponse({
        "data": result
    })
