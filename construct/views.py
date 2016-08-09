from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from laboratory.decorators import group_required
from podrazdeleniya.models import Subgroups
import directory.models as directory
import simplejson as json

@login_required
@group_required("Оператор")
def menu(request):
    """ Меню конструктора """
    return render(request, 'construct_menu.html')


@login_required
@group_required("Оператор")
def researches(request):
    """ Конструктор исследований """
    lab_subgroups = Subgroups.objects.filter(podrazdeleniye__isLab=True)
    return render(request, 'construct_researches.html', {"lab_subgroups": lab_subgroups})


@login_required
@group_required("Оператор")
def researches_tune(request):
    """ Настройка исследований """
    pk = request.GET["pk"]
    return render(request, 'construct_researches_tune.html', {"pk": pk})


@login_required
@group_required("Оператор")
def tubes(request):
    """ Создание и редактирование пробирок """
    return render(request, 'construct_tubes.html')


@login_required
@group_required("Оператор")
def directions_group(request):
    """ Группировка по направлениям """
    lab_subgroups = Subgroups.objects.filter(podrazdeleniye__isLab=True)
    return render(request, 'construct_directions_group.html', {"lab_subgroups": lab_subgroups})


@login_required
@group_required("Оператор")
def uets(request):
    """ Настройка УЕТов """
    lab_subgroups = Subgroups.objects.filter(podrazdeleniye__isLab=True)
    return render(request, 'uets.html', {"lab_subgroups": lab_subgroups})


@csrf_exempt
@login_required
@group_required("Оператор")
def onlywith(request):
    """ Настройка назначения анализов вместе """
    if request.method == "GET":
        lab_subgroups = Subgroups.objects.filter(podrazdeleniye__isLab=True)
        return render(request, 'onlywith.html', {"lab_subgroups": lab_subgroups})
    elif request.method == "POST":
        pk = int(request.POST["pk"])
        onlywith_value = int(request.POST.get("onlywith", "-1"))
        res = directory.Researches.objects.get(pk=pk)
        if onlywith_value > -1:
            res.onlywith = directory.Researches.objects.get(pk=onlywith_value)
            res.save()
        else:
            res.onlywith = None
            res.save()
        return HttpResponse(json.dumps({"ok": True}), content_type="application/json")
