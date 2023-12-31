import locale
import os.path
import sys
from copy import deepcopy
from io import BytesIO
from typing import List, Union
import simplejson as json
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from transliterate import translit
from directions.models import Napravleniya
from laboratory.settings import FONTS_FOLDER
from laboratory.utils import strdate, strtime
from podrazdeleniya.models import Podrazdeleniya
from utils import xh
from utils.xh import translation_number_from_decimal
from reportlab.graphics.barcode import qr
from reportlab.graphics.barcode import createBarcodeDrawing
from django.utils.text import Truncator
from django.core.paginator import Paginator


def form_01(request_data):
    """
    ширина 80 мм
    """


    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    # Генерировать pdf-Лист на оплату
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Symbola', os.path.join(FONTS_FOLDER, 'Symbola.ttf')))

    buffer = BytesIO()
    pagesize = (80 * mm, 850 * mm)
    doc = SimpleDocTemplate(
        buffer, pagesize=pagesize, leftMargin=2 * mm, rightMargin=0 * mm, topMargin=1 * mm, bottomMargin=1 * mm, allowSplitting=1, title="Форма {}".format("80 мм")
    )
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 8
    style.leading = 7
    style.spaceAfter = -1 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = -1 * mm

    styleFL = deepcopy(style)
    styleFL.firstLineIndent = 0
    styleFL.fontSize = 20

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 10
    styleCenter.leading = 10
    styleCenter.spaceAfter = 0 * mm

    styleCenterHospital = deepcopy(styleCenter)
    styleCenterHospital.fontSize = 8

    styleCenterTitle = deepcopy(styleCenter)
    styleCenterTitle.fontSize = 14

    styleTypeResearch = deepcopy(style)
    styleTypeResearch.firstLineIndent = -0.5 * mm

    objs: List[Union[Spacer, Paragraph, Table, KeepTogether]] = []

    directions = json.loads(request_data.get("napr_id", '[]'))
    for direction in sorted(directions):
        dir = Napravleniya.objects.filter(pk=direction).first()
        objs.append(Paragraph(f"{dir.hospital_short_title}", styleCenter))
        objs.append(Paragraph(f"({dir.hospital_address}, <br/>{dir.hospital_phones})", styleCenterHospital))
        objs.append(Paragraph("Направление", styleCenterTitle))
        objs.append(Spacer(1, 5 * mm))
        bcd = createBarcodeDrawing('EAN13', value=dir.pk + 460000000000, humanReadable=0, barHeight=8 * mm, width=45 * mm)
        bcd.hAlign = 'LEFT'

        opinion = [
            [
                Paragraph(f'{dir.pk}', styleFL),
                bcd,
            ],
        ]

        tbl = Table(opinion, colWidths=(33 * mm, 42 * mm))
        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 0.1, colors.white),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (1, 0), (-1, -1), -1 * mm),
                    ('LEFTPADDING', (0, 0), (-1, -1), -0.3 * mm),
                ]
            )
        )
        objs.append(tbl)

        opinion = [
            [Paragraph(f'Создано: {strdate(dir.data_sozdaniya)} {strtime(dir.data_sozdaniya)[:5]}', style), Paragraph('', style)],
            [Paragraph(f'ФИО: {dir.client.individual.fio()}', style), Paragraph(f'Код {translation_number_from_decimal(int(dir.client.pk))}', style)],
            [Paragraph(f'Номер карты: {dir.client.number_with_type()}', style), Paragraph(f'Д/р: {dir.client.individual.bd()}', style)],
            [Paragraph('Диагноз (МКБ 10):', style), Paragraph(f'({dir.client.individual.age_s(direction=dir)})–{dir.client.individual.sex}', style)],
            [Paragraph(f'Вид финансировния: {dir.client.base.title} - {dir.istochnik_f.title}', style), Paragraph('', style)],
        ]

        tbl = Table(opinion, colWidths=(53 * mm, 22 * mm))
        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 1 * mm),
                    ('TOPPADDING', (0, 0), (-1, -1), 0.5 * mm),
                ]
            )
        )

        objs.append(tbl)
        issledovaniya = dir.issledovaniya_set.all()

        vid = []
        has_descriptive = False
        has_doc_refferal = False
        need_qr_code = False
        values = []
        for i in issledovaniya:
            rtp = i.research.reversed_type
            if rtp < -1:
                has_doc_refferal = True
                rt = {
                    -2: 'Консультации',
                    -3: 'Лечение',
                    -4: 'Стоматология',
                    -5: 'Стационар',
                    -6: 'Микробиология',
                    -9998: 'Морфология',
                    -9: 'Формы',
                    -11: 'Заявления',
                    -12: 'Мониторинги',
                    -14: 'Случай',
                }[rtp]
                # if rtp == -6:
                #     has_micro = True
            else:
                rt = i.research.podrazdeleniye.get_title()
            if rt not in vid:
                vid.append(rt)
                if i.research.podrazdeleniye and i.research.podrazdeleniye.p_type == Podrazdeleniya.PARACLINIC:
                    has_descriptive = True
                    if i.research.podrazdeleniye.can_has_pacs:
                        need_qr_code = True
        objs.append(Paragraph(f'Вид: {", ".join(vid)}', styleTypeResearch))

        service_locations = {}
        n = 0
        opinion = []
        for v in issledovaniya:
            n += 1
            service_location_title = "" if not v.service_location else v.service_location.title
            if service_location_title:
                if service_location_title not in service_locations:
                    service_locations[service_location_title] = []
                service_locations[service_location_title].append(n)
            values.append(
                {
                    "title": v.research.get_title(),
                    "full_title": v.research.title,
                    "sw": v.research.sort_weight,
                    "count": v.how_many,
                    "comment": v.localization.title if v.localization else v.comment,
                    "n": n,
                    "g": -1 if not v.research.fractions_set.exists() else v.research.fractions_set.first().relation_id,
                    "info": v.research.paraclinic_info,
                    "hospital_department_replaced_title": v.hospital_department_replaced_title,
                }
            )
        one_sl = len(service_locations) <= 1
        ns = {}
        values.sort(key=lambda l: l["full_title"])
        if has_descriptive or has_doc_refferal:
            opinion = [[Paragraph("Назначение", style), Paragraph('Информация', style)]]

            for v in values:
                ns[v["n"]] = v["n"]
                tmp = [
                    Paragraph(
                        '<font face="OpenSans" size="8">'
                        + ("" if one_sl else "№{}: ".format(v["n"]))
                        + xh.fix(v["full_title"])
                        + ("" if not v["comment"] else " <font face=\"OpenSans\" size=\"" + str(8 * 0.8) + "\">[{}]</font>".format(v["comment"]))
                        + ("" if not v["hospital_department_replaced_title"] else f"<br/>Направлен в: {v['hospital_department_replaced_title']}")
                        + "</font>",
                        style,
                    ),
                    Paragraph('<font face="OpenSans" size="8">' + xh.fix(v["info"]) + "</font>", style),
                ]
                opinion.append(tmp)
        else:
            values.sort(key=lambda l: (l["g"], l["sw"]))
            n_rows = int(len(values) / 2)
            normvars = []
            c_cnt = nc_cnt = 0
            for i in range(0, len(values) + 1):
                if (i + 1) % 2 == 0:
                    nc_cnt += 1
                    if nc_cnt + n_rows < len(values):
                        normvars.append(values[nc_cnt + n_rows])
                else:
                    normvars.append(values[c_cnt])
                    c_cnt += 1

            p = Paginator(normvars, 2)
            n = 1
            for pg_num in p.page_range:
                pg = p.page(pg_num)
                tmp = []
                for obj in pg.object_list:
                    ns[obj["n"]] = n
                    tmp.append(Paragraph(f'{obj["title"]}', style))
                    n += 1
                if len(pg.object_list) < 2:
                    tmp.append(Paragraph('', style))
                opinion.append(tmp)

        tbl = Table(opinion, colWidths=(37 * mm, 37 * mm))
        tbl.setStyle(
            TableStyle(
                [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                    ('TOPPADDING', (0, 0), (-1, -1), 0.4 * mm),
                ]
            )
        )
        objs.append(Spacer(1, 1 * mm))
        objs.append(tbl)

        if need_qr_code:
            qr_value = translit(dir.client.individual.fio(), 'ru', reversed=True)
            qr_code = qr.QrCodeWidget(qr_value)
            qr_code.barWidth = 70
            qr_code.barHeight = 70
            qr_code.qrVersion = 1
            d = Drawing()
            d.add(qr_code)

            bcd = createBarcodeDrawing('QR', value=qr_value, width=70, height=70, humanReadable=0)
            bcd.hAlign = 'LEFT'

            opinion = [
                [
                    Paragraph(f'', styleFL),
                    bcd,
                ],
            ]

            tbl = Table(opinion, colWidths=(50 * mm, 25 * mm))
            tbl.setStyle(
                TableStyle(
                    [
                        ('GRID', (0, 0), (-1, -1), 0.1, colors.white),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (1, 0), (-1, -1), -1 * mm),
                        ('LEFTPADDING', (0, 0), (-1, -1), -0.3 * mm),
                    ]
                )
            )
            objs.append(Spacer(1, 2 * mm))
            objs.append(tbl)
        objs.append(Spacer(1, 2 * mm))
        if not dir.imported_from_rmis:
            if dir.doc_who_create and dir.doc_who_create != dir.doc:
                objs.append(Paragraph(f"Выписал:{Truncator(dir.doc_who_create.get_fio() (dir.doc_who_create.podrazdeleniye.title).chars(63))}", style))

            if dir.doc:
                objs.append(Paragraph(f"Отделение: {Truncator(dir.get_doc_podrazdeleniye_title()).chars(50)}", style))
                objs.append(Paragraph(f"Л/врач: {dir.doc.get_fio()}", style))

        opinion = [[Paragraph("", style)]]
        tbl = Table(opinion, colWidths=(90 * mm), rowHeights=0.1 * mm)
        tbl.setStyle(
            TableStyle(
                [
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                ]
            )
        )
        objs.append(Spacer(1, 9 * mm))
        objs.append(tbl)
        objs.append(Spacer(1, 5 * mm))

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
