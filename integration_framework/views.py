from rest_framework.decorators import api_view
from rest_framework.response import Response

import directions.models as directions


@api_view()
def next_result_direction(request):
    from_pk = request.GET.get("fromPk")
    after_date = request.GET.get("afterDate")
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
    for xx in dirs[:10]:
        x.append(xx.pk)

    return Response({"next": next_pk, "next10": x, "fromPk": from_pk, "afterDate": after_date})
