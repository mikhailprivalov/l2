from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from directions.models import ParaclinicResult, Issledovaniya, Napravleniya
from hospitals.models import Hospitals
from laboratory.settings import FONTS_FOLDER
from laboratory.utils import strfdatetime
from results.prepare_data import text_to_bold, fields_result_only_title_fields
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, SimpleDocTemplate, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape, A5, portrait
import os.path
import directory.models as directory
from reportlab.lib.units import mm
from utils.common import get_system_name
import json
from utils.dates import normalize_date
from utils.xh import show_qr_lk_address


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

    hospital: Hospitals = request_data["hospital"]

    hospital_name = hospital.safe_short_title
    hospital_address = hospital.safe_address
    hospital_kod_ogrn = hospital.safe_ogrn

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    fwb = []
    opinion = [
        [
            Paragraph(f'<font size=10>{hospital_name}<br/>Адрес: {hospital_address}<br/></font>', styleT),
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

    opinion = [
        [
            Paragraph('Код ОГРН', styleT),
            Paragraph(f"{hospital_kod_ogrn[0]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[1]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[2]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[3]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[4]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[5]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[6]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[7]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[8]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[9]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[10]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[11]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[12]}", styleT),
        ],
    ]
    fwb.append(tbl)
    col_width = [6 * mm for i in range(13)]
    col_width.insert(0, 21 * mm)
    tbl = Table(opinion, hAlign='LEFT', rowHeights=6 * mm, colWidths=tuple(col_width))
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (0, 0), 0.75, colors.white),
                ('GRID', (1, 0), (-1, -1), 0.75, colors.black),
                ('LEFTPADDING', (1, 0), (-1, -1), 2 * mm),
                ('LEFTPADDING', (0, 0), (0, -1), 1 * mm),
                ('LEFTPADDING', (0, 0), (0, 0), 3 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5 * mm),
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
    if not iss.time_confirmation:
        return ""

    result = protocol_fields_result(iss)
    work_place, work_position, harmful_factor, type_med_examination, restrictions, med_report, date, department, recommendation = ("", "", "", "", "", "", "", "", "")
    dispensary_group = "__________________________________________________________"
    name_disease = "____________________________________________________"
    patalogy, type_med_examination_padeg = "", ""
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
                type_med_examination_padeg = 'предварительного'
            if type_med_examination.lower() == 'периодический':
                type_med_examination_padeg = 'периодического'
        elif i["title"] == "Медицинские противопоказания к работе":
            restrictions = i["value"]
        elif i["title"] == "Заключение по приказу N302н":
            med_report = i["value"]
        elif i["title"] == "Дата осмотра":
            date = i["value"]
        elif i["title"] == "Цех, участок ОПУ":
            department = i["value"]
        elif i["title"] == "Рекомендации":
            recommendation = i["value"]
        elif i["title"] == "Диспансерная группа":
            dispensary_group = i["value"]
        elif i["title"] == "Наименование заболевания":
            name_disease = i["value"]
        elif i["title"] == "Патология":
            patalogy = i["value"]
        elif i["title"] == "Группа здоровья":
            tmp_json = json.loads(i["value"])
            dispensary_group = tmp_json["title"]

    fwb.append(Paragraph('Медицинское заключение по результатам', styleCenterBold))
    fwb.append(Paragraph(f'{type_med_examination_padeg} медицинского осмотра (обследования) № {direction}', styleCenterBold))
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
    fwb.append(Paragraph(f"4. <u>{type_med_examination.capitalize()}</u> медицинский осмотр (обследование)", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(
        Paragraph(
            f"5. Согласно результатам проведенного <u>{type_med_examination_padeg}</u> медицинского осмотра (обследования): "
            f"<u>{restrictions}</u> медицинские противопоказания к работе с вредными и/или опасными веществами и производственными факторами заключение <u>{med_report}</u> ",
            style,
        )
    )
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(
        Paragraph(
            f"6. Рекомендации по результатам <u>{type_med_examination_padeg}</u> медицинского осмотра (обсле-дования) (направление в специализированную или профпатологическую медицинскую "
            f"организацию; использование средств индивидуальной защиты, или др.): {recommendation}",
            style,
        )
    )
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f"7. Группа здоровья: {dispensary_group}", style))
    fwb.append(Spacer(1, 3 * mm))
    notice = "_____________________________"
    fwb.append(Paragraph(f"8. Дата и номер извещения об установлении предварительного диагноза острого или хронического профессионального заболевания (отравления): {notice}", style))
    fwb.append(Spacer(1, 3 * mm))
    space_symbol = '&nbsp;'
    date_diagnos = iss.medical_examination
    date_diagnos = date_diagnos.strftime("%d.%m.%Y")
    opinion = [
        [
            Paragraph('9. Председатель врачебной комиссии:', style),
            Paragraph('10. Члены врачебной комиссии:', style),
        ],
        [
            Paragraph(f'_________________________ {space_symbol * 3} ____________', style),
            Paragraph(f'_________________________ {space_symbol * 3} ____________', style),
        ],
        [
            Paragraph('', style),
            Paragraph(f'_________________________ {space_symbol * 3} ____________', style),
        ],
        [
            Paragraph(f'{date_diagnos} г.', style),
            Paragraph(f'_________________________ {space_symbol * 3} ____________', style),
        ],
    ]

    tbl = Table(opinion, colWidths=(100 * mm, 90 * mm))
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (1, 0), (-1, -1), 2 * mm),
                ('LEFTPADDING', (0, 0), (0, -1), 7 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )

    fwb.append(tbl)

    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph('М.П.', style))
    fwb.append(Spacer(1, 8 * mm))
    fwb.append(Paragraph(f'_______________________({fio_short}) {date} г.', style))
    fwb.append(Paragraph('(подпись работника<br/>освидетельствуемого)', style))

    doc.build(fwb)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def protocol_fields_result(iss):
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
        'Цех, участок ОПУ',
        'Выявлено',
        'Дополнительные сведения',
        'Перенесенные заболевания',
        'Профилактические прививки',
        'Врач-терапевт',
        'Врач-хирург',
        'Врач-невролог',
        'Врач-оториноларинголог',
        'Врач-офтальмолог',
        'Данные флюорографии',
        'Данные лабораторных исследований',
        'Заключение о профессиональной пригодности',
        'Рекомендации',
        'Диспансерная группа',
        'Наименование заболевания',
        'Патология',
        'Медицинское заключение',
        'Место регистрации',
        'Группа здоровья',
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

    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A5), leftMargin=18 * mm, rightMargin=18 * mm, topMargin=6 * mm, bottomMargin=6 * mm, allowSplitting=1, title="Форма {}".format("058/у")
    )

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10.7
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

    hospital: Hospitals = request_data["hospital"]

    hospital_name = hospital.safe_short_title
    hospital_address = hospital.safe_address
    hospital_hospital_kod_ogrn = hospital.safe_ogrn

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 3.5 * mm

    fwb = []
    opinion = [
        [
            Paragraph('<font size=10>{}<br/>Адрес: {}<br/>ОГРН: {}</font>'.format(hospital_name, hospital_address, hospital_hospital_kod_ogrn), styleT),
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
    if not iss.time_confirmation:
        return ""

    result = form_05_06_data_result_(iss)

    work_place, work_position, address, phone, add_diagnos = '', '', '', '', ''
    main_diagnos, date_start_ill, date_post, last_visit, medical_treatment = '', '', '', '', ''
    protocol_num, protocol_date, protocol_date, laboratory_protocol = '', '', '', ''
    for i in result:
        if i["title"] == "Место работы (обучения)":
            work_place = i["value"]
        elif i["title"] == "Должность (группа)":
            work_position = i["value"]
        elif i["title"] == "Адрес":
            address = i["value"]
        elif i["title"] == "Телефон":
            phone = i["value"]
        elif i["title"] == "Диагноз сопутствующий":
            add_diagnos = i["value"]
        elif i["title"] == "Диагноз основной":
            main_diagnos = i["value"]
        elif i["title"] == "Дата заболевания":
            date_start_ill = i["value"]
        elif i["title"] == "Дата обращения":
            date_post = i["value"]
        elif i["title"] == "Последнее посещение":
            last_visit = i["value"]
        elif i["title"] == "Лечение (амб/стац)":
            medical_treatment = i["value"]
        elif i["title"] == "Протокол №":
            protocol_num = i["value"]
        elif i["title"] == "Дата формирования протокола":
            protocol_date = i["value"]
        elif i["title"] == "Лаборатория":
            laboratory_protocol = i["value"]

    if add_diagnos:
        add_diagnos = f"сопутствующий - {add_diagnos}"

    date_diagnos = iss.medical_examination
    date_diagnos = date_diagnos.strftime("%d.%m.%Y")
    space_symbol = '&nbsp;'
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f'1. Диагноз: <u>основной-{main_diagnos}</u>, {add_diagnos}', style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph(f"2. Фамилия, имя, отчество:  {patient_data['fio']} {space_symbol * 10} 3. Пол: {patient_data['sex']}", style))
    fwb.append(Spacer(1, 1 * mm))
    age = dir.client.individual.age_s(direction=dir)
    fwb.append(Paragraph(f"4. Возраст (для детей до 14 лет - дата рождения): {patient_data['born']} ({age})", style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph(f"5. Адрес, населенный пункт: {address} - тел. {phone}", style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph(f'6. Наименование и адрес места работы (учебы, детского учреждения) {work_place} - {work_position}', style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph('7. Даты', style))
    fwb.append(Paragraph(f'заболевания - {date_start_ill}', style))
    fwb.append(Paragraph(f'первичного обращения (выявления) - {date_post}', style))
    fwb.append(Paragraph(f'установления диагноза - {date_diagnos}; / {laboratory_protocol} / {protocol_date} / {protocol_num} /', style))
    fwb.append(Paragraph(f'последующего посещения детского учреждения, школы - {last_visit}', style))
    fwb.append(Paragraph(f'госпитализации - {medical_treatment}', style))

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
    fwb.append(Paragraph(f'Подпись пославшего извещение _____________________{iss.doc_confirmation_fio}', style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph('Регистрационный N _______________ в журнале ф. N ______________', style))
    fwb.append(Paragraph('санэпидстанции', style))
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph('Подпись получившего извещение ________________________', style))
    fwb.append(Spacer(1, 10 * mm))
    fwb.append(
        Paragraph(
            'Составляется медработником, выявившим при любых обстоятельствах инфекционное заболевание, пищевое отравление, острое профессиональное отравление или подозревающих их, '
            'а также при изменении диагноза.',
            styleJustified,
        )
    )
    fwb.append(Paragraph('Посылается в санэпидстанцию по месту выявления больного не позднее 12 часов с момента обнаружения больного.', styleJustified))
    fwb.append(Paragraph('В случае сообщения об изменении диагноза п.1 извещения указывается измененный диагноз, дата его установления и первоначальный диагноз.', styleJustified))
    fwb.append(
        Paragraph(
            'Извещение составляется также на случаи укусов, оцарапанья, ослюнения домашними или дикими животными, которые следует рассматривать как подозрение на заболевание бешенством',
            styleJustified,
        )
    )

    doc.build(fwb)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_06(request_data):
    # Эпидемиологу
    direction = request_data["dir"]

    buffer = BytesIO()
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    doc = SimpleDocTemplate(
        buffer, pagesize=portrait(A4), leftMargin=20 * mm, rightMargin=10 * mm, topMargin=6 * mm, bottomMargin=6 * mm, allowSplitting=1, title="Форма {}".format("Эпидемиологу")
    )

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10
    style.leading = 12
    style.spaceAfter = 0.5 * mm

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 10
    styleCenterBold.face = 'PTAstraSerifBold'

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 12
    styleT.leading = 5 * mm

    fwb = []
    fwb.append(Paragraph('Сведения для эпидемиолога', styleCenterBold))

    dir = Napravleniya.objects.get(pk=direction)
    patient_data = dir.client.get_data_individual()
    age = dir.client.individual.age_s(direction=dir)
    iss = Issledovaniya.objects.filter(napravleniye__pk=direction).order_by("research__pk", "research__sort_weight").first()
    if not iss.time_confirmation:
        return ""
    result = form_05_06_data_result_(iss)
    work_place, work_position, address, phone, work_address = '', '', '', '', ''
    work_phone, last_visit, date_start_ill, date_post, protocol_num = '', '', '', '', ''
    date_post, protocol_date, laboratory_protocol, symptoms, add_diagnos = '', '', '', '', ''
    main_diagnos, medical_treatment, medical_destination, contacts = '', '', '', ''
    for i in result:
        if i["title"] == "Место работы (обучения)":
            work_place = i["value"]
        elif i["title"] == "Должность (группа)":
            work_position = i["value"]
        elif i["title"] == "Адрес":
            address = i["value"]
        elif i["title"] == "Телефон":
            phone = i["value"]
        elif i["title"] == "Адрес работы":
            work_address = i["value"]
        elif i["title"] == "Телефон по месту работы":
            work_phone = i["value"]
        elif i["title"] == "Последнее посещение":
            last_visit = i["value"]
        elif i["title"] == "Дата заболевания":
            date_start_ill = i["value"]
        elif i["title"] == "Дата обращения":
            date_post = i["value"]
        elif i["title"] == "Протокол №":
            protocol_num = i["value"]
        elif i["title"] == "Дата формирования протокола":
            protocol_date = i["value"]
        elif i["title"] == "Лаборатория":
            laboratory_protocol = i["value"]
        elif i["title"] == "Симптомы":
            symptoms = i["value"]
        elif i["title"] == "Диагноз сопутствующий":
            add_diagnos = i["value"]
        elif i["title"] == "Диагноз основной":
            main_diagnos = i["value"]
        elif i["title"] == "Лечение (амб/стац)":
            medical_treatment = i["value"]
        elif i["title"] == "Назначения":
            medical_destination = i["value"]
        elif i["title"] == "Контактные":
            contacts = i["value"]

    date_diagnos = iss.medical_examination
    date_diagnos = date_diagnos.strftime("%d.%m.%Y")
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(Paragraph(f'осомтр {get_system_name()} - {dir.pk} подтверждено  {strfdatetime(iss.time_confirmation, "%d.%m.%Y")}', styleCenterBold))
    fwb.append(Spacer(1, 6 * mm))
    opinion = [
        [
            Paragraph('Дата выявление', styleT),
            Paragraph(f'{date_diagnos}', styleT),
        ],
        [
            Paragraph('Экстренное извещение №', styleT),
            Paragraph('', styleT),
        ],
        [
            Paragraph('ФИО', styleT),
            Paragraph(f'{patient_data["fio"]}', styleT),
        ],
        [
            Paragraph('Дата рождения', styleT),
            Paragraph(f'{patient_data["born"]}', styleT),
        ],
        [
            Paragraph('Возраст', styleT),
            Paragraph(f'{age}', styleT),
        ],
        [
            Paragraph('Адрес', styleT),
            Paragraph(f'{address}', styleT),
        ],
        [
            Paragraph('ФИО терапевта', styleT),
            Paragraph(f'{iss.doc_confirmation_fio}', styleT),
        ],
        [
            Paragraph('Телефон', styleT),
            Paragraph(f'{phone}', styleT),
        ],
        [
            Paragraph('Место работы (обучения)', styleT),
            Paragraph(f'{work_place}', styleT),
        ],
        [
            Paragraph('Должность (группа)', styleT),
            Paragraph(f'{work_position}', styleT),
        ],
        [
            Paragraph('Адрес работы', styleT),
            Paragraph(f'{work_address}', styleT),
        ],
        [
            Paragraph('Телефон по месту работы', styleT),
            Paragraph(f'{work_phone}', styleT),
        ],
        [
            Paragraph('Последнее посещение', styleT),
            Paragraph(f'{last_visit}', styleT),
        ],
        [
            Paragraph('Дата заболевания', styleT),
            Paragraph(f'{date_start_ill}', styleT),
        ],
        [
            Paragraph('Дата обращения', styleT),
            Paragraph(f'{date_post}', styleT),
        ],
        [
            Paragraph('Протокол №', styleT),
            Paragraph(f'{protocol_num}', styleT),
        ],
        [
            Paragraph('Дата формирования протокола', styleT),
            Paragraph(f'{protocol_date}', styleT),
        ],
        [
            Paragraph('Лаборатория', styleT),
            Paragraph(f'{laboratory_protocol}', styleT),
        ],
        [
            Paragraph('Симптомы', styleT),
            Paragraph(f'{symptoms}', styleT),
        ],
        [
            Paragraph('Диагноз сопутсвующий', styleT),
            Paragraph(f'{add_diagnos}', styleT),
        ],
        [
            Paragraph('Диагноз основной', styleT),
            Paragraph(f'{main_diagnos}', styleT),
        ],
        [
            Paragraph('Дата установления диагноза', styleT),
            Paragraph(f'{date_diagnos}', styleT),
        ],
        [
            Paragraph('Лечение (амб/стац)', styleT),
            Paragraph(f'{medical_treatment}', styleT),
        ],
        [
            Paragraph('Амбулаторное лечение (назначение)', styleT),
            Paragraph(f'{medical_destination}', styleT),
        ],
        [
            Paragraph('Контактные (близкие)<br/>(ФИО, ДР, ТЕЛ, Адрес, симптомы/нет, Работает/нет)', styleT),
            Paragraph(f'{contacts}', styleT),
        ],
    ]

    tbl = Table(opinion, colWidths=(75 * mm, 100 * mm))
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5 * mm),
            ]
        )
    )

    fwb.append(tbl)

    doc.build(fwb)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_05_06_data_result_(iss):
    result = []
    title = ''
    title_fields = [
        'Адрес',
        'Телефон',
        'Место работы (обучения)',
        'Должность (группа)',
        'Адрес работы',
        'Телефон по месту работы',
        'Последнее посещение',
        'Дата заболевания',
        'Дата обращения',
        'Протокол №',
        'Дата формирования протокола',
        'Лаборатория',
        'Симптомы',
        'Диагноз сопутствующий',
        'Диагноз основной',
        'Дата установления диагноза',
        'Лечение (амб/стац)',
        'Назначения',
        'Контактные',
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


def form_07(request_data):
    # Справка на госслужбу № 001-ГС/у от 14.12.2009 № 984н
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

    hospital: Hospitals = request_data["hospital"]
    hospital_name = hospital.safe_short_title

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    fwb = []
    opinion = [
        [
            Paragraph('', styleT),
            Paragraph('<font size=10>Учетная форма № 001-ГС/у <br/>Утверждена Приказом Минздравсоцразвития России<br/>от 14.12.2009 № 984н</font>', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [105 * mm])
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
    patient_data = patient.client.get_data_individual()

    iss = Issledovaniya.objects.filter(napravleniye__pk=direction).order_by("research__pk", "research__sort_weight").first()
    if not iss.time_confirmation:
        return ""

    result = protocol_fields_result(iss)
    work_place, identified = "", ""
    for i in result:
        if i["title"] == "Место работы":
            work_place = i["value"]
        elif i["title"] == "Выявлено":
            identified = i["value"]

    fwb.append(Paragraph(f'Заключение № {direction}', styleCenterBold))
    fwb.append(
        Paragraph(
            'медицинского учреждения о наличии (отсутствии) заболевания, препятствующего поступлению на государственную '
            'гражданскую службу Российской Федерации и муниципальную службу или ее прохождению',
            styleCenterBold,
        )
    )
    date_medical_examination = iss.medical_examination.strftime("%Y-%m-%d")
    date_medical_examination = normalize_date(date_medical_examination)

    fwb.append(Paragraph(f'от {date_medical_examination} г', styleCenterBold))
    fwb.append(Spacer(1, 8 * mm))
    fwb.append(Paragraph(f'1. Выдано:  {hospital_name}', style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f'2. Наименование, почтовый адрес государственного органа, органа муниципального образования, куда представляется Заключение: <u>{work_place}</u>', style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f'3. Фамилия, имя, отчество:  {fio}', style))
    sex = "мужской" if patient_data["sex"] == "м" else "женский"
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f'4. Пол:  {sex}', style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f'5. Дата рождения: {patient_data["born"]}', style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f'6. Адрес места жительства: {patient_data["main_address"]}', style))
    fwb.append(Spacer(1, 4 * mm))
    fwb.append(
        Paragraph(
            f'7. Заключение<br/>'
            f'Выявлено {identified}, препятствующего поступлению на государственную гражданскую службу Российской Федерации (муниципальную службу) или ее прохождению'
            f'',
            style,
        )
    )
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Spacer(1, 8 * mm))
    space_symbol = '&nbsp;'
    fwb.append(Paragraph(f"____________________________________ {space_symbol * 10} ________________ {space_symbol * 10} __________________", style))
    fwb.append(Paragraph(f"(должность врача, выдавшего заключение){space_symbol * 13} (подпись) {space_symbol * 30}(Ф.И.О.)", style))
    fwb.append(Spacer(1, 7 * mm))
    fwb.append(Paragraph(f"Главный врач учреждения здравоохранения {space_symbol * 7} ________________ {space_symbol * 10} __________________ ", style))
    fwb.append(Paragraph(f"{space_symbol * 87} (подпись) {space_symbol * 30}(Ф.И.О.)", style))

    fwb.append(Paragraph('М.П. "___" ________________ 20__ г.', style))

    doc.build(fwb)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_08(request_data):
    # Форма Судья == N 086-1/у от 21 февраля 2002 г. N 61
    direction = request_data["dir"]

    buffer = BytesIO()
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A5), leftMargin=15 * mm, rightMargin=10 * mm, topMargin=5 * mm, bottomMargin=5 * mm, allowSplitting=1, title="Форма {}".format("Заключение")
    )

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.alignment = TA_JUSTIFY
    style.leading = 12

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"

    hospital: Hospitals = request_data["hospital"]
    hospital_name = hospital.safe_short_title

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    fwb = []
    opinion = [
        [
            Paragraph(f'<font size=10>Министерство здравоохранения<br/>Российской Федерации<br/>{hospital_name}</font>', styleT),
            Paragraph('<font size=10>Медицинская документация<br/>Форма N 086-1/у<br/>Утверждена приказом Минздрава России<br/>21 февраля 2002 г. N 61</font>', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [105 * mm])
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
    fwb.append(Spacer(1, 3 * mm))

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 11.5
    styleCenterBold.leading = 15
    styleCenterBold.fontName = 'PTAstraSerifBold'

    patient = Napravleniya.objects.get(pk=direction)
    fio = patient.client.individual.fio()
    patient_data = patient.client.get_data_individual()

    iss = Issledovaniya.objects.filter(napravleniye__pk=direction).order_by("research__pk", "research__sort_weight").first()
    if not iss.time_confirmation:
        return ""

    result = protocol_fields_result(iss)
    work_place, identified_fianl = "", ""
    for i in result:
        if i["title"] == "Место работы":
            work_place = i["value"]
        elif i["title"] == "Заключение по приказу N302н":
            identified_fianl = i["value"]

    fwb.append(Paragraph(f'Медицинское освидетельствование № {direction}', styleCenterBold))
    fwb.append(Paragraph('претендента на должность судьи', styleCenterBold))
    date_medical_examination = iss.medical_examination.strftime("%Y-%m-%d")
    date_medical_examination = normalize_date(date_medical_examination)

    fwb.append(Paragraph(f'от {date_medical_examination} г', styleCenterBold))
    fwb.append(Spacer(1, 4 * mm))
    fwb.append(Paragraph(f'1. Выдано:  {hospital_name}', style))
    fwb.append(Spacer(1, 2 * mm))
    fwb.append(Paragraph(f'2. Наименование учреждения, куда представляется освидетельствование: <u>{work_place}</u>', style))
    fwb.append(Spacer(1, 2 * mm))
    fwb.append(Paragraph(f'3. Фамилия, имя, отчество:  {fio}', style))
    fwb.append(Spacer(1, 2 * mm))
    space_symbol = '&nbsp;'
    fwb.append(Paragraph(f'4. Пол:  {patient_data["sex"]} {space_symbol * 10} 5. Дата рождения: {patient_data["born"]}', style))
    fwb.append(Spacer(1, 2 * mm))
    fwb.append(Paragraph(f'6. Адрес места жительства: {patient_data["main_address"]}', style))
    fwb.append(Spacer(1, 2 * mm))
    fwb.append(Paragraph(f'7. Врачебное  заключение о   профессиональной   пригодности: <u>{identified_fianl}</u>', style))
    fwb.append(
        Paragraph(
            '<font size=9>(дается в соответствии с перечнем заболеваний, препятствующих  назначению на  должность  судьи,  утвержденным  решением  Совета  судей  Российской Федерации)</font>',  # noqa: E501
            style,
        )
    )
    fwb.append(Spacer(1, 4 * mm))
    fwb.append(Paragraph("Подпись лица, заполнившего освидетельствование ________________________", style))
    fwb.append(Spacer(1, 2 * mm))
    fwb.append(Paragraph("Подпись главного врача лечебно-", style))
    fwb.append(Paragraph("профилактического учреждения __________________________________________", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph('Место печати', style))
    doc.build(fwb)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_091(request_data):
    # Прикрепление
    direction = request_data["dir"]

    buffer = BytesIO()
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A5), leftMargin=15 * mm, rightMargin=10 * mm, topMargin=5 * mm, bottomMargin=5 * mm, allowSplitting=1, title="Форма {}".format("Прикрепление")
    )

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.alignment = TA_JUSTIFY
    style.leading = 12

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"

    hospital: Hospitals = request_data["hospital"]
    hospital_name = hospital.safe_full_title
    hospital_address = hospital.safe_address
    hospital_phones = hospital.safe_phones
    hospital_email = hospital.safe_email

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 11.5
    styleCenterBold.leading = 15
    styleCenterBold.fontName = 'PTAstraSerifBold'

    fwb = []
    fwb.append(Paragraph(f'{hospital_name}', styleCenterBold))
    fwb.append(HRFlowable(width=200 * mm, spaceAfter=3 * mm, spaceBefore=3 * mm, color=colors.black))

    iss = Issledovaniya.objects.filter(napravleniye__pk=direction).order_by("research__pk", "research__sort_weight").first()
    date_medical_examination = iss.medical_examination.strftime("%Y-%m-%d")
    date_medical_examination = normalize_date(date_medical_examination)
    opinion = [
        [
            Paragraph(
                f'<font size=10>Юридический адрес:<br/>{hospital_address}<br/>тел: {hospital_phones}<br/>e-mail: {hospital_email}<br/><br/>{date_medical_examination} г.</font>', styleT
            ),
            Paragraph('', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [105 * mm])
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
    fwb.append(Spacer(1, 3 * mm))

    patient = Napravleniya.objects.get(pk=direction)
    fio = patient.client.individual.fio()
    patient_data = patient.client.get_data_individual()

    if not iss.time_confirmation:
        return ""

    fwb.append(Paragraph(f'Врачебная справка № {direction}', styleCenterBold))
    fwb.append(Spacer(1, 4 * mm))
    result = protocol_fields_result(iss)
    data = ""
    for i in result:
        if i["title"] == "Дополнительные сведения":
            data = i["value"]
    fwb.append(Paragraph(f'Дана {fio} {patient_data["born"]}. в том, что она прикреплен(а) в: {hospital_name}. {data}', style))
    fwb.append(Spacer(1, 8 * mm))
    space_symbol = '&nbsp;'
    fwb.append(Paragraph(f'Лечащий врач {space_symbol * 80} {iss.doc_confirmation_fio}', style))

    doc.build(fwb)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_09(request_data):
    # Прикрепление
    direction = request_data["dir"]

    buffer = BytesIO()
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A5), leftMargin=15 * mm, rightMargin=10 * mm, topMargin=5 * mm, bottomMargin=5 * mm, allowSplitting=1, title="Форма {}".format("Прикрепление")
    )

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.alignment = TA_JUSTIFY
    style.leading = 12

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"

    hospital: Hospitals = request_data["hospital"]
    hospital_name = hospital.safe_full_title
    hospital_address = hospital.safe_address
    hospital_phones = hospital.safe_phones
    hospital_email = hospital.safe_email

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 11.5
    styleCenterBold.leading = 15
    styleCenterBold.fontName = 'PTAstraSerifBold'

    fwb = []
    fwb.append(Paragraph(f'{hospital_name}', styleCenterBold))
    fwb.append(HRFlowable(width=200 * mm, spaceAfter=3 * mm, spaceBefore=3 * mm, color=colors.black))

    iss = Issledovaniya.objects.filter(napravleniye__pk=direction).order_by("research__pk", "research__sort_weight").first()
    date_medical_examination = iss.medical_examination.strftime("%Y-%m-%d")
    date_medical_examination = normalize_date(date_medical_examination)
    opinion = [
        [
            Paragraph(
                f'<font size=10>Юридический адрес:<br/>{hospital_address}<br/>тел: {hospital_phones}<br/>e-mail: {hospital_email}<br/><br/>{date_medical_examination} г.</font>', styleT
            ),
            Paragraph('', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [105 * mm])
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
    fwb.append(Spacer(1, 3 * mm))

    patient = Napravleniya.objects.get(pk=direction)
    fio = patient.client.individual.fio()
    patient_data = patient.client.get_data_individual()

    if not iss.time_confirmation:
        return ""

    fwb.append(Paragraph(f'Врачебная справка № {direction}', styleCenterBold))
    fwb.append(Spacer(1, 4 * mm))
    result = protocol_fields_result(iss)
    data = ""
    for i in result:
        if i["title"] == "Дополнительные сведения":
            data = i["value"]
    fwb.append(Paragraph(f'Дана {fio} {patient_data["born"]}. в том, что она прикреплен(а) в: {hospital_name}. {data}', style))
    fwb.append(Spacer(1, 8 * mm))
    space_symbol = '&nbsp;'
    fwb.append(Paragraph(f'Лечащий врач {space_symbol * 80} {iss.doc_confirmation_fio}', style))

    doc.build(fwb)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_10(request_data):
    # Форма N 086/у от 15 декабря 2014 г. N 834н
    direction = request_data["dir"]

    buffer = BytesIO()
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A5), leftMargin=15 * mm, rightMargin=10 * mm, topMargin=5 * mm, bottomMargin=5 * mm, allowSplitting=1, title="Форма {}".format("Прикрепление")
    )

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.alignment = TA_JUSTIFY
    style.leading = 14

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"

    hospital: Hospitals = request_data["hospital"]
    hospital_short_title = hospital.safe_short_title
    hospital_address = hospital.safe_address
    hospital_phones = hospital.safe_phones

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 11.5
    styleCenterBold.leading = 15
    styleCenterBold.fontName = 'PTAstraSerifBold'

    fwb = []

    iss = Issledovaniya.objects.filter(napravleniye__pk=direction).order_by("research__pk", "research__sort_weight").first()
    date_medical_examination = iss.medical_examination.strftime("%Y-%m-%d")
    date_medical_examination = normalize_date(date_medical_examination)
    opinion = [
        [
            Paragraph(f'<font size=10>{hospital_short_title}<br/>{hospital_address}<br/>тел: {hospital_phones}</font>', styleT),
            Paragraph('<font size=10>Медицинская документация<br/>Форма N 086/у<br/>Утверждена приказом Минздрава России<br/>от 15 декабря 2014 г. N 834н</font>', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [105 * mm])
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
    fwb.append(Spacer(1, 3 * mm))

    patient = Napravleniya.objects.get(pk=direction)
    fio = patient.client.individual.fio()
    patient_data = patient.client.get_data_individual()

    if not iss.time_confirmation:
        return ""

    fwb.append(Paragraph(f'МЕДИЦИНСКАЯ СПРАВКА № {direction}', styleCenterBold))
    fwb.append(Paragraph('(врачебное профессионально-консультативное заключение)', styleCenterBold))
    fwb.append(Spacer(1, 4 * mm))
    result = protocol_fields_result(iss)
    was_ill, vaccinations, therapy_doc, hirurg_doc, nevrolog_doc, lor_doc, ophtalmolog_doc, fluorograph, laboratory, final_examination = '', '', '', '', '', '', '', '', '', ''
    for i in result:
        if i["title"] == "Перенесенные заболевания":
            was_ill = i["value"]
        if i["title"] == "Профилактические прививки":
            vaccinations = i["value"]
        if i["title"] == "Врач-терапевт":
            therapy_doc = i["value"]
        if i["title"] == "Врач-хирург":
            hirurg_doc = i["value"]
        if i["title"] == "Врач-невролог":
            nevrolog_doc = i["value"]
        if i["title"] == "Врач-оториноларинголог":
            lor_doc = i["value"]
        if i["title"] == "Врач-офтальмолог":
            ophtalmolog_doc = i["value"]
        if i["title"] == "Данные флюорографии":
            fluorograph = i["value"]
        if i["title"] == "Данные лабораторных исследований":
            laboratory = i["value"]
        if i["title"] == "Заключение о профессиональной пригодности":
            final_examination = i["value"]

    fwb.append(Paragraph(f'1. Фамилия, имя, отчество {fio}', style))
    fwb.append(Spacer(1, 2 * mm))
    born = patient_data["born"].split('.')
    fwb.append(Paragraph(f'2. Дата рождения: число <u>{born[0]}</u> месяц <u>{born[1]}</u> год <u>{born[2]}</u>', style))
    fwb.append(Spacer(1, 2 * mm))
    fwb.append(Paragraph(f'3. Место регистрации: {patient_data["main_address"]}', style))
    fwb.append(Spacer(1, 2 * mm))
    work_p = patient_data['work_place_db'] if patient_data['work_place_db'] else patient_data['work_place']
    fwb.append(Paragraph(f'4. Место учебы, работы: {work_p}', style))
    fwb.append(Spacer(1, 2 * mm))
    fwb.append(Paragraph(f'5. Перенесенные заболевания: {was_ill}', style))
    fwb.append(Spacer(1, 2 * mm))
    fwb.append(Paragraph(f'6. Профилактические прививки: {vaccinations}', style))
    fwb.append(PageBreak())
    fwb.append(Paragraph('7. Объективные данные и состояние здоровья:', style))
    fwb.append(Paragraph(f'Врач-терапевт: {therapy_doc}', style))
    fwb.append(Paragraph(f'Врач-хирург: {hirurg_doc}', style))
    fwb.append(Paragraph(f'Врач-невролог: {nevrolog_doc}', style))
    fwb.append(Paragraph(f'Врач-оториноларинголог: {lor_doc}', style))
    fwb.append(Paragraph(f'Врач-офтальмолог: {ophtalmolog_doc}', style))
    fwb.append(Paragraph(f'Данные флюорографии: {fluorograph}', style))
    fwb.append(Paragraph(f'Данные лабораторных исследований: {laboratory}', style))

    fwb.append(Spacer(1, 2 * mm))
    fwb.append(Paragraph(f'8. Заключение о профессиональной пригодности: {final_examination}', style))
    fwb.append(Spacer(1, 2 * mm))
    fwb.append(Paragraph('Дата выдачи справки', style))
    fwb.append(Paragraph(f'{date_medical_examination}', style))
    fwb.append(Spacer(1, 2 * mm))
    fwb.append(Paragraph(f'Ф.И.О. врача, выдавшего медицинскую справку: /{iss.doc_confirmation_fio}/ _____________________', style))
    fwb.append(Spacer(1, 4 * mm))
    fwb.append(Paragraph('Ф.И.О Главного врача медицинской организации /_____________________/ _______________', style))
    fwb.append(Spacer(1, 4 * mm))
    fwb.append(Paragraph('МП', style))
    fwb.append(Spacer(1, 8 * mm))
    fwb.append(Paragraph('Медицинская справка действительна в течение 6 месяцев со дня выдачи.', style))

    doc.build(fwb)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_11(request_data):
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

    hospital: Hospitals = request_data["hospital"]

    hospital_name = hospital.safe_short_title
    hospital_address = hospital.safe_address
    hospital_kod_ogrn = hospital.safe_ogrn

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    fwb = []
    opinion = [
        [
            Paragraph(f'<font size=10>{hospital_name}<br/>Адрес: {hospital_address}<br/></font>', styleT),
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

    opinion = [
        [
            Paragraph('Код ОГРН', styleT),
            Paragraph(f"{hospital_kod_ogrn[0]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[1]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[2]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[3]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[4]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[5]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[6]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[7]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[8]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[9]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[10]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[11]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[12]}", styleT),
        ],
    ]
    fwb.append(tbl)
    col_width = [6 * mm for i in range(13)]
    col_width.insert(0, 21 * mm)
    tbl = Table(opinion, hAlign='LEFT', rowHeights=6 * mm, colWidths=tuple(col_width))
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (0, 0), 0.75, colors.white),
                ('GRID', (1, 0), (-1, -1), 0.75, colors.black),
                ('LEFTPADDING', (1, 0), (-1, -1), 2 * mm),
                ('LEFTPADDING', (0, 0), (0, -1), 1 * mm),
                ('LEFTPADDING', (0, 0), (0, 0), 3 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5 * mm),
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
    sex = "мужской" if patient.client.individual.sex == "м" else "женский"
    fio_short = patient.client.individual.fio(short=True, dots=True)
    born = patient.client.individual.bd()

    iss = Issledovaniya.objects.filter(napravleniye__pk=direction).order_by("research__pk", "research__sort_weight").first()
    if not iss.time_confirmation:
        return ""

    work_place, work_position, harmful_factor, type_med_examination, restrictions, med_report, date, department = ("", "", "", "", "", "", "", "")
    type_med_examination_padeg = "", ""
    dispensary_group = ""

    title_fields = [
        "Место работы",
        "Должность",
        "Вредный производственный фактор или вид работы",
        "Тип медосмотра",
        "Медицинские противопоказания к работе",
        "Заключение по приказу N29н",
        "Дата осмотра",
        "Цех, участок ОПУ",
        "Диспансерная группа",
    ]
    result = fields_result_only_title_fields(iss, title_fields)
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
                type_med_examination_padeg = 'предварительного'
            if type_med_examination.lower() == 'периодический':
                type_med_examination_padeg = 'периодического'
        elif i["title"] == "Медицинские противопоказания к работе":
            restrictions = i["value"]
        elif i["title"] == "Заключение по приказу N302н":
            med_report = i["value"]
        elif i["title"] == "Дата осмотра":
            date = i["value"]
        elif i["title"] == "Цех, участок ОПУ":
            department = i["value"]
        elif i["title"] == "Диспансерная группа":
            dispensary_group = i["value"]

    fwb.append(Paragraph('Заключение по результатам', styleCenterBold))
    fwb.append(Paragraph(f'{type_med_examination_padeg} медицинского осмотра (обследования) № {direction}', styleCenterBold))
    fwb.append(Spacer(1, 8 * mm))
    fwb.append(Paragraph(f'1. Ф.И.О:  {fio}, {born} ', style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f'2. Пол:  {sex} ', style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph("3. Место работы:", style))
    fwb.append(Paragraph(f"3.1 Организация (предприятие): {work_place}", style))
    fwb.append(Paragraph(f"3.2 Цех, участок ОПУ: {department}", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f"4 Профессия (должность) (в настоящее время): {work_position}", style))
    fwb.append(Paragraph(f"5 Вредный производственный фактор или вид работы: согласно приказу № 29Н - {harmful_factor}", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(
        Paragraph(
            f"6. Согласно результатам проведенного <u>{type_med_examination_padeg}</u> медицинского осмотра (обследования): "
            f"<u>{restrictions}</u> медицинские противопоказания к работе с вредными и/или опасными веществами и производственными факторами заключение <u>{med_report}</u> ",
            style,
        )
    )
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f"7 Диспансерная группа: {dispensary_group}", style))
    fwb.append(Spacer(1, 5 * mm))
    fwb.append(Paragraph("Председатель врачебной комиссии________________________(__________)", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph('М.П.', style))
    fwb.append(Spacer(1, 8 * mm))
    fwb.append(Paragraph(f'_______________________({fio_short}) {date} г.', style))
    fwb.append(Paragraph('(подпись работника<br/>освидетельствуемого)', style))
    fwb = show_qr_lk_address(fwb)

    doc.build(fwb)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_12(request_data):
    # Профосомтр по 29Н
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

    hospital: Hospitals = request_data["hospital"]

    hospital_name = hospital.safe_short_title
    hospital_address = hospital.safe_address
    hospital_kod_ogrn = hospital.safe_ogrn

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    fwb = []
    opinion = [
        [
            Paragraph(f'<font size=10>{hospital_name}<br/>Адрес: {hospital_address}<br/></font>', styleT),
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

    opinion = [
        [
            Paragraph('Код ОГРН', styleT),
            Paragraph(f"{hospital_kod_ogrn[0]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[1]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[2]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[3]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[4]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[5]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[6]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[7]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[8]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[9]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[10]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[11]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[12]}", styleT),
        ],
    ]
    fwb.append(tbl)
    col_width = [6 * mm for i in range(13)]
    col_width.insert(0, 21 * mm)
    tbl = Table(opinion, hAlign='LEFT', rowHeights=6 * mm, colWidths=tuple(col_width))
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (0, 0), 0.75, colors.white),
                ('GRID', (1, 0), (-1, -1), 0.75, colors.black),
                ('LEFTPADDING', (1, 0), (-1, -1), 2 * mm),
                ('LEFTPADDING', (0, 0), (0, -1), 1 * mm),
                ('LEFTPADDING', (0, 0), (0, 0), 3 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5 * mm),
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
    born = patient.client.individual.bd()
    sex = patient.client.individual.sex

    iss = Issledovaniya.objects.filter(napravleniye__pk=direction).order_by("research__pk", "research__sort_weight").first()
    if not iss.time_confirmation:
        return ""

    work_place, work_position, harmful_factor, type_med_examination, restrictions, date, department = ("", "", "", "", "", "", "")
    type_med_examination_padeg, group_health = "", ""

    title_fields = [
        "Место работы",
        "Должность",
        "Вредный производственный фактор или вид работы",
        "Тип медосмотра",
        "Медицинские противопоказания к работе",
        "Заключение по приказу N29н",
        "Дата осмотра",
        "Цех, участок ОПУ",
        "Группа здоровья",
    ]
    result = fields_result_only_title_fields(iss, title_fields)
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
                type_med_examination_padeg = 'предварительного'
            if type_med_examination.lower() == 'периодический':
                type_med_examination_padeg = 'периодического'
        elif i["title"] == "Медицинские противопоказания к работе":
            restrictions = i["value"]
        elif i["title"] == "Дата осмотра":
            date = i["value"]
        elif i["title"] == "Цех, участок ОПУ":
            department = i["value"]
        elif i["title"] == "Группа здоровья":
            group_health = i["value"]

    fwb.append(Paragraph('Заключение по результатам', styleCenterBold))
    fwb.append(Paragraph(f'{type_med_examination_padeg} медицинского осмотра (обследования) № {direction} от {date}', styleCenterBold))
    fwb.append(Spacer(1, 8 * mm))
    fwb.append(Paragraph(f'1. Ф.И.О:  {fio}', style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f'2. Дата рождения:  {born}', style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f"3. Пол лица, поступающего на работу: {sex}", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f"4.Наименование работодателя: : {work_place}", style))
    fwb.append(Paragraph(f"4.1. Наименование структурного подразделения работодателя (при наличии): {department}", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f"5.Наименование должности (профессии) или вида работы: {work_position}", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f"6.Наименование вредных и (или) опасных производственных факторов, видов работ: {harmful_factor}", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f"7.Результаты  <u>{type_med_examination_padeg}</u> медицинского осмотра (обследования): " f"медицинские противопоказания к работе <u>{restrictions}</u>", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f"8.Группа здоровья: {group_health}", style))
    fwb.append(Spacer(1, 5 * mm))
    fwb.append(Paragraph("Председатель врачебной комиссии________________________(__________)", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph('М.П.', style))
    fwb.append(Spacer(1, 8 * mm))
    fwb.append(Paragraph(f'_______________________({fio_short}) {date} г.', style))
    fwb.append(Paragraph('(подпись работника<br/>освидетельствуемого)', style))

    doc.build(fwb)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_13(request_data):
    # профосомтр по 29Н-v2
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

    hospital: Hospitals = request_data["hospital"]

    hospital_name = hospital.safe_short_title
    hospital_address = hospital.safe_address
    hospital_kod_ogrn = hospital.safe_ogrn

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    fwb = []
    opinion = [
        [
            Paragraph(f'<font size=10>{hospital_name}<br/>Адрес: {hospital_address}<br/></font>', styleT),
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

    opinion = [
        [
            Paragraph('Код ОГРН', styleT),
            Paragraph(f"{hospital_kod_ogrn[0]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[1]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[2]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[3]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[4]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[5]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[6]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[7]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[8]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[9]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[10]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[11]}", styleT),
            Paragraph(f"{hospital_kod_ogrn[12]}", styleT),
        ],
    ]
    fwb.append(tbl)
    col_width = [6 * mm for i in range(13)]
    col_width.insert(0, 21 * mm)
    tbl = Table(opinion, hAlign='LEFT', rowHeights=6 * mm, colWidths=tuple(col_width))
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (0, 0), 0.75, colors.white),
                ('GRID', (1, 0), (-1, -1), 0.75, colors.black),
                ('LEFTPADDING', (1, 0), (-1, -1), 2 * mm),
                ('LEFTPADDING', (0, 0), (0, -1), 1 * mm),
                ('LEFTPADDING', (0, 0), (0, 0), 3 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5 * mm),
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
    born = patient.client.individual.bd()

    iss = Issledovaniya.objects.filter(napravleniye__pk=direction).order_by("research__pk", "research__sort_weight").first()
    if not iss.time_confirmation:
        return ""

    work_place, work_position, harmful_factor, type_med_examination, restrictions, med_report, date, department = ("", "", "", "", "", "", "", "")
    type_med_examination_padeg = "", ""
    group_health, score_risk, chairman = "", "", ""

    title_fields = [
        "Место работы",
        "Должность",
        "Вредный производственный фактор или вид работы",
        "Тип медосмотра",
        "Медицинские противопоказания к работе",
        "Заключение по приказу N29н",
        "Дата осмотра",
        "Цех, участок ОПУ",
        "Группа здоровья",
        "SCORE-риск",
        "Председатель врачебной комиссии",
    ]

    result = fields_result_only_title_fields(iss, title_fields)
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
                type_med_examination_padeg = 'предварительного'
            if type_med_examination.lower() == 'периодический':
                type_med_examination_padeg = 'периодического'
        elif i["title"] == "Медицинские противопоказания к работе":
            restrictions = i["value"]
        elif i["title"] == "Заключение по приказу N29н":
            med_report = i["value"]
        elif i["title"] == "Дата осмотра":
            date = i["value"]
        elif i["title"] == "Цех, участок ОПУ":
            department = i["value"]
        elif i["title"] == "Группа здоровья":
            group_health = i["value"]
        elif i["title"] == "SCORE-риск":
            score_risk = i["value"]
        elif i["title"] == "Председатель врачебной комиссии":
            chairman = i["value"]


    fwb.append(Paragraph('Медицинское заключение по результатам предварительного', styleCenterBold))
    fwb.append(Paragraph(f'медицинского осмотра (обследования) № {direction}', styleCenterBold))
    fwb.append(Spacer(1, 8 * mm))
    fwb.append(Paragraph(f'1. Ф.И.О:  {fio}, {born} ', style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f'2. Дата рождения: {born}', style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph("3. Место работы:", style))
    fwb.append(Paragraph(f"3.1 Организация (предприятие): {work_place}", style))
    fwb.append(Paragraph(f"3.2 Цех, участок ОПУ: {department}", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f"4 Профессия (должность) (в настоящее время): {work_position}", style))
    result_harmful_factor = harmful_factor.split(";")
    result_harmful_factor = " ".join([f"П{i};" for i in result_harmful_factor])
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f"5 Вредный производственный фактор или вид работы: {result_harmful_factor}", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(
        Paragraph(
            f"6. Согласно результатам проведенного <u>{type_med_examination_padeg}</u> медицинского осмотра (обследования): "
            f"<u>{restrictions}</u> медицинские противопоказания к работе с вредными и/или опасными веществами и производственными факторами заключение <u>{med_report}</u> ",
            style,
        )
    )
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f"7 Группа здоровья: {group_health}", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f"Сердечно-сосудистый риск по шкале SCORE:  {score_risk}", style))
    fwb.append(Spacer(1, 5 * mm))
    fwb.append(Paragraph(f"Председатель врачебной комиссии________________________({chairman}) {date}", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph('М.П.', style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f'________________________________________________ (________________________) {date}', style))
    fwb.append(Spacer(1, 8 * mm))
    space_symbol = '&nbsp;'
    fwb.append(Paragraph(f'(подпись работника (освидетельствуемого){space_symbol *60} {fio_short} {date} г.', style))
    fwb.append(Spacer(1, 5 * mm))
    fwb.append(Paragraph("*Передается  работодателю  и  приобщается  к  личному  делу  работника (освидетельствуемого)", styleT))
    fwb.append(Paragraph("**Перечислить  в соответствии с Перечнем вредных факторов и Перечнем", styleT))
    fwb = show_qr_lk_address(fwb)

    doc.build(fwb)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf
