from dateutil.relativedelta import relativedelta
from rest_framework.response import Response

from api.directions.sql_func import get_confirm_direction_by_hospital
from appconf.manager import SettingManager
from hospitals.models import Hospitals
from laboratory.utils import current_time, TZ
from rest_framework.decorators import api_view


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

    return Response(hosp_structure_by_id)
