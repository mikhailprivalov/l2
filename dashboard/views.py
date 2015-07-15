from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User, Group
from users.models import DoctorProfile
from podrazdeleniya.models import Podrazdeleniya
from directions.models import IstochnikiFinansirovaniya
from researches.models import Tubes
from django.views.decorators.cache import cache_page
from laboratory.decorators import group_required

# @cache_page(60 * 15)
@login_required
def dashboard(request):  # Представление панели управления
    return render(request, 'dashboard.html')


# @cache_page(60 * 15)
@login_required
@group_required("Заборщик биоматериала")
def researches_control(request):
    tubes = Tubes.objects.all()
    return render(request, 'dashboard/recive_material.html', {"tubes": tubes})


@login_required
@staff_member_required
def create_user(request):  # Страница создания пользователя
    registered = False
    podr = Podrazdeleniya.objects.all()  # Получение всех подразделений
    podrpost = 0
    groups = Group.objects.all();  # Получение всех групп
    if request.method == 'POST':
        username = request.POST['username']  # Имя пользователя
        password = request.POST['password']  # Пароль
        podrpost = request.POST['podr']  # Подразделение
        fio = request.POST['fio']  # ФИО
        groups_user = request.POST.getlist('groups')  # Группы

        if username and password and fio:  # Проверка наличия всех полей
            if not User.objects.filter(username=username).exists():  # Проверка существования пользователя
                user = User.objects.create_user(username)  # Создание пользователя
                user.set_password(password)  # Установка пароля
                user.is_active = True  # Активация пользователя
                user.save()  # Сохранение пользователя
                for g in groups_user:  # Перебор выбранных групп
                    gTmp = Group.objects.get(pk=g)  # Выбор группы
                    gTmp.user_set.add(user)  # Установка группы
                profile = DoctorProfile.objects.create()  # Создание профиля
                profile.user = user  # Привязка профиля к пользователю
                profile.fio = fio  # ФИО
                profile.podrazileniye = podr.get(pk=podrpost)  # Привязка подразделения
                profile.save()  # Сохранение профиля
                registered = True
            else:
                return render(request, 'dashboard/create_user.html',
                              {'error': True, 'mess': 'Пользователь с таким именем пользователя уже существует',
                               'uname': username, 'fio': fio, 'status': registered, 'podr': podr, 'podrpost': podrpost,
                               'g': groups})  # Вывод
        else:
            return render(request, 'dashboard/create_user.html',
                          {'error': True, 'mess': 'Данные введены неверно', 'uname': username, 'fio': fio,
                           'status': registered, 'podr': podr, 'podrpost': podrpost, 'g': groups})  # Вывод

    return render(request, 'dashboard/create_user.html',
                  {'error': False, 'mess': '', 'uname': '', 'fio': '', 'status': registered, 'podr': podr,
                   'podrpost': podrpost, 'g': groups})  # Вывод


@login_required
@staff_member_required
def create_pod(request):
    p = False
    e = True
    mess = ''
    podr = Podrazdeleniya.objects.all()  # Выбор подразделения
    if request.method == 'POST':  # Проверка типа запроса
        title = request.POST['title']  # Получение названия
        if title:  # Если название есть
            if not Podrazdeleniya.objects.filter(title=title).exists():  # Если название не существует
                pd = Podrazdeleniya.objects.create()  # Создание подразделения
                pd.title = title
                pd.save()  # Сохранение подразделения
                p = True
                e = False
            else:
                mess = "Такое подразделение уже есть"
        else:
            mess = "Название заполнено некорректно"
    else:
        e = False
    return render(request, 'dashboard/create_podr.html',
                  {'error': e, 'mess': mess, 'title': '', 'status': p, 'podr': podr})


# @cache_page(60 * 15)
@login_required
@group_required("Лечащий врач")
def directions(request):
    podr = Podrazdeleniya.objects.all()

    return render(request, 'dashboard/directions.html', {'labs': podr,
                                                         'fin_poli':
                                                             IstochnikiFinansirovaniya.objects.filter(istype="poli"),
                                                         'fin_stat':
                                                             IstochnikiFinansirovaniya.objects.filter(istype="stat")})
