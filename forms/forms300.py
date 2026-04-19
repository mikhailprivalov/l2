import calendar
import datetime
from io import BytesIO
from typing import List, Tuple, Dict

import pytils
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table

from employees.models import TimeTrackingDocument, WorkDayStatus, Holidays
from forms.utils import register_fonts, create_style, create_table
from hospitals.models import Hospitals


def _create_meta_information(canvas, context: dict) -> None:
    """
    Функция добавления мета информации для печатной формы графика
    """

    style_right = create_style(font_size=6, leading=6, alignment="right")
    style_left = create_style(style_right, alignment="left")
    style_left_bottom_bold = create_style(style_right, font_name="PTAstraSerifBold", alignment="left")
    style_center = create_style(font_size=6, leading=6, alignment="center")
    style_center_header_bold = create_style(style_center, font_name="PTAstraSerifBold", font_size=9, leading=9)
    canvas.saveState()
    text = Paragraph("Приложение №2 к <br/> приказу от '20' февраля 2025 г №37", style_left)
    text.wrapOn(canvas, 256 * mm, 203 * mm)
    text.drawOn(canvas, 256 * mm, 203 * mm)
    current_date = datetime.datetime.now()
    current_month_name = pytils.dt.ru_strftime(u"%B", inflected=True, date=current_date)
    current_day = current_date.day
    current_year = current_date.year
    document_year = context.get("document_year")
    document_month_name = context.get("document_month_name")
    document_last_day_month = context.get("document_last_day_month")
    header_table_data = [
        [
            Paragraph("", style_right),
            Paragraph("Председатель ППО", style_right),
            Paragraph("", style_center_header_bold),
            Paragraph("", style_right),
            Paragraph("УТВЕРЖДАЮ", style_left),
            Paragraph("", style_right),
        ],
        [
            Paragraph("", style_right),
            Paragraph("", style_right),
            Paragraph("", style_center_header_bold),
            Paragraph("ГРАФИК РАБОЧЕГО ВРЕМЕНИ", style_center_header_bold),
            Paragraph("Руководитель учреждения", style_left_bottom_bold),
            Paragraph("", style_right),
        ],
        [
            Paragraph("", style_right),
            Paragraph("", style_right),
            Paragraph("", style_center_header_bold),
            Paragraph("", style_right),
            Paragraph("", style_right),
            Paragraph("подпись", style_right),
        ],
        [
            Paragraph("", style_right),
            Paragraph("", style_right),
            Paragraph("", style_right),
            Paragraph(f"{context.get('organization_title')}", style_center_header_bold),
            Paragraph(f'"{current_day}"{current_month_name} {current_year}г.', style_right),
            Paragraph("", style_right),
        ],
        [
            Paragraph("&nbsp;", style_right),
            Paragraph("", style_right),
            Paragraph(" ", style_right),
            Paragraph(" ", style_right),
            Paragraph(" ", style_right),
            Paragraph(" ", style_right),
        ],
        [
            Paragraph("", style_right),
            Paragraph("", style_right),
            Paragraph("", style_right),
            Paragraph(f"{context.get('department_title')}", style_center_header_bold),
            Paragraph(f"календарных дней {document_last_day_month}", style_left),
            Paragraph("", style_right),
        ],
        [
            Paragraph("", style_right),
            Paragraph("", style_right),
            Paragraph("", style_center),
            Paragraph("(подразделение)", style_center),
            Paragraph("рабочих дней", style_left),
            Paragraph("", style_right),
        ],
        [
            Paragraph("", style_right),
            Paragraph("", style_right),
            Paragraph("", style_right),
            Paragraph(f"{document_month_name} {document_year} год", style_center),
            Paragraph("", style_right),
            Paragraph("", style_right),
        ],
    ]

    col_widths = [
        8 * mm,
        19 * mm,
        21 * mm,
        144 * mm,
        26.5 * mm,
        30 * mm,
    ]
    department_title_style = [
        ("TOPPADDING", (3, 0), (3, -1), 0),
        ("BOTTOMPADDING", (3, 0), (3, -1), 2.5),
    ]
    header_table_style = [
        ("VALIGN", (4, 2), (4, 2), "BOTTOM"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("SPAN", (4, 3), (5, 3)),
        ("LINEBELOW", (2, 0), (2, 0), 0.75, colors.black),
        ("LINEBELOW", (5, 1), (5, 1), 0.75, colors.black),
        ("LINEBELOW", (0, 5), (4, 5), 0.75, colors.black),
        ("LINEBELOW", (4, 6), (4, 6), 0.75, colors.black),
        *department_title_style,
    ]
    table = create_table(header_table_data, header_table_style, col_widths)
    table.wrapOn(canvas, 7 * mm, 179 * mm)
    table.drawOn(canvas, 7 * mm, 179 * mm)

    canvas.setFont("PTAstraSerifReg", 8)
    canvas.drawString(11 * mm, 10 * mm, "Заведующий отделением")
    canvas.line(42 * mm, 9 * mm, 72 * mm, 9 * mm)
    canvas.drawString(110 * mm, 10 * mm, "Старшая медицинская сестра")
    canvas.line(146 * mm, 9 * mm, 176 * mm, 9 * mm)

    canvas.restoreState()


def _create_work_time_schedule_table_header(style_center, document_last_day_month: int) -> List[List[Paragraph]]:
    second_row_data = [
        Paragraph("", style_center),
        Paragraph("", style_center),
        Paragraph("", style_center),
        Paragraph("", style_center),
        Paragraph("", style_center),
        Paragraph("", style_center),
        Paragraph("", style_center),
    ]
    date_month_start = [Paragraph(f"{number_day}", style_center) for number_day in range(1, document_last_day_month + 1)]
    summ_all = [
        Paragraph("Количество часов согласно графику", style_center),
        Paragraph("Подпись работника", style_center),
    ]

    second_row_data.extend(date_month_start)
    second_row_data.extend(summ_all)

    header_table_data = [
        [
            Paragraph("№ п/п", style_center),
            Paragraph("Фамилия, имя, отчество", style_center),
            Paragraph("Должность (профессия)", style_center),
            Paragraph("Вид занятости (осн, внутр, внеш)", style_center),
            Paragraph("Занимаемый объем (согл ТД), шт ед", style_center),
            Paragraph("Норма часов на занимаемый объем", style_center),
            Paragraph("Рабочая смена", style_center),
            Paragraph("Числа месяца", style_center),
        ],
        second_row_data,
    ]

    return header_table_data


def _create_work_time_schedule_table_style(document_date: datetime.date, document_last_day_month: int, holidays: dict) -> List[Tuple]:
    table_style = [
        ("GRID", (0, 0), (-1, -1), 0.75, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("SPAN", (0, 0), (0, 1)),
        ("SPAN", (1, 0), (1, 1)),
        ("SPAN", (2, 0), (2, 1)),
        ("SPAN", (3, 0), (3, 1)),
        ("SPAN", (4, 0), (4, 1)),
        ("SPAN", (5, 0), (5, 1)),
        ("SPAN", (6, 0), (6, 1)),
        ("SPAN", (7, 0), (-1, 0)),
        ("LEFTPADDING", (0, 0), (-1, -1), 0.1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0.1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), -1),
    ]
    weekend_fill_color = "#FFE699"
    holiday_fill_color = "#D4B86A"
    date_start_col = 7
    date_header_row = 2
    row_end = -1
    dates = [datetime.date(document_date.year, document_date.month, number_day) for number_day in range(1, document_last_day_month + 1)]
    fill_style = []
    for offset, date in enumerate(dates):
        col = date_start_col + offset
        holiday_info = holidays.get(date.strftime("%Y-%m-%d")) or {}
        holiday_kind = holiday_info.get("kind")
        is_holiday = holiday_kind == Holidays.Kind.HOLIDAY
        is_weekday = date.isoweekday() in (6, 7)
        if is_holiday:
            fill_style.append(("BACKGROUND", (col, date_header_row), (col, row_end), holiday_fill_color))
        elif is_weekday:
            fill_style.append(("BACKGROUND", (col, date_header_row), (col, row_end), weekend_fill_color))
    table_style.extend(fill_style)

    return table_style


def _create_work_time_schedule_table_cols_widths(document_last_day_month: int) -> List[float]:
    item_number_col_width = 8 * mm
    fio_col_width = 17 * mm
    position_col_width = 15 * mm
    type_employment_col_width = 13 * mm
    occupied_volume_col_width = 11 * mm
    norm_hours_col_width = 13 * mm
    working_shift_col_width = 8.7 * mm
    dates_col_widths = [None for _ in range(1, document_last_day_month + 1)]
    amount_hours_col_width = 14 * mm
    employees_signature = 15 * mm
    cols_widths = [
        item_number_col_width,
        fio_col_width,
        position_col_width,
        type_employment_col_width,
        occupied_volume_col_width,
        norm_hours_col_width,
        working_shift_col_width,
        *dates_col_widths,
        amount_hours_col_width,
        employees_signature,
    ]
    return cols_widths


def _parse_cell_data(work_day_statuses: Dict, cell_value: Dict):
    start_time = cell_value.get("startWorkTime")
    end_time = cell_value.get("endWorkTime")
    type_id = cell_value.get("typeId")
    if type_id:
        result = work_day_statuses.get(int(type_id), "")
    elif start_time and end_time:
        result = f"{start_time}\n{end_time}"
    else:
        result = ""
    return result


def _create_work_time_schedule_table_body(employees_work_time: List[Dict], work_day_statuses: Dict[int, str], style_center, style_left) -> List[List[Paragraph]]:
    table_body = []
    for index, work_time in enumerate(employees_work_time, 1):
        item_number = Paragraph(f"{index}", style_center)
        fio = Paragraph(work_time.get("fio"), style_left)
        position = Paragraph(work_time.get("position"), style_left)
        type_employment = Paragraph(work_time.get("bidType"), style_center)
        occupied_volume = Paragraph("", style_center)
        norm_hours = Paragraph("", style_center)
        working_shift = Paragraph("", style_center)
        total_hours_decimal = Paragraph(work_time.get("totalHoursDecimal"), style_center)
        date_keys = []
        for key in work_time.keys():
            try:
                date_key = datetime.datetime.strptime(key, "%Y-%m-%d")
                date_keys.append(date_key)
            except ValueError:
                pass
        date_keys_sorted = sorted(date_keys)
        date_values = [Paragraph(_parse_cell_data(work_day_statuses, work_time.get(date_key.strftime("%Y-%m-%d"))), style_center) for date_key in date_keys_sorted]
        row = [item_number, fio, position, type_employment, occupied_volume, norm_hours, working_shift, *date_values, total_hours_decimal]
        table_body.append(row)
    return table_body


def _create_work_time_schedule_table(style_center, style_left, document_date: datetime.date, document_last_day_month: int, employees_work_time: List[Dict], work_day_statuses: dict, holidays: dict) -> Table:
    data = [
        *_create_work_time_schedule_table_header(style_center, document_last_day_month),
        *_create_work_time_schedule_table_body(employees_work_time, work_day_statuses, style_center, style_left),
    ]
    style = _create_work_time_schedule_table_style(document_date, document_last_day_month, holidays)
    cols_widths = _create_work_time_schedule_table_cols_widths(document_last_day_month)
    table = create_table(data, style, cols_widths, "LEFT", 1, 2)
    return table


def form_01(request_data):
    """
    Создание печатной формы графика рабочего времени
    """
    request_body = request_data.get("request_body")
    document_id = request_body.get("documentId")
    employees_work_time = request_body.get("employeesWorkTime")
    time_tracking_document: TimeTrackingDocument = TimeTrackingDocument.get_document_for_print(document_id)
    work_day_statuses = WorkDayStatus.get_statuses_dict()

    register_fonts()
    style_center = create_style(font_size=6, leading=6, alignment="center")
    style_left = create_style(style_center, alignment="left")

    document_date = time_tracking_document.month
    document_month_name = pytils.dt.ru_strftime(u"%B", date=document_date)
    document_year = document_date.year
    document_month = document_date.month
    document_last_day_month = calendar.monthrange(document_year, document_month)[1]
    department_title = time_tracking_document.department.name
    organization: Hospitals = request_data.get("hospital")
    organization_title = organization.safe_short_title
    holidays = Holidays.get_holidays(datetime.date(document_year, document_month, 1))

    work_time_schedule_table = _create_work_time_schedule_table(style_center, style_left, document_date, document_last_day_month, employees_work_time, work_day_statuses, holidays)
    document_data = [work_time_schedule_table]

    meta_context = {
        "document_year": document_year,
        "document_month_name": document_month_name,
        "document_last_day_month": document_last_day_month,
        "organization_title": organization_title,
        "department_title": department_title,
    }

    def first_pages(canvas, doc):
        _create_meta_information(canvas, meta_context)

    def later_pages(canvas, doc):
        _create_meta_information(canvas, meta_context)

    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=5 * mm, leftMargin=5 * mm, topMargin=32 * mm, bottomMargin=15 * mm, title="График рабочего времени")
    document.build(document_data, first_pages, later_pages)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
