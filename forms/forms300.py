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
    # TODO изменить под график

    style_right = create_style(font_size=6, leading=6, space_after=0, space_before=0, alignment="right")
    style_left = create_style(font_size=6, leading=6, space_after=0, space_before=0)
    style_left_bottom_bold = create_style(font_name="PTAstraSerifBold", font_size=6, leading=6, space_after=0, space_before=0)
    style_center_bold = create_style(font_name="PTAstraSerifBold", font_size=9, leading=9, space_after=0, space_before=0, alignment="center")
    canvas.saveState()
    text = Paragraph(f"Приложение №{context.get('order_appendix_number')} к <br/> приказу {context.get('order_date')}", context.get("style_left"))
    if is_first_page:
        text.wrapOn(canvas, 256 * mm, 197 * mm)
        text.drawOn(canvas, 256 * mm, 197 * mm)
    else:
        text.wrapOn(canvas, 256 * mm, 201 * mm)
        text.drawOn(canvas, 256 * mm, 201 * mm)
    date_now: datetime.datetime = context.get("date_now")
    current_day = date_now.day
    current_year = date_now.year
    month_name = context.get("month_name")
    table_data = [
        [
            Paragraph("", context.get("style_left")),
            Paragraph("Председатель ППО", style_right),
            Paragraph("", context.get("style_center_bold")),
            Paragraph("", context.get("style_left")),
            Paragraph("УТВЕРЖДАЮ", style_left),
            Paragraph("", context.get("style_left")),
        ],
        [
            Paragraph("", context.get("style_left")),
            Paragraph("", context.get("style_left")),
            Paragraph("", context.get("style_center")),
            Paragraph("ГРАФИК РАБОЧЕГО ВРЕМЕНИ", style_center_bold),
            Paragraph("Руководитель учреждения", style_left_bottom_bold),
            Paragraph("", context.get("style_left")),
        ],
        [
            Paragraph("", context.get("style_left")),
            Paragraph("", context.get("style_left")),
            Paragraph("", context.get("style_center")),
            Paragraph("", context.get("style_left")),
            Paragraph("", context.get("style_left")),
            Paragraph("подпись", style_right),
        ],
        [
            Paragraph("", context.get("style_left")),
            Paragraph("", context.get("style_left")),
            Paragraph("", context.get("style_center")),
            Paragraph(f"{context.get('organization_title')}", context.get("style_center")),
            Paragraph(f'"{current_day}"{month_name} {current_year}г.', context.get("style_right")),
            Paragraph("", context.get("style_center_title")),
        ],
        [
            Paragraph("&nbsp;", context.get("style_left")),
            Paragraph("", context.get("style_left")),
            Paragraph(" ", context.get("style_center")),
            Paragraph(" ", context.get("style_left")),
            Paragraph(" ", context.get("style_left")),
            Paragraph(" ", context.get("style_left")),
        ],
        [
            Paragraph("", context.get("style_left")),
            Paragraph("", context.get("style_left")),
            Paragraph("", context.get("style_center_bold")),
            Paragraph(f"{context.get('department_title')}", context.get("style_center")),
            Paragraph("календарных дней", style_left),  # TODO кол-во дней в месяце графика
            Paragraph("", context.get("style_left")),
        ],
        [
            Paragraph("", context.get("style_left")),
            Paragraph("", context.get("style_left")),
            Paragraph("", context.get("style_center")),
            Paragraph("(подразделение)", context.get("style_center")),
            Paragraph("рабочих дней", style_left),  # TODO кол-во рабочих дней из графика
            Paragraph("", context.get("style_left")),
        ],
        [
            Paragraph("", context.get("style_left")),
            Paragraph("", context.get("style_left")),
            Paragraph("", context.get("style_left")),
            Paragraph("__________________ 2025 год", context.get("style_center")),  #TODO месяц и год графика
            Paragraph("", context.get("style_left")),
            Paragraph("", context.get("style_left")),
        ]
    ]

    col_widths = [
        context.get("item_number_col_width"),
        19 * mm,
        21 * mm,
        144 * mm,
        26.5 * mm,
        30 * mm,
    ]
    table_style = [
        # ("GRID", (0, 0), (-1, -1), 0.75, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("VALIGN", (4, 1), (4, 1), "BOTTOM"),
        ("VALIGN", (5, 2), (5, 2), "TOP"),
        ("VALIGN", (4, 5), (4, 6), "BOTTOM"),
        ("TOPPADDING", (5, 2), (5, 2), 0),
        ("BOTTOMPADDING", (5, 2), (5, 2), 6),

        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("SPAN", (4, 3), (5, 3)),
        ("LINEBELOW", (2, 0), (2, 0), 0.75, colors.black),
        ("LINEBELOW", (5, 1), (5, 1), 0.75, colors.black),
        ("LINEBELOW", (0, 5), (4, 5), 0.75, colors.black),
        ("LINEBELOW", (4, 6), (4, 6), 0.75, colors.black),
    ]
    table = create_table(table_data, table_style, col_widths)
    if is_first_page:
        table.wrapOn(canvas, 7 * mm, 156 * mm)
        table.drawOn(canvas, 7 * mm, 156 * mm)
    else:
        table.wrapOn(canvas, 7 * mm, 160 * mm)
        table.drawOn(canvas, 7 * mm, 160 * mm)
    canvas.setFont("PTAstraSerifReg", 8)

    canvas.drawString(11 * mm, 41 * mm, "Заведующий отделением")
    canvas.line(42 * mm, 40 * mm, 72 * mm, 40 * mm)
    canvas.drawString(110 * mm, 41 * mm, "Старшая медицинская сестра")
    canvas.line(146 * mm, 40 * mm, 176 * mm, 40 * mm)

    canvas.restoreState()


def form_01(request_data):
    """
    Создание печатной формы графика рабочего времени
    """
    # TODO Изменить таблицу табеля на таблицу графика в форме (кол-во колонок, названия)
    register_fonts()
    style = create_style(font_size=10, alignment="justify")
    style_center = create_style(style, alignment="center")
    style_center_bold = create_style(style_center, "PTAstraSerifBold")
    style_center_title = create_style(style_center, font_size=7)
    style_center_sup = create_style(style_center, font_size=5)
    style_center_data = create_style(style_center, font_size=6)
    style_left = create_style(font_size=6)
    style_left_bold = create_style(style_left, "PTAstraSerifBold")
    style_right = create_style(style_left, alignment="right")
    style_right_bold = create_style(style_right, "PTAstraSerifBold")

    document_data = []
    department_table_number = 27  # TODO не актуально?
    month_name = pytils.dt.ru_strftime(u"%B", inflected=True, date=datetime.datetime.now())  # TODO месяц надо получать из документа который приходит в запросе
    current_year = datetime.date.today().year  # TODO год из документа
    current_month = datetime.date.today().month  # TODO месяц из документа
    first_day_month = 1
    last_day_month = calendar.monthrange(current_year, current_month)[1]
    tabel_type = "первичный"  # TODO Этого нет в графике
    department_title = "Кабинет неотложной травматологии и ортопедии (травмпункт)"  # TODO это из документа
    date_now = datetime.datetime.now()  # TODO не из документа а время печати?
    main_doctor = "Новожилов В.А."  # TODO динамически
    head_department = "Преториус Т.Л."  # TODO Из документа
    old_sestra = "Тотьямина Д.С."  # TODO из документа, переименовать
    hr_specialist = "Краснова С.А."  # TODO не актуально
    organization: Hospitals = request_data.get("hospital")
    organization_title = organization.safe_short_title
    order_appendix_number = "2"
    order_date = "от '20' февраля 2025 г №37"

    second_row_data = [
        Paragraph("", style_center_data),
        Paragraph("", style_center_data),
        Paragraph("", style_center_data),
        Paragraph("", style_center_data),
        Paragraph("", style_center_data),
        Paragraph("", style_center_data),
        Paragraph("", style_center_data),
    ]
    date_month_start = [Paragraph(f"{number_day}", style_center_data) for number_day in range(1, last_day_month + 1)]
    summ_all = [
        Paragraph("Количество часов согласно графику", style_center_data),
        Paragraph("Подпись работника", style_center_data),
    ]

    second_row_data.extend(date_month_start)
    second_row_data.extend(summ_all)

    working_time_schedule_data = [
        [
            Paragraph("№ п/п", style_center_data),
            Paragraph("Фамилия, имя, отчество", style_center_data),
            Paragraph("Должность (профессия)", style_center_data),
            Paragraph("Вид занятости (осн, внутр, внеш)", style_center_data),
            Paragraph("Занимаемый объем (согл ТД), шт ед", style_center_data),
            Paragraph("Норма часов на занимаемый объем", style_center_data),
            Paragraph("Рабочая смена", style_center_data),
            Paragraph("Числа месяца", style_center_data)
        ],
        second_row_data,
    ]
    # TODO Здесь заполнение таблицы данными, с объединением строк по фио (одно фио, две должности) для табеля, необходимо поменять под график
    # col_span = []
    # start_row = 3
    # for data_person in data_json["personData"]:
    #     row = 0
    #     for data_employee in data_person["employeeData"]:
    #         common = []
    #         fio = data_person["personLastname"] + " " + data_person["personFirstName"] + " " + data_person["personPatronymic"]
    #         post = data_employee["postTitle"] + " " + data_employee["typePost"]
    #         common.append(Paragraph(fio, style_center_data))
    #         common.append(Paragraph(data_employee["tabelNumber"], style_center_data))
    #         common.append(Paragraph(post, style_center_data_title))
    #         dates = data_employee["dates"]
    #         dates.sort()
    #         tmp_common_hours = ['' for x in range(len(dates))]
    #         for k, v in data_employee["commonHours"].items():
    #             pos = dates.index(k)
    #             tmp_common_hours[pos] = Paragraph(v, style_center_data)
    #         tmp_common_hours.insert(15, Paragraph('10', style_center_data))
    #         common.extend(tmp_common_hours)
    #         common.append(Paragraph('7', style_center_data))
    #         common.append(Paragraph('46', style_center_data))
    #         common.append(Paragraph('28', style_center_data))
    #         common.append(Paragraph('', style_center_data))
    #         common.append(Paragraph('', style_center_data))
    #         opinion.append(common)
    #         row += 1
    #     col_span.append(('SPAN', (0, start_row), (0, start_row + (row - 1))))
    #     start_row += row

    working_time_schedule_style = [
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
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMTPADDING", (0, 0), (-1, -1), -1),
        ("TOPPADDING", (0, 0), (-1, -1), -1),
        ("TOPPADDING", (0, 2), (-1, 2), 4),
    ]
    # table_style.extend(col_span)

    item_number_col_width = 8 * mm
    fio_col_width = 17 * mm
    position_col_width = 15 * mm
    type_employment_col_width = 13 * mm
    occupied_volume_col_width = 11 * mm
    norm_hours_col_width = 13 * mm
    working_shift_col_width = 8.7 * mm
    dates_col_widths = [None for _ in range(1, last_day_month+1)]  # 5.6 норм
    amount_hours_col_width = 14 * mm
    employees_signature = 15 * mm
    col_widths = [
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

    table = create_table(working_time_schedule_data, working_time_schedule_style, col_widths, "LEFT", 1, 3)

    document_data.append(table)

    context = {
        "department_table_number": department_table_number,
        "month_name": month_name,
        "current_year": current_year,
        "first_day_month": first_day_month,
        "last_day_month": last_day_month,
        "date_now": date_now,
        "organization_title": organization_title,
        "department_title": department_title,
        "tabel_type": tabel_type,
        "main_doctor": main_doctor,
        "head_department": head_department,
        "old_sestra": old_sestra,
        "hr_specialist": hr_specialist,
        "style_left": style_left,
        "style_left_bold": style_left_bold,
        "style_right": style_right,
        "style_center": style_center,
        "style_center_bold": style_center_bold,
        "style_center_title": style_center_title,
        "style_center_sup": style_center_sup,
        "style_right_bold": style_right_bold,
        "order_appendix_number": order_appendix_number,
        "order_date": order_date,
        "item_number_col_width": item_number_col_width,
    }

    def first_pages(canvas, doc):
        _create_meta_information(canvas, True, context)

    def later_pages(canvas, doc):
        _create_meta_information(canvas, False, context)

    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=5 * mm, leftMargin=5 * mm, topMargin=56 * mm, bottomMargin=43 * mm, title="График рабочего времени")
    document.build(document_data, first_pages, later_pages)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
