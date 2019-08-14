from rest_framework.decorators import api_view
from rest_framework.response import Response

import directions.models as directions


@api_view()
def next_result_direction(request):
    from_pk = request.GET.get("fromPk")
    after_date = request.GET.get("afterDate")
    next_n = int(request.GET.get("nextN", 10))
    dirs = directions.Napravleniya.objects.filter(issledovaniya__time_confirmation__isnull=False).exclude(
        issledovaniya__time_confirmation__isnull=True).order_by('issledovaniya__time_confirmation', 'pk').distinct()
    if from_pk:
        dirs = dirs.filter(pk__gt=from_pk)
    if after_date:
        dirs = dirs.filter(data_sozdaniya__date__gte=after_date)

    next_pk = None
    if dirs.exists():
        next_pk = dirs[0].pk

    x = []
    for xx in dirs[:next_n]:
        x.append(xx.pk)

    return Response({"next": next_pk, "next_n": x, "n": next_n, "fromPk": from_pk, "afterDate": after_date})


@api_view()
def direction_data(request):
    pk = request.GET.get("pk")
    direction = directions.Napravleniya.objects.get(pk=pk)
    card = direction.client
    individual = card.individual

    return Response({
        "pk": pk,
        "createdAt": direction.data_sozdaniya,
        "patient": {
            **card.get_data_individual(full_empty=True),
            "family": individual.family,
            "name": individual.name,
            "patronymic": individual.patronymic,
            "birthday": individual.birthday,
            "sex": individual.sex,
            "card": {
                "base": {
                    "pk": card.base_id,
                    "title": card.base.title,
                    "short_title": card.base.short_title,
                },
                "pk": card.pk,
                "number": card.number,
            },
        }
    })
