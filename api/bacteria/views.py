from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from directory.models import Culture, GroupCulture, Antibiotic, GroupAntibiotic


@login_required
def load_culture(request):
    type = request.GET.get('type')
    searchObj = request.GET.get('searchObj')
    print(searchObj)
    result = {"groups": [], "elements": []}
    obj_el, obj_group = None, None

    if searchObj == 'Бактерии':
        obj_el = Culture
        obj_group = GroupCulture

    if searchObj == 'Антибиоткики':
        obj_el = Antibiotic
        obj_group = GroupAntibiotic
    if obj_el:
        if type == "Все":
            elements_send = obj_el.objects.all()
        else:
            elements_send = obj_el.objects.filter(group_culture__title=type)
        elements = [{"pk": i.pk, "title": i.title, "group": i.group_culture.pk} for i in elements_send]

        group_send_obj = obj_group.objects.all()
        groups = [{"pk": g.pk, "title": g.title} for g in group_send_obj]
        groups.insert(0, {"pk": -1, "title": "Все"})

        result = {"groups": groups, "elements": elements}

    return JsonResponse(result)


