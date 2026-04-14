import petrovna
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import api_view

from api.requests.views import link_image_to_request
from clients.models import Individual, Card
from directions.models import Napravleniya, IstochnikiFinansirovaniya
from directory.models import Researches
from ftp_orders.main import FailedCreatingDirectionsException
from hospitals.models import Hospitals
from integration_framework.models import EquipmentReceive
import simplejson as json
import re
from django.http import HttpRequest

from integration_framework.views import limit_str
from django.db import transaction

from slog.models import Log
from users.models import DoctorProfile


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
    order_internal_id = order_data.get("internalId", "")

    if order_internal_id is None:
        return Response({"ok": False, "message": "Некорректный номер заказа orderData.internalId"})
    else:
        id_in_hospital = limit_str(order_internal_id, 15)
        if Napravleniya.objects.filter(id_in_hospital=id_in_hospital, hospital=hospital).first():
            return Response({"ok": False, "message": f"Уже существует номер заказа {id_in_hospital} в orderData.internalId для текуще организации"})

    fsidi_code = order_data.get("fsidiCode", "")
    researches = Researches.objects.filter(nsi_id=fsidi_code, hide=False)
    if len(researches) > 1:
        return Response({"ok": False, "message": f"У исполнителя в справочнике услуг КОД{fsidi_code} больше одного"})
    elif len(researches) > 1:
        return Response({"ok": False, "message": f"У исполнителя в справочнике услуг КОД- {fsidi_code} отсутствует "})
    else:
        service_pk = Researches.objects.filter(hide=False, nsi_id=fsidi_code).first().pk
    operator_created_id = order_data.get("operatorCreatedId")
    if not operator_created_id:
        return Response({"ok": False, "message": "Не указан id-оператора"})
    doc_profile = DoctorProfile.objects.filter(id=operator_created_id).first()
    if doc_profile.hospital != hospital:
        return Response({"ok": False, "message": "Id-оператора не верный"})
    financing_source = IstochnikiFinansirovaniya.objects.filter(title__iexact="омс", base__internal_type=True).first()
    services = [service_pk]
    with transaction.atomic():
        result = Napravleniya.gen_napravleniya_by_issledovaniya(
            card.pk,
            "",
            financing_source.pk,
            "",
            None,
            doc_profile,
            {-1: services},
            {},
            False,
            {},
            hospital_override=hospital.pk,
            id_in_hospital=id_in_hospital,
        )
        if not result["r"]:
            raise FailedCreatingDirectionsException(result.get("message") or "Failed creating directions")
        direction_id = result["list_id"][0]
        direction = Napravleniya.objects.filter(id=direction_id).first()
        direction.is_cito = order_data.get('cito', False)
        direction.is_request = True
        direction.contrast_amount = order_data.get('contrastAmount', '')
        direction.dose = order_data.get('dose', '')
        direction.anamnesis = order_data.get('anamnesis', '')
        direction.direction_comment = order_data.get('comment', '')
        direction.fact_research_date = order_data.get('dateStudy', '') or None
        direction.fact_research_time = order_data.get('time', '') or None

        Log.log(
            id_in_hospital,
            190004,
            doc_profile,
            {
                "org": hospital.safe_short_title,
                "content": body,
                "service": services,
                "directions": result["list_id"],
                "card": card.number_with_type(),
                "internalId": id_in_hospital
            },
        )

    return Response({"ok": True, "message": "", "directions": result["list_id"]})


@api_view(['POST'])
def dcm_study_link(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    body = json.loads(request.body)
    hospital = request.user.hospital

    internal_id = body.get("internalId")
    direction_num = body.get("directionNum")
    study_instance_uid = body.get("studyInstanceUID")

    direction = Napravleniya.objects.filter(id=int(direction_num), id_in_hospital=internal_id, hospital=hospital)

    try:
        equipment_receive = EquipmentReceive.objects.get(study_instance_uid_tag=study_instance_uid)
    except EquipmentReceive.DoesNotExist:
        return Response({"ok": False, "message": "Изображение не найдено в PACS исполнителя"})

    imageId = equipment_receive.pk
    request_id = direction.pk
    doc_profile = direction.doc

    body_data = json.dumps({"imageId": imageId, "request_id": request_id})
    http_obj = HttpRequest()
    http_obj._body = body_data
    http_obj.user = doc_profile.user
    return link_image_to_request(http_obj)
