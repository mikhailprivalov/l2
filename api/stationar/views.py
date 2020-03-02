from collections import defaultdict

import simplejson as json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from api.stationar.stationar_func import get_direction_attrs, hosp_get_lab_iss, forbidden_edit_dir, \
    hosp_get_hosp_direction, hosp_get_text_iss, get_temperature_list, desc_to_data
from clients.models import Card
from directions.models import Issledovaniya, Napravleniya
from directory.models import HospitalService
from laboratory.decorators import group_required
from appconf.manager import SettingManager


TADP = SettingManager.get("tadp", default='Температура', default_type='s')


@login_required
@group_required("Врач стационара", "t, ad, p")
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
        forbidden_edit = forbidden_edit_dir(direction.pk)
        result["data"] = {
            "direction": direction.pk,
            "cancel": direction.cancel,
            "fin_pk": direction.istochnik_f_id,
            "iss": i.pk,
            "iss_title": i.research.title,
            "forbidden_edit": forbidden_edit or "Врач стационара" not in [str(x) for x in request.user.groups.all()],
            "soft_forbidden": not forbidden_edit,
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
@group_required("Врач стационара", "t, ad, p")
def counts(request):
    data = json.loads(request.body)
    pk = int(data["direction"])
    every = data.get("every", False)
    result = defaultdict(int)

    if every:
        hosps = list(
            map(
                lambda d: d["direction"],
                filter(
                    lambda d: not Napravleniya.objects.get(pk=d["direction"]).cancel,
                    hosp_get_hosp_direction(pk)
                )
            )
        )
        result["all"] += 1
    else:
        hosps = [pk]

    for i in Issledovaniya.objects.filter(napravleniye__pk__in=hosps, research__is_hospital=True).distinct():
        for k in HospitalService.TYPES_BY_KEYS:
            hss = HospitalService.objects.filter(
                main_research=i.research,
                site_type=HospitalService.TYPES_BY_KEYS[k]
            )
            nested = Napravleniya.objects.filter(
                parent=i,
                issledovaniya__research__in=[x.slave_research for x in hss]
            ).distinct()
            result[k] += nested.count()
        result["laboratory"] += Napravleniya.objects.filter(parent=i,
                                                            issledovaniya__research__podrazdeleniye__p_type=2).distinct().count()
        result["paraclinical"] += Napravleniya.objects.filter(parent=i,
                                                              issledovaniya__research__is_paraclinic=True).distinct().count()
        result["consultation"] += Napravleniya.objects.filter(parent=i,
                                                              issledovaniya__research__is_doc_refferal=True).distinct().count()
        result["all"] += Napravleniya.objects.filter(parent=i).count()
    return JsonResponse(dict(result))


@login_required
@group_required("Врач стационара", "t, ad, p")
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
@group_required("Врач стационара", "t, ad, p")
def make_service(request):
    data = json.loads(request.body)
    main_direction = Napravleniya.objects.get(pk=data["main_direction"])
    parent_iss = Issledovaniya.objects.filter(napravleniye=main_direction, research__is_hospital=True).first()
    service = HospitalService.objects.get(pk=data["service"])
    if "Врач стационара" not in [str(x) for x in request.user.groups.all()] and TADP not in service.slave_research.title:
        return JsonResponse({"pk": None})
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
def directions_by_key(request):
    data = json.loads(request.body)
    base_direction_pk = int(data["direction"])
    r_type = data["r_type"]
    every = data.get("every", False)
    level = -1 if every else 2
    type_by_key = HospitalService.TYPES_BY_KEYS.get(r_type, -1)
    if type_by_key == -1:
        type_service = HospitalService.TYPES_REVERSED.get(r_type, "None")
        result = get_direction_attrs(base_direction_pk, type_service=type_service, level=level)
    else:
        result = get_direction_attrs(base_direction_pk, site_type=type_by_key, level=level)
    return JsonResponse({"data": list(reversed(result))})


@login_required
def aggregate_laboratory(request):
    data = json.loads(request.body)
    pk = data.get('pk', -1)
    extract = data.get('extract', False)
    result = hosp_get_lab_iss(pk, extract)
    return JsonResponse(result)


@login_required
def aggregate_desc(request):
    data = json.loads(request.body)
    pk = data.get('pk', -1)
    extract = data.get('extract', False)
    r_type = data.get("r_type")
    type_service = HospitalService.TYPES_REVERSED.get(r_type, None) if r_type != 'desc' else 'desc'
    if type_service == "diaries":
        iss = Issledovaniya.objects.get(pk=pk)
        diaries_researches = [x.slave_research for x in HospitalService.objects.filter(site_type=HospitalService.TYPES_BY_KEYS["diaries"], main_research=iss.research)]
        num_dirs = [x.pk for x in Napravleniya.objects.filter(issledovaniya__research__in=diaries_researches, parent=iss, issledovaniya__time_confirmation__isnull=False)]
        result = desc_to_data(num_dirs, True)
    else:
        result = hosp_get_text_iss(pk, extract, mode=type_service)
    return JsonResponse(result, safe=False)


@login_required
def aggregate_tadp(request):
    data = json.loads(request.body)
    directions = data.get('directions', [])
    result = {}
    for pk in directions:
        if not result:
            result = get_temperature_list(pk)
        else:
            next_result = get_temperature_list(pk)
            for k in next_result:
                merge_sub_tadp(result[k], next_result[k])
    return JsonResponse(result)


def merge_sub_tadp(a, b):
    try:
        a['data'].extend(b['data'])
    except:
        pass
    try:
        a['xtext'].extend(b['xtext'])
    except:
        pass
