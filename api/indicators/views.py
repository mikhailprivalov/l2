import datetime
import json

from django.http import JsonResponse

from api.indicators.sql_func import indicator_sql
from directory.models import ParaclinicInputField, ParaclinicInputGroups
from external_system.models import CuratorCdaFields, CdaFields
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

    doctorprofile = request.user.doctorprofile
    print("doctorprofile", doctorprofile)
    indicators = CuratorCdaFields.objects.filter(curator=doctorprofile).values_list("indicator_id", flat=True)
    cda_pks = CdaFields.objects.filter(pk__in=indicators).values_list("pk", flat=True)
    print(cda_pks)
    groups_obj = ParaclinicInputGroups.objects.filter(cda_option__in=cda_pks)
    print("groups_obj", groups_obj)
    fields_obj = ParaclinicInputField.objects.filter(group__in=groups_obj).values_list("pk", flat=True)
    print("fields_obj", fields_obj)


    result_extra = indicator_sql(tuple(fields_obj), datetime_start, datetime_end)
    result = []
    prev_direction, prev_group = None, None
    step = 0
    current_result = {}
    for i in result_extra:
        if step == 0:
            current_result = {
                "direction": i.direction_id,
                "issledovaniye": i.issledovaniye_id,
                'hospital': i.hospital_title,
                'indicatorTitle': i.group_title,
            }

        if (prev_direction != i.direction_id or prev_group != i.group_title) and step != 0:
            result.append(current_result.copy())
            current_result = {
                "direction": i.direction_id,
                "issledovaniye": i.issledovaniye_id,
                'hospital': i.hospital_title,
                'indicatorTitle': i.group_title,
            }
        if "значение" in i.field_title.lower():
            current_result['hospitalValue'] = i.result_value
        if "балл" in i.field_title.lower():
            current_result['score'] = i.result_value
        step += 1
        prev_direction = i.direction_id
        prev_group = i.group_title
    result.append(current_result.copy())

    return JsonResponse({'rows': result})
