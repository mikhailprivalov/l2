from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, FrameBreak, Table, \
    TableStyle
from reportlab.platypus import PageBreak, NextPageTemplate
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

import datetime
import locale
import sys
import pytils
import os.path
from io import BytesIO

def form_health_passport(fio,born_date):
    """
    generate health passport (Пасспорт здровья)
    :param ind: individual object(объекти физлицо)
    :param t: type form (тип формы)
    :return:
    """
    """
    Ниже блок переменных, заменить из реальных объектов
    """
    hospital_name = "ОГАУЗ \"Иркутская медикосанитарная часть № 2\""
    organization_address = "г. Иркутс, ул. Байкальская 201"
    hospital_kod_ogrn = "1033801542576"
    number_health_passport = "1"  # номер id patient из базы
    individual_sex = "М"
    individual_address = "г.Иркутск, ул. Сибирских-Партизан д. 8 кв. 9"
    document_passport_number = "010503"
    document_passport_serial = "0506"
    document_passport_issued = "УВД Октябрьского р-на г. Братска"
    document_polis_number = "77777777"
    individual_work_organization = "Управление Федераньной службы по ветеринарному и фитосанитрному надзору по Иркутской области" \
                                   "и Усть-Ордынскому бурятскому автономному округу"  # реест организаций
    work_organization_okved = "91.5 - Обслуживание и ремонт компютерной и оргтехники, заправка картриджей" \
                              "обслуживание принтеров"
    individual_department = "отдел информационных технология, ораганизаци ремонта и обслуживания медицинского оборудования"
    individual_profession = "старший государственный таможенный инспектор"  # реест профессий

    list_result = ['Общ. анализ крови', 'Общ.анализ мочи', 'Глюкоза крови', 'Холестерин', 'RW', 'Флюорография', 'ЭКГ',
                   'Спирометрия', 'УЗИ м/желёз (маммогр.)', 'Аудиометрия', 'УЗИ огр.м/таза',
                   'Исслед. вестибулярн. аппарата',
                   'Исслед.вибрационн. чувствительности', 'Острота зрения', 'Рефрактометрия', 'Объём аккомодации',
                   'Исслед.бинокулярн. зрения',
                   'Цветоощущение', 'Офтальмотонометрия', 'Биомикроскопия сред глаза', 'Поля зрения',
                   'Бактериоскопия мазка',
                   'Офтальмоскопия глазного дня', 'Мазок из зева и носа', 'Ретикулоциты', 'АЛК или КП в моче',
                   'Метгемоглобины',
                   'Базальн. Зернист. Эритроцитов'
                   ]  # список лабораторных, инструментальных исследований
    list_doctor = ['Терапевт', 'Психиатр', 'Нарколог', 'Гинеколог', 'Офтальмолог', 'Лор', 'Невролог', 'Дерматолог',
                   'Хирург', 'Стоматолог']  # список врачей-специалистов

    for i in range(0, 3):
        list_doctor.append('')

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    FONTS_FOLDER = 'c:\\tmp\\iq200-pyth\\fonts1\\'
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    # http://www.cnews.ru/news/top/2018-12-10_rossijskim_chinovnikam_zapretili_ispolzovat
    # Причина PTAstraSerif использовать

    buffer = BytesIO()
    individual_fio = fio
    individual_date_born = born_date

    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=10 * mm,
                            rightMargin=10 * mm, topMargin=10 * mm,
                            bottomMargin=10 * mm, allowSplitting=1,
                            title="Форма {}".format("Паспорт здоровья"))
    width, height = landscape(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifBold"
    style.fontSize = 9
    style.leading = 5
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 5.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    righ_frame = Frame(148.5 * mm, 0 * mm, width=148.5 * mm, height=210 * mm,
                       leftPadding=10 * mm, bottomPadding=6, rightPadding=10 * mm, topPadding=6, showBoundary=1)
    left_frame = Frame(0 * mm, 0 * mm, width=148.5 * mm, height=210 * mm,
                       leftPadding=10 * mm, bottomPadding=6, rightPadding=10 * mm, topPadding=6, showBoundary=1)
    doc.addPageTemplates(PageTemplate(id='TwoCol', frames=[righ_frame, left_frame], pagesize=landscape(A4)))

    space = 5.5 * mm
    objs = [
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifBold">Министерство здравоохранения Российской Федерации</font>',
                  styleCenter),
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifBold"><u>{}</u></font>'.format(hospital_name), styleCenter),
        Spacer(1, 2 * mm),
        Paragraph('<font face="PTAstraSerifReg"><font size=9>(наименование медицинской организации)</font></font>',
                  styleCenter),
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifBold"><u>{}</u></font>'.format(organization_address), styleCenter),
        Spacer(1, 5 * mm),
        Paragraph('<font face="PTAstraSerifBold" size=12>Код ОГРН {}</font>'.format(hospital_kod_ogrn), styleCenter),
        Spacer(1, 10 * mm),
        Paragraph('<font face="PTAstraSerifBold" size=12>ПАСПОРТ ЗДОРОВЬЯ РАБОТНИКА № <u>{}</u></font>'.
                  format(number_health_passport), styleCenter),
        Spacer(1, space),
        Paragraph('<font face="PTAstraSerifReg"size=10><u>{} года</u></font>'.
                  format(pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=datetime.datetime.now())),
                  styleCenter),
        Spacer(1, 7),
        Paragraph('<font face="PTAstraSerifReg" size=7>(дата оформления)</font>', styleCenter),
        Spacer(1, space),
        Paragraph('<font face="PTAstraSerifReg">1.Фамилия, имя, отчество:  '
                  '<u>{}</u> </font>'.format(individual_fio), styleJustified),
        Paragraph('<font face="PTAstraSerifReg">2.Пол: <u>{}</u> <img src="forms/img/FFFFFF-space.png" width="90" />'
                  '3.Дата Рождения: <u>{}</u> </font>'.format(individual_sex, individual_date_born), styleJustified),
        Paragraph('<font face="PTAstraSerifReg">4.Паспорт: серия <u>{}</u> <img src="forms/img/FFFFFF-space.png" width="20" />'
                  'номер: <u>{}</u> </font>'.format(document_passport_serial, document_passport_number),
                  styleJustified),
        Paragraph('<font face="PTAstraSerifReg">кем выдан: <u>{}</u></font>'.format(document_passport_issued),
                  styleJustified),
        Paragraph('<font face="PTAstraSerifReg">5. Адрес регистрации по месту жительства (пребывания):'
                  ' <u>{}</u></font>'.format(individual_address), styleJustified),
        Paragraph('<font face="PTAstraSerifReg">6. Номер страхового полиса:'
                  ' <u>{}</u></font>'.format(document_polis_number), styleJustified),
        Paragraph('<font face="PTAstraSerifReg">7. Наименование работодателя:'
                  ' <u>{}</u></font>'.format(individual_work_organization), styleJustified),
        Paragraph('<font face="PTAstraSerifReg">7.1 Форма собственности и вид экономической деятельности '
                  'работодателя по ОКВЭД: <u>{}</u></font>'.format(work_organization_okved), styleJustified),
        Paragraph('<font face="PTAstraSerifReg">7.2  Наименование структурного подразделения (цех, участок, отдел):'
                  ' <u> {} </u></font>'.format(individual_department), styleJustified),
        Paragraph('<font face="PTAstraSerifReg">8. Профессия (должность) (в настоящее время):'
                  ' <u>{}</u></font>'.format(individual_profession), styleJustified),
        FrameBreak(),
        Spacer(1, space),
        Paragraph('<font face="PTAstraSerifReg">12. Заключение:</font>', styleJustified),
    ]
    styleT = deepcopy(style)
    styleT.alignment = TA_CENTER
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    opinion = [
        [Paragraph('<font face="PTAstraSerifReg">Заключение по результатам предварительного '
                   'и периодического медицинского осмотра</font>', styleT),
         Paragraph('<font face="PTAstraSerifReg">Дата получения заключения</font>', styleT),
         Paragraph('<font face="PTAstraSerifReg"> Подпись профпатолога</font>', styleT)],
    ]

    for i in range(0, 5):
        para = [Paragraph('<font face="PTAstraSerifReg" size=11>Профпригоден/\nпрофнепригоден</font>', styleT)]
        opinion.append(para)

    tbl = Table(opinion, colWidths=(48 * mm, 40 * mm, 40 * mm), hAlign='LEFT', style=[
        ('GRID', (0, 0), (-1, -1), 0.7, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),

    ])

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
    objs.append(Paragraph('<font face="PTAstraSerifReg">11. Результаты лабораторных и инструментальных исследований'
                          '</font>', styleJustified))

    tbl_result = [
        [Paragraph('<font face="PTAstraSerifReg" size=11>Вид исследования</font>', styleT),
         Paragraph('<font face="PTAstraSerifReg" size=11>Даты исследований</font>', styleT),
         '', '', '', ''],
        ['', '', '', '', '', '']
    ]

    styleTR = deepcopy(styleT)
    styleTR.alignment = TA_LEFT
    styleTR.fontSize = 11
    styleTR.spaceAfter = 12 * mm

    for i in list_result:
        para = [Paragraph('<font face="PTAstraSerifReg">{}</font>'.format(i), styleTR)]
        tbl_result.append(para)

    tbl = Table(tbl_result, colWidths=(41 * mm, 22 * mm, 17 * mm, 17 * mm, 17 * mm, 17 * mm), hAlign='LEFT', style=[
        ('GRID', (0, 0), (-1, -1), 0.7, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 0.01 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.01 * mm),
        ('LEFTPADDING ', (0, 2), (0, -1), 0.1 * mm),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (-1, 0)),
    ])
    objs.append(tbl)

    objs.append(FrameBreak())
    objs.append(Spacer(1, 7 * mm))
    objs.append(Paragraph('<font face="PTAstraSerifReg">9. Условия труда в настоящее время</font>', styleJustified))

    tbl_result = [
        [Paragraph('<font face="PTAstraSerifReg" size=10>Наименование производственного фактора, вида работы с '
                   'указанием пункта</font>', styleT),
         Paragraph('<font face="PTAstraSerifReg" size=10>Стаж работы с фактором</font>', styleT), ]
    ]
    for i in range(0, 4):
        para = ['', '']
        tbl_result.append(para)

    row_height = []
    for i in tbl_result:
        row_height.append(8 * mm)

    row_height[0] = None
    tbl = Table(tbl_result, colWidths=(75 * mm, 55 * mm), rowHeights=row_height, hAlign='LEFT', style=[
        ('GRID', (0, 0), (-1, -1), 0.7, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 0.01 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.01 * mm),
        ('LEFTPADDING ', (0, 2), (0, -1), 0.1 * mm),
        ('SPAN', (1, 1), (1, -1)),
    ])

    objs.append(tbl)

    objs.append(Spacer(1, 5 * mm))

    styleDoc = deepcopy(styleJustified)
    styleDoc.spaceAfter = 1 * mm
    objs.append(Paragraph('<font face="PTAstraSerifReg">10. Заключения врачей - специалистов:</font>', styleDoc, ))
    tbl_result = [
        [Paragraph('<font face="PTAstraSerifReg" size=11>Врач-специалист</font>', styleT),
         Paragraph('<font face="PTAstraSerifReg" size=11>Даты исследований</font>', styleT),
         '', '', '', ''],
        ['', '', '', '', '', '']
    ]

    for i in list_doctor:
        para = [Paragraph('<font face="PTAstraSerifReg">{}</font>'.format(i), styleTR)]
        tbl_result.append(para)

    row_height = []
    for i in tbl_result:
        row_height.append(9 * mm)

    row_height[0] = None
    row_height[1] = None
    tbl = Table(tbl_result, colWidths=(41 * mm, 22 * mm, 17 * mm, 17 * mm, 17 * mm, 17 * mm), rowHeights=row_height,
                hAlign='LEFT', style=[
            ('GRID', (0, 0), (-1, -1), 0.7, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 0.01 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.01 * mm),
            ('LEFTPADDING ', (0, 2), (0, -1), 0.1 * mm),
            ('SPAN', (0, 0), (0, 1)),
            ('SPAN', (1, 0), (-1, 0)),
        ])
    objs.append(tbl)

    doc.build(objs)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf