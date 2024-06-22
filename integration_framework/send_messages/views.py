from dateutil.relativedelta import relativedelta
from rest_framework.response import Response

from api.directions.sql_func import get_confirm_direction_by_hospital, get_lab_podr, get_direction_data_by_directions_id, get_total_confirm_direction
from appconf.manager import SettingManager
from directions.models import Napravleniya
from hospitals.models import Hospitals
from integration_framework.common_func import directions_pdf_result
from laboratory.utils import current_time, TZ
from rest_framework.decorators import api_view
import simplejson as json

from utils.response import status_response


@api_view()
def get_directions_for_org_mail_send(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    days_ago = SettingManager.get("days_before_hosp", default="30", default_type="i")
    d_end_time = current_time()
    d_start_time = d_end_time + relativedelta(days=-days_ago)

    d_end = d_end_time.strftime("%Y-%m-%d %H:%M:%S")
    d_start = d_start_time.strftime("%Y-%m-%d %H:%M:%S")

    hospital_send_mail = Hospitals.hospitals_need_send_result_mail()
    hospitals_ids = tuple([i.get("id") for i in hospital_send_mail])
    if hospitals_ids:
        result = get_confirm_direction_by_hospital(hospitals_ids, d_start, d_end, email_with_results_sent_is_false="1")
    else:
        return Response([])
    hosp_structure_by_id = {k.get("id"): {"send_after_time_min": k.get("send_after_time_min"), "mail": k.get("mail"), "dirs": []} for k in hospital_send_mail}

    for r in result:
        last_confirm_time = r.last_confirmed_at.astimezone(TZ)
        after_time_approve_send = last_confirm_time + relativedelta(minutes=hosp_structure_by_id[r.hospital]["send_after_time_min"])
        if after_time_approve_send < d_end_time:
            hosp_structure_by_id[r.hospital]["dirs"].append(r.direction)

    result = [{"hospitalId": k, "mail": v["mail"], "dirs": v["dirs"]} for k, v in hosp_structure_by_id.items() if len(v["dirs"]) > 0]

    return Response(result)


@api_view(['POST'])
def get_directions_for_person_mail_send(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})
    request_data = json.loads(request.body)

    days_ago = SettingManager.get("days_before_hosp", default="30", default_type="i")
    d_end_time = current_time()
    d_start_time = d_end_time + relativedelta(days=-days_ago)

    d_end = d_end_time.strftime("%Y-%m-%d %H:%M:%S")
    d_start = d_start_time.strftime("%Y-%m-%d %H:%M:%S")

    is_lab = request_data.get('is_lab', False) == 'is_lab'
    is_paraclinic = request_data.get('is_paraclinic', False) == 'is_paraclinic'
    is_doc_refferal = request_data.get('is_doc_refferal', False) == 'is_doc_refferal'

    if not is_lab and not is_doc_refferal and not is_paraclinic:
        return Response({"results": []})

    if is_lab:
        lab_podr = get_lab_podr()
        lab_podr = [i[0] for i in lab_podr]
    else:
        lab_podr = [-1]

    confirm_direction = get_total_confirm_direction(d_start, d_end, lab_podr, is_lab, is_paraclinic, is_doc_refferal)
    if not confirm_direction:
        return Response({"results": []})
    result_direction = [i for i in confirm_direction.napravleniye_id]
    direction_data = get_direction_data_by_directions_id(tuple(result_direction))
    direction_structure_by_client = {}

    for row in direction_data:
        if row.email_with_results_sent_to_person or not row.patient_email:
            continue

        if not direction_structure_by_client.get(row.client_id):
            direction_structure_by_client[row.client_id] = {"mail": row.patien_email, "fio": f"{row.family} {row.name} {row.patronymic}", "directions": [row.direction_id]}
        else:
            direction_structure_by_client[row.client_id]["directions"].append(row.direction_id)

    result = [{"clientId": k, "mail": v["mail"], "dirs": v["directions"]} for k, v in direction_structure_by_client]

    return Response(result)


@api_view(['POST'])
def get_pdf_for_mail_send(request):
    body = json.loads(request.body)
    hospital_id = body.get("hospitalId")
    directions_ids = body.get("directionsIds")
    is_person_send = body.get("isPersonSend", "0") == "1"
    client_id = body.get("clientId")

    for direction_id in directions_ids:
        n = Napravleniya.objects.get(pk=direction_id)
        if not is_person_send and (n.hospital_id != hospital_id):
            return Response(f"Направление №{n.pk} не принадлежит организации {hospital_id}")
        if is_person_send and n.client_id != client_id:
            return Response(f"Направление №{n.pk} не принадлежит карте пациента с id {client_id}")
        if not n.total_confirmed:
            return Response(f"Направление №{n.pk} не подтверждено")

    directions_ids = list(set(directions_ids))
    directions_ids.sort(key=lambda x: Napravleniya.objects.get(pk=x).last_confirmed_at, reverse=True)

    if not directions_ids:
        return status_response(False, "Empty directions ids")

    pdf_b64 = directions_pdf_result(directions_ids)
    filename = f"results_{hospital_id}_{directions_ids[0]}--_.pdf"
    for direction_id in directions_ids:
        n = Napravleniya.objects.get(pk=direction_id)
        n.email_with_results_sent = True
        n.save(update_fields=["email_with_results_sent"])
    result = {"b64File": pdf_b64, "filename": filename}

    return Response(result)
