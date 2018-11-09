import simplejson as json
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

import directory.models as directory
from appconf.manager import SettingManager
from laboratory.decorators import group_required
from podrazdeleniya.models import Podrazdeleniya


@login_required
def menu(request):
    """ Меню конструктора """
    groups = [str(x) for x in request.user.groups.all()]
    pages = [
        {"url": "/construct/tubes", "title": "Ёмкости для биоматериала",
         "access": ["Конструктор: Ёмкости для биоматериала"], "module": None},
        {"url": "/construct/researches", "title": "Лабораторные исследования",
         "access": ["Конструктор: Лабораторные исследования"], "module": None},
        {"url": "/construct/researches-paraclinic", "title": "Параклинические (описательные) исследования",
         "access": ["Конструктор: Параклинические (описательные) исследования"], "module": "paraclinic_module"},
        {"url": "/construct/consults", "title": "Консультации",
         "access": ["Конструктор: Консультации"], "module": "consults_module"},
        {"url": "/construct/directions_group", "title": "Группировка исследований по направлениям",
         "access": ["Конструктор: Группировка исследований по направлениям"], "module": None},
        {"url": "/construct/uets", "title": "Настройка УЕТов",
         "access": ["Конструктор: Настройка УЕТов"], "module": None},
    ]

    from context_processors.utils import make_menu
    menu = make_menu(pages, groups, request.user.is_superuser)

    menu_st = [menu[i:i + 4] for i in range(0, len(menu), 4)]

    return render(request, 'construct_menu.html', {
        "menu": menu_st,
    })


@login_required
@group_required("Оператор", "Конструктор: Лабораторные исследования")
def researches(request):
    """ Конструктор исследований """
    labs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY)
    return render(request, 'construct_researches.html',
                  {"labs": labs, "variants": directory.ResultVariants.objects.all()})


@login_required
@group_required("Оператор", "Конструктор: Лабораторные исследования")
def researches_tune(request):
    """ Настройка исследований """
    pk = request.GET["pk"]
    return render(request, 'construct_researches_tune.html',
                  {"pk": pk, "material_types": directory.MaterialVariants.objects.all()})


@login_required
@group_required("Оператор", "Конструктор: Ёмкости для биоматериала")
def tubes(request):
    """ Создание и редактирование ёмкостей """
    return render(request, 'construct_tubes.html')


@login_required
@group_required("Оператор", "Конструктор: Группировка исследований по направлениям")
def directions_group(request):
    """ Группировка по направлениям """
    labs = Podrazdeleniya.objects.filter(Q(p_type=Podrazdeleniya.LABORATORY) | Q(p_type=Podrazdeleniya.PARACLINIC))
    return render(request, 'construct_directions_group.html', {"labs": labs})


@login_required
@group_required("Оператор", "Конструктор: Настройка УЕТов")
def uets(request):
    """ Настройка УЕТов """
    labs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY)
    return render(request, 'uets.html', {"labs": labs})


@csrf_exempt
@login_required
@group_required("Оператор", "Группировка исследований по направлениям")
def onlywith(request):
    """ Настройка назначения анализов вместе """
    if request.method == "GET":
        labs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY)
        return render(request, 'onlywith.html', {"labs": labs})
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
        return JsonResponse({"ok": True})


@csrf_exempt
@login_required
def refs(request):
    """ Настройка назначения анализов вместе """
    if request.method == "GET":
        rows = []
        fraction = directory.Fractions.objects.get(pk=int(request.GET["pk"]))
        for r in directory.References.objects.filter(fraction=fraction).order_by("pk"):
            rows.append({'pk': r.pk, 'title': r.title, 'about': r.about,
                         'ref_m': json.loads(r.ref_m) if isinstance(r.ref_m, str) else r.ref_m,
                         'ref_f': json.loads(r.ref_f) if isinstance(r.ref_f, str) else r.ref_f, 'del': False,
                         'hide': False, 'isdefault': r.pk == fraction.default_ref.pk})
        return JsonResponse(rows, safe=False)
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
                    nrf = directory.References(title=r["title"], about=r["about"], ref_m=r["ref_m"], ref_f=r["ref_f"],
                                               fraction=fraction)
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
        return JsonResponse({"ok": True})


@login_required
@group_required("Оператор", "Конструктор: Параклинические (описательные) исследования")
def researches_paraclinic(request):
    if SettingManager.get("paraclinic_module", default='false', default_type='b'):
        return render(request, 'construct_paraclinic.html')
    else:
        return redirect('/')


@login_required
@group_required("Оператор", "Конструктор: консультации")
def construct_consults(request):
    if SettingManager.get("consults_module", default='false', default_type='b'):
        return render(request, 'construct_consults.html')
    else:
        return redirect('/')
