from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse


def home(request):
    """Страница автоизации"""
    if request.method == 'POST':  # Проверка типа запроса
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)  # Аутитификация
        if user:  # Проверка на правильность введенных данных
            if user.is_active:  # Проверка активности профиля
                login(request, user)  # Установка статуса авторизации в положительный
            else:
                return HttpResponse("Ваш аккаунт отключен")  # Сообщение об ошибке
        else:
            return render(request, 'auth.html', {'error': True, 'username': username})  # Сообщение об ошибке
    if request.user.is_authenticated():  # Проверка статуса автоизации
        return HttpResponseRedirect('/dashboard')  # Редирект в п/у
    return render(request, 'auth.html', {'error': False, 'username': ''})  # Вывод формы авторизации
