from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from directory.models import Culture, GroupCulture, Antibiotic, GroupAntibiotic, AntibioticSets
import simplejson as json


@login_required
def load_culture(request):
    type = request.GET.get('type')
    searchObj = request.GET.get('searchObj')
    groups = [{"pk": -2, "title": "не найдено"}]
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

    if types_object == 'Бактерии':
        Culture.culture_save(pk, title, fsli)

    if types_object == 'Антибиотики':
        Antibiotic.antibiotic_save(pk, title, fsli)

    result = {"ok": True, "message": ""}

    return JsonResponse(result)


@login_required
def save_group(request):
    request_data = json.loads(request.body)
    types_object = request_data['TypesObject']
    obj = request_data['obj']

    if types_object == 'Бактерии':
        for i in obj:
            if 'group' in i.keys() and 'elements' in i.keys():
                Culture.culture_update_group(i['group'], i['elements'])

    if types_object == 'Антибиотики':
        for i in obj:
            if 'group' in i.keys() and 'elements' in i.keys():
                Antibiotic.antibiotic_update_group(i['group'], i['elements'])

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
    # request_data = json.loads(request.body)
    # types_object = request_data['TypesObject']
    # types_group = request_data['typeGroups']
    types_object = request.GET.get('TypesObject')
    types_group = request.GET.get('typeGroups')
    groups = {"pk": -2, "title": "не найдено"}
    print(types_object, types_group)

    if types_object == 'Антибиотики' and types_group == 'Наборы':
        groups = AntibioticSets.get_antibiotic_set()

    print(groups)

    return JsonResponse({"groups": groups})
