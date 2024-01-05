import os
from copy import deepcopy

from django.core.exceptions import ObjectDoesNotExist
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import eanbc
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib import colors
from appconf.manager import SettingManager
from directions.models import Napravleniya
from reportlab.platypus import Table, TableStyle, Paragraph, Frame, Spacer, KeepInFrame
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Image

from directory.models import Fractions
from laboratory.utils import strdate, strtime
import sys
import locale
from reportlab.lib.colors import black, HexColor
from laboratory.settings import FONTS_FOLDER
from directions.models import Issledovaniya
from utils.flowable import InteractiveTextField


def form_01(c: Canvas, dir: Napravleniya):
    # Диагностический центр - COVID-19
    def printForm():
        hospital_name = dir.hospital_short_title

        if sys.platform == "win32":
            locale.setlocale(locale.LC_ALL, "rus_rus")
        else:
            locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")

        pdfmetrics.registerFont(TTFont("PTAstraSerifBold", os.path.join(FONTS_FOLDER, "PTAstraSerif-Bold.ttf")))
        pdfmetrics.registerFont(TTFont("PTAstraSerifReg", os.path.join(FONTS_FOLDER, "PTAstraSerif-Regular.ttf")))
        pdfmetrics.registerFont(TTFont("PTAstraSerifBoldItalic", os.path.join(FONTS_FOLDER, "PTAstraSerif-BoldItalic.ttf")))
        pdfmetrics.registerFont(TTFont("Symbola", os.path.join(FONTS_FOLDER, "Symbola.ttf")))

        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = "PTAstraSerifReg"
        style.fontSize = 10
        style.leading = 14
        style.borderColor = black
        style.alignment = TA_CENTER

        styleLeft = deepcopy(style)
        styleLeft.alignment = TA_LEFT

        styleRight = deepcopy(style)
        styleRight.alignment = TA_RIGHT

        styleFontEight = deepcopy(style)
        styleFontEight.fontSize = 8

        styleBoldItalic = deepcopy(style)
        styleBoldItalic.fontName = "PTAstraSerifBoldItalic"
        styleBoldItalic.fontSize = 12

        # ширина ячеек
        frame_left_padding = 11.7 * mm
        even, odd = 4.07 * mm, 1.09 * mm
        thick_dashed_for_symbol = 0.7
        step_round_dash = (0.03 * mm, 1 * mm)
        round_dash = "round"

        type_dash = "round"
        step_dash = step_round_dash
        # color_dash_for_symbol = HexColor('#5b5e5c')
        color_dash_for_symbol = HexColor("#b3b3b3")

        objs = []
        space_symbol = "&nbsp;"

        opinion = [
            [
                Paragraph(" ", styleFontEight),
                Paragraph('<font size="10">Печать</font><br/> направляющей медицинской <br/> организации', styleFontEight),
                Paragraph("", style),
                Paragraph("Штрих-код пробирки", style),
            ],
        ]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=27 * mm, colWidths=(63 * mm, 51 * mm, 13 * mm, 50 * mm))
        tbl.setStyle(
            TableStyle(
                [
                    ("INNERGRID", (1, 0), (1, 0), 1.5, colors.black, "round", step_round_dash),
                    ("OUTLINE", (1, 0), (1, 0), 1.5, colors.black, "round", step_round_dash),
                    ("INNERGRID", (3, 0), (3, 0), 1.5, colors.black),
                    ("OUTLINE", (3, 0), (3, 0), 1.5, colors.black),
                    ("BOTTOMPADDING", (1, 0), (1, 0), 5 * mm),
                    ("BOTTOMPADDING", (3, 0), (3, 0), 10 * mm),
                ]
            )
        )
        objs.append(Spacer(1, 1.3 * mm))
        objs.append(tbl)
        objs.append(Spacer(1, 1.5 * mm))
        objs.append(Paragraph("Наименование направляющего учреждения", styleLeft))
        hospital_name = list(hospital_name)
        count = 36 * 2
        opinion = [Paragraph(" ", style) for i in range(0, count)]
        x = 0
        for i in hospital_name:
            opinion[x] = Paragraph(f"{i}", style)
            x += 2

        opinion = [opinion]
        col_width = create_dot_table(count, odd, even)
        col_width = tuple(col_width)
        tbl = Table(opinion, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)

        a = [("OUTLINE", (i, 0), (i, 0), thick_dashed_for_symbol, color_dash_for_symbol, type_dash, step_dash) for i in range(0, count) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), 0.1 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.2 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        tbl.setStyle(TableStyle(a))
        objs.append(Spacer(1, 1 * mm))
        objs.append(tbl)

        objs.append(Spacer(1, 1 * mm))
        objs.append(Paragraph("Отделение", styleLeft))
        count = 23 * 2
        opinion = [Paragraph(" ", style) for i in range(0, count)]
        len_opinion = int(count / 2)
        department_title = list(dir.get_doc_podrazdeleniye_title().upper())[0:len_opinion]
        x = 0
        for i in department_title:
            opinion[x] = Paragraph(f"{i}", style)
            x += 2
        opinion = [opinion]
        col_width = create_dot_table(count, odd, even)
        col_width = tuple(col_width)
        tbl = Table(opinion, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
        a = [("OUTLINE", (i, 0), (i, 0), thick_dashed_for_symbol, color_dash_for_symbol, type_dash, step_dash) for i in range(0, count) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), 0.1 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.2 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        tbl.setStyle(TableStyle(a))
        objs.append(tbl)
        objs.append(Spacer(1, 1 * mm))
        objs.append(Paragraph("Ф.И.О. врача", styleLeft))
        count = 20 * 2
        opinion = [Paragraph(" ", style) for i in range(0, count)]
        len_opinion = int(count / 2)
        doc_fio = list(dir.doc.get_fio().upper())[0:len_opinion]
        x = 0
        for i in doc_fio:
            opinion[x] = Paragraph(f"{i}", style)
            x += 2
        opinion = [opinion]
        col_width = create_dot_table(count, odd, even)
        col_width = tuple(col_width)
        tbl = Table(opinion, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
        a = [("OUTLINE", (i, 0), (i, 0), thick_dashed_for_symbol, color_dash_for_symbol, type_dash, step_dash) for i in range(0, count) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), 0.1 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.2 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        tbl.setStyle(TableStyle(a))
        objs.append(tbl)
        objs.append(Spacer(1, 2 * mm))
        objs.append(Paragraph('<font size="12">НАПРАВЛЕНИЕ НА ЛАБОРАТОРНОЕ ИССЛЕДОВАНИЕ</font>', styleBoldItalic))
        objs.append(Paragraph('<font size="12">качественное определение РНК коронавируса (SARS-CoV-2)</font>', styleBoldItalic))
        organization_frame = Frame(0 * mm, 212 * mm, 212.5 * mm, 75 * mm, leftPadding=frame_left_padding, bottomPadding=0 * mm, rightPadding=12 * mm, topPadding=0 * mm, showBoundary=0)
        organization_frame.addFromList(objs, c)

        patient_fio = []
        count = 18 * 2
        col_width = create_dot_table(count, odd, even)
        col_width.insert(0, odd)
        col_width.insert(0, 15 * mm)
        opinion = [Paragraph(" ", style) for i in range(0, 38)]
        opinion_family = opinion.copy()
        opinion_family[0] = Paragraph("Фамилия", styleRight)
        full_name_individual, family_individual = (
            "",
            "",
        )
        fio_individual = dir.client.individual.fio()
        full_name_individual = split_fio(fio_individual)
        if len(full_name_individual) > 0:
            family_individual = full_name_individual[0]
            family_individual = list(family_individual.upper())[0:17]
        x = 2
        for i in family_individual:
            opinion_family[x] = Paragraph(f"{i}", style)
            x += 2
        opinion_family = [opinion_family]
        col_width = tuple(col_width)
        tbl_family = Table(opinion_family, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
        a = [("OUTLINE", (i, 0), (i, 0), thick_dashed_for_symbol, color_dash_for_symbol, type_dash, step_dash) for i in range(2, count) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), 0.1 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.2 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        tbl_family.setStyle(TableStyle(a))
        patient_fio.append(tbl_family)
        opinion_name = opinion.copy()
        opinion_name[0] = Paragraph("Имя", styleRight)
        name_individual = ""
        if len(full_name_individual) > 1:
            name_individual = full_name_individual[1]
            name_individual = list(name_individual.upper())[0:17]
        x = 2
        for i in name_individual:
            opinion_name[x] = Paragraph(f"{i}", style)
            x += 2
        opinion_name = [opinion_name]
        tbl_name = Table(opinion_name, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
        tbl_name.setStyle(TableStyle(a))
        patient_fio.append(Spacer(1, 1.7 * mm))
        patient_fio.append(tbl_name)
        opinion_patronymic = opinion.copy()
        opinion_patronymic[0] = Paragraph("Отчество", styleRight)
        patronymic_individual = ""
        if len(full_name_individual) > 2:
            patronymic_individual = full_name_individual[2]
            patronymic_individual = list(patronymic_individual.upper())[0:17]
        x = 2
        for i in patronymic_individual:
            opinion_patronymic[x] = Paragraph(f"{i}", style)
            x += 2
        opinion_patronymic = [opinion_patronymic]
        tbl_patronymic = Table(opinion_patronymic, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
        tbl_patronymic.setStyle(TableStyle(a))
        patient_fio.append(Spacer(1, 1.9 * mm))
        patient_fio.append(tbl_patronymic)
        patient_fio_frame = Frame(0 * mm, 189 * mm, 126 * mm, 22 * mm, leftPadding=9 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=2 * mm, showBoundary=0)
        patient_fio_frame.addFromList(patient_fio, c)

        polis_data = []
        polis_data.append(Paragraph("Серия полиса", styleLeft))
        count = 6 * 2
        col_width = create_dot_table(count, odd, even)
        opinion = [[Paragraph(" ", style) for i in range(0, count)]]
        col_width = tuple(col_width)
        tbl = Table(opinion, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
        a = [("OUTLINE", (i, 0), (i, 0), 0.7, color_dash_for_symbol, type_dash, step_dash) for i in range(0, count) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), 0.1 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.2 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        tbl.setStyle(TableStyle(a))
        polis_data.append(tbl)
        polis_data.append(Spacer(1, 0.8 * mm))
        polis_data.append(Paragraph("Номер полиса", styleLeft))
        count = 16 * 2
        col_width = create_dot_table(count, odd, even)
        col_width = tuple(col_width)
        opinion = [Paragraph(" ", style) for i in range(0, count)]
        polis_num = ""
        ind_data = dir.client.get_data_individual()
        if ind_data["oms"]["polis_num"]:
            polis_num = list(ind_data["oms"]["polis_num"])[0:16]
        x = 0
        for i in polis_num:
            opinion[x] = Paragraph(f"{i}", style)
            x += 2
        opinion = [opinion]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
        a = [("OUTLINE", (i, 0), (i, 0), 0.7, color_dash_for_symbol, type_dash, step_dash) for i in range(0, count) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), 0.1 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.2 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        tbl.setStyle(TableStyle(a))
        polis_data.append(tbl)
        polis_data_frame = Frame(116 * mm, 189 * mm, 95 * mm, 22 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        polis_data_frame.addFromList(polis_data, c)

        born_data = []
        count = 10 * 2
        col_width = create_dot_table(count, odd, even)
        col_width = tuple(col_width)
        opinion = [Paragraph(" ", style) for i in range(0, count)]
        date_born = dir.client.individual.bd()
        x = 0
        for i in date_born:
            opinion[x] = Paragraph(f"{i}", style)
            x += 2
        opinion = [opinion]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
        a = [("OUTLINE", (i, 0), (i, 0), 0.7, color_dash_for_symbol, type_dash, step_dash) for i in range(0, count) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), 0.1 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.2 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        a.pop(2)
        a.pop(4)
        tbl.setStyle(TableStyle(a))
        born_data.append(Paragraph(f"Число {space_symbol * 4} Месяц {space_symbol * 5} Год рождения", styleLeft))
        born_data.append(Spacer(1, 0.6 * mm))
        born_data.append(tbl)
        born_data_frame = Frame(0 * mm, 179 * mm, 65 * mm, 11 * mm, leftPadding=10 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        born_data_frame.addFromList(born_data, c)

        sex_data = []
        styleSex = deepcopy(style)
        styleSex.fontSize = 10
        female, male = " ", " "
        is_check_data = '<font face="Symbola" size=13>\u2713</font>'
        if dir.client.individual.sex == "ж":
            female = is_check_data
        else:
            male = is_check_data

        opinion = [
            [Paragraph("Пол", styleSex), Paragraph(male, styleSex), Paragraph("М", styleSex)],
            [Paragraph("", styleSex), Paragraph("", styleSex), Paragraph(" ", styleSex)],
            [Paragraph("", styleSex), Paragraph(female, styleSex), Paragraph("Ж", styleSex)],
        ]

        col_width = [10 * mm, 3.5 * mm, 7 * mm]
        row_height = [3.5 * mm, 1.5 * mm, 3.5 * mm]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=row_height, colWidths=col_width)
        a = [
            ("OUTLINE", (1, 0), (1, 0), 1, colors.black),
            ("OUTLINE", (1, 2), (1, 2), 1, colors.black),
        ]
        a.extend(
            [
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 0.8 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0.05 * mm),
                ("BOTTOMPADDING", (0, 0), (0, -1), 3 * mm),
                ("BOTTOMPADDING", (1, 0), (1, 0), -0.2 * mm),
                ("BOTTOMPADDING", (1, 2), (1, 2), -0.2 * mm),
                ("SPAN", (0, 0), (0, -1)),
            ]
        )
        tbl.setStyle(TableStyle(a))
        sex_data.append(Spacer(1, 1 * mm))
        sex_data.append(tbl)
        sex_data_frame = Frame(66 * mm, 178 * mm, 50 * mm, 11 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        sex_data_frame.addFromList(sex_data, c)

        contact_data = []
        count = 11 * 2
        col_width = create_dot_table(count, odd, even)
        opinion = [Paragraph(" ", style) for i in range(0, count)]
        phone_num = dir.client.get_phones()
        tel = []
        if len(phone_num) > 0:
            tel = list(phone_num[0])[0:11]
        x = 0
        if len(tel) > 0:
            for i in tel:
                opinion[x] = Paragraph(f"{i}", style)
                x += 2
        col_width = tuple(col_width)
        opinion = [opinion]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
        a = [("OUTLINE", (i, 0), (i, 0), 0.7, color_dash_for_symbol, type_dash, step_dash) for i in range(0, count) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), 0.1 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.2 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        tbl.setStyle(TableStyle(a))
        contact_data.append(Paragraph("Контактный телефон", styleLeft))
        contact_data.append(tbl)
        contact_data_frame = Frame(116 * mm, 179 * mm, 95 * mm, 11 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        contact_data_frame.addFromList(contact_data, c)

        address_data = []
        main_address = dir.client.main_address
        fact_address = dir.client.fact_address if dir.client.fact_address else main_address
        work_place = dir.workplace

        opinion = [
            [Paragraph("Адрес региcтрации", styleLeft), Paragraph(main_address, styleLeft), Paragraph("", styleLeft)],
            [Paragraph("Адрес фактический", styleLeft), Paragraph(fact_address, styleLeft), Paragraph("", styleLeft)],
            [Paragraph("Место работы/учебы, должность", styleLeft), Paragraph("", styleLeft), Paragraph(work_place, styleLeft)],
        ]

        col_width = [32 * mm, 20 * mm, 137 * mm]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=4.4 * mm, colWidths=col_width)
        a = [("GRID", (0, 0), (-1, -1), 0.2, color_dash_for_symbol)]
        a.extend(
            [
                ("BOTTOMPADDING", (0, 0), (-1, -1), -0.65 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 0.1 * mm),
                ("SPAN", (1, 0), (2, 0)),
                ("SPAN", (1, 1), (2, 1)),
                ("SPAN", (0, 2), (1, 2)),
                ("GRID", (0, 0), (-1, -1), 1, colors.white),
                ("LINEBELOW", (1, 0), (-1, 0), 0.5, color_dash_for_symbol, "round", (0.5, 1.5)),
                ("LINEBELOW", (1, 1), (-1, 1), 0.5, color_dash_for_symbol, "round", (0.5, 1.5)),
                ("LINEBELOW", (2, 2), (2, -1), 0.5, color_dash_for_symbol, "round", (0.5, 1.5)),
            ]
        )
        tbl.setStyle(TableStyle(a))
        address_data.append(tbl)
        address_frame = Frame(0 * mm, 164 * mm, 212 * mm, 14 * mm, leftPadding=10 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        address_frame.addFromList(address_data, c)

        diagnos_data_t = []
        opinion = [[Paragraph("", styleLeft)]]
        col_width = [189 * mm]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=14 * mm, colWidths=col_width)
        a = [("GRID", (0, 0), (-1, -1), 1.2, color_dash_for_symbol, None, (1.5, 1.5, 1.5))]
        tbl.setStyle(TableStyle(a))
        diagnos_data_t.append(tbl)
        diagnos_t_frame = Frame(0 * mm, 148.5 * mm, 210 * mm, 15 * mm, leftPadding=10 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        diagnos_t_frame.addFromList(diagnos_data_t, c)

        diagnos_data = []
        opinion = [Paragraph("Предварительный диагноз", styleLeft), Paragraph("", styleLeft)]
        col_width = [42 * mm, 144 * mm]
        opinion = [opinion]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
        a = [
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0.05 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 0.1 * mm),
            ("LINEBELOW", (1, 0), (1, 0), 0.5, color_dash_for_symbol, None, (1, 1, 1)),
        ]
        tbl.setStyle(TableStyle(a))
        diagnos_data.append(tbl)
        diagnos_frame = Frame(14 * mm, 149 * mm, 187 * mm, 15 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        diagnos_frame.addFromList(diagnos_data, c)

        start_ill_data = []
        count = 10 * 2
        col_width = create_dot_table(count, odd, even)
        col_width.insert(0, odd)
        col_width.insert(0, 28 * mm)
        col_width = tuple(col_width)
        opinion = [Paragraph(" ", style) for i in range(0, count + 2)]
        opinion = opinion.copy()
        opinion[0] = Paragraph("Дата заболевания:", styleRight)
        start_ill = "  .  .    "
        create_date = strdate(dir.data_sozdaniya)
        x = 2
        if start_ill:
            for i in start_ill:
                opinion[x] = Paragraph(f"{i}", style)
                x += 2
        opinion = [opinion]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
        a = [("OUTLINE", (i, 0), (i, 0), 0.7, color_dash_for_symbol, round_dash, step_round_dash) for i in range(2, count + 2) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), 0.1 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.2 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        a.pop(2)
        a.pop(4)
        tbl.setStyle(TableStyle(a))
        start_ill_data.append(tbl)
        start_ill_data_frame = Frame(115 * mm, 150.5 * mm, 52 * mm, 6 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        start_ill_data_frame.addFromList(start_ill_data, c)

        kod_mkb_data = []
        count = 5 * 2
        col_width = create_dot_table(count, odd, even)
        col_width.insert(0, odd)
        col_width.insert(0, 21 * mm)
        col_width = tuple(col_width)
        opinion = [Paragraph(" ", style) for i in range(0, count + 2)]
        opinion = opinion.copy()
        opinion[0] = Paragraph("Код по МКБ:", styleRight)
        kod_mkb = ""
        x = 2
        if kod_mkb:
            for i in kod_mkb:
                opinion[x] = Paragraph(f"{i}", style)
                x += 2
        opinion = [opinion]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
        a = [("OUTLINE", (i, 0), (i, 0), 0.7, color_dash_for_symbol, "round", (0.03 * mm, 1 * mm)) for i in range(2, count + 2) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), 0.1 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.2 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        tbl.setStyle(TableStyle(a))
        kod_mkb_data.append(tbl)
        kod_mkb_data_frame = Frame(28 * mm, 150.5 * mm, 52 * mm, 6 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        kod_mkb_data_frame.addFromList(kod_mkb_data, c)

        country_data_t = []
        opinion = [[Paragraph("", styleLeft)]]
        col_width = [189 * mm]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=25 * mm, colWidths=col_width)
        a = [("GRID", (0, 0), (-1, -1), 1.2, color_dash_for_symbol, None, (1.5, 1.5, 1.5))]
        tbl.setStyle(TableStyle(a))
        country_data_t.append(tbl)
        country_t_frame = Frame(0 * mm, 121.5 * mm, 210 * mm, 25.5 * mm, leftPadding=10 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        country_t_frame.addFromList(country_data_t, c)

        country_data = []
        opinion = [Paragraph("Страна прибытия/регион (для прибывших в течение 14 дней на территорию пребывания):", styleLeft), Paragraph("", styleLeft)]
        col_width = [138 * mm, 48 * mm]
        opinion = [opinion]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
        a = [
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0.05 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 0.1 * mm),
            ("LINEBELOW", (1, 0), (1, 0), 0.5, color_dash_for_symbol, None, (1, 1, 1)),
        ]
        tbl.setStyle(TableStyle(a))
        country_data.append(tbl)
        country_data.append(HRFlowable(width=184.5 * mm, lineCap="round", thickness=0.5, spaceAfter=0.1 * mm, spaceBefore=4 * mm, color=color_dash_for_symbol, dash=(0.5, 1.5)))
        country_data.append(Paragraph(f"{space_symbol * 15}Дата прибывания{space_symbol * 35}Время взятия образца{space_symbol * 35}Время отправки образца", styleLeft))
        country_data.append(Spacer(1, 5.2 * mm))
        country_data.append(Paragraph(f"{space_symbol * 81}день{space_symbol * 26}час{space_symbol * 32}день{space_symbol * 26}час", styleLeft))
        country_frame = Frame(14 * mm, 122 * mm, 187 * mm, 24.5 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        country_frame.addFromList(country_data, c)

        date_arrive_data = []
        count = 10 * 2
        col_width = create_dot_table(count, odd, even)
        col_width = tuple(col_width)
        opinion = [Paragraph(" ", style) for i in range(0, count)]
        opinion[4] = Paragraph(".", style)
        opinion[10] = Paragraph(".", style)
        opinion = [opinion]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
        a = [("OUTLINE", (i, 0), (i, 0), 0.7, color_dash_for_symbol, type_dash, step_dash) for i in range(0, count) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), 0.1 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.2 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        a.pop(2)
        a.pop(4)
        tbl.setStyle(TableStyle(a))
        date_arrive_data.append(tbl)
        date_arrive_data_frame = Frame(16 * mm, 127 * mm, 52 * mm, 5 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        date_arrive_data_frame.addFromList(date_arrive_data, c)

        day_get_date = ""
        if create_date:
            day_get_date = create_date[0:5]
        day_get_material = [four_obj_date(odd, even, style, type_dash, step_dash, day_get_date, color_dash_for_symbol)]
        day_get_material_frame = Frame(75.4 * mm, 127 * mm, 25 * mm, 5 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        day_get_material_frame.addFromList(day_get_material, c)

        time_get_date = ""
        if create_date:
            time_get_date = strtime(dir.data_sozdaniya)[:5].replace(":", ".")
        time_get_material = [four_obj_date(odd, even, style, type_dash, step_dash, time_get_date, color_dash_for_symbol)]
        time_get_material_frame = Frame(105.1 * mm, 127 * mm, 25 * mm, 5 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        time_get_material_frame.addFromList(time_get_material, c)

        day_out_material = [four_obj_date(odd, even, style, type_dash, step_dash, day_get_date, color_dash_for_symbol)]
        day_out_material_frame = Frame(139.1 * mm, 127 * mm, 25 * mm, 5 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        day_out_material_frame.addFromList(day_out_material, c)

        time_out_material = [four_obj_date(odd, even, style, type_dash, step_dash, "", color_dash_for_symbol)]
        time_out_material_frame = Frame(168.1 * mm, 127 * mm, 25 * mm, 5 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        time_out_material_frame.addFromList(time_out_material, c)

        type_material_t = []
        opinion = [[Paragraph("", styleLeft)]]
        col_width = [189 * mm]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=14 * mm, colWidths=col_width)
        a = [("GRID", (0, 0), (-1, -1), 1.2, color_dash_for_symbol, None, (1.5, 1.5, 1.5))]
        tbl.setStyle(TableStyle(a))
        type_material_t.append(tbl)
        type_material_t_frame = Frame(0 * mm, 105 * mm, 210 * mm, 14 * mm, leftPadding=10 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        type_material_t_frame.addFromList(type_material_t, c)

        type_material = []
        type_material.append(Spacer(1, 0.5 * mm))
        type_material.append(Paragraph("Вид материала:", styleLeft))
        count = 6
        col_width = [2.5 * mm, 81 * mm, 2.5 * mm, 53.5 * mm, 2.5 * mm, 35 * mm]
        col_width = tuple(col_width)
        opinion = [Paragraph(" ", style) for i in range(0, count)]

        iss = Issledovaniya.objects.get(napravleniye=dir.pk)
        service_location_title = "" if not iss.service_location else iss.service_location.title
        localization0, localization1, localization2, localization3, localization4, localization5 = "", "", "", "", "", ""
        type_ischeck = '<font face="Symbola" size=10>\u2713</font>'
        if service_location_title:
            if service_location_title == "Мазок/отделяемое из носоглотки и ротоглотки":
                localization0 = type_ischeck
            elif service_location_title == "Мокрота":
                localization1 = type_ischeck
            elif service_location_title == "Аспират из трахеи":
                localization2 = type_ischeck
            elif service_location_title == "Биопсийный (аутопсийный) материал":
                localization3 = type_ischeck
            elif service_location_title == "Бронхоальвеолярный лаваж":
                localization4 = type_ischeck
            elif service_location_title == "Кровь (сыворотка)":
                localization5 = type_ischeck
        opinion[0] = [Paragraph(localization0, styleLeft)]
        opinion[1] = [Paragraph("Мазок/отделяемое из носоглотки и ротоглотки", styleLeft)]
        opinion[2] = [Paragraph(localization1, styleLeft)]
        opinion[3] = [Paragraph("Мокрота", styleLeft)]
        opinion[4] = [Paragraph(localization2, styleLeft)]
        opinion[5] = [Paragraph("Аспират из трахеи", styleLeft)]
        opinion_t = [opinion]
        tbl = Table(opinion_t, hAlign="LEFT", rowHeights=2.5 * mm, colWidths=col_width)
        a = [("OUTLINE", (i, 0), (i, 0), 1, colors.black) for i in range(0, count) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), -1.4 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.3 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        a.extend([("LEFTPADDING", (1, 0), (1, 0), 1 * mm), ("LEFTPADDING", (3, 0), (3, 0), 1 * mm), ("LEFTPADDING", (5, 0), (5, 0), 1 * mm)])
        a.extend([("BOTTOMPADDING", (0, 0), (0, 0), -1.6 * mm)])
        tbl.setStyle(TableStyle(a))
        type_material.append(Spacer(1, 1.8 * mm))
        type_material.append(tbl)
        type_material.append(Spacer(1, 1.7 * mm))
        opinion_second = opinion.copy()
        opinion_second[0] = [Paragraph(localization3, styleLeft)]
        opinion_second[1] = [Paragraph("Биопсийный (аутопсийный) материал", styleLeft)]
        opinion_second[2] = [Paragraph(localization4, styleLeft)]
        opinion_second[3] = [Paragraph("Бронхоальвеолярный лаваж", styleLeft)]
        opinion_second[4] = [Paragraph(localization5, styleLeft)]
        opinion_second[5] = [Paragraph("Кровь (сыворотка)", styleLeft)]
        opinion_t = [opinion_second]
        tbl = Table(opinion_t, hAlign="LEFT", rowHeights=2.5 * mm, colWidths=col_width)
        a = [("OUTLINE", (i, 0), (i, 0), 1, colors.black) for i in range(0, count) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), -1.4 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.3 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        a.extend([("LEFTPADDING", (1, 0), (1, 0), 1 * mm), ("LEFTPADDING", (3, 0), (3, 0), 1 * mm), ("LEFTPADDING", (5, 0), (5, 0), 1 * mm)])
        tbl.setStyle(TableStyle(a))
        type_material.append(tbl)
        type_material_frame = Frame(11.7 * mm, 105.6 * mm, 187 * mm, 14.5 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        type_material_frame.addFromList(type_material, c)

        category_patient_t = []
        opinion = [[Paragraph("", styleLeft)]]
        col_width = [189 * mm]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=23 * mm, colWidths=col_width)
        a = [("GRID", (0, 0), (-1, -1), 1.2, color_dash_for_symbol, None, (1.5, 1.5, 1.5))]
        tbl.setStyle(TableStyle(a))
        category_patient_t.append(tbl)
        category_patient_t_frame = Frame(0 * mm, 79 * mm, 210 * mm, 23 * mm, leftPadding=10 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        category_patient_t_frame.addFromList(category_patient_t, c)
        category_patient = []
        category_patient_data = iss.localization.title if iss.localization else iss.comment
        count = 6
        col_width = [2.5 * mm, 77.6 * mm, 2.5 * mm, 58 * mm, 2.5 * mm, 41 * mm]
        col_width = tuple(col_width)
        opinion = [Paragraph(" ", style) for i in range(0, count)]
        category_patient0, category_patient1, category_patient2, category_patient3, category_patient4, category_patient5 = "", "", "", "", "", ""
        category_patient6, category_patient7, category_patient8, category_patient9, category_patient10 = "", "", "", "", ""
        own_category = ""
        if category_patient_data == "Диагноз COVID-2019 (10 и 12 день)":
            category_patient0 = type_ischeck
        elif category_patient_data == "Прибывшие с признаками ОРВИ":
            category_patient1 = type_ischeck
        elif category_patient_data == "Медицинские работники":
            category_patient2 = type_ischeck
        elif category_patient_data == "Внебольничная пневмония":
            category_patient3 = type_ischeck
        elif category_patient_data == "Больные с тяжелым течением ОРВИ":
            category_patient4 = type_ischeck
        elif category_patient_data == "Прибывшие (10, 12 день)":
            category_patient5 = type_ischeck
        elif category_patient_data == "Контакт с больными COVID-2019":
            category_patient6 = type_ischeck
        elif category_patient_data == "Старше 65 лет с признаками ОРВИ":
            category_patient7 = type_ischeck
        elif category_patient_data == "Плановая госпитализация":
            category_patient8 = type_ischeck
        elif category_patient_data == "Прочие":
            category_patient9 = type_ischeck
        elif category_patient_data == "Больные с ОРВИ, в учреждении пост. пребывания":
            category_patient10 = type_ischeck
        else:
            category_patient9 = type_ischeck
            own_category = category_patient_data

        category_patient.append(Paragraph(f"Категория обследуемого: <u>{own_category}</u>", styleLeft))
        opinion[0] = [Paragraph(category_patient0, styleLeft)]
        opinion[1] = [Paragraph("Диагноз COVID-2019 (10 и 12 день)", styleLeft)]
        opinion[2] = [Paragraph(category_patient1, styleLeft)]
        opinion[3] = [Paragraph("Прибывшие с признаками ОРВИ", styleLeft)]
        opinion[4] = [Paragraph(category_patient2, styleLeft)]
        opinion[5] = [Paragraph("Медицинские работники", styleLeft)]
        opinion_t = [opinion]
        tbl = Table(opinion_t, hAlign="LEFT", rowHeights=2.5 * mm, colWidths=col_width)
        a = [("OUTLINE", (i, 0), (i, 0), 1, colors.black) for i in range(0, count) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), -1.4 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.3 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        a.extend([("LEFTPADDING", (1, 0), (1, 0), 1 * mm), ("LEFTPADDING", (3, 0), (3, 0), 1 * mm), ("LEFTPADDING", (5, 0), (5, 0), 1 * mm)])
        a.extend([("BOTTOMPADDING", (4, 0), (4, 0), -1.6 * mm)])
        tbl.setStyle(TableStyle(a))
        category_patient.append(Spacer(1, 1 * mm))
        category_patient.append(tbl)
        category_patient.append(Spacer(1, 1.5 * mm))
        opinion_second = [Paragraph(" ", style) for i in range(0, count)]
        opinion_second[0] = [Paragraph(category_patient3, styleLeft)]
        opinion_second[1] = [Paragraph("Внебольничная пневмония", styleLeft)]
        opinion_second[2] = [Paragraph(category_patient4, styleLeft)]
        opinion_second[3] = [Paragraph("Больные с тяжелым течением ОРВИ", styleLeft)]
        opinion_second[4] = [Paragraph(category_patient5, styleLeft)]
        opinion_second[5] = [Paragraph("Прибывшие (10, 12 день)", styleLeft)]
        opinion_t = [opinion_second]
        tbl = Table(opinion_t, hAlign="LEFT", rowHeights=2.5 * mm, colWidths=col_width)
        a = [("OUTLINE", (i, 0), (i, 0), 1, colors.black) for i in range(0, count) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), -1.4 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.3 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        a.extend([("LEFTPADDING", (1, 0), (1, 0), 1 * mm), ("LEFTPADDING", (3, 0), (3, 0), 1 * mm), ("LEFTPADDING", (5, 0), (5, 0), 1 * mm)])
        tbl.setStyle(TableStyle(a))
        category_patient.append(tbl)
        category_patient.append(Spacer(1, 1.5 * mm))
        opinion_third = [Paragraph(" ", style) for i in range(0, count)]
        opinion_third[0] = [Paragraph(category_patient6, styleLeft)]
        opinion_third[1] = [Paragraph("Контакт с больными COVID-2019", styleLeft)]
        opinion_third[2] = [Paragraph(category_patient7, styleLeft)]
        opinion_third[3] = [Paragraph("Старше 65 лет с признаками ОРВИ", styleLeft)]
        opinion_third[4] = [Paragraph(category_patient8, styleLeft)]
        opinion_third[5] = [Paragraph("Плановая госпитализация", styleLeft)]
        opinion_t = [opinion_third]
        tbl = Table(opinion_t, hAlign="LEFT", rowHeights=2.5 * mm, colWidths=col_width)
        a = [("OUTLINE", (i, 0), (i, 0), 1, colors.black) for i in range(0, count) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), -1.4 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.3 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        a.extend([("LEFTPADDING", (1, 0), (1, 0), 1 * mm), ("LEFTPADDING", (3, 0), (3, 0), 1 * mm), ("LEFTPADDING", (5, 0), (5, 0), 1 * mm)])
        tbl.setStyle(TableStyle(a))
        category_patient.append(tbl)

        count = 4
        col_width = [2.5 * mm, 77.6 * mm, 2.5 * mm, 98 * mm]
        col_width = tuple(col_width)
        opinion_four = [Paragraph(" ", style) for i in range(0, count)]
        opinion_four[0] = [Paragraph(category_patient9, styleLeft)]
        opinion_four[1] = [Paragraph("Прочие", styleLeft)]
        opinion_four[2] = [Paragraph(category_patient10, styleLeft)]
        opinion_four[3] = [Paragraph("Больные с ОРВИ, в учреждении пост. пребывания", styleLeft)]
        opinion_t = [opinion_four]
        tbl = Table(opinion_t, hAlign="LEFT", rowHeights=2.5 * mm, colWidths=col_width)
        a = [("OUTLINE", (i, 0), (i, 0), 1, colors.black) for i in range(0, count) if i % 2 == 0]
        a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), -1.4 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.3 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
        a.extend([("LEFTPADDING", (1, 0), (1, 0), 1 * mm), ("LEFTPADDING", (3, 0), (3, 0), 1 * mm)])
        a.extend([("BOTTOMPADDING", (0, 0), (0, 0), -1.6 * mm)])
        tbl.setStyle(TableStyle(a))
        category_patient.append(Spacer(1, 1.8 * mm))
        category_patient.append(tbl)
        category_patient_frame = Frame(11.4 * mm, 79.5 * mm, 187 * mm, 22.5 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        category_patient_frame.addFromList(category_patient, c)

        anamnes_and_picker_t = []
        opinion = [[Paragraph("", styleLeft)]]
        col_width = [189 * mm]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=18 * mm, colWidths=col_width)
        a = [("GRID", (0, 0), (-1, -1), 1.2, colors.white, None, (1.5, 1.5, 1.5))]
        tbl.setStyle(TableStyle(a))
        anamnes_and_picker_t.append(tbl)
        anamnes_and_picker_t_frame = Frame(0 * mm, 60 * mm, 210 * mm, 18 * mm, leftPadding=10 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        anamnes_and_picker_t_frame.addFromList(anamnes_and_picker_t, c)

        anamnes_and_picker = []
        col_width = [24.5 * mm, 165 * mm]
        col_width = tuple(col_width)
        opinion = [Paragraph("ЭпидАнамнез:", styleLeft), Paragraph(" ", style)]
        opinion = [opinion]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
        a = [
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0.05 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 0.1 * mm),
            ("LINEBELOW", (1, 0), (1, 0), 0.5, colors.black, None, (1, 1, 1)),
        ]
        tbl.setStyle(TableStyle(a))
        anamnes_and_picker.append(tbl)
        anamnes_and_picker.append(HRFlowable(width=185.5 * mm, lineCap="round", thickness=0.5, spaceAfter=0.1 * mm, spaceBefore=4 * mm, color=colors.black, dash=(0.5, 1.5)))
        col_width = [107 * mm, 78 * mm]
        col_width = tuple(col_width)
        opinion = [Paragraph("Должность, ФИО, подпись, телефон лица отбиравшего биоматериал:", styleLeft), Paragraph(" ", style)]
        opinion = [opinion]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
        a = [
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0.05 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 0.1 * mm),
            ("LINEBELOW", (1, 0), (1, 0), 0.5, colors.black, None, (1, 1, 1)),
        ]
        tbl.setStyle(TableStyle(a))
        anamnes_and_picker.append(tbl)
        anamnes_and_picker.append(HRFlowable(width=185.5 * mm, lineCap="round", thickness=0.5, spaceAfter=0.1 * mm, spaceBefore=4 * mm, color=colors.black, dash=(0.5, 1.5)))
        anamnes_and_picker_frame = Frame(10 * mm, 60.5 * mm, 187 * mm, 17.5 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=1 * mm, showBoundary=0)
        anamnes_and_picker_frame.addFromList(anamnes_and_picker, c)

        previous_t = []
        opinion = [[Paragraph("", styleLeft)]]
        col_width = [189 * mm]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=15 * mm, colWidths=col_width)
        a = [("GRID", (0, 0), (-1, -1), 1.2, color_dash_for_symbol, None, (1.5, 1.5, 1.5))]
        tbl.setStyle(TableStyle(a))
        previous_t.append(tbl)
        previous_t_frame = Frame(0 * mm, 43.5 * mm, 210 * mm, 15 * mm, leftPadding=10 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        previous_t_frame.addFromList(previous_t, c)

        previous = []
        previous.append(Paragraph("Сведения о выполненных ранее исследованиях (заполняет лаборатория):", styleLeft))
        previous_frame = Frame(10 * mm, 44 * mm, 187 * mm, 15 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        previous_frame.addFromList(previous, c)

        attention_t = []
        opinion = [[Paragraph("", styleLeft)]]
        col_width = [189 * mm]
        tbl = Table(opinion, hAlign="LEFT", rowHeights=8 * mm, colWidths=col_width)
        a = [("GRID", (0, 0), (-1, -1), 1.2, colors.white, None, (1.5, 1.5, 1.5))]
        tbl.setStyle(TableStyle(a))
        attention_t.append(tbl)
        attention_t_frame = Frame(0 * mm, 26 * mm, 210 * mm, 8 * mm, leftPadding=12 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0 * mm, showBoundary=0)
        attention_t_frame.addFromList(attention_t, c)

        attention = []
        attention.append(Paragraph("ВНИМАНИЕ! Анализы сдаются только в медицинском учреждении по месту выдачи бланка", styleBoldItalic))
        attention_frame = Frame(10 * mm, 26.5 * mm, 187 * mm, 8 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=3 * mm, showBoundary=0)
        attention_frame.addFromList(attention, c)

        picture_t = []
        img_path = os.path.join(FONTS_FOLDER, "..", "img")
        footer_picture = os.path.join(img_path, "idc_covid_footer.png")
        alphabet_image = Image(footer_picture)
        alphabet_image.drawHeight = 13 * mm
        alphabet_image.drawWidth = 137 * mm
        picture_t.append(alphabet_image)
        picture_t_frame = Frame(14.5 * mm, 10 * mm, 138 * mm, 13.5 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0.3 * mm, showBoundary=1)
        picture_t_frame.addFromList(picture_t, c)

        barcode = eanbc.Ean13BarcodeWidget(3220556479540, humanReadable=1, barHeight=13.7 * mm)
        dir_code = Drawing()
        dir_code.add(barcode)
        renderPDF.draw(dir_code, c, 155 * mm, 10 * mm)
        renderPDF.draw(draw_rectangle(7.6 * mm, 10 * mm), c, 0 * mm, 0 * mm)
        renderPDF.draw(draw_rectangle(9 * mm, 281 * mm), c, 0 * mm, 0 * mm)
        renderPDF.draw(draw_rectangle(194 * mm, 9.5 * mm), c, 0 * mm, 0 * mm)
        renderPDF.draw(draw_rectangle(195 * mm, 281 * mm), c, 0 * mm, 0 * mm)
        c.showPage()

        barcode = eanbc.Ean13BarcodeWidget(7220556479621, humanReadable=1, barHeight=13.7 * mm)
        dir_code = Drawing()
        dir_code.add(barcode)
        renderPDF.draw(dir_code, c, 155 * mm, 10 * mm)
        renderPDF.draw(draw_rectangle(7.6 * mm, 10 * mm), c, 0 * mm, 0 * mm)
        renderPDF.draw(draw_rectangle(9 * mm, 281 * mm), c, 0 * mm, 0 * mm)
        renderPDF.draw(draw_rectangle(194 * mm, 9.5 * mm), c, 0 * mm, 0 * mm)
        renderPDF.draw(draw_rectangle(195 * mm, 281 * mm), c, 0 * mm, 0 * mm)

        c.showPage()

    printForm()


def create_dot_table(count, odd, even):
    col_width = []
    for i in range(0, count):
        if i % 2 == 0:
            col_width.append(even)
        else:
            col_width.append(odd)
    return col_width


def split_fio(fio):
    fio = fio.strip().replace("  ", " ").strip()
    fio_split = fio.split(" ")

    if len(fio_split) == 0:
        return ""
    if len(fio_split) == 1:
        return [fio]

    if len(fio_split) > 3:
        fio_split = [fio_split[0], " ".join(fio_split[1:-2]), fio_split[-1]]

    return [fio_split[0], fio_split[1], fio_split[2]]


def four_obj_date(odd, even, style, type_dash, step_dash, data="", color_dash_for_symbol=colors.gray):
    count = 5 * 2
    col_width = create_dot_table(count, odd, even)
    col_width = tuple(col_width)
    opinion = [Paragraph(" ", style) for i in range(0, count)]
    opinion[4] = Paragraph(".", style)
    x = 0
    if data:
        for i in list(data):
            opinion[x] = Paragraph(f"{i}", style)
            x += 2
    opinion = [opinion]
    tbl = Table(opinion, hAlign="LEFT", rowHeights=5 * mm, colWidths=col_width)
    a = [("OUTLINE", (i, 0), (i, 0), 0.7, color_dash_for_symbol, type_dash, step_dash) for i in range(0, count) if i % 2 == 0]
    a.extend([("BOTTOMPADDING", (0, 0), (-1, -1), 0.1 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 0.2 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0.2 * mm)])
    a.pop(2)
    tbl.setStyle(TableStyle(a))
    return tbl


def draw_rectangle(x, y):
    rectangle = Rect(x, y, 5 * mm, 5 * mm)
    rectangle.strokeColor = HexColor("#000000")
    rectangle.fillColor = HexColor("#000000")
    rect_draw = Drawing()
    rect_draw.add(rectangle)
    return rect_draw


def form_02(c: Canvas, dir: Napravleniya):
    # Диагностический цент - направление на МСКТ
    def printForm():
        hospital_name = dir.hospital_short_title
        hospital_address = SettingManager.get("org_address")

        if sys.platform == "win32":
            locale.setlocale(locale.LC_ALL, "rus_rus")
        else:
            locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")

        pdfmetrics.registerFont(TTFont("PTAstraSerifBold", os.path.join(FONTS_FOLDER, "PTAstraSerif-Bold.ttf")))
        pdfmetrics.registerFont(TTFont("PTAstraSerifReg", os.path.join(FONTS_FOLDER, "PTAstraSerif-Regular.ttf")))

        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = "PTAstraSerifReg"
        style.fontSize = 11.5
        style.leading = 14
        style.spaceAfter = 3.5 * mm

        styleZeroSpaceAfter = deepcopy(style)
        styleZeroSpaceAfter.spaceAfter = 1 * mm

        styleCenterBold = deepcopy(style)
        styleCenterBold.alignment = TA_CENTER
        styleCenterBold.fontSize = 12
        styleCenterBold.leading = 15
        styleCenterBold.fontName = "PTAstraSerifBold"

        styleT = deepcopy(style)
        styleT.alignment = TA_LEFT
        styleT.fontSize = 10
        styleT.leading = 4.5 * mm
        styleT.face = "PTAstraSerifReg"

        objs = []
        objs.append(Spacer(1, 32 * mm))
        opinion = [
            [
                Paragraph("<font size=10>Иркутский областной клинический<br/>консультативно  диагностический центр<br/>г. Иркутск 666047  ул., Байкальская 109</font>", styleT),
                Paragraph("", styleT),
            ],
        ]

        tbl = Table(opinion, 2 * [100 * mm])
        tbl.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.75, colors.white),
                    ("LEFTPADDING", (1, 0), (-1, -1), 55 * mm),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        objs.append(tbl)
        objs.append(Spacer(1, 5 * mm))
        try:
            issledovaniye = Issledovaniya.objects.get(napravleniye=dir.pk)
        except ObjectDoesNotExist:
            issledovaniye = None
        title_research = issledovaniye.research.title
        objs.append(Paragraph(f"НАПРАВЛЕНИЕ № {dir.pk} ", styleCenterBold))
        objs.append(Paragraph("для получения  медицинских  услуг в областном  государственном  учреждении  здравоохранения.", styleCenterBold))
        objs.append(Spacer(1, 10 * mm))
        objs.append(Paragraph(f"От: {strdate(dir.data_sozdaniya)}", style))
        objs.append(Paragraph(f"ФИО: {dir.client.individual.fio()}", style))
        space_symbol = "&nbsp;"

        sex = dir.client.individual.sex
        if sex == "м":
            sex = "муж"
        else:
            sex = "жен"

        born = dir.client.individual.bd().split(".")
        objs.append(Paragraph(f"Дата <u>{born[0]}</u> Месяц <u>{born[1]}</u> Год рождения <u>{born[2]}</u> Пол {sex} ", style))
        objs.append(Paragraph(f"Контактный телефон: {dir.client.phone}", style))

        polis_num = ""
        polis_issue = ""
        ind_data = dir.client.get_data_individual()
        if ind_data["oms"]["polis_num"]:
            polis_num = ind_data["oms"]["polis_num"]
        if ind_data["oms"]["polis_issued"]:
            polis_issue = ind_data["oms"]["polis_issued"]
        address = ind_data["main_address"]
        objs.append(Paragraph(f"Регистрация по месту жительства: {address}", style))
        objs.append(Paragraph(f"Страховой полис № {polis_num} <br/>Страховая компания: {polis_issue}", style))
        objs.append(Paragraph(f"Наименование территориального лечебно – профилактического учреждения<br/>по месту прикрепления {hospital_address} {hospital_name}", style))
        objs.append(Paragraph(f"Наименование направившего ЛПУ  {hospital_address} {hospital_name}", style))
        objs.append(Paragraph(f"Направлени на: <br/>{title_research}", style))
        diagnos = dir.diagnos
        if not diagnos or len(diagnos) <= 1:
            objs.append(Paragraph('<font face="PTAstraSerifBold">Диагноз направившего учреждения:</font>', styleZeroSpaceAfter))
            objs.append(InteractiveTextField())
        else:
            objs.append(Paragraph(f'<font face="PTAstraSerifBold">Диагноз направившего учреждения: <br/>{diagnos}</font>', style))

        objs.append(Spacer(1, 2 * mm))
        objs.append(Paragraph(f"Врач: {dir.doc.get_fio()} {space_symbol * 5} подпись _________", style))
        objs.append(Spacer(1, 3 * mm))
        hospital_director = SettingManager.get("hospital director", default="", default_type="s")
        objs.append(Paragraph(f"Руководитель направившего  ЛПУ__________________________{hospital_director}", style))
        objs.append(Spacer(1, 3 * mm))
        objs.append(Paragraph("М.П.", style))

        picture_t = []
        img_path = os.path.join(FONTS_FOLDER, "..", "img")
        footer_picture = os.path.join(img_path, "dc_label.png")
        alphabet_image = Image(footer_picture)
        alphabet_image.drawHeight = 30 * mm
        alphabet_image.drawWidth = 60 * mm
        picture_t.append(alphabet_image)
        picture_t_frame = Frame(12 * mm, 250 * mm, 65 * mm, 35 * mm, leftPadding=0 * mm, bottomPadding=0 * mm, rightPadding=0 * mm, topPadding=0.3 * mm, showBoundary=0)
        picture_t_frame.addFromList(picture_t, c)

        gistology_frame = Frame(0 * mm, 0 * mm, 210 * mm, 297 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)
        gistology_inframe = KeepInFrame(210 * mm, 297 * mm, objs, hAlign="LEFT", vAlign="TOP", fakeWidth=False)
        gistology_frame.addFromList([gistology_inframe], c)

    printForm()


def form_03_1(c: Canvas, dir: Napravleniya):
    # СПИД направление на ВИЧ
    def printForm():
        hospital_name = dir.hospital_short_title

        if sys.platform == 'win32':
            locale.setlocale(locale.LC_ALL, 'rus_rus')
        else:
            locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

        pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = "PTAstraSerifReg"
        style.fontSize = 10
        style.leading = 8
        style.spaceAfter = 1.1 * mm

        styleZeroSpaceAfter = deepcopy(style)
        styleZeroSpaceAfter.spaceAfter = 1 * mm

        styleCenterBold = deepcopy(style)
        styleCenterBold.alignment = TA_CENTER
        styleCenterBold.fontSize = 12
        styleCenterBold.fontName = 'PTAstraSerifBold'

        styleCenter = deepcopy(styleCenterBold)
        styleCenter.fontName = 'PTAstraSerifReg'

        styleCenter10 = deepcopy(styleCenter)
        styleCenter10.fontSize = 10

        styleT = deepcopy(style)
        styleT.alignment = TA_LEFT
        styleT.fontSize = 10
        styleT.leading = 4.5 * mm
        styleT.face = 'PTAstraSerifReg'

        objs = []
        objs.append(Paragraph('Иркутский областной центр по профилактике и борьбе со СПИД и инфекционными заболеваниями.', styleCenter))
        objs.append(Paragraph('Лаборатория молекулярно-генетических методов исследования', styleCenter))
        objs.append(Paragraph('664035, г.Иркутска ,ул.Спартаковская , 11, тел:(83952)777-958', styleCenter))
        objs.append(Spacer(1, 2 * mm))
        objs.append(Paragraph('Штамп учреждения', style))
        objs.append(Spacer(1, 3 * mm))
        objs.append(Paragraph(f'НАПРАВЛЕНИЕ № {dir.pk} ', styleCenterBold))
        objs.append(Paragraph('На количественное определение РНК ВИЧ -1', styleCenter))
        objs.append(Paragraph('(Тест системы:Abbot Real Time ВИЧ-1,COBAS® AmpliPer/ COBAS® TagMan® HIV-1,', styleCenter))
        objs.append(Paragraph('АмплиСенс ВМЧ-Монитор –FRT, АмплиСенс ВИЧ Монитор –M-FL, РеалБест ВИЧ ПЦР)', styleCenter))
        objs.append(Spacer(1, 2 * mm))
        space_symbol = '&nbsp;'
        objs.append(Paragraph(f'Дата {strdate(dir.data_sozdaniya)}г. {space_symbol * 5}№ история болезни _____________________________________', style))
        sex = dir.client.individual.sex
        if sex == "м":
            sex = 'муж'
        else:
            sex = 'жен'

        objs.append(Paragraph(f'Ф.И.О.: {dir.client.individual.fio()} {space_symbol * 25} Пол {sex} ', style))
        born = dir.client.individual.bd().split('.')
        address = dir.client.fact_address if dir.client.fact_address else dir.client.main_address
        objs.append(Paragraph(f'Дата рождения: {born[0]}.{born[1]}.{born[2]} {space_symbol * 3} Адрес: {address}', style))
        objs.append(Paragraph('Эпид.номер_____________________ Код_____________', style))
        objs.append(Paragraph('Дата иммуноблота______________ Стадия ВИЧ-инфекции_________ в фазе____________________________', style))
        objs.append(Paragraph(f'{space_symbol * 50} Прежнее значение вирусной нагрузки ____________________________________', style))
        objs.append(Paragraph('Обследование в связи с (подчеркнуть)', styleCenter10))
        objs.append(Paragraph('Мониторингом терапии (принимает АРВП)', styleCenter10))
        objs.append(Paragraph('Плановым диспансерным наблюдением (не принимает АРВП)', styleCenter10))
        objs.append(Paragraph(f'Направляющая организация: {hospital_name}', style))
        objs.append(Paragraph(f'Ф.И.О, Лечащего врача {dir.doc.get_fio()} {space_symbol * 25} Подпись___________', style))

        objs.append(Paragraph('Необходимые отметки по забору, хранению и транспортировке образца:', styleCenter10))
        objs.append(Paragraph('Ф.И.О. оператора, подпись  _____________________________________________________', styleCenter10))
        objs.append(Paragraph('Дата забора крови «___»_________20___г.__________час.____мин.___________________', styleCenter10))
        objs.append(Paragraph('Время забора плазмы : ______час.____мин.___________', styleCenter10))
        objs.append(Paragraph('Условия хранения плазмы (укажите дату и время ,когда образец поместили на хранение):', styleCenter10))
        objs.append(Paragraph('+2-+8C «__»_________20__г.____________час_______.мин.:', styleCenter10))
        objs.append(Paragraph('-20C «__»_________20__г.____________час_______.мин.', styleCenter10))
        objs.append(Paragraph('Результаты исследования HIV-1 РНК: ____________________________', styleCenter10))
        objs.append(Paragraph('Дата выдачи ___________________________  Подпись ___________', styleCenter10))
        objs.append(Paragraph('__________________________________________________________________________________________________________', styleCenter10))
        objs.append(Paragraph('__________________________________________________________________________________________________________', styleCenter10))
        objs.append(Spacer(1, 15 * mm))
        one_frame = Frame(0 * mm, 0 * mm, 210 * mm, 297 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)
        one_inframe = KeepInFrame(210 * mm, 146 * mm, objs, hAlign='LEFT', vAlign='TOP', fakeWidth=False)
        two_inframe = KeepInFrame(210 * mm, 146 * mm, objs, hAlign='LEFT', vAlign='TOP', fakeWidth=False)
        one_frame.addFromList([one_inframe, two_inframe], c)

    printForm()


def form_03(c: Canvas, dir: Napravleniya):
    # СПИД направление на ВИЧ
    def printForm():
        hospital_name = dir.hospital_short_title

        if sys.platform == "win32":
            locale.setlocale(locale.LC_ALL, "rus_rus")
        else:
            locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")

        pdfmetrics.registerFont(TTFont("PTAstraSerifBold", os.path.join(FONTS_FOLDER, "PTAstraSerif-Bold.ttf")))
        pdfmetrics.registerFont(TTFont("PTAstraSerifReg", os.path.join(FONTS_FOLDER, "PTAstraSerif-Regular.ttf")))

        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = "PTAstraSerifReg"
        style.fontSize = 10
        style.leading = 8
        style.spaceAfter = 1.1 * mm

        styleZeroSpaceAfter = deepcopy(style)
        styleZeroSpaceAfter.spaceAfter = 1 * mm

        styleCenterBold = deepcopy(style)
        styleCenterBold.alignment = TA_CENTER
        styleCenterBold.fontSize = 12
        styleCenterBold.fontName = "PTAstraSerifBold"

        styleCenter = deepcopy(styleCenterBold)
        styleCenter.fontName = "PTAstraSerifReg"

        styleCenter10 = deepcopy(styleCenter)
        styleCenter10.fontSize = 10

        styleT = deepcopy(style)
        styleT.alignment = TA_LEFT
        styleT.fontSize = 10
        styleT.leading = 4.5 * mm
        styleT.face = "PTAstraSerifReg"

        objs = []
        objs.append(Paragraph("Иркутский областной центр по профилактике и борьбе со СПИД и инфекционными заболеваниями.", styleCenter))
        objs.append(Paragraph("Лаборатория молекулярно-генетических методов исследования", styleCenter))
        objs.append(Paragraph("664035, г.Иркутска ,ул.Спартаковская , 11, тел:(83952)777-958", styleCenter))
        objs.append(Spacer(1, 2 * mm))
        objs.append(Paragraph("Штамп учреждения", style))
        objs.append(Spacer(1, 3 * mm))
        objs.append(Paragraph(f"НАПРАВЛЕНИЕ № {dir.pk} ", styleCenterBold))
        objs.append(Paragraph("На количественное определение РНК ВИЧ -1", styleCenter))
        objs.append(Paragraph("(Тест системы:Abbot Real Time ВИЧ-1,COBAS® AmpliPer/ COBAS® TagMan® HIV-1,", styleCenter))
        objs.append(Paragraph("АмплиСенс ВМЧ-Монитор –FRT, АмплиСенс ВИЧ Монитор –M-FL, РеалБест ВИЧ ПЦР)", styleCenter))
        objs.append(Spacer(1, 2 * mm))
        space_symbol = "&nbsp;"
        objs.append(Paragraph(f"Дата {strdate(dir.data_sozdaniya)}г. {space_symbol * 5}№ история болезни _____________________________________", style))
        sex = dir.client.individual.sex
        if sex == "м":
            sex = "муж"
        else:
            sex = "жен"

        objs.append(Paragraph(f"Ф.И.О.: {dir.client.individual.fio()} {space_symbol * 25} Пол {sex} ", style))
        born = dir.client.individual.bd().split(".")
        address = dir.client.fact_address if dir.client.fact_address else dir.client.main_address
        objs.append(Paragraph(f"Дата рождения: {born[0]}.{born[1]}.{born[2]} {space_symbol * 3} Адрес: {address}", style))
        objs.append(Paragraph("Эпид.номер_____________________ Код_____________", style))
        objs.append(Paragraph("Дата иммуноблота______________ Стадия ВИЧ-инфекции_________ в фазе____________________________", style))
        objs.append(Paragraph(f"{space_symbol * 50} Прежнее значение вирусной нагрузки ____________________________________", style))
        objs.append(Paragraph("Обследование в связи с (подчеркнуть)", styleCenter10))
        objs.append(Paragraph("Мониторингом терапии (принимает АРВП)", styleCenter10))
        objs.append(Paragraph("Плановым диспансерным наблюдением (не принимает АРВП)", styleCenter10))
        objs.append(Paragraph(f"Направляющая организация: {hospital_name}", style))
        objs.append(Paragraph(f"Ф.И.О, Лечащего врача {dir.doc.get_fio()} {space_symbol * 25} Подпись___________", style))

        objs.append(Paragraph("Необходимые отметки по забору, хранению и транспортировке образца:", styleCenter10))
        objs.append(Paragraph("Ф.И.О. оператора, подпись  _____________________________________________________", styleCenter10))
        objs.append(Paragraph("Дата забора крови «___»_________20___г.__________час.____мин.___________________", styleCenter10))
        objs.append(Paragraph("Время забора плазмы : ______час.____мин.___________", styleCenter10))
        objs.append(Paragraph("Условия хранения плазмы (укажите дату и время ,когда образец поместили на хранение):", styleCenter10))
        objs.append(Paragraph("+2-+8C «__»_________20__г.____________час_______.мин.:", styleCenter10))
        objs.append(Paragraph("-20C «__»_________20__г.____________час_______.мин.", styleCenter10))
        objs.append(Paragraph("Результаты исследования HIV-1 РНК: ____________________________", styleCenter10))
        objs.append(Paragraph("Дата выдачи ___________________________  Подпись ___________", styleCenter10))
        objs.append(Paragraph("__________________________________________________________________________________________________________", styleCenter10))
        objs.append(Paragraph("__________________________________________________________________________________________________________", styleCenter10))
        objs.append(Spacer(1, 15 * mm))
        one_frame = Frame(0 * mm, 0 * mm, 210 * mm, 297 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)
        one_inframe = KeepInFrame(210 * mm, 146 * mm, objs, hAlign="LEFT", vAlign="TOP", fakeWidth=False)
        two_inframe = KeepInFrame(210 * mm, 146 * mm, objs, hAlign="LEFT", vAlign="TOP", fakeWidth=False)
        one_frame.addFromList([one_inframe, two_inframe], c)

    printForm()


def form_04(c: Canvas, dir: Napravleniya):
    # Направление на химико-токсикологические исследования
    def printForm():
        hospital_name = dir.hospital_short_title

        if sys.platform == "win32":
            locale.setlocale(locale.LC_ALL, "rus_rus")
        else:
            locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")

        pdfmetrics.registerFont(TTFont("PTAstraSerifBold", os.path.join(FONTS_FOLDER, "PTAstraSerif-Bold.ttf")))
        pdfmetrics.registerFont(TTFont("PTAstraSerifReg", os.path.join(FONTS_FOLDER, "PTAstraSerif-Regular.ttf")))

        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = "PTAstraSerifReg"
        style.fontSize = 12
        style.leading = 5

        styleLeading8 = deepcopy(style)
        styleLeading8.leading = 13
        styleLeading8.leftIndent = 10 * mm

        styleZeroSpaceAfter = deepcopy(style)
        styleZeroSpaceAfter.spaceAfter = 1 * mm

        styleCenterBold = deepcopy(style)
        styleCenterBold.alignment = TA_CENTER
        styleCenterBold.fontName = "PTAstraSerifBold"

        styleCenter = deepcopy(styleCenterBold)
        styleCenter.fontName = "PTAstraSerifReg"
        styleCenter.fontSize = 14

        styleCenter12 = deepcopy(styleCenter)
        styleCenter12.fontSize = 12
        styleCenter12.SpaceAfter = 1 * mm

        styleCenter10 = deepcopy(styleCenter12)
        styleCenter10.fontSize = 10

        styleCenter2 = deepcopy(styleCenter12)
        styleCenter2.SpaceBefor = -20 * mm

        styleT = deepcopy(style)
        styleT.alignment = TA_LEFT
        styleT.fontSize = 10
        styleT.leading = 4.5 * mm
        styleT.face = "PTAstraSerifReg"

        objs = []
        opinion = [
            [
                Paragraph(f"<font size=10>Министерство здравоохранения<br/>Российской Федерации<br/>{hospital_name}<br/></font>", styleT),
                Paragraph("<font size=10>Медицинская документация<br/>Учетная форма № 452/у-06</font>", styleT),
            ],
        ]
        tbl = Table(opinion, 2 * [105 * mm])
        tbl.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.75, colors.white),
                    ("LEFTPADDING", (1, 0), (-1, -1), 35 * mm),
                    ("LEFTPADDING", (0, 0), (0, -1), 15 * mm),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        objs.append(tbl)
        objs.append(Spacer(1, 2 * mm))
        objs.append(Paragraph("Направление<br/><br/> на химико-токсикологические исследования", styleCenter))
        objs.append(Spacer(1, 2 * mm))
        space_symbol = "&nbsp;"
        objs.append(Paragraph(f"{strdate(dir.data_sozdaniya)} {space_symbol * 140} №{dir.pk}", styleCenter12))
        objs.append(Spacer(1, 3 * mm))
        objs.append(Paragraph(f" в ХТЛ {hospital_name}", styleCenter))
        objs.append(Spacer(1, 0.2 * mm))
        objs.append(Paragraph("______________________________________________________________________________________________________________________", styleCenter10))
        objs.append(Spacer(1, 2.2 * mm))
        objs.append(Paragraph("(наименование химико-токсикологической лаборатории – ХТЛ)", styleCenter10))
        objs.append(Spacer(1, 5 * mm))
        objs.append(Paragraph("______________________________________________________________________________________________________________________", styleCenter10))
        objs.append(Spacer(1, 2.2 * mm))
        objs.append(Paragraph("(наименование медицинской организации и его структурного подразделения, выдавшего направление)", styleCenter10))
        objs.append(Spacer(1, 5 * mm))
        objs.append(Paragraph(f"{dir.client.individual.fio()} {space_symbol * 5} Возраст: {dir.client.individual.age()}", styleCenter12))
        objs.append(Spacer(1, 0.2 * mm))
        objs.append(Paragraph("______________________________________________________________________________________________________________________", styleCenter10))
        objs.append(Spacer(1, 2.2 * mm))
        objs.append(Paragraph("(фамилия, имя, отчество освидетельствуемого, возраст)", styleCenter10))
        objs.append(Spacer(1, 4 * mm))
        objs.append(Paragraph(f"Код биологического объекта {dir.pk} ", style))
        objs.append(Spacer(1, 4 * mm))
        objs.append(Paragraph("______________________________________________________________________________________________________________________", styleCenter10))
        objs.append(Spacer(1, 4 * mm))
        objs.append(Paragraph(f"Дата и время отбора объекта  {strdate(dir.data_sozdaniya)} ", style))
        objs.append(Spacer(1, 4 * mm))
        objs.append(Paragraph("Условия хранения объектов __________________________________________________________________________", style))
        objs.append(Spacer(1, 4 * mm))
        objs.append(Paragraph("Биологический объект и его количество и показатели МОЧА", style))
        objs.append(Spacer(1, 4 * mm))
        objs.append(Paragraph("______________________________________________________________________________________________________________________", styleCenter10))
        objs.append(Spacer(1, 4 * mm))
        objs.append(Paragraph("______________________________________________________________________________________________________________________", styleCenter10))
        objs.append(Spacer(1, 4 * mm))
        diagnosis = dir.diagnos.strip()[:35]
        objs.append(Paragraph(f"Предварительный клинический диагноз: {diagnosis}", style))
        objs.append(Spacer(1, 4 * mm))
        objs.append(Paragraph("Цель химико-токсикологических исследований:  <u>Обнаружены / Не обнаружены</u>", style))
        iss = Issledovaniya.objects.filter(napravleniye=dir).first()
        research = iss.research
        fractions = Fractions.objects.filter(research=research, hide=False)
        test = [f.title for f in fractions]
        objs.append(Spacer(1, 4 * mm))
        objs.append(Paragraph(f'{"<br/>".join(test)}', styleLeading8))
        objs.append(Spacer(1, 4 * mm))
        objs.append(Paragraph("Дополнительные сведения ___________________________________________________________________________", style))
        objs.append(Spacer(1, 4 * mm))
        objs.append(Paragraph("Дата и время отправки биологических объектов в ХТЛ", style))
        objs.append(Spacer(1, 10 * mm))
        objs.append(Paragraph(f"Ф.И.О. врача (фельдшера), <br/><br/>выдавшего направление {space_symbol * 20} {dir.doc.get_fio()} {space_symbol * 40} _______________________", style))
        objs.append(Spacer(1, 1.5 * mm))
        objs.append(Paragraph(f"{space_symbol * 150}(подпись)", style))

        data_frame = Frame(0 * mm, 0 * mm, 210 * mm, 297 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)
        data_inframe = KeepInFrame(210 * mm, 297 * mm, objs, hAlign="LEFT", vAlign="TOP", fakeWidth=False)
        data_frame.addFromList([data_inframe], c)

    printForm()
