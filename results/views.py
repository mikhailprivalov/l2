from django.shortcuts import render
from django.http import HttpResponse
import simplejson as json
from directions.models import TubesRegistration, Issledovaniya, Result
from django.contrib.auth.decorators import login_required
from laboratory.decorators import group_required
from django.views.decorators.csrf import csrf_exempt
import directory.models as directory


@login_required
@group_required("Врач-лаборант", "Лаборант")
def enter(request):
    return render(request, 'dashboard/resultsenter.html')


@login_required
def loadready(request):
    result = {"tubes": [], "directions": []}
    tubes = TubesRegistration.objects.filter(doc_recive__isnull=False, doc_get__isnull=False)
    for tube in tubes:
        if Issledovaniya.objects.filter(
                tubes__id=tube.id).first().research.subgroup.podrazdeleniye != request.user.doctorprofile.podrazileniye:
            continue
        iss_set = Issledovaniya.objects.filter(tubes__id=tube.id).all()  # .filter(issledovaniye__hide=0)
        if len(iss_set) == 0: continue
        complete = False
        '''for issledovaniye in iss_set:
            if issledovaniye.resultat != None and issledovaniye.resultat != "":
                complete = True'''
        direction = iss_set.first().napravleniye
        dicttube = {"id": tube.pk, "direction": direction.pk}
        if not complete and dicttube not in result["tubes"]:
            result["tubes"].append(dicttube)
        dictdir = {"id": direction.pk}
        if dictdir not in result["directions"]:
            result["directions"].append(dictdir)
    result["tubes"] = sorted(result["tubes"], key=lambda k: k['id'])
    result["directions"] = sorted(result["directions"], key=lambda k: k['id'])
    return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
@login_required
def results_save(request):
    result = {}
    if request.method == "POST":
        fractions = json.loads(request.POST["fractions"])
        issledovaniye = Issledovaniya.objects.get(pk=int(request.POST["issledovaniye"]))
        for key in fractions.keys():
            fraction_result = None
            if Result.objects.filter(issledovaniye=issledovaniye, fraction__pk=key).exists():
                fraction_result = Result.objects.get(issledovaniye=issledovaniye, fraction__pk=key)
            else:
                fraction_result = Result(issledovaniye=issledovaniye, fraction=directory.Fractions.objects.get(pk=key))
            fraction_result.value = fractions[key]
            fraction_result.iteration = 1
            fraction_result.save()

    return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
@login_required
def result_get(request):
    result = {}
    if request.method == "GET":
        issledovaniye = Issledovaniya.objects.get(pk=int(request.GET["iss_id"]))
        results = Result.objects.filter(issledovaniye=issledovaniye)
        # for v in results:


    return HttpResponse(json.dumps(result), content_type="application/json")
