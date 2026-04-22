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
        return Response({"ok": False, "message": "Должно быть указано oid"})
    hospital = None
    if not hospital:
        hospital = Hospitals.objects.filter(oid=oid_org).first()

    if not hospital:
        return Response({"ok": False, "message": "Организация не найдена"})

    if not request.user.hospitals.filter(pk=hospital.pk).exists():
        return Response({"ok": False, "message": "Нет доступа в переданную организацию"})

    patient = body.get("patient", {})
    enp = (patient.get("enp") or "").replace(" ", "")

    if enp and (len(enp) != 16 or not enp.isdigit()):
        return Response({"ok": False, "message": "Неверные данные полиса, должно быть 16 чисел"})

    snils = (str(patient.get("snils")) or "").replace(" ", "").replace("-", "")
    if len(snils) == 10:
        snils = f"0{snils}"

    if snils and not petrovna.validate_snils(snils):
        return Response({"ok": False, "message": "patient.snils: не прошёл валидацию"})

    lastname = str(patient.get("lastname") or "")
    firstname = str(patient.get("firstname") or "")
    patronymic = str(patient.get("patronymic") or "")
    birthdate = str(patient.get("birthdate") or "")
    sex = patient.get("sex") or ""
    if sex == "m":
        sex = "м"
    else:
        sex = "ж"

    if not enp and not (lastname and firstname and birthdate):
        return Response({"ok": False, "message": "При пустом patient.enp должно быть передано поле patient.individual"})

    if lastname and not firstname:
        return Response({"ok": False, "message": "При передаче lastname должен быть передан и firstname"})

    if firstname and not lastname:
        return Response({"ok": False, "message": "При передаче firstname должен быть передан и lastname"})

    if firstname and lastname and not birthdate:
        return Response({"ok": False, "message": "При передаче firstname и lastname должно быть передано поле birthdate"})

    if birthdate and (not re.fullmatch(r"\d{4}-\d\d-\d\d", birthdate) or birthdate[0] not in ["1", "2"]):
        return Response({"ok": False, "message": "birthdate должно соответствовать формату YYYY-MM-DD"})

    if birthdate and sex not in ["м", "ж"]:
        return Response({"ok": False, "message": 'sex должно быть "м" или "ж"'})

    individual, individuals = None, None
    if enp:
        individuals = Individual.objects.filter(tfoms_enp=enp, owner=hospital, owner_patient_id=patient["internalId"])
        if not individuals.exists():
            individuals = Individual.objects.filter(document__number=enp).filter(Q(document__document_type__title="Полис ОМС") | Q(document__document_type__title="ЕНП"))

    if not individual and snils:
        individuals = Individual.objects.filter(document__number=snils, document__document_type__title="СНИЛС")
    if individuals:
        if individuals.exists():
            individual = individuals.objects.filter(owner=hospital, owner_patient_id=patient["internalId"]).first()

    card = None
    if not individual and lastname:
        card = Individual.import_from_simple_data(
            {
                "family": lastname,
                "name": firstname,
                "patronymic": patronymic,
                "sex": sex,
                "birthday": birthdate,
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
    if not fsidi_code:
        return Response({"ok": False, "message": "Не указа ФСИДИ КОД"})
    researches = Researches.objects.filter(nsi_id=fsidi_code, hide=False)
    if len(researches) > 1:
        return Response({"ok": False, "message": f"У исполнителя в справочнике услуг КОД{fsidi_code} больше одного"})
    elif len(researches) < 1:
        return Response({"ok": False, "message": f"У исполнителя в справочнике услуг КОД- {fsidi_code} отсутствует"})
    else:
        service_pk = Researches.objects.filter(hide=False, nsi_id=fsidi_code).first().pk
    operator_created_id = order_data.get("operatorCreatedId")
    if not operator_created_id:
        return Response({"ok": False, "message": "Не указан id-оператора"})
    doc_profile = DoctorProfile.objects.filter(id=operator_created_id).first()
    if doc_profile.hospital != hospital:
        return Response({"ok": False, "message": "Id-оператора не принадлежит вашей организации"})
    financing_source = IstochnikiFinansirovaniya.objects.filter(title="ОМС", base__internal_type=True).first()
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
        date_study = order_data.get('dateStudy', '')
        date_study = date_study.split(" ")
        date_fact, time_fact = None, None
        if len(date_study) > 1:
            date_fact = date_study[0]
            time_fact = date_study[1]
        direction.fact_research_date = date_fact
        direction.fact_research_time = time_fact
        direction.save()

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
    # hospital = request.user.hospital
    hospitals = request.user.hospitals.all()
    permission_hospitals = [i for i in hospitals]

    # articles = Article.objects.filter(tags__name='django').filter(tags__name='python')
    # Application.objects.filter(key=api_key).exists()

    internal_id = body.get("internalId")
    direction_num = body.get("directionNum")
    study_instance_uid = body.get("studyInstanceUID")
    equipment_model_id = body.get("deviceId")
    operatorCreatedId = body.get("operatorCreatedId")

    direction = Napravleniya.objects.filter(id=int(direction_num), id_in_hospital=internal_id, hospital__in=permission_hospitals, doc_id=operatorCreatedId).first()
    try:
        equipment_receive = EquipmentReceive.objects.get(study_instance_uid_tag=study_instance_uid, equipment_model_id=equipment_model_id)
    except EquipmentReceive.DoesNotExist:
        return Response({"ok": False, "message": "Изображение не найдено в PACS исполнителя"})

    image_id = equipment_receive.pk
    request_id = direction.pk
    doc_profile = DoctorProfile.objects.filter(id=operatorCreatedId).first()

    body_data = json.dumps({"imageId": image_id, "requestId": request_id})
    http_obj = HttpRequest()
    http_obj._body = body_data
    http_obj.user = doc_profile.user
    return link_image_to_request(http_obj)
