import petrovna
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import api_view

from clients.models import Individual, Card
from hospitals.models import Hospitals
from integration_framework.models import EquipmentReceive
import simplejson as json
import re


@api_view(['POST'])
def get_meta_tags(request):
    result = EquipmentReceive.save_meta_tag_from_dicom_server(request)

    return Response({"result": result})


@api_view(['POST'])
def dcm_order_create(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    body = json.loads(request.body)
    oid_org = body.get("oid", {})
    if not oid_org:
        return {"ok": False, "message": "Должно быть указано oid"}
    hospital = None
    if not hospital:
        hospital = Hospitals.objects.filter(oid=oid_org).first()

    if not hospital:
        return {"ok": False, "message": "Организация не найдена"}

    if not request.user.hospitals.filter(pk=hospital.pk).exists():
        return {"ok": False, "message": "Нет доступа в переданную организацию"}

    patient = body.get("patient", {})
    enp = (patient.get("enp") or "").replace(" ", "")

    if enp and (len(enp) != 16 or not enp.isdigit()):
        return {"ok": False, "message": "Неверные данные полиса, должно быть 16 чисел"}

    snils = (str(patient.get("snils")) or "").replace(" ", "").replace("-", "")
    if len(snils) == 10:
        snils = f"0{snils}"

    if snils and not petrovna.validate_snils(snils):
        return {"ok": False, "message": "patient.snils: не прошёл валидацию"}

    lastname = str(patient.get("lastName") or "")
    firstname = str(patient.get("firstName") or "")
    patronymic = str(patient.get("patronymicName") or "")
    birthdate = str(patient.get("birthDate") or "")
    sex = patient.get("sex") or ""
    if sex == "m":
        sex = "м"
    else:
        sex = "ж"

    if not enp and not (lastname and firstname and birthdate):
        return {"ok": False, "message": "При пустом patient.enp должно быть передано поле patient.individual"}

    if lastname and not firstname:
        return {"ok": False, "message": "При передаче lastname должен быть передан и firstname"}

    if firstname and not lastname:
        return {"ok": False, "message": "При передаче firstname должен быть передан и lastname"}

    if firstname and lastname and not birthdate:
        return {"ok": False, "message": "При передаче firstname и lastname должно быть передано поле birthdate"}

    if birthdate and (not re.fullmatch(r"\d{4}-\d\d-\d\d", birthdate) or birthdate[0] not in ["1", "2"]):
        return {"ok": False, "message": "birthdate должно соответствовать формату YYYY-MM-DD"}

    if birthdate and sex not in ["м", "ж"]:
        return {"ok": False, "message": 'sex должно быть "м" или "ж"'}

    individual, individuals = None, None
    if enp:
        individuals = Individual.objects.filter(tfoms_enp=enp, owner=hospital, owner_patient_id=patient["internalId"])
        if not individuals.exists():
            individuals = Individual.objects.filter(document__number=enp).filter(Q(document__document_type__title="Полис ОМС") | Q(document__document_type__title="ЕНП"))

    if not individual and snils:
        individuals = Individual.objects.filter(document__number=snils, document__document_type__title="СНИЛС")
    if individuals.exists():
        individual = individuals.objects.filter(owner=hospital, owner_patient_id=patient["internalId"]).first()

    card = None
    if not individual and lastname:
        card = Individual.import_from_simple_data(
            {
                "family": lastname,
                "name": firstname,
                "patronymic": patronymic,
                "sex": patient["sex"],
                "birthday": patient["birthdate"],
                "snils": patient["snils"],
            },
            hospital,
            patient["internalId"],
            patient.get("email"),
            patient.get("phone"),
        )
        card.main_address = patient.get("mainAddress")
        card.fact_address = patient.get("factAddress")
        card.save(update_fields=["main_address", "fact_address"])

    if not card and individual:
        card = Card.objects.filter(individual=individual, owner=hospital).first()

    if not card:
        return Response({"ok": False, "message": "Карта не найдена или не создана"})









    order_data = body.get("orderData", {})




    return Response({"result": True})