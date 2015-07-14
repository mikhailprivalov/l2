from django.shortcuts import render
from podrazdeleniya.models import Podrazdeleniya, Subgroups
from directions.models import Napravleniya, Issledovaniya, IstochnikiFinansirovaniya, TubesRegistration
from django.http import HttpResponse
from users.models import DoctorProfile
import simplejson as json
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def receive(request):
    """Представление для приемщика материала в лаборатории"""
    from django.utils import timezone

    if request.method == "GET":
        groups = Subgroups.objects.filter(
            podrazdeleniye=request.user.doctorprofile.podrazileniye)  # Список доступных групп для текущего пользователя
        podrazdeleniya = Podrazdeleniya.objects.all()  # Список всех подразделений
        return render(request, 'dashboard/receive.html', {"groups": groups, "podrazdeleniya": podrazdeleniya})
    else:
        tubes = json.loads(request.POST["data"])
        for tube_get in tubes:
            tube = TubesRegistration.objects.get(id=tube_get["id"])

            if tube_get["status"]:
                tube.doc_recive = request.user.doctorprofile
                tube.time_recive = timezone.now()
            else:
                tube.notice = tube_get["notice"]
            tube.save()
        result = {"r": True}
        return HttpResponse(json.dumps(result), content_type="application/json")


def tubes_get(request):
    result = []
    if request.method == "GET":
        subgroup_lab = Subgroups.objects.get(pk=request.GET["subgroup"])
        podrazledeniye = Podrazdeleniya.objects.get(pk=request.GET["from"])
        docs = DoctorProfile.objects.filter(podrazileniye=podrazledeniye)
        for doc in docs:
            tubes = TubesRegistration.objects.exclude(time_get__lt=datetime.now().date()).filter(doc_get=doc)
            for tube in tubes:
                if tube.doc_get is None: continue
                issledovaniya = Issledovaniya.objects.filter(tube=tube)
                issledovaniya_tmp = []
                for iss in issledovaniya:
                    if iss.issledovaniye.subgroup_lab == subgroup_lab:
                        issledovaniya_tmp.append(iss.issledovaniye.ref_title)
                if len(issledovaniya_tmp) > 0 and not tube.rstatus() and tube.notice == "":
                    result.append({"researches": ', '.join(issledovaniya_tmp),
                                   "direction": tube.issledovaniya_set.first().napravleniye.pk,
                                   "tube": {"type": tube.type.title, "id": tube.getbc(), "status": tube.rstatus(),
                                            "color": tube.type.color, "notice": tube.notice}})

    return HttpResponse(json.dumps(result), content_type="application/json")
