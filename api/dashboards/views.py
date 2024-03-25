import calendar
import json
import logging

from dateutil.relativedelta import relativedelta
from django.http import JsonResponse

from dashboards.models import Dashboard
from dashboards.views import exec_query, get_dashboard
from integration_framework.employees.sql_func import get_cash_resister_by_depatment_period
from laboratory.settings import DASH_REPORT_LIMIT_DURATION_DAYS
from laboratory.utils import current_time, str_date
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)


def dashboard_list(request):
    result = get_dashboard()
    return JsonResponse({'rows': result})


def dashboard_charts(request):
    request_data = json.loads(request.body)
    dashboard_pk = request_data.get("dashboard", -1)

    end_period_type = request_data.get("end_type", None)
    end_period_duration = request_data.get("end_duration", 0)

    start_period_type = request_data.get("start_type", None)
    start_period_duration = request_data.get("start_duration", 0)

    date_end = request_data.get("date_end", None)
    date_start = request_data.get("date_start", None)

    date_period_start = request_data.get("dateStart", None)
    date_period_end = request_data.get("dateEnd", None)

    if date_end and date_start:
        try:
            date_end = str_date(date_end)
        except Exception as e:
            logger.exception(e)
            date_end = None
        try:
            date_start = str_date(date_start, indicator="min")
        except Exception as e:
            logger.exception(e)
            date_start = None

    elif start_period_type and start_period_duration:
        start_periods_data = define_period(start_period_type, start_period_duration)
        date_end = current_time()

        if end_period_type and end_period_duration:
            end_periods_data = define_period(end_period_type, end_period_duration)
            date_end = date_end + relativedelta(years=end_periods_data["years"], months=end_periods_data["months"], weeks=end_periods_data["weeks"], days=end_periods_data["days"])

        date_start = date_end + relativedelta(years=start_periods_data["years"], months=start_periods_data["months"], weeks=start_periods_data["weeks"], days=start_periods_data["days"])

    if date_end and date_start:
        d = date_end - date_start
        if d.days > DASH_REPORT_LIMIT_DURATION_DAYS["max_delta_days"] or d.days < 0:
            date_end = None
            date_start = None
    try:
        result = exec_query(dashboard_pk, {"date_start": date_period_start or date_start, "date_end": date_period_end or date_end})
    except Exception as e:
        logger.exception(e)
        return JsonResponse({"ok": False})

    dash = Dashboard.objects.get(pk=dashboard_pk)
    return JsonResponse(
        {'rows': result["result"], "ok": True, "intervalReloadSeconds": dash.interval_reload_seconds, "showDatesParam": result["show_dates_param"], "datesParam": result["dates_param"]}
    )


@login_required
def cash_register(request):
    body = json.loads(request.body)
    mode = body.get("mode")
    date_start = body.get("dateStart")

    date_start_year = date_start[:4]
    date_start_month = date_start[4:6]
    date_start_day = "01"
    _, num_days = calendar.monthrange(int(date_start_year), int(date_start_month))
    date_start_query = f"{date_start_year}{date_start_month}{date_start_day}"
    date_end_query = f"{date_start_year}{date_start_month}{num_days}"

    date_per_month = []
    for i in range(int(date_start_day), num_days + 1):
        if i < 10:
            i = f"0{i}"
        date_per_month.append(i)

    columns = [
        {
            "key": f"{i}.{date_start_month}.{date_start_year}",
            "field": f"{i}.{date_start_month}.{date_start_year}",
            "title": f"{i}.{date_start_month}",
            "align": "right",
            "width": 100,
        }
        for i in date_per_month
    ]

    columns.insert(0, {"key": "office", "field": "office", "title": "Офисы", "align": "left", "width": 200, "fixed": 'left'})
    table_data = []

    if mode == "department":
        query_result = get_cash_resister_by_depatment_period(date_start_query, date_end_query)
        data = {}
        for qr in query_result:
            if not data.get(qr.department_id):
                data[qr.department_id] = {"office": qr.depart_name, **{f"{i}.{date_start_month}.{date_start_year}": "" for i in date_per_month}, "officeRow": True}
                data[f"Наличные {qr.department_id}"] = {"office": "Наличные", **{f"{i}.{date_start_month}.{date_start_year}": "" for i in date_per_month}, "only1stCol": True}
                data[f"Терминал {qr.department_id}"] = {"office": "Терминал", **{f"{i}.{date_start_month}.{date_start_year}": "" for i in date_per_month}, "only1stCol": True}
                data[f"Возврат нал {qr.department_id}"] = {"office": "Возврат нал ", **{f"{i}.{date_start_month}.{date_start_year}": "" for i in date_per_month}}
                data[f"Возврат терм {qr.department_id}"] = {"office": "Возврат терм ", **{f"{i}.{date_start_month}.{date_start_year}": "" for i in date_per_month}}
                data[f"Итого {qr.department_id}"] = {"office": "Итого", **{f"{i}.{date_start_month}.{date_start_year}": "" for i in date_per_month}, "totalRow": True}
            data[f"Наличные {qr.department_id}"][qr.char_day] = f"{qr.received_cash:,.2f}"
            data[f"Терминал {qr.department_id}"][qr.char_day] = f"{qr.received_terminal:,.2f}"
            data[f"Возврат нал {qr.department_id}"][qr.char_day] = f"{qr.return_cash:,.2f}"
            data[f"Возврат терм {qr.department_id}"][qr.char_day] = f"{qr.return_terminal:,.2f}"
            data[f"Итого {qr.department_id}"][qr.char_day] = f"{(qr.received_cash + qr.received_terminal - qr.return_cash - qr.return_terminal):,.2f}"
        table_data = [v for v in data.values()]

    return JsonResponse({"columns": columns, "tableData": table_data})


def define_period(period_type, period_duration):
    years, months, weeks, days = 0, 0, 0, 0
    if period_type == "y" and 0 < period_duration < DASH_REPORT_LIMIT_DURATION_DAYS["years"]:
        years = -period_duration
    elif period_type == "m" and 0 < period_duration < DASH_REPORT_LIMIT_DURATION_DAYS["months"]:
        months = -period_duration
    elif period_type == "w" and 0 < period_duration < DASH_REPORT_LIMIT_DURATION_DAYS["weeks"]:
        weeks = -period_duration
    elif period_type == "d" and 0 < period_duration < DASH_REPORT_LIMIT_DURATION_DAYS["days"]:
        days = -period_duration
    return {"years": years, "months": months, "weeks": weeks, "days": days}
