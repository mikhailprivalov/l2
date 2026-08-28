import datetime
import decimal
import ftplib
import logging
import os
import time
import uuid
from io import BytesIO
from sys import stdout
from urllib.parse import urlparse

import simplejson as json

from laboratory.settings import BASE_DIR, FTP_JSON_ORDERS_URL, FTP_JSON_ORDERS_SPOOL_DIR, FTP_JSON_ORDERS_INTERVAL_SECONDS

logger = logging.getLogger(__name__)

FILE_TYPE_ORDER = "ord"
FILE_TYPE_STUDY = "dcm"


def get_spool_dir():
    return FTP_JSON_ORDERS_SPOOL_DIR or os.path.join(BASE_DIR, "ftp_json_spool")


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
    payload["_l2_file_type"] = file_type
    if extra:
        payload.update(extra)
    return payload


def _safe_filename_part(value):
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in str(value))


def build_filename(direction_pk, file_type, study_instance_uid=None, event_time=None):
    event_time = event_time or datetime.datetime.now()
    timestamp = f"{event_time:%Y%m%d}_{event_time:%H%M%S}{event_time.microsecond // 1000:03d}"
    if file_type == FILE_TYPE_STUDY:
        return f"{direction_pk}_{timestamp}_{_safe_filename_part(study_instance_uid or 'nouid')}_{FILE_TYPE_STUDY}.json"
    return f"{direction_pk}_{timestamp}_{FILE_TYPE_ORDER}.json"


def spool_json(filename, payload):
    spool_dir = get_spool_dir()
    os.makedirs(spool_dir, exist_ok=True)
    path = os.path.join(spool_dir, filename)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)
    return path


def spool_order_json(direction):
    filename = build_filename(direction.pk, FILE_TYPE_ORDER)
    return spool_json(filename, build_direction_payload(direction, FILE_TYPE_ORDER))


def spool_study_link_json(direction, equipment_receive):
    study_instance_uid = equipment_receive.study_instance_uid_tag
    filename = build_filename(direction.pk, FILE_TYPE_STUDY, study_instance_uid)
    extra = {
        "equipment_receive_id": equipment_receive.pk,
        "study_instance_uid": study_instance_uid,
    }
    return spool_json(filename, build_direction_payload(direction, FILE_TYPE_STUDY, extra))


def _connect():
    parsed_url = urlparse(FTP_JSON_ORDERS_URL)
    ftp = ftplib.FTP(parsed_url.hostname)
    ftp.login(parsed_url.username, parsed_url.password)
    if parsed_url.path:
        ftp.cwd(parsed_url.path)
    return ftp


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
            os.remove(path)
            stdout.write(f"ftp_json_orders: sent {filename}\n")
    except ftplib.all_errors:
        logger.exception("ftp_json_orders: ftp error")
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
