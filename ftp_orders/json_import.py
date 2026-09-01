import base64
import datetime
import ftplib
import logging
import time
from sys import stdout
from tempfile import NamedTemporaryFile

import simplejson as json
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from clients.models import Card, DocumentType, Individual
from directory.models import Contrasts, Researches
from directions.models import IssledovaniyaFiles, IstochnikiFinansirovaniya, Napravleniya
from equipment.models import Equipment
from ftp_orders.json_export import FILE_TYPE_ORDER, FILE_TYPE_RESULT, FILE_TYPE_STUDY, connect_ftp
from ftp_orders.main import FailedCreatingDirectionsException
from hospitals.models import Hospitals
from integration_framework.models import EquipmentReceive
from laboratory.settings import FTP_JSON_ORDERS_INTERVAL_SECONDS, FTP_JSON_ORDERS_PULL_URL, FTP_JSON_RESULTS_PULL_URL
from slog.models import Log
from users.models import DoctorProfile

logger = logging.getLogger(__name__)


def _result(ok, message="", directions=None, skipped=False):
    return {"ok": ok, "message": message, "directions": directions or [], "skipped": skipped}


def detect_file_type(payload, filename=""):
    file_type = payload.get("_l2_file_type")
    if file_type in (FILE_TYPE_ORDER, FILE_TYPE_STUDY, FILE_TYPE_RESULT):
        return file_type
    name = (filename or "").lower()
    if name.endswith("_ord.json"):
        return FILE_TYPE_ORDER
    if name.endswith("_dcm.json"):
        return FILE_TYPE_STUDY
    if name.endswith("_res.json"):
        return FILE_TYPE_RESULT
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


def _payload_text(payload, key):
    value = payload.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _create_equipment_receive_from_payload(payload, equipment, study_instance_uid):
    return EquipmentReceive(
        family=_payload_text(payload, "family"),
        name=_payload_text(payload, "name"),
        patronymic=_payload_text(payload, "patronymic"),
        birthday=_parse_birthday(payload.get("birthday")),
        sex=_normalize_sex(payload.get("sex")) or "м",
        order_id=_payload_text(payload, "order_id"),
        tag_patient_name=_payload_text(payload, "tag_patient_name"),
        tag_study_date=_payload_text(payload, "tag_study_date"),
        tag_station_name=_payload_text(payload, "tag_station_name") or equipment.station_name or None,
        tag_institution_name=_payload_text(payload, "tag_institution_name") or equipment.institution_name or None,
        tag_manufacturer=_payload_text(payload, "tag_manufacturer") or equipment.manufacturer or None,
        tag_manufacturer_model_name=_payload_text(payload, "tag_manufacturer_model_name") or equipment.manufacturer_model_name or None,
        tag_device_serial_number=_payload_text(payload, "tag_device_serial_number") or equipment.device_serial_number or None,
        tag_patient_sex=_payload_text(payload, "tag_patient_sex"),
        tag_patient_birthdate=_payload_text(payload, "tag_patient_birthdate"),
        tag_patient_id=_payload_text(payload, "tag_patient_id"),
        tag_sex=_payload_text(payload, "tag_sex"),
        study_instance_uid_tag=study_instance_uid,
        tag_instance_id=_payload_text(payload, "tag_instance_id"),
        equipment_title=equipment.title or None,
        equipment_model=equipment,
        ip_address=_payload_text(payload, "ip_address") or equipment.ip_address,
        tag_pacs_property=_payload_text(payload, "tag_pacs_property") or equipment.pacs_property or None,
    )


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

    equipment_uuid = str(payload.get("uuid") or "").strip()
    if not equipment_uuid:
        return _result(False, "Не указан uuid оборудования")

    equipment = Equipment.objects.filter(uuid=equipment_uuid).exclude(uuid="").first()
    if not equipment:
        return _result(False, f"Оборудование с uuid {equipment_uuid} не найдено")

    with transaction.atomic():
        EquipmentReceive.objects.filter(study_instance_uid_tag=study_instance_uid, equipment_model=equipment).delete()

        equipment_receive = _create_equipment_receive_from_payload(payload, equipment, study_instance_uid)
        equipment_receive.napravleniye = direction
        equipment_receive.doc_save_link = direction.doc
        equipment_receive.time_save_link = timezone.now()
        equipment_receive.save()

        for iss in direction.issledovaniya_set.all():
            iss.study_instance_uid = study_instance_uid
            iss.study_instance_uid_tag = study_instance_uid
            iss.save(update_fields=["study_instance_uid", "study_instance_uid_tag"])

        Log.log(source_id, 190013, direction.doc, {"org": hospital.safe_short_title, "study_instance_uid": study_instance_uid, "direction": direction.pk, "uuid": equipment_uuid})

    return _result(True, "", directions=[direction.pk])


def _parse_confirmation_time(value):
    if not value:
        return timezone.now()
    if hasattr(value, "isoformat") and not isinstance(value, str):
        dt = value
    else:
        text = str(value).strip().replace("Z", "")
        dt = parse_datetime(text)
        if dt is None:
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M"):
                try:
                    dt = datetime.datetime.strptime(text[:26], fmt)
                    break
                except ValueError:
                    continue
    if dt is None:
        return timezone.now()
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def apply_result_from_res_payload(payload, hospitals=None):
    source_id = _source_order_id(payload)
    if not source_id:
        return _result(False, "Не указан id заявки")

    pdf_b64 = payload.get("pdf") or ""
    if not pdf_b64:
        return _result(False, "Не указан pdf")
    try:
        pdf_bytes = base64.b64decode(pdf_b64)
    except Exception:
        return _result(False, "Некорректный pdf (base64)")
    if not pdf_bytes:
        return _result(False, "Пустой pdf")

    qs = Napravleniya.objects.filter(is_request=True)
    if hospitals is not None:
        qs = qs.filter(hospital__in=hospitals)
    try:
        direction = qs.filter(pk=int(source_id)).first()
    except (TypeError, ValueError):
        direction = None
    if not direction:
        return _result(False, f"Заявка {source_id} не найдена")

    doctor_fio = str(payload.get("doctor_fio") or "").strip()
    time_confirmation = _parse_confirmation_time(payload.get("time_confirmation"))

    with transaction.atomic():
        for iss in direction.issledovaniya_set.all():
            IssledovaniyaFiles.objects.filter(issledovaniye=iss).delete()
            pdf_content_file = ContentFile(pdf_bytes)
            iss_file = IssledovaniyaFiles(issledovaniye=iss, uploaded_file=pdf_content_file)
            iss_file.uploaded_file.name = f"{direction.pk}_result.pdf"
            iss_file.save()
            iss.time_confirmation = time_confirmation
            iss.time_save = timezone.now()
            iss.doc_confirmation_string = doctor_fio
            iss.save(update_fields=["time_confirmation", "time_save", "doc_confirmation_string"])

        direction.sync_confirmed_fields(skip_post=True)
        Log.log(source_id, 190014, direction.doc, {"direction": direction.pk, "doctor_fio": doctor_fio, "time_confirmation": str(time_confirmation)})

    return _result(True, "", directions=[direction.pk])


def import_json_payload(payload, filename=""):
    file_type = detect_file_type(payload, filename)
    if file_type == FILE_TYPE_ORDER:
        return create_request_from_ord_payload(payload)
    if file_type == FILE_TYPE_STUDY:
        return link_study_from_dcm_payload(payload)
    if file_type == FILE_TYPE_RESULT:
        return apply_result_from_res_payload(payload)
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
    _process_pull_json(FTP_JSON_ORDERS_PULL_URL, "ftp_json_orders_pull")


def process_pull_json_results():
    _process_pull_json(FTP_JSON_RESULTS_PULL_URL, "ftp_json_results_pull")


def _process_pull_json(url, log_prefix):
    if not url:
        return

    ftp = None
    try:
        ftp = connect_ftp(url)
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
                    stdout.write(f"{log_prefix}: {filename} {result.get('message') or 'ok'} {result.get('directions')}\n")
                else:
                    logger.error("%s: %s %s", log_prefix, filename, result.get("message"))
                    stdout.write(f"{log_prefix}: fail {filename} {result.get('message')}\n")
            except Exception:
                logger.exception("%s: failed %s", log_prefix, filename)
    except ftplib.all_errors:
        logger.exception("%s: ftp error", log_prefix)
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


def process_pull_json_results_start():
    stdout.write("Starting pull_json_results process\n")
    while True:
        process_pull_json_results()
        time.sleep(FTP_JSON_ORDERS_INTERVAL_SECONDS)
