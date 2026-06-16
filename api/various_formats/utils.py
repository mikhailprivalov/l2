import datetime
from io import BytesIO
from zipfile import ZipFile

import pytz
import simplejson as json
from django.http import HttpRequest, QueryDict
from docxtpl import DocxTemplate

from directions.models import Issledovaniya, Napravleniya
from forms import views as forms_views
from integration_framework.models import EquipmentReceive
from results.sql_func import get_paraclinic_result_by_iss
from utils.dates import normalize_date


def _transform_value(field_value, type_field):
    result = ""
    if type_field == 1:
        result = normalize_date(field_value)
    if type_field == 34:
        try:
            field_json = json.loads(field_value)
            code = field_json.get("code")
            title = field_json.get("title")
            result = f"{code} - {title}"
        except Exception:
            result = ""
    return result


def get_docx_template_path(iss: Issledovaniya):
    if iss.doc_confirmation and iss.doc_confirmation.hospital.schema_docx:
        return iss.doc_confirmation.hospital.schema_docx.path

    schema_pdf = iss.research.schema_pdf
    if schema_pdf and str(schema_pdf).split(".")[-1] == "docx":
        return schema_pdf.path

    return None


def get_docx_protocol_context(direction: Napravleniya, iss: Issledovaniya):
    fields_values = get_paraclinic_result_by_iss(iss.pk)
    result_data = {
        i.attached: _transform_value(i.field_value, i.field_type) if i.field_type in [1, 34] else i.field_value for i in fields_values
    }

    converted_dt = ""
    if direction.fact_research_date and direction.fact_research_time:
        naive_datetime = datetime.datetime.combine(direction.fact_research_date, direction.fact_research_time)
        source_timezone = pytz.timezone(direction.hospital.time_zone)
        aware_dt = source_timezone.localize(naive_datetime)
        converted_dt = aware_dt.astimezone(pytz.timezone("Europe/Moscow"))

    equipment = EquipmentReceive.objects.filter(napravleniye=direction).first()
    equipment_title = equipment.equipment_model.title if equipment else ""

    individual = direction.client.get_data_individual()
    meta_info = {
        "contrast_amount": direction.contrast_amount,
        "dose": direction.dose,
        "anamnesis": direction.anamnesis,
        "direction_comment": direction.direction_comment,
        "converted_dt": converted_dt,
        "equipment_title": equipment_title,
        "date_service": converted_dt.strftime("%d.%m.%Y") if converted_dt else "",
        "time_service": converted_dt.strftime("%H:%M") if converted_dt else "",
        "card_number": direction.client.number,
        "fio": individual.get("fio"),
        "sex": individual.get("sex"),
        "born": individual.get("born"),
        "protocol_number": direction.pk,
        "research": iss.research.title,
        "hosp_confirmation": iss.doc_confirmation.hospital.title if iss.doc_confirmation else "",
        "license_data": iss.doc_confirmation.hospital.license_data if iss.doc_confirmation else "",
        "direction_pk": direction.pk,
    }
    return {**meta_info, **result_data}


def get_docx_protocol_bytes(direction: Napravleniya, iss: Issledovaniya):
    template_path = get_docx_template_path(iss)
    if not template_path:
        return None, "Docx-шаблон не настроен для направления"

    doc = DocxTemplate(template_path)
    doc.render(get_docx_protocol_context(direction, iss))

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue(), None


def extract_document_xml(docx_bytes):
    with ZipFile(BytesIO(docx_bytes)) as archive:
        return archive.read("word/document.xml").decode("utf-8")


def get_docx_protocol_xml_from_form(form_type, params, user):
    request = HttpRequest()
    request.method = "GET"
    request.user = user

    query = QueryDict(mutable=True)
    query["type"] = form_type
    for key, value in params.items():
        if value is not None:
            query[key] = str(value)
    request.GET = query

    try:
        response = forms_views.docx(request)
    except Exception as exc:
        return None, str(exc)

    if response.status_code != 200:
        return None, "Ошибка генерации docx"

    if not response.content:
        return None, "Пустой docx-документ"

    return extract_document_xml(response.content), None
