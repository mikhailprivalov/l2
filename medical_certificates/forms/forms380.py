from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from directions.models import ParaclinicResult, Issledovaniya, Napravleniya
from laboratory.settings import FONTS_FOLDER
from results.prepare_data import text_to_bold
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, SimpleDocTemplate
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from appconf.manager import SettingManager
from io import BytesIO
from reportlab.lib.pagesizes import A4
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
    work_place, work_position, harmful_factor, type_med_examination, restrictions, med_report, date = (
        "",
        "",
        "",
        "",
        "",
        "",
        "",
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

    fwb.append(Paragraph(f'Заключение № {direction}', styleCenterBold))
    fwb.append(Paragraph(f'{type_med_examination} медицинского осмотра (обследования)', styleCenterBold))
    fwb.append(Spacer(1, 8 * mm))
    fwb.append(Paragraph(f'1. Ф.И.О:  {fio}', style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph("2. Место работы:", style))
    fwb.append(Paragraph(f"2.1 Организация (предприятие): {work_place}", style))
    fwb.append(Paragraph("2.2 Цех, участок ОПУ:", style))
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
