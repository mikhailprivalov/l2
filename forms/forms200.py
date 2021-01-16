from datetime import datetime, time as dtime
import locale
import os.path
import sys
from copy import deepcopy
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from api.directions.sql_func import get_confirm_direction_pathology
from contracts.models import Company
from directions.models import Napravleniya, Issledovaniya
from hospitals.models import Hospitals
from laboratory.settings import FONTS_FOLDER
from medical_certificates.forms.forms380 import protocol_fields_result
from utils.dates import normalize_date


def form_01(request_data):

    d1 = request_data['date1']
    d2 = request_data['date2']
    company_pk = request_data['company']

    date1 = normalize_date(d1)
    date2 = normalize_date(d2)
    company_objs = Company.objects.get(pk=company_pk)
    d1 = datetime.strptime(date1, '%d.%m.%Y')
    d2 = datetime.strptime(date2, '%d.%m.%Y')
    start_date = datetime.combine(d1, dtime.min)
    end_date = datetime.combine(d2, dtime.max)
    confirm_direction = get_confirm_direction_pathology(start_date, end_date)
    confirm_direction = [i[0] for i in confirm_direction]
    dir_obs = Napravleniya.objects.filter(pk__in=confirm_direction, workplace__icontains=company_objs.title)

    hospital: Hospitals = request_data["hospital"]
    hospital_name = hospital.safe_short_title
    hospital_address = hospital.safe_address
    hospital_kod_ogrn = hospital.safe_ogrn

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=25 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=6 * mm, allowSplitting=1, title="Форма {}".format("025/у"))
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.leading = 15
    style.spaceAfter = 0.5 * mm
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 12
    styleCenter.leading = 7
    styleCenter.spaceAfter = 1 * mm
    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'
    styleCenterBold.borderColor = black
    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    objs = []

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 11
    styleT.leading = 4.5 * mm
    styleT.face = 'PTAstraSerifReg'

    styleTCenter = deepcopy(styleT)
    styleTCenter.alignment = TA_CENTER

    opinion = [
        [
            Paragraph('<font size=11>{}<br/>Адрес: {}<br/></font>'.format(hospital_name, hospital_address), styleT),
            Paragraph('', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [90 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )

    objs.append(tbl)

    opinion = [[Paragraph('Код ОГРН', styleT)]]
    opinion[0].extend([Paragraph(f"{hospital_kod_ogrn[i]}", styleT) for i in range(13)])
    col_width = [6 * mm for i in range(13)]
    col_width.insert(0, 22 * mm)
    tbl = Table(opinion, hAlign='LEFT', rowHeights=6 * mm, colWidths=tuple(col_width))
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (1, 0), (-1, 0), 0.75, colors.black),
                ('LINEABOVE', (0, 0), (0, -1), 0.5, colors.white),
                ('LINEBEFORE', (0, 0), (0, -1), 2.5, colors.white),
                ('LINEBELOW', (0, 0), (0, -1), 1.5, colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5 * mm),
                ('LEFTPADDING', (1, 0), (-1, -1), 1 * mm),
            ]
        )
    )

    objs.append(Spacer(1, 3 * mm))
    objs.append(tbl)

    space_symbol = '&nbsp;'
    objs.append(Spacer(1, 13 * mm))
    objs.append(Paragraph('ЗАКЛЮЧИТЕЛЬНЫЙ АКТ', styleCenterBold))
    objs.append(Paragraph('по  результатам  проведенного  периодического  медицинского  осмотра ', styleCenterBold))
    objs.append(Paragraph('(обследования) работников за 2020 год. ', styleCenterBold))
    objs.append(Spacer(1, 4 * mm))

    objs.append(Paragraph(f'{date2}', styleBold))
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph('Комиссией в составе', style))
    objs.append(Paragraph(f'Председатель  врачебной  комиссии {space_symbol * 10} {hospital_name} Кирилюк К.В.', style))
    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph(f'Врач-терапевт {space_symbol * 10} {hospital_name} Шатурская Л.Е.', style))

    bold_open = '<font fontname ="PTAstraSerifBold">'
    bold_close = '</font>'
    objs.append(Spacer(1, 3 * mm))
    objs.append(
        Paragraph(
            f'Составлен настоящий акт по результатам  проведенного  периодического  медицинского  осмотра (обследования) работников {bold_open}{company_objs.title}{bold_close} '
            f'в период: {bold_open}с {date1}  по {date2}.{bold_close}',
            style,
        )
    )

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('1. Число работников организации (предприятия), цеха:', style))
    objs = all_and_women(objs, styleT)

    objs.append(Spacer(1, 3 * mm))
    objs.append(
        Paragraph('2. Число работников организации (предприятия), цеха, работающих с вредными и (или) опасными веществами и производственными факторами, а так же на работах*:', style)
    )
    objs = all_and_women(objs, styleT)

    objs.append(Spacer(1, 3 * mm))
    objs.append(
        Paragraph(
            '3. Число работников, подлежащих периодическому медицинскому осмотру (обследованию), работающих в контакте с вредными и (или) опасными веществами и '
            'производственными факторами, а так же на работах* в данном году:',
            style,
        )
    )
    objs = all_and_women(objs, styleT)

    objs.append(Spacer(1, 3 * mm))

    people = []
    count = 0
    for dir in dir_obs:
        count += 1
        iss = Issledovaniya.objects.filter(napravleniye=dir).first()
        fio = dir.client.individual.fio()
        patient_data = dir.client.get_data_individual()
        result = protocol_fields_result(iss)
        position, identified_final = '', ''
        for i in result:
            if i["title"] == "Должность":
                position = i["value"]
            elif i["title"] == "Заключение по приказу N302н":
                identified_final = i["value"]
        people.append(
            [
                Paragraph(f'{count}', styleT),
                Paragraph(f'{fio}', styleT),
                Paragraph(f'{patient_data["sex"]}', styleT),
                Paragraph(f'{patient_data["born"]}', styleT),
                Paragraph(f'{position}', styleT),
                Paragraph(f'{identified_final}', styleT),
            ]
        )

    objs.append(Paragraph('4. Число работников, прошедших периодический медицинский осмотр (обследования):', style))
    objs = all_and_women(objs, styleT)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Поименный список работников, завершивших периодический медицинский осмотр ', style))
    opinion = [
        [
            Paragraph('№', styleT),
            Paragraph('Ф.И.О.', styleT),
            Paragraph('пол', styleT),
            Paragraph('Дата рождения', styleT),
            Paragraph('Должность', styleT),
            Paragraph('Заключение', styleT),
        ],
    ]
    opinion.extend(people)
    tbl = Table(
        opinion,
        colWidths=(
            7 * mm,
            80 * mm,
            10 * mm,
            25 * mm,
            30 * mm,
            25 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('5. % охвата периодическими медицинскими осмотрами:', style))
    objs = all_and_women(objs, styleT)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('6. Число работников, не завершивших периодический медицинский осмотр (обследования):', style))
    objs = all_and_women(objs, styleT)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Поименный список работников, не завершивших периодический медицинский осмотр (обследования):', style))
    opinion = [
        [
            Paragraph('№', styleT),
            Paragraph('Ф.И.О.', styleT),
            Paragraph('Подразделение предприятия', styleT),
        ],
        [
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
        ],
    ]
    tbl = Table(
        opinion,
        colWidths=(
            7 * mm,
            120 * mm,
            50 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('7. Число работников, не прошедших периодический медицинский осмотр (обследование):', style))
    opinion = [
        [
            Paragraph('всего,', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('в том числе женщин', styleT),
            Paragraph('-', styleT),
        ],
        [
            Paragraph('в том числе по причине: (медосмотр прошел при переводе, после лечения)', styleT),
            Paragraph('-', styleT),
        ],
        [
            Paragraph('больничный лист', styleT),
            Paragraph('-', styleT),
        ],
        [
            Paragraph('командировка', styleT),
            Paragraph('-', styleT),
        ],
        [
            Paragraph('очередной отпуск', styleT),
            Paragraph('-', styleT),
        ],
        [
            Paragraph('увольнение', styleT),
            Paragraph('-', styleT),
        ],
        [
            Paragraph('отказ от прохождения', styleT),
            Paragraph('-', styleT),
        ],
    ]
    tbl = Table(opinion, colWidths=(150 * mm, 20 * mm))
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Поименный список работников, не прошедших периодический медицинский осмотр (обследование):', style))
    opinion = [
        [
            Paragraph('№', styleT),
            Paragraph('Ф.И.О.', styleT),
            Paragraph('Подразделение предприятия', styleT),
            Paragraph('Причина', styleT),
        ],
        [
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
        ],
    ]
    tbl = Table(
        opinion,
        colWidths=(
            7 * mm,
            80 * mm,
            60 * mm,
            30 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('8. Заключение по результатам данного периодического медицинского осмотра (обследования)', style))
    objs.append(Spacer(1, 1 * mm))
    objs.append(Paragraph('8.1 Сводная таблица N 1:', style))
    opinion = [
        [
            Paragraph('Результаты периодического медицинского осмотра (обследования)', styleT),
            Paragraph('Всего', styleT),
            Paragraph('В том числе женщин', styleT),
        ],
        [
            Paragraph('Число лиц, профпригодных к работе с вредными и (или) опасными веществами и производственными факторами, к видам работ*', styleT),
            Paragraph('-', styleT),
            Paragraph('-', styleT),
        ],
        [
            Paragraph('Число лиц, временно профнепригодных к работе с вредными и (или) опасными веществами и производственными факторами, к видам работ*', styleT),
            Paragraph('-', styleT),
            Paragraph('-', styleT),
        ],
    ]
    tbl = Table(
        opinion,
        colWidths=(
            120 * mm,
            27 * mm,
            27 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs = add_needs_text(objs, 'Число лиц, постоянно профнепригодных к работе с вредными и (или) опасными веществами и производственными факторами, к видам работ*', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц нуждающихся в дообследовании (заключение не дано)', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц с подозрением на профессиональное заболевание', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц, нуждающихся в обследовании в центре профпатологии', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Люди', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц, нуждающихся в амбулаторном обследовании и лечении', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц, нуждающихся в стационарном обследовании и лечении: (оперативное лечение)', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц, нуждающихся в санаторно-курортном лечении', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц, нуждающихся в лечебно-профилактическом питании', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц, нуждающихся в диспансерном наблюдении', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц, нуждающихся в направлении на медико-социальную экспертизу', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs.append(Spacer(1, 5 * mm))
    objs.append(Paragraph('8.3 Выявлено лиц с подозрением на профессиональное заболевание:', style))
    opinion = [
        [
            Paragraph('Nп/п', styleT),
            Paragraph('Ф.И.О.', styleT),
            Paragraph('Подразделение предприятия', styleT),
            Paragraph('Профессия, должность', styleT),
            Paragraph('Вредные и (или) опасные вещества и производственные факторы', styleT),
        ],
    ]
    tbl = Table(
        opinion,
        colWidths=(
            10 * mm,
            90 * mm,
            25 * mm,
            25 * mm,
            25 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 5 * mm))
    objs.append(Paragraph('8.4 Выявлено впервые в жизни хронических соматических заболеваний:', style))
    opinion = [
        [
            Paragraph('№', styleT),
            Paragraph('Класс заболевания по МКБ-10', styleT),
            Paragraph('Количество работников (всего)', styleT),
        ],
    ]
    tbl = Table(
        opinion,
        colWidths=(
            10 * mm,
            130 * mm,
            30 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 5 * mm))
    objs.append(Paragraph('8.5 Выявлено впервые в жизни хронических профессиональных заболеваний:', style))
    opinion = [
        [
            Paragraph('№', styleT),
            Paragraph('Класс заболевания по МКБ-10', styleT),
            Paragraph('Количество работников (всего)', styleT),
        ],
    ]
    tbl = Table(
        opinion,
        colWidths=(
            10 * mm,
            130 * mm,
            30 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 5 * mm))
    objs.append(
        Paragraph('9. Результаты выполнения рекомендаций предыдущего заключительного акта. по результатам проведенного периодического медицинского осмотра (обследования) работников.', style)
    )

    opinion = [
        [
            Paragraph('Nп/п', styleT),
            Paragraph('Мероприятия', styleT),
            Paragraph('Подлежало (чел.)', styleT),
            Paragraph('абс.', styleT),
            Paragraph('в %', styleT),
        ],
        [
            Paragraph('1', styleT),
            Paragraph('Обследование в центре профпатологии', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('2', styleT),
            Paragraph('Дообследование', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('3', styleT),
            Paragraph('Лечение и обследование амбулаторное', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('4', styleT),
            Paragraph('Лечение и обследование стационарное', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('5', styleT),
            Paragraph('Санаторно-курортное лечение', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('6', styleT),
            Paragraph('Диетпитание', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('7', styleT),
            Paragraph('Взято на диспансерное наблюдение', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('8', styleT),
            Paragraph('Направлено на медико-социальную экспертизу', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
        ],
    ]
    tbl = Table(
        opinion,
        colWidths=(
            10 * mm,
            90 * mm,
            25 * mm,
            25 * mm,
            25 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 5 * mm))
    objs.append(
        Paragraph(
            '10. Рекомендации     работодателю:       санитарно-профилактические     и оздоровительные мероприятия и т.п.: Соблюдение режима труда и отдыха; сезонная вакцинация '
            '(грипп; клещевой энцефалит); зарядка на рабочем мест; закаливание; обеспечить возможность и оказать содействие работникам, нуждающимся в прохождении '
            'соответствующего обследования и лечения; обеспечить возможность и оказать содействие работникам , нуждающимся в санаторно – курортном лечении, в прохождении '
            'соответствующего СКЛ; обеспечить возможность и оказать содействие работникам, нуждающимся диспансерном наблюдении, в прохождении соответствующего наблюдения, '
            'обеспечить соблюдение санитарно- гигиенических норм условий труда.',
            style,
        )
    )

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def add_needs_text(objs, text, styleT):
    objs.append(Spacer(1, 7 * mm))
    opinion = [
        [
            Paragraph(f'{text}', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
        ],
    ]
    tbl = Table(opinion, colWidths=(125 * mm, 25 * mm, 25 * mm))
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)
    return objs


def add_fio_spec_diagnosis(objs, styleT):
    objs.append(Spacer(1, 0 * mm))
    opinion = [
        [
            Paragraph('№', styleT),
            Paragraph('Ф.И.О.', styleT),
            Paragraph('Подразделение', styleT),
            Paragraph('Специалист', styleT),
            Paragraph('Диагноз', styleT),
        ]
    ]
    tbl = Table(
        opinion,
        colWidths=(
            10 * mm,
            90 * mm,
            25 * mm,
            25 * mm,
            25 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                # ('LEFTPADDING', (1, 0), (-1, -1), 2 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    return objs


def all_and_women(objs, styleT):
    col_width = (150 * mm, 20 * mm)
    opinion = [
        [
            Paragraph('всего,', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('в том числе женщин,', styleT),
            Paragraph(' ', styleT),
        ],
    ]
    tbl = Table(opinion, colWidths=col_width)
    tbl.setStyle(
        TableStyle(
            [
                ('LEFTPADDING', (1, 0), (-1, -1), 1.5 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 1.5, colors.black),
            ]
        )
    )
    objs.append(tbl)
    return objs


def form_02(request_data):

    d1 = request_data['date1']
    d2 = request_data['date2']
    company_pk = request_data['company']

    date1 = normalize_date(d1)
    date2 = normalize_date(d2)
    company_objs = Company.objects.get(pk=company_pk)
    d1 = datetime.strptime(date1, '%d.%m.%Y')
    d2 = datetime.strptime(date2, '%d.%m.%Y')
    start_date = datetime.combine(d1, dtime.min)
    end_date = datetime.combine(d2, dtime.max)
    confirm_direction = get_confirm_direction_pathology(start_date, end_date)
    confirm_direction = [i[0] for i in confirm_direction]
    dir_obs = Napravleniya.objects.filter(pk__in=confirm_direction, workplace__icontains=company_objs.title)

    hospital: Hospitals = request_data["hospital"]
    hospital_name = hospital.safe_short_title
    hospital_address = hospital.safe_address
    hospital_kod_ogrn = hospital.safe_ogrn

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    




    objs = []

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 11
    styleT.leading = 4.5 * mm
    styleT.face = 'PTAstraSerifReg'

    styleTCenter = deepcopy(styleT)
    styleTCenter.alignment = TA_CENTER

    opinion = [
        [
            Paragraph('<font size=11>{}<br/>Адрес: {}<br/></font>'.format(hospital_name, hospital_address), styleT),
            Paragraph('', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [90 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )

    objs.append(tbl)

    opinion = [[Paragraph('Код ОГРН', styleT)]]
    opinion[0].extend([Paragraph(f"{hospital_kod_ogrn[i]}", styleT) for i in range(13)])
    col_width = [6 * mm for i in range(13)]
    col_width.insert(0, 22 * mm)
    tbl = Table(opinion, hAlign='LEFT', rowHeights=6 * mm, colWidths=tuple(col_width))
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (1, 0), (-1, 0), 0.75, colors.black),
                ('LINEABOVE', (0, 0), (0, -1), 0.5, colors.white),
                ('LINEBEFORE', (0, 0), (0, -1), 2.5, colors.white),
                ('LINEBELOW', (0, 0), (0, -1), 1.5, colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5 * mm),
                ('LEFTPADDING', (1, 0), (-1, -1), 1 * mm),
            ]
        )
    )

    objs.append(Spacer(1, 3 * mm))
    objs.append(tbl)

    space_symbol = '&nbsp;'
    objs.append(Spacer(1, 13 * mm))
    objs.append(Paragraph('ЗАКЛЮЧИТЕЛЬНЫЙ АКТ', styleCenterBold))
    objs.append(Paragraph('по  результатам  проведенного  периодического  медицинского  осмотра ', styleCenterBold))
    objs.append(Paragraph('(обследования) работников за 2020 год. ', styleCenterBold))
    objs.append(Spacer(1, 4 * mm))

    objs.append(Paragraph(f'{date2}', styleBold))
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph('Комиссией в составе', style))
    objs.append(Paragraph(f'Председатель  врачебной  комиссии {space_symbol * 10} {hospital_name} Кирилюк К.В.', style))
    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph(f'Врач-терапевт {space_symbol * 10} {hospital_name} Шатурская Л.Е.', style))

    bold_open = '<font fontname ="PTAstraSerifBold">'
    bold_close = '</font>'
    objs.append(Spacer(1, 3 * mm))
    objs.append(
        Paragraph(
            f'Составлен настоящий акт по результатам  проведенного  периодического  медицинского  осмотра (обследования) работников {bold_open}{company_objs.title}{bold_close} '
            f'в период: {bold_open}с {date1}  по {date2}.{bold_close}',
            style,
        )
    )

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('1. Число работников организации (предприятия), цеха:', style))
    objs = all_and_women(objs, styleT)

    objs.append(Spacer(1, 3 * mm))
    objs.append(
        Paragraph('2. Число работников организации (предприятия), цеха, работающих с вредными и (или) опасными веществами и производственными факторами, а так же на работах*:', style)
    )
    objs = all_and_women(objs, styleT)

    objs.append(Spacer(1, 3 * mm))
    objs.append(
        Paragraph(
            '3. Число работников, подлежащих периодическому медицинскому осмотру (обследованию), работающих в контакте с вредными и (или) опасными веществами и '
            'производственными факторами, а так же на работах* в данном году:',
            style,
        )
    )
    objs = all_and_women(objs, styleT)

    objs.append(Spacer(1, 3 * mm))

    people = []
    count = 0
    for dir in dir_obs:
        count += 1
        iss = Issledovaniya.objects.filter(napravleniye=dir).first()
        fio = dir.client.individual.fio()
        patient_data = dir.client.get_data_individual()
        result = protocol_fields_result(iss)
        position, identified_final = '', ''
        for i in result:
            if i["title"] == "Должность":
                position = i["value"]
            elif i["title"] == "Заключение по приказу N302н":
                identified_final = i["value"]
        people.append(
            [
                Paragraph(f'{count}', styleT),
                Paragraph(f'{fio}', styleT),
                Paragraph(f'{patient_data["sex"]}', styleT),
                Paragraph(f'{patient_data["born"]}', styleT),
                Paragraph(f'{position}', styleT),
                Paragraph(f'{identified_final}', styleT),
            ]
        )

    objs.append(Paragraph('4. Число работников, прошедших периодический медицинский осмотр (обследования):', style))
    objs = all_and_women(objs, styleT)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Поименный список работников, завершивших периодический медицинский осмотр ', style))
    opinion = [
        [
            Paragraph('№', styleT),
            Paragraph('Ф.И.О.', styleT),
            Paragraph('пол', styleT),
            Paragraph('Дата рождения', styleT),
            Paragraph('Должность', styleT),
            Paragraph('Заключение', styleT),
        ],
    ]
    opinion.extend(people)
    tbl = Table(
        opinion,
        colWidths=(
            7 * mm,
            80 * mm,
            10 * mm,
            25 * mm,
            30 * mm,
            25 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('5. % охвата периодическими медицинскими осмотрами:', style))
    objs = all_and_women(objs, styleT)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('6. Число работников, не завершивших периодический медицинский осмотр (обследования):', style))
    objs = all_and_women(objs, styleT)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Поименный список работников, не завершивших периодический медицинский осмотр (обследования):', style))
    opinion = [
        [
            Paragraph('№', styleT),
            Paragraph('Ф.И.О.', styleT),
            Paragraph('Подразделение предприятия', styleT),
        ],
        [
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
        ],
    ]
    tbl = Table(
        opinion,
        colWidths=(
            7 * mm,
            120 * mm,
            50 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('7. Число работников, не прошедших периодический медицинский осмотр (обследование):', style))
    opinion = [
        [
            Paragraph('всего,', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('в том числе женщин', styleT),
            Paragraph('-', styleT),
        ],
        [
            Paragraph('в том числе по причине: (медосмотр прошел при переводе, после лечения)', styleT),
            Paragraph('-', styleT),
        ],
        [
            Paragraph('больничный лист', styleT),
            Paragraph('-', styleT),
        ],
        [
            Paragraph('командировка', styleT),
            Paragraph('-', styleT),
        ],
        [
            Paragraph('очередной отпуск', styleT),
            Paragraph('-', styleT),
        ],
        [
            Paragraph('увольнение', styleT),
            Paragraph('-', styleT),
        ],
        [
            Paragraph('отказ от прохождения', styleT),
            Paragraph('-', styleT),
        ],
    ]
    tbl = Table(opinion, colWidths=(150 * mm, 20 * mm))
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Поименный список работников, не прошедших периодический медицинский осмотр (обследование):', style))
    opinion = [
        [
            Paragraph('№', styleT),
            Paragraph('Ф.И.О.', styleT),
            Paragraph('Подразделение предприятия', styleT),
            Paragraph('Причина', styleT),
        ],
        [
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
        ],
    ]
    tbl = Table(
        opinion,
        colWidths=(
            7 * mm,
            80 * mm,
            60 * mm,
            30 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('8. Заключение по результатам данного периодического медицинского осмотра (обследования)', style))
    objs.append(Spacer(1, 1 * mm))
    objs.append(Paragraph('8.1 Сводная таблица N 1:', style))
    opinion = [
        [
            Paragraph('Результаты периодического медицинского осмотра (обследования)', styleT),
            Paragraph('Всего', styleT),
            Paragraph('В том числе женщин', styleT),
        ],
        [
            Paragraph('Число лиц, профпригодных к работе с вредными и (или) опасными веществами и производственными факторами, к видам работ*', styleT),
            Paragraph('-', styleT),
            Paragraph('-', styleT),
        ],
        [
            Paragraph('Число лиц, временно профнепригодных к работе с вредными и (или) опасными веществами и производственными факторами, к видам работ*', styleT),
            Paragraph('-', styleT),
            Paragraph('-', styleT),
        ],
    ]
    tbl = Table(
        opinion,
        colWidths=(
            120 * mm,
            27 * mm,
            27 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs = add_needs_text(objs, 'Число лиц, постоянно профнепригодных к работе с вредными и (или) опасными веществами и производственными факторами, к видам работ*', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц нуждающихся в дообследовании (заключение не дано)', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц с подозрением на профессиональное заболевание', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц, нуждающихся в обследовании в центре профпатологии', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Люди', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц, нуждающихся в амбулаторном обследовании и лечении', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц, нуждающихся в стационарном обследовании и лечении: (оперативное лечение)', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц, нуждающихся в санаторно-курортном лечении', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц, нуждающихся в лечебно-профилактическом питании', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц, нуждающихся в диспансерном наблюдении', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs = add_needs_text(objs, 'Число лиц, нуждающихся в направлении на медико-социальную экспертизу', styleT)
    objs = add_fio_spec_diagnosis(objs, styleT)

    objs.append(Spacer(1, 5 * mm))
    objs.append(Paragraph('8.3 Выявлено лиц с подозрением на профессиональное заболевание:', style))
    opinion = [
        [
            Paragraph('Nп/п', styleT),
            Paragraph('Ф.И.О.', styleT),
            Paragraph('Подразделение предприятия', styleT),
            Paragraph('Профессия, должность', styleT),
            Paragraph('Вредные и (или) опасные вещества и производственные факторы', styleT),
        ],
    ]
    tbl = Table(
        opinion,
        colWidths=(
            10 * mm,
            90 * mm,
            25 * mm,
            25 * mm,
            25 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 5 * mm))
    objs.append(Paragraph('8.4 Выявлено впервые в жизни хронических соматических заболеваний:', style))
    opinion = [
        [
            Paragraph('№', styleT),
            Paragraph('Класс заболевания по МКБ-10', styleT),
            Paragraph('Количество работников (всего)', styleT),
        ],
    ]
    tbl = Table(
        opinion,
        colWidths=(
            10 * mm,
            130 * mm,
            30 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 5 * mm))
    objs.append(Paragraph('8.5 Выявлено впервые в жизни хронических профессиональных заболеваний:', style))
    opinion = [
        [
            Paragraph('№', styleT),
            Paragraph('Класс заболевания по МКБ-10', styleT),
            Paragraph('Количество работников (всего)', styleT),
        ],
    ]
    tbl = Table(
        opinion,
        colWidths=(
            10 * mm,
            130 * mm,
            30 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 5 * mm))
    objs.append(
        Paragraph('9. Результаты выполнения рекомендаций предыдущего заключительного акта. по результатам проведенного периодического медицинского осмотра (обследования) работников.', style)
    )

    opinion = [
        [
            Paragraph('Nп/п', styleT),
            Paragraph('Мероприятия', styleT),
            Paragraph('Подлежало (чел.)', styleT),
            Paragraph('абс.', styleT),
            Paragraph('в %', styleT),
        ],
        [
            Paragraph('1', styleT),
            Paragraph('Обследование в центре профпатологии', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('2', styleT),
            Paragraph('Дообследование', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('3', styleT),
            Paragraph('Лечение и обследование амбулаторное', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('4', styleT),
            Paragraph('Лечение и обследование стационарное', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('5', styleT),
            Paragraph('Санаторно-курортное лечение', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('6', styleT),
            Paragraph('Диетпитание', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('7', styleT),
            Paragraph('Взято на диспансерное наблюдение', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
        ],
        [
            Paragraph('8', styleT),
            Paragraph('Направлено на медико-социальную экспертизу', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
            Paragraph(' ', styleT),
        ],
    ]
    tbl = Table(
        opinion,
        colWidths=(
            10 * mm,
            90 * mm,
            25 * mm,
            25 * mm,
            25 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    objs.append(tbl)

    objs.append(Spacer(1, 5 * mm))
    objs.append(
        Paragraph(
            '10. Рекомендации     работодателю:       санитарно-профилактические     и оздоровительные мероприятия и т.п.: Соблюдение режима труда и отдыха; сезонная вакцинация '
            '(грипп; клещевой энцефалит); зарядка на рабочем мест; закаливание; обеспечить возможность и оказать содействие работникам, нуждающимся в прохождении '
            'соответствующего обследования и лечения; обеспечить возможность и оказать содействие работникам , нуждающимся в санаторно – курортном лечении, в прохождении '
            'соответствующего СКЛ; обеспечить возможность и оказать содействие работникам, нуждающимся диспансерном наблюдении, в прохождении соответствующего наблюдения, '
            'обеспечить соблюдение санитарно- гигиенических норм условий труда.',
            style,
        )
    )

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf
