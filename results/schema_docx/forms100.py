from io import BytesIO

import pytz
from appconf.manager import SettingManager
from directions.models import Napravleniya, Issledovaniya
from docxtpl import DocxTemplate
import os
import datetime
from pdfrw import PdfReader, PdfWriter

from integration_framework.models import EquipmentReceive
from laboratory.settings import COMMAND_DOCX_2_PDF
from results.sql_func import get_paraclinic_result_by_iss
from slog.models import Log
from utils.dates import normalize_date
import simplejson as json


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
            "research": iss.research.title,
            "hosp_confirmation": iss.doc_confirmation.hospital.title if iss.doc_confirmation else "",
            "license_data": iss.doc_confirmation.hospital.license_data if iss.doc_confirmation else "",
            "direction_pk": direction.pk,
        }
        context = {**meta_info, **result_data}
        doc.render(context)
        dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
        today = datetime.datetime.now()
        date_now1 = datetime.datetime.strftime(today, "%y%m%d%H%M%S%f")[:-3]
        date_now_str = str(direction.client_id) + str(date_now1)
        temp_file_dir = os.path.join(dir_param, date_now_str + '_dir')
        doc.save(f"{temp_file_dir}.docx")

        os.system(f"{COMMAND_DOCX_2_PDF} {temp_file_dir}.docx")
        writer = PdfWriter()
        pdf_all = BytesIO()
        writer.addpages(PdfReader(f"{temp_file_dir}.pdf").pages)
        writer.write(pdf_all)
        pdf_out = pdf_all.getvalue()
        os.remove(f"{temp_file_dir}.pdf")
        os.remove(f"{temp_file_dir}.docx")
        return pdf_out, name_pdf_file
    except AttributeError as e:
        Log.log(key=direction.pk, type=997, body={direction.pk: {"error": e, "protocolid": direction.pk, "message": "Версии библиотек не те"}})
    except Exception as e:
        Log.log(key=direction.pk, type=997, body={direction.pk: {"error": e, "protocolid": direction.pk}})

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
            "research": iss.research.title,
            "hosp_confirmation": iss.doc_confirmation.hospital.title if iss.doc_confirmation else "",
            "license_data": iss.doc_confirmation.hospital.license_data if iss.doc_confirmation else "",
            "direction_pk": direction.pk,
            "doc_confirm": iss.doc_confirmation.get_full_fio(),
            "time_confirm": iss.time_confirmation.astimezone(pytz.timezone('Europe/Moscow')).strftime("%d.%m.%Y - %H:%M:%S") if iss.time_confirmation else "XX:XX:XX:XX:XX"
        }
        context = {**meta_info, **result_data}
        doc.render(context)

        dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
        today = datetime.datetime.now()
        date_now1 = datetime.datetime.strftime(today, "%y%m%d%H%M%S%f")[:-3]
        date_now_str = str(direction.client_id) + str(date_now1)
        temp_file_dir = os.path.join(dir_param, date_now_str + '_dir')
        doc.save(f"{temp_file_dir}.docx")

        os.system(f"{COMMAND_DOCX_2_PDF} {temp_file_dir}.docx")
        writer = PdfWriter()
        pdf_all = BytesIO()
        writer.addpages(PdfReader(f"{temp_file_dir}.pdf").pages)
        writer.write(pdf_all)
        pdf_out = pdf_all.getvalue()
        os.remove(f"{temp_file_dir}.pdf")
        os.remove(f"{temp_file_dir}.docx")
        return pdf_out, name_pdf_file
    except AttributeError as e:
        Log.log(key=direction.pk, type=997, body={direction.pk: {"error": e, "protocolid": direction.pk, "message": "Версии библиотек не те"}})
    except Exception as e:
        Log.log(key=direction.pk, type=997, body={direction.pk: {"error": e, "protocolid": direction.pk}})

    return fwb

