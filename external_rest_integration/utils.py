from django.core.files.base import ContentFile
from directions.sql_func import get_tube_by_number
from external_rest_integration.integration import make_request_get_token, rest_make_request_get, rest_make_request_get_result
from ftp_orders.main import FTPConnection
from hl7_actions.hl7_generator import HL7Generator, create_sample_data
from hospitals.models import Hospitals
from directions.models import Napravleniya, IssledovaniyaFiles, Issledovaniya
import json
import base64

from laboratory.utils import current_time
from slog.models import Log
import os
from laboratory.settings import BASE_DIR
import datetime
from sys import stdout
import time


def rest_api_pull_result(only_new_order=True):
    hospitals = Hospitals.get_hospitals_pull_results_from_external_system()
    hospitals_id = {i.pk: i.auth_data_for_rest for i in hospitals}
    hospitals_id_ftp_connect = {i.pk: i.result_push_by_numbers_for_rest for i in hospitals}
    hospitals_object = {i.pk: i for i in hospitals}
    stdout.write(f"Iterating over {len(hospitals_id_ftp_connect)} servers")

    d_qs = Napravleniya.objects.filter(order_redirection_number_is_finished=False, order_redirection_number__isnull=False, hospital_id__in=hospitals_id.keys())
    order_redirection_numbers = {i.order_redirection_number: i.hospital_id for i in d_qs}
    order_redirection_numbers_internal_direction = {i.order_redirection_number: i.pk for i in d_qs}
    for order_redirection_number, v in order_redirection_numbers.items():
        iss = None
        direction = None
        hosp_data = json.loads(hospitals_id.get(v))
        rest_token = make_request_get_token(hosp_data, method="GET")
        default_part_url = hosp_data.get("url")
        result_check = rest_make_request_get(default_part_url, "ky/check", rest_token, hosp_data, {}, method="GET")
        if result_check.get("result") == "ok":
            pass
        else:
            rest_token = make_request_get_token(hosp_data, method="GET", get_new_token=True)
        result_order_data = rest_make_request_get_result(default_part_url, rest_token, hosp_data, order_redirection_number, only_new=only_new_order)
        print(result_order_data)
        result_order = result_order_data.get('data')
        if not result_order.get("results"):
            continue
        for i in result_order.get("results"):
            try:
                pdf_base_64 = i.get("binary")
                base64_bytes = pdf_base_64.encode('utf-8')
                data = ContentFile(base64.b64decode(base64_bytes))
            except:
                Log.log(
                    key=order_redirection_number,
                    type=190006,
                    body={"order_redirection_number": order_redirection_number, "reason": "base64 ошибка"},
                    user=None,
                )
                continue
            doctor_data = ["", "", ""]

            for article in i.get("articles"):
                stdout.write(f"Data of article: {article} ")
                tube_number = int(article.get("barcode"))
                internal_code = article.get("article")
                doctor = article.get("doctor")
                doctor_data = doctor.split(" ")
                date_time_confirm = article.get("date")
                tubes_sql = get_tube_by_number(tube_number)
                for t in tubes_sql:
                    if internal_code == t.research_internal_code:
                        iss = Issledovaniya.objects.filter(id=t.issledovaniye_id).first()
                        if IssledovaniyaFiles.objects.filter(issledovaniye=iss).exists():
                            iss_files = IssledovaniyaFiles.objects.filter(issledovaniye=iss)
                            for iss_file in iss_files:
                                iss_file.delete()
                        iss_file = IssledovaniyaFiles(issledovaniye=iss, uploaded_file=data)
                        file_name_internal_code = internal_code.replace(".", "_")
                        iss_file.uploaded_file.name = f"{tube_number}_{file_name_internal_code}.pdf"
                        iss_file.save()
                        iss.lab_comment = ""
                        iss.time_confirmation = datetime.datetime.strptime(date_time_confirm, "%Y.%m.%dT%H:%M:%S")
                        iss.time_save = current_time()
                        iss.doc_confirmation_string = doctor
                        iss.save()
                        direction = Napravleniya.objects.filter(pk=t.direction_number).first()
                        break
                # проверить статус - если 3 зафинишировать
                generator = HL7Generator(os.path.join(BASE_DIR, 'hl7_actions', 'templates'))
                time_confirm = iss.time_confirmation.strftime("%Y%m%d%H%M%S")
                obr_data = {
                    "order_number": order_redirection_number,
                    "tube_number": tube_number,
                    "code_nmu": iss.research.code,
                    "research_title": iss.research.title,
                    "research_internal_code": iss.research.internal_code,
                    "doctor_fio": iss.doc_confirmation_string,
                    "doctor_family": doctor_data[0] if doctor_data[0] else "",
                    "doctor_name": doctor_data[1] if doctor_data[1] else "",
                    "doctor_patronymic": doctor_data[2] if doctor_data[2] else "",
                    "direction_id": direction.pk,
                    "time_confirm": time_confirm,
                }
                data_patient = {
                    "patient_id": direction.client.number,
                    "patient_name": "",
                    "patient_birthday": "",
                    "patient_sec": "",
                }

                data = create_sample_data(data_patient, obr_data, pdf_base_64)
                hl7_message = generator.generate_hl7_message(data)
                ftp_connection = FTPConnection(hospitals_id_ftp_connect.get(v), hospital=hospitals_object.get(v))
                ftp_connection.connect()
                created_at = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

                filename = f"{direction.pk}_{order_redirection_number}_{iss.research.internal_code}_{created_at}.res"
                stdout.write(f"filename###: {filename}### ")
                ftp_connection.write_file_as_text(filename, hl7_message)
                Log.log(
                    key=order_redirection_number,
                    type=190003,
                    body={"order_redirection_number": order_redirection_number, "direction": direction.pk, "hl7_message": hl7_message},
                    user=None,
                )

        result_check = rest_make_request_get(default_part_url, "ky/check", rest_token, hosp_data, {}, method="GET")
        if result_check.get("result") == "ok":
            pass
        else:
            rest_token = make_request_get_token(hosp_data, method="GET", get_new_token=True)
        path = f"order/status/{order_redirection_number}"
        result = rest_make_request_get(default_part_url, path, rest_token, hosp_data, {}, method="GET")
        if result.get("status") == 3:
            direction.order_redirection_number_is_finished = True
            direction.save()


def process_rest_api_pull_result_star():
    stdout.write("Starting pull_orders process")
    while True:
        rest_api_pull_result()
        time.sleep(10)
