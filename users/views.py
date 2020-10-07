import re

from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
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
                log = slog.Log(key="", type=18, body="IP: {0}".format(slog.Log.get_client_ip(request)), user=request.user.doctorprofile)
                log.save()
            else:
                return HttpResponse("Ваш аккаунт отключен")  # Сообщение об ошибке
        elif len(password) == 0 and len(f1) == 1 and len(f1[0]) == 2:
            did = int(f1[0][0].replace("X", ""))
            u = DoctorProfile.objects.filter(pk=did).first()
            if u and u.get_login_id() == username and u.user.is_active:
                user = u.user
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                slog.Log(key='По штрих-коду', type=18, body="IP: {0}".format(slog.Log.get_client_ip(request)), user=request.user.doctorprofile).save()
            else:
                return render(request, 'auth.html', {'error': True, 'username': username, 'message': 'Ошибка'})
        else:
            return render(request, 'auth.html', {'error': True, 'username': username})  # Сообщение об ошибке
    if request.user.is_authenticated:  # Проверка статуса автоизации
        return HttpResponseRedirect(next)  # Редирект в п/у
    response = render(request, 'auth.html', {'error': False, 'username': ''},)  # Вывод формы авторизации
    response["Login-Screen"] = 1
    return response
