from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from directions.models import ParaclinicResult, Issledovaniya, Napravleniya
from laboratory.settings import FONTS_FOLDER
from results.prepare_data import text_to_bold
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, SimpleDocTemplate, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from appconf.manager import SettingManager
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape, A5
import os.path
import directory.models as directory
from reportlab.lib.units import mm


def form_04(request_data):
    # Профосомтр
    direction = request_data["dir"]

    buffer = BytesIO()
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=10 * mm, bottomMargin=5 * mm, allowSplitting=1, title="Форма {}".format("Заключение"))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.alignment = TA_JUSTIFY
    style.leading = 15

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"

    hospital_name = SettingManager.get("org_title")
    hospital_address = SettingManager.get("org_address")
    hospital_kod_ogrn = SettingManager.get("org_ogrn")

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    fwb = []
    opinion = [
        [
            Paragraph(f'<font size=10>{hospital_name}<br/>Адрес: {hospital_address}<br/>Код ОГРН: {hospital_kod_ogrn} <br/> </font>', styleT),
            Paragraph('', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [100 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (1, 0), (-1, -1), 35 * mm),
                ('LEFTPADDING', (0, 0), (0, -1), 15 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )

    fwb.append(tbl)
    fwb.append(Spacer(1, 5 * mm))

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 11.5
    styleCenterBold.leading = 15
    styleCenterBold.fontName = 'PTAstraSerifBold'

    patient = Napravleniya.objects.get(pk=direction)
    fio = patient.client.individual.fio()
    fio_short = patient.client.individual.fio(short=True, dots=True)

    iss = Issledovaniya.objects.filter(napravleniye__pk=direction).order_by("research__pk", "research__sort_weight").first()
    if not iss.doc_confirmation:
        return ""

    result = form_04_data_result_(iss)
    work_place, work_position, harmful_factor, type_med_examination, restrictions, med_report, date, department = (
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        ""
    )
    for i in result:
        if i["title"] == "Место работы":
            work_place = i["value"]
        elif i["title"] == "Должность":
            work_position = i["value"]
        elif i["title"] == "Вредный производственный фактор или вид работы":
            harmful_factor = i["value"]
        elif i["title"] == "Тип медосмотра":
            type_med_examination = i["value"]
            if type_med_examination.lower() == 'предварительный':
                type_med_examination = 'предварительного'
            if type_med_examination.lower() == 'периодический':
                type_med_examination = 'периодического'
        elif i["title"] == "Медицинские противопоказания к работе":
            restrictions = i["value"]
        elif i["title"] == "Заключение по приказу N302н":
            med_report = i["value"]
        elif i["title"] == "Дата осмотра":
            date = i["value"]
        elif i["title"] == "Цех, участок ОПУ":
            department = i["value"]

    fwb.append(Paragraph(f'Заключение № {direction}', styleCenterBold))
    fwb.append(Paragraph(f'{type_med_examination} медицинского осмотра (обследования)', styleCenterBold))
    fwb.append(Spacer(1, 8 * mm))
    fwb.append(Paragraph(f'1. Ф.И.О:  {fio}', style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph("2. Место работы:", style))
    fwb.append(Paragraph(f"2.1 Организация (предприятие): {work_place}", style))
    fwb.append(Paragraph(f"2.2 Цех, участок ОПУ: {department}", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f"3 Профессия (должность) (в настоящее время): {work_position}", style))
    fwb.append(Paragraph(f"Вредный производственный фактор или вид работы: {harmful_factor}", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(
        Paragraph(
            f"4. Согласно результатам проведенного <u>{type_med_examination}</u> медицинского осмотра (обследования): "
            f"<u>{restrictions}</u> медицинские противопоказания к работе с вредными и/или опасными веществами и производственными факторами, "
            f"заключение <u>{med_report}</u> ",
            style,
        )
    )

    fwb.append(Spacer(1, 8 * mm))
    fwb.append(Paragraph("Председатель врачебной комиссии ____________________________ (__________)", style))
    fwb.append(Spacer(1, 6 * mm))
    fwb.append(Paragraph('М.П. "___" ________________ 20__ г.', style))
    fwb.append(Spacer(1, 8 * mm))
    fwb.append(Paragraph(f'_______________________({fio_short}) {date} г.', style))
    fwb.append(Paragraph('(подпись работника<br/>освидетельствуемого)', style))

    doc.build(fwb)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_04_data_result_(iss):
    result = []
    title = ''
    title_fields = [
        'Место работы',
        'Должность',
        'Вредный производственный фактор или вид работы',
        'Тип медосмотра',
        'Медицинские противопоказания к работе',
        'Заключение по приказу N302н',
        'Дата осмотра',
        'Цех, участок ОПУ'
    ]
    for group in directory.ParaclinicInputGroups.objects.filter(research=iss.research).order_by("order"):
        results = ParaclinicResult.objects.filter(issledovaniye=iss, field__group=group).exclude(value="").order_by("field__order")
        if results.exists():
            for r in results:
                if r.field.title not in title_fields:
                    continue
                field_type = r.get_field_type()
                v = r.value.replace('<', '&lt;').replace('>', '&gt;').replace("\n", "<br/>")
                v = v.replace('&lt;sub&gt;', '<sub>')
                v = v.replace('&lt;/sub&gt;', '</sub>')
                v = v.replace('&lt;sup&gt;', '<sup>')
                v = v.replace('&lt;/sup&gt;', '</sup>')
                v = text_to_bold(v)
                if field_type == 1:
                    vv = v.split('-')
                    if len(vv) == 3:
                        v = "{}.{}.{}".format(vv[2], vv[1], vv[0])
                if field_type in [11, 13]:
                    v = v.replace("&lt;br/&gt;", " ")
                if r.field.get_title(force_type=field_type) != "":
                    title = r.field.get_title(force_type=field_type).replace('<', '&lt;').replace('>', '&gt;')
                result.append({"title": title, "value": v})
    return result


def form_05(request_data):
    # Роспотребнадзор 058/у
    direction = request_data["dir"]

    buffer = BytesIO()
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    doc = SimpleDocTemplate(buffer, pagesize=landscape(A5), leftMargin=18 * mm, rightMargin=18 * mm, topMargin=6 * mm, bottomMargin=6 * mm, allowSplitting=1, title="Форма {}".format("058/у"))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10
    style.leading = 12
    style.spaceAfter = 0.5 * mm

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"

    styleRight = deepcopy(style)
    styleRight.alignment = TA_RIGHT

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 12
    styleCenter.leading = 7
    styleCenter.spaceAfter = 1 * mm

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 10
    styleCenterBold.face = 'PTAstraSerifBold'

    styleJustified = deepcopy(style)
    styleJustified.fontSize = 9
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.leading = 3 * mm
    styleJustified.firstLineIndent = 5 * mm

    hospital_name = SettingManager.get("org_title")
    hospital_address = SettingManager.get("org_address")
    hospital_kod_ogrn = SettingManager.get("org_ogrn")

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 3.5 * mm

    fwb = []
    opinion = [
        [
            Paragraph('<font size=10>{}<br/>Адрес: {}<br/>ОГРН: {}</font>'.format(hospital_name, hospital_address, hospital_kod_ogrn), styleT),
            Paragraph('<font size=9 >Код формы по ОКУД:<br/>Код организации по ОКПО:<br/>Медицинская документация<br/>Учетная форма N 058/у</font>', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [90 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (1, 0), (-1, -1), 120),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )

    fwb.append(tbl)
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph('ЭКСТРЕННОЕ ИЗВЕЩЕНИЕ<br/>об инфекционном заболевании, пищевом, остром<br/> профессиональном отравлении, необычной реакции на прививку', styleCenterBold))

    dir = Napravleniya.objects.get(pk=direction)
    patient_data = dir.client.get_data_individual()

    iss = Issledovaniya.objects.filter(napravleniye__pk=direction).order_by("research__pk", "research__sort_weight").first()
    if not iss.doc_confirmation:
        return ""

    result = form_05_data_result_(iss)

    for i in result:
        if i["title"] == "Место работы":
            work_place = i["value"]
        elif i["title"] == "Должность":
            work_position = i["value"]
        elif i["title"] == "Дата осмотра":
            date = i["value"]


    temp = ""
    space_symbol = '&nbsp;'
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f'1. Диагноз:  ', style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph(f"2. Фамилия, имя, отчество:  {patient_data['fio']} {space_symbol * 10} 3. Пол: {patient_data['sex']}", style))
    fwb.append(Spacer(1, 1 * mm))
    age = dir.client.individual.age_s(direction=dir)
    fwb.append(Paragraph(f"4. Возраст (для детей до 14 лет - дата рождения): {patient_data['born']} ({age})", style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph(f"5. Адрес, населенный пункт {temp} район улица {temp} дом N {temp} кв. N {temp}", style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph('6. Наименование и адрес места работы (учебы, детского учреждения)', style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph('7. Даты', style))
    fwb.append(Paragraph('заболевания', style))
    fwb.append(Paragraph('первичного обращения (выявления)', style))
    fwb.append(Paragraph('установления диагноза', style))
    fwb.append(Paragraph('последующего посещения детского учреждения, школы', style))
    fwb.append(Paragraph('госпитализации', style))

    fwb.append(PageBreak())
    fwb.append(Paragraph('оборотная сторона ф. N 058/у', styleRight))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph('8. Место госпитализации __________________________________', style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph('9.Если отравление - указать, где оно произошло, чем отравлен пострадавший', style))
    fwb.append(Paragraph('___________________________________', style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph('10. Проведенные первичные противоэпидемические мероприятия и дополнительные сведения', style))
    fwb.append(Paragraph('______________________________________________', style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph('11. Дата и час первичной сигнализации (по телефону и пр.) в СЭС', style))
    fwb.append(Paragraph('______________________________________________', style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph('Фамилия сообщившего __________________', style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph('Кто принял сообщение _________________', style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph('12. Дата и час отсылки извещения _____________________', style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph(f'Подпись пославшего извещение _____________________{iss.doc_confirmation.get_fio()}', style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph('Регистрационный N _______________ в журнале ф. N ______________', style))
    fwb.append(Paragraph('санэпидстанции', style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph('Подпись получившего извещение ________________________', style))
    fwb.append(Spacer(1, 10 * mm))
    fwb.append(Paragraph('Составляется медработником, выявившим при любых обстоятельствах инфекционное заболевание, пищевое отравление, острое профессиональное отравление или подозревающих их, а также при изменении диагноза.', styleJustified))
    fwb.append(Paragraph('Посылается в санэпидстанцию по месту выявления больного не позднее 12 часов с момента обнаружения больного.', styleJustified))
    fwb.append(Paragraph('В случае сообщения об изменении диагноза п.1 извещения указывается измененный диагноз, дата его установления и первоначальный диагноз.', styleJustified))
    fwb.append(Paragraph('Извещение составляется также на случаи укусов, оцарапанья, ослюнения домашними или дикими животными, которые следует рассматривать как подозрение на заболевание бешенством', styleJustified))


    doc.build(fwb)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_05_data_result_(iss):
    result = []
    title = ''
    title_fields = [
        'Место работы',
        'Должность',
        'Дата осмотра',
        'Диагноз основной',
        'Диагноз сопутствующий',
        'Наименование и адрес места работы',
        'Дата заболевания',
        'Дата обращения(выявления)',
        'Дата установления диагноза',
        'Данные анализа',
        'Дата последующего посещения',
        'Дата госпитализации',
        'Место госпитализации',
    ]
    for group in directory.ParaclinicInputGroups.objects.filter(research=iss.research).order_by("order"):
        results = ParaclinicResult.objects.filter(issledovaniye=iss, field__group=group).exclude(value="").order_by("field__order")
        if results.exists():
            for r in results:
                if r.field.title not in title_fields:
                    continue
                field_type = r.get_field_type()
                v = r.value.replace('<', '&lt;').replace('>', '&gt;').replace("\n", "<br/>")
                v = v.replace('&lt;sub&gt;', '<sub>')
                v = v.replace('&lt;/sub&gt;', '</sub>')
                v = v.replace('&lt;sup&gt;', '<sup>')
                v = v.replace('&lt;/sup&gt;', '</sup>')
                v = text_to_bold(v)
                if field_type == 1:
                    vv = v.split('-')
                    if len(vv) == 3:
                        v = "{}.{}.{}".format(vv[2], vv[1], vv[0])
                if field_type in [11, 13]:
                    v = v.replace("&lt;br/&gt;", " ")
                if r.field.get_title(force_type=field_type) != "":
                    title = r.field.get_title(force_type=field_type).replace('<', '&lt;').replace('>', '&gt;')
                result.append({"title": title, "value": v})
    return result
