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


@csrf_exempt
@login_required
def refs(request):
    """ Настройка назначения анализов вместе """
    if request.method == "GET":
        rows = []
        fraction = directory.Fractions.objects.get(pk=int(request.GET["pk"]))
        for r in directory.References.objects.filter(fraction=fraction).order_by("pk"):
            rows.append({'pk': r.pk, 'title': r.title, 'about': r.about, 'ref_m': json.loads(r.ref_m) if isinstance(r.ref_m, str) else r.ref_m, 'ref_f': json.loads(r.ref_f) if isinstance(r.ref_f, str) else r.ref_f, 'del': False, 'hide': False, 'isdefault': r.pk == fraction.default_ref.pk})
        return HttpResponse(json.dumps(rows), content_type="application/json")
    elif request.method == "POST":
        pk = int(request.POST["pk"])
        default = int(request.POST["default"])
        if pk > -1:
            fraction = directory.Fractions.objects.get(pk=pk)
            for r in json.loads(request.POST["refs"]):
                r["ref_m"].pop("", None)
                r["ref_f"].pop("", None)
                if r["del"] and r["pk"] != -1:
                    directory.References.objects.filter(pk=r["pk"]).delete()
                    if r["pk"] == default:
                        default = -1
                elif not r["del"] and r["pk"] == -1:
                    nrf = directory.References(title=r["title"], about=r["about"], ref_m=r["ref_m"], ref_f=r["ref_f"], fraction=fraction)
                    nrf.save()
                    if r["isdefault"]:
                        default = nrf.pk
                else:
                    row = directory.References.objects.get(pk=r["pk"])
                    row.title = r["title"]
                    row.about = r["about"]
                    row.ref_m = json.dumps(r["ref_m"])
                    row.ref_f = json.dumps(r["ref_f"])
                    row.save()
            fraction.default_ref = None if default == -1 else directory.References.objects.get(pk=default)
            fraction.save()
        return HttpResponse(json.dumps({"ok": True}), content_type="application/json")
