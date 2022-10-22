from copy import deepcopy
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from clients.models import Card
from laboratory.settings import FONTS_FOLDER
from reportlab.lib.pagesizes import A6
import os.path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table

from laboratory.utils import current_year
from users.models import DoctorProfile


def form_01(request_data):
    # Талон приема
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Symbola', os.path.join(FONTS_FOLDER, 'Symbola.ttf')))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 9
    style.leading = 10
    style.spaceAfter = 0 * mm
    style.alignment = TA_JUSTIFY

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleBoldCenter = deepcopy(styleBold)
    styleBoldCenter.alignment = TA_CENTER

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 9
    styleCenter.leading = 10
    styleCenter.spaceAfter = 0 * mm

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 10
    styleCenterBold.leading = 10
    styleCenterBold.face = 'PTAstraSerifBold'

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    card_pk = request_data["card_pk"]
    date = request_data["date"]
    time = request_data["time"]
    page_format = request_data["pageFormat"]
    researches = request_data["researches"]
    researches = researches.split(";-")

    rmis_location = request_data["rmis_location"]
    type_slot = request_data["typeSlot"]
    if type_slot == "resource":
        rmis_location = f"{rmis_location}@R"

    doctor_data = DoctorProfile.objects.filter(rmis_location=rmis_location).first()
    doctor_fio, cabinet = "", ""
    if doctor_data:
        cabinet = doctor_data.cabinet if doctor_data.cabinet else ""
        doctor_fio = doctor_data.get_full_fio()

    buffer = BytesIO()
    p_size = A6
    col_widths = (
        24 * mm,
        70 * mm,
    )
    if page_format == "P80":
        p_size = (80 * mm, 130 * mm)
        col_widths = (24 * mm, 46 * mm,)

    doc = SimpleDocTemplate(buffer, pagesize=p_size, leftMargin=3 * mm, rightMargin=5 * mm, topMargin=2 * mm, bottomMargin=3 * mm, allowSplitting=1, title="Форма {}".format("Талон80"))
    hospital_title = request_data['user'].doctorprofile.get_hospital_title()
    objs = [Paragraph(f"{hospital_title}", styleCenterBold)]
    address = request_data['user'].doctorprofile.hospital.address
    objs.append(Paragraph(f"{address}", styleCenter))
    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph(f"{researches[0]}", styleCenterBold))
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph("ТАЛОН НА ПРИЕМ", styleCenterBold))
    objs.append(Paragraph(f"№ {researches[1]}", styleCenter))

    ind_card = Card.objects.get(pk=card_pk)
    patient_data = ind_card.get_data_individual()
    opinion = [
        [
            Paragraph('Дата приема', styleT),
            Paragraph(f'{date}', styleT),
        ],
        [
            Paragraph('Время', styleT),
            Paragraph(f'{time}', styleT),
        ],
        [
            Paragraph('Кабинет', styleT),
            Paragraph(f'{cabinet}', styleT),
        ],
        [
            Paragraph('Врач', styleT),
            Paragraph(f'{doctor_fio}', styleT),
        ],
        [
            Paragraph('Код пациента', styleT),
            Paragraph(f'{patient_data.get("ecp_id", "")} (из ЕЦП)', styleT),
        ],
        [
            Paragraph('ФИО', styleT),
            Paragraph(f'{patient_data["fio"]}', styleT),
        ],
        [
            Paragraph('Д/р', styleT),
            Paragraph(f'{patient_data["born"]}', styleT),
        ],
        [
            Paragraph('Полных лет:', styleT),
            Paragraph(f'{patient_data["age"]}', styleT),
        ],
    ]

    tbl = Table(
        opinion,
        colWidths=col_widths,
        hAlign='LEFT',
        style=[
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 1 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
            ('LEFTPADDING', (0, 0), (0, -1), 0.8 * mm),
        ],
    )

    objs.append(Spacer(1, 2 * mm))
    objs.append(tbl)

    objs.append(Spacer(1, 2 * mm))
    phone = request_data['user'].doctorprofile.hospital.phones
    objs.append(
        Paragraph(
            f"В случае отказа от приема просим позвонить по телефону {phone} Время ожидания приема врача от назначенного времени до 30 мин."
            f"(Террит. программа гос.гарантиий Иркутской области на {current_year()}г .)",
            style,
        )
    )

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf
