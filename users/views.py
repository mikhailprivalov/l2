import re

import simplejson as json
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from ldap3 import Server, Connection, SIMPLE, SYNC, ALL_ATTRIBUTES, SUBTREE, ALL

import laboratory.settings as settings
import slog.models as slog
from users.models import DoctorProfile


def home(request):
    """Страница автоизации"""
    next = '/mainmenu/'
    if request.method == 'POST':  # Проверка типа запроса
        username = request.POST['username']  # Имя пользователя
        password = request.POST['password']  # Пароль
        if 'next' in request.POST.keys():
            next = request.POST['next']
        user = authenticate(username=username, password=password)  # Аутинтификация
        f1 = re.findall(r"^([ X0-9]{5})([0-9a-fA-F]{5})$", username)
        if user:  # Проверка на правильность введенных данных
            if user.is_active:  # Проверка активности профиля
                login(request, user)  # Установка статуса авторизации в положительный
                log = slog.Log(key="", type=18, body="IP: {0}".format(slog.Log.get_client_ip(request)),
                               user=request.user.doctorprofile)
                log.save()
            else:
                return HttpResponse("Ваш аккаунт отключен")  # Сообщение об ошибке
        elif len(password) == 0 and len(f1) == 1 and len(f1[0]) == 2:
            did = int(f1[0][0].replace("X", ""))
            u = DoctorProfile.objects.filter(pk=did).first()
            if u and u.get_login_id() == username and u.user.is_active:
                user = u.user
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                slog.Log(key='По штрих-коду', type=18, body="IP: {0}".format(slog.Log.get_client_ip(request)),
                         user=request.user.doctorprofile).save()
            else:
                return render(request, 'auth.html', {'error': True, 'username': username, 'message': 'Ошибка'})
        else:
            if settings.LDAP and settings.LDAP["enable"] and False:  # Проверка на наличие и активность настройки LDAP
                s = Server(settings.LDAP["server"]["host"], port=settings.LDAP["server"]["port"],
                           get_info=ALL)  # Создание объекта сервера
                c = Connection(s, auto_bind=True, user=settings.LDAP["server"]["user"],
                               password=settings.LDAP["server"]["password"], client_strategy=SYNC,
                               authentication=SIMPLE, check_names=True)  # Создание соединения с сервером

                c.search(search_base=settings.LDAP["base"],
                         search_filter='(&(uid=' + username + ')(userPassword=' + password + '))',
                         search_scope=SUBTREE,
                         attributes=ALL_ATTRIBUTES,
                         get_operational_attributes=True)  # Выполнение поиска пользователя в LDAP
                resp = json.loads(c.response_to_json())  # Нормализация ответа

                if len(resp["entries"]) == 1:  # Если пользователь был найден
                    if not User.objects.filter(username=username).exists():  # Проверка существования пользователя
                        user = User.objects.create_user(username)  # Создание пользователя
                        user.set_password(password)  # Установка пароля
                        if resp["entries"][0]["attributes"]["accountStatus"] == "active":  # Проверка статуса активности
                            user.is_active = True  # Активация пользователя
                        else:
                            user.is_active = False  # Деактивация
                        user.save()  # Сохранение пользователя

                        profile = DoctorProfile.objects.create()  # Создание профиля
                        profile.user = user  # Привязка профиля к пользователю
                        profile.isLDAP_user = True  # Установка флага, показывающего, что это импортированый из LDAP пользователь
                        profile.fio = resp["entries"][0]["attributes"]["displayName"]  # ФИО
                        profile.save()  # Сохранение профиля

                    c.unbind()  # Отключение от сервера
                    return home(request)  # Запуск запроса еще раз
                c.unbind()  # Отключение от сервера
            return render(request, 'auth.html', {'error': True, 'username': username})  # Сообщение об ошибке
    if request.user.is_authenticated:  # Проверка статуса автоизации
        return HttpResponseRedirect(next)  # Редирект в п/у
    response = render(request, 'auth.html', {'error': False, 'username': ''}, )  # Вывод формы авторизации
    response["Login-Screen"] = 1
    return response
