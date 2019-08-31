from django.db.models import Min
from rest_framework.decorators import api_view
from rest_framework.response import Response
import datetime

from laboratory.utils import strdatetime

import directions.models as directions
from . import sql_if


@api_view()
def next_result_direction(request):
    from_pk = request.GET.get("fromPk")
    after_date = request.GET.get("afterDate", datetime.datetime.today())
    next_n = int(request.GET.get("nextN", 2))
    type_researches = request.GET.get("research", '*')
    type_researches = 'mbu'
    after_date = '2019-01-01 10:48:07.558120'
    d_start = f'{after_date}+08'
    after_date = datetime.datetime.strptime('01.01.2019', '%d.%m.%Y')
    dirs = None
    dirs = sql_if.direction_collect(d_start, type_researches, next_n)
    print(dirs)

    next_pk = None
    next_time = None
    napr = []
    if dirs:
        for i in dirs:
            napr.append(i[0])
            next_time = i[3]

    print(napr)
    print(next_time)

    return Response({"next": next_pk, "next_n": x, "n": next_n, "fromPk": from_pk, "afterDate": after_date})


@api_view()
def direction_data(request):
    pk = request.GET.get("pk")
    research_pks = request.GET.get("research", '*')
    direction = directions.Napravleniya.objects.get(pk=pk)
    card = direction.client
    individual = card.individual

    iss = directions.Issledovaniya.objects.filter(napravleniye=direction, time_confirmation__isnull=False)
    if research_pks != '*':
        iss = iss.filter(research__pk__in=research_pks.split(','))

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
        },
        "issledovaniya": [x.pk for x in iss]
    })


@api_view()
def issledovaniye_data(request):
    pk = request.GET.get("pk")
    i = directions.Issledovaniya.objects.get(pk=pk)

    sample = directions.TubesRegistration.objects.filter(issledovaniya=i, time_get__isnull=False).first()
    results = directions.Result.objects.filter(issledovaniye=i, fraction__fsli__isnull=False)

    if not sample or not results.exists():
        return Response({
            "ok": False,
        })

    results_data = []

    for r in results:
        results_data.append({
            "pk": r.pk,
            "fsli": r.fraction.fsli,
            "value": r.value.replace(',', '.'),
            "units": r.get_units(),
            "ref": list(map(lambda rf: rf if '.' in rf else rf + '.0', map(lambda f: f.replace(',', '.'),
                                                                           r.calc_normal(only_ref=True).get("r",
                                                                                                            r.value).split(
                                                                               "-"))))
        })

    return Response({
        "ok": True,
        "pk": pk,
        "sample": {
            "date": sample.time_get.date()
        },
        "date": i.time_confirmation.date(),
        "results": results_data,
        "code": i.research.code,
    })
