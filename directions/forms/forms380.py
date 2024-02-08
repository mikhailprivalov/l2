import os
from copy import deepcopy
from typing import Union, List

import pytils
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from django.utils.text import Truncator
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import eanbc, qr
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors

from api.stationar.stationar_func import hosp_get_hosp_direction
from appconf.manager import SettingManager
from directions.models import Napravleniya, Issledovaniya, DirectionParamsResult
from reportlab.platypus import Table, TableStyle, Paragraph, Frame, KeepInFrame, Spacer, HRFlowable
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4

from forms.forms_func import hosp_get_clinical_diagnos
from laboratory.settings import FONTS_FOLDER
from laboratory.utils import strdate
from transliterate import translit
import sys
import locale
from laboratory.utils import current_year
from reportlab.graphics.barcode import code128
import datetime

from results.prepare_data import previous_laboratory_result, previous_doc_refferal_result, table_part_result, get_direction_params
from utils.common import get_system_name

w, h = A4


def py(y=0.0):
    y *= mm
    return h - y


def pyb(y=0.0):
    y *= mm
    return y


def px(x=0.0):
    return x * mm


def pxr(x=0.0):
    x *= mm
    return w - x


def form_01(c: Canvas, d: Napravleniya):
    def printForm(offset):
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.2 * mm)
        c.setFont('TimesNewRoman', 8)
        topw1 = pxr(61.5)
        c.drawString(topw1, py(19.6 + offset), "Приложение 5")
        c.drawString(topw1, py(22.74 + offset), "к приказу министерства")
        c.drawString(topw1, py(25.88 + offset), "здравоохранения Иркутской области")
        c.drawString(topw1, py(29.02 + offset), "от 17.08.2009 г. № 1027-мпр.")

        c.setFont('TimesNewRoman', 11)
        c.drawString(px(18.5), py(34 + offset), "Наименование учереждения здравоохранения: " + d.hospital_short_title)
        c.line(px(95.5), py(35.2 + offset), pxr(18), py(35.2 + offset))
        c.drawString(px(18.5), py(43 + offset), "Отделение, палата")
        c.line(px(50), py(44.2 + offset), pxr(18), py(44.2 + offset))
        c.drawCentredString(w / 2, py(53 + offset), "НАПРАВЛЕНИЕ БИОЛОГИЧЕСКОГО МАТЕРИАЛА ДЛЯ ИССЛЕДОВАНИЯ")
        c.drawCentredString(w / 2, py(58 + offset), "НА ВИЧ № {}".format(d.pk))

        c.drawString(px(18.5), py(68 + offset), "Фамилия: " + d.client.individual.family)
        c.line(px(34.8), py(69.2 + offset), pxr(97.5), py(69.2 + offset))
        c.drawString(pxr(97), py(68 + offset), "Имя: " + d.client.individual.name)
        c.line(pxr(88.7), py(69.2 + offset), pxr(18), py(69.2 + offset))

        c.drawString(px(18.5), py(73 + offset), "Отчество: " + d.client.individual.patronymic)
        c.line(px(35), py(74.2 + offset), pxr(114.5), py(74.2 + offset))
        c.drawString(pxr(114), py(73 + offset), "Дата рождения(число,месяц,год): " + d.client.individual.birthday.strftime("%d.%m.%Y"))
        c.line(pxr(58.5), py(74.2 + offset), pxr(18), py(74.2 + offset))

        c.drawString(px(18.5), py(78 + offset), "Адрес регистрации(прописки): " + d.client.main_address)
        c.line(px(71), py(79.2 + offset), pxr(18), py(79.2 + offset))

        c.drawString(px(18.5), py(83 + offset), "Адрес фактического места проживания: " + d.client.fact_address)
        c.line(px(85), py(84.2 + offset), pxr(18), py(84.2 + offset))

        c.drawString(px(18.5), py(88 + offset), "Социальный статус: ")
        c.line(px(52.3), py(89.2 + offset), pxr(18), py(89.2 + offset))

        c.drawString(px(18.5), py(93 + offset), "Код: " + d.vich_code)
        c.line(px(26.3), py(94.2 + offset), px(52), py(94.2 + offset))
        c.drawString(px(53), py(93 + offset), "Диагноз: ")
        c.line(px(68), py(94.2 + offset), pxr(18), py(94.2 + offset))

        c.drawString(px(18.5), py(98 + offset), "ФИО врача, направившего на обследование: {}".format(d.doc.get_full_fio()))
        c.line(pxr(117.5), py(99.2 + offset), pxr(18), py(99.2 + offset))

        c.drawString(px(18.5), py(103 + offset), "ФИО процедурной м/с: ")
        c.line(px(57.3), py(104.2 + offset), pxr(18), py(104.2 + offset))

        c.drawString(px(18.5), py(108 + offset), "Дата забора крови: «_____»_________________20____г.")

        c.drawString(px(18.5), py(113 + offset), "Дата доставки крови в ИОЦ СПИД: «_____»_________________20____г. (заполняется ИОЦ СПИД)")

        c.drawString(px(18.5), py(123 + offset), "РЕЗУЛЬТАТ ИССЛЕДОВАНИЯ")

        c.drawString(px(18.5), py(133 + offset), "Дата выдачи результата: «_____»_________________20____г.  Подпись ____________________________")

        c.setFont('TimesNewRoman', 8)
        c.drawString(px(18.5), py(139 + offset), f"ИС {get_system_name()}. Форма 38001")

    printForm(0)

    c.setStrokeColorRGB(*([0.8] * 3))
    c.line(px(0), h / 2, pxr(0), h / 2)

    printForm(h / 2 / mm)


def form_02(c: Canvas, dir: Napravleniya):
    def printForm():
        pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.2 * mm)
        c.setFont('PTAstraSerifReg', 12)

        c.drawCentredString((210 / 2) * mm, 280 * mm, dir.hospital_short_title)
        c.drawCentredString((210 / 2) * mm, 275 * mm, SettingManager.get("org_address") + ' ' + SettingManager.get("org_phones"))

        try:
            issledovaniye = Issledovaniya.objects.get(napravleniye=dir.pk)
        except ObjectDoesNotExist:
            issledovaniye = None

        dp_title, full_title = "", ""
        comment, info, service_location_title, localization = "", "", "", ""
        if issledovaniye:
            dp_title = issledovaniye.research.podrazdeleniye.title
            service_location_title = "" if not issledovaniye.service_location else issledovaniye.service_location.title
            full_title = issledovaniye.research.title
            comment = issledovaniye.comment if not service_location_title else ''
            info = issledovaniye.research.paraclinic_info
            localization = "" if not issledovaniye.localization else issledovaniye.localization.title

        c.setFont('PTAstraSerifReg', 14)
        c.drawCentredString((210 / 2) * mm, 265 * mm, 'Направление на ' + dp_title)

        # Точки отсчета
        x_coord, y_coord = 20, 235
        barcode = eanbc.Ean13BarcodeWidget(dir.pk + 460000000000, humanReadable=0, barHeight=10 * mm, barWidth=1.25)
        dir_code = Drawing()
        dir_code.add(barcode)
        renderPDF.draw(dir_code, c, (x_coord + 120) * mm, 250 * mm)

        c.setFont('PTAstraSerifReg', 20)

        # Данные пациента
        y_patient = []
        y = 0
        for i in range(0, 9):
            y_patient.append(y_coord - y)
            y += 5
        c.drawString(x_coord * mm, 250 * mm, "№ " + str(dir.pk))  # Номер направления

        c.setFont('PTAstraSerifReg', 12)
        c.drawString(x_coord * mm, y_patient[0] * mm, "Дата: " + strdate(dir.data_sozdaniya))
        additional_num = dir.additional_num
        history_num = dir.history_num
        if history_num and len(history_num) > 0:
            c.drawString((x_coord + 125) * mm, y_patient[0] * mm, "№ истории: " + history_num)
        elif additional_num and len(additional_num) > 0:
            c.drawString((x_coord + 125) * mm, y_patient[0] * mm, "доп.№: " + additional_num)
        elif dir.client.number_poliklinika and len(dir.client.number_poliklinika) > 0:
            c.drawString((x_coord + 125) * mm, y_patient[0] * mm, "доп.№: " + dir.client.number_poliklinika)

        c.drawString(x_coord * mm, y_patient[1] * mm, "ФИО: " + dir.client.individual.fio())
        c.drawString(x_coord * mm, y_patient[2] * mm, "Пол: " + dir.client.individual.sex)
        c.drawString(x_coord * mm, y_patient[3] * mm, "Д/р: {} ({})".format(dir.client.individual.bd(), dir.client.individual.age_s(direction=dir)))
        c.drawString(x_coord * mm, y_patient[4] * mm, "{}: {}".format("ID" if dir.client.base.is_rmis else "Номер карты", dir.client.number_with_type()))
        diagnosis = dir.diagnos.strip()
        if not dir.imported_from_rmis:
            if diagnosis != "":
                c.drawString(
                    x_coord * mm,
                    y_patient[5] * mm,
                    ("" if dir.vich_code == "" else ("Код: " + dir.vich_code + "  ")) + "Диагноз (МКБ 10): " + ("не указан" if diagnosis == "-" else diagnosis),
                )
            if dir.istochnik_f:
                c.drawString(x_coord * mm, y_patient[6] * mm, "Источник финансирования: " + dir.client.base.title + " - " + dir.istochnik_f.title)
            else:
                c.drawString(x_coord * mm, y_patient[6] * mm, "Источник финансирования: ")
        ind_data = dir.client.get_data_individual()
        if ind_data['oms']['polis_issued'] and ind_data['oms']['polis_num']:
            c.drawString((x_coord) * mm, y_patient[7] * mm, "С/к: " + ind_data['oms']['polis_issued'])
            c.drawString((x_coord) * mm, y_patient[8] * mm, "Полис №: " + ind_data['oms']['polis_num'])

        # Данные направления
        y_dir_data = []
        y = 50
        for i in range(0, 4):
            y_dir_data.append(y_coord - y)
            y += 6

        c.setFont('PTAstraSerifBold', 12)
        c.drawString(x_coord * mm, y_dir_data[0] * mm, "Назначение: " + full_title)
        c.setFont('PTAstraSerifReg', 12)
        c.drawString(x_coord * mm, y_dir_data[1] * mm, "Область исследования (комментарий): " + localization + ' ' + comment)
        c.drawString(x_coord * mm, y_dir_data[2] * mm, "Информация: " + info)
        c.drawString(x_coord * mm, y_dir_data[3] * mm, "Место оказания: " + service_location_title)

        # Специфицные данные формы
        y_dir_form = []
        y = 75
        for i in range(0, 19):
            y_dir_form.append(y_coord - y)
            y += 6
        c.setLineWidth(0.2)
        c.drawString(x_coord * mm, y_dir_form[0] * mm, "Цель исследования:")
        c.line((x_coord + 40) * mm, y_dir_form[0] * mm, 200 * mm, y_dir_form[0] * mm)

        c.drawString(x_coord * mm, y_dir_form[1] * mm, "Онкологические заболевания в анамнезе: " + "отрицает /")
        c.line((x_coord + 95) * mm, y_dir_form[1] * mm, 200 * mm, y_dir_form[1] * mm)

        c.drawString(x_coord * mm, y_dir_form[2] * mm, "Операции по поводу онкологических заболеваний: " + "Нет / Да")
        c.line((x_coord + 110) * mm, y_dir_form[2] * mm, 200 * mm, y_dir_form[2] * mm)

        c.drawString(x_coord * mm, y_dir_form[3] * mm, "Данные инструментальных методов исследования в зоне  исследования МСКТ:")
        c.drawString(x_coord * mm, y_dir_form[4] * mm, "УЗС:")
        c.line((x_coord + 10) * mm, y_dir_form[4] * mm, 200 * mm, y_dir_form[4] * mm)
        c.line(x_coord * mm, y_dir_form[5] * mm, 200 * mm, y_dir_form[5] * mm)
        c.line(x_coord * mm, y_dir_form[6] * mm, 200 * mm, y_dir_form[6] * mm)

        c.drawString(x_coord * mm, y_dir_form[7] * mm, "ФБС, ФГС, колоноскопия, R – графия, МРТ:")
        c.drawString(x_coord * mm, y_dir_form[8] * mm, "Аллергия на контрастные вещества: Нет / Да")
        c.line((x_coord + 83) * mm, y_dir_form[8] * mm, 200 * mm, y_dir_form[8] * mm)

        c.drawString(x_coord * mm, y_dir_form[9] * mm, "При планировании МСКТ ангиографии необходимо указать анализы:")
        c.line(x_coord * mm, y_dir_form[10] * mm, 200 * mm, y_dir_form[10] * mm)

        c.drawString(x_coord * mm, y_dir_form[11] * mm, "При ЭКГ – синхронизированных исследованиях сердца указать ЧСС")
        c.line((x_coord + 125) * mm, y_dir_form[11] * mm, 200 * mm, y_dir_form[11] * mm)

        c.drawString(x_coord * mm, y_dir_form[12] * mm, "При   исследовании   живота   уточнить   проводилось ли в ближайшую неделю исследование")
        c.drawString(x_coord * mm, y_dir_form[13] * mm, "с барием: Нет / Да")
        c.drawString(x_coord * mm, y_dir_form[14] * mm, "Обязательно предоставлять данные предыдущих КТ и МРТ исследований (!!!)")

        # Служебные данные дата, врач, отделение
        c.drawString(x_coord * mm, y_dir_form[17] * mm, "Лечащий врач: " + dir.doc.get_fio())
        c.line((x_coord + 120) * mm, y_dir_form[17] * mm, 200 * mm, y_dir_form[17] * mm)
        c.setFont('PTAstraSerifReg', 9)
        c.drawString((x_coord + 140) * mm, (y_dir_form[17] - 3) * mm, "(подпись)")

        c.setFont('PTAstraSerifReg', 12)
        c.drawString(x_coord * mm, y_dir_form[18] * mm, "Отделение: " + Truncator(dir.get_doc_podrazdeleniye_title()).chars(100))

        # QR-code
        qr_value = translit(dir.client.individual.fio(), 'ru', reversed=True)
        qr_code = qr.QrCodeWidget(qr_value)
        qr_code.barWidth = 80
        qr_code.barHeight = 80
        qr_code.qrVersion = 1
        d = Drawing()
        d.add(qr_code)
        renderPDF.draw(d, c, 170 * mm, 10 * mm)

    printForm()


def form_03(c: Canvas, dir: Napravleniya):
    # Covid-19
    def printForm():
        pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
        pdfmetrics.registerFont(TTFont('Symbola', os.path.join(FONTS_FOLDER, 'Symbola.ttf')))

        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.2 * mm)
        c.setFont('PTAstraSerifBold', 12)

        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = "PTAstraSerifBold"
        style.fontSize = 12
        style.leading = 3.5 * mm
        style.alignment = TA_LEFT

        styleTB = deepcopy(style)
        styleTB.fontName = "PTAstraSerifReg"
        styleTB.fontSize = 10

        styleBold = deepcopy(style)
        styleBold.fontSize = 10

        c.drawString(10 * mm, 287 * mm, "Дата: {}".format(strdate(dir.data_sozdaniya)))

        barcode = eanbc.Ean13BarcodeWidget(dir.pk + 460000000000, humanReadable=0, barHeight=8 * mm, barWidth=1.25)
        dir_code = Drawing()
        dir_code.add(barcode)
        renderPDF.draw(dir_code, c, 150 * mm, 285 * mm)
        c.drawString(100 * mm, 287 * mm, "№ - {}".format(dir.pk))

        c.drawCentredString((210 / 2) * mm, 281 * mm, "Контактные данные учреждения, направляющего материал")
        organization_data = [
            [Paragraph('Название', style), Paragraph(dir.hospital_short_title, styleTB)],
            [Paragraph('Телефон', style), Paragraph(SettingManager.get("org_phones"), styleTB)],
            [Paragraph('Факс', style), Paragraph(SettingManager.get("org_phones"), styleTB)],
            [Paragraph('E-mail', style), Paragraph(SettingManager.get("mail", default='', default_type='s'), styleTB)],
            [Paragraph('Адрес', style), Paragraph(SettingManager.get("org_address"), styleTB)],
            [Paragraph('Ф.И.О, должность лица, отправившего материал', style), Paragraph('', styleTB)],
            [Paragraph('E-mail', style), Paragraph('', styleTB)],
            [Paragraph('Цель исследования', style), Paragraph('Коронавирусная инфекция COVID-19 (2019-nCov)', styleTB)],
            [
                Paragraph('Указания для исследования', style),
                Paragraph(
                    'Во исполнении письма Федеральной службы по надзору в сфере защиты прав потребителей и благополучия человека (Роспотребнадзора) '
                    'от 09.01.2020 № 02/107-2020-27 "О дополнительных мерах по недопущению завозов инфекционных заболеваний"',
                    styleTB,
                ),
            ],
        ]
        tbl_o = Table(
            organization_data,
            colWidths=(
                60 * mm,
                150 * mm,
            ),
        )
        tbl_o.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 1.0, colors.black), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.3 * mm), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        organization_text = [tbl_o]
        organoztion_frame = Frame(10 * mm, 220 * mm, 190 * mm, 60 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
        organoztion_inframe = KeepInFrame(190 * mm, 60 * mm, organization_text, hAlign='CENTRE', vAlign='TOP', fakeWidth=False)
        organoztion_frame.addFromList([organoztion_inframe], c)

        c.drawCentredString((210 / 2) * mm, 219 * mm, "Севедения о заболевшем")
        issledovaniye = Issledovaniya.objects.get(napravleniye=dir.pk)
        localization = issledovaniye.localization.title if issledovaniye.localization else issledovaniye.comment
        patient_data = [
            [Paragraph('Категория', style), Paragraph(localization, styleTB)],
            [Paragraph('ФИО', style), Paragraph(dir.client.individual.fio(), styleTB)],
            [Paragraph('Пол', style), Paragraph(dir.client.individual.sex, styleTB)],
            [Paragraph('Возраст', style), Paragraph(dir.client.individual.age_s(direction=dir), styleTB)],
            [Paragraph('Место проживания (регистрации)', style), Paragraph(dir.client.main_address, styleTB)],
            [Paragraph('Эпидемиологический анамнез, включая место и время пребывания (указывается страна, населенный пункт, провинция)', styleBold), Paragraph('Не выезжал', styleTB)],
            [Paragraph('Дата появления симптомов преспираторного заболевания', style), Paragraph('', styleTB)],
            [Paragraph('Дата (день от начала заболевания) обращения за медицинской помощью', style), Paragraph(strdate(dir.data_sozdaniya), styleTB)],
            [Paragraph('Предварительный диагноз', style), Paragraph('', styleTB)],
            [Paragraph('Состояние (тяжесть заболевания) пр обращении за медицинской помощью', style), Paragraph('', styleTB)],
            [Paragraph('Сопутствующий диагноз', style), Paragraph('', styleTB)],
        ]
        tbl_o = Table(
            patient_data,
            colWidths=(
                105 * mm,
                95 * mm,
            ),
        )
        tbl_o.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 1.0, colors.black), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.3 * mm), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        patient_text = [tbl_o]
        patient_frame = Frame(10 * mm, 138 * mm, 190 * mm, 80 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
        patient_inframe = KeepInFrame(190 * mm, 80 * mm, patient_text, hAlign='CENTRE', vAlign='TOP', fakeWidth=False)
        patient_frame.addFromList([patient_inframe], c)

        c.drawCentredString((210 / 2) * mm, 136 * mm, "Севедения о материале")
        material_data = [
            [Paragraph('Сопроводительный номер на контейнере с биоматериалом', style), Paragraph('Вид биологического материала (нужное отметит)', styleTB)],
            [Paragraph("{}".format(dir.pk), style), Paragraph('<font face="Symbola" size=11>\u2713</font> Мазки из носа и зева', styleTB)],
            [Paragraph('', style), Paragraph('<font face="Symbola" size=10>\u25CB</font> Сыворотка', styleTB)],
            [Paragraph('', style), Paragraph('<font face="Symbola" size=10>\u25CB</font> Мокрота', styleTB)],
            [Paragraph('', style), Paragraph('<font face="Symbola" size=10>\u25CB</font> Моча', styleTB)],
            [Paragraph('', style), Paragraph('<font face="Symbola" size=10>\u25CB</font> Другое указать', styleTB)],
            [Paragraph('Дата отбора материала', style), Paragraph(strdate(dir.data_sozdaniya), styleTB)],
            [Paragraph('ФИО, должность забиравшего материал, телефон', style), Paragraph('', styleTB)],
            [Paragraph('Дата получения материала в лабораторном подразделении', style), Paragraph('', styleTB)],
        ]
        tbl_o = Table(
            material_data,
            colWidths=(
                105 * mm,
                95 * mm,
            ),
        )
        tbl_o.setStyle(
            TableStyle([('GRID', (0, 0), (-1, -1), 1.0, colors.black), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.3 * mm), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('SPAN', (0, 1), (0, 5))])
        )
        material_text = [tbl_o]
        material_frame = Frame(10 * mm, 75 * mm, 190 * mm, 60 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
        material_inframe = KeepInFrame(190 * mm, 60 * mm, material_text, hAlign='CENTRE', vAlign='TOP', fakeWidth=False)
        material_frame.addFromList([material_inframe], c)

        c.drawCentredString((210 / 2) * mm, 74 * mm, "Севедения о проведенных исследованиях")
        result_data = [
            [Paragraph('Показатель', style), Paragraph('Результат', style)],
            [
                Paragraph(
                    'РНК вируса гриппа, респираторно-синициального вируса, метапневмовируса, вирусов парагриппа 1,2,3,3 типов, коронавируа, '
                    'риновируса, ДНК аденовирусов групп В, С и Е, бокавируса, ДНК Mycoplasma pneumonia и Chlamydophila pneumonia',
                    styleBold,
                ),
                Paragraph('', styleTB),
            ],
            [Paragraph('2019-nCov', style), Paragraph('', styleTB)],
        ]
        tbl_o = Table(result_data, colWidths=(105 * mm, 95 * mm))
        tbl_o.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 1.0, colors.black), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.3 * mm), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        result_text = [tbl_o]
        result_frame = Frame(10 * mm, 42 * mm, 190 * mm, 30 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
        result_inframe = KeepInFrame(190 * mm, 30 * mm, result_text, hAlign='CENTRE', vAlign='TOP', fakeWidth=False)
        result_frame.addFromList([result_inframe], c)

        c.drawCentredString((210 / 2) * mm, 37 * mm, "Севедения об отправке материала")
        result_data = [
            [Paragraph('Дата и время отправки материала (номер рейса)', style), Paragraph('', style)],
            [
                Paragraph('По адресу', style),
                Paragraph('ФБУЗ "Центр гигиены и эпидимиологии в Иркутской области" Отделение вирусологических исследований с ПЦР лабораторией и микробиологической лаборатории', styleTB),
            ],
        ]
        tbl_o = Table(
            result_data,
            colWidths=(
                60 * mm,
                150 * mm,
            ),
        )
        tbl_o.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 1.0, colors.black), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.3 * mm), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        result_text = [tbl_o]
        result_frame = Frame(10 * mm, 10 * mm, 190 * mm, 25 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
        result_inframe = KeepInFrame(190 * mm, 25 * mm, result_text, hAlign='CENTRE', vAlign='TOP', fakeWidth=False)
        result_frame.addFromList([result_inframe], c)

    printForm()


def form_04(c: Canvas, dir: Napravleniya):
    # Микробиология - Учетная форма № 204/у Утверждена приказом 10130
    def printForm():
        hospital_name = dir.hospital_short_title
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
        style.leading = 12
        style.spaceAfter = 1.5 * mm

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

        styleTCentre = deepcopy(styleT)
        styleTCentre.alignment = TA_CENTER
        styleTCentre.fontSize = 13

        barcode = eanbc.Ean13BarcodeWidget(dir.pk + 460000000000, humanReadable=0, barHeight=8 * mm, barWidth=1.25)
        dir_code = Drawing()
        dir_code.add(barcode)
        renderPDF.draw(dir_code, c, 157 * mm, 259 * mm)

        objs = []
        opinion = [
            [
                Paragraph(f'<font size=11>{hospital_name}<br/>Адрес: {hospital_address}<br/>ОГРН: {hospital_kod_ogrn} <br/> </font>', styleT),
                Paragraph('<font size=9 >Код формы по ОКУД:<br/>Код организации по ОКПО: <br/>' 'Медицинская документация<br/>Учетная форма № 204/у</font>', styleT),
            ],
        ]

        tbl = Table(opinion, 2 * [100 * mm])
        tbl.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.75, colors.white), ('LEFTPADDING', (1, 0), (-1, -1), 55 * mm), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))

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
        ind_data = dir.client.get_data_individual()
        if ind_data['oms']['polis_num']:
            polis_num = ind_data['oms']['polis_num']
        if ind_data['oms']['polis_issued']:
            polis_issue = ind_data['oms']['polis_issued']
        objs.append(Paragraph(f'Полис ОМС: {polis_num} с/к: {polis_issue}', style))
        address = ind_data['main_address']
        objs.append(Paragraph(f'Карта: {dir.client.number_with_type()}', style))
        objs.append(Paragraph(f'Отделение: {dir.get_doc_podrazdeleniye_title()} {space_symbol * 7} палата _______ ', style))
        objs.append(Paragraph(f'Адрес постоянного места жительства: {address}', style))
        objs.append(Paragraph(f'Место работы, учебы (наименование детского учреждения, школы): {dir.workplace}', style))
        clinical_diagnos = ''
        if dir.parent:
            hosp_nums_obj = hosp_get_hosp_direction(dir.parent.napravleniye_id)
            if len(hosp_nums_obj) > 0:
                clinical_diagnos = hosp_get_clinical_diagnos(hosp_nums_obj)[0]

        objs.append(Paragraph(f"Диагноз, дата заболевания:  <font face=\"PTAstraSerifBold\">{clinical_diagnos}</font>", style))
        objs.append(Paragraph('_______________________________________________________________________________________________________', style))

        issledovaniya = dir.issledovaniya_set.all()
        opinion = [
            [
                Paragraph('Цель и наименование исследования', styleCenterBold),
                Paragraph('Материал - место взятия', styleCenterBold),
                Paragraph('Показания к обследованию', styleCenterBold),
                Paragraph('Номер', styleCenterBold),
            ],
        ]

        for v in issledovaniya:
            tmp_value = []
            tmp_value.append(Paragraph(f"{v.research.title}<br/>{v.research.code}", styleT))
            type_material = "" if not v.research.site_type else v.research.site_type.title
            service_location_title = "" if not v.service_location else v.service_location.title
            tmp_value.append(Paragraph(f"{type_material}-{service_location_title}", styleT))
            category_patient = v.localization.title if v.localization else v.comment
            tmp_value.append(Paragraph(f"{category_patient}", styleT))
            num_iss = '{:,}'.format(v.pk).replace(',', ' ')
            iss_barcode128 = code128.Code128(v.pk, barHeight=10 * mm, barWidth=1.25, lquiet=1 * mm)
            tmp_value.append(Paragraph(f"{num_iss}", styleTCentre))
            opinion.append(tmp_value.copy())
            opinion.append([Paragraph('', styleT), Paragraph('', styleT), Paragraph('', styleT), iss_barcode128])

        style_table = []
        style_table.append(('VALIGN', (0, 0), (-1, -1), 'TOP'))
        style_table.append(('GRID', (0, 0), (-1, -1), 0.75, colors.black))
        count_rows = len(opinion)
        for i in range(count_rows):
            if i % 2 == 0 and i != 0:
                for count_col in range(3):
                    style_table.append(('SPAN', (count_col, i), (count_col, i - 1)))
                    style_table.append(('SPA', (count_col, i), (count_col, i - 1)))
                    style_table.append(('LINEABOVE', (-1, i), (-1, i), 2, colors.white))

        style_table.append(('LINEBEFORE', (-1, 0), (-1, -1), 0.75, colors.black))
        style_table.append(('LINEAFTER', (-1, 0), (-1, -1), 0.75, colors.black))
        cols_width = [95 * mm, 35 * mm, 32 * mm, 40 * mm]
        tbl = Table(opinion, colWidths=cols_width, hAlign='LEFT')
        tbl.setStyle(TableStyle(style_table))
        objs.append(Spacer(1, 5 * mm))
        objs.append(tbl)

        objs.append(Spacer(1, 5 * mm))
        objs.append(Paragraph(f'Врач: {dir.doc.get_fio()} {space_symbol * 5} подпись _________', style))
        if dir.doc_who_create and dir.doc_who_create != dir.doc:
            objs.append(Paragraph(f'Выписал: {dir.doc_who_create.get_fio()}', style))
        objs.append(Paragraph(f'Дата направления:  {strdate(dir.data_sozdaniya)}', style))

        gistology_frame = Frame(0 * mm, 0 * mm, 210 * mm, 297 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)
        gistology_inframe = KeepInFrame(210 * mm, 297 * mm, objs, hAlign='LEFT', vAlign='TOP', fakeWidth=False)
        gistology_frame.addFromList([gistology_inframe], c)

    printForm()


def form_05(c: Canvas, dir_obj: Union[QuerySet, List[Napravleniya]]):
    # Утверждено Приказом Министерства здравоохранения Иркутской области от 22 мая 2013 г. N 83-МПР
    def printForm(dir):
        if sys.platform == 'win32':
            locale.setlocale(locale.LC_ALL, 'rus_rus')
        else:
            locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

        pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

        try:
            issledovaniye = Issledovaniya.objects.filter(napravleniye=dir.pk)
        except ObjectDoesNotExist:
            issledovaniye = None
        title_research = []
        is_doc_refferal = False

        for i in issledovaniye:
            title_research.append(i.research.title)
            if i.research.is_doc_refferal:
                is_doc_refferal = True

        title_research = "<br/>".join(title_research)

        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = "PTAstraSerifReg"
        style.fontSize = 11
        style.leading = 12
        style.spaceAfter = 1.5 * mm

        styleBold = deepcopy(style)
        styleBold.fontName = 'PTAstraSerifBold'

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

        styleTCentre = deepcopy(styleT)
        styleTCentre.alignment = TA_CENTER
        styleTCentre.fontSize = 13

        barcode = eanbc.Ean13BarcodeWidget(dir.pk + 460000000000, humanReadable=0, barHeight=8 * mm, barWidth=1.25)
        dir_code = Drawing()
        dir_code.add(barcode)
        renderPDF.draw(dir_code, c, 154 * mm, 255 * mm)

        objs = []
        opinion = [
            [
                Paragraph(f'<font size=11>{dir.hospital_title}<br/>Адрес: {dir.hospital_address}<br/>ОГРН: {dir.hospital.ogrn} <br/> </font>', styleT),
                Paragraph('<font size=9 >Утверждено<br/>Приказом Министерства здравоохранения<br/>Иркутской области от 22 мая 2013 г. N 83-МПР</font>', styleT),
            ],
        ]

        tbl = Table(opinion, 2 * [100 * mm])
        tbl.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.75, colors.white), ('LEFTPADDING', (1, 0), (-1, -1), 55 * mm), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))

        objs.append(tbl)
        objs.append(Spacer(1, 3 * mm))
        objs.append(Paragraph(f'НАПРАВЛЕНИЕ № {dir.pk}', styleCenterBold))
        objs.append(Paragraph('в медицинские организации Иркутской области', styleCenterBold))
        objs.append(Spacer(1, 3 * mm))
        space_symbol = '&nbsp;'
        objs.append(Paragraph(f'От: {strdate(dir.data_sozdaniya)}', style))
        objs.append(Paragraph(f'Фамилия, Имя, Отчество: {dir.client.individual.fio()}', style))
        sex = dir.client.individual.sex
        if sex == "м":
            sex = f'{sex}-1'
        else:
            sex = f'{sex}-2'
        born = dir.client.individual.bd().split('.')
        objs.append(Paragraph(f'Дата <u>{born[0]}</u> Месяц <u>{born[1]}</u> Год рождения <u>{born[2]}</u> Пол {sex} ', style))
        objs.append(Paragraph(f'Рабочий, домашний телефон : {dir.client.phone}', style))
        polis_num = ''
        polis_issue = ''
        ind_data = dir.client.get_data_individual()
        if ind_data['oms']['polis_num']:
            polis_num = ind_data['oms']['polis_num']
        if ind_data['oms']['polis_issued']:
            polis_issue = ind_data['oms']['polis_issued']
        address = ind_data['main_address']
        objs.append(Paragraph(f'Регистрация по месту жительства: {address}', style))
        objs.append(Paragraph(f"Страховой полис серия: _______ №{polis_num}", style))
        objs.append(Paragraph(f"Страховая компания (наименование): {polis_issue}", style))
        external_org = dir.external_organization.title if dir.external_organization else ""
        objs.append(Paragraph(f"Направляется в: {external_org}", style))
        objs.append(Paragraph("Дата приема _______________________ Время приема _________________", style))
        objs.append(Paragraph(f"Наименование медицинской организации по месту прикрепления: {dir.hospital_address} {dir.hospital_title}", style))
        objs.append(Paragraph(f"Наименование направившей медицинской организации: {dir.hospital_address} {dir.hospital_title}", style))
        objs.append(Paragraph("Направлен(а) на:", style))
        objs.append(Paragraph("1) консультацию (вписать специалистов)", style))
        if is_doc_refferal:
            objs.append(Paragraph(f"{title_research}", styleBold))
        objs.append(Paragraph("2) исследование (указать вид исследования)", style))
        if not is_doc_refferal:
            objs.append(Paragraph(f"{title_research}", styleBold))
        objs.append(Paragraph("3) госпитализацию", style))
        objs.append(Paragraph("____________________________________________________", style))
        objs.append(Paragraph("Цель консультации (и, или) исследования (нужное обвести):", style))
        direction_params = DirectionParamsResult.objects.filter(napravleniye=dir)
        descriptive_values = []
        laboratory_value, purpose, table_value = None, None, None
        main_diagnos, near_diagnos, anamnes, other_purpose = '', '', '', ''

        for param in direction_params:
            if param.field_type == 24:
                laboratory_value = param.value
            if param.field_type == 27:
                table_value = param.value
            if param.field_type in [26, 25]:
                descriptive_values.append(param.value)
            if param.title == 'Цель':
                purpose = param.value
            if param.title == 'Прочие цели':
                other_purpose = param.value
            if param.title == 'Диагноз основной':
                main_diagnos = param.value
            if param.title == 'Диагноз сопутствующий':
                near_diagnos = f"{near_diagnos} {param.value}"
            if param.title == 'Данные анамнеза':
                anamnes = param.value

        if purpose:
            objs.append(Paragraph(f"{space_symbol * 10} {purpose} {other_purpose}", style))
        else:
            objs.append(Paragraph(f"{space_symbol * 10}01 - дообследование при неясном диагнозе;", style))
            objs.append(Paragraph(f"{space_symbol * 10}02 - уточнение диагноза;", style))
            objs.append(Paragraph(f"{space_symbol * 10}03 - для коррекции лечения;", style))
            objs.append(Paragraph(f"{space_symbol * 10}04 - дообследование для госпитализации;", style))
            objs.append(Paragraph(f"{space_symbol * 10}05 - и прочие цели (нужное вписать) __________________", style))
        objs.append(Paragraph("Диагноз направившей медицинской организации (диагноз/ код диагноза в соответствии с МКБ10):", style))
        if main_diagnos:
            objs.append(Paragraph(f"Основной{main_diagnos}", style))
        else:
            objs.append(Paragraph("Основной ______________________________________________________________________________________", style))
        if near_diagnos:
            objs.append(Paragraph(f"Сопутствующий {near_diagnos}", style))
        else:
            objs.append(Paragraph("Сопутствующий ______________________________________________________________________________________", style))
        objs.append(Spacer(1, 3 * mm))
        objs.append(Paragraph("Выписка из амбулаторной карты:", style))
        objs.append(Paragraph("(данные анамнеза, клиники, предварительного обследования и проведенного лечения)", style))
        if anamnes:
            objs.append(Paragraph(f"{anamnes}", style))
        else:
            objs.append(Paragraph("______________________________________________________________________________________", style))
            objs.append(Paragraph("______________________________________________________________________________________", style))
            objs.append(Paragraph("______________________________________________________________________________________", style))
            objs.append(Paragraph("______________________________________________________________________________________", style))
            objs.append(Paragraph("______________________________________________________________________________________", style))
        for v in descriptive_values:
            objs = previous_doc_refferal_result(v, objs)
        if laboratory_value:
            lab_values = previous_laboratory_result(laboratory_value)
            if lab_values:
                objs.extend(lab_values)
        if table_value:
            table_value_result = table_part_result(table_value)
            if table_value_result:
                objs.extend(table_value_result)

        objs.append(Paragraph("______________________________________________________________________________________", style))
        objs.append(Paragraph("Сведения о профилактических прививках (для детей до 18 лет) ________________________", style))
        objs.append(Paragraph("______________________________________________________________________________________", style))
        objs.append(Paragraph("______________________________________________________________________________________", style))
        objs.append(Paragraph("______________________________________________________________________________________", style))
        objs.append(Paragraph("Справка об отсутствии инфекционных контактов (для детей до 18 лет), выданная не ранее 3 дней на дату поступления в ОГУЗ ", style))
        objs.append(Paragraph("______________________________________________________________________________________", style))
        objs.append(Paragraph("Врач ___________________________________________________________________________", style))
        objs.append(Paragraph('телефон ____________________________ "_____" _____________ 20__ г.', style))
        objs.append(Paragraph("Руководитель направившей медицинской организации", style))
        objs.append(Paragraph("Согласие пациента на передачу сведений электронной почтой для осуществления предварительной записи и передачи заключения:", style))

        print_frame = Frame(0 * mm, mm, 210 * mm, 297 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)
        for p in objs:
            while print_frame.add(p, c) == 0:
                print_frame.split(p, c)
                c.showPage()
                print_frame = Frame(0 * mm, mm, 210 * mm, 297 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)

    count = 0
    for dir in dir_obj:
        count += 1
        if count > 1:
            c.showPage()
        printForm(dir)


def form_06(c: Canvas, dir_obj: Union[QuerySet, List[Napravleniya]]):
    # Заявление на ВМП
    def printForm(dir: Napravleniya):
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
        style.leading = 12
        style.spaceAfter = 1.5 * mm

        styleBold = deepcopy(style)
        styleBold.fontName = 'PTAstraSerifBold'

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

        styleTCentre = deepcopy(styleT)
        styleTCentre.alignment = TA_CENTER
        styleTCentre.fontSize = 13

        styleSign = deepcopy(style)
        styleSign.firstLineIndent = 0
        styleSign.alignment = TA_LEFT
        styleSign.leading = 13

        barcode = eanbc.Ean13BarcodeWidget(dir.pk + 460000000000, humanReadable=0, barHeight=8 * mm, barWidth=1.25)
        dir_code = Drawing()
        dir_code.add(barcode)
        renderPDF.draw(dir_code, c, 10 * mm, 250 * mm)

        objs = []
        hospital_name = dir.hospital.title
        short_name = dir.hospital.short_title
        phones = dir.hospital.phones
        hospital_address = dir.hospital.address

        objs.append(Spacer(1, 3 * mm))
        objs.append(Paragraph(f'{hospital_name.upper()}', styleCenterBold))
        objs.append(HRFlowable(width=190 * mm, spaceAfter=3 * mm, spaceBefore=3 * mm, color=colors.black, thickness=1.5))
        opinion = [
            [
                Paragraph(f'<font size=11>{hospital_address}</font>', styleT),
                Paragraph(f'<font size=9 >{phones}</font>', styleT),
            ],
        ]

        tbl = Table(opinion, 2 * [100 * mm])
        tbl.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.75, colors.white), ('LEFTPADDING', (1, 0), (-1, -1), 55 * mm), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        objs.append(tbl)

        opinion = [
            [
                Paragraph('', styleT),
                Paragraph(f'В комиссию {short_name}<br/>По отбору и направлению больных<br/> На оказание высокотехнологичной<br/> Медицинской помощи', styleT),
            ],
        ]

        tbl = Table(opinion, 2 * [100 * mm])
        tbl.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.75, colors.white), ('LEFTPADDING', (1, 0), (-1, -1), 35 * mm), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        objs.append(tbl)
        objs.append(Spacer(1, 5 * mm))
        objs.append(
            Paragraph(
                'Заявление пациента (законного представителя пациента) о<br/>' 'рассмотрении медицинских документов и оказание<br/>высокотехнологичной медицинской помощи.', styleCenterBold
            )
        )

        objs.append(Spacer(1, 5 * mm))

        ind_card = dir.client
        patient_data = ind_card.get_data_individual()

        agent_status = False
        if ind_card.who_is_agent:
            p_agent = getattr(ind_card, ind_card.who_is_agent)
            agent_status = bool(p_agent)

        # Если владельцу карты меньше 15 лет и не передан представитель, то вернуть ошибку
        who_patient = 'пациента'
        if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i') and not agent_status:
            return False
        elif patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i') and agent_status:
            who_patient = 'ребёнка'

        if agent_status:
            person_data = p_agent.get_data_individual()
        else:
            person_data = patient_data

        d = datetime.datetime.strptime(person_data['born'], '%d.%m.%Y').date()
        date_individual_born = pytils.dt.ru_strftime(u"\"%d\" %B %Y", inflected=True, date=d)

        objs.append(Spacer(1, 3 * mm))
        objs.append(Paragraph('Я, нижеподписавшийся(аяся) {}&nbsp; {} г. рождения'.format(person_data['fio'], date_individual_born), styleSign))

        styleLeft = deepcopy(style)
        styleLeft.alignment = TA_LEFT
        objs.append(Paragraph('Зарегистрированный(ая) по адресу: {}'.format(person_data['main_address']), styleSign))
        objs.append(Paragraph('Проживающий(ая) по адресу: {}'.format(person_data['fact_address']), styleSign))
        objs.append(
            Paragraph(
                'Документ, удостоверяющий личность {}: серия <u> {}</u> номер: <u>{}</u>'.format(person_data['type_doc'], person_data['passport_serial'], person_data['passport_num']),
                styleSign,
            )
        )
        objs.append(Paragraph('Выдан: {} {}'.format(person_data['passport_date_start'], person_data['passport_issued']), styleSign))
        objs.append(Spacer(1, 2 * mm))

        if agent_status:
            opinion = [
                Paragraph('являюсь законным представителем ({}) {}:'.format(ind_card.get_who_is_agent_display(), who_patient), styleBold),
                Paragraph('{}&nbsp; {} г. рождения'.format(patient_data['fio'], patient_data['born']), styleSign),
                Paragraph('Зарегистрированный(ая) по адресу: {}'.format(patient_data['main_address']), styleSign),
                Paragraph('Проживающий(ая) по адресу: {}'.format(patient_data['fact_address']), styleSign),
            ]
            # Проверить возраст пациента при наличии представителя (ребёнок|взрослый)
            if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i'):
                opinion.append(
                    Paragraph(
                        'Документ, удостоверяющий личность {}: серия <u>{}</u> номер <u>{}</u>'.format(patient_data['type_doc'], patient_data['bc_serial'], patient_data['bc_num']), styleSign
                    )
                )
                opinion.append(Paragraph('Выдан: {} {}'.format(patient_data["bc_date_start"], person_data['bc_issued']), styleSign))
            else:
                opinion.append(
                    Paragraph(
                        'Документ, удостоверяющий личность {}: серия {} номер {}'.format(patient_data['type_doc'], patient_data['passport_serial'], patient_data['passport_num']), styleSign
                    )
                )
                opinion.append(Paragraph('Выдан: {} {}'.format(patient_data["passport_date_start"], person_data['passport_issued']), styleSign))

            objs.extend(opinion)

        objs.append(Spacer(1, 2 * mm))
        direction_params = DirectionParamsResult.objects.filter(napravleniye=dir)
        department, main_diagnos = '', ''
        result = get_direction_params(direction_params, ['Диагноз', 'Отделение'])
        for k, v in result.items():
            if k == 'Диагноз':
                main_diagnos = v
            if k == 'Отделение':
                department = v

        objs.append(Paragraph(f'госпитализированного в отделение {department}', style))
        objs.append(Paragraph(f'прошу рассмотреть медицинские документы и оказать высокотехнологичную медицинскую помощь по поводу (диагноз): {main_diagnos}', style))

        objs.append(Spacer(1, 5 * mm))
        objs.append(Paragraph(f'Место проведения лечения: {short_name}', style))

        space_symbol = '&nbsp;'

        date_now = pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=datetime.datetime.now())
        objs.append(Spacer(1, 15 * mm))

        objs.append(Paragraph(f'<u>{date_now} г.</u> {15 * space_symbol} ______________________________ {25 * space_symbol} _________________________', style))
        objs.append(Paragraph(f'{space_symbol * 5}(дата) {45 * space_symbol} (ФИО) {70 * space_symbol} (подпись)', style))

        print_frame = Frame(0 * mm, mm, 210 * mm, 297 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)
        for p in objs:
            while print_frame.add(p, c) == 0:
                print_frame.split(p, c)
                c.showPage()
                print_frame = Frame(0 * mm, mm, 210 * mm, 297 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)

    printForm(dir_obj)


def form_07(c: Canvas, dir: Napravleniya):
    # Универсальная форма с параметрами
    def printForm():
        hospital_name = dir.hospital_short_title
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
        style.leading = 12
        style.spaceAfter = 1.5 * mm

        styleCenterBold = deepcopy(style)
        styleCenterBold.alignment = TA_CENTER
        styleCenterBold.fontSize = 12
        styleCenterBold.leading = 15
        styleCenterBold.fontName = 'PTAstraSerifBold'

        styleBold = deepcopy(styleCenterBold)
        styleBold.alignment = TA_LEFT

        styleT = deepcopy(style)
        styleT.alignment = TA_LEFT
        styleT.fontSize = 10
        styleT.leading = 4.5 * mm
        styleT.face = 'PTAstraSerifReg'

        styleTCentre = deepcopy(styleT)
        styleTCentre.alignment = TA_CENTER
        styleTCentre.fontSize = 13

        barcode = eanbc.Ean13BarcodeWidget(dir.pk + 460000000000, humanReadable=0, barHeight=8 * mm, barWidth=1.25)
        dir_code = Drawing()
        dir_code.add(barcode)
        renderPDF.draw(dir_code, c, 157 * mm, 259 * mm)

        objs = []
        opinion = [
            [
                Paragraph(f'<font size=11>{hospital_name}<br/>Адрес: {hospital_address}<br/>ОГРН: {hospital_kod_ogrn} <br/> </font>', styleT),
                Paragraph('<font size=9 >Код формы по ОКУД:<br/>Код организации по ОКПО: <br/>' 'Медицинская документация<br/>Учетная форма № 204/у</font>', styleT),
            ],
        ]

        tbl = Table(opinion, 2 * [100 * mm])
        tbl.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.75, colors.white), ('LEFTPADDING', (1, 0), (-1, -1), 55 * mm), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))

        objs.append(tbl)
        objs.append(Spacer(1, 3 * mm))
        history_num = ''
        if dir.parent and dir.parent.research.is_hospital:
            history_num = f"(cтационар-{str(dir.parent.napravleniye_id)})"
        objs.append(Paragraph(f'НАПРАВЛЕНИЕ № {dir.pk} {history_num} ', styleCenterBold))
        objs.append(Paragraph('патолого-анатомического вскрытия', styleCenterBold))
        objs.append(Spacer(1, 3 * mm))
        space_symbol = '&nbsp;'
        objs.append(Paragraph(f'Фамилия, Имя, Отчество: {dir.client.individual.fio()}', style))
        sex = dir.client.individual.sex
        if sex == "м":
            sex = f'{sex}-1'
        else:
            sex = f'{sex}-2'
        objs.append(Paragraph(f'Возраст: {dir.client.individual.bd()} ({dir.client.individual.age_s(direction=dir)}) {space_symbol * 5} Пол: {sex},', style))
        polis_num = ''
        polis_issue = ''
        ind_data = dir.client.get_data_individual()
        if ind_data['oms']['polis_num']:
            polis_num = ind_data['oms']['polis_num']
        if ind_data['oms']['polis_issued']:
            polis_issue = ind_data['oms']['polis_issued']
        objs.append(Paragraph(f'Полис ОМС: {polis_num} с/к: {polis_issue}', style))
        address = ind_data['main_address']
        objs.append(Paragraph(f'Адрес постоянного места жительства: {address}', style))
        objs.append(Paragraph(f'Место работы, учебы (наименование детского учреждения, школы): {dir.workplace}', style))

        issledovaniya = dir.issledovaniya_set.all()
        for v in issledovaniya:
            objs.append(Paragraph(f"{v.research.title}", style))
        objs.append(Spacer(1, 5 * mm))
        objs.append(Paragraph("Параметры направления:", styleBold))
        objs.append(Spacer(1, 1 * mm))

        direction_params = DirectionParamsResult.objects.filter(napravleniye=dir)
        for dp in direction_params:
            objs.append(Paragraph(f"{dp.title}: {dp.value}", style))

        objs.append(Spacer(1, 3 * mm))
        objs.append(Paragraph(f'Врач: {dir.doc.get_fio()} {space_symbol * 5} подпись _________', style))
        if dir.doc_who_create and dir.doc_who_create != dir.doc:
            objs.append(Paragraph(f'Выписал: {dir.doc_who_create.get_fio()}', style))
        objs.append(Paragraph(f'Дата направления:  {strdate(dir.data_sozdaniya)}', style))

        gistology_frame = Frame(0 * mm, 0 * mm, 210 * mm, 297 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)
        gistology_inframe = KeepInFrame(210 * mm, 297 * mm, objs, hAlign='LEFT', vAlign='TOP', fakeWidth=False)
        gistology_frame.addFromList([gistology_inframe], c)

    printForm()


def form_08(c: Canvas, dir_obj: Union[QuerySet, List[Napravleniya]]):
    # Универсальное на бак.исследование
    def printForm(dir: Napravleniya):
        if sys.platform == 'win32':
            locale.setlocale(locale.LC_ALL, 'rus_rus')
        else:
            locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

        pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = "PTAstraSerifReg"
        style.fontSize = 12
        style.leading = 12
        style.spaceAfter = 1.5 * mm

        styleBold = deepcopy(style)
        styleBold.fontName = 'PTAstraSerifBold'

        styleCenterBold = deepcopy(style)
        styleCenterBold.alignment = TA_CENTER
        styleCenterBold.fontSize = 12
        styleCenterBold.leading = 15
        styleCenterBold.fontName = 'PTAstraSerifBold'

        styleT = deepcopy(style)
        styleT.alignment = TA_LEFT
        styleT.fontSize = 12
        styleT.leading = 4.5 * mm
        styleT.face = 'PTAstraSerifReg'

        styleTCentre = deepcopy(styleT)
        styleTCentre.alignment = TA_CENTER
        styleTCentre.fontSize = 13

        objs = []

        objs.append(Paragraph(f"Направление № {dir.pk}", style=styleCenterBold))
        patient_data = dir.client.get_data_individual()
        if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i'):
            patient_data['serial'] = patient_data['bc_serial']
            patient_data['num'] = patient_data['bc_num']
        else:
            patient_data['serial'] = patient_data['passport_serial']
            patient_data['num'] = patient_data['passport_num']
        opinion = [
            [
                Paragraph("ФИО:", styleT),
                Paragraph(f"{dir.client.individual.fio()}", styleT),
            ],
            [
                Paragraph("Пол:", styleT),
                Paragraph(f"{dir.client.individual.sex}", styleT),
            ],
            [
                Paragraph("Дата рождения:", styleT),
                Paragraph(f"{dir.client.individual.bd()} ({dir.client.individual.age_s(direction=dir)})", styleT),
            ],
            [
                Paragraph("№ полиса:", styleT),
                Paragraph(f"{patient_data['oms']['polis_num']}", styleT),
            ],
            [
                Paragraph("СНИЛС:", styleT),
                Paragraph(f"{patient_data['snils']}", styleT),
            ],
            [
                Paragraph("Документ: ", styleT),
                Paragraph(f"{patient_data['type_doc']} гражданина России,{patient_data['serial']}, {patient_data['num']}", styleT),
            ],
            [
                Paragraph("Адрес : ", styleT),
                Paragraph(f"{patient_data['main_address']}", styleT),
            ],
            [
                Paragraph("Ds и дата заболевания: ", styleT),
                Paragraph("", styleT),
            ],
            [
                Paragraph("Материал, дата забора", styleT),
                Paragraph("", styleT),
            ],
        ]

        tbl = Table(opinion, colWidths=(40 * mm, 140 * mm))
        tbl.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.75, colors.white), ('LEFTPADDING', (1, 0), (-1, -1), 2 * mm), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        objs.append(Spacer(1, 4 * mm))
        objs.append(tbl)

        objs.append(Spacer(1, 6 * mm))
        objs.append(Paragraph("Результат бактериологического исследования №", style=styleCenterBold))
        objs.append(Paragraph("Выделенная культура", style=style))
        objs.append(Paragraph("______________________________________________________________________", style=style))
        objs.append(Paragraph("______________________________________________________________________", style=style))
        objs.append(Paragraph("______________________________________________________________________", style=style))
        objs.append(Spacer(1, 4 * mm))

        opinion = [
            [Paragraph("Ампицилин", styleT), Paragraph("Налидиксовая к-та", styleT)],
            [Paragraph("Амоксициллин:", styleT), Paragraph("Офлоксацин", styleT)],
            [Paragraph("Оксациллин", styleT), Paragraph("Ципрофлоксацин", styleT)],
            [Paragraph("Цефипим", styleT), Paragraph("Тетрациклин", styleT)],
            [Paragraph("Цефуроксим", styleT), Paragraph("Доксициклин", styleT)],
            [Paragraph("Цефоперазон", styleT), Paragraph("Эритромицин", styleT)],
            [Paragraph("Цефаклор", styleT), Paragraph("Кларитромицин", styleT)],
            [Paragraph("Цефиксим", styleT), Paragraph("Азитромицин", styleT)],
            [Paragraph("Цефотаксим", styleT), Paragraph("Линкомицин", styleT)],
            [Paragraph("Цефтазидим", styleT), Paragraph("Клиндамицин", styleT)],
            [Paragraph("Цефтриаксон", styleT), Paragraph("Пиперациллин", styleT)],
            [Paragraph("Тобрамицин", styleT), Paragraph("Хлорамфеником", styleT)],
            [Paragraph("Амикацин", styleT), Paragraph("Фузидин", styleT)],
            [Paragraph("Пефлоксацин", styleT), Paragraph("Имипенем", styleT)],
            [Paragraph("Фуразолидон", styleT), Paragraph("Гентамицин", styleT)],
            [Paragraph("Норфлоксацин", styleT), Paragraph("Чувствительность к фагу", styleT)],
        ]

        tbl = Table(opinion, colWidths=(90 * mm, 90 * mm))
        tbl.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.75, colors.black), ('LEFTPADDING', (1, 0), (-1, -1), 2 * mm), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        objs.append(tbl)

        objs.append(Spacer(1, 4 * mm))
        objs.append(Paragraph('"___ " __________ 20__ г. Подпись___________________', style=style))

        print_frame = Frame(0 * mm, mm, 210 * mm, 297 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)
        for p in objs:
            while print_frame.add(p, c) == 0:
                print_frame.split(p, c)
                c.showPage()
                print_frame = Frame(0 * mm, mm, 210 * mm, 297 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)

    printForm(dir_obj)


def form_09(c: Canvas, dir_obj: Union[QuerySet, List[Napravleniya]]):
    # Универсальное на 80 mm
    def printForm(dir: Napravleniya):
        if sys.platform == 'win32':
            locale.setlocale(locale.LC_ALL, 'rus_rus')
        else:
            locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

        pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = "PTAstraSerifReg"
        style.fontSize = 12
        style.leading = 12
        style.spaceAfter = 1.5 * mm

        styleBold = deepcopy(style)
        styleBold.fontName = 'PTAstraSerifBold'

        styleCenterBold = deepcopy(style)
        styleCenterBold.alignment = TA_CENTER
        styleCenterBold.fontSize = 12
        styleCenterBold.leading = 15
        styleCenterBold.fontName = 'PTAstraSerifBold'

        styleT = deepcopy(style)
        styleT.alignment = TA_LEFT
        styleT.fontSize = 12
        styleT.leading = 4.5 * mm
        styleT.face = 'PTAstraSerifReg'

        styleTCentre = deepcopy(styleT)
        styleTCentre.alignment = TA_CENTER
        styleTCentre.fontSize = 13

        objs = []

        objs.append(Paragraph(f"Направление № {dir.pk}", style=styleCenterBold))
        patient_data = dir.client.get_data_individual()
        if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i'):
            patient_data['serial'] = patient_data['bc_serial']
            patient_data['num'] = patient_data['bc_num']
        else:
            patient_data['serial'] = patient_data['passport_serial']
            patient_data['num'] = patient_data['passport_num']
        opinion = [
            [
                Paragraph("ФИО:", styleT),
                Paragraph(f"{dir.client.individual.fio()}", styleT),
            ],
            [
                Paragraph("Пол:", styleT),
                Paragraph(f"{dir.client.individual.sex}", styleT),
            ],
            [
                Paragraph("Дата рождения:", styleT),
                Paragraph(f"{dir.client.individual.bd()} ({dir.client.individual.age_s(direction=dir)})", styleT),
            ],
            [
                Paragraph("№ полиса:", styleT),
                Paragraph(f"{patient_data['oms']['polis_num']}", styleT),
            ],
            [
                Paragraph("СНИЛС:", styleT),
                Paragraph(f"{patient_data['snils']}", styleT),
            ],
            [
                Paragraph("Документ: ", styleT),
                Paragraph(f"{patient_data['type_doc']} гражданина России,{patient_data['serial']}, {patient_data['num']}", styleT),
            ],
            [
                Paragraph("Адрес : ", styleT),
                Paragraph(f"{patient_data['main_address']}", styleT),
            ],
            [
                Paragraph("Ds и дата заболевания: ", styleT),
                Paragraph("", styleT),
            ],
            [
                Paragraph("Материал, дата забора", styleT),
                Paragraph("", styleT),
            ],
        ]

        tbl = Table(opinion, colWidths=(40 * mm, 140 * mm))
        tbl.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.75, colors.white), ('LEFTPADDING', (1, 0), (-1, -1), 2 * mm), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        objs.append(Spacer(1, 4 * mm))
        objs.append(tbl)

        objs.append(Spacer(1, 6 * mm))

        tbl = Table(opinion, colWidths=(90 * mm, 90 * mm))
        tbl.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.75, colors.black), ('LEFTPADDING', (1, 0), (-1, -1), 2 * mm), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        objs.append(tbl)

        objs.append(Spacer(1, 4 * mm))
        objs.append(Paragraph('"___ " __________ 20__ г. Подпись___________________', style=style))

        print_frame = Frame(0 * mm, mm, 80 * mm, 150 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)
        for p in objs:
            while print_frame.add(p, c) == 0:
                print_frame.split(p, c)
                c.showPage()
                print_frame = Frame(0 * mm, mm, 80 * mm, 150 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)

    printForm(dir_obj)
