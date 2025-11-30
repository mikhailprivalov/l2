import pytz
from hospitals.models import Hospitals
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Flowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_JUSTIFY
from directions.models import Issledovaniya, Napravleniya
from laboratory.settings import FONTS_FOLDER
import os.path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from results.sql_func import get_paraclinic_results_by_direction


def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None, **kwargs):
    """
    Протокол результата парклиники с логотипом
    """

    hospital: Hospitals = direction.hospital
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 9
    style.leading = 10
    style.spaceAfter = 0 * mm
    style.alignment = TA_JUSTIFY

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleBold.firstLineIndent = 0
    styleBold.fontSize = 8

    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 11
    styleJustified.leading = 4.5 * mm

    objs = []
    header_title = gen_header_title(iss.napravleniye.doc.hospital)
    objs.append(header_title)

    result = get_paraclinic_results_by_direction(iss.napravleniye_id)
    data = {r.cda_title_field: r.value for r in result}
    direction = Napravleniya.objects.filter(pk=iss.napravleniye_id).first()
    contrast_amount = direction.contrast_amount
    dose = direction.dose
    anamnesis = direction.anamnesis
    direction_comment = direction.direction_comment
    fact_research_date = direction.fact_research_date

    individula = direction.client.get_data_individual()

    table_data = [
        [
            Paragraph("Дата и время проведения исследования", style),
            Paragraph(f"{fact_research_date.strftime('%d.%m.%Y')}", style),
        ],
        [
            Paragraph("ФИО", style),
            Paragraph(f"{individula.get('fio')}", style),
        ],
        [
            Paragraph("Пол (М/Ж)", style),
            Paragraph(f"{individula.get('sex')}", style),
        ],
        [
            Paragraph("Дата рождения (ДД/ММ/ГГГГ)", style),
            Paragraph(f"{individula.get('born')}", style),
        ],
        [
            Paragraph("Протокол исследования", style),
            Paragraph(f"{direction.pk}", style),
        ],
        [
            Paragraph("Первичное/вторичное исследование", style),
            Paragraph(f"{data.get('пр-Этап исследования')}", style),
        ],
        [
            Paragraph("Краткий анамнез", style),
            Paragraph(f"{anamnesis}", style),
        ],
        [
            Paragraph("Вид исследования", style),
            Paragraph(f"{iss.research.title}", style),
        ],
        [
            Paragraph("Наименование медицинского оборудования", style),
            Paragraph("", style),
        ],
        [
            Paragraph("Эффективная доза (при наличии)", style),
            Paragraph(f"{dose}", style),
        ],
        [
            Paragraph("Ограничения визуализации", style),
            Paragraph("", style),
        ],
        [
            Paragraph("Примечания", style),
            Paragraph(f"{direction_comment}", style),
        ],
        [
            Paragraph("Пероральный контраст", style),
            Paragraph("", style),
        ],
        [
            Paragraph("Внутривенный контраст", style),
            Paragraph(f"{contrast_amount}", style),
        ],
        [
            Paragraph("Аллергическая реакция", style),
            Paragraph("", style),
        ],
    ]

    custom_style = [
        ("GRID", (0, 0), (-1, -1), 0.75, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.6 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 0.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    table = Table(table_data, colWidths=(65 * mm, 105 * mm), hAlign="LEFT")

    table.setStyle(TableStyle(custom_style))
    objs.append(table)
    objs.append(Spacer(1, 3 * mm))

    objs.append(Paragraph("ОПИСАНИЕ", styleBold))
    objs.append(Paragraph(f"{data.get('пр-Результат')}", styleJustified))
    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph("ЗАКЛЮЧЕНИЕ", styleBold))
    objs.append(Paragraph(f"{data.get('пр-Заключение')}", styleJustified))
    objs.append(Spacer(1, 3 * mm))
    if data.get('пр-Рекомендации'):
        objs.append(Paragraph("РЕКОМЕНДАЦИИ", styleBold))
        objs.append(Paragraph(f"{data.get('пр-Рекомендации')}", styleJustified))

    objs.append(Spacer(1, 15 * mm))

    moscow_dt = iss.time_confirmation.astimezone(pytz.timezone('Europe/Moscow')).strftime("%d.%m.%Y - %H:%M:%S")
    objs.append(Paragraph(f"{moscow_dt} (Мск)", style))
    objs.append(Paragraph(f"Врач: {iss.doc_confirmation.get_full_fio()}", style))
    tbl = gen_table(iss.doc_confirmation)
    objs.append(Spacer(1, 3 * mm))
    objs.append(tbl)

    fwb.extend(objs)
    return fwb


def gen_header_title(hospital):
    file_jpg = hospital.get_title_stamp_executor_pdf()
    width_stamp = hospital.width_stamp_jpg if hospital.width_stamp_jpg else 1
    height_stamp = hospital.height_stamp_jpg if hospital.height_stamp_jpg else 1
    x_offset = hospital.x_offset if hospital.x_offset else 1
    y_offset = hospital.y_offset if hospital.y_offset else 1
    img = None
    if file_jpg:
        img = ImageWithOffset(
            file_jpg,
            width_stamp * mm,
            height_stamp * mm,
            x_offset=x_offset * mm,
            y_offset=y_offset * mm
        )
    return img


class ImageWithOffset(Flowable):
    def __init__(self, image_path, width, height, x_offset=0, y_offset=0):
        Flowable.__init__(self)
        self.image_path = image_path
        self.width = width
        self.height = height
        self.x_offset = x_offset
        self.y_offset = y_offset

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        self.canv.saveState()
        self.canv.translate(self.x_offset, self.y_offset)
        self.canv.drawImage(self.image_path, 0, 0, self.width, self.height)
        self.canv.restoreState()


def gen_table(doctor):
    img = ""
    if doctor:
        file_jpg = doctor.get_signature_stamp_pdf()
        width_stamp = doctor.width_stamp_jpg if doctor.width_stamp_jpg else 35
        height_stamp = doctor.height_stamp_jpg if doctor.height_stamp_jpg else 35
        x_offset = doctor.x_offset if doctor.x_offset else 1 * mm
        y_offset = doctor.y_offset if doctor.y_offset else 1 * mm
        if file_jpg:
            img = ImageWithOffset(
                file_jpg,
                width_stamp * mm,
                height_stamp * mm,
                x_offset=x_offset * mm,
                y_offset=y_offset * mm,
            )

    opinion = [
        [
            "",
            img,
        ],
    ]
    gentbl = Table(opinion, colWidths=(50 * mm, 100 * mm))
    gentbl.setStyle(
        TableStyle(
            [
                ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
                ('LINEBELOW', (2, 0), (2, 0), 0.75, colors.black),
                ('LINEBELOW', (6, 0), (6, 0), 0.75, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), -20 * mm),
                ('LEFTPADDING', (-1, 0), (-1, 0), 6 * mm),

            ]
        )
    )
    return gentbl
