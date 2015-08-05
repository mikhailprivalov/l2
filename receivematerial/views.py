from django.shortcuts import render
from podrazdeleniya.models import Podrazdeleniya, Subgroups
from directions.models import Napravleniya, Issledovaniya, IstochnikiFinansirovaniya, TubesRegistration
from django.http import HttpResponse
from users.models import DoctorProfile
import simplejson as json
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from laboratory.decorators import group_required
import slog.models as slog


@csrf_exempt
@login_required
@group_required("Получатель биоматериала")
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
            message = ""
            if tube_get["status"]:
                tube.doc_recive = request.user.doctorprofile
                tube.time_recive = timezone.now()
                type = 11
            else:
                tube.notice = tube_get["notice"]
                type = 12
            tube.save()
            slog.Log(key=str(tube_get["id"]), user=request.user.doctorprofile, type=type,
                     body=json.dumps({"status": tube_get["status"], "notice": tube_get["notice"]})).save()
        result = {"r": True}
        return HttpResponse(json.dumps(result), content_type="application/json")


@login_required
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
                issledovaniya = Issledovaniya.objects.filter(tubes__id=tube.id)
                issledovaniya_tmp = []
                for iss in issledovaniya:
                    if iss.research.subgroup == subgroup_lab:
                        issledovaniya_tmp.append(iss.research.title)
                if len(issledovaniya_tmp) > 0 and not tube.rstatus() and tube.notice == "":
                    result.append({"researches": ', '.join(issledovaniya_tmp),
                                   "direction": tube.issledovaniya_set.first().napravleniye.pk,
                                   "tube": {"type": tube.type.tube.title, "id": tube.getbc(), "status": tube.rstatus(),
                                            "color": tube.type.tube.color, "notice": tube.notice}})

    return HttpResponse(json.dumps(result), content_type="application/json")
