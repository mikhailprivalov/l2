import datetime
from typing import Optional
from laboratory.utils import strdatetime
from directions.models import DirectionParamsResult, Issledovaniya, Napravleniya
from hospitals.models import Hospitals
import json

from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from api.monitorings.sql_func import monitoring_sql_by_all_hospital
from directory.models import Researches
from utils.data_verification import data_parse


@login_required
def search(request):
    request_data = json.loads(request.body)
    research_pk = int(request_data.get("research_pk", 2))
    date = request_data["date"]

    prepare_date = date.split("-")

    research_obj = Researches.objects.get(pk=research_pk)
    type_period = research_obj.type_period
    start_date, end_date = None, None
    param_hour, param_day, param_month, param_quarter, param_halfyear, param_year = None, None, None, None, None, None
    param_hour = request_data["hour"]

    if type_period == "PERIOD_WEEK":
        start_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        end_date = start_date + relativedelta(days=+6)

    if type_period == "PERIOD_DAY" or type_period == "PERIOD_HOUR":
        param_day = prepare_date[2]
        param_month = prepare_date[1]

    param_year = prepare_date[0]
    result_monitoring = monitoring_sql_by_all_hospital(
        monitoring_research=research_pk,
        type_period=type_period,
        period_param_hour=param_hour,
        period_param_day=param_day,
        period_param_month=param_month,
        period_param_quarter=param_quarter,
        period_param_halfyear=param_halfyear,
        period_param_year=param_year,
        period_param_week_date_start=start_date,
        period_param_week_date_end=end_date,
    )
    titles_data = []
    rows = []
    title_group = {}
    rows_data = {}
    step = 0
    old_group_title = None
    current_index = 0
    for i in result_monitoring:
        if not title_group.get(i.group_title):
            title_group[i.group_title] = [i.field_title]
        else:
            title_group[i.group_title].append(i.field_title)

        if not rows_data.get(f"{i.hospital_id}-{i.short_title}-{i.napravleniye_id}-{i.confirm}"):
            rows_data[f"{i.hospital_id}-{i.short_title}-{i.napravleniye_id}-{i.confirm}"] = [[i.value_aggregate]]
            current_index = 0

        if (i.group_title != old_group_title) and (step != 0):
            rows_data[f"{i.hospital_id}-{i.short_title}-{i.napravleniye_id}-{i.confirm}"].append([i.value_aggregate])
            current_index += 1
        elif step != 0:
            rows_data[f"{i.hospital_id}-{i.short_title}-{i.napravleniye_id}-{i.confirm}"][current_index].append(i.value_aggregate)

        old_group_title = i.group_title
        step += 1

    for k, v in title_group.items():
        titles_data.append({"groupTitle": k, "fields": v})

    for k, v in rows_data.items():
        data = k.split('-')
        rows.append({"hospTitle": data[1], "direction": data[2], "confirm": data[3], "values": v})

    result = {"titles": titles_data, "rows": rows}
    return JsonResponse({'rows': result})


@login_required
def history(request):
    data = data_parse(request.body, {'offset': int, 'pk': int, 'filterResearches': list}, {'pk': None, 'offset': None, 'filterResearches': None})
    offset: Optional[int] = data[0]
    pk: Optional[int] = data[1]
    filter_researches: Optional[list] = data[2]
    limit = 40
    end = offset + limit if not pk else None
    hospital: Hospitals = request.user.doctorprofile.get_hospital()
    directions = Napravleniya.objects.filter(issledovaniya__research__is_monitoring=True, hospital=hospital).order_by('-data_sozdaniya')
    if pk:
        directions = directions.filter(pk=pk)
    if filter_researches and len(filter_researches) > 0:
        directions = directions.filter(issledovaniya__research_id__in=filter_researches)
    rows = []
    next_offset = None

    directions_chunk = directions[offset:end] if not pk else directions

    d: Napravleniya
    for d in directions_chunk:
        direction_params = DirectionParamsResult.objects.filter(napravleniye=d).order_by('order')

        i: Issledovaniya = d.issledovaniya_set.all()[0]

        rows.append(
            {
                "pk": d.pk,
                "title": i.research.get_title(),
                "lastActionAt": strdatetime(i.time_confirmation or i.time_save or d.data_sozdaniya),
                "isSaved": d.has_save(),
                "isConfirmed": d.is_all_confirm(),
                "author": str(d.doc_who_create or d.doc or ""),
                "params": [
                    {
                        "title": " → ".join([x for x in [x.field.group.title, x.field.title] if x]),
                        "value": x.string_value_normalized,
                    }
                    for x in direction_params
                ],
            }
        )

    total_count = None

    if end:
        total_count = directions.count()
        if total_count > end:
            next_offset = end

    return JsonResponse({"nextOffset": next_offset, "rows": rows, "totalCount": total_count})
