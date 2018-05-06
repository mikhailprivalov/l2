import datetime
import re

import requests
import simplejson as json
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from zeep.exceptions import Fault

from appconf.manager import SettingManager
from clients.models import Phones
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


def get_db(request):
    # key = request.GET["key"]
    code = request.GET["code"]
    data = []
    for x in Clients.Card.objects.filter(base__short_title=code, is_archive=False).prefetch_related():
        docs = x.individual.document_set.filter(document_type__in=Clients.DocumentType.objects.filter(title__startswith="Полис ОМС"))
        snilses = x.individual.document_set.filter(document_type__in=Clients.DocumentType.objects.filter(title__startswith="СНИЛС"))
        doc = x.polis if x.polis is not None else (None if not docs.exists() else docs.first())
        snils = "" if not snilses.exists() else snilses[0].number
        data.append({
            "Family": x.individual.family,
            "Name": x.individual.name,
            "Twoname": x.individual.patronymic,
            "Sex": x.individual.sex,
            "Bday": "{:%d.%m.%Y}".format(x.individual.birthday),
            "Number": x.number,
            "Polisser": "" if not doc else doc.serial,
            "Polisnum": "" if not doc else doc.number,
            "Snils": snils,
            "Tels": [y.number for y in Phones.objects.filter(card=x)]
        })
    return JsonResponse(data, safe=False)


@csrf_exempt
def receive_db(request):
    # key = request.POST["key"]
    data = request.POST["data"]
    code = request.POST["code"]
    base = Clients.CardBase.objects.filter(short_title=code).first()
    d = json.loads(data)

    bulk_cards = []

    def fix(s: str):
        return s.strip().title()

    from rmis_integration.client import Client
    from slog.models import Log
    # Log(key="receive_db", type=0, body=data, user=None).save()
    c = None
    try:
        if SettingManager.get("rmis_enabled", default='false', default_type='b'):
            c = Client()
    except (requests.exceptions.ConnectionError, Fault):
        pass
    for x in d:
        polis = Clients.Document.objects.filter(
            document_type__in=Clients.DocumentType.objects.filter(title__startswith="Полис ОМС"),
            serial=x.get("Polisser", ""),
            number=x.get("Polisnum", "")).exclude(number="")
        snils = Clients.Document.objects.filter(
            document_type=Clients.DocumentType.objects.filter(title="СНИЛС").first(),
            number=x.get("Snils", "")).exclude(number="")

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
            individual = Clients.Individual.objects.filter(family=x["Family"],
                                                           name=x["Name"],
                                                           patronymic=x["Twoname"],
                                                           birthday=datetime.datetime.strptime(x["Bday"], "%d.%m.%Y").date()).order_by("-pk")
            if not individual.exists():
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

        if x.get("Polisnum", "") != "":
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
        if c is not None:
            try:
                individual.sync_with_rmis(c=c)
            except (requests.exceptions.ConnectionError, Fault):
                pass
        cards = Clients.Card.objects.filter(number=x["Number"], base=base, is_archive=False).exclude(individual=individual)
        todelete = []
        for acard in cards:
            directions = [x.pk for x in acard.napravleniya_set.all()]
            Log(key=str(acard.pk), type=2004, body=json.dumps({"individual": str(acard.individual), "directions": directions, "number": acard.number_with_type()}), user=None).save()
            acard.is_archive = True
            acard.save()
            if len(directions) == 0:
                todelete.append(acard.pk)
                Log(key=str(acard.pk), type=2005, body="", user=None).save()
        Clients.Card.objects.filter(pk__in=todelete).delete()
        if not Clients.Card.objects.filter(number=x["Number"], base=base, is_archive=False).exists():
            polis = list(polis)
            card = Clients.Card(number=x["Number"], base=base, individual=individual, is_archive=False, polis=None if len(polis) == 0 else polis[0])
            card.save()
            for t in x.get("Tels", []):
                card.add_phone(t)
            card.clear_phones(x.get("Tels", []))
        else:
            for card in Clients.Card.objects.filter(number=x["Number"], base=base, is_archive=False):
                for t in x.get("Tels", []):
                    card.add_phone(t)
                card.clear_phones(x.get("Tels", []))
    if len(bulk_cards) != 0:
        Clients.Card.objects.bulk_create(bulk_cards)
    return HttpResponse("OK", content_type="text/plain")
