from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from directory.models import Culture, GroupCulture, Antibiotic, GroupAntibiotic, AntibioticSets
import simplejson as json


@login_required
def load_culture(request):
    request_data = json.loads(request.body)
    type = request_data['type']
    searchObj = request_data['searchObj']
    groups = [{"pk": -3, "title": "не найдено"}]
    elements = []
    if searchObj == 'Бактерии':
        elements = Culture.get_cultures(type)
        groups = GroupCulture.get_all_cultures_groups()
        groups.insert(0, {"pk": -2, "title": "Без группы"})
        groups.insert(0, {"pk": -1, "title": "Все"})

    if searchObj == 'Антибиотики':
        elements = Antibiotic.get_antibiotics(type)
        groups = GroupAntibiotic.get_all_antibiotic_groups()
        groups.insert(0, {"pk": -2, "title": "Без группы"})
        groups.insert(0, {"pk": -1, "title": "Все"})

    return JsonResponse({"groups": groups, "elements": elements})


@login_required
def save_culture(request):
    request_data = json.loads(request.body)
    types_object = request_data['TypesObject']
    title = request_data['title']
    fsli = request_data['fsli']
    pk = request_data['pk']
    hide = request_data['hide']

    if types_object == 'Бактерии':
        Culture.culture_save(pk, title, fsli, hide)

    if types_object == 'Антибиотики':
        Antibiotic.antibiotic_save(pk, title, fsli, hide)

    result = {"ok": True, "message": ""}

    return JsonResponse(result)


@login_required
def save_group(request):
    request_data = json.loads(request.body)
    types_object = request_data['TypesObject']
    types_group = request_data['typeGroups']
    obj = request_data['obj']

    if types_object == 'Бактерии' and types_group == 'Группы':
        for i in obj:
            if 'group' in i.keys() and 'elements' in i.keys():
                Culture.culture_update_group(i['group'], i['elements'])

    if types_object == 'Антибиотики' and types_group == 'Группы':
        for i in obj:
            if 'group' in i.keys() and 'elements' in i.keys():
                Antibiotic.antibiotic_update_group(i['group'], i['elements'])

    if types_object == 'Антибиотики' and types_group == 'Наборы':
        set = request_data['set']
        if 'group' in set.keys() and 'elements' in set.keys():
            AntibioticSets.update_antibiotic_set_elements(set['group'], set['elements'])

    result = {"ok": True, "message": ""}

    return JsonResponse(result)


@login_required
def new_group(request):
    request_data = json.loads(request.body)
    types_object = request_data['TypesObject']
    types_group = request_data['typeGroups']
    title = request_data['newgroup']

    result = {"ok": False, "message": "Ошибка"}

    if types_object == 'Бактерии':
        obj = GroupCulture.create_culture_group(title)
        result = {"ok": True, "message": "", "obj": obj.as_dict()}

    if types_object == 'Антибиотики' and types_group == 'Группы':
        obj = GroupAntibiotic.create_antibiotic_group(title)
        result = {"ok": True, "message": "", "obj": obj.as_dict()}

    if types_object == 'Антибиотики' and types_group == 'Наборы':
        obj = AntibioticSets.create_antibiotic_set(title)
        result = {"ok": True, "message": "", "obj": obj.as_dict()}

    return JsonResponse(result)


def load_antibiotic_set(request):
    request_data = json.loads(request.body)
    types_object = request_data['TypesObject']
    types_group = request_data['typeGroups']
    groups = [{"pk": -2, "title": "не найдено"}]

    if types_object == 'Антибиотики' and types_group == 'Наборы':
        groups = AntibioticSets.get_antibiotic_set()

    return JsonResponse({"groups": groups})


def load_set_elements(request):
    request_data = json.loads(request.body)
    types_group = request_data['typeGroups']
    result = {""}

    if types_group == 'Наборы' and request_data['type'] and request_data['type'] != "Все":
        title = request_data['type']
        result = AntibioticSets.get_antibiotic_set_elements(title)

    return JsonResponse({"elements": result})


@login_required
def update_group(request):
    request_data = json.loads(request.body)
    types_object = request_data['TypesObject']
    types_group = request_data['typeGroups']
    obj = request_data['obj']

    if types_object == 'Бактерии' and types_group == 'Группы':
        if 'pk' in obj.keys() and 'title' in obj.keys() and 'hide' in obj.keys():
            GroupCulture.update_culture_group(obj['pk'], obj['title'], obj['hide'])

    if types_object == 'Антибиотики' and types_group == 'Группы':
        if 'pk' in obj.keys() and 'title' in obj.keys() and 'hide' in obj.keys():
            GroupAntibiotic.update_antibiotic_group(obj['pk'], obj['title'], obj['hide'])

    if types_object == 'Антибиотики' and types_group == 'Наборы':
        if 'pk' in obj.keys() and 'title' in obj.keys() and 'hide' in obj.keys():
            AntibioticSets.update_antibiotic_set(obj['pk'], obj['title'], obj['hide'])

    return JsonResponse({"ok": True, "message": ""})


@login_required
def get_bac_groups(request):
    groups = GroupCulture.objects.filter(hide=False).order_by('title')
    return JsonResponse({
        "groups": [{
            "pk": x.pk,
            "title": x.title,
        } for x in groups]
    })


@login_required
def get_antibiotic_groups(request):
    groups = GroupAntibiotic.objects.filter(hide=False).order_by('title')
    result = {
        "groups": [*[{
            "pk": x.pk,
            "title": x.title,
        } for x in groups], {"pk": -1, "title": "Все антибиотики"}],
        "groupsObj": {},
        "antibiotics": {},
        "sets": [{
            "pk": x.pk,
            "title": x.title,
            "ids": [y.pk for y in x.get_not_hidden_antibiotics()]
        } for x in AntibioticSets.objects.filter(hide=False).order_by('title')]
    }

    anti: Antibiotic
    for anti in Antibiotic.objects.all().order_by('title'):
        result["antibiotics"][anti.pk] = anti.title
        if anti.hide:
            continue
        if -1 not in result["groupsObj"]:
            result["groupsObj"][-1] = []
        result["groupsObj"][-1].append(anti.as_dict())

        if anti.group_antibiotic:
            if anti.group_antibiotic.pk not in result["groupsObj"]:
                result["groupsObj"][anti.group_antibiotic.pk] = []

            result["groupsObj"][anti.group_antibiotic.pk].append(anti.as_dict())
    return JsonResponse(result)


@login_required
def get_bac_by_group(request):
    request_data = json.loads(request.body)
    group_pk = request_data["groupId"]

    return JsonResponse({
        "list": [{
            "pk": x.pk,
            "title": x.title,
        } for x in Culture.objects.filter(group_culture_id=group_pk, hide=False).order_by('title')]
    })


@login_required
def package_group_create(request):
    request_data = json.loads(request.body)
    title = request_data["title"]
    types_object = request_data["typesObject"]
    elements = request_data["elements"]

    if types_object == 'Бактерии':
        obj = GroupCulture.create_culture_group(title)
        pks = []
        for e in elements:
            if e["title"]:
                pks.append(Culture.culture_save(-1, e["title"], e["fsli"]).pk)
        Culture.culture_update_group(group=obj.pk, elements=pks)
        return JsonResponse({"ok": True, "obj": obj.as_dict()})
    elif types_object == 'Антибиотики':
        obj = GroupAntibiotic.create_antibiotic_group(title)
        pks = []
        for e in elements:
            if e["title"]:
                pks.append(Antibiotic.antibiotic_save(-1, e["title"], e["fsli"]).pk)
        Antibiotic.antibiotic_update_group(group=obj.pk, elements=pks)
        return JsonResponse({"ok": True, "obj": obj.as_dict()})

    return JsonResponse({"ok": False, "message": "Неизвестные параметры"})
