import os
from copy import deepcopy

from django.core.exceptions import ObjectDoesNotExist
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import eanbc
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors

from api.stationar.stationar_func import hosp_get_hosp_direction
from appconf.manager import SettingManager
from directions.models import Napravleniya, Issledovaniya
from reportlab.platypus import Table, TableStyle, Paragraph, Frame, KeepInFrame, Spacer
from reportlab.pdfgen.canvas import Canvas
from laboratory.settings import FONTS_FOLDER
from laboratory.utils import strdate
import sys
import locale
from forms.forms_func import hosp_get_clinical_diagnos
from laboratory.utils import current_year


def form_01(c: Canvas, dir: Napravleniya):
    # Микробиология - Учетная форма № 204/у Утверждена приказом 10130
    def printForm():
        hospital_name = SettingManager.get("org_title")
        hospital_address = SettingManager.get("org_address")
        hospital_kod_ogrn = SettingManager.get("org_ogrn")

        if sys.platform == 'win32':
            locale.setlocale(locale.LC_ALL, 'rus_rus')
        else:
            locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

        pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = "PTAstraSerifReg"
        style.fontSize = 11
        style.leading = 10
        style.spaceAfter = 1 * mm

        styleCenterBold = deepcopy(style)
        styleCenterBold.alignment = TA_CENTER
        styleCenterBold.fontSize = 12
        styleCenterBold.leading = 15
        styleCenterBold.fontName = 'PTAstraSerifBold'

        styleT = deepcopy(style)
        styleT.alignment = TA_LEFT
        styleT.fontSize = 10
        styleT.leading = 4.5 * mm
        styleT.face = 'PTAstraSerifReg'

        barcode = eanbc.Ean13BarcodeWidget(dir.pk + 460000000000, humanReadable=0, barHeight=8 * mm, barWidth=1.25)
        dir_code = Drawing()
        dir_code.add(barcode)
        renderPDF.draw(dir_code, c, 157 * mm, 259 * mm)

        objs = []
        opinion = [
            [Paragraph(f'<font size=11>{hospital_name}<br/>Адрес: {hospital_address}<br/>ОГРН: {hospital_kod_ogrn} <br/> </font>', styleT),
             Paragraph('<font size=9 >Код формы по ОКУД:<br/>Код организации по ОКПО: <br/>'
                       'Медицинская документация<br/>Учетная форма № 204/у</font>', styleT)],
        ]

        tbl = Table(opinion, 2 * [100 * mm])
        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
            ('LEFTPADDING', (1, 0), (-1, -1), 55 * mm),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        objs.append(tbl)
        objs.append(Spacer(1, 3 * mm))
        history_num = ''
        if dir.parent and dir.parent.research.is_hospital:
            history_num = f"(cтационар-{str(dir.parent.napravleniye_id)})"
        objs.append(Paragraph(f'НАПРАВЛЕНИЕ № {dir.pk} {history_num} ', styleCenterBold))
        objs.append(Paragraph('на микробиологическое исследование', styleCenterBold))
        objs.append(Spacer(1, 3 * mm))
        space_symbol = '&nbsp;'
        objs.append(Paragraph(f'Дата и время взятия материала: "____" ____________{current_year()} {space_symbol * 10} _____ час. _______ мин.', style))
        objs.append(Paragraph('В бактериологическую лабораторию', style))
        objs.append(Paragraph(f'Фамилия, Имя, Отчество: {dir.client.individual.fio()}', style))
        sex = dir.client.individual.sex
        if sex == "м":
            sex = f'{sex}-1'
        else:
            sex = f'{sex}-2'
        objs.append(Paragraph(f'Возраст: {dir.client.individual.bd()} ({dir.client.individual.age_s(direction=dir)}) {space_symbol * 5} Пол: {sex},', style))
        polis_num = ''
        polis_issue = ''
        snils = ''
        ind_data = dir.client.get_data_individual()
        if ind_data['oms']['polis_num']:
            polis_num = ind_data['oms']['polis_num']
        if ind_data['oms']['polis_issued']:
            polis_issue = ind_data['oms']['polis_issued']
        objs.append(Paragraph(f'Полис ОМС: {polis_num} с/к: {polis_issue}', style))
        address = ind_data['main_address']
        objs.append(Paragraph(f'Медицинская карта N : {dir.client.number_with_type()}', style))
        objs.append(Paragraph(f'Отделение: {dir.doc.podrazdeleniye.title} {space_symbol * 7} палата _______ ', style))
        objs.append(Paragraph(f'Адрес постоянного места жительства: {address}', style))
        objs.append(Paragraph(f'Место работы, учебы (наименование детского учреждения, школы): {dir.workplace}', style))
        clinical_diagnos = ''
        if dir.parent:
            hosp_nums_obj = hosp_get_hosp_direction(dir.parent.napravleniye_id)
            if len(hosp_nums_obj) > 0:
                clinical_diagnos = hosp_get_clinical_diagnos(hosp_nums_obj)

        objs.append(Paragraph(f"Диагноз, дата заболевания:  <font face=\"PTAstraSerifBold\">{clinical_diagnos}</font>", style))
        objs.append(Paragraph('_______________________________________________________________________________________________________', style))

        issledovaniya = dir.issledovaniya_set.all()
        opinion = [
            [Paragraph('Цель и наименование исследования', styleT), Paragraph('Материал - место взятия', styleT), Paragraph('Показания   к    обследованию', styleT),],
        ]

        for v in issledovaniya:
            tmp_value = []
            tmp_value.append(Paragraph(f"{v.research.title} - {v.research.code}", styleT))
            type_material = "" if not v.research.site_type else v.research.site_type.title
            service_location_title = "" if not v.service_location else v.service_location.title
            tmp_value.append(Paragraph(f"{type_material}-{service_location_title}", styleT))
            category_patient = v.localization.title if v.localization else v.comment
            tmp_value.append(Paragraph(category_patient, styleT))
            opinion.append(tmp_value.copy())

        cols_width = [105 * mm, 45 * mm, 47 * mm]
        tbl = Table(opinion, colWidths=cols_width, hAlign='LEFT')
        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        objs.append(Spacer(1, 5 * mm))
        objs.append(tbl)

        objs.append(Spacer(1, 5 * mm))
        objs.append(Paragraph(f'Фамилия, инициалы врача: {dir.doc.get_fio()} {space_symbol * 5} подпись _________', style))
        objs.append(Paragraph(f'Дата направления:  {strdate(dir.data_sozdaniya)}', style))

        gistology_frame = Frame(0 * mm, 0 * mm, 210 * mm, 297 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)
        gistology_inframe = KeepInFrame(210 * mm, 297 * mm, objs, hAlign='LEFT', vAlign='TOP', fakeWidth=False)
        gistology_frame.addFromList([gistology_inframe], c)

    printForm()
