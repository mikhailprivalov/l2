import datetime
import re

import requests
import simplejson as json
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from zeep.exceptions import Fault

from appconf.manager import SettingManager
from clients.models import Phones, District
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
    code = request.GET["code"]
    data = []
    docs_types = Clients.DocumentType.objects.filter(title__startswith="Полис ОМС")
    snils_types = Clients.DocumentType.objects.filter(title__startswith="СНИЛС")
    for x in Clients.Card.objects.filter(base__short_title=code, is_archive=False). \
            values("number",
                   "pk",
                   "individual_id",
                   "district_id",
                   "individual__family", "individual__name", "individual__patronymic", "individual__sex",
                   "individual__birthday",
                   "polis",
                   "main_diagnosis",
                   "main_address"):
        doc = Clients.Document.objects.get(pk=x["polis"]) if x["polis"] else Clients.Document.objects.filter(
            document_type__in=docs_types, individual__pk=x["individual_id"]).first()
        snils = Clients.Document.objects.filter(document_type__in=snils_types,
                                                individual__pk=x["individual_id"]).first()
        data.append({
            "Family": x["individual__family"],
            "Name": x["individual__name"],
            "Twoname": x["individual__patronymic"],
            "Sex": x["individual__sex"],
            "Bday": "{:%d.%m.%Y}".format(x["individual__birthday"]),
            "Number": x["number"],
            "Polisser": "" if not doc else doc.serial,
            "Polisnum": "" if not doc else doc.number,
            "Snils": snils.number if snils else None,
            "Tels": [y["number"] for y in Phones.objects.filter(card__pk=x["pk"]).values("number")],
            "MainDiagnosis": x["main_diagnosis"],
            "MainAddress": x["main_address"],
            "District": None if not x["district_id"] else District.objects.get(pk=x["district_id"]).title,
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
            c = Client(modules="patients")
    except (requests.exceptions.ConnectionError, Fault):
        pass
    docs_types = Clients.DocumentType.objects.filter(title__startswith="Полис ОМС")
    snils_types = Clients.DocumentType.objects.filter(title__startswith="СНИЛС")
    districts = {}
    for d in District.objects.all():
        districts[d.title] = d

    for x in d:
        polis = Clients.Document.objects.filter(
            document_type__in=docs_types,
            serial=x.get("Polisser", ""),
            number=x.get("Polisnum", "")).exclude(number="")
        snils = Clients.Document.objects.filter(
            document_type=snils_types.first(),
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
            individual = Clients.Individual.objects.filter(family=fix(x["Family"]),
                                                           name=fix(x["Name"]),
                                                           patronymic=fix(x["Twoname"]),
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
            card = Clients.Card(number=x["Number"], base=base, individual=individual, is_archive=False, polis=None if len(polis) == 0 else polis[0], main_diagnosis=x.get("MainDiagnosis", ""))
            card.save()
            for t in x.get("Tels", []):
                card.add_phone(t)
            card.clear_phones(x.get("Tels", []))
            card.main_address = x.get("MainAddress", "")
        else:
            for card in Clients.Card.objects.filter(number=x["Number"], base=base, is_archive=False):
                for t in x.get("Tels", []):
                    card.add_phone(t)
                card.clear_phones(x.get("Tels", []))
                if card.main_diagnosis != x.get("MainDiagnosis", "") or card.main_address != x.get("MainAddress", ""):
                    card.main_diagnosis = x.get("MainDiagnosis", "")
                    card.main_address = x.get("MainAddress", "")
                    card.save()
                if 'District' in x and x['District'] in districts and card.district != districts[x['District']]:
                    card.district = districts[x['District']]
                    card.save()
    if len(bulk_cards) != 0:
        Clients.Card.objects.bulk_create(bulk_cards)
    return HttpResponse("OK", content_type="text/plain")


def search_phone(request):
    r = ""
    q = Clients.Phones.nn(request.GET.get("q", ""))
    p = Clients.Phones.objects.filter(normalized_number=q, card__is_archive=False).exclude(normalized_number="").first()
    if p:
        r = "Пациент: {}".format(p.card.individual.fio())
    return HttpResponse(r, content_type="text/plain; charset=utf-8")
