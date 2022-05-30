import copy
import datetime
import calendar
import json
import os
from io import BytesIO

import pytils as pytils
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle

from hospitals.models import Hospitals
from time_cards.models import DocumentFactTimeWork
from laboratory.settings import FONTS_FOLDER


pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))


def tabel_52n(request_data):
    data = DocumentFactTimeWork.objects.get(tabel_document_id=1)
    data_json = json.loads(data.data_document)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer,
                            pagesize=landscape(A4),
                            rightMargin=10 * mm,
                            leftMargin=5 * mm,
                            topMargin=56 * mm,
                            bottomMargin=43 * mm,
                            title='Табель учёта рабочего времени')

    style_sheet = getSampleStyleSheet()
    style = style_sheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10
    style.alignment = TA_JUSTIFY

    style_center_bold = copy.deepcopy(style)
    style_center_bold.fontName = "PTAstraSerifBold"
    style_center_bold.fontSize = 10
    style_center_bold.alignment = TA_CENTER

    style_center = copy.deepcopy(style_center_bold)
    style_center.fontName = "PTAstraSerifReg"

    style_left = copy.deepcopy(style)
    style_left.fontSize = 6
    style_left.alignment = TA_LEFT

    style_right = copy.deepcopy(style_left)
    style_right.alignment = TA_RIGHT

    style_right_bold = copy.deepcopy(style_right)
    style_right_bold.fontName = "PTAstraSerifBold"

    style_center_title = copy.deepcopy(style_right)
    style_center_title.alignment = TA_CENTER
    style_center_title.fontSize = 7

    style_center_sup = copy.deepcopy(style_center_title)
    style_center_sup.fontSize = 5

    style_center_data = copy.deepcopy(style_center_sup)
    style_center_data.fontSize = 8

    style_center_data_bold = copy.deepcopy(style_center_sup)
    style_center_data_bold.fontSize = 10
    style_center_data_bold.fontName = "PTAstraSerifBold"

    style_center_data_title = copy.deepcopy(style_center_sup)
    style_center_data_title.alignment = TA_CENTER
    style_center_data_title.fontSize = 7

    objs = []
    department_table_number = 27
    month_name = pytils.dt.ru_strftime(u"%B", inflected=True, date=datetime.datetime.now())
    current_year = datetime.date.today().year
    current_month = datetime.date.today().month
    first_day_month = 1
    last_day_month = calendar.monthrange(current_year, current_month)[1]
    tabel_type = 'первичный'
    department_name = 'Кабинет неотложной травматологии и ортопедии (травмпункт)'
    date_now = datetime.datetime.now().strftime('%d.%m.%Y')
    main_doctor = 'Новожилов В.А.'
    head_department = 'Преториус Т.Л.'
    old_sestra = 'Тотьямина Д.С.'
    hr_specialist = 'Краснова С.А.'
    hospital: Hospitals = request_data["hospital"]
    hospital_name = hospital.safe_short_title

    title = [
        Paragraph('', style_center_data_title),
        Paragraph('', style_center_data_title),
        Paragraph('', style_center_data_title),
    ]
    date_month_start = [Paragraph(f'{x}', style_center_data_title) for x in range(1, 16)]
    summ_day_15 = [Paragraph('Итого дней (часов) явок (неявок) с 1-15', style_center_data_title)]
    date_month_end = [Paragraph(f'{x}', style_center_data_title) for x in range(16, last_day_month+1)]
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

    num = [Paragraph(f'{x}', style_center_data_title) for x in range(1, last_day_month + 10)]

    opinion = [
        [
            Paragraph('Фамилия, имя, отчество', style_center_data),
            Paragraph('Учетный номер', style_center_data),
            Paragraph('Должность (профессия)', style_center_data),
            Paragraph('Числа месяца', style_center_data)
        ],
        title,
        num
    ]

    col_span = []
    start_row = 3
    for data_person in data_json["personData"]:
        row = 0
        for data_employee in data_person["employeeData"]:
            common = []
            fio = data_person["personLastname"] + " " + data_person["personFirstName"] + " " + data_person["personPatronymic"]
            post = data_employee["postTitle"] + " " + data_employee["typePost"]
            common.append(Paragraph(fio, style_center_data))
            common.append(Paragraph(data_employee["tabelNumber"], style_center_data))
            common.append(Paragraph(post, style_center_data_title))
            dates = data_employee["dates"]
            dates.sort()
            tmp_common_hours = ['' for x in range(len(dates))]
            for k, v in data_employee["commonHours"].items():
                pos = dates.index(k)
                tmp_common_hours[pos] = Paragraph(v, style_center_data)
            tmp_common_hours.insert(15, Paragraph('10', style_center_data))
            common.extend(tmp_common_hours)
            common.append(Paragraph('7', style_center_data))
            common.append(Paragraph('46', style_center_data))
            common.append(Paragraph('28', style_center_data))
            common.append(Paragraph('', style_center_data))
            common.append(Paragraph('', style_center_data))
            opinion.append(common)
            row += 1
        col_span.append(('SPAN', (0, start_row), (0, start_row + (row - 1))))
        start_row += row

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
    table_style.extend(col_span)

    col_Widths = []
    counter = 1
    for i in range(1, last_day_month + 10):
        if counter == 1:
            col_Widths.append(23 * mm)
        elif counter == 2:
            col_Widths.append(10 * mm)
        elif counter == 3:
            col_Widths.append(19 * mm)
        elif counter == 19:
            col_Widths.append(10 * mm)
        elif counter <= last_day_month + 4:
            col_Widths.append(5.8 * mm)
        elif counter == last_day_month + 5:
            col_Widths.append(10 * mm)
        elif counter <= last_day_month + 9:
            col_Widths.append(7.5 * mm)
        counter += 1

    tbl = Table(opinion, colWidths=col_Widths, hAlign='LEFT', splitByRow=1, repeatRows=3)
    tbl.setStyle(TableStyle(table_style))

    objs.append(tbl)

    def first_pages(canvas, doc):
        canvas.saveState()
        text = Paragraph('Утв приказом Минфина России <br/> от 30 марта 2015 г. № 52н', style_right_bold)
        text.wrapOn(canvas, 141 * mm, 194 * mm)
        text.drawOn(canvas, 141 * mm, 194 * mm)
        opinion_c = [
            [
                Paragraph('', style_left),
                Paragraph(f'Табель № <u>{department_table_number}</u>', style_center_bold),
                Paragraph('', style_right),
                Paragraph('', style_center_title)
            ],
            [
                Paragraph('', style_left),
                Paragraph('учета использования рабочего времени', style_center),
                Paragraph('', style_right),
                Paragraph('Коды', style_center_title)
            ],
            [
                Paragraph('', style_left),
                Paragraph('', style_center),
                Paragraph('Форма ОКУД', style_right),
                Paragraph('0504421', style_center_title)
            ],
            [
                Paragraph('', style_left),
                Paragraph(f'За период с {first_day_month} по {last_day_month} {month_name} {current_year} года',
                          style_center),
                Paragraph('Дата', style_right),
                Paragraph(f'{date_now}', style_center_title)
            ],
            [
                Paragraph('Учреждение', style_left),
                Paragraph(f'{hospital_name}', style_center),
                Paragraph('по ОКПО', style_right),
                Paragraph('', style_center_title)
            ],
            [
                Paragraph('Структурное подразделение', style_left),
                Paragraph(f'{department_name}', style_center_bold),
                Paragraph('', style_right),
                Paragraph('', style_center_title)
            ],
            [
                Paragraph('Вид табеля', style_left),
                Paragraph(f'{tabel_type}', style_center),
                Paragraph('Номер корректировки', style_right),
                Paragraph('', style_center_title)
            ],
            [
                Paragraph('', style_left),
                Paragraph('(первичный - 0, корректирующий 1,2  и т.д)', style_center_sup),
                Paragraph('Дата формирования документа', style_right),
                Paragraph(f'{date_now}', style_center_title)
            ]
        ]
        table = Table(opinion_c, [30 * mm, 180 * mm, 40 * mm, 25 * mm])
        table.setStyle(
            TableStyle(
                [
                    ('LINEBELOW', (1, 4), (1, 6), 0.75, colors.black),
                    ('GRID', (3, 1), (3, -1), 0.75, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 1),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                    ('BOTTOMTPADDING', (0, 0), (-1, -1), -1),
                    ('TOPPADDING', (0, 0), (-1, -1), -1)
                ]
            )
        )
        table.wrapOn(canvas, 7 * mm, 156 * mm)
        table.drawOn(canvas, 7 * mm, 156 * mm)
        canvas.setFont('PTAstraSerifReg', 8)

        canvas.drawString(11 * mm, 41 * mm, 'Главный врач')
        canvas.drawString(75 * mm, 41 * mm, f'{main_doctor}')

        canvas.line(7 * mm, 40 * mm, 33 * mm, 40 * mm)
        canvas.line(45 * mm, 40 * mm, 101 * mm, 40 * mm)

        canvas.drawString(12 * mm, 37 * mm, '(должность)')
        canvas.drawString(50 * mm, 37 * mm, '(подпись)')

        canvas.drawString(10 * mm, 31 * mm, 'Зав. отделением')
        canvas.drawString(75 * mm, 31 * mm, f'{head_department}')

        canvas.line(7 * mm, 30 * mm, 33 * mm, 30 * mm)
        canvas.line(45 * mm, 30 * mm, 101 * mm, 30 * mm)

        canvas.drawString(12 * mm, 27 * mm, '(должность)')
        canvas.drawString(50 * mm, 27 * mm, '(подпись)')

        canvas.drawString(8 * mm, 21 * mm, 'Старшая медсестра')
        canvas.drawString(75 * mm, 21 * mm, f'{old_sestra}')

        canvas.line(7 * mm, 20 * mm, 33 * mm, 20 * mm)
        canvas.line(45 * mm, 20 * mm, 101 * mm, 20 * mm)

        canvas.drawString(12 * mm, 17 * mm, '(должность)')
        canvas.drawString(50 * mm, 17 * mm, '(подпись)')

        canvas.drawString(10 * mm, 11 * mm, 'Специалист о.к.')
        canvas.drawString(75 * mm, 11 * mm, f'{hr_specialist}')

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

    def later_pages(canvas, doc):
        canvas.saveState()
        text = Paragraph('Утв приказом Минфина России <br/> от 30 марта 2015 г. № 52н', style_right_bold)
        text.wrapOn(canvas, 141 * mm, 198 * mm)
        text.drawOn(canvas, 141 * mm, 198 * mm)
        opinion_c = [
            [
                Paragraph('', style_left),
                Paragraph(f'Табель № <u>{department_table_number}</u>', style_center_bold),
                Paragraph('', style_right),
                Paragraph('', style_center_title)
            ],
            [
                Paragraph('', style_left),
                Paragraph('учета использования рабочего времени', style_center),
                Paragraph('', style_right),
                Paragraph('Коды', style_center_title)
            ],
            [
                Paragraph('', style_left),
                Paragraph('', style_center),
                Paragraph('Форма ОКУД', style_right),
                Paragraph('0504421', style_center_title)
            ],
            [
                Paragraph('', style_left),
                Paragraph(f'За период с {first_day_month} по {last_day_month} {month_name} {current_year} года',
                          style_center),
                Paragraph('Дата', style_right),
                Paragraph(f'{date_now}', style_center_title)
            ],
            [
                Paragraph('Учреждение', style_left),
                Paragraph(f'{hospital_name}', style_center),
                Paragraph('по ОКПО', style_right),
                Paragraph('', style_center_title)
            ],
            [
                Paragraph('Структурное подразделение', style_left),
                Paragraph(f'{department_name}', style_center_bold),
                Paragraph('', style_right),
                Paragraph('', style_center_title)
            ],
            [
                Paragraph('Вид табеля', style_left),
                Paragraph(f'{tabel_type}', style_center),
                Paragraph('Номер корректировки', style_right),
                Paragraph('', style_center_title)
            ],
            [
                Paragraph('', style_left),
                Paragraph('(первичный - 0, корректирующий 1,2  и т.д)', style_center_sup),
                Paragraph('Дата формирования документа', style_right),
                Paragraph(f'{date_now}', style_center_title)
            ]
        ]
        table = Table(opinion_c, [30 * mm, 180 * mm, 40 * mm, 25 * mm])
        table.setStyle(
            TableStyle(
                [
                    ('LINEBELOW', (1, 4), (1, 6), 0.75, colors.black),
                    ('GRID', (3, 1), (3, -1), 0.75, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 1),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                    ('BOTTOMTPADDING', (0, 0), (-1, -1), -1),
                    ('TOPPADDING', (0, 0), (-1, -1), -1)
                ]
            )
        )
        table.wrapOn(canvas, 7 * mm, 160 * mm)
        table.drawOn(canvas, 7 * mm, 160 * mm)
        canvas.setFont('PTAstraSerifReg', 8)

        canvas.drawString(11 * mm, 41 * mm, 'Главный врач')
        canvas.drawString(75 * mm, 41 * mm, f'{main_doctor}')

        canvas.line(7 * mm, 40 * mm, 33 * mm, 40 * mm)
        canvas.line(45 * mm, 40 * mm, 101 * mm, 40 * mm)

        canvas.drawString(12 * mm, 37 * mm, '(должность)')
        canvas.drawString(50 * mm, 37 * mm, '(подпись)')

        canvas.drawString(10 * mm, 31 * mm, 'Зав. отделением')
        canvas.drawString(75 * mm, 31 * mm, f'{head_department}')

        canvas.line(7 * mm, 30 * mm, 33 * mm, 30 * mm)
        canvas.line(45 * mm, 30 * mm, 101 * mm, 30 * mm)

        canvas.drawString(12 * mm, 27 * mm, '(должность)')
        canvas.drawString(50 * mm, 27 * mm, '(подпись)')

        canvas.drawString(8 * mm, 21 * mm, 'Старшая медсестра')
        canvas.drawString(75 * mm, 21 * mm, f'{old_sestra}')

        canvas.line(7 * mm, 20 * mm, 33 * mm, 20 * mm)
        canvas.line(45 * mm, 20 * mm, 101 * mm, 20 * mm)

        canvas.drawString(12 * mm, 17 * mm, '(должность)')
        canvas.drawString(50 * mm, 17 * mm, '(подпись)')

        canvas.drawString(10 * mm, 11 * mm, 'Специалист о.к.')
        canvas.drawString(75 * mm, 11 * mm, f'{hr_specialist}')

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

    doc.build(objs, onFirstPage=first_pages, onLaterPages=later_pages)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
