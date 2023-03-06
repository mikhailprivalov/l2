import datetime
import locale
import os.path
import sys
from copy import deepcopy
from io import BytesIO

import pytils
from reportlab.lib import colors
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, A5, landscape, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import NextPageTemplate, Indenter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, FrameBreak, Table, TableStyle, PageBreak

from api.patients.views import research_last_result_every_month
from appconf.manager import SettingManager
from clients.models import Card, DispensaryReg, DispensaryRegPlans
from directory.models import DispensaryPlan, Researches
from hospitals.models import Hospitals
from laboratory.settings import FONTS_FOLDER, FORM_100_08_A4_FORMAT
from laboratory.utils import strdate
from statistics_tickets.models import VisitPurpose
from utils.dates import normalize_date
from utils.flowable import InteractiveListBoxField, InteractiveTextField, InteractiveListTypeMedExam
from laboratory.utils import strfdatetime


def form_01(request_data):
    """
    Форма Паспорт здоровья Приказ Министерства здравоохранения и социального развития РФ от 12 апреля 2011 г. N 302н
    """
    ind_card = Card.objects.get(pk=request_data["card_pk"])
    patient_data = ind_card.get_data_individual()

    work_data = patient_data['work_position']
    work_data = work_data.split(';')
    work_department, work_position = "", ""
    if len(work_data) >= 2:
        work_department = work_data[1]

    if len(work_data) >= 1:
        work_position = work_data[0]
    else:
        work_position = work_data

    hospital: Hospitals = request_data["hospital"]

    hospital_name = hospital.title
    hospital_address = hospital.safe_address
    hospital_kod_ogrn = hospital.safe_ogrn

    health_passport_num = request_data["card_pk"]  # номер id patient из базы

    list_result = [
        'Общ. анализ крови',
        'Общ.анализ мочи',
        'Глюкоза крови',
        'Холестерин',
        'RW',
        'Флюорография',
        'ЭКГ',
        'Спирометрия',
        'УЗИ м/желёз (маммогр.)',
        'Аудиометрия',
        'УЗИ огр.м/таза',
        'Исслед. вестибулярн. аппарата',
        'Исслед.вибрационн. чувствительности',
        'Острота зрения',
        'Рефрактометрия',
        'Объём аккомодации',
        'Исслед.бинокулярн. зрения',
        'Цветоощущение',
        'Офтальмотонометрия',
        'Биомикроскопия сред глаза',
        'Поля зрения',
        'Бактериоскопия мазка',
        'Офтальмоскопия глазного дня',
        'Мазок из зева и носа',
        'Ретикулоциты',
        'АЛК или КП в моче',
        'Метгемоглобины',
        'Базальн. Зернист. Эритроцитов',
    ]  # список лабораторных, инструментальных исследований
    list_doctor = ['Терапевт', 'Психиатр', 'Нарколог', 'Гинеколог', 'Офтальмолог', 'Лор', 'Невролог', 'Дерматолог', 'Хирург', 'Стоматолог']  # список врачей-специалистов

    for i in range(0, 3):
        list_doctor.append('')

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=10 * mm, rightMargin=10 * mm, topMargin=10 * mm, bottomMargin=10 * mm, allowSplitting=1, title="Форма {}".format("Паспорт здоровья")
    )
    width, height = landscape(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifBold"
    style.fontSize = 9
    style.leading = 6
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.leading = 1
    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.leading = 10
    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    righ_frame = Frame(148.5 * mm, 0 * mm, width=148.5 * mm, height=210 * mm, leftPadding=10 * mm, bottomPadding=6, rightPadding=10 * mm, topPadding=6, showBoundary=1)
    left_frame = Frame(0 * mm, 0 * mm, width=148.5 * mm, height=210 * mm, leftPadding=10 * mm, bottomPadding=6, rightPadding=10 * mm, topPadding=6, showBoundary=1)
    doc.addPageTemplates(PageTemplate(id='TwoCol', frames=[righ_frame, left_frame], pagesize=landscape(A4)))

    space = 5.5 * mm
    space_symbol = '&nbsp;'

    work_p = patient_data['work_place_db'] if patient_data['work_place_db'] else patient_data['work_place']
    objs = [
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifBold">Министерство здравоохранения Российской Федерации</font>', styleCenter),
        Spacer(1, 5 * mm),
        Paragraph('<font face="PTAstraSerifBold"><u>{}</u></font>'.format(hospital_name), styleCenterBold),
        Spacer(1, 1),
        Paragraph('<font face="PTAstraSerifReg"><font size=9>(наименование медицинской организации)</font></font>', styleCenter),
        Spacer(1, 7 * mm),
        Paragraph('<font face="PTAstraSerifBold"><u>{}</u></font>'.format(hospital_address), styleCenter),
        Spacer(1, 5 * mm),
        Paragraph('<font face="PTAstraSerifBold" size=12>Код ОГРН {}</font>'.format(hospital_kod_ogrn), styleCenter),
        Spacer(1, 10 * mm),
        Paragraph('<font face="PTAstraSerifBold" size=12>ПАСПОРТ ЗДОРОВЬЯ РАБОТНИКА № <u>{}</u></font>'.format(health_passport_num), styleCenter),
        Spacer(1, space),
        Paragraph('<font face="PTAstraSerifReg"size=10><u>{} года</u></font>'.format(pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=datetime.datetime.now())), styleCenter),
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifReg" size=7>(дата оформления)</font>', styleCenter),
        Spacer(1, space),
        Paragraph('<font face="PTAstraSerifReg">1.Фамилия, имя, отчество:' '<u>{}</u> </font>'.format(patient_data['fio']), styleJustified),
        Paragraph(
            '<font face="PTAstraSerifReg">2.Пол: <u>{}</u> <img src="forms/img/FFFFFF-space.png" width="90" />'
            '3.Дата Рождения: <u>{}</u> </font>'.format(patient_data['sex'], patient_data['born']),
            styleJustified,
        ),
        Paragraph(
            '<font face="PTAstraSerifReg">4.Паспорт: серия <u>{}</u> <img src="forms/img/FFFFFF-space.png" width="25"/>'
            'номер: <u>{}</u></font>'.format(patient_data['passport_serial'], patient_data['passport_num']),
            styleJustified,
        ),
        Paragraph('<font face="PTAstraSerifReg">Дата выдачи: <u>{}</u></font>'.format(patient_data['passport_date_start']), styleJustified),
        Paragraph('<font face="PTAstraSerifReg"> Кем Выдан: <u>{}</u></font>'.format(patient_data['passport_issued']), styleJustified),
        Paragraph('<font face="PTAstraSerifReg">5. Адрес регистрации по месту жительства (пребывания):' ' <u>{}</u></font>'.format(patient_data['main_address']), styleJustified),
        Paragraph('<font face="PTAstraSerifReg">6. Номер страхового полиса(ЕНП):' ' <u>{}</u></font>'.format(patient_data['oms']['polis_num']), styleJustified),
        Paragraph('<font face="PTAstraSerifReg">7. Наименование работодателя:' ' <u>{}</u></font>'.format(work_p), styleJustified),
        Paragraph(
            '<font face="PTAstraSerifReg">7.1 Форма собственности и вид экономической деятельности ' 'работодателя по ОКВЭД: <u>{}</u></font>'.format(50 * space_symbol), styleJustified
        ),
        Paragraph('<font face="PTAstraSerifReg">7.2  Наименование структурного подразделения (цех, участок, отдел):<u> {}</u></font>'.format(work_department), styleJustified),
        Paragraph('<font face="PTAstraSerifReg">8. Профессия (должность) (в настоящее время):' ' <u>{}</u></font>'.format(work_position), styleJustified),
        FrameBreak(),
        Spacer(1, space),
        Paragraph('<font face="PTAstraSerifReg">12. Заключение:</font>', styleJustified),
    ]
    styleT = deepcopy(style)
    styleT.alignment = TA_CENTER
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    opinion = [
        [
            Paragraph('<font face="PTAstraSerifReg">Заключение по результатам предварительного ' 'и периодического медицинского осмотра</font>', styleT),
            Paragraph('<font face="PTAstraSerifReg">Дата получения заключения</font>', styleT),
            Paragraph('<font face="PTAstraSerifReg"> Подпись профпатолога</font>', styleT),
        ],
    ]

    for i in range(0, 5):
        para = [Paragraph('<font face="PTAstraSerifReg" size=11>Профпригоден/\nпрофнепригоден</font>', styleT)]
        opinion.append(para)

    tbl = Table(
        opinion,
        colWidths=(48 * mm, 40 * mm, 40 * mm),
        hAlign='LEFT',
        style=[
            ('GRID', (0, 0), (-1, -1), 0.7, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
        ],
    )

    objs.append(tbl)

    objs.append(Spacer(1, 10 * mm))
    objs.append(Paragraph('<font face="PTAstraSerifReg">Для заметок:</font>', styleJustified))

    s = "___________________________________________________________"
    for i in range(0, 6):
        objs.append(Spacer(1, 1 * mm))
        objs.append(Paragraph('<font face="PTAstraSerifReg">{}</font>'.format(s), styleJustified))

    objs.append(NextPageTemplate("TwoCol"))
    objs.append(FrameBreak())
    objs.append(Spacer(1, 7 * mm))
    objs.append(Paragraph('<font face="PTAstraSerifReg">11. Результаты лабораторных и инструментальных исследований' '</font>', styleJustified))

    tbl_result = [
        [
            Paragraph('<font face="PTAstraSerifReg" size=11>Вид исследования</font>', styleT),
            Paragraph('<font face="PTAstraSerifReg" size=11>Даты исследований</font>', styleT),
            '',
            '',
            '',
            '',
        ],
        ['', '', '', '', '', ''],
    ]

    styleTR = deepcopy(styleT)
    styleTR.alignment = TA_LEFT
    styleTR.fontSize = 11
    styleTR.spaceAfter = 12 * mm

    for i in list_result:
        para = [Paragraph('<font face="PTAstraSerifReg">{}</font>'.format(i), styleTR)]
        tbl_result.append(para)

    tbl = Table(
        tbl_result,
        colWidths=(41 * mm, 22 * mm, 17 * mm, 17 * mm, 17 * mm, 17 * mm),
        hAlign='LEFT',
        style=[
            ('GRID', (0, 0), (-1, -1), 0.7, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 0.01 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.01 * mm),
            ('SPAN', (0, 0), (0, 1)),
            ('SPAN', (1, 0), (-1, 0)),
        ],
    )
    objs.append(tbl)

    objs.append(FrameBreak())
    objs.append(Spacer(1, 7 * mm))
    objs.append(Paragraph('<font face="PTAstraSerifReg">9. Условия труда в настоящее время</font>', styleJustified))

    tbl_result = [
        [
            Paragraph('<font face="PTAstraSerifReg" size=10>Наименование производственного фактора, вида работы с ' 'указанием пункта</font>', styleT),
            Paragraph('<font face="PTAstraSerifReg" size=10>Стаж работы с фактором</font>', styleT),
        ]
    ]
    for i in range(0, 4):
        para = ['', '']
        tbl_result.append(para)

    row_height = []
    for i in tbl_result:
        row_height.append(8 * mm)

    row_height[0] = None
    tbl = Table(
        tbl_result,
        colWidths=(75 * mm, 55 * mm),
        rowHeights=row_height,
        hAlign='LEFT',
        style=[
            ('GRID', (0, 0), (-1, -1), 0.7, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 0.01 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.01 * mm),
            ('LEFTPADDING ', (0, 2), (0, -1), 0.1 * mm),
            ('SPAN', (1, 1), (1, -1)),
        ],
    )

    objs.append(tbl)

    objs.append(Spacer(1, 5 * mm))

    styleDoc = deepcopy(styleJustified)
    styleDoc.spaceAfter = 1 * mm
    objs.append(
        Paragraph(
            '<font face="PTAstraSerifReg">10. Заключения врачей - специалистов:</font>',
            styleDoc,
        )
    )
    tbl_result = [
        [
            Paragraph('<font face="PTAstraSerifReg" size=11>Врач-специалист</font>', styleT),
            Paragraph('<font face="PTAstraSerifReg" size=11>Даты исследований</font>', styleT),
            '',
            '',
            '',
            '',
        ],
        ['', '', '', '', '', ''],
    ]

    for i in list_doctor:
        para = [Paragraph('<font face="PTAstraSerifReg">{}</font>'.format(i), styleTR)]
        tbl_result.append(para)

    row_height = []
    for i in tbl_result:
        row_height.append(9 * mm)

    row_height[0] = None
    row_height[1] = None
    tbl = Table(
        tbl_result,
        colWidths=(41 * mm, 22 * mm, 17 * mm, 17 * mm, 17 * mm, 17 * mm),
        rowHeights=row_height,
        hAlign='LEFT',
        style=[
            ('GRID', (0, 0), (-1, -1), 0.7, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 0.01 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.01 * mm),
            ('LEFTPADDING ', (0, 2), (0, -1), 0.1 * mm),
            ('SPAN', (0, 0), (0, 1)),
            ('SPAN', (1, 0), (-1, 0)),
        ],
    )
    objs.append(tbl)

    def first_pages(canvas, document):
        canvas.saveState()
        canvas.restoreState()

    def later_pages(canvas, document):
        canvas.saveState()
        canvas.restoreState()

    doc.build(objs, onFirstPage=first_pages, onLaterPages=later_pages)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def form_02(request_data):
    """
    Форма 025/у - титульный лист амбулаторной карты
    Приказ Минздрава России от 15.12.2014 N 834н (ред. от 09.01.2018)
    http://docs.cntd.ru/document/436733768 Об утверждении критериев оценки качества медицинской помощи
    ПРИКАЗ Минздрава России от 10 мая 2017 года N 203н https://minjust.consultant.ru/documents/35361
    """
    ind_card = Card.objects.get(pk=request_data["card_pk"])
    patient_data = ind_card.get_data_individual()
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
    style.fontSize = 10
    style.leading = 12
    style.spaceAfter = 0.5 * mm
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 12
    styleCenter.leading = 15
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
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm
    styleT.face = 'PTAstraSerifReg'

    print_district = ''
    if SettingManager.get("district", default='True', default_type='b'):
        if ind_card.district is not None:
            print_district = 'Уч: {}'.format(ind_card.district.title)

    opinion = [
        [
            Paragraph('<font size=11>{}<br/>Адрес: {}<br/>ОГРН: {} <br/><u>{}</u> </font>'.format(hospital_name, hospital_address, hospital_kod_ogrn, print_district), styleT),
            Paragraph('<font size=9 >Код формы по ОКУД:<br/>Код организации по ОКПО: 31348613<br/>' 'Медицинская документация<br/>Учетная форма № 025/у</font>', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [90 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (1, 0), (-1, -1), 80),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )

    objs.append(tbl)
    space_symbol = '&nbsp;'
    if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i'):
        patient_data['serial'] = patient_data['bc_serial']
        patient_data['num'] = patient_data['bc_num']
    else:
        patient_data['serial'] = patient_data['passport_serial']
        patient_data['num'] = patient_data['passport_num']

    p_phone = ''
    if patient_data['phone']:
        p_phone = 'тел. ' + ", ".join(patient_data['phone'])

    card_num_obj = patient_data['card_num'].split(' ')
    p_card_num = card_num_obj[0]
    if len(card_num_obj) == 2:
        p_card_type = '(' + str(card_num_obj[1]) + ')'
    else:
        p_card_type = ''
    content_title = [
        Indenter(left=0 * mm),
        Spacer(1, 1 * mm),
        Paragraph('МЕДИЦИНСКАЯ КАРТА ПАЦИЕНТА, <br/> ПОЛУЧАЮЩЕГО МЕДИЦИНСКУЮ ПОМОЩЬ В АМБУЛАТОРНЫХ УСЛОВИЯХ', styleCenter),
        Paragraph(
            '{}<font size=14>№</font><font fontname="PTAstraSerifBold" size=17> <u>{}</u></font><font size=14> {}</font>'.format(3 * space_symbol, p_card_num, p_card_type), styleCenter
        ),
        Spacer(1, 2 * mm),
        Paragraph('1.Дата заполнения медицинской карты: {}'.format(pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=datetime.datetime.now())), style),
        Paragraph("2. Фамилия, имя, отчество:&nbsp;  <font size=11.7 fontname ='PTAstraSerifBold'> {} </font> ".format(patient_data['fio']), style),
        Paragraph('3. Пол: {} {} 4. Дата рождения: {}'.format(patient_data['sex'], 3 * space_symbol, patient_data['born']), style),
        Paragraph('5. Место регистрации: {}'.format(patient_data['main_address']), style),
        Paragraph('{}'.format(p_phone), style),
        Paragraph('6. Местность: городская — 1, сельская — 2', style),
        Paragraph(
            '7. Полис ОМС: серия {} №: {} {}' '8. СНИЛС: {}'.format(patient_data['oms']['polis_serial'], patient_data['oms']['polis_num'], 13 * space_symbol, patient_data['snils']), style
        ),
        Paragraph('9. Наименование страховой медицинской организации: {}'.format(patient_data['oms']['polis_issued']), style),
        Paragraph(
            '10. Код категории льготы: {} {} 11. Документ: {} &nbsp; серия: {} &nbsp;&nbsp; №: {}'.format(
                8 * space_symbol, 25 * space_symbol, patient_data['type_doc'], patient_data['serial'], patient_data['num']
            ),
            style,
        ),
    ]

    objs.extend(content_title)
    if SettingManager.get("dispensary", default='True', default_type='b'):
        objs.append(Paragraph('12. Заболевания, по поводу которых осуществляется диспансерное наблюдение:', style))
        objs.append(Spacer(1, 2 * mm))

        styleTCenter = deepcopy(styleT)
        styleTCenter.alignment = TA_CENTER
        styleTCenter.leading = 3.5 * mm

        opinion = [
            [
                Paragraph('<font size=9>Дата начала диспансерного наблюдения </font>', styleTCenter),
                Paragraph('<font size=9 >Дата прекращения диспансерного наблюдения</font>', styleTCenter),
                Paragraph('<font size=9 >Диагноз</font>', styleTCenter),
                Paragraph('<font size=9 >Код по МКБ-10</font>', styleTCenter),
                Paragraph('<font size=9 >Врач</font>', styleTCenter),
            ],
        ]
        for i in range(0, 5):
            para = ['', '', '', '', '']
            opinion.append(para)

        row_height = []
        for i in opinion:
            row_height.append(6 * mm)

        row_height[0] = None

        tbl = Table(opinion, colWidths=(27 * mm, 30 * mm, 75 * mm, 20 * mm, 27 * mm), rowHeights=row_height)

        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                    ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                ]
            )
        )

        objs.append(tbl)

    def first_pages(canvas, document):
        canvas.saveState()
        canvas.restoreState()

    def later_pages(canvas, document):
        canvas.saveState()
        canvas.restoreState()

    doc.build(objs, onFirstPage=first_pages, onLaterPages=later_pages)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_03(request_data):
    """
    Форма - титульный лист для Профосомтров амбулаторной карты
    """
    ind_card = Card.objects.get(pk=request_data["card_pk"])
    patient_data = ind_card.get_data_individual()

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
    if FORM_100_08_A4_FORMAT:
        doc = SimpleDocTemplate(
            buffer, pagesize=portrait(A4), leftMargin=25 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=6 * mm, allowSplitting=1, title="Форма {}".format("Профосомотры")
        )
    else:
        doc = SimpleDocTemplate(
            buffer, pagesize=landscape(A5), leftMargin=25 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=6 * mm, allowSplitting=1, title="Форма {}".format("Профосомотры")
        )
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12 if FORM_100_08_A4_FORMAT else 10
    style.leading = 12
    style.spaceAfter = 0.5 * mm
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 12
    styleCenter.leading = 15
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
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm
    styleT.face = 'PTAstraSerifReg'

    print_district = ''
    if SettingManager.get("district", default='True', default_type='b'):
        if ind_card.district is not None:
            print_district = 'Уч: {}'.format(ind_card.district.title)

    opinion = [
        [
            Paragraph('<font size=11>{}<br/>Адрес: {}<br/>ОГРН: {} <br/><u>{}</u> </font>'.format(hospital_name, hospital_address, hospital_kod_ogrn, print_district), styleT),
            Paragraph('', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [90 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (1, 0), (-1, -1), 80),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )

    objs.append(tbl)
    space_symbol = '&nbsp;'
    if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i'):
        patient_data['serial'] = patient_data['bc_serial']
        patient_data['num'] = patient_data['bc_num']
    else:
        patient_data['serial'] = patient_data['passport_serial']
        patient_data['num'] = patient_data['passport_num']

    p_phone = ''
    if patient_data['phone']:
        p_phone = 'тел. ' + ", ".join(patient_data['phone'])

    p_number_poliklinika = ''
    if patient_data['number_poliklinika']:
        p_number_poliklinika = "" + patient_data['number_poliklinika']

    card_num_obj = patient_data['card_num'].split(' ')
    p_card_num = card_num_obj[0]
    if len(card_num_obj) == 2:
        p_card_type = '(' + str(card_num_obj[1]) + ')'
    else:
        p_card_type = ''
    content_title = [
        Indenter(left=0 * mm),
        Spacer(1, 1 * mm),
        Paragraph('МЕДИЦИНСКАЯ КАРТА ПАЦИЕНТА, <br/> ПОЛУЧАЮЩЕГО МЕДИЦИНСКУЮ ПОМОЩЬ В АМБУЛАТОРНЫХ УСЛОВИЯХ', styleCenter),
        Paragraph(
            '{}<font size=14>№</font><font fontname="PTAstraSerifBold" size=17> {}</font><font size=14> {}</font> {}{}'.format(
                3 * space_symbol, p_card_num, p_card_type, 40 * space_symbol, p_number_poliklinika
            ),
            styleCenter,
        ),
        Spacer(1, 2 * mm),
        Paragraph('1.Дата заполнения медицинской карты: {}'.format(pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=datetime.datetime.now())), style),
        Paragraph("2. Фамилия, имя, отчество:&nbsp;  <font size=11.7 fontname ='PTAstraSerifBold'> {} </font> ".format(patient_data['fio']), style),
        Paragraph('3. Пол: {} {} 4. Дата рождения: {}'.format(patient_data['sex'], 3 * space_symbol, patient_data['born']), style),
        Paragraph('5. Место регистрации: {}'.format(patient_data['main_address']), style),
        Paragraph('{}'.format(p_phone), style),
        Paragraph('6. Местность: городская — 1, сельская — 2', style),
        Paragraph(
            '7. Полис ОМС: серия {} №: {} {}' '8. СНИЛС: {}'.format(patient_data['oms']['polis_serial'], patient_data['oms']['polis_num'], 13 * space_symbol, patient_data['snils']), style
        ),
        Paragraph('9. Наименование страховой медицинской организации: {}'.format(patient_data['oms']['polis_issued']), style),
        Paragraph('10. Документ: {} &nbsp; серия: {} &nbsp;&nbsp; №: {}'.format(patient_data['type_doc'], patient_data['serial'], patient_data['num']), style),
    ]

    objs.extend(content_title)

    work_p = patient_data['work_place_db'] if patient_data['work_place_db'] else patient_data['work_place']
    if FORM_100_08_A4_FORMAT:
        objs.append(Paragraph(f'11. Место работы: <font fontname="PTAstraSerifBold" size=12> {work_p}</font>', style))
    else:
        objs.append(Paragraph(f"11. Место работы: {work_p}", style))
    objs.append(Paragraph(f"12. Должность: {patient_data['work_position']}", style))
    objs.append(Paragraph(f"13. Вредность: {patient_data['harmful_factor']}", style))

    opinion = [
        [Paragraph('14. Прикрепление', style), InteractiveTextField(width=140 * mm, fontsize=10, height=5 * mm)],
    ]
    tbl = Table(opinion, colWidths=(40 * mm, 140 * mm), spaceBefore=0 * mm)
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (1, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (0, 0), 4.5),
                ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ]
        )
    )
    objs.append(tbl)
    objs.append(Spacer(1, 7 * mm))
    objs.append(InteractiveListBoxField())
    objs.append(Spacer(1, 10 * mm))
    objs.append(InteractiveListTypeMedExam())

    def first_pages(canvas, document):
        canvas.saveState()
        canvas.restoreState()

    def later_pages(canvas, document):
        canvas.saveState()
        canvas.restoreState()

    doc.build(objs, onFirstPage=first_pages, onLaterPages=later_pages)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_04(request_data):
    """
    Форма 030/у - контрольная карта диспансерного учета
    """
    reg_dipensary = DispensaryReg.objects.get(pk=request_data["reg_pk"])
    ind_card = reg_dipensary.card
    patient_data = ind_card.get_data_individual()

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
    # doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=25 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=6 * mm, allowSplitting=1, title="Форма {}".format("025/у"))
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A5), leftMargin=25 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=6 * mm, allowSplitting=1, title="Форма {}".format("030/у"))
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10
    style.leading = 12
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
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm
    styleT.face = 'PTAstraSerifReg'

    styleTCenter = deepcopy(styleT)
    styleTCenter.alignment = TA_CENTER

    print_district = ''
    if SettingManager.get("district", default='True', default_type='b'):
        if ind_card.district is not None:
            print_district = 'Уч: {}'.format(ind_card.district.title)

    opinion = [
        [
            Paragraph('<font size=11>{}<br/>Адрес: {}<br/>ОГРН: {} <br/><u>{}</u> </font>'.format(hospital_name, hospital_address, hospital_kod_ogrn, print_district), styleT),
            Paragraph('<font size=9 >Код формы по ОКУД:<br/>Код организации по ОКПО:<br/>' 'Медицинская документация<br/>Учетная форма N 030/у</font>', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [90 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (1, 0), (-1, -1), 80),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )

    objs.append(tbl)
    space_symbol = '&nbsp;'
    if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i'):
        patient_data['serial'] = patient_data['bc_serial']
        patient_data['num'] = patient_data['bc_num']
    else:
        patient_data['serial'] = patient_data['passport_serial']
        patient_data['num'] = patient_data['passport_num']

    card_num_obj = patient_data['card_num'].split(' ')
    p_card_num = card_num_obj[0]
    if len(card_num_obj) == 2:
        p_card_type = '(' + str(card_num_obj[1]) + ')'
    else:
        p_card_type = ''

    diagnos = reg_dipensary.diagnos
    illnes = reg_dipensary.illnes
    doctor = reg_dipensary.doc_start_reg
    doc_speciality = "____________________"
    if doctor.specialities:
        doc_speciality = f"<u>{doctor.specialities.title}</u>"
    doc_fio = doctor.get_full_fio()
    date_start = reg_dipensary.date_start
    date_start = strdate(date_start, short_year=True)
    date_start = normalize_date(date_start)

    date_end = reg_dipensary.date_end
    if date_end:
        date_end = strdate(date_end, short_year=True)
        date_end = normalize_date(date_end)
    else:
        date_end = ""

    why_stop = reg_dipensary.why_stop

    if reg_dipensary.what_times == 1:
        what_times = "впервые - 1"
    elif reg_dipensary.what_times == 2:
        what_times = "повторно - 2"
    else:
        what_times = "впервые - 1, повторно - 2"

    if reg_dipensary.how_identified == 1:
        how_identified = "обращении за лечением - 1"
    elif reg_dipensary.how_identified == 2:
        how_identified = "профилактическом осмотре - 2"
    else:
        how_identified = "обращении за лечением - 1, профилактическом осмотре - 2"

    content_title = [
        Indenter(left=0 * mm),
        Spacer(1, 1 * mm),
        Paragraph('КОНТРОЛЬНАЯ КАРТА, ', styleCenter),
        Paragraph(
            'ДИСПАНСЕРНОГО НАБЛЮДЕНИЯ {}<font size=14>№</font><font fontname="PTAstraSerifBold" size=17> <u>{}</u></font><font size=14> {}</font>'.format(
                3 * space_symbol, p_card_num, p_card_type
            ),
            styleCenter,
        ),
        Spacer(1, 7 * mm),
        Paragraph(f'1. Диагноз заболевания, по поводу которого пациент подлежит диспансерному наблюдению: <u>{illnes}</u> Код по МКБ-10: <u>{diagnos}</u>', style),
        Paragraph('2.Дата заполнения медицинской карты: _____________________', style),
        Paragraph(f'3. Специальность врача: {doc_speciality} {4 * space_symbol} 4.ФИО врача: <u>{doc_fio}</u>', style),
        Paragraph(f'5. Дата установления диагноза: <u>{date_start}</u> {4 * space_symbol} 6. Диагноз установлен: {what_times}', style),
        Paragraph(f'7. Заболевание выявлено при: {how_identified}', style),
        Paragraph(f'8. Дата начала диспансерного наблюдения <u>{date_start}</u> {4 * space_symbol} 9. Дата прекращения диспансерного наблюдения {date_end}', style),
        Paragraph(f'10. Причины прекращения диспансерного наблюдения: <u>{why_stop}</u>', style),
        Paragraph("11. Фамилия, имя, отчество:&nbsp;  <font size=11.7 fontname ='PTAstraSerifBold'> {} </font> ".format(patient_data['fio']), style),
        Paragraph('12. Пол: {} {} 13. Дата рождения: {}'.format(patient_data['sex'], 3 * space_symbol, patient_data['born']), style),
        Paragraph('14. Место регистрации: {}'.format(patient_data['main_address']), style),
        Paragraph('15. Код категории льготы:__________', style),
    ]

    objs.extend(content_title)
    objs.append(Spacer(1, 5 * mm))

    research_need = DispensaryPlan.objects.filter(diagnos=diagnos).order_by('research__title', 'speciality__title')
    researches_list = []
    specialities_list = []
    visits_result = ""
    visits_plan = ""
    visits_research = VisitPurpose.objects.filter(title__icontains="диспансерн")

    current_year = datetime.datetime.now().year
    year = request_data.get('year', current_year)
    for i in research_need:
        if i.speciality:
            results = research_last_result_every_month(Researches.objects.filter(speciality=i.speciality), ind_card, year, visits_research)
            dates_result = ""
            dates_plan = ""
            plans = DispensaryRegPlans.objects.filter(card=ind_card, research=None, speciality=i.speciality, date__year=year).order_by('date')
            for p in plans:
                dates_plan = f"{dates_plan} {strfdatetime(p.date, '%d.%m')};"
            for r in range(12):
                if results[r]:
                    if r < 9:
                        dates_result = f"{dates_result} {results[r]['date']}.0{r + 1};"
                    else:
                        dates_result = f"{dates_result} {results[r]['date']}.{r + 1};"
            if i.is_visit:
                visits_result = dates_result
                visits_plan = dates_plan
            else:
                specialities_list.append(f'{i.speciality.title}-{dates_plan}-{dates_result}')
        if i.research:
            dates_plan = " "
            plans = DispensaryRegPlans.objects.filter(card=ind_card, research=None, speciality=i.speciality, date__year=year).order_by('date')
            for p in plans:
                dates_plan = f"{dates_plan} {strfdatetime(p.date, '%d.%m')};"
            results = research_last_result_every_month([i.research], ind_card, year)
            dates_result = ""
            for r in range(12):
                if results[r]:
                    if r < 9:
                        dates_result = f"{dates_result} {results[r]['date']}.0{r + 1};"
                    else:
                        dates_result = f"{dates_result} {results[r]['date']}.{r + 1};"
            researches_list.append(f'{i.research.title}-{dates_plan}-{dates_result}')

    researches_list.extend(specialities_list)
    visits_result = visits_result.split(';')[:-1]
    visits_plan = visits_plan.split(';')[:-1]
    visits_plan = [Paragraph(i, styleT) for i in visits_plan]
    if len(visits_plan) < 7:
        for i in range(7 - len(visits_plan)):
            visits_plan.append(Paragraph('', styleT))
    visits_plan.insert(0, Paragraph('Назначено явиться', styleT))

    visits_result = [Paragraph(i, styleT) for i in visits_result]
    if len(visits_result) < 7:
        for i in range(7 - len(visits_result)):
            visits_result.append(Paragraph('', styleT))
    visits_result.insert(0, Paragraph('Явился(лась)', styleT))

    opinion = [
        [
            Paragraph('Даты посещений', styleTCenter),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
        ],
        visits_plan,
        visits_result,
    ]

    tbl = Table(opinion, colWidths=(40 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm))
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('SPAN', (0, 0), (-1, 0)),
            ]
        )
    )
    objs.append(tbl)
    objs.append(PageBreak())
    objs.append(Paragraph('оборотная сторона ф. N 030/у', style))
    objs.append(Spacer(1, 5 * mm))

    visit_date = [Paragraph('', styleT) for i in range(7)]
    visit_date.insert(0, Paragraph('Даты посещений', styleTCenter))
    visits_plan = [Paragraph('', styleT) for i in range(7)]
    visits_plan.insert(0, Paragraph('Назначено явиться', styleT))
    visits_result = [Paragraph('', styleT) for i in range(7)]
    visits_result.insert(0, Paragraph('Явился(лась)я', styleT))

    opinion = [visit_date, visits_plan, visits_result]

    tbl = Table(opinion, colWidths=(40 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm))
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('SPAN', (0, 0), (-1, 0)),
            ]
        )
    )

    objs.append(tbl)
    objs.append(Spacer(1, 5 * mm))
    objs.append(Paragraph('17. Сведения об изменении диагноза', style))
    objs.append(Spacer(1, 2 * mm))
    empty_para = [Paragraph('', styleT) for i in range(4)]
    opinion = [
        [
            Paragraph('Дата', styleTCenter),
            Paragraph('Формулировка диагноза', styleT),
            Paragraph('Код по МКБ-10', styleT),
            Paragraph('ФИО врача', styleT),
        ],
        empty_para,
        empty_para,
    ]
    tbl = Table(opinion, colWidths=(30 * mm, 85 * mm, 30 * mm, 35 * mm), rowHeights=6 * mm)
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
            ]
        )
    )
    objs.append(tbl)
    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('18. Сопутствующие заболевания ______________________________________________________________________', style))
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph('___________________________________________________________________________________________________', style))
    objs.append(Spacer(1, 1 * mm))
    objs.append(Paragraph('19. Лечебно-профилактические мероприятия', style))

    opinion_title = [
        Paragraph('N п/п', styleT),
        Paragraph('Мероприятия', styleT),
        Paragraph('Дата<br/> начала', styleT),
        Paragraph('Дата<br/>окончания', styleT),
        Paragraph('Отметка о<br/>выполнении', styleT),
        Paragraph('ФИО врача', styleT),
    ]

    opinion = [['', Paragraph(f'{i.split("-")[0]}', styleT), '', Paragraph(f'{i.split("-")[2]}', styleT), ''] for i in researches_list]
    opinion.insert(0, opinion_title)

    tbl = Table(opinion, colWidths=(10 * mm, 60 * mm, 25 * mm, 25 * mm, 23 * mm, 35 * mm))
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
            ]
        )
    )
    objs.append(tbl)

    def first_pages(canvas, document):
        canvas.saveState()
        canvas.restoreState()

    def later_pages(canvas, document):
        canvas.saveState()
        canvas.restoreState()

    doc.build(objs, onFirstPage=first_pages, onLaterPages=later_pages)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf
