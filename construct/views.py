from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from laboratory.decorators import group_required
from podrazdeleniya.models import Subgroups


@login_required
@group_required("Оператор")
def menu(request):
    return render(request, 'construct_menu.html')


@login_required
@group_required("Оператор")
def researches(request):
    lab_subgroups = Subgroups.objects.all()
    return render(request, 'construct_researches.html', {"lab_subgroups": lab_subgroups})
