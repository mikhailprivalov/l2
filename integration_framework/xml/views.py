import base64
import os
from xml.sax.saxutils import escape

from django.http import HttpResponse, JsonResponse
from django.utils.timezone import localtime
from jinja2 import Environment, FileSystemLoader
from rest_framework.decorators import api_view

from directions.models import DirectionDocument, DocumentSign, Issledovaniya, Napravleniya
from laboratory.settings import BASE_DIR, CDA_TEMPLATE_XML_DIRECTORY, N3_IEMK_GUID, N3_IEMK_ID_LPU
from users.models import DoctorProfileEmployeePosition

SIGN_DOCTOR = "Врач"
SIGN_ORGANIZATION = "Медицинская организация"
NS_MED_DOC = "http://schemas.datacontract.org/2004/07/N3.EMK.Dto.MedRec.MedDoc"
NS_MED_REC = "http://schemas.datacontract.org/2004/07/N3.EMK.Dto.MedRec"
NS_DTO = "http://schemas.datacontract.org/2004/07/N3.EMK.Dto"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"


def _fail(message):
    return JsonResponse({"ok": False, "message": message}, status=400)


def _xml_text(tag, value, nil_if_empty=False):
    if value is None or value == "":
        if nil_if_empty:
            return f"<{tag} i:nil=\"true\"/>"
        return f"<{tag}></{tag}>"
    return f"<{tag}>{escape(str(value))}</{tag}>"


def _nil(tag):
    return f"<{tag} i:nil=\"true\"/>"


def _clean_sign(value):
    return "".join((value or "").split())


def _identity_document(snils):
    return (
        "<c:Documents>"
        "<c:IdentityDocument>"
        f"{_xml_text('c:DocN', snils)}"
        f"{_nil('c:DocS')}"
        f"{_xml_text('c:DocumentName', 'СНИЛС')}"
        f"{_nil('c:ExpiredDate')}"
        f"{_xml_text('c:IdDocumentType', 223)}"
        f"{_nil('c:IdProvider')}"
        f"{_nil('c:IssuedDate')}"
        f"{_xml_text('c:ProviderName', 'ПФР')}"
        f"{_nil('c:RegionCode')}"
        f"{_nil('c:StartDate')}"
        "</c:IdentityDocument>"
        "</c:Documents>"
    )


def _human_name(doctor):
    return (
        "<c:HumanName>"
        f"{_xml_text('c:GivenName', doctor.name or '')}"
        f"{_xml_text('c:MiddleName', doctor.patronymic or '')}"
        f"{_xml_text('c:FamilyName', doctor.family or '')}"
        "</c:HumanName>"
    )


def _doctor_birthdate(doctor):
    link = (
        DoctorProfileEmployeePosition.objects.filter(doctor_profile=doctor, employee_position__employee__date_birth__isnull=False)
        .select_related("employee_position__employee")
        .order_by("id")
        .first()
    )
    if not link or not link.employee_position or not link.employee_position.employee or not link.employee_position.employee.date_birth:
        return None
    return f"{link.employee_position.employee.date_birth.isoformat()}T00:00:00"


def _person(doctor, birthdate=None, include_birthdate=False):
    birth = ""
    if include_birthdate:
        birth = _xml_text("c:Birthdate", birthdate or "", nil_if_empty=True)
    return "<c:Person>" f"{_human_name(doctor)}" f"{_nil('c:Sex')}" f"{birth}" f"{_xml_text('c:IdPersonMis', doctor.pk)}" f"{_identity_document(doctor.snils or '')}" "</c:Person>"


def _n3_code(value):
    if value is None:
        return None
    return str(value)


def _author_xml(doctor):
    position = _n3_code(doctor.position.n3_id if doctor.position_id and doctor.position else None)
    return (
        f'<b:Author xmlns:c="{NS_DTO}">'
        f"{_person(doctor, birthdate=_doctor_birthdate(doctor), include_birthdate=True)}"
        f"{_nil('c:IdLpu')}"
        f"{_xml_text('c:IdPosition', position, nil_if_empty=True)}"
        f"{_xml_text('c:IdMedicalStaff', 0)}"
        f"{_nil('c:SpecialityName')}"
        f"{_nil('c:PositionName')}"
        "</b:Author>"
    )


def _personal_sign_xml(sign):
    doctor = sign.executor
    speciality = _n3_code(doctor.specialities.n3_id if doctor.specialities_id and doctor.specialities else None)
    position = _n3_code(doctor.position.n3_id if doctor.position_id and doctor.position else None)
    return (
        "<b:MedDocumentDto.PersonalSign>"
        f"{_xml_text('b:Sign', _clean_sign(sign.sign_value))}"
        f'<b:Doctor xmlns:c="{NS_DTO}">'
        f"{_person(doctor)}"
        f"{_nil('c:IdLpu')}"
        f"{_xml_text('c:IdSpeciality', speciality, nil_if_empty=True)}"
        f"{_xml_text('c:IdPosition', position, nil_if_empty=True)}"
        f"{_xml_text('c:IdMedicalStaff', 0)}"
        f"{_nil('c:SpecialityName')}"
        f"{_nil('c:PositionName')}"
        "</b:Doctor>"
        "</b:MedDocumentDto.PersonalSign>"
    )


def _cda_document(direction):
    documents = DirectionDocument.objects.filter(direction=direction, file_type=DirectionDocument.CDA, is_archive=False).exclude(file="").exclude(file__isnull=True)
    last_confirm = direction.last_time_confirm()
    document = None
    if last_confirm:
        document = documents.filter(last_confirmed_at=last_confirm).order_by("-id").first()
    if not document:
        document = documents.order_by("-last_confirmed_at", "-id").first()
    return document


def _confirmed_iss(direction):
    return Issledovaniya.objects.filter(napravleniye=direction).select_related("research").order_by("-time_confirmation").first()


def build_add_med_record_xml(direction):
    document = _cda_document(direction)
    if not document or not document.file:
        return None, "Нет CDA документа"

    signs = list(DocumentSign.objects.filter(document=document).select_related("executor", "executor__position", "executor__specialities").order_by("signed_at", "id"))
    doctor_signs = [sign for sign in signs if sign.sign_type == SIGN_DOCTOR and _clean_sign(sign.sign_value)]
    org_signs = [sign for sign in signs if sign.sign_type == SIGN_ORGANIZATION and _clean_sign(sign.sign_value)]
    if not doctor_signs or not org_signs:
        return None, "Нет двух подписей CDA: врача и медицинской организации"

    try:
        cda_b64 = base64.b64encode(document.file.read()).decode("ascii")
    except OSError:
        return None, "Нет CDA документа"
    if not cda_b64:
        return None, "Нет CDA документа"

    org_sign = org_signs[-1]
    author = doctor_signs[-1].executor
    hospital = author.hospital
    iss = _confirmed_iss(direction)
    med_type = ""
    if iss and iss.research_id and iss.research.n3_id_med_document_type:
        med_type = str(iss.research.n3_id_med_document_type)
    created = ""
    if iss and iss.time_confirmation:
        created = localtime(iss.time_confirmation).isoformat()

    personal = "".join(_personal_sign_xml(sign) for sign in doctor_signs)
    xml = (
        '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">'
        "<s:Body>"
        '<AddMedRecord xmlns="http://tempuri.org/">'
        f"{_xml_text('guid', N3_IEMK_GUID or '')}"
        f"{_xml_text('idLpu', hospital.n3_id if hospital else '')}"
        f"{_xml_text('idPatientMis', direction.client_id)}"
        "<medRecord "
        'i:type="b:MedDocument" '
        f'xmlns:a="{NS_MED_REC}" '
        f'xmlns:i="{NS_XSI}" '
        f'xmlns:b="{NS_MED_DOC}">'
        "<b:Attachments>"
        "<b:MedDocumentDto.DocumentAttachment>"
        f"{_xml_text('b:Data', cda_b64)}"
        f"{_xml_text('b:OrganizationSign', _clean_sign(org_sign.sign_value))}"
        "<b:PersonalSigns>"
        f"{personal}"
        "</b:PersonalSigns>"
        f"{_xml_text('b:MimeType', 'text/xml')}"
        f"{_nil('b:Url')}"
        "</b:MedDocumentDto.DocumentAttachment>"
        "</b:Attachments>"
        f"{_author_xml(author)}"
        f"{_xml_text('b:CreationDate', created)}"
        f"{_nil('b:FhirMedDocumentType')}"
        f"{_xml_text('b:Header', direction.get_eds_title())}"
        f"{_xml_text('b:IdDocumentMis', direction.pk)}"
        f"{_xml_text('b:IdMedDocumentType', med_type)}"
        f"{_nil('b:Observations')}"
        "</medRecord>"
        "</AddMedRecord>"
        "</s:Body>"
        "</s:Envelope>"
    )
    return xml, None


@api_view(["POST"])
def add_med_record(request):
    raw_pk = request.data.get("pk") if isinstance(request.data, dict) else None
    if raw_pk is None or isinstance(raw_pk, bool) or not str(raw_pk).isdigit():
        return _fail("Номер направления не указан")
    direction = Napravleniya.objects.select_related("client").filter(pk=int(raw_pk)).first()
    if not direction:
        return _fail("Направление не найдено")
    xml, message = build_add_med_record_xml(direction)
    if message:
        return _fail(message)
    return HttpResponse(xml, content_type="text/xml; charset=utf-8")


def _direction_from_request(request):
    raw_pk = request.data.get("pk") if isinstance(request.data, dict) else None
    if raw_pk is None or isinstance(raw_pk, bool) or not str(raw_pk).isdigit():
        return None, "Номер направления не указан"
    direction = Napravleniya.objects.select_related("client").filter(pk=int(raw_pk)).first()
    if not direction:
        return None, "Направление не найдено"
    return direction, None


def _signed_cda(direction):
    document = _cda_document(direction)
    if not document or not document.file:
        return None, None, None, "Нет CDA документа"
    signs = list(DocumentSign.objects.filter(document=document).select_related("executor", "executor__position", "executor__specialities").order_by("signed_at", "id"))
    doctor_signs = [sign for sign in signs if sign.sign_type == SIGN_DOCTOR and _clean_sign(sign.sign_value)]
    org_signs = [sign for sign in signs if sign.sign_type == SIGN_ORGANIZATION and _clean_sign(sign.sign_value)]
    if not doctor_signs or not org_signs:
        return None, None, None, "Нет двух подписей CDA: врача и медицинской организации"
    try:
        cda_b64 = base64.b64encode(document.file.read()).decode("ascii")
    except OSError:
        return None, None, None, "Нет CDA документа"
    if not cda_b64:
        return None, None, None, "Нет CDA документа"
    return cda_b64, doctor_signs, org_signs[-1], None


def _template_doctor(doctor):
    speciality = ""
    if doctor.specialities_id and doctor.specialities and doctor.specialities.n3_id is not None:
        speciality = str(doctor.specialities.n3_id)
    return {
        "givenName": doctor.name or "",
        "middleName": doctor.patronymic or "",
        "familyName": doctor.family or "",
        "idPersonMis": str(doctor.pk),
        "snils": doctor.snils or "",
        "idSpeciality": speciality,
        "idPosition": (doctor.n3_id or "").strip(),
    }


def build_add_med_record_template_xml(direction):
    cda_b64, doctor_signs, org_sign, message = _signed_cda(direction)
    if message:
        return None, message
    author = _template_doctor(doctor_signs[-1].executor)
    hospital = doctor_signs[-1].executor.hospital
    id_lpu = (hospital.n3_id or "").strip() if hospital else ""
    if not id_lpu:
        id_lpu = (N3_IEMK_ID_LPU or "").strip()
    iss = _confirmed_iss(direction)
    med_type = ""
    if iss and iss.research_id and iss.research.n3_id_med_document_type:
        med_type = str(iss.research.n3_id_med_document_type)
    if not med_type:
        med_type = "309"
    created = ""
    if iss and iss.time_confirmation:
        created = localtime(iss.time_confirmation).isoformat()
    card_number = ""
    if direction.client_id and direction.client and direction.client.number:
        card_number = str(direction.client.number).strip()
    context = {
        "guid": (N3_IEMK_GUID or "").strip(),
        "idLpu": id_lpu,
        "idPatientMis": card_number,
        "data": cda_b64,
        "organizationSign": _clean_sign(org_sign.sign_value),
        "personalSigns": [{"sign": _clean_sign(sign.sign_value), "doctor": _template_doctor(sign.executor)} for sign in doctor_signs],
        "author": author,
        "creationDate": created,
        "header": direction.get_eds_title(),
        "idDocumentMis": str(direction.pk),
        "idMedDocumentType": med_type,
    }
    loader = FileSystemLoader(os.path.join(BASE_DIR, "xml_generate", CDA_TEMPLATE_XML_DIRECTORY))
    env = Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
    return env.get_template("remd/add_med_record.xml").render(context), None


@api_view(["POST"])
def add_med_record_template(request):
    direction, message = _direction_from_request(request)
    if message:
        return _fail(message)
    xml, message = build_add_med_record_template_xml(direction)
    if message:
        return _fail(message)
    return HttpResponse(xml, content_type="text/xml; charset=utf-8")
