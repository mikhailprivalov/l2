from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from directory.models import Culture, GroupCulture


@login_required
def load_culture(request):
    type = request.GET.get('type')
    elements = []
    groups = []
    if type == "all":
        culture_obj = Culture.objects.all()
        for i in culture_obj:
            elements.append({"pk": i.pk, "title": i.title, "group": i.group_culture.pk})
        group_culture_onj = GroupCulture.objects.all()
        for g in group_culture_onj:
            groups.append({"pk": g.pk, "title": g.title})
    else:
        culture_obj = Culture.objects.filter(group_culture__title=type)
        for i in culture_obj:
            elements.append({"pk": i.pk, "title": i.title, "group": i.group_culture.pk})

        group_culture_onj = GroupCulture.objects.filter(title=type)

        for g in group_culture_onj:
            groups.append({"pk": g.pk, "title": g.title})

    return JsonResponse({"groups": groups, "elements": elements})
