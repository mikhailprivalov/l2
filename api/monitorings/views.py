import datetime
from typing import Optional
import json
from copy import deepcopy

import openpyxl
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required

from api.monitorings import structure_sheet
from laboratory.decorators import group_required
from django.http import JsonResponse, HttpResponse
from api.monitorings.sql_func import (
    monitoring_sql_by_all_hospital,
    dashboard_sql_by_day,
    sql_charts_sum_by_field_all_hospitals,
    dashboard_sql_by_day_filter_hosp,
    sql_charts_sum_by_field_filter_hospitals,
    sql_charts_sum_by_field_every_hospitals,
)
from directory.models import Researches
from utils.data_verification import data_parse
from laboratory.utils import strdatetime
from directions.models import DirectionParamsResult, Issledovaniya, Napravleniya, Dashboard, DashboardCharts
from hospitals.models import Hospitals


@login_required
@group_required("Просмотр мониторингов")
def search(request):
    request_data = json.loads(request.body)
    research_pk = request_data["research"]
    date = request_data["date"]

    prepare_date = date.split("-")

    research_obj = Researches.objects.get(pk=research_pk)
    type_period = research_obj.type_period
    start_date, end_date = None, None
    param_hour, param_day, param_month, param_quarter, param_halfyear, param_year = None, None, None, None, None, None
    param_hour = request_data["hour"]
    if param_hour == '-':
        param_hour = None

    if type_period == "PERIOD_WEEK":
        start_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        end_date = start_date + relativedelta(days=6)

    if type_period == "PERIOD_DAY" or type_period == "PERIOD_HOUR":
        param_day = prepare_date[2]
        param_month = prepare_date[1]

    if type_period == "PERIOD_MONTH":
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
    requirement_research_hosp = list(Hospitals.objects.values_list('pk', flat=True).filter(research=research_pk))
    requirement_group_hosp = list(
        Hospitals.objects.values_list('pk', flat=True).filter(hospitalsgroup__research__pk=research_pk, hospitalsgroup__type_hospital='REQUIREMENT_MONITORING_HOSP')
    )
    requirement_research_hosp.extend(requirement_group_hosp)
    requirement_research_hosp = list(set(requirement_research_hosp))
    delimiter = "@"
    for i in result_monitoring:
        if not title_group.get(i.group_title):
            title_group[i.group_title] = [i.field_title]
        else:
            if i.field_title not in title_group[i.group_title]:
                title_group[i.group_title].append(i.field_title)
        if i.field_type == 18 or i.field_type == 3:
            data_value = i.value_aggregate
        else:
            data_value = i.value_text

        if not rows_data.get(f"{i.hospital_id}{delimiter}{i.short_title}{delimiter}{i.napravleniye_id}{delimiter}{i.confirm}"):
            rows_data[f"{i.hospital_id}{delimiter}{i.short_title}{delimiter}{i.napravleniye_id}{delimiter}{i.confirm}"] = [[data_value]]
            step = 0
            current_index = 0
            if i.hospital_id in requirement_research_hosp:
                requirement_research_hosp.remove(i.hospital_id)

        if (i.group_title != old_group_title) and (step != 0):
            rows_data[f"{i.hospital_id}{delimiter}{i.short_title}{delimiter}{i.napravleniye_id}{delimiter}{i.confirm}"].append([data_value])
            current_index += 1
        elif step != 0:
            rows_data[f"{i.hospital_id}{delimiter}{i.short_title}{delimiter}{i.napravleniye_id}{delimiter}{i.confirm}"][current_index].append(data_value)

        old_group_title = i.group_title
        step += 1

    for k, v in title_group.items():
        titles_data.append({"groupTitle": k, "fields": v})

    total = []
    for k, v in rows_data.items():
        data = k.split(delimiter)
        rows.append({"hospTitle": data[1], "direction": data[2], "confirm": data[3], "values": v})
        if len(total) == 0:
            total = deepcopy(v)
        else:
            for external_index in range(len(v)):
                for internal_index in range(len(v[external_index])):
                    try:
                        int(total[external_index][internal_index])
                        is_digit = True
                    except ValueError:
                        is_digit = False
                    if not is_digit:
                        total[external_index][internal_index] = ""
                        continue
                    current_val = total[external_index][internal_index] + v[external_index][internal_index]
                    total[external_index][internal_index] = current_val

    empty_research_hosp = [Hospitals.objects.get(pk=i).short_title for i in requirement_research_hosp]
    result = {"titles": titles_data, "rows": rows, "empty_hospital": empty_research_hosp, "total": total}

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


@login_required
@group_required("Просмотр мониторингов")
def filexlsx(request):
    if request.method == "POST":
        data = json.loads(request.body)
        table_data = data.get("data")
        date = data.get("date")

        research_pk = data.get("research")
        monitoring = Researches.objects.get(pk=research_pk)
        symbols = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ", u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")  # Словарь для транслитерации
        tr = {ord(a): ord(b) for a, b in zip(*symbols)}  # Перевод словаря для транслита

        response = HttpResponse(content_type='application/ms-excel')
        wb = openpyxl.Workbook()
        wb.remove(wb.get_sheet_by_name('Sheet'))
        ws = wb.create_sheet(f'{monitoring.title}')
        ws = structure_sheet.monitoring_xlsx(ws, monitoring.title, table_data, date)

        response['Content-Disposition'] = str.translate(f"attachment; filename=\"{monitoring.title}, {date}.xlsx\"", tr)
        wb.save(response)
        return response


@login_required
@group_required("Просмотр мониторингов")
def get_dashboard(request):
    request_data = json.loads(request.body)
    dashboard_pk = request_data["dashboard"]

    # даты начала
    date = request_data["date"]
    prepare_date = date.split("-")
    param_day_start = prepare_date[2]
    param_month_start = prepare_date[1]
    param_year_start = prepare_date[0]

    # даты конец
    # date_end = request_data["date_end"]
    # prepare_date_end = date_end.split("-")
    prepare_date_end = [2021, 8, 1]
    param_day_end = prepare_date_end[2]
    param_month_end = prepare_date_end[1]
    param_year_end = prepare_date_end[0]

    is_one_date = prepare_date == prepare_date_end

    charts_objs = DashboardCharts.objects.filter(dashboard__pk=dashboard_pk, hide=False)

    default_charts = []
    charts_sum_by_field_all_hospitals = []
    charts_sum_by_field_some_hospitals = {}
    chrart_only_some_hospitals = {}
    chrart_every_hospitals = {}
    for c in charts_objs:
        if c.sum_by_field and c.hospitals_group is None:
            charts_sum_by_field_all_hospitals.append(c.pk)
        elif c.sum_by_field and c.hospitals_group:
            if c.group_by_type and c.group_by_type == "EVERY_HOSPITAL":
                chrart_every_hospitals[c.pk] = list(Hospitals.objects.values_list('pk', flat=True).filter(hospitalsgroup__pk=c.hospitals_group.pk))
            else:
                charts_sum_by_field_some_hospitals[c.pk] = list(Hospitals.objects.values_list('pk', flat=True).filter(hospitalsgroup__pk=c.hospitals_group.pk))
        elif not c.sum_by_field and c.hospitals_group:
            chrart_only_some_hospitals[c.pk] = list(Hospitals.objects.values_list('pk', flat=True).filter(hospitalsgroup__pk=c.hospitals_group.pk))
        else:
            default_charts.append(c.pk)

    result = []
    if default_charts:
        result_dashboard = dashboard_sql_by_day(default_charts, param_day_start, param_month_start, param_year_start, param_day_end, param_month_end, param_year_end)
        result = result_dashboard_func(result_dashboard, result, sum_by_field=False, default_charts=True, date=True)
    if chrart_only_some_hospitals:
        for chart_pk, need_hospitals in chrart_only_some_hospitals.items():
            result_dashboard = dashboard_sql_by_day_filter_hosp(
                [chart_pk], param_day_start, param_month_start, param_year_start, param_day_end, param_month_end, param_year_end, need_hospitals
            )
            result = result_dashboard_func(result_dashboard, result, sum_by_field=False, default_charts=True, date=True)
    if charts_sum_by_field_all_hospitals:
        result_dashboard = sql_charts_sum_by_field_all_hospitals(
            charts_sum_by_field_all_hospitals, param_day_start, param_month_start, param_year_start, param_day_end, param_month_end, param_year_end
        )
        result = result_dashboard_func(result_dashboard, result, sum_by_field=True, default_charts=False)
    if charts_sum_by_field_some_hospitals:
        for chart_pk, need_hospitals in charts_sum_by_field_some_hospitals.items():
            result_dashboard = sql_charts_sum_by_field_filter_hospitals(
                [chart_pk], param_day_start, param_month_start, param_year_start, param_day_end, param_month_end, param_year_end, need_hospitals
            )
            result = result_dashboard_func(result_dashboard, result, sum_by_field=True, default_charts=False)
    if chrart_every_hospitals:
        for chart_pk, need_hospitals in chrart_every_hospitals.items():
            result_dashboard = sql_charts_sum_by_field_every_hospitals(
                [chart_pk], param_day_start, param_month_start, param_year_start, param_day_end, param_month_end, param_year_end, need_hospitals
            )
            result = result_dashboard_func(result_dashboard, result, sum_by_field=False, default_charts=True)

    result = sorted(result, key=lambda k: k['chart_order'])
    print(result)

    return JsonResponse({'rows': result})


@login_required
@group_required("Просмотр мониторингов")
def dashboard_list(request):
    result = []
    dasboards = Dashboard.objects.filter(hide=False)
    for dasboard in dasboards:
        result.append({"label": dasboard.title, "id": dasboard.pk})

    return JsonResponse({"rows": result})


def result_dashboard_func(result_dashboard, result, sum_by_field=False, default_charts=True, date=False):
    previous_chart_title = None
    previous_hosp_short_title = None
    tmp_chart = {"title": "", "type": "", "pk": "", "chart_order": -1, "data": [{"title": "", "fields": [], "values": []}]}
    step = 0
    current_index = 0
    hosp_short_title = ""

    unique_dates = {i.date for i in result_dashboard}
    unique_dates = sorted(list(unique_dates))

    for i in result_dashboard:
        if sum_by_field:
            hosp_short_title = "Всего"
        elif default_charts:
            hosp_short_title = i.hosp_short_title
        if i.chart_title != previous_chart_title and step == 0:
            tmp_chart["title"] = i.chart_title
            tmp_chart["pk"] = i.chart_id
            tmp_chart["chart_order"] = i.chart_order
            tmp_chart["type"] = i.chart_type
            tmp_chart["data"] = [{"title": hosp_short_title, "fields": [i.title_for_field], "values": [i.value_aggregate]}]
            previous_chart_title = i.chart_title
            previous_hosp_short_title = hosp_short_title
        elif i.chart_title != previous_chart_title:
            tmp_chart["fields"] = tmp_chart["data"][current_index]["fields"]
            result.append(deepcopy(tmp_chart))
            tmp_chart["title"] = i.chart_title
            tmp_chart["pk"] = i.chart_id
            tmp_chart["type"] = i.chart_type
            tmp_chart["chart_order"] = i.chart_order
            tmp_chart["data"] = [{"title": hosp_short_title, "fields": [i.title_for_field], "values": [i.value_aggregate]}]
            previous_chart_title = i.chart_title
            previous_hosp_short_title = hosp_short_title
            current_index = 0
        elif hosp_short_title != previous_hosp_short_title:
            tmp_chart["data"].append({"title": hosp_short_title, "fields": [i.title_for_field], "values": [i.value_aggregate]})
            current_index += 1
            previous_hosp_short_title = hosp_short_title
        else:
            if i.title_for_field not in tmp_chart["data"][current_index]:
                tmp_chart["data"][current_index]["fields"].append(i.title_for_field)
            tmp_chart["data"][current_index]["values"].append(i.value_aggregate)
        step += 1

    tmp_chart["fields"] = tmp_chart["data"][current_index]["fields"]
    if step > 0:
        result.append(deepcopy(tmp_chart))

    return result
