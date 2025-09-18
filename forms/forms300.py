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
    canvas.saveState()
    text = Paragraph('Утв приказом Минфина России <br/> от 30 марта 2015 г. № 52н', context.get("style_right_bold"))
    if is_first_page:
        text.wrapOn(canvas, 141 * mm, 194 * mm)
        text.drawOn(canvas, 141 * mm, 194 * mm)
    else:
        text.wrapOn(canvas, 141 * mm, 198 * mm)
        text.drawOn(canvas, 141 * mm, 198 * mm)
    opinion_f = [
        [
            Paragraph('', context.get("style_left")),
            Paragraph(f'Табель № <u>{context.get("department_table_number")}</u>', context.get("style_center_bold")),
            Paragraph('', context.get("style_right")),
            Paragraph('', context.get("style_center_title"))
        ],
        [
            Paragraph('', context.get("style_left")),
            Paragraph('учета использования рабочего времени', context.get("style_center")),
            Paragraph('', context.get("style_right")),
            Paragraph('Коды', context.get("style_center_title"))
        ],
        [
            Paragraph('', context.get("style_left")),
            Paragraph('', context.get("style_center")),
            Paragraph('Форма ОКУД', context.get("style_right")),
            Paragraph('0504421', context.get("style_center_title"))
        ],
        [
            Paragraph('', context.get("style_left")),
            Paragraph(f'За период с {context.get("first_day_month")} по {context.get("last_day_month")} {context.get("month_name")} {context.get("current_year")} года',
                      context.get("style_center")),
            Paragraph('Дата', context.get("style_right")),
            Paragraph(f'{context.get("date_now")}', context.get("style_center_title"))
        ],
        [
            Paragraph('Учреждение', context.get("style_left")),
            Paragraph(f'{context.get("organization_title")}', context.get("style_center")),
            Paragraph('по ОКПО', context.get("style_right")),
            Paragraph('', context.get("style_center_title"))
        ],
        [
            Paragraph('Структурное подразделение', context.get("style_left")),
            Paragraph(f'{context.get("department_name")}', context.get("style_center_bold")),
            Paragraph('', context.get("style_right")),
            Paragraph('', context.get("style_center_title"))
        ],
        [
            Paragraph('Вид табеля', context.get("style_left")),
            Paragraph(f'{context.get("tabel_type")}', context.get("style_center")),
            Paragraph('Номер корректировки', context.get("style_right")),
            Paragraph('', context.get("style_center_title"))
        ],
        [
            Paragraph('', context.get("style_left")),
            Paragraph('(первичный - 0, корректирующий 1,2  и т.д)', context.get("style_center_sup")),
            Paragraph('Дата формирования документа', context.get("style_right")),
            Paragraph(f'{context.get("date_now")}', context.get("style_center_title"))
        ]
    ]
    col_widths_f = [30 * mm, 180 * mm, 40 * mm, 25 * mm]
    table_style_f = [
        ('LINEBELOW', (1, 4), (1, 6), 0.75, colors.black),
        ('GRID', (3, 1), (3, -1), 0.75, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 1),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMTPADDING', (0, 0), (-1, -1), -1),
        ('TOPPADDING', (0, 0), (-1, -1), -1)
    ]
    table_f = create_table(opinion_f, table_style_f, col_widths_f)
    if is_first_page:
        table_f.wrapOn(canvas, 7 * mm, 156 * mm)
        table_f.drawOn(canvas, 7 * mm, 156 * mm)
    else:
        table_f.wrapOn(canvas, 7 * mm, 160 * mm)
        table_f.drawOn(canvas, 7 * mm, 160 * mm)
    canvas.setFont('PTAstraSerifReg', 8)

    canvas.drawString(11 * mm, 41 * mm, 'Главный врач')
    canvas.drawString(75 * mm, 41 * mm, f'{context.get("main_doctor")}')

    canvas.line(7 * mm, 40 * mm, 33 * mm, 40 * mm)
    canvas.line(45 * mm, 40 * mm, 101 * mm, 40 * mm)

    canvas.drawString(12 * mm, 37 * mm, '(должность)')
    canvas.drawString(50 * mm, 37 * mm, '(подпись)')

    canvas.drawString(10 * mm, 31 * mm, 'Зав. отделением')
    canvas.drawString(75 * mm, 31 * mm, f'{context.get("head_department")}')

    canvas.line(7 * mm, 30 * mm, 33 * mm, 30 * mm)
    canvas.line(45 * mm, 30 * mm, 101 * mm, 30 * mm)

    canvas.drawString(12 * mm, 27 * mm, '(должность)')
    canvas.drawString(50 * mm, 27 * mm, '(подпись)')

    canvas.drawString(8 * mm, 21 * mm, 'Старшая медсестра')
    canvas.drawString(75 * mm, 21 * mm, f'{context.get("old_sestra")}')

    canvas.line(7 * mm, 20 * mm, 33 * mm, 20 * mm)
    canvas.line(45 * mm, 20 * mm, 101 * mm, 20 * mm)

    canvas.drawString(12 * mm, 17 * mm, '(должность)')
    canvas.drawString(50 * mm, 17 * mm, '(подпись)')

    canvas.drawString(10 * mm, 11 * mm, 'Специалист о.к.')
    canvas.drawString(75 * mm, 11 * mm, f'{context.get("hr_specialist")}')

    canvas.line(7 * mm, 10 * mm, 33 * mm, 10 * mm)
    canvas.line(45 * mm, 10 * mm, 101 * mm, 10 * mm)

    canvas.drawString(12 * mm, 7 * mm, '(должность)')
    canvas.drawString(50 * mm, 7 * mm, '(подпись)')

    canvas.rect(156 * mm, 10 * mm, 112 * mm, 23 * mm, stroke=1, fill=0)
    canvas.setFont('PTAstraSerifBold', 8)
    canvas.drawString(185 * mm, 30 * mm, 'Отметка бухгалтерии о принятии настоящего табеля')
    canvas.drawString(160 * mm, 24 * mm, 'Исполнитель')
    canvas.setFont('PTAstraSerifReg', 8)
    canvas.line(180 * mm, 23 * mm, 255 * mm, 23 * mm)
    canvas.drawString(210 * mm, 20 * mm, '(подпись)')

    canvas.line(165 * mm, 13 * mm, 175 * mm, 13 * mm)
    canvas.line(180 * mm, 13 * mm, 210 * mm, 13 * mm)
    canvas.line(215 * mm, 13 * mm, 225 * mm, 13 * mm)

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
    style_center_data = create_style(style_center, font_size=8)
    style_left = create_style(font_size=6)
    style_right = create_style(style_left, alignment="right")
    style_right_bold = create_style(style_right, "PTAstraSerifBold")

    document_data = []
    department_table_number = 27  # TODO не актуально?
    month_name = pytils.dt.ru_strftime(u"%B", inflected=True, date=datetime.datetime.now()) # TODO месяц надо получать из документа который приходит в запросе
    current_year = datetime.date.today().year  # TODO год из документа
    current_month = datetime.date.today().month  # TODO месяц из документа
    first_day_month = 1
    last_day_month = calendar.monthrange(current_year, current_month)[1]
    tabel_type = 'первичный'  # TODO Этого нет в графике
    department_name = 'Кабинет неотложной травматологии и ортопедии (травмпункт)' # TODO это из документа
    date_now = datetime.datetime.now().strftime('%d.%m.%Y') # TODO не актуально
    main_doctor = 'Новожилов В.А.'  # TODO динамически
    head_department = 'Преториус Т.Л.'  # TODO Из документа
    old_sestra = 'Тотьямина Д.С.'  # TODO из документа
    hr_specialist = 'Краснова С.А.'  # TODO не акутально
    organization: Hospitals = request_data.get("hospital")
    organization_title = organization.safe_short_title

    title = [
        Paragraph('', style_center_title),
        Paragraph('', style_center_title),
        Paragraph('', style_center_title),
    ]
    date_month_start = [Paragraph(f'{number_day}', style_center_title) for number_day in range(1, 16)]
    # summ_day_15 = [Paragraph('Итого дней (часов) явок (неявок) с 1-15', style_center_title)]
    date_month_end = [Paragraph(f'{number_day}', style_center_title) for number_day in range(16, last_day_month + 1)]
    summ_all = [
        Paragraph("Количество часов согласно графику", style_center_title),
        Paragraph('Подпись работника', style_center_title),
    ]

    title.extend(date_month_start)
    # title.extend(summ_day_15)
    title.extend(date_month_end)
    title.extend(summ_all)

    opinion = [
        [
            Paragraph('№ п/п', style_center_data),
            Paragraph('Фамилия, имя, отчество', style_center_data),
            Paragraph('Должность (профессия)', style_center_data),
            Paragraph('Числа месяца', style_center_data)
        ],
        title,
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
            col_widths.append(8 * mm)  # для ячейки "№ п/п"
        elif counter == 2:
            col_widths.append(23 * mm)  # для ячейки "ФИО"
        elif counter == 3:
            col_widths.append(19 * mm)  # для ячейки "Должность"
        # elif counter == 19:
        #     col_widths.append(10 * mm)  # для ячейки с 1 по 15ое
        elif counter <= last_day_month + 3:
            col_widths.append(5.8 * mm)  # для ячеек дат
        elif counter == last_day_month + 4:
            col_widths.append(14 * mm)  # для ячейки "кол-во часов согласно графику"
        elif counter == last_day_month + 5:
            col_widths.append(16 * mm)  # для ячейки "Подпись работника"
        counter += 1

    table = create_table(opinion, table_style, col_widths, "LEFT", 1, 3)

    document_data.append(table)

    context = {
        "department_table_number": department_table_number,
        "month_name": month_name,
        "current_year": current_year,
        "first_day_month": first_day_month,
        "last_day_month": last_day_month,
        "date_now": date_now,
        "organization_title": organization_title,
        "department_name": department_name,
        "tabel_type": tabel_type,
        "main_doctor": main_doctor,
        "head_department": head_department,
        "old_sestra": old_sestra,
        "hr_specialist": hr_specialist,
        "style_left": style_left,
        "style_right": style_right,
        "style_center": style_center,
        "style_center_bold": style_center_bold,
        "style_center_title": style_center_title,
        "style_center_sup": style_center_sup,
        "style_right_bold": style_right_bold,
    }

    def first_pages(canvas, doc):
        _create_meta_information(canvas, True, context)

    def later_pages(canvas, doc):
        _create_meta_information(canvas, False, context)

    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=10 * mm, leftMargin=5 * mm, topMargin=56 * mm, bottomMargin=43 * mm, title="График рабочего времени")
    document.build(document_data, first_pages, later_pages)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
