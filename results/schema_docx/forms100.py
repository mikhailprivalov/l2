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


def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None, **kwargs):
    current_template_file = None
    if kwargs.get('link', False) == "hospital":
        current_template_file = iss.doc_confirmation.hospital.schema_docx.path
    if kwargs.get('link', False) == "research":
        current_template_file = iss.research.schema_pdf.path
    try:
        fields_values = get_paraclinic_result_by_iss(iss.pk)
        result_data = {i.field_title: i.field_value for i in fields_values}
        doc = DocxTemplate(current_template_file)
        direction = Napravleniya.objects.filter(pk=iss.napravleniye_id).first()
        contrast_amount = direction.contrast_amount
        dose = direction.dose
        anamnesis = direction.anamnesis
        direction_comment = direction.direction_comment
        fact_research_date = direction.fact_research_date
        fact_research_time = direction.fact_research_time

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
            "date_service": converted_dt.strftime('%d.%m.%Y'),
            "time_service": converted_dt.strftime('%H:%M'),
            "card_number": direction.client.number,
            "fio": individula.get('fio'),
            "sex": individula.get('sex'),
            "born": individula.get('born'),
            "protocol_number": direction.pk,
            "research": iss.research.title,
            "hosp_confirmation": iss.doc_confirmation.hospital.title,
            "license_data": iss.doc_confirmation.hospital.license_data
        }
        context = {
            **meta_info,
            **result_data
        }
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
        return pdf_out
    except Exception as e:
        print(f"Ошибка: {e}")

    return fwb