from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from laboratory.decorators import group_required
from podrazdeleniya.models import Subgroups


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
    lab_subgroups = Subgroups.objects.all()
    return render(request, 'construct_directions_group.html', {"lab_subgroups": lab_subgroups})
