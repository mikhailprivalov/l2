import simplejson as json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from api.cases.helpers import get_case_direction_tree
from api.cases.stationar_func import (
    hosp_get_lab_iss,
    hosp_get_text_iss,
)
from clients.models import Card
from directions.models import Issledovaniya, Napravleniya
from directory.models import HospitalService
from laboratory.decorators import group_required
from appconf.manager import SettingManager
from django.db.models import Q

from laboratory.utils import strfdatetime
from pharmacotherapy.models import ProcedureList


@login_required
@group_required('Врач параклиники', 'Врач консультаций')
def search(request):
    data = json.loads(request.body)
    pk = int(data["q"])
    if pk >= 4600000000000:
        pk -= 4600000000000
        pk //= 10
    result = {"ok": False, "message": "Не найдено", "data": {}}
    original_direction = None
    original_view = None
    need_to_open_original = False

    for i in Issledovaniya.objects.filter(napravleniye__pk=pk, research__is_case=False):
        direction: Napravleniya = i.napravleniye
        if direction.parent_case:
            if direction.parent_case.napravleniye_id:
                if i.research.is_doc_refferal:
                    original_view = 'consultation'
                elif i.research.is_paraclinic:
                    original_view = 'paraclinical'
                elif i.research.podrazdeleniye and i.research.podrazdeleniye.p_type == 2:
                    original_view = 'laboratory'
                elif i.research.is_microbiology:
                    original_view = 'morfology'
                elif i.research.is_citology:
                    original_view = 'morfology'
                elif i.research.is_gistology:
                    original_view = 'morfology'
                elif i.research.is_form:
                    original_view = 'forms'
                if original_view:
                    original_direction = pk
                need_to_open_original = True
                pk = direction.parent_case.napravleniye_id
        break

    tree_direction = get_case_direction_tree(pk)
    i: Issledovaniya
    for i in Issledovaniya.objects.filter(napravleniye__pk=pk, research__is_case=True):
        direction: Napravleniya = i.napravleniye
        card: Card = direction.client
        result["ok"] = True
        result["message"] = ""
        if direction.cancel:
            result["message"] = "Направление было отменено"
        forbidden_edit = False  # make true for closed case
        child_issledovaniye, child_research_title, child_direction = '', '', ''
        for iss in tree_direction:
            if i.pk == iss['parent_iss']:
                child_issledovaniye = iss['issledovaniye']
                iss_obj = Issledovaniya.objects.filter(pk=child_issledovaniye).first()
                if iss_obj:
                    child_direction = iss_obj.napravleniye.pk
                    child_research_title = iss_obj.research.title
                    if not original_view:
                        if iss_obj.research.is_doc_refferal:
                            original_view = 'consultation'
                        elif iss_obj.research.is_paraclinic:
                            original_view = 'paraclinical'
                        elif iss_obj.research.podrazdeleniye and iss_obj.research.podrazdeleniye.p_type == 2:
                            original_view = 'laboratory'
                        elif iss_obj.research.is_microbiology:
                            original_view = 'morfology'
                        elif iss_obj.research.is_citology:
                            original_view = 'morfology'
                        elif iss_obj.research.is_gistology:
                            original_view = 'morfology'
                        elif iss_obj.research.is_form:
                            original_view = 'forms'
                break

        if not child_research_title or child_research_title == '-1':
            first_child: Napravleniya = Napravleniya.objects.filter(parent_case=i).order_by('id').first()
            if first_child:
                child_direction = first_child.pk
                iss: Issledovaniya = first_child.issledovaniya_set.first()
                if iss:
                    child_issledovaniye = iss.pk
                    child_research_title = iss.research.title

        result["data"] = {
            "direction": direction.pk,
            "cancel": direction.cancel,
            "fin_pk": direction.istochnik_f_id,
            "iss": i.pk,
            "parentIssledovaniye": direction.parent.pk if direction.parent else '-1',
            "caseTitle": i.research.title,
            "childResearch": None,
            "forbiddenToEdit": forbidden_edit,
            "closed": direction.total_confirmed,
            "originalDirection": {
                'id': original_direction or child_direction,
                'view': original_view,
                'open': need_to_open_original,
            },
            "patient": {
                "fioWithAge": card.individual.fio(full=True),
                "card": card.number_with_type(),
                "base": card.base_id,
                "cardPk": card.pk,
                "individualPk": card.individual_id,
            },
            "tree": list(
                map(
                    lambda dirc: {
                        **dirc,
                        "research_title": dirc["research_title"],
                        "isCurrent": int(dirc["direction"]) == pk,
                        "cancel": Napravleniya.objects.get(pk=dirc["direction"]).cancel,
                        "correct_level": dirc["correct_level"],
                        "color": dirc["color"],
                        "issledovaniye": dirc["issledovaniye"],
                        "order": dirc["order"],
                    },
                    tree_direction,
                )
            ),
            "counts": {
                'laboratory': 0,
                'paraclinical': 0,
                'consultation': 0,
                'morfology': 0,
                'pharmacotherapy': 0,
                'forms': 0,
                'all': 0,
            },
        }

        if child_issledovaniye and child_direction and child_research_title:
            result['data']['childResearch'] = {
                "issledovaniye": child_issledovaniye,
                "direction": child_direction,
                "title": child_research_title,
            }

        for i in Issledovaniya.objects.filter(napravleniye__pk=pk, research__is_case=True).distinct():
            result['data']['counts']["laboratory"] += Napravleniya.objects.filter(parent_case=i, issledovaniya__research__podrazdeleniye__p_type=2).distinct().count()
            result['data']['counts']["paraclinical"] += Napravleniya.objects.filter(parent_case=i, issledovaniya__research__is_paraclinic=True).distinct().count()
            result['data']['counts']["consultation"] += Napravleniya.objects.filter(parent_case=i, issledovaniya__research__is_doc_refferal=True).distinct().count()
            result['data']['counts']["morfology"] += (
                Napravleniya.objects.filter(parent_case=i)
                .filter(Q(issledovaniya__research__is_microbiology=True) | Q(issledovaniya__research__is_citology=True) | Q(issledovaniya__research__is_gistology=True))
                .distinct()
                .count()
            )
            result['data']['counts']["pharmacotherapy"] += ProcedureList.objects.filter(history=i.napravleniye, cancel=False, diary__issledovaniya__time_confirmation__isnull=False).count()
            result['data']['counts']["forms"] += Napravleniya.objects.filter(parent_case=i, issledovaniya__research__is_form=True).distinct().count()
            result['data']['counts']["all"] += Napravleniya.objects.filter(parent_case=i).count()
        break
    return JsonResponse(result)


@login_required
@group_required('Врач параклиники', 'Врач консультаций')
def hosp_services_by_type(request):
    data = json.loads(request.body)
    base_direction_pk = int(data["direction"] or 0)
    r_type = data["r_type"]
    result = []
    type_by_key = HospitalService.TYPES_BY_KEYS.get(r_type, -1)
    for i in Issledovaniya.objects.filter(napravleniye__pk=base_direction_pk, research__is_case=True):
        hosp_research = i.research
        if int(data['hospResearch']) > -1:
            hosp_research = int(data['hospResearch'])
        for hs in HospitalService.objects.filter(site_type=type_by_key, main_research=hosp_research, hide=False):
            result.append(
                {
                    "pk": hs.pk,
                    "title": hs.slave_research.title,
                    "short_title": hs.slave_research.short_title,
                    "main_title": hs.main_research.title,
                }
            )
    return JsonResponse({"data": result})


@login_required
@group_required('Врач параклиники', 'Врач консультаций')
def make_service(request):
    data = json.loads(request.body)
    main_direction = Napravleniya.objects.get(pk=data["main_direction"])
    parent_iss = Issledovaniya.objects.filter(napravleniye=main_direction, research__is_case=True).first()
    service = HospitalService.objects.get(pk=data["service"])
    TADP = SettingManager.get("tadp", default='Температура', default_type='s')
    if "Врач стационара" not in [str(x) for x in request.user.groups.all()] and TADP not in service.slave_research.title:
        return JsonResponse({"pk": None})
    result = Napravleniya.gen_napravleniya_by_issledovaniya(
        main_direction.client_id,
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
        parent_iss=parent_iss.pk,
        rmis_slot=None,
    )
    pk = result["list_id"][0]
    return JsonResponse({"pk": pk})


@login_required
def directions_by_key(request):
    data = json.loads(request.body)
    pk = data["caseId"]
    view = data["view"]
    directions = Napravleniya.objects.filter(parent_case__napravleniye_id=pk)

    if view == 'laboratory':
        directions = directions.filter(issledovaniya__research__podrazdeleniye__p_type=2)
    elif view == 'morfology':
        directions = directions.filter(Q(issledovaniya__research__is_microbiology=True) | Q(issledovaniya__research__is_citology=True) | Q(issledovaniya__research__is_gistology=True))
    elif view == 'paraclinical':
        directions = directions.filter(issledovaniya__research__is_paraclinic=True)
    elif view == 'consultation':
        directions = directions.filter(issledovaniya__research__is_doc_refferal=True)
    elif view == 'forms':
        directions = directions.filter(issledovaniya__research__is_form=True)

    directions = directions.distinct().order_by('id')

    return JsonResponse(
        {
            'rows': [
                {
                    'pk': x.pk,
                    'confirm': x.total_confirmed,
                    'date_create': strfdatetime(x.data_sozdaniya_local, "%d.%m.%Y"),
                    'researches_short': [y.short_title for y in x.services],
                    'researches': [y.title for y in x.services],
                    'showResults': x.issledovaniya_set.all().filter(research__podrazdeleniye__p_type=2).exists(),
                }
                for x in directions
            ]
        }
    )


@login_required
def aggregate(request):
    data = json.loads(request.body)
    pk = data.get('caseDirection', -1)
    view = data["view"]
    directions = Napravleniya.objects.filter(parent_case__napravleniye_id=pk)

    if view == 'laboratory':
        directions = directions.filter(issledovaniya__research__podrazdeleniye__p_type=2)
    elif view == 'morfology':
        directions = directions.filter(Q(issledovaniya__research__is_microbiology=True) | Q(issledovaniya__research__is_citology=True) | Q(issledovaniya__research__is_gistology=True))
    elif view == 'paraclinical':
        directions = directions.filter(issledovaniya__research__is_paraclinic=True)
    elif view == 'consultation':
        directions = directions.filter(issledovaniya__research__is_doc_refferal=True)
    elif view == 'forms':
        directions = directions.filter(issledovaniya__research__is_form=True)

    directions = directions.distinct().order_by('id')

    if view == 'laboratory':
        result = hosp_get_lab_iss([x.pk for x in directions])
    else:
        result = hosp_get_text_iss([x.pk for x in directions])
    return JsonResponse(result, safe=False)
