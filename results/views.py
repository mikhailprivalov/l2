from django.shortcuts import render
from django.http import HttpResponse
import simplejson as json
from directions.models import TubesRegistration, Issledovaniya


def enter(request):
    return render(request, 'dashboard/resultsenter.html')


def loadready(request):
    result = {"tubes": [], "directions": []}
    tubes = TubesRegistration.objects.filter(doc_recive__isnull=False, doc_get__isnull=False)
    for tube in tubes:
        if tube.issledovaniya_set.first().issledovaniye.subgroup_lab.podrazdeleniye != request.user.doctorprofile.podrazileniye:
            continue
        iss_set = tube.issledovaniya_set.all()  # .filter(issledovaniye__hide=0)
        if len(iss_set) == 0: continue
        complete = False
        for issledovaniye in iss_set:
            if issledovaniye.resultat != None and issledovaniye.resultat != "":
                complete = True
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
