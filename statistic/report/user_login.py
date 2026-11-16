import datetime

import openpyxl
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter

from laboratory.utils import replace_tz, strfdatetime
from slog.models import Log

LOGIN_LOG_TYPE = 18


def login_ip(body):
    text = (body or "").strip()
    if text.upper().startswith("IP:"):
        return text[3:].strip()
    return text


def login_user_label(doctor):
    if not doctor:
        return ""
    fio = doctor.get_fio()
    username = ""
    if getattr(doctor, "user_id", None) and getattr(doctor, "user", None):
        username = doctor.user.username or ""
    if username:
        return f"{fio} ({username})"
    return fio


def user_login_rows(date_start, date_end):
    start_raw = datetime.datetime.strptime(date_start, "%d.%m.%Y")
    end_raw = datetime.datetime.strptime(date_end, "%d.%m.%Y")
    start_date = replace_tz(datetime.datetime.combine(start_raw, datetime.time.min))
    end_date = replace_tz(datetime.datetime.combine(end_raw, datetime.time.max))
    logs = Log.objects.filter(type=LOGIN_LOG_TYPE, time__gte=start_date, time__lte=end_date).select_related("user", "user__user").order_by("time")
    return [(login_ip(row.body), login_user_label(row.user), strfdatetime(row.time, "%d.%m.%Y %H:%M:%S")) for row in logs]


def user_login_xls(request_data, response, tr):
    date_start = request_data.get("date-start") or ""
    date_end = request_data.get("date-end") or ""
    rows = []
    if date_start and date_end:
        rows = user_login_rows(date_start, date_end)

    wb = openpyxl.Workbook()
    wb.remove(wb["Sheet"])
    ws = wb.create_sheet("Вход в систему")
    thin = Side(style="thin", color="000000")
    border = Border(left=thin, top=thin, right=thin, bottom=thin)
    header_font = Font(bold=True, size=12)
    header_alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
    cell_alignment = Alignment(wrap_text=True, vertical="center")
    columns = (("IP-адрес", 22), ("Пользователь", 45), ("Время", 22))

    ws.cell(row=1, column=1).value = "Вход в систему"
    ws.cell(row=1, column=1).font = Font(bold=True, size=14)
    if date_start and date_end:
        ws.cell(row=2, column=1).value = f"{date_start} — {date_end}"

    header_row = 4
    for idx, column in enumerate(columns, 1):
        cell = ws.cell(row=header_row, column=idx)
        cell.value = column[0]
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border
        ws.column_dimensions[get_column_letter(idx)].width = column[1]

    for offset, row in enumerate(rows, 1):
        for idx, value in enumerate(row, 1):
            cell = ws.cell(row=header_row + offset, column=idx)
            cell.value = value
            cell.alignment = cell_alignment
            cell.border = border

    response["Content-Disposition"] = str.translate('attachment; filename="Вход_в_систему.xlsx"', tr)
    wb.save(response)
    return response
