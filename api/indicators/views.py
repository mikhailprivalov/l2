import datetime
import json

from django.http import JsonResponse

from api.indicators.sql_func import indicator_sql
from laboratory.settings import EXTRA_MASTER_RESEARCH_PK, EXTRA_SLAVE_RESEARCH_PK
from utils.dates import normalize_dots_date


def search_indicator(request):
    request_data = json.loads(request.body)
    status = int(request_data.get("status", 2))
    hospital = int(request_data.get("hospital", -1))
    date_period = request_data["datePeriod"]
    time_start = f'{normalize_dots_date(date_period[0])} {request_data.get("time_start", "00:00")}:00'
    time_end = f'{normalize_dots_date(date_period[1])} {request_data.get("time_end", "23:59")}:59:999999'
    datetime_start = datetime.datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S')
    datetime_end = datetime.datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S:%f')

    user_hospital = request.user.doctorprofile.get_hospital_id() or -1

    if user_hospital != hospital and "Заполнение экстренных извещений" not in [str(x) for x in request.user.groups.all()]:
        hospital = -1

    if hospital == -1:
        return JsonResponse(
            {
                'result': [],
            }
        )

    result_extra = indicator_sql(EXTRA_MASTER_RESEARCH_PK, EXTRA_SLAVE_RESEARCH_PK, datetime_start, datetime_end, hospital, status)
    result = []
    for i in result_extra:
        result.append(
            {
                'hospital': i.hospital_title,
                'direction': i.direction_id,
                'indicatorTitle': i.indicator_title,
                'indicatorHospitalValue': i.indicator_hospital_value,
                'ballHospitalValue': i.ball_hospital_value,
                'curatorFieldValue': i.indicator_curator_value,
                'curatorFieldBallValue': i.ball_curator_value,
            }
        )
    return JsonResponse({'rows': result})
