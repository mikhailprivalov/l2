from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from laboratory.decorators import group_required


@login_required
@group_required("Оператор")
def menu(request):
    return render(request, 'construct_menu.html')
