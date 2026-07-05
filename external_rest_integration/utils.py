from django.core.files.base import ContentFile
from django.utils import timezone
from directions.sql_func import get_tube_by_number
from external_rest_integration.integration import (
    make_request_get_token,
    rest_make_request_get,
    rest_make_request_get_result,
    interactive_log,
)
from ftp_orders.main import FTPConnection
from hl7_actions.hl7_generator import HL7Generator, create_sample_data
from hospitals.models import Hospitals
from directions.models import Napravleniya, IssledovaniyaFiles, Issledovaniya
import json
import base64

from laboratory.utils import current_time
from slog.models import Log
import os
from laboratory.settings import BASE_DIR, REST_API_PULL_RESULT_DAYS_LIMIT
import datetime
from sys import stdout
import time


def _get_hospitals_context():
    hospitals = Hospitals.get_hospitals_pull_results_from_external_system()
    return {
        'hospitals_id': {i.pk: i.auth_data_for_rest for i in hospitals},
        'hospitals_id_ftp_connect': {i.pk: i.result_push_by_numbers_for_rest for i in hospitals},
        'hospitals_object': {i.pk: i for i in hospitals},
    }


def _pull_and_process_order(order_redirection_number, hospital_id, hospitals_id, hospitals_id_ftp_connect, hospitals_object, only_new_order):
    iss = None
    direction = None
    interactive_log(f"--- Заказ {order_redirection_number}, hospital_id={hospital_id}, only_new={only_new_order} ---")
    auth_data = hospitals_id.get(hospital_id)
    if not auth_data:
        interactive_log(f"Заключение по заказу {order_redirection_number}: нет auth_data для hospital_id={hospital_id}")
        return
    hosp_data = json.loads(auth_data)
    interactive_log(
        f"Настройки: url={hosp_data.get('url')}, login={hosp_data.get('login')}, "
        f"password={hosp_data.get('password')}, auth_login={hosp_data.get('auth_login')}, "
        f"auth_password={hosp_data.get('auth_password')}"
    )
    rest_token = make_request_get_token(hosp_data, method="GET")
    default_part_url = hosp_data.get("url")
    if not default_part_url:
        interactive_log(f"Заключение по заказу {order_redirection_number}: не задан url")
        return
    interactive_log(f"Проверка токена: GET {default_part_url}/ky/check")
    result_check = rest_make_request_get(default_part_url, "ky/check", rest_token, hosp_data, {}, method="GET")
    if result_check.get("result") == "ok":
        interactive_log("Токен действителен")
    else:
        interactive_log("Токен недействителен, запрос нового ключа")
        rest_token = make_request_get_token(hosp_data, method="GET", get_new_token=True)
    interactive_log(f"Запрос результата: POST {default_part_url}/result, number={order_redirection_number}")
    result_order_data = rest_make_request_get_result(default_part_url, rest_token, hosp_data, order_redirection_number, only_new=only_new_order)
    if not result_order_data:
        interactive_log(f"Заключение по заказу {order_redirection_number}: пустой ответ API")
        return
    result_order = result_order_data.get('data')
    if not result_order or not result_order.get("results"):
        interactive_log(f"Заключение по заказу {order_redirection_number}: результатов нет")
        return
    processed_articles = 0
    for i in result_order.get("results"):
        stdout.write(f"results: {i} ")
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

        for article in i.get("articles") or []:
            stdout.write(f"Data of article: {article} ")
            processed_articles += 1
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
            try:
                ftp_connection = FTPConnection(hospitals_id_ftp_connect.get(hospital_id), hospital=hospitals_object.get(hospital_id))
                if not ftp_connection:
                    continue
                ftp_connection.connect()
            except:
                continue
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

    interactive_log(f"Проверка статуса заказа: GET {default_part_url}/order/status/{order_redirection_number}")
    result_check = rest_make_request_get(default_part_url, "ky/check", rest_token, hosp_data, {}, method="GET")
    if result_check.get("result") == "ok":
        pass
    else:
        rest_token = make_request_get_token(hosp_data, method="GET", get_new_token=True)
    path = f"order/status/{order_redirection_number}"
    result = rest_make_request_get(default_part_url, path, rest_token, hosp_data, {}, method="GET")
    finished = result.get("status") == 3 and direction
    if finished:
        direction.order_redirection_number_is_finished = True
        direction.save()
    interactive_log(f"Заключение по заказу {order_redirection_number}: обработано позиций={processed_articles}, " f"статус={result.get('status')}, завершён={'да' if finished else 'нет'}")


def _get_order_redirection_numbers(ctx, direction_pks=None, days_limit=None):
    qs = Napravleniya.objects.filter(
        order_redirection_number__isnull=False,
        hospital_id__in=ctx['hospitals_id'].keys(),
    )
    if direction_pks is not None:
        qs = qs.filter(pk__in=direction_pks)
    else:
        qs = qs.filter(order_redirection_number_is_finished=False)
    if days_limit is not None:
        date_from = timezone.now() - datetime.timedelta(days=days_limit)
        interactive_log(f"Фильтр направлений: созданы не ранее {date_from.strftime('%Y-%m-%d %H:%M:%S')} ({days_limit} дн.)")
        qs = qs.filter(data_sozdaniya__gte=date_from)
    elif direction_pks is not None:
        interactive_log("Ручной запрос: без ограничения по дате создания направления")
    return {i.order_redirection_number: i.hospital_id for i in qs}


def _run_pull_for_orders(ctx, order_redirection_numbers, only_new_order):
    for order_redirection_number, hospital_id in order_redirection_numbers.items():
        _pull_and_process_order(
            order_redirection_number,
            hospital_id,
            ctx['hospitals_id'],
            ctx['hospitals_id_ftp_connect'],
            ctx['hospitals_object'],
            only_new_order,
        )


def rest_api_pull_result(only_new_order=True):
    ctx = _get_hospitals_context()
    stdout.write(f"Iterating over {len(ctx['hospitals_id_ftp_connect'])} servers\n")
    interactive_log(f"Старт опроса результатов, only_new={only_new_order}, серверов={len(ctx['hospitals_id_ftp_connect'])}")

    order_redirection_numbers = _get_order_redirection_numbers(ctx, days_limit=REST_API_PULL_RESULT_DAYS_LIMIT)
    interactive_log(f"Заказов к обработке: {len(order_redirection_numbers)}")
    _run_pull_for_orders(ctx, order_redirection_numbers, only_new_order)
    interactive_log(f"Заключение: обработано заказов {len(order_redirection_numbers)}")


def rest_api_pull_result_for_directions(direction_pks, only_new_order=False):
    ctx = _get_hospitals_context()
    interactive_log(f"Ручной запрос результатов, only_new={only_new_order}, направлений={len(direction_pks)}")

    order_redirection_numbers = _get_order_redirection_numbers(ctx, direction_pks=direction_pks, days_limit=None)
    interactive_log(f"Заказов к обработке: {len(order_redirection_numbers)}")
    _run_pull_for_orders(ctx, order_redirection_numbers, only_new_order)
    interactive_log(f"Заключение: обработано заказов {len(order_redirection_numbers)}")


def process_rest_api_pull_result_start():
    stdout.write("Starting pull_orders process")
    while True:
        rest_api_pull_result()
        time.sleep(10)
