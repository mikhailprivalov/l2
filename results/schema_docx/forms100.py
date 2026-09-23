from io import BytesIO

import pytz
from appconf.manager import SettingManager
from directions.models import DirectionDocument, DocumentSign, Napravleniya, Issledovaniya
from docx.shared import Mm
from docxtpl import DocxTemplate, InlineImage
import os
import datetime
from pdfrw import PdfReader, PdfWriter
from PIL import Image, ImageDraw, ImageFont

from integration_framework.models import EquipmentReceive
from laboratory.settings import COMMAND_DOCX_2_PDF, FONTS_FOLDER
from results.schema_docx.paraclinic_files import append_paraclinic_images_to_pdf, hospital_for_paraclinic_pdf_appendix
from results.sql_func import get_paraclinic_result_by_iss, get_paraclinic_results_by_direction
from slog.models import Log
from hospitals.models import TitleResearchHospital
from utils.dates import normalize_date
import simplejson as json


def _certificate_signs(direction):
    last_time_confirm = direction.last_time_confirm()
    document_for_sign = DirectionDocument.objects.filter(
        direction=direction,
        last_confirmed_at=last_time_confirm,
        is_archive=False,
        file_type=DirectionDocument.PDF,
    ).first()
    if not document_for_sign:
        return []
    signs = []
    seen = set()
    queryset = DocumentSign.objects.filter(document=document_for_sign, sign_certificate__isnull=False).select_related("sign_certificate")
    for sign in queryset:
        thumbprint = sign.sign_certificate.thumbprint
        if thumbprint in seen:
            continue
        seen.add(thumbprint)
        signs.append(sign)
    return signs


def _text_size(font, text):
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _certificate_stamp_image(signs):
    font_bold = ImageFont.truetype(os.path.join(FONTS_FOLDER, "FreeSansBold.ttf"), 28)
    font = ImageFont.truetype(os.path.join(FONTS_FOLDER, "FreeSans.ttf"), 22)
    padding = 18
    line_gap = 8
    block_gap = 16
    blocks = []
    max_width = 0
    total_height = 0
    for sign in signs:
        certificate = sign.sign_certificate
        valid_from = certificate.valid_from.strftime("%d.%m.%Y") if certificate.valid_from else ""
        valid_to = certificate.valid_to.strftime("%d.%m.%Y") if certificate.valid_to else ""
        lines = [
            ("ДОКУМЕНТ ПОДПИСАН ЭЛЕКТРОННОЙ ПОДПИСЬЮ", font_bold),
            (f"Сертификат: {certificate.thumbprint or ''}", font),
            (f"Владелец: {certificate.owner or ''}", font),
            (f"Действителен с {valid_from} по {valid_to}", font),
        ]
        measured = []
        block_width = 0
        block_height = padding * 2
        for text, line_font in lines:
            width, height = _text_size(line_font, text)
            measured.append((text, line_font, height))
            block_width = max(block_width, width)
            block_height += height + line_gap
        block_width += padding * 2
        blocks.append((measured, block_width, block_height))
        max_width = max(max_width, block_width)
        total_height += block_height + block_gap
    if not blocks:
        return None
    total_height -= block_gap
    image = Image.new("RGB", (max_width, total_height), "white")
    draw = ImageDraw.Draw(image)
    top = 0
    for measured, block_width, block_height in blocks:
        box = (0, top, block_width - 1, top + block_height - 1)
        if hasattr(draw, "rounded_rectangle"):
            draw.rounded_rectangle(box, radius=12, outline="black", width=2)
        else:
            draw.rectangle(box, outline="black", width=2)
        text_top = top + padding
        for text, line_font, height in measured:
            draw.text((padding, text_top), text, fill="black", font=line_font)
            text_top += height + line_gap
        top += block_height + block_gap
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    buffer.width_px = image.width
    buffer.height_px = image.height
    return buffer


def stamp_doctor_value(doc, direction, doctor):
    signs = _certificate_signs(direction) if direction else []
    if signs:
        try:
            image = _certificate_stamp_image(signs)
        except Exception as exc:
            Log.log(key=getattr(direction, "pk", ""), type=997, body={getattr(direction, "pk", ""): {"error": str(exc), "message": "Штамп сертификата"}})
            image = None
        if image:
            width_mm = 90
            height_mm = width_mm * image.height_px / image.width_px
            return InlineImage(doc, image, width=Mm(width_mm), height=Mm(height_mm))
    return get_stamp_doctor_image(doc, doctor)


def get_stamp_doctor_image(doc, doctor):
    if not doctor:
        return ""
    stamp_path = doctor.get_signature_stamp_pdf()
    if not stamp_path or not os.path.exists(stamp_path):
        return ""
    width = doctor.width_stamp_jpg if doctor.width_stamp_jpg else 35
    height = doctor.height_stamp_jpg if doctor.height_stamp_jpg else 35
    return InlineImage(doc, stamp_path, width=Mm(width), height=Mm(height))


def _research_title_for_user(iss, user):
    fallback = iss.research.title if iss.research else ""
    hospital_id = TitleResearchHospital.hospital_id_from_user(user)
    return TitleResearchHospital.get_display_title(hospital_id, iss.research, fallback)


def transform_value(field_value, type_field):
    result = ""
    if type_field == 1:
        result = normalize_date(field_value)
    if type_field == 34:
        try:
            field_json = json.loads(field_value)
            code = field_json.get("code")
            title = field_json.get("title")
            result = f"{code} - {title}"
        except:
            result = ""
    return result


def _read_docx_converted_pdf(temp_file_dir: str) -> bytes:
    pdf_path = f"{temp_file_dir}.pdf"
    writer = PdfWriter()
    pdf_all = BytesIO()
    writer.addpages(PdfReader(pdf_path).pages)
    writer.write(pdf_all)
    return pdf_all.getvalue()


def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None, **kwargs):
    current_template_file = None
    if kwargs.get('link', False) == "hospital":
        current_template_file = iss.doc_confirmation.hospital.schema_docx.path
    if kwargs.get('link', False) == "research":
        current_template_file = iss.research.schema_pdf.path
    if kwargs.get('link', False) == "created_direction_hospital":
        current_template_file = direction.hospital.schema_docx_result_created_direction_hospital.path
    try:
        fields_values = get_paraclinic_result_by_iss(iss.pk)
        result_data = {i.attached: transform_value(i.field_value, i.field_type) if i.field_type in [1, 34] else i.field_value for i in fields_values}
        name_pdf_file = ""
        for k, v in result_data.items():
            if "name_file" in k:
                name_pdf_file = f"{name_pdf_file}{v}"
        if name_pdf_file:
            name_pdf_file = f"{name_pdf_file}_{direction.pk}"
            name_pdf_file = name_pdf_file.replace(" ", "_")
        doc = DocxTemplate(current_template_file)
        direction = Napravleniya.objects.filter(pk=iss.napravleniye_id).first()
        contrast_amount = direction.contrast_amount
        dose = direction.dose
        request_code = direction.request_code
        anamnesis = direction.anamnesis
        direction_comment = direction.direction_comment
        fact_research_date = direction.fact_research_date
        fact_research_time = direction.fact_research_time
        converted_dt = ""
        if fact_research_date and fact_research_time:
            naive_datetime = datetime.datetime.combine(fact_research_date, fact_research_time)
            source_timezone = pytz.timezone(direction.hospital.time_zone)
            aware_dt = source_timezone.localize(naive_datetime)
            target_timezone = pytz.timezone('Europe/Moscow')
            converted_dt = aware_dt.astimezone(target_timezone)
        equipment = EquipmentReceive.objects.filter(napravleniye=direction).first()
        equipment_title = ''
        if equipment:
            equipment_title = equipment.equipment_model.title

        individula = direction.client.get_data_individual()
        meta_info = {
            "contrast_amount": contrast_amount,
            "dose": dose,
            "request_code": request_code,
            "anamnesis": anamnesis,
            "direction_comment": direction_comment,
            "converted_dt": converted_dt,
            "equipment_title": equipment_title,
            "date_service": converted_dt.strftime('%d.%m.%Y') if converted_dt else "",
            "time_service": converted_dt.strftime('%H:%M') if converted_dt else "",
            "card_number": direction.client.number,
            "fio": individula.get('fio'),
            "sex": individula.get('sex'),
            "born": individula.get('born'),
            "protocol_number": direction.pk,
            "research": f"{iss.research.code} {_research_title_for_user(iss, user)}",
            "hosp_confirmation": iss.doc_confirmation.hospital.title if iss.doc_confirmation else "",
            "license_data": iss.doc_confirmation.hospital.license_data if iss.doc_confirmation else "",
            "direction_pk": direction.pk,
        }
        context = {**meta_info, **result_data, "stamp_doctor": stamp_doctor_value(doc, direction, iss.doc_confirmation)}
        doc.render(context)
        dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
        today = datetime.datetime.now()
        date_now1 = datetime.datetime.strftime(today, "%y%m%d%H%M%S%f")[:-3]
        date_now_str = str(direction.client_id) + str(date_now1)
        temp_file_dir = os.path.join(dir_param, date_now_str + '_dir')
        doc.save(f"{temp_file_dir}.docx")

        os.system(f"{COMMAND_DOCX_2_PDF} {temp_file_dir}.docx")
        pdf_out = _read_docx_converted_pdf(temp_file_dir)
        pdf_out = append_paraclinic_images_to_pdf(
            pdf_out,
            iss,
            hospital_for_paraclinic_pdf_appendix(direction, iss),
        )
        os.remove(f"{temp_file_dir}.pdf")
        os.remove(f"{temp_file_dir}.docx")
        return pdf_out, name_pdf_file
    except AttributeError as e:
        Log.log(key=direction.pk, type=997, body={direction.pk: {"error": str(e), "protocolid": direction.pk, "message": "Версии библиотек не те"}})
    except Exception as e:
        Log.log(key=direction.pk, type=997, body={direction.pk: {"error": str(e), "protocolid": direction.pk}})

    return fwb


def form_02(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None, **kwargs):
    current_template_file = None
    if kwargs.get('link', False) == "created_direction_hospital":
        current_template_file = direction.hospital.schema_docx_result_created_direction_hospital.path
    try:
        fields_values = get_paraclinic_result_by_iss(iss.pk)
        result_data = {i.field_title: transform_value(i.field_value, i.field_type) if i.field_type in [1, 34] else i.field_value for i in fields_values}
        name_pdf_file = ""
        for k, v in result_data.items():
            if "name_file" in k:
                name_pdf_file = f"{name_pdf_file}{v}"
        if name_pdf_file:
            name_pdf_file = f"{name_pdf_file}_{direction.pk}"
            name_pdf_file = name_pdf_file.replace(" ", "_")
        doc = DocxTemplate(current_template_file)
        direction = Napravleniya.objects.filter(pk=iss.napravleniye_id).first()
        contrast_amount = direction.contrast_amount
        dose = direction.dose
        request_code = direction.request_code
        anamnesis = direction.anamnesis
        direction_comment = direction.direction_comment
        fact_research_date = direction.fact_research_date
        fact_research_time = direction.fact_research_time
        converted_dt = ""
        if fact_research_date and fact_research_time:
            naive_datetime = datetime.datetime.combine(fact_research_date, fact_research_time)
            source_timezone = pytz.timezone(direction.hospital.time_zone)
            aware_dt = source_timezone.localize(naive_datetime)
            target_timezone = pytz.timezone('Europe/Moscow')
            converted_dt = aware_dt.astimezone(target_timezone)
        equipment = EquipmentReceive.objects.filter(napravleniye=direction).first()
        equipment_title = ''
        if equipment:
            equipment_title = equipment.equipment_model.title

        individula = direction.client.get_data_individual()
        if direction.doc_who_create:
            laborant = direction.doc_who_create.get_fio()
        else:
            laborant = direction.doc.get_fio()

        result = get_paraclinic_results_by_direction(iss.napravleniye_id)
        data = {r.cda_title_field: r.value for r in result}
        reason_visit = f"{data.get('пр-Диагноз', '')} {data.get('пр-Причина', '')}"
        stage = f"{data.get('пр-Этап исследования', '')}"
        limit_visual = f"{data.get('пр-Ограничения визуализации', '')}"
        peroral_amount = f"{data.get('пр-Пероральный контраст', '')}"
        allergy = f"{data.get('пр-Аллергическая реакция', '')}"

        meta_info = {
            "contrast_amount": contrast_amount,
            "dose": dose,
            "request_code": request_code,
            "anamnesis": anamnesis,
            "direction_comment": direction_comment,
            "converted_dt": converted_dt,
            "equipment_title": equipment_title,
            "date_service": converted_dt.strftime('%d.%m.%Y') if converted_dt else "",
            "time_service": converted_dt.strftime('%H:%M') if converted_dt else "",
            "card_number": direction.client.number,
            "fio": individula.get('fio'),
            "sex": individula.get('sex'),
            "born": individula.get('born'),
            "protocol_number": direction.pk,
            "research": f"{iss.research.code} {_research_title_for_user(iss, user)}",
            "hosp_confirmation": iss.doc_confirmation.hospital.title if iss.doc_confirmation else "",
            "license_data": iss.doc_confirmation.hospital.license_data if iss.doc_confirmation else "",
            "direction_pk": direction.pk,
            "doc_confirm": iss.doc_confirmation.get_full_fio(),
            "time_confirm": iss.time_confirmation.astimezone(pytz.timezone('Europe/Moscow')).strftime("%d.%m.%Y - %H:%M:%S") if iss.time_confirmation else "XX:XX:XX:XX:XX",
            "rt_laborant": laborant,
            "reason_visit": reason_visit,
            "limit_visual": limit_visual,
            "stage": stage,
            "peroral_amount": peroral_amount,
            "allergy": allergy,
        }
        context = {**meta_info, **result_data, "stamp_doctor": stamp_doctor_value(doc, direction, iss.doc_confirmation)}
        doc.render(context)

        dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
        today = datetime.datetime.now()
        date_now1 = datetime.datetime.strftime(today, "%y%m%d%H%M%S%f")[:-3]
        date_now_str = str(direction.client_id) + str(date_now1)
        temp_file_dir = os.path.join(dir_param, date_now_str + '_dir')
        doc.save(f"{temp_file_dir}.docx")

        os.system(f"{COMMAND_DOCX_2_PDF} {temp_file_dir}.docx")
        pdf_out = _read_docx_converted_pdf(temp_file_dir)
        pdf_out = append_paraclinic_images_to_pdf(
            pdf_out,
            iss,
            hospital_for_paraclinic_pdf_appendix(direction, iss),
        )
        os.remove(f"{temp_file_dir}.pdf")
        os.remove(f"{temp_file_dir}.docx")
        return pdf_out, name_pdf_file
    except AttributeError as e:
        Log.log(key=direction.pk, type=997, body={direction.pk: {"error": str(e), "protocolid": direction.pk, "message": "Версии библиотек не те"}})
    except Exception as e:
        Log.log(key=direction.pk, type=997, body={direction.pk: {"error": str(e), "protocolid": direction.pk}})

    return fwb
