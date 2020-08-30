import os
from copy import deepcopy
from django.core.exceptions import ObjectDoesNotExist
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
from directions.models import Napravleniya, Issledovaniya
from reportlab.platypus import Table, TableStyle, Paragraph, Frame, KeepInFrame, Spacer
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4

from forms.forms_func import hosp_get_clinical_diagnos
from laboratory.settings import FONTS_FOLDER
from laboratory.utils import strdate
from transliterate import translit
import sys
import locale
from laboratory.utils import current_year

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
        c.drawString(px(18.5), py(34 + offset),
                     "Наименование учереждения здравоохранения: " + SettingManager.get("org_title"))
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
        c.drawString(pxr(114), py(73 + offset),
                     "Дата рождения(число,месяц,год): " + d.client.individual.birthday.strftime("%d.%m.%Y"))
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

        c.drawString(px(18.5), py(98 + offset), "ФИО врача, направившего на обследование: {}".format(d.doc.fio))
        c.line(pxr(117.5), py(99.2 + offset), pxr(18), py(99.2 + offset))

        c.drawString(px(18.5), py(103 + offset), "ФИО процедурной м/с: ")
        c.line(px(57.3), py(104.2 + offset), pxr(18), py(104.2 + offset))

        c.drawString(px(18.5), py(108 + offset), "Дата забора крови: «_____»_________________20____г.")

        c.drawString(px(18.5), py(113 + offset),
                     "Дата доставки крови в ИОЦ СПИД: «_____»_________________20____г. (заполняется ИОЦ СПИД)")

        c.drawString(px(18.5), py(123 + offset), "РЕЗУЛЬТАТ ИССЛЕДОВАНИЯ")

        c.drawString(px(18.5), py(133 + offset),
                     "Дата выдачи результата: «_____»_________________20____г.  Подпись ____________________________")

        c.setFont('TimesNewRoman', 8)
        c.drawString(px(18.5), py(139 + offset), "ИС L2. Форма 38001")

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

        c.drawCentredString((210 / 2) * mm, 280 * mm, SettingManager.get("org_title"))
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
        c.drawString(x_coord * mm, y_patient[3] * mm,
                     "Д/р: {} ({})".format(dir.client.individual.bd(), dir.client.individual.age_s(direction=dir)))
        c.drawString(x_coord * mm, y_patient[4] * mm,
                     "{}: {}".format("ID" if dir.client.base.is_rmis else "Номер карты", dir.client.number_with_type()))
        diagnosis = dir.diagnos.strip()
        if not dir.imported_from_rmis:
            if diagnosis != "":
                c.drawString(x_coord * mm, y_patient[5] * mm,
                             ("" if dir.vich_code == "" else (
                                 "Код: " + dir.vich_code + "  ")) + "Диагноз (МКБ 10): " + (
                                 "не указан" if diagnosis == "-" else diagnosis))
            if dir.istochnik_f:
                c.drawString(x_coord * mm, y_patient[6] * mm,
                             "Источник финансирования: " + dir.client.base.title + " - " + dir.istochnik_f.title)
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
        c.setLineWidth(.2)
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
        c.drawString(x_coord * mm, y_dir_form[18] * mm, "Отделение: " + Truncator(dir.doc.podrazdeleniye.title).chars(100))

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
            [Paragraph('Название', style), Paragraph(SettingManager.get("org_title"), styleTB)],
            [Paragraph('Телефон', style), Paragraph(SettingManager.get("org_phones"), styleTB)],
            [Paragraph('Факс', style), Paragraph(SettingManager.get("org_phones"), styleTB)],
            [Paragraph('E-mail', style), Paragraph(SettingManager.get("mail", default='', default_type='s'), styleTB)],
            [Paragraph('Адрес', style), Paragraph(SettingManager.get("org_address"), styleTB)],
            [Paragraph('Ф.И.О, должность лица, отправившего материал', style), Paragraph('', styleTB)],
            [Paragraph('E-mail', style), Paragraph('', styleTB)],
            [Paragraph('Цель исследования', style), Paragraph('Коронавирусная инфекция COVID-19 (2019-nCov)', styleTB)],
            [Paragraph('Указания для исследования', style), Paragraph(
                'Во исполнении письма Федеральной службы по надзору в сфере защиты прав потребителей и благополучия человека (Роспотребнадзора) '
                'от 09.01.2020 № 02/107-2020-27 "О дополнительных мерах по недопущению завозов инфекционных заболеваний"',
                styleTB)],
        ]
        tbl_o = Table(organization_data, colWidths=(60 * mm, 150 * mm,))
        tbl_o.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.3 * mm),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        organization_text = [tbl_o]
        organoztion_frame = Frame(10 * mm, 220 * mm, 190 * mm, 60 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
        organoztion_inframe = KeepInFrame(190 * mm, 60 * mm, organization_text, hAlign='CENTRE', vAlign='TOP', fakeWidth=False)
        organoztion_frame.addFromList([organoztion_inframe], c)

        c.drawCentredString((210 / 2) * mm, 219 * mm, "Севедения о заболевшем")
        issledovaniye = Issledovaniya.objects.get(napravleniye=dir.pk)
        localization = "" if not issledovaniye.localization else issledovaniye.localization.title
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
        tbl_o = Table(patient_data, colWidths=(105 * mm, 95 * mm,))
        tbl_o.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.3 * mm),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
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
        tbl_o = Table(material_data, colWidths=(105 * mm, 95 * mm,))
        tbl_o.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.3 * mm),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (0, 1), (0, 5))
        ]))
        material_text = [tbl_o]
        material_frame = Frame(10 * mm, 75 * mm, 190 * mm, 60 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
        material_inframe = KeepInFrame(190 * mm, 60 * mm, material_text, hAlign='CENTRE', vAlign='TOP', fakeWidth=False)
        material_frame.addFromList([material_inframe], c)

        c.drawCentredString((210 / 2) * mm, 74 * mm, "Севедения о проведенных исследованиях")
        result_data = [
            [Paragraph('Показатель', style), Paragraph('Результат', style)],
            [Paragraph('РНК вируса гриппа, респираторно-синициального вируса, метапневмовируса, вирусов парагриппа 1,2,3,3 типов, коронавируа, '
                       'риновируса, ДНК аденовирусов групп В, С и Е, бокавируса, ДНК Mycoplasma pneumonia и Chlamydophila pneumonia', styleBold), Paragraph('', styleTB)],
            [Paragraph('2019-nCov', style), Paragraph('', styleTB)],
        ]
        tbl_o = Table(result_data, colWidths=(105 * mm, 95 * mm,))
        tbl_o.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.3 * mm),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        result_text = [tbl_o]
        result_frame = Frame(10 * mm, 42 * mm, 190 * mm, 30 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
        result_inframe = KeepInFrame(190 * mm, 30 * mm, result_text, hAlign='CENTRE', vAlign='TOP', fakeWidth=False)
        result_frame.addFromList([result_inframe], c)

        c.drawCentredString((210 / 2) * mm, 37 * mm, "Севедения об отправке материала")
        result_data = [
            [Paragraph('Дата и время отправки материала (номер рейса)', style), Paragraph('', style)],
            [Paragraph('По адресу', style),
             Paragraph('ФБУЗ "Центр гигиены и эпидимиологии в Иркутской области" Отделение вирусологических исследований с ПЦР лабораторией и микробиологической лаборатории', styleTB)],
        ]
        tbl_o = Table(result_data, colWidths=(60 * mm, 150 * mm,))
        tbl_o.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.3 * mm),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        result_text = [tbl_o]
        result_frame = Frame(10 * mm, 10 * mm, 190 * mm, 25 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
        result_inframe = KeepInFrame(190 * mm, 25 * mm, result_text, hAlign='CENTRE', vAlign='TOP', fakeWidth=False)
        result_frame.addFromList([result_inframe], c)

    printForm()


def form_04(c: Canvas, dir: Napravleniya):
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
        objs.append(Paragraph(f'Карта: {dir.client.number_with_type()}', style))
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
        objs.append(Paragraph(f'Врач: {dir.doc.get_fio()} {space_symbol * 5} подпись _________', style))
        objs.append(Paragraph(f'Дата направления:  {strdate(dir.data_sozdaniya)}', style))

        gistology_frame = Frame(0 * mm, 0 * mm, 210 * mm, 297 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)
        gistology_inframe = KeepInFrame(210 * mm, 297 * mm, objs, hAlign='LEFT', vAlign='TOP', fakeWidth=False)
        gistology_frame.addFromList([gistology_inframe], c)

    printForm()
