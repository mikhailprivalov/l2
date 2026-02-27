import pytz
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Flowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_JUSTIFY
from directions.models import Issledovaniya, Napravleniya
from integration_framework.models import EquipmentReceive
from laboratory.settings import FONTS_FOLDER
import os.path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from results.sql_func import get_paraclinic_results_by_direction
import datetime

from utils.xh import check_valid_square_brackets


def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None, **kwargs):
    """
    Протокол результата парклиники с логотипом
    """

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
    styleBold.fontSize = 9

    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 11
    styleJustified.leading = 4.5 * mm
    styleJustified.firstLineIndent = 13

    styleJustifiedDoctor = deepcopy(styleJustified)
    styleJustifiedDoctor.firstLineIndent = 0

    objs = []

    if iss.napravleniye.doc.podrazdeleniye.title_stamp_customer:
        header_title = gen_header_title(iss.napravleniye.doc.podrazdeleniye)
    else:
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
    fact_research_time = direction.fact_research_time

    naive_datetime = datetime.datetime.combine(fact_research_date, fact_research_time)
    source_timezone = pytz.timezone(direction.hospital.time_zone)
    aware_dt = source_timezone.localize(naive_datetime)
    target_timezone = pytz.timezone('Europe/Moscow')
    converted_dt = aware_dt.astimezone(target_timezone)

    individula = direction.client.get_data_individual()
    equipment = EquipmentReceive.objects.filter(napravleniye=direction).first()
    equipment_title = ''
    if equipment:
        equipment_title = equipment.equipment_model.title

    table_data = [
        [
            Paragraph("Дата и время проведения исследования", style),
            Paragraph(f"{converted_dt.strftime('%d.%m.%Y')} {converted_dt.strftime('%H:%M')} (МСК)", style),
        ],
        [
            Paragraph("Номер карты", style),
            Paragraph(f"{direction.client.number}", style),
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
            Paragraph("Причина обращения или диагноз", style),
            Paragraph(f"{data.get('пр-Диагноз', '')} {data.get('пр-Причина', '')}", style),
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
            Paragraph(equipment_title, style),
        ],
        [
            Paragraph("Эффективная доза (при наличии)", style),
            Paragraph(f"{dose}", style),
        ],
        [
            Paragraph("Ограничения визуализации", style),
            Paragraph(f"{data.get('пр-Ограничения визуализации')}", style),
        ],
        [
            Paragraph("Примечания", style),
            Paragraph(f"{direction_comment}", style),
        ],
        [
            Paragraph("Пероральный контраст", style),
            Paragraph(f"{data.get('пр-Пероральный контраст')}", style),
        ],
        [
            Paragraph("Внутривенный контраст", style),
            Paragraph(f"{contrast_amount}", style),
        ],
        [
            Paragraph("Аллергическая реакция", style),
            Paragraph(f"{data.get('пр-Аллергическая реакция')}", style),
        ],
        [
            Paragraph("Медицинская организация, осуществившая анализ(описание) результатов", style),
            Paragraph(f"{iss.doc_save.hospital.title} {iss.doc_save.hospital.license_data}", style),
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
    space_symbol = '&nbsp;'
    objs.append(Paragraph("ОПИСАНИЕ", styleBold))
    opis = data.get('пр-Результат').replace('<', '&lt;').replace('>', '&gt;').replace("\n", f"<br/>{space_symbol * 5}").replace("\r", f"<br/>{space_symbol * 5}")
    opis = text_to_bold(opis)
    objs.append(Paragraph(opis, styleJustified))
    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph("ЗАКЛЮЧЕНИЕ", styleBold))
    final = data.get('пр-Заключение').replace('<', '&lt;').replace('>', '&gt;').replace("\n", f"<br/>{space_symbol*5}")
    final = text_to_bold(final)
    objs.append(Paragraph(final, styleJustified))
    objs.append(Spacer(1, 3 * mm))
    if data.get('пр-Рекомендации'):
        objs.append(Paragraph("РЕКОМЕНДАЦИИ", styleBold))
        recomindation = data.get('пр-Рекомендации').replace('<', '&lt;').replace('>', '&gt;').replace("\n", f"<br/>{space_symbol*5}")
        recomindation = text_to_bold(recomindation)
        objs.append(Paragraph(recomindation, styleJustified))

    objs.append(Spacer(1, 15 * mm))

    moscow_dt = iss.time_confirmation.astimezone(pytz.timezone('Europe/Moscow')).strftime("%d.%m.%Y - %H:%M:%S") if iss.time_confirmation else "XX:XX:XX:XX:XX"
    objs.append(Paragraph(f"{moscow_dt} (МСК)", style))
    if iss.doc_confirmation:
        objs.append(Paragraph(f"Врач-рентгенолог: {iss.doc_confirmation.get_full_fio()}", styleJustifiedDoctor))
    else:
        objs.append(Paragraph("Врач-рентгенолог: Образец-Доктор", styleJustifiedDoctor))
    has_any_signature = kwargs.get('has_any_signature', False)
    if not has_any_signature:
        tbl = gen_table(iss.doc_confirmation)
        objs.append(Spacer(1, 3 * mm))
        objs.append(tbl)

    fwb.extend(objs)
    return fwb


def gen_header_title(obj_where_store_stamp):
    file_jpg = obj_where_store_stamp.get_title_stamp_executor_pdf()
    width_stamp = obj_where_store_stamp.width_stamp_jpg if obj_where_store_stamp.width_stamp_jpg else 1
    height_stamp = obj_where_store_stamp.height_stamp_jpg if obj_where_store_stamp.height_stamp_jpg else 1
    x_offset = obj_where_store_stamp.x_offset if obj_where_store_stamp.x_offset else 1
    y_offset = obj_where_store_stamp.y_offset if obj_where_store_stamp.y_offset else 1
    img = None
    if file_jpg:
        img = ImageWithOffset(file_jpg, width_stamp * mm, height_stamp * mm, x_offset=x_offset * mm, y_offset=y_offset * mm)
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


def text_to_bold(v):
    valid = check_valid_square_brackets(v)
    if valid:
        v = v.replace('[', '<font face=\"PTAstraSerifBold\">')
        v = v.replace(']', '</font>')

    return v
