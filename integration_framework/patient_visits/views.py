import codecs

from rest_framework.response import Response
from rest_framework.decorators import api_view
from api.models import Application
from directions.models import Napravleniya, Issledovaniya
import simplejson as json
from results.sql_func import get_paraclinic_results_by_direction
from utils.dates import normalize_date, normalize_dots_date
from xml_generate.views import gen_result_cda_files


@api_view(['POST'])
def data_by_direction(request):
    token = request.META.get("HTTP_AUTHORIZATION")
    token = token.replace("Bearer ", "")
    if not token:
        return Response({"message": "token is empty"})
    token_is_not_valid = False
    try:
        app = Application.objects.filter(active=True, key=token).first()
        if not app:
            token_is_not_valid = True
    except:
        token_is_not_valid = True

    if token_is_not_valid:
        return Response({"message": "token is not valid"})

    data = json.loads(request.body)
    direction_id = data.get("directionId")
    direction = Napravleniya.objects.filter(pk=direction_id).first()
    result_l2 = get_direction_data_by_cda_group(direction.pk)
    result_tempalte = gen_result_cda_files("protocol/proto.js", result_l2)
    json_data = json.loads(result_tempalte)
    final_proto = {k: string_to_unicode_escape(v) for k, v in json_data.items()}
    iss = Issledovaniya.objects.filter(napravleniye=direction).first()
    additional_data = {}
    if iss.doc_confirmation.additional_info:
        if "{" in iss.doc_confirmation.additional_info and "}" in iss.doc_confirmation.additional_info:
            try:
                additional_data = json.loads(iss.doc_confirmation.additional_info)
                if not additional_data or not isinstance(additional_data, dict):
                    additional_data = {}
            except Exception:
                additional_data = None
    if (
        not additional_data
        or not iss.doc_confirmation.rmis_login
        or not iss.doc_confirmation.rmis_password
    ):
        iss.napravleniye.amd_message = "Нет связи с внешним сервисом"
        return Response({"result": None})

    date_inspection = iss.time_confirmation.strftime("%d.%m.%Y")
    time_inspection = iss.time_confirmation.strftime("%H:%M")

    result = {
        "patient": {
            "family": direction.client.individual.family,
            "name": direction.client.individual.name,
            "patronymic": direction.client.individual.patronymic,
            "birthday": direction.client.individual.bd(),
        },
        "service": {
            "directionId": direction.pk,
            "dateInspection": result_l2.get("date_inspection") if result_l2.get("date_inspection") else date_inspection,
            "timeInspection": result_l2.get("time_inspection") if result_l2.get("time_inspection") else time_inspection,
            "dateLatin": normalize_dots_date(result_l2.get("date_inspection")) if result_l2.get("date_inspection") else normalize_dots_date(date_inspection),
            "protocol": final_proto,
            "raw_data": result_tempalte,
            "mainDiagnos": result_l2.get("main_diagnos"),
            "general_condition": result_l2.get("general_condition") if result_l2.get("general_condition") else "Средней тяжести",
            "character_illness": result_l2.get("character_illness") if result_l2.get("character_illness") else "острое",
            "code": iss.research.code,
        },
        "doctor": {"additionalInfo": additional_data, "login": iss.doc_confirmation.rmis_login, "password": iss.doc_confirmation.rmis_password},
    }
    return Response(result)


@api_view(['POST'])
def result_rmis_sent_direction(request):
    token = request.META.get("HTTP_AUTHORIZATION")
    token = token.replace("Bearer ", "")
    if not token:
        return Response({"message": "token is empty"})
    token_is_not_valid = False
    try:
        app = Application.objects.filter(active=True, key=token).first()
        if not app:
            token_is_not_valid = True
    except:
        token_is_not_valid = True

    if token_is_not_valid:
        return Response({"message": "token is not valid"})

    data = json.loads(request.body)
    direction_id = data.get("directionId")
    rmis_number = data.get("rmis_number")
    message = data.get("message")
    success = data.get("success")
    direction = Napravleniya.objects.filter(pk=direction_id).first()
    if message and not success:
        direction.amd_message = message
        direction.result_rmis_send = False
        direction.save()
    if success:
        direction.rmis_case_number = rmis_number
        direction.result_rmis_send = True
        direction.amd_message = ""
        direction.save()

    return Response({"ok": True})


def get_direction_data_by_cda_group(direction_pk):
    result = get_paraclinic_results_by_direction(direction_pk)
    data = {}
    date_inspection, time_inspection, main_diagnos, general_condition = None, None, None, None
    for i in result:
        if i.cda_field_code and i.value:
            if i.cda_field_code == 7005:
                date_inspection = normalize_date(i.value)
            if i.cda_field_code == 7004:
                time_inspection = i.value
            if i.cda_field_code == 809:
                main_diagnos = i.value
            if i.cda_field_code == 7003:
                general_condition = i.value
            if not data.get(i.cda_field_code):
                data[i.cda_field_code] = [{i.title: i.value}]
            else:
                data[i.cda_field_code].append({i.title: i.value})
            continue
        if i.cda_group_code and i.value:
            if not data.get(i.cda_group_code):
                data[i.cda_group_code] = [{i.title: i.value}]
            else:
                data[i.cda_group_code].append({i.title: i.value})
    temp_result = {}
    for k, v in data.items():
        s = ""
        for j in v:
            for key, val in j.items():
                if key:
                    s = f"{s}{key}: {val};"
                else:
                    s = f"{s}{val};"
        temp_result[k] = s
    temp_result = {str(k): v for k, v in temp_result.items()}
    return {"data": temp_result, "date_inspection": date_inspection, "time_inspection": time_inspection, "main_diagnos": main_diagnos, "general_condition": general_condition}


def string_to_unicode_escape(text):
    symbols_data = ''.join(f'\\u{ord(char):04x}' for char in text)
    return symbols_data
