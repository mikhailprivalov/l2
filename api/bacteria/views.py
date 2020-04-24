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
    else:
        culture_obj = Culture.objects.filter(group_culture__title=type)
    elements = [{"pk": i.pk, "title": i.title, "group": i.group_culture.pk} for i in culture_obj]

    group_culture_obj = GroupCulture.objects.all()
    groups = [{"pk": g.pk, "title": g.title} for g in group_culture_obj]

    return JsonResponse({"groups": groups, "elements": elements})
