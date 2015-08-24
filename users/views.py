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
        username = request.POST['username']  # Имя пользователя
        password = request.POST['password']  # Пароль
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
    if request.user.is_authenticated():  # Проверка статуса автоизации
        return HttpResponseRedirect('/dashboard')  # Редирект в п/у
    return render(request, 'auth.html', {'error': False, 'username': ''})  # Вывод формы авторизации
