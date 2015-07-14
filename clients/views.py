from django.core import serializers
from django.http import HttpResponse
from .models import Importedclients
import re


def ignore_exception(IgnoreException=Exception, DefaultVal=None):
    """ Decorator for ignoring exception from a function
    e.g.   @ignore_exception(DivideByZero)
    e.g.2. ignore_exception(DivideByZero)(Divide)(2/0)
    """

    def dec(function):
        def _dec(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except IgnoreException:
                return DefaultVal

        return _dec

    return dec


def ajax_search(request):
    objects = []
    if request.method == "GET" and request.GET['query'] and request.GET[
        'type']:  # Проверка типа запроса и наличия полей
        type = request.GET['type']
        query = request.GET['query'].strip()
        p = re.compile(r'[а-я]{3}[0-9]{8}',
                       re.IGNORECASE)  # Регулярное выражение для определения запроса вида иии10121999
        p2 = re.compile(
            r'([А-я]{2,}) ([А-я]{2,}) ([А-я]{0,}) ([0-9]{2}.[0-9]{2}.[0-9]{4})')  # Регулярное выражение для определения запроса вида Иванов Иван Иванович 10.12.1999
        p3 = re.compile(r'[0-9]{1,10}')  # Регулярное выражение для определения запроса по номеру карты
        if re.search(p, query):  # Если это краткий запрос
            initials = query[0:3]
            btday = query[3:5] + "." + query[5:7] + "." + query[7:11] + " 0:00:00"
            if type == "all":
                objects = Importedclients.objects.filter(initials=initials, birthday=btday)[0:10]
            else:
                objects = Importedclients.objects.filter(initials=initials, birthday=btday, type=type)[0:10]
        elif re.search(p2, query):  # Если это полный запрос
            split = str(query).split()
            btday = split[3] + " 0:00:00"
            if type == "all":  # Проверка типа базы, all - поиск по Поликлиннике и по Стационару
                objects = Importedclients.objects.filter(family=split[0], name=split[1], twoname=split[2],
                                                         birthday=btday)[0:10]
            else:
                objects = Importedclients.objects.filter(family=split[0], name=split[1], twoname=split[2],
                                                         birthday=btday, type=type)[0:10]
        elif re.search(p3, query):  # Если это запрос номер карты
            try:
                objects = Importedclients.objects.filter(num=int(query), type=type)[0:10]
            except ValueError:
                pass
    return HttpResponse(serializers.serialize('json', objects), content_type="application/json")  # Создание JSON
