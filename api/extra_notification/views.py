import datetime
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from api.extra_notification.sql_func import extra_notification_sql
from laboratory.settings import EXTRA_MASTER_RESEARCH_PK, EXTRA_SLAVE_RESEARCH_PK


@login_required
def search(request):
    request_data = json.loads(request.body)
    # status - 0 новые, 1-присвоенные номера от ЭпидЦентра, 2 - все
    status = int(request_data.get("status", 2))
    hospital = int(request_data.get("hospital", -1))
    date = request_data["date"]
    time_start = f'{date} {request_data.get("time_start", "00:00")}:00'
    time_end = f'{date} {request_data.get("time_end", "23:59")}:59:999999'
    datetime_start = datetime.datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S')
    datetime_end = datetime.datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S:%f')

    if not request.user.doctorprofile.all_hospitals_users_control:
        hospital = request.user.doctorprofile.get_hospital_id() or -1

    if hospital == -1:
        return JsonResponse({})

    result_extra = extra_notification_sql(EXTRA_MASTER_RESEARCH_PK, EXTRA_SLAVE_RESEARCH_PK, datetime_start, datetime_end, hospital, status)
    result = []
    for i in result_extra:
        title = i.title
        if i.short_title:
            title = i.short_title
        patient = f'{i.pfam} {i.pname} {i.twoname}'
        result.append({'hospital': title, 'main_direction': i.dir_id, 'slave_dir': i.r_dir_id, 'patient': patient, 'born': i.birthday, 'value': i.num_value, 'iss_pk': i.r_iss_id})

    return JsonResponse({'result': result})
