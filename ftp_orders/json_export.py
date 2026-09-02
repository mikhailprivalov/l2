import base64
import datetime
import decimal
import ftplib
import logging
import os
import shutil
import time
import uuid
from io import BytesIO
from sys import stdout
from urllib.parse import urlparse

import simplejson as json

from laboratory.settings import (
    BASE_DIR,
    FTP_JSON_ORDERS_ARCHIVE_DIR,
    FTP_JSON_ORDERS_INTERVAL_SECONDS,
    FTP_JSON_ORDERS_SPOOL_DIR,
    FTP_JSON_ORDERS_URL,
    FTP_JSON_RESULTS_ARCHIVE_DIR,
    FTP_JSON_RESULTS_SPOOL_DIR,
    FTP_JSON_RESULTS_URL,
)

logger = logging.getLogger(__name__)

FILE_TYPE_ORDER = "ord"
FILE_TYPE_STUDY = "dcm"
FILE_TYPE_RESULT = "res"


def get_spool_dir():
    return FTP_JSON_ORDERS_SPOOL_DIR or os.path.join(BASE_DIR, "ftp_json_spool")


def get_archive_dir():
    return FTP_JSON_ORDERS_ARCHIVE_DIR or os.path.join(BASE_DIR, "ftp_json_archive")


def get_results_spool_dir():
    return FTP_JSON_RESULTS_SPOOL_DIR or os.path.join(BASE_DIR, "ftp_json_results_spool")


def get_results_archive_dir():
    return FTP_JSON_RESULTS_ARCHIVE_DIR or os.path.join(BASE_DIR, "ftp_json_results_archive")


def _archive_sent_file(path, filename, archive_dir=None):
    archive_dir = archive_dir or get_archive_dir()
    os.makedirs(archive_dir, exist_ok=True)
    dest = os.path.join(archive_dir, filename)
    if os.path.exists(dest):
        name, ext = os.path.splitext(filename)
        dest = os.path.join(archive_dir, f"{name}_{int(time.time() * 1000)}{ext}")
    shutil.move(path, dest)
    return dest


def _serialize_value(value):
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (str, int, float, bool, list, dict)) or value is None:
        return value
    return str(value)


def build_direction_payload(direction, file_type, extra=None):
    payload = {field.attname: _serialize_value(getattr(direction, field.attname, None)) for field in direction._meta.concrete_fields}
    if extra:
        payload.update(extra)
    payload["_l2_file_type"] = file_type
    return payload


def _patient_documents(individual):
    if not individual:
        return []
    from clients.models import Document

    docs = Document.objects.filter(individual=individual, is_active=True).select_related("document_type").order_by("pk")
    return [
        {
            "type": (d.document_type.title if d.document_type else "") or "",
            "serial": d.serial or "",
            "number": d.number or "",
        }
        for d in docs
    ]


def _direction_internal_code(direction):
    iss = direction.issledovaniya_set.select_related("research").order_by("pk").first()
    if not iss or not iss.research:
        return ""
    return iss.research.internal_code or ""


def _order_extra_fields(direction):
    individual = getattr(getattr(direction, "client", None), "individual", None)
    hospital = getattr(direction, "hospital", None)
    return {
        "family": (individual.family if individual else "") or "",
        "name": (individual.name if individual else "") or "",
        "patronymic": (individual.patronymic if individual else "") or "",
        "birthday": _serialize_value(individual.birthday if individual else None),
        "sex": (individual.sex if individual else "") or "",
        "doctor_id": direction.doc_id,
        "uuid": (direction.doc.uuid if direction.doc else "") or "",
        "hospital_oid": (hospital.oid if hospital else "") or "",
        "internal_code": _direction_internal_code(direction),
        "documents": _patient_documents(individual),
    }


def _safe_filename_part(value):
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in str(value))


def build_filename(direction_pk, file_type, study_instance_uid=None, event_time=None):
    event_time = event_time or datetime.datetime.now()
    timestamp = f"{event_time:%Y%m%d}_{event_time:%H%M%S}{event_time.microsecond // 1000:03d}"
    if file_type == FILE_TYPE_STUDY:
        return f"{direction_pk}_{timestamp}_{_safe_filename_part(study_instance_uid or 'nouid')}_{FILE_TYPE_STUDY}.json"
    if file_type == FILE_TYPE_RESULT:
        return f"{direction_pk}_{timestamp}_{FILE_TYPE_RESULT}.json"
    return f"{direction_pk}_{timestamp}_{FILE_TYPE_ORDER}.json"


def spool_json(filename, payload, spool_dir=None):
    spool_dir = spool_dir or get_spool_dir()
    os.makedirs(spool_dir, exist_ok=True)
    path = os.path.join(spool_dir, filename)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)
    return path


def build_order_json(direction):
    return build_direction_payload(direction, FILE_TYPE_ORDER, extra=_order_extra_fields(direction))


def spool_order_json(direction):
    filename = build_filename(direction.pk, FILE_TYPE_ORDER)
    return spool_json(filename, build_order_json(direction))


def _study_extra_fields(direction, equipment_receive):
    equipment = getattr(equipment_receive, "equipment_model", None)
    hospital = getattr(direction, "hospital", None)
    return {
        "uuid": (equipment.uuid if equipment else "") or "",
        "hospital_oid": (hospital.oid if hospital else "") or "",
        "study_instance_uid": equipment_receive.study_instance_uid_tag,
        "family": equipment_receive.family or "",
        "name": equipment_receive.name or "",
        "patronymic": equipment_receive.patronymic or "",
        "birthday": _serialize_value(equipment_receive.birthday),
        "sex": equipment_receive.sex or "",
        "order_id": equipment_receive.order_id or "",
        "tag_patient_name": equipment_receive.tag_patient_name or "",
        "tag_study_date": equipment_receive.tag_study_date or "",
        "tag_station_name": equipment_receive.tag_station_name or "",
        "tag_institution_name": equipment_receive.tag_institution_name or "",
        "tag_manufacturer": equipment_receive.tag_manufacturer or "",
        "tag_manufacturer_model_name": equipment_receive.tag_manufacturer_model_name or "",
        "tag_device_serial_number": equipment_receive.tag_device_serial_number or "",
        "tag_patient_sex": equipment_receive.tag_patient_sex or "",
        "tag_patient_birthdate": equipment_receive.tag_patient_birthdate or "",
        "tag_patient_id": equipment_receive.tag_patient_id or "",
        "tag_sex": equipment_receive.tag_sex or "",
        "tag_instance_id": equipment_receive.tag_instance_id or "",
        "ip_address": equipment_receive.ip_address or "",
        "tag_pacs_property": equipment_receive.tag_pacs_property or "",
    }


def spool_study_link_json(direction, equipment_receive):
    study_instance_uid = equipment_receive.study_instance_uid_tag
    filename = build_filename(direction.pk, FILE_TYPE_STUDY, study_instance_uid)
    return spool_json(filename, build_direction_payload(direction, FILE_TYPE_STUDY, extra=_study_extra_fields(direction, equipment_receive)))


def _result_source_id(direction):
    source_id = str(getattr(direction, "id_in_hospital", None) or "").strip()
    if source_id:
        return source_id
    return str(direction.pk)


def should_spool_result(direction):
    hospital = getattr(direction, "hospital", None)
    return bool(hospital and hospital.json_result_auto_export)


def _result_issledovaniye(direction):
    confirmed = [iss for iss in direction.issledovaniya_set.all() if iss.time_confirmation]
    if confirmed:
        return max(confirmed, key=lambda iss: iss.time_confirmation)
    return direction.issledovaniya_set.order_by("pk").first()


def build_result_json(direction):
    from integration_framework.common_func import direction_pdf_content

    iss = _result_issledovaniye(direction)
    time_confirmation = None
    if iss and iss.time_confirmation:
        time_confirmation = iss.time_confirmation
    elif direction.last_confirmed_at:
        time_confirmation = direction.last_confirmed_at
    pdf_bytes = direction_pdf_content(direction.pk)
    return {
        "_l2_file_type": FILE_TYPE_RESULT,
        "id": _result_source_id(direction),
        "pdf": base64.b64encode(pdf_bytes).decode("utf-8"),
        "time_confirmation": _serialize_value(time_confirmation),
        "doctor_fio": (iss.doc_confirmation_fio if iss else "") or "",
    }


def spool_result_json(direction):
    if not should_spool_result(direction):
        return None
    filename = build_filename(_result_source_id(direction), FILE_TYPE_RESULT)
    return spool_json(filename, build_result_json(direction), spool_dir=get_results_spool_dir())


def connect_ftp(url=None):
    parsed_url = urlparse(url or FTP_JSON_ORDERS_URL)
    ftp = ftplib.FTP(parsed_url.hostname)
    ftp.login(parsed_url.username, parsed_url.password)
    if parsed_url.path:
        ftp.cwd(parsed_url.path)
    return ftp


def _connect():
    return connect_ftp(FTP_JSON_ORDERS_URL)


def process_push_json_orders():
    if not FTP_JSON_ORDERS_URL:
        return

    spool_dir = get_spool_dir()
    if not os.path.isdir(spool_dir):
        return

    files = sorted(f for f in os.listdir(spool_dir) if f.endswith(".json"))
    if not files:
        return

    ftp = None
    try:
        ftp = _connect()
        for filename in files:
            path = os.path.join(spool_dir, filename)
            with open(path, "rb") as f:
                content = f.read()
            ftp.storbinary(f"STOR {filename}", BytesIO(content))
            try:
                archived = _archive_sent_file(path, filename)
                stdout.write(f"ftp_json_orders: sent {filename} -> {archived}\n")
            except OSError:
                logger.exception("ftp_json_orders: failed to archive %s", filename)
    except ftplib.all_errors:
        logger.exception("ftp_json_orders: ftp error")
    finally:
        if ftp:
            try:
                ftp.quit()
            except ftplib.all_errors:
                pass


def process_push_json_results():
    spool_dir = get_results_spool_dir()
    spool_dir_abs = os.path.abspath(spool_dir)
    stdout.write(f"ftp_json_results: 1) spool_dir={spool_dir_abs}\n")

    if not os.path.isdir(spool_dir):
        stdout.write("ftp_json_results: 2) files=[] (directory does not exist)\n")
    else:
        all_files = sorted(os.listdir(spool_dir))
        stdout.write(f"ftp_json_results: 2) files={all_files}\n")

    stdout.write(f"ftp_json_results: 3) FTP_JSON_RESULTS_URL={FTP_JSON_RESULTS_URL}\n")

    if not FTP_JSON_RESULTS_URL:
        stdout.write("ftp_json_results: 4) skip (FTP_JSON_RESULTS_URL is empty)\n")
        return

    if not os.path.isdir(spool_dir):
        stdout.write("ftp_json_results: 4) skip (directory does not exist)\n")
        return

    files = sorted(f for f in os.listdir(spool_dir) if f.endswith(".json"))
    if not files:
        stdout.write("ftp_json_results: 4) skip (no .json files)\n")
        return

    ftp = None
    try:
        ftp = connect_ftp(FTP_JSON_RESULTS_URL)
        stdout.write("ftp_json_results: 4) ftp connected\n")
        for filename in files:
            path = os.path.join(spool_dir, filename)
            with open(path, "rb") as f:
                content = f.read()
            ftp.storbinary(f"STOR {filename}", BytesIO(content))
            try:
                archived = _archive_sent_file(path, filename, archive_dir=get_results_archive_dir())
                stdout.write(f"ftp_json_results: 4) sent {filename} -> {archived}\n")
            except OSError as e:
                stdout.write(f"ftp_json_results: 4) sent {filename} but archive failed: {e}\n")
                logger.exception("ftp_json_results: failed to archive %s", filename)
    except ftplib.all_errors as e:
        stdout.write(f"ftp_json_results: 4) ftp error: {e}\n")
        logger.exception("ftp_json_results: ftp error")
    finally:
        if ftp:
            try:
                ftp.quit()
            except ftplib.all_errors:
                pass


def process_push_json_orders_start():
    stdout.write("Starting push_json_orders process\n")
    while True:
        process_push_json_orders()
        time.sleep(FTP_JSON_ORDERS_INTERVAL_SECONDS)


def process_push_json_results_start():
    stdout.write("Starting push_json_results process\n")
    while True:
        process_push_json_results()
        time.sleep(FTP_JSON_ORDERS_INTERVAL_SECONDS)
