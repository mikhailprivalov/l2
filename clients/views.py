import datetime
import re

import simplejson as json
from django.core import serializers
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from users.models import DoctorProfile
from . import models as Clients


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


from rmis_integration.client import Client


def ajax_search(request):
    """ Поиск пациентов """
    objects = []
    data = []
    if request.method == "GET" and request.GET['query'] and request.GET['type']:  # Проверка типа запроса и наличия полей
        type = request.GET['type']
        card_type = Clients.CardBase.objects.get(pk=type)
        query = request.GET['query'].strip()
        p = re.compile(r'[а-яё]{3}[0-9]{8}', re.IGNORECASE)  # Регулярное выражение для определения запроса вида иии10121999
        p2 = re.compile(r'([А-яЕё]{2,})( ([А-яЕё]{2,})( ([А-я]*)( ([0-9]{2}.[0-9]{2}.[0-9]{4}))?)?)?')  # Регулярное выражение для определения запроса вида Иванов Иван Иванович 10.12.1999
        p3 = re.compile(r'[0-9]{1,15}')  # Регулярное выражение для определения запроса по номеру карты
        pat_bd = re.compile(r"\d{4}-\d{2}-\d{2}")
        if re.search(p, query.lower()):  # Если это краткий запрос
            initials = query[0:3].upper()
            btday = query[7:11] + "-" + query[5:7] + "-" + query[3:5]
            if not pat_bd.match(btday):
                return JsonResponse([], safe=False)
            try:
                objects = Clients.Individual.objects.filter(family__startswith=initials[0], name__startswith=initials[1],
                                                            patronymic__startswith=initials[2], birthday=btday, card__base=card_type)
                if card_type.is_rmis and len(objects) == 0:
                    c = Client()
                    objects = c.patients.import_individual_to_base({"surname": query[0] + "%", "name": query[1] + "%", "patrName": query[2] + "%", "birthDate": btday}, fio=True)
            except ValidationError:
                objects = []
        elif re.search(p2, query):  # Если это полный запрос
            split = str(query).split()
            f = n = p = btday = ""
            f = split[0]
            rmis_req = {"surname": f+"%"}
            if len(split) > 1:
                n = split[1]
                rmis_req["name"] = n+"%"
            if len(split) > 2:
                p = split[2]
                rmis_req["patrName"] = p+"%"
            if len(split) > 3:
                btday = split[3].split(".")
                btday = btday[2] + "-" + btday[1] + "-" + btday[0]
                rmis_req["birthDate"] = btday
            objects = Clients.Individual.objects.filter(family__istartswith=f, name__istartswith=n,
                                                        patronymic__istartswith=p, card__base=card_type)[:10]
            if len(split) > 3:
                objects = Clients.Individual.objects.filter(family__istartswith=f, name__istartswith=n,
                                                            patronymic__istartswith=p, card__base=card_type,
                                                            birthday=datetime.datetime.strptime(split[3], "%d.%m.%Y").date())[:10]

            if card_type.is_rmis and (len(objects) == 0 or (len(split) < 4 and len(objects) < 10)):
                c = Client()
                objects = list(objects)
                objects += c.patients.import_individual_to_base(rmis_req, fio=True, limit=10-len(objects))

        if (re.search(p3, query) or card_type.is_rmis) and len(list(objects)) == 0:  # Если это запрос номер карты
            try:
                objects = Clients.Individual.objects.filter(card__number=query.upper(), card__is_archive=False,
                                                            card__base=card_type)
            except ValueError:
                pass
            if card_type.is_rmis and len(objects) == 0 and len(query) == 16:
                c = Client()
                objects = c.patients.import_individual_to_base(query)

        '''
        c = Client()
        for i in objects:
            c.patients.get_rmis_id_for_individual(i, True)'''

        for row in Clients.Card.objects.filter(base=card_type, individual__in=objects, is_archive=False).prefetch_related("individual").distinct():
            data.append({"type_title": card_type.title,
                         "num": row.number,
                         "family": row.individual.family,
                         "name": row.individual.name,
                         "twoname": row.individual.patronymic,
                         "birthday": row.individual.bd(),
                         "sex": row.individual.sex,
                         "individual_pk": row.individual.pk,
                         "pk": row.pk})
    return JsonResponse(data, safe=False)


def get_db(request):
    key = request.GET["key"]
    code = request.GET["code"]
    data = []
    for x in Clients.Card.objects.filter(base__short_title=code, is_archive=False).prefetch_related():
        docs = x.individual.document_set.filter(
            document_type=Clients.DocumentType.objects.filter(title__startswith="Полис ОМС").first())
        doc = x.polis if x.polis is not None else (None if not docs.exists() else docs.first())
        data.append({
            "Family": x.individual.family,
            "Name": x.individual.name,
            "Twoname": x.individual.patronymic,
            "Sex": x.individual.sex,
            "Bday": "{:%d.%m.%Y}".format(x.individual.birthday),
            "Number": x.number,
            "Polisser": "" if not doc else doc.serial,
            "Polisnum": "" if not doc else doc.number
        })
    return JsonResponse(data, safe=False)


@csrf_exempt
def receive_db(request):
    key = request.POST["key"]
    data = request.POST["data"]
    code = request.POST["code"]
    base = Clients.CardBase.objects.filter(short_title=code).first()
    d = json.loads(data)
    c = "OK"

    api_user = DoctorProfile.objects.filter(user__username="api").first()
    bulk_polises = []
    bulk_cards = []

    def fix(s: str):
        return s.strip().title()
    from rmis_integration.client import Client
    c = Client()
    for x in d:
        individual = Clients.Individual.objects.filter(family=x["Family"],
                                                       name=x["Name"],
                                                       patronymic=x["Twoname"],
                                                       birthday=datetime.datetime.strptime(x["Bday"], "%d.%m.%Y").date()).order_by("-pk")
        polis = [None]
        if not individual.exists():
            polis = Clients.Document.objects.filter(
                document_type__in=Clients.DocumentType.objects.filter(title__startswith="Полис ОМС"),
                serial=x["Polisser"],
                number=x["Polisnum"])
            snils = Clients.Document.objects.filter(
                document_type=Clients.DocumentType.objects.filter(title="СНИЛС").first(),
                number=x.get("Snils", ""))
            if snils.exists() or polis.exists():
                individual = (snils if snils.exists() else polis)[0].individual
                if not Clients.Card.objects.filter(individual=individual, base__is_rmis=True).exists():
                    individual.family = fix(x["Family"])
                    individual.name = fix(x["Name"])
                    individual.patronymic = fix(x["Twoname"])
                    individual.birthday = datetime.datetime.strptime(x["Bday"], "%d.%m.%Y").date()
                    individual.sex = x["Sex"].lower().strip()
                    individual.save()
            else:
                individual = Clients.Individual(family=fix(x["Family"]),
                                                name=fix(x["Name"]),
                                                patronymic=fix(x["Twoname"]),
                                                birthday=datetime.datetime.strptime(x["Bday"], "%d.%m.%Y").date(),
                                                sex=x["Sex"])
                individual.save()
        else:
            individual = individual[0]
            if individual.sex != x["Sex"]:
                individual.sex = x["Sex"]
                individual.save()
        if x["Polisnum"] != "":
            polis = Clients.Document.objects.filter(
                document_type__in=Clients.DocumentType.objects.filter(title__startswith="Полис ОМС"), serial=x["Polisser"],
                number=x["Polisnum"], individual=individual).order_by("-pk")
            if not polis.exists():
                polis = [Clients.Document(
                    document_type=Clients.DocumentType.objects.filter(title__startswith="Полис ОМС").first(), serial=x["Polisser"],
                    number=x["Polisnum"], individual=individual).save()]
        if x.get("Snils", "") != "":
            snils = Clients.Document.objects.filter(
                document_type=Clients.DocumentType.objects.filter(title="СНИЛС").first(),
                number=x["Snils"], individual=individual).order_by("-pk")
            if not snils.exists():
                Clients.Document(
                    document_type=Clients.DocumentType.objects.filter(title="СНИЛС").first(),
                    number=x["Snils"], individual=individual).save()
        individual.sync_with_rmis()
        cards = Clients.Card.objects.filter(number=x["Number"], base=base, is_archive=False).exclude(
            individual=individual)
        cards.update(is_archive=True)
        cards.filter(napravleniya__isnull=True).delete()
        if not Clients.Card.objects.filter(number=x["Number"], base=base, is_archive=False).exists():
            polis = list(polis)
            bulk_cards.append(Clients.Card(number=x["Number"], base=base, individual=individual, is_archive=False, polis=None if len(polis) == 0 else polis[0]))
    if len(bulk_cards) != 0:
        Clients.Card.objects.bulk_create(bulk_cards)
    return HttpResponse("OK", content_type="text/plain")
