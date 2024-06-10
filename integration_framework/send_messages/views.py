from dateutil.relativedelta import relativedelta
from rest_framework.response import Response

from api.directions.sql_func import get_confirm_direction_by_hospital
from appconf.manager import SettingManager
from directions.models import Napravleniya
from hospitals.models import Hospitals
from integration_framework.common_func import directions_pdf_result
from laboratory.utils import current_time, TZ
from rest_framework.decorators import api_view
import simplejson as json
from utils.response import status_response
from django.core.files.base import ContentFile
import base64
from slog.models import Log


@api_view()
def get_directions_for_mail_send(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    days_ago = SettingManager.get("days_before_hosp", default="30", default_type="i")
    d_end_time = current_time()
    d_start_time = d_end_time + relativedelta(days=-days_ago)

    d_end = d_end_time.strftime("%Y-%m-%d %H:%M:%S")
    d_start = d_start_time.strftime("%Y-%m-%d %H:%M:%S")

    hospital_send_mail = Hospitals.hospitals_need_send_result_mail()
    hospitals_ids = tuple([i.get("id") for i in hospital_send_mail])
    result = get_confirm_direction_by_hospital(hospitals_ids, d_start, d_end, email_with_results_sent_is_false="1")
    hosp_structure_by_id = {k.get("id"): {"send_after_time_min": k.get("send_after_time_min"), "mail": k.get("mail"), "dirs": []} for k in hospital_send_mail}

    for r in result:
        last_confirm_time = r.last_confirmed_at.astimezone(TZ)
        after_time_approve_send = last_confirm_time + relativedelta(minutes=hosp_structure_by_id[r.hospital]["send_after_time_min"])
        if after_time_approve_send < d_end_time:
            hosp_structure_by_id[r.hospital]["dirs"].append(r.direction)

    result = [{"hospitalId": k, "mail": v["mail"], "dirs": v["dirs"]} for k, v in hosp_structure_by_id.items() if len(v["dirs"]) > 0]

    return Response(result)


@api_view()
def get_pdf_for_mail_send(request):
    body = json.loads(request.body)
    hospital_id = body.get("hospitalId")
    directions_ids = body.get("directionsIds")

    for direction_id in directions_ids:
        n = Napravleniya.objects.get(pk=direction_id)
        if n.hospital != hospital_id:
            return Response(f"Направление №{n.pk} не принадлежит организации {hospital_id}")
        if not n.total_confirmed:
            return Response(f"Направление №{n.pk} не подтверждено")

    directions_ids = list(set(directions_ids))
    directions_ids.sort(key=lambda x: Napravleniya.objects.get(pk=x).last_confirmed_at, reverse=True)

    if not directions_ids:
        return status_response(False, "Empty directions ids")

    pdf = directions_pdf_result(directions_ids)
    filename = f"results_{hospital_id}_{directions_ids[0]}--_.pdf"
    file = ContentFile(base64.b64decode(pdf), name=filename)
    hospital = Hospitals.objects.get(pk=hospital_id)
    for direction_id in directions_ids:
        n = Napravleniya.objects.get(pk=direction_id)
        n.email_with_results_sent = True
        n.save(update_fields=["email_with_results_sent"])
        Log.log(
            direction_id,
            140000,
            request.user.doctorprofile,
            {
                "hospital": hospital.title,
                "hospital_id": hospital_id,
                "directions_ids": directions_ids,
            },
        )
    result = {"file": file, "filename": filename}

    return Response(result)
