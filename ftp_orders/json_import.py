import datetime
import ftplib
import logging
import time
from sys import stdout
from tempfile import NamedTemporaryFile

import simplejson as json
from django.db import transaction
from django.utils import timezone

from clients.models import Card, DocumentType, Individual
from directory.models import Contrasts, Researches
from directions.models import IstochnikiFinansirovaniya, Napravleniya
from ftp_orders.json_export import FILE_TYPE_ORDER, FILE_TYPE_STUDY, connect_ftp
from ftp_orders.main import FailedCreatingDirectionsException
from hospitals.models import Hospitals
from integration_framework.models import EquipmentReceive
from laboratory.settings import FTP_JSON_ORDERS_INTERVAL_SECONDS, FTP_JSON_ORDERS_PULL_URL
from slog.models import Log
from users.models import DoctorProfile

logger = logging.getLogger(__name__)


def _result(ok, message="", directions=None, skipped=False):
    return {"ok": ok, "message": message, "directions": directions or [], "skipped": skipped}


def detect_file_type(payload, filename=""):
    file_type = payload.get("_l2_file_type")
    if file_type in (FILE_TYPE_ORDER, FILE_TYPE_STUDY):
        return file_type
    name = (filename or "").lower()
    if name.endswith("_ord.json"):
        return FILE_TYPE_ORDER
    if name.endswith("_dcm.json"):
        return FILE_TYPE_STUDY
    return None


def _normalize_sex(value):
    sex = (value or "").strip().lower()
    if sex in ("м", "m"):
        return "м"
    if sex in ("ж", "f", "w"):
        return "ж"
    return sex


def _parse_birthday(value):
    if not value:
        return None
    if hasattr(value, "isoformat") and not isinstance(value, str):
        return value
    text = str(value).split(" ")[0]
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _doc_by_type(documents, *needles):
    for doc in documents or []:
        title = (doc.get("type") or "").lower()
        if any(needle.lower() in title for needle in needles):
            return (doc.get("serial") or "").strip(), (doc.get("number") or "").strip()
    return "", ""


def _clean_number(number):
    return (number or "").replace(" ", "").replace("-", "")


def _find_hospital(payload):
    oid = (payload.get("hospital_oid") or "").strip()
    if oid:
        hospital = Hospitals.objects.filter(oid=oid, hide=False).first()
        if hospital:
            return hospital, ""
        return None, f"Организация с oid {oid} не найдена"
    hospital_id = payload.get("hospital_id")
    if hospital_id:
        hospital = Hospitals.objects.filter(pk=hospital_id, hide=False).first()
        if hospital:
            return hospital, ""
        return None, f"Организация с id {hospital_id} не найдена"
    return None, "Не указан hospital_oid"


def _find_research(payload):
    internal_code = (payload.get("internal_code") or "").strip()
    if internal_code:
        researches = list(Researches.objects.filter(internal_code=internal_code, hide=False))
        if len(researches) == 1:
            return researches[0], ""
        if len(researches) > 1:
            return None, f"Найдено несколько услуг с internal_code {internal_code}"
        return None, f"Услуга с internal_code {internal_code} не найдена"
    return None, "Не указан internal_code"


def _find_doctor(payload, hospital):
    doctor_uuid = str(payload.get("uuid") or "").strip()
    if doctor_uuid:
        doctor = DoctorProfile.objects.filter(uuid=doctor_uuid, hospital=hospital).first()
        if doctor:
            return doctor, ""
        return None, f"Врач с uuid {doctor_uuid} не найден"
    doctor_id = payload.get("doctor_id") or payload.get("doc_id")
    if doctor_id:
        doctor = DoctorProfile.objects.filter(pk=doctor_id, hospital=hospital).first()
        if doctor:
            return doctor, ""
    doctor = DoctorProfile.objects.filter(hospital=hospital).order_by("pk").first()
    if doctor:
        return doctor, ""
    return None, "Врач не найден"


def _find_or_create_card(payload, hospital):
    documents = payload.get("documents") or []
    _, snils = _doc_by_type(documents, "снилс")
    _, polis = _doc_by_type(documents, "полис омс", "енп")
    snils_clean = _clean_number(snils)
    polis_clean = _clean_number(polis)

    individual = None
    if snils_clean:
        individual = Individual.objects.filter(document__number=snils, document__document_type__title__startswith="СНИЛС").first()
        if not individual:
            individual = Individual.objects.filter(document__number=snils_clean, document__document_type__title__startswith="СНИЛС").first()
    if not individual and polis_clean:
        individual = Individual.objects.filter(document__number=polis, document__document_type__title__in=["Полис ОМС", "ЕНП"]).first()
        if not individual:
            individual = Individual.objects.filter(document__number=polis_clean, document__document_type__title__in=["Полис ОМС", "ЕНП"]).first()

    family = (payload.get("family") or "").strip()
    name = (payload.get("name") or "").strip()
    patronymic = (payload.get("patronymic") or "").strip()
    sex = _normalize_sex(payload.get("sex"))
    birthday = _parse_birthday(payload.get("birthday"))

    if not individual and family and name and birthday:
        qs = Individual.objects.filter(family__iexact=family, name__iexact=name, birthday=birthday, sex=sex)
        if patronymic:
            qs = qs.filter(patronymic__iexact=patronymic)
        individual = qs.filter(owner=hospital).first() or qs.first()

    card = None
    if individual:
        card = Card.objects.filter(individual=individual, owner=hospital, is_archive=False).first()
        if not card:
            card = Card.add_l2_card(individual=individual, force=True, owner=hospital)

    if not card:
        if not (family and name and birthday and sex):
            return None, "Недостаточно данных пациента (ФИО, дата рождения, пол или документы)"
        card = Individual.import_from_simple_data(
            {
                "family": family,
                "name": name,
                "patronymic": patronymic,
                "sex": sex,
                "birthday": birthday.isoformat(),
                "snils": snils,
                "enp": polis,
            },
            hospital,
            str(payload.get("client_id") or payload.get("id") or ""),
            None,
            None,
        )

    if not card:
        return None, "Карта не найдена или не создана"

    _sync_documents(card.individual, documents)
    return card, ""


def _sync_documents(individual, documents):
    if not individual:
        return
    for doc in documents or []:
        title = (doc.get("type") or "").strip()
        number = (doc.get("number") or "").strip()
        if not title or not number:
            continue
        doc_type = DocumentType.objects.filter(title=title).first() or DocumentType.objects.filter(title__istartswith=title).first()
        if not doc_type:
            continue
        individual.add_or_update_doc(doc_type, doc.get("serial") or "", number)


def _source_order_id(payload):
    source_id = payload.get("id")
    if source_id is None:
        return ""
    return str(source_id)[:20]


def create_request_from_ord_payload(payload):
    hospital, error = _find_hospital(payload)
    if error:
        return _result(False, error)

    source_id = _source_order_id(payload)
    if source_id:
        existing = Napravleniya.objects.filter(id_in_hospital=source_id, hospital=hospital, is_request=True).first()
        if existing:
            return _result(True, "Заявка уже существует", directions=[existing.pk], skipped=True)

    research, error = _find_research(payload)
    if error:
        return _result(False, error)

    doctor, error = _find_doctor(payload, hospital)
    if error:
        return _result(False, error)

    card, error = _find_or_create_card(payload, hospital)
    if error:
        return _result(False, error)

    fin_source = IstochnikiFinansirovaniya.objects.filter(title="ОМС", hide=False, base=card.base).first()
    if not fin_source:
        fin_source = IstochnikiFinansirovaniya.objects.filter(title="ОМС", base__internal_type=True, hide=False).first()
    if not fin_source:
        fin_source = IstochnikiFinansirovaniya.objects.filter(base=card.base, hide=False).order_by("-order_weight").first()
    if not fin_source:
        return _result(False, "Не найден источник финансирования")

    with transaction.atomic():
        result = Napravleniya.gen_napravleniya_by_issledovaniya(
            card.pk,
            payload.get("diagnos") or "",
            fin_source.pk,
            "",
            None,
            doctor,
            {-1: [research.pk]},
            {},
            False,
            {},
            hospital_override=hospital.pk,
            id_in_hospital=source_id or None,
            is_cito=bool(payload.get("is_cito")),
        )
        if not result.get("r"):
            raise FailedCreatingDirectionsException(result.get("message") or "Failed creating directions")

        direction_id = result["list_id"][0]
        direction = Napravleniya.objects.get(pk=direction_id)
        direction.is_request = True
        direction.is_cito = bool(payload.get("is_cito"))
        direction.is_dynamic = bool(payload.get("is_dynamic"))
        direction.contrast_amount = payload.get("contrast_amount") or ""
        direction.dose = payload.get("dose") or ""
        direction.anamnesis = payload.get("anamnesis") or ""
        direction.direction_comment = payload.get("direction_comment") or ""
        direction.text_contrast = payload.get("text_contrast") or ""
        direction.fact_research_date = payload.get("fact_research_date") or None
        direction.fact_research_time = payload.get("fact_research_time") or None
        type_contrast_id = payload.get("type_contrast_id")
        if type_contrast_id:
            contrast_type = Contrasts.objects.filter(pk=int(type_contrast_id)).first()
            if contrast_type:
                direction.type_contrast = contrast_type
                if not direction.text_contrast:
                    direction.text_contrast = contrast_type.title
        if source_id:
            direction.id_in_hospital = source_id
        direction.save()

        Log.log(
            source_id or direction.pk,
            190012,
            doctor,
            {"org": hospital.safe_short_title, "content": payload, "directions": result["list_id"], "card": card.number_with_type()},
        )

    return _result(True, "", directions=result["list_id"])


def link_study_from_dcm_payload(payload):
    hospital, error = _find_hospital(payload)
    if error:
        return _result(False, error)

    source_id = _source_order_id(payload)
    if not source_id:
        return _result(False, "Не указан id направления")

    direction = Napravleniya.objects.filter(id_in_hospital=source_id, hospital=hospital, is_request=True).first()
    if not direction:
        return _result(False, f"Заявка {source_id} не найдена")

    study_instance_uid = payload.get("study_instance_uid") or payload.get("study_instance_uid_tag")
    if not study_instance_uid:
        return _result(False, "Не указан study_instance_uid")

    equipment_receive = EquipmentReceive.objects.filter(study_instance_uid_tag=study_instance_uid).first()
    if not equipment_receive:
        return _result(False, "Снимок не найден")

    if equipment_receive.napravleniye_id == direction.pk:
        return _result(True, "Снимок уже привязан", directions=[direction.pk], skipped=True)

    with transaction.atomic():
        for iss in direction.issledovaniya_set.all():
            iss.study_instance_uid = study_instance_uid
            iss.study_instance_uid_tag = study_instance_uid
            iss.save(update_fields=["study_instance_uid", "study_instance_uid_tag"])

        equipment_receive.napravleniye = direction
        equipment_receive.doc_save_link = direction.doc
        equipment_receive.time_save_link = timezone.now()
        equipment_receive.doc_reset_link = None
        equipment_receive.time_reset_link = None
        equipment_receive.save(update_fields=["napravleniye", "doc_save_link", "time_save_link", "doc_reset_link", "time_reset_link"])

        Log.log(source_id, 190013, direction.doc, {"org": hospital.safe_short_title, "study_instance_uid": study_instance_uid, "direction": direction.pk})

    return _result(True, "", directions=[direction.pk])


def import_json_payload(payload, filename=""):
    file_type = detect_file_type(payload, filename)
    if file_type == FILE_TYPE_ORDER:
        return create_request_from_ord_payload(payload)
    if file_type == FILE_TYPE_STUDY:
        return link_study_from_dcm_payload(payload)
    return _result(False, "Неизвестный тип JSON-файла")


def _read_ftp_json(ftp, filename):
    with NamedTemporaryFile() as tmp:
        ftp.retrbinary(f"RETR {filename}", tmp.write)
        tmp.seek(0)
        content = tmp.read()
    try:
        return json.loads(content.decode("utf-8-sig"))
    except UnicodeDecodeError:
        return json.loads(content.decode("cp1251"))


def process_pull_json_orders():
    if not FTP_JSON_ORDERS_PULL_URL:
        return

    ftp = None
    try:
        ftp = connect_ftp(FTP_JSON_ORDERS_PULL_URL)
        try:
            file_list = ftp.nlst()
        except ftplib.error_perm as resp:
            if str(resp).startswith("550"):
                file_list = []
            else:
                raise
        files = sorted(name for name in file_list if name.endswith(".json"))
        for filename in files:
            try:
                payload = _read_ftp_json(ftp, filename)
                result = import_json_payload(payload, filename)
                if result.get("ok"):
                    ftp.delete(filename)
                    stdout.write(f"ftp_json_orders_pull: {filename} {result.get('message') or 'ok'} {result.get('directions')}\n")
                else:
                    logger.error("ftp_json_orders_pull: %s %s", filename, result.get("message"))
                    stdout.write(f"ftp_json_orders_pull: fail {filename} {result.get('message')}\n")
            except Exception:
                logger.exception("ftp_json_orders_pull: failed %s", filename)
    except ftplib.all_errors:
        logger.exception("ftp_json_orders_pull: ftp error")
    finally:
        if ftp:
            try:
                ftp.quit()
            except ftplib.all_errors:
                pass


def process_pull_json_orders_start():
    stdout.write("Starting pull_json_orders process\n")
    while True:
        process_pull_json_orders()
        time.sleep(FTP_JSON_ORDERS_INTERVAL_SECONDS)
