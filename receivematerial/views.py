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
        podrazdeleniya = Podrazdeleniya.objects.filter(isLab=False, hide=False).order_by(
            "title")  # Список всех подразделений
        return render(request, 'dashboard/receive.html', {"groups": groups, "podrazdeleniya": podrazdeleniya})
    else:
        tubes = json.loads(request.POST["data"])
        for tube_get in tubes:
            tube = TubesRegistration.objects.get(id=tube_get["id"])
            if tube_get["status"]:
                tube.set_r(request.user.doctorprofile)
            elif tube_get["notice"] != "":
                tube.set_notice(tube_get["notice"])

        result = {"r": True}
        return HttpResponse(json.dumps(result), content_type="application/json")


@login_required
def tubes_get(request):
    """ Получение списка не принятых пробирок """
    result = []
    if request.method == "GET":
        subgroup_lab = Subgroups.objects.get(pk=request.GET["subgroup"])
        podrazledeniye = Podrazdeleniya.objects.get(pk=request.GET["from"])
        for doc in DoctorProfile.objects.filter(podrazileniye=podrazledeniye):
            for tube in TubesRegistration.objects.filter(doc_get=doc, notice="", doc_recive__isnull=True):
                issledovaniya_tmp = []
                for iss in Issledovaniya.objects.filter(tubes__id=tube.id, research__subgroup=subgroup_lab):
                    issledovaniya_tmp.append(iss.research.title)
                if len(issledovaniya_tmp) > 0 and not tube.rstatus():
                    result.append({"researches": ' | '.join(issledovaniya_tmp),
                                   "direction": tube.issledovaniya_set.first().napravleniye.pk,
                                   "tube": {"type": tube.type.tube.title, "id": tube.getbc(), "status": tube.rstatus(),
                                            "color": tube.type.tube.color, "notice": tube.notice}})

    return HttpResponse(json.dumps(result), content_type="application/json")
