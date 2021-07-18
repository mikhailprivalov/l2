import datetime
import json
from copy import deepcopy

from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from api.monitorings.sql_func import monitoring_sql_by_all_hospital
from directory.models import Researches
from hospitals.models import Hospitals


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
    requirement_research_hosp = list(Hospitals.objects.values_list('pk', flat=True).filter(research=771))

    for i in result_monitoring:
        if not title_group.get(i.group_title):
            title_group[i.group_title] = [i.field_title]
        else:
            if i.field_title not in title_group[i.group_title]:
                title_group[i.group_title].append(i.field_title)

        if not rows_data.get(f"{i.hospital_id}-{i.short_title}-{i.napravleniye_id}-{i.confirm}"):
            rows_data[f"{i.hospital_id}-{i.short_title}-{i.napravleniye_id}-{i.confirm}"] = [[i.value_aggregate]]
            step = 0
            current_index = 0
            if i.hospital_id in requirement_research_hosp:
                requirement_research_hosp.remove(i.hospital_id)

        if (i.group_title != old_group_title) and (step != 0):
            rows_data[f"{i.hospital_id}-{i.short_title}-{i.napravleniye_id}-{i.confirm}"].append([i.value_aggregate])
            current_index += 1
        elif step != 0:
            rows_data[f"{i.hospital_id}-{i.short_title}-{i.napravleniye_id}-{i.confirm}"][current_index].append(i.value_aggregate)

        old_group_title = i.group_title
        step += 1

    for k, v in title_group.items():
        titles_data.append({"groupTitle": k, "fields": v})

    total = []
    for k, v in rows_data.items():
        data = k.split('-')
        rows.append({"hospTitle": data[1], "direction": data[2], "confirm": data[3], "values": v})
        if len(total) == 0:
            total = deepcopy(v)
        else:
            for external_index in range(len(v)):
                for internal_index in range(len(v[external_index])):
                    current_val = total[external_index][internal_index] + v[external_index][internal_index]
                    total[external_index][internal_index] = current_val

    empty_research_hosp = [Hospitals.objects.get(pk=i).short_title for i in requirement_research_hosp]
    result = {"titles": titles_data, "rows": rows, "empty_hospital": empty_research_hosp, "total": total}

    return JsonResponse({'rows': result})
