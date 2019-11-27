from django.db.models import Min
from rest_framework.decorators import api_view
from rest_framework.response import Response

import directions.models as directions
from slog.models import Log
from . import sql_if
from laboratory.settings import AFTER_DATE
from laboratory import utils
import random


@api_view()
def next_result_direction(request):
    from_pk = request.GET.get("fromPk")
    after_date = request.GET.get("afterDate")
    if after_date == '0':
        after_date = AFTER_DATE
    next_n = int(request.GET.get("nextN", 1))
    type_researches = request.GET.get("research", '*')
    d_start = f'{after_date}'
    dirs = sql_if.direction_collect(d_start, type_researches, next_n)

    next_time = None
    naprs = []
    if dirs:
        for i in dirs:
            naprs.append(i[0])
            next_time = i[3]

    return Response({"next": naprs, "next_time": next_time, "n": next_n, "fromPk": from_pk, "afterDate": after_date})


@api_view()
def get_dir_amd(request):
    next_n = int(request.GET.get("nextN", 1))
    dirs = sql_if.direction_resend_amd(next_n)
    if dirs:
        naprs = [ i[0] for i in dirs]

    return Response({"next": naprs})


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

    if not iss:
        return Response({
        "ok": False,
    })

    iss_index = random.randrange(len(iss))

    return Response({
        "ok": True,
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
        "issledovaniya": [x.pk for x in iss],
        "timeConfirmation": iss[iss_index].time_confirmation,
        "docLogin": iss[iss_index].doc_confirmation.rmis_login,
        "docPassword": iss[iss_index].doc_confirmation.rmis_password
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


@api_view()
def make_log(request):
    key = request.GET.get("key")
    t = int(request.GET.get("type"))
    if t in (60000, 60001):
        Log.log(key=key, type=t)
    return Response({
        "ok": True,
    })
