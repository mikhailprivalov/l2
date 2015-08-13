from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from ldap3 import Server, Connection, SIMPLE, SYNC, ALL_ATTRIBUTES, SUBTREE, ALL
from django.contrib.auth.models import User, Group
from users.models import DoctorProfile
import slog.models as slog
import laboratory.settings as settings
import simplejson as json


def home(request):
    """Страница автоизации"""
    if request.method == 'POST':  # Проверка типа запроса
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)  # Аутинтификация
        if user:  # Проверка на правильность введенных данных
            if user.is_active:  # Проверка активности профиля
                login(request, user)  # Установка статуса авторизации в положительный
                log = slog.Log(key="", type=18, body="IP: {0}".format(slog.Log.get_client_ip(request)),
                               user=request.user.doctorprofile)
                log.save()
            else:
                return HttpResponse("Ваш аккаунт отключен")  # Сообщение об ошибке
        else:
            if settings.LDAP and settings.LDAP["enable"]:
                s = Server(settings.LDAP["server"]["host"], port=settings.LDAP["server"]["port"], get_info=ALL)
                c = Connection(s, auto_bind=True, user=settings.LDAP["server"]["user"],
                               password=settings.LDAP["server"]["password"], client_strategy=SYNC,
                               authentication=SIMPLE, check_names=True)

                result_t = ""

                c.search(search_base=settings.LDAP["base"],
                         search_filter='(&(uid=' + username + ')(userPassword=' + password + '))',
                         search_scope=SUBTREE,
                         attributes=ALL_ATTRIBUTES,
                         get_operational_attributes=True)
                resp = json.loads(c.response_to_json())

                if len(resp["entries"]) == 1:
                    if not User.objects.filter(username=username).exists():  # Проверка существования пользователя
                        user = User.objects.create_user(username)  # Создание пользователя
                        user.set_password(password)  # Установка пароля
                        if resp["entries"][0]["attributes"]["accountStatus"] == "active":
                            user.is_active = True  # Активация пользователя
                        else:
                            user.is_active = False
                        user.save()  # Сохранение пользователя

                        profile = DoctorProfile.objects.create()  # Создание профиля
                        profile.user = user  # Привязка профиля к пользователю
                        profile.isLDAP_user = True
                        profile.fio = resp["entries"][0]["attributes"]["displayName"]  # ФИО
                        profile.save()  # Сохранение профиля

                    c.unbind()
                    return home(request)
                c.unbind()
            return render(request, 'auth.html', {'error': True, 'username': username})  # Сообщение об ошибке
    if request.user.is_authenticated():  # Проверка статуса автоизации
        return HttpResponseRedirect('/dashboard')  # Редирект в п/у
    return render(request, 'auth.html', {'error': False, 'username': ''})  # Вывод формы авторизации
