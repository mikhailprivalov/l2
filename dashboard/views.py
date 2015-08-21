from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User, Group
from users.models import DoctorProfile
from podrazdeleniya.models import Podrazdeleniya
from directions.models import IstochnikiFinansirovaniya
from django.views.decorators.csrf import csrf_exempt
from researches.models import Tubes
from django.views.decorators.cache import cache_page
from laboratory.decorators import group_required
import slog.models as slog
import simplejson as json
from django.http import HttpResponse
import simplejson as json


# @cache_page(60 * 15)
@login_required
def dashboard(request):  # Представление панели управления
    from laboratory import settings

    menu = []
    groups = [str(x) for x in request.user.groups.all()]

    if "Лечащий врач" in groups:
        menu.append({"url": "/dashboard/directions", "title": "Направления", "keys": "Shift+n", "nt": False})
    if "Заборщик биоматериала" in groups:
        menu.append({"url": "/researches/control", "title": "Взятие материала", "keys": "Shift+g", "nt": False})
    if "Получатель биоматериала" in groups:
        menu.append({"url": "/dashboard/receive", "title": "Прием материала", "keys": "Shift+r", "nt": False})
    if "Врач-лаборант" in groups or "Лаборант" in groups:
        menu.append({"url": "/results/enter", "title": "Ввод результатов", "keys": "Shift+v", "nt": False})
        menu.append({"url": "/results/conformation", "title": "Подтверждение и печать результатов", "keys": "Shift+d",
                     "nt": False})
    if "Оператор" in groups:
        menu.append({"url": "/construct/menu", "title": "Конструктор справочника", "keys": "Shift+c", "nt": False})
    if "Просмотр статистики" in groups:
        menu.append({"url": "/statistic", "title": "Статистика", "keys": "Shift+s", "nt": False})

    if request.user.is_superuser:
        menu.append({"url": "/admin", "title": "Админ-панель", "keys": "Alt+a", "nt": False})
        menu.append({"url": "/dashboard/create_user", "title": "Создать пользователя", "keys": "Alt+n", "nt": False})
        menu.append({"url": "/dashboard/create_podr", "title": "Добавить подразделение", "keys": "Alt+p", "nt": False})
        if settings.LDAP and settings.LDAP["enable"]:
            menu.append({"url": "/dashboard/ldap_sync", "title": "Синхронизация с LDAP", "keys": "Alt+s", "nt": False})

    menu.append({"url": "http://home", "title": "Домашняя страница", "keys": "Shift+h", "nt": True})

    menu_st = [menu[i:i + 4] for i in range(0, len(menu), 4)]
    return render(request, 'dashboard.html', {"menu": menu_st})


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
                profile.isLDAP_user = False
                profile.save()  # Сохранение профиля
                registered = True
                slog.Log(key=str(profile.pk), user=request.user.doctorprofile, type=16, body=json.dumps(
                    {"username": username, "password": password, "podr": podrpost, "fio": fio})).save()
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
    """ Создание подразделения """
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
                slog.Log(key=str(pd.pk), user=request.user.doctorprofile, type=17,
                         body=json.dumps({"title": title})).save()
            else:
                mess = "Такое подразделение уже есть"
        else:
            mess = "Название заполнено некорректно"
    else:
        e = False
    return render(request, 'dashboard/create_podr.html',
                  {'error': e, 'mess': mess, 'title': '', 'status': p, 'podr': podr})


@login_required
@staff_member_required
def ldap_sync(request):
    """ Страница синхронизации с LDAP """
    return render(request, 'dashboard/ldap_sync.html')


# @cache_page(60 * 15)
@login_required
@group_required("Лечащий врач")
def directions(request):
    """ Страница создания направлений """
    podr = Podrazdeleniya.objects.filter(isLab=True)

    return render(request, 'dashboard/directions.html', {'labs': podr,
                                                         'fin_poli':
                                                             IstochnikiFinansirovaniya.objects.filter(istype="poli"),
                                                         'fin_stat':
                                                             IstochnikiFinansirovaniya.objects.filter(istype="stat")})


@login_required
@staff_member_required
def users_count(request):
    """ Получение количества пользователей """
    result = {"all": 0, "ldap": 0}
    result["all"] = User.objects.all().count()
    result["ldap"] = DoctorProfile.objects.filter(isLDAP_user=True).count()

    return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
@login_required
@staff_member_required
def users_dosync(request):
    """ Выполнение синхронизации с LDAP """
    from ldap3 import Server, Connection, SIMPLE, SYNC, ALL_ATTRIBUTES, SUBTREE, ALL
    from laboratory import settings

    result = {}

    s = Server(settings.LDAP["server"]["host"], port=settings.LDAP["server"]["port"], get_info=ALL)
    c = Connection(s, auto_bind=True, user=settings.LDAP["server"]["user"],
                   password=settings.LDAP["server"]["password"], client_strategy=SYNC, authentication=SIMPLE,
                   check_names=True)

    result_t = ""

    groups = {}
    c.search(search_base=settings.LDAP["base"],
             search_filter='(&(objectClass=person))',
             search_scope=SUBTREE,
             attributes=ALL_ATTRIBUTES,
             get_operational_attributes=True)
    resp = json.loads(c.response_to_json())
    i = 0
    for ldap_user in resp["entries"]:
        if "uidNumber" not in ldap_user["attributes"].keys() or "uid" not in ldap_user[
            "attributes"].keys() or "userPassword" not in ldap_user["attributes"].keys() or "displayName" not in \
                ldap_user["attributes"].keys():
            continue

        if Podrazdeleniya.objects.filter(gid_n=int(ldap_user["attributes"]["gidNumber"])).exists():
            pod = Podrazdeleniya.objects.get(gid_n=int(ldap_user["attributes"]["gidNumber"]))
            pod.title = ldap_user["attributes"]["ou"][0]
            pod.save()
        else:
            pod = Podrazdeleniya(title=ldap_user["attributes"]["ou"][0],
                                 gid_n=int(ldap_user["attributes"]["gidNumber"]))
            pod.save()

        i += 1
        active = False
        if ldap_user["attributes"]["accountStatus"] == "active":
            active = True
        dn = ldap_user["attributes"]["displayName"]

        username = ldap_user["attributes"]["uid"][0]
        password = ldap_user["attributes"]["userPassword"][0]

        if not User.objects.filter(username=username).exists():  # Проверка существования пользователя
            user = User.objects.create_user(username)  # Создание пользователя
            user.set_password(password)  # Установка пароля
            user.is_active = active
            user.save()  # Сохранение пользователя

            profile = DoctorProfile.objects.create()  # Создание профиля
            profile.user = user  # Привязка профиля к пользователю
            profile.isLDAP_user = True
            profile.fio = dn  # ФИО
            profile.podrazileniye = pod
            profile.save()  # Сохранение профиля
        else:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_active = active
            user.save()
            profile = DoctorProfile.objects.get(user=user)
            profile.isLDAP_user = True
            profile.fio = dn
            profile.podrazileniye = pod
            profile.save()
    c.unbind()
    return HttpResponse(json.dumps(groups), content_type="application/json")
