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
        groups.insert(0, {"pk": -1, "title": "Все"})
        groups.insert(1, {"pk": -2, "title": "Без группы"})

    if searchObj == 'Антибиотики':
        elements = Antibiotic.get_antibiotics(type)
        groups = GroupAntibiotic.get_all_antibiotic_groups()
        groups.insert(0, {"pk": -1, "title": "Все"})
        groups.insert(1, {"pk": -2, "title": "Без группы"})

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
        GroupCulture.create_culture_group(title)
        result = {"ok": True, "message": ""}

    if types_object == 'Антибиотики' and types_group == 'Группы':
        GroupAntibiotic.create_antibiotic_group(title)
        result = {"ok": True, "message": ""}

    if types_object == 'Антибиотики' and types_group == 'Наборы':
        AntibioticSets.create_antibiotic_set(title)
        result = {"ok": True, "message": ""}

    return JsonResponse(result)


def load_antibiotic_set(request):
    request_data = json.loads(request.body)
    types_object = request_data['TypesObject']
    types_group = request_data['typeGroups']
    groups = {"pk": -2, "title": "не найдено"}

    if types_object == 'Антибиотики' and types_group == 'Наборы':
        groups = AntibioticSets.get_antibiotic_set()

    return JsonResponse({"groups": groups})


def load_set_elements(request):
    request_data = json.loads(request.body)
    types_group = request_data['typeGroups']
    result = {"pk": -2, "title": "не загружено"}

    if types_group == 'Наборы' and request_data['type']:
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

    result = {"ok": True, "message": ""}

    return JsonResponse(result)


