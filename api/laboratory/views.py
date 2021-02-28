from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
import simplejson as json
from django.utils import dateformat

from directions.models import TubesRegistration
from directory.models import Fractions, Researches
from podrazdeleniya.models import Podrazdeleniya
from utils.dates import try_parse_range


@login_required
def fractions(request):
    request_data = json.loads(request.body)
    pk = int(request_data['pk'])
    research = Researches.objects.get(pk=pk)
    fractions_list = []
    for f in Fractions.objects.filter(research=research).order_by("sort_weight"):
        fractions_list.append(
            {
                "pk": f.pk,
                "title": f.title,
                "units": f.units,
                "fsli": f.get_fsli_code(),
            }
        )
    return JsonResponse(
        {
            "fractions": fractions_list,
            "title": research.get_title(),
        }
    )


@login_required
def save_fsli(request):
    request_data = json.loads(request.body)
    fractions = request_data['fractions']
    for fd in fractions:
        f = Fractions.objects.get(pk=fd['pk'])
        nf = fd['fsli'].strip() or None
        if f != f.get_fsli_code():
            f.fsli = nf
            f.save(update_fields=['fsli'])
    return JsonResponse({"ok": True})


def fraction(request):
    request_data = json.loads(request.body)
    pk = request_data['pk'] or -1
    if Fractions.objects.filter(pk=pk).exists():
        f = Fractions.objects.get(pk=pk)
        ft = f.title
        rt = f.research.get_title()
        return JsonResponse({"title": f"{rt} – {ft}" if ft != rt and ft else rt})

    return JsonResponse({"title": None})


def laboratories(request):
    rows = []
    active = -1
    r: Podrazdeleniya
    for r in Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY).exclude(title="Внешние организации").order_by("title"):
        rows.append({
            "pk": r.pk,
            "title": r.get_title(),
        })
        if active == -1 or request.user.doctorprofile.podrazdeleniye_id == r.pk:
            active = r.pk
    return JsonResponse({"rows": rows, "active": active})


def ready(request):
    request_data = json.loads(request.body)
    dates = request_data['date_range']
    laboratory_pk = request_data['laboratory']
    laboratory = Podrazdeleniya.objects.get(pk=laboratory_pk)
    result = {"tubes": [], "directions": []}

    date_start, date_end = try_parse_range(*dates)
    dates_cache = {}
    tubes = set()
    dirs = set()

    tlist = TubesRegistration.objects.filter(
        doc_recive__isnull=False,
        time_recive__range=(date_start, date_end),
        issledovaniya__time_confirmation__isnull=True,
        issledovaniya__research__podrazdeleniye=laboratory,
        issledovaniya__isnull=False,
    )

    tlist = tlist.filter(
        Q(issledovaniya__napravleniye__hospital=request.user.doctorprofile.hospital) |
        Q(issledovaniya__napravleniye__hospital__isnull=True)
    )

    for tube in tlist.prefetch_related('issledovaniya_set__napravleniye'):
        direction = None
        if tube.pk not in tubes:
            if not direction:
                direction = tube.issledovaniya_set.first().napravleniye
            if tube.time_recive.date() not in dates_cache:
                dates_cache[tube.time_recive.date()] = dateformat.format(tube.time_recive, 'd.m.y')
            tubes.add(tube.pk)
            dicttube = {
                "id": tube.pk,
                "direction": direction.pk,
                "date": dates_cache[tube.time_recive.date()],
                "tube": {"title": tube.type.tube.title, "color": tube.type.tube.color},
            }
            result["tubes"].append(dicttube)

        if tube.issledovaniya_set.first().napravleniye_id not in dirs:
            if not direction:
                direction = tube.issledovaniya_set.first().napravleniye
            if direction.data_sozdaniya.date() not in dates_cache:
                dates_cache[direction.data_sozdaniya.date()] = dateformat.format(direction.data_sozdaniya, 'd.m.y')
            dirs.add(direction.pk)
            dictdir = {"id": direction.pk, "date": dates_cache[direction.data_sozdaniya.date()]}
            result["directions"].append(dictdir)

    result["tubes"].sort(key=lambda k: k['id'])
    result["directions"].sort(key=lambda k: k['id'])
    return JsonResponse(result)
