import json
import os
import shlex
import uuid
from datetime import date, datetime, timedelta
from io import BytesIO
from urllib.parse import quote

from django.http import HttpResponse
from docxtpl import DocxTemplate

from appconf.manager import SettingManager
from document_management.models import Documents
from employees.models import EmployeePosition
from laboratory.settings import COMMAND_DOCX_2_PDF
from results.schema_docx.forms100 import transform_value
from results.sql_func import get_paraclinic_result_by_iss
from slog.models import Log

MENTEE_FIELD_TYPE = 46
MENTOR_FIELD_TYPE = 47

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

_MONTHS_GENITIVE = (
    "",
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)


def _error(message, status=400):
    return HttpResponse(message, status=status, content_type="text/plain; charset=utf-8")


def _file_name(document, extension):
    title = ""
    if document.type_document and document.type_document.title:
        title = document.type_document.title
    safe = "".join(char if char.isalnum() or char in " _-" else "_" for char in title).strip() or "document"
    return f"{safe}-{document.pk}.{extension}"


def _file_response(payload, name, content_type, attachment):
    response = HttpResponse(payload, content_type=content_type)
    disposition = "attachment" if attachment else "inline"
    response["Content-Disposition"] = f"{disposition}; filename*=utf-8''{quote(name)}"
    return response


def _person_payload(raw):
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    if isinstance(data, dict):
        return data
    return {}


def _person_print_values(raw):
    payload = _person_payload(raw)
    stored_fio = str(payload.get("fio") or "").strip()
    try:
        position_id = int(payload.get("id"))
    except (TypeError, ValueError):
        position_id = None
    row = None
    if position_id:
        row = EmployeePosition.objects.filter(pk=position_id).select_related("employee", "position", "department").first()
    if not row:
        return stored_fio, "", ""
    fio = EmployeePosition._employee_fio(row.employee).strip() if row.employee_id else stored_fio
    position = (row.position.name or "").strip() if row.position_id else ""
    department = (row.department.name or "").strip() if row.department_id else ""
    return fio or stored_fio, position, department


def _parse_print_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def _shift_date(value, days, months):
    months = int(months or 0)
    days = int(days or 0)
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)
    shifted = date(year, month, min(value.day, month_end.day))
    return shifted + timedelta(days=days)


def ru_date(value, days=0, months=0):
    parsed = _parse_print_date(value)
    if not parsed:
        return ""
    try:
        shifted = _shift_date(parsed, days, months)
    except (TypeError, ValueError, OverflowError):
        return ""
    return f"«{shifted.day:02d}» {_MONTHS_GENITIVE[shifted.month]} {shifted.year}"


def _context_for_iss(iss_pk):
    context = {}
    if not iss_pk:
        return context
    for row in get_paraclinic_result_by_iss(iss_pk):
        key = (row.attached or "").strip()
        if not key:
            continue
        try:
            field_type = int(row.field_type)
        except (TypeError, ValueError):
            field_type = None
        value = row.field_value if row.field_value is not None else ""
        if field_type in (MENTEE_FIELD_TYPE, MENTOR_FIELD_TYPE):
            fio, position, department = _person_print_values(value)
            context[key] = fio
            context[f"{key}_fio"] = fio
            context[f"{key}_dolzhnost"] = position
            context[f"{key}_podrazdelenie"] = department
            continue
        if field_type in (1, 34):
            value = transform_value(value, field_type) or ""
        context[key] = value
    return context


def _render_docx_bytes(document):
    from directions.models import Issledovaniya

    iss = Issledovaniya.objects.filter(document=document).order_by("pk").only("pk").first()
    template = DocxTemplate(document.type_document.print_docx.path)
    context = _context_for_iss(iss.pk if iss else None)
    context["ru_date"] = ru_date
    template.render(context)
    buffer = BytesIO()
    template.save(buffer)
    return buffer.getvalue()


def _docx_bytes_to_pdf(docx_bytes):
    command = (COMMAND_DOCX_2_PDF or "").strip()
    if not command:
        raise RuntimeError("Не настроена конвертация docx в pdf")
    dir_param = SettingManager.get("dir_param", default="/tmp", default_type="s")
    temp_file_dir = os.path.join(dir_param, f"dou_print_{uuid.uuid4().hex}")
    docx_path = f"{temp_file_dir}.docx"
    pdf_path = f"{temp_file_dir}.pdf"
    try:
        with open(docx_path, "wb") as handle:
            handle.write(docx_bytes)
        os.system(f"{command} {shlex.quote(docx_path)}")
        if not os.path.exists(pdf_path):
            raise RuntimeError("PDF не создан")
        with open(pdf_path, "rb") as handle:
            return handle.read()
    finally:
        for path in (docx_path, pdf_path):
            if os.path.exists(path):
                os.remove(path)


def render_document_print(document_id, output_format, doctor):
    try:
        pk = int(document_id)
    except (TypeError, ValueError):
        return _error("Документ не найден")
    document = Documents.objects.select_related("type_document").filter(pk=pk).first()
    if not doctor or not document or not Documents.can_see_document(document, doctor):
        return _error("Документ не найден")
    if not document.type_document_id or not document.type_document.print_docx:
        return _error("У вида нет шаблона печати")
    output_format = (output_format or "").lower()
    if output_format not in ("docx", "pdf"):
        return _error("Укажите формат docx или pdf")
    try:
        docx_bytes = _render_docx_bytes(document)
    except Exception as exc:
        Log.log(key=document.pk, type=997, body={document.pk: {"error": str(exc), "message": "Печать ДОУ docx"}})
        return _error("Не удалось заполнить шаблон")
    if output_format == "docx":
        return _file_response(docx_bytes, _file_name(document, "docx"), DOCX_CONTENT_TYPE, True)
    try:
        pdf_bytes = _docx_bytes_to_pdf(docx_bytes)
    except Exception as exc:
        Log.log(key=document.pk, type=997, body={document.pk: {"error": str(exc), "message": "Печать ДОУ pdf"}})
        return _error("Не удалось сделать PDF")
    return _file_response(pdf_bytes, _file_name(document, "pdf"), "application/pdf", False)
