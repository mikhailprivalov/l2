import calendar
import datetime
from io import BytesIO

import pytils
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph

from forms.utils import register_fonts, create_style, create_table
from hospitals.models import Hospitals


def _create_meta_information(canvas, is_first_page: bool, context: dict):
    """
    Функция создания мета информации для печатной формы графика-табеля
    """

    style_right = create_style(font_size=6, leading=6, alignment="right")
    style_left = create_style(style_right, alignment="left")
    style_left_bottom_bold = create_style(style_right, font_name="PTAstraSerifBold", alignment="left")
    style_center = create_style(font_size=6, leading=6, alignment="center")
    style_center_header_bold = create_style(style_center, font_name="PTAstraSerifBold", font_size=9, leading=9)
    canvas.saveState()
    text = Paragraph(f"Приложение №{context.get('order_appendix_number')} к <br/> приказу {context.get('order_date')}", style_left)
    # TODO Надо ли разных страницах разную высоту? 4мм выше на следующих страницах
    if is_first_page:
        text.wrapOn(canvas, 256 * mm, 203 * mm)
        text.drawOn(canvas, 256 * mm, 203 * mm)
    else:
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
            Paragraph("рабочих дней", style_left),  # TODO кол-во рабочих дней из графика
            Paragraph("", style_right),
        ],
        [
            Paragraph("", style_right),
            Paragraph("", style_right),
            Paragraph("", style_right),
            Paragraph(f"{document_month_name} {document_year} год", style_center),
            Paragraph("", style_right),
            Paragraph("", style_right),
        ]
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
        *department_title_style
    ]
    table = create_table(header_table_data, header_table_style, col_widths)
    if is_first_page:
        table.wrapOn(canvas, 7 * mm, 179 * mm)
        table.drawOn(canvas, 7 * mm, 179 * mm)
    else:
        table.wrapOn(canvas, 7 * mm, 179 * mm)
        table.drawOn(canvas, 7 * mm, 179 * mm)
    canvas.setFont("PTAstraSerifReg", 8)

    canvas.drawString(11 * mm, 10 * mm, "Заведующий отделением")
    canvas.line(42 * mm, 9 * mm, 72 * mm, 9 * mm)
    canvas.drawString(110 * mm, 10 * mm, "Старшая медицинская сестра")
    canvas.line(146 * mm, 9 * mm, 176 * mm, 9 * mm)

    canvas.restoreState()


def _create_wts_table_header(style_center, document_last_day_month):
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
            Paragraph("Числа месяца", style_center)
        ],
        second_row_data,
    ]

    return header_table_data


def _create_wts_table_body():
    # TODO здесь будут данные
    return [[]]


def _create_wts_table_style():
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
    return table_style


def _create_wts_table_cols_widths(document_last_day_month: int) -> list:
    item_number_col_width = 8 * mm
    fio_col_width = 17 * mm
    position_col_width = 15 * mm
    type_employment_col_width = 13 * mm
    occupied_volume_col_width = 11 * mm
    norm_hours_col_width = 13 * mm
    working_shift_col_width = 8.7 * mm
    dates_col_widths = [None for _ in range(1, document_last_day_month + 1)]  # TODO подумать какую ширину сделать, ~5.6 норм
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
        employees_signature
    ]
    return cols_widths


def _create_work_time_schedule_table(style_center, document_last_day_month: int):
    data = [
        *_create_wts_table_header(style_center, document_last_day_month),
        *_create_wts_table_body()
    ]
    style = _create_wts_table_style()
    cols_widths = _create_wts_table_cols_widths(document_last_day_month)
    table = create_table(data, style, cols_widths, "LEFT", 1, 3)
    return table


def form_01(request_data):
    """
    Создание печатной формы графика рабочего времени
    """
    register_fonts()
    style_center = create_style(font_size=6, leading=6, alignment="center")

    document_date = datetime.datetime.now()  # TODO Брать из документа
    document_month_name = pytils.dt.ru_strftime(u"%B", date=document_date)
    document_year = document_date.year
    document_month = document_date.month
    document_last_day_month = calendar.monthrange(document_year, document_month)[1]
    department_title = "Кабинет неотложной травматологии и ортопедии (травмпункт)"  # TODO это из документа
    organization: Hospitals = request_data.get("hospital")
    organization_title = organization.safe_short_title
    order_appendix_number = "2"
    order_date = "от '20' февраля 2025 г №37"

    work_time_schedule_table = _create_work_time_schedule_table(style_center, document_last_day_month)
    document_data = [work_time_schedule_table]

    meta_context = {
        "document_year": document_year,
        "document_month_name": document_month_name,
        "document_last_day_month": document_last_day_month,
        "organization_title": organization_title,
        "department_title": department_title,
        "order_appendix_number": order_appendix_number,
        "order_date": order_date,
    }

    def first_pages(canvas, doc):
        _create_meta_information(canvas, True, meta_context)

    def later_pages(canvas, doc):
        _create_meta_information(canvas, False, meta_context)

    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=5 * mm, leftMargin=5 * mm, topMargin=32 * mm, bottomMargin=43 * mm, title="График рабочего времени")
    document.build(document_data, first_pages, later_pages)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
