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


def form_01(request_data):
    """
    Создание печатной формы графика рабочего времени
    """
    register_fonts()
    style = create_style(font_size=10, alignment="justify")
    # TODO Изменить названия стилей на более правильные
    style_center = create_style(style, alignment="center")
    style_center_bold = create_style(style_center, "PTAstraSerifBold")
    style_center_title = create_style(style_center, font_size=7)
    style_center_sup = create_style(style_center, font_size=5)
    style_center_data = create_style(style_center, font_size=8)
    style_center_data_bold = create_style(style_center_bold)  # TODO Заменить его в коде на style_center_bold
    style_center_data_title = create_style(style_center_title)  # TODO Заменить его в коде на style_center_title
    style_left = create_style(font_size=6)
    style_right = create_style(style_left, alignment="right")
    style_right_bold = create_style(style_right, "PTAstraSerifBold")

    objs = [] # TODO Изменить на document_data
    department_table_number = 27
    month_name = pytils.dt.ru_strftime(u"%B", inflected=True, date=datetime.datetime.now()) # TODO месяц надо получать из документа который приходит в запросе
    current_year = datetime.date.today().year # TODO год из документа
    current_month = datetime.date.today().month # TODO месяц из документа
    first_day_month = 1
    last_day_month = calendar.monthrange(current_year, current_month)[1]
    tabel_type = 'первичный'  # TODO Этого нет в графике
    department_name = 'Кабинет неотложной травматологии и ортопедии (травмпункт)' # TODO это из документа
    date_now = datetime.datetime.now().strftime('%d.%m.%Y') # TODO не актуально
    main_doctor = 'Новожилов В.А.'  # TODO динамически
    head_department = 'Преториус Т.Л.'  # TODO Из документа
    old_sestra = 'Тотьямина Д.С.'  # TODO из документа
    hr_specialist = 'Краснова С.А.'  # TODO не акутально
    hospital: Hospitals = request_data.get("hospital")  # TODO заменить на organization
    hospital_name = hospital.safe_short_title

    title = [
        Paragraph('', style_center_data_title),
        Paragraph('', style_center_data_title),
        Paragraph('', style_center_data_title),
    ]
    date_month_start = [Paragraph(f'{number_day}', style_center_data_title) for number_day in range(1, 16)]
    summ_day_15 = [Paragraph('Итого дней (часов) явок (неявок) с 1-15', style_center_data_title)]
    date_month_end = [Paragraph(f'{number_day}', style_center_data_title) for number_day in range(16, last_day_month + 1)]
    summ_all = [
        Paragraph('Всего дней (часов) явок (неявок) за месяц', style_center_data_title),
        Paragraph('Всего отработано часов', style_center_data_title),
        Paragraph('Ночные', style_center_data_title),
        Paragraph('Выходные', style_center_data_title),
        Paragraph('Праздничные', style_center_data_title),
    ]

    title.extend(date_month_start)
    title.extend(summ_day_15)
    title.extend(date_month_end)
    title.extend(summ_all)

    column_numbers = [Paragraph(f'{column_number}', style_center_data_title) for column_number in range(1, last_day_month + 10)]

    opinion = [
        [
            Paragraph('Фамилия, имя, отчество', style_center_data),
            Paragraph('Учетный номер', style_center_data),
            Paragraph('Должность (профессия)', style_center_data),
            Paragraph('Числа месяца', style_center_data)
        ],
        title,
        column_numbers
    ]

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

    table_style = [
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('SPAN', (2, 0), (2, 1)),
        ('SPAN', (3, 0), (-1, 0)),
        ('LEFTPADDING', (0, 0), (-1, -1), 1),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMTPADDING', (0, 0), (-1, -1), -1),
        ('TOPPADDING', (0, 0), (-1, -1), -1),
        ('TOPPADDING', (0, 2), (-1, 2), 4),
    ]
    # table_style.extend(col_span)

    col_widths = []
    counter = 1
    for i in range(1, last_day_month + 10):
        if counter == 1:
            col_widths.append(23 * mm)
        elif counter == 2:
            col_widths.append(10 * mm)
        elif counter == 3:
            col_widths.append(19 * mm)
        elif counter == 19:
            col_widths.append(10 * mm)
        elif counter <= last_day_month + 4:
            col_widths.append(5.8 * mm)
        elif counter == last_day_month + 5:
            col_widths.append(10 * mm)
        elif counter <= last_day_month + 9:
            col_widths.append(7.5 * mm)
        counter += 1

    table = create_table(opinion, table_style, col_widths, "LEFT", 1, 3)

    objs.append(table)

    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=10 * mm, leftMargin=5 * mm, topMargin=56 * mm, bottomMargin=43 * mm, title="График рабочего времени")
    document.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
