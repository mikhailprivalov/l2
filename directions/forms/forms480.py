import os
from copy import deepcopy
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import eanbc, qr
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from appconf.manager import SettingManager
from directions.models import Napravleniya
from reportlab.platypus import Table, TableStyle, Paragraph, Frame, KeepInFrame, Spacer
from reportlab.pdfgen.canvas import Canvas
from laboratory.settings import FONTS_FOLDER
from laboratory.utils import strdate
import sys
import locale


def form_01(c: Canvas, dir: Napravleniya):
    # Гистология - Учетная форма № 014/у Утверждена приказом Минздрава России от 24 марта 2016 г. № 179н
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
        style.fontSize = 10.5
        style.leading = 14
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
                       'Медицинская документация<br/>Учетная форма № 014/у</font>', styleT)],
        ]

        tbl = Table(opinion, 2 * [100 * mm])
        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
            ('LEFTPADDING', (1, 0), (-1, -1), 55 * mm),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        objs.append(tbl)
        objs.append(Spacer(1, 5 * mm))
        history_num = ''
        if dir.parent and dir.parent.research.is_hospital:
            history_num = f"(cтационар-{str(dir.parent.napravleniye_id)})"
        objs.append(Paragraph(f'НАПРАВЛЕНИЕ № {dir.pk} {history_num} ', styleCenterBold))
        objs.append(Paragraph(f'НА ПРИЖИЗНЕННОЕ ПАТОЛОГО-АНАТОМИЧЕСКОЕ<br/> ИССЛЕДОВАНИЕ БИОПСИЙНОГО (ОПЕРАЦИОННОГО) МАТЕРИАЛА', styleCenterBold))
        objs.append(Spacer(1, 10 * mm))
        space_symbol = '&nbsp;'
        objs.append(Paragraph(f'1. Отделение, направившее биопсийный (операционный) материал: {dir.doc.podrazdeleniye.title}', style))
        objs.append(Paragraph(f'2. Фамилия, имя, отчество (при наличии) пациента: {dir.client.individual.fio()}', style))
        sex = dir.client.individual.sex
        if sex == "м":
            sex = f'{sex}-1'
        else:
            sex = f'{sex}-2'
        objs.append(Paragraph(f'3. Пол: {sex}, {space_symbol * 5}   4. Дата рождения: число: {dir.client.individual.bd()}', style))
        polis_num = ''
        polis_issue = ''
        snils = ''
        ind_data = dir.client.get_data_individual()
        if ind_data['oms']['polis_num']:
            polis_num = ind_data['oms']['polis_num']
        if ind_data['oms']['polis_issued']:
            polis_issue = ind_data['oms']['polis_issued']
        objs.append(Paragraph(f'5. Полис ОМС: {polis_num} с/к: {polis_issue}', style))
        if ind_data['snils']:
            snils = ind_data['snils']
        objs.append(Paragraph(f'6. СНИЛС: {snils}', style))
        address = ind_data['main_address']
        objs.append(Paragraph(f'7. Место регистрации: {address}', style))
        objs.append(Paragraph(f'8. Местность: городская — 1, сельская — 2.', style))
        objs.append(Paragraph(f'9. Диагноз основного заболевания (состояния)_______________________________________________________________', style))
        objs.append(Paragraph(f'_______________________________________________________________________________________________________', style))
        objs.append(Paragraph(f'_______________________________________________________________________________________________________', style))
        diagnosis = ''
        if dir.diagnos.strip():
            diagnosis = dir.diagnos.strip()
        objs.append(Paragraph(f'10. Код по МКБ: {diagnosis}', style))
        objs.append(Paragraph(f'11. Задача прижизненного патолого-анатомического исследования биопсийного (операционного) материала', style))
        objs.append(Paragraph(f'_______________________________________________________________________________________________________', style))
        objs.append(Paragraph(f'12. Дополнительные клинические сведения (основные симптомы, оперативное или гормональное, или лучевое лечение,', style))
        objs.append(Paragraph(f'результаты инструментальных и лабораторных исследований)__________________________________________________', style))
        objs.append(Paragraph(f'_______________________________________________________________________________________________________', style))
        objs.append(Paragraph(f'14. Проведенное предоперационное лечение (вид лечения, его сроки, дозировка лекарственного препарата, доза облучения)', style))
        objs.append(Paragraph(f'_______________________________________________________________________________________________________', style))
        objs.append(Paragraph(f'_______________________________________________________________________________________________________', style))
        objs.append(Paragraph(f'15. Способ получения биопсийного (операционного) материала: эндоскопическая биопсия—1, пункционная биопсия—2,', style))
        objs.append(Paragraph(f'аспирационная биопсия—3, инцизионная биопсия—4, операционная биопсия—5, операционный материал—6,', style))
        objs.append(Paragraph(f'самопроизвольно отделившиеся фрагменты тканей—7.', style))
        objs.append(Paragraph(f'16. Дата забора материала_________________________ время ______________', style))
        objs.append(Paragraph(f'17. Материал помещен в 10%-ный раствор нейтрального формалина (да/нет)___________', style))
        objs.append(Paragraph(f'18. Маркировка биопсийного (операционного) материала (расшифровка маркировки флаконов):', style))

        opinion = [
            [Paragraph(f'Номер флакона', styleT),
             Paragraph('Локализация патологического процесса (орган, топография)', styleT),
             Paragraph('Характер патологического процесса (эрозия, язва, полип, пятно, узел, внешне не измененная ткань, отношение к окружающим тканям)', styleT),
             Paragraph('Количество объектов', styleT)],
            [Paragraph(f'1', styleT), Paragraph('', styleT), Paragraph('', styleT), Paragraph('', styleT)],
            [Paragraph(f'2', styleT), Paragraph('', styleT), Paragraph('', styleT), Paragraph('', styleT)],
            [Paragraph(f'3', styleT), Paragraph('', styleT), Paragraph('', styleT), Paragraph('', styleT)],
            [Paragraph(f'4', styleT), Paragraph('', styleT), Paragraph('', styleT), Paragraph('', styleT)],
            [Paragraph(f'5', styleT), Paragraph('', styleT), Paragraph('', styleT), Paragraph('', styleT)],
        ]

        cols_width = [20 * mm, 50 * mm, 100 * mm, 30 * mm]
        tbl = Table(opinion, colWidths=cols_width)
        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        objs.append(Spacer(1, 5 * mm))
        objs.append(tbl)
        objs.append(Spacer(1, 5 * mm))
        objs.append(Paragraph(f'19. Фамилия, инициалы врача: {dir.doc.get_fio()} {space_symbol * 5} подпись _________', style))
        objs.append(Paragraph(f'20. Дата направления:  {strdate(dir.data_sozdaniya)}', style))

        organoztion_frame = Frame(0 * mm, 0 * mm, 210 * mm, 297 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)
        organoztion_inframe = KeepInFrame(210 * mm, 297 * mm, objs, hAlign='LEFT', vAlign='TOP', fakeWidth=False)
        organoztion_frame.addFromList([organoztion_inframe], c)

    printForm()
