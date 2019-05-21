from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, portrait, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import PageBreak, Indenter
from reportlab.platypus.flowables import HRFlowable

from copy import deepcopy
import os.path
import locale
import sys
from io import BytesIO
from . import forms_func
from laboratory.settings import FONTS_FOLDER
from datetime import *
import datetime
import simplejson as json
from appconf.manager import SettingManager
from directions.models import Issledovaniya, Result, Napravleniya, IstochnikiFinansirovaniya, ParaclinicResult
from laboratory import utils


def form_01(request_data):
    """
    Ведомость статталонов по амбулаторным приемам. Входные параметры врач, дата.
    Выходные: форма
    """

    doc_confirm = request_data['user'].doctorprofile
    str_date = request_data['date']
    date_confirm = datetime.datetime.strptime(str_date, "%d%m%Y")
    doc_results = forms_func.get_doc_results(doc_confirm, date_confirm)
    data_talon = forms_func.get_finaldata_talon(doc_results)

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Symbola', os.path.join(FONTS_FOLDER, 'Symbola.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=12 * mm,
                            rightMargin=5 * mm, topMargin=25 * mm,
                            bottomMargin=28 * mm, allowSplitting=1,
                            title="Форма {}".format("Ведомость по статталонам"))

    styleSheet = getSampleStyleSheet()
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 9
    style.leading = 12
    style.spaceAfter = 0 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = 15

    styleFL = deepcopy(style)
    styleFL.firstLineIndent = 0

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleBold.fontSize = 11
    styleBold.alignment = TA_LEFT
    styleBold.firstLineIndent = 0

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 9
    styleCenter.leading = 10
    styleCenter.spaceAfter = 0 * mm

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 14
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'

    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    objs = []
    objs.append(Spacer(1, 1 * mm))

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.firstLineIndent = 0
    styleT.fontSize = 9
    param = request_data.get('param', '0') == '1'

    if param:
        title = 'Ведомость статистических талонов по услугам пациентов'
        opinion = [
            [Paragraph('№ п.п.', styleT), Paragraph('ФИО пациента, &nbsp № направления', styleT),
             Paragraph('Дата рождения', styleT),
             Paragraph('№ карты', styleT), Paragraph('Данные полиса', styleT),
             Paragraph('Код услуги', styleT),
             Paragraph('Наименование услуги', styleT), ]
        ]
    else:
        title = 'Ведомость статистических талонов по посещениям пациентов'
        opinion = [
            [Paragraph('№ п.п.', styleT), Paragraph('ФИО пациента, &nbsp № направления', styleT), Paragraph('Дата рождения', styleT),
             Paragraph('№ карты', styleT), Paragraph('Данные полиса', styleT), Paragraph('Цель посещения (код)', styleT),
             Paragraph('Первичный прием', styleT), Paragraph('Диагноз МКБ', styleT), Paragraph('Впервые', styleT),
             Paragraph('Результат обращения (код)', styleT), Paragraph('Исход (код)', styleT),
             Paragraph('Д-учет<br/>Стоит', styleT),
             Paragraph('Д-учет<br/>Взят', styleT), Paragraph('Д-учет<br/>Снят', styleT),
             Paragraph('Причина снятия', styleT),
             Paragraph('Онко<br/> подозрение', styleT), ]
        ]

    new_page = False
    list_g = []

    if param:
        talon = data_talon[1]
    else:
        talon = data_talon[0]

    for k, v in talon.items():
        if len(talon.get(k)) == 0:
            continue
        if new_page:
            objs.append(PageBreak())
        objs.append(Paragraph('Источник финансирования - {}'.format(str(k).upper()), styleBold))
        objs.append(Spacer(1, 1.5 * mm))
        t_opinion = opinion.copy()
        for u, s in v.items():
            list_t = [Paragraph(str(u), styleT)]
            for t, q in s.items():
                list_t.append(Paragraph(str(q), styleT))
            list_g.append(list_t)
        t_opinion.extend(list_g)

        if param:
            tbl = Table(t_opinion,
                        colWidths=(10 * mm, 60 * mm, 19 * mm, 15 * mm, 75 * mm, 30 * mm, 70 * mm, ))
        else:
            tbl = Table(t_opinion,
                        colWidths=(10 * mm, 30 * mm, 19 * mm, 15 * mm, 46 * mm, 20 * mm, 10 * mm, 13 * mm, 11 * mm,
                               20 * mm, 20 * mm, 14 * mm, 14 * mm, 14 * mm, 17 * mm, 13 * mm))

        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
        ]))

        objs.append(tbl)
        new_page = True
        list_g = []

    styleTatr = deepcopy(style)
    styleTatr.alignment = TA_LEFT
    styleTatr.firstLineIndent = 0
    styleTatr.fontSize = 11

    opinion = [
        [Paragraph('ФИО врача:', styleTatr), Paragraph('{}'.format(doc_confirm.fio), styleTatr),
         Paragraph('{}'.format(date_confirm.strftime('%d.%m.%Y')), styleTatr)],
        [Paragraph('Специальность:', styleTatr), Paragraph('{}'.format(doc_confirm.specialities), styleTatr),
         Paragraph('', styleTatr)],
    ]

    def later_pages(canvas, document):
        canvas.saveState()
        # вывести Название и данные врача
        width, height = landscape(A4)
        canvas.setFont('PTAstraSerifBold', 14)
        canvas.drawString(99 * mm, 200 * mm, '{}'.format(title))

        tbl = Table(opinion, colWidths=(35 * mm, 220 * mm, 25 * mm), rowHeights=(5 * mm))
        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
        ]))
        tbl.wrapOn(canvas, width, height)
        tbl.drawOn(canvas, 30, 530)

        canvas.restoreState()

    doc.build(objs, onFirstPage=later_pages, onLaterPages=later_pages, )

    pdf = buffer.getvalue()

    buffer.close()
    return pdf


def form_02(request_data):
    """
    Отдельный статталон по отдельному амбулаторному приему.
    Краткая форма - результата проткола. Учитываются те поля, к-рые имеют признак "для статталона"
    -------------------------------
    Вход: Направление.
    Выходные: форма
    """

    #получить направления
    ind_dir = json.loads(request_data["napr_id"])

    hospital_name = SettingManager.get("rmis_orgname")
    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Symbola', os.path.join(FONTS_FOLDER, 'Symbola.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=18 * mm,
                            rightMargin=5 * mm, topMargin=6 * mm,
                            bottomMargin=6 * mm, allowSplitting=1,
                            title="Форма {}".format("Статталон пациента"))
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10
    style.leading = 12
    style.spaceAfter = 0.5 * mm

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 12
    styleCenter.leading = 10
    styleCenter.spaceAfter = 1 * mm

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'
    styleCenterBold.borderColor = black

    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    objs = []

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm
    styleT.face = 'PTAstraSerifReg'

    for dir in ind_dir:
        obj_dir = Napravleniya.objects.get(pk=dir)
        ind_card = obj_dir.client
        patient_data = ind_card.get_data_individual()

        if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i'):
            patient_data['serial'] = patient_data['bc_serial']
            patient_data['num'] = patient_data['bc_num']
        else:
            patient_data['serial'] = patient_data['passport_serial']
            patient_data['num'] = patient_data['passport_num']

        card_num_obj = patient_data['card_num'].split(' ')
        p_card_num = card_num_obj[0]
        if len(card_num_obj) == 2:
            p_card_type = '(' + str(card_num_obj[1]) + ')'
        else:
            p_card_type = ''

        space_symbol = '&nbsp;'

        #Добавить сведения о пациента
        content_title = [
            Indenter(left=0 * mm),
            Spacer(1, 1 * mm),
            Paragraph('{}'.format(hospital_name), styleCenterBold),
            Spacer(1, 2 * mm),
            Paragraph('<u>Статистический талон пациента</u>', styleCenter),
            Paragraph('{}<font size=10>Карта № </font><font fontname="PTAstraSerifBold" size=10>{}</font><font size=10> из {}</font>'.format(
                    3 * space_symbol, p_card_num, p_card_type), styleCenter),
            Spacer(1, 2 * mm),
            Paragraph('<font size=11>Данные пациента:</font>', styleBold),
            Paragraph("1. Фамилия, имя, отчество:&nbsp;  <font size=11.7 fontname ='PTAstraSerifBold'> {} </font> ".format(
                patient_data['fio']), style),
            Paragraph(
                '2. Пол: {} {} 3. Дата рождения: {}'.format(patient_data['sex'], 3 * space_symbol, patient_data['born']),
                style),
            Paragraph('4. Место регистрации: {}'.format(patient_data['main_address']), style),
            Paragraph('5. Полис ОМС: серия {} №: {} {}'
                      '6. СНИЛС: {}'.format(patient_data['oms']['polis_serial'], patient_data['oms']['polis_num'],
                                            13 * space_symbol, patient_data['snils']), style),
            Paragraph('7. Наименование страховой медицинской организации: {}'.format(patient_data['oms']['polis_issued']),
                      style),
        ]

        objs.extend(content_title)

        #добавить данные об услуге
        objs.append(Spacer(1, 3 * mm))
        objs.append(Paragraph('<font size=11>Данные об услуге:</font>', styleBold))
        objs.append(Spacer(1, 1 * mm))

        obj_iss = Issledovaniya.objects.filter(napravleniye=obj_dir, parent_id=None).first()
        date_proto = utils.strfdatetime(obj_iss.time_confirmation, "%d.%m.%Y")

        opinion = [
            [Paragraph('Основная услуга', styleT), Paragraph(
                '<font fontname="PTAstraSerifBold">{}</font> <font face="Symbola">\u2013</font> {}'.format(
                    obj_iss.research.code, obj_iss.research.title), styleT)],
            [Paragraph('Направление №', styleT), Paragraph('{}'.format(dir), styleT)],
            [Paragraph('Дата протокола', styleT), Paragraph('{}'.format(date_proto), styleT)],
        ]

        # Найти и добавить поля у к-рых флаг "for_talon". Отсортировано по 'order' (группа, поле)
        field_iss = ParaclinicResult.objects.filter(issledovaniye=obj_iss, field__for_talon=True, ).order_by(
            'field__group__order', 'field__order')

        for f in field_iss:
            list_f =[[Paragraph(f.field.title, styleT), Paragraph(f.value, styleT)]]
            opinion.extend(list_f)

        tbl = Table(opinion, colWidths=(60 * mm, 123* mm))
        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
        ]))

        objs.append(tbl)

        #Заключительные положения
        objs.append(Spacer(1, 4 * mm))
        objs.append(Paragraph('<font size=11>Заключительные положения:</font>', styleBold))
        objs.append(Spacer(1, 1 * mm))
        empty = '-'
        purpose = empty if not obj_iss.purpose else obj_iss.purpose
        outcome_illness = empty if not obj_iss.outcome_illness else obj_iss.outcome_illness
        result_reception = empty if not obj_iss.result_reception else obj_iss.result_reception
        diagnos = empty if not obj_iss.diagnos else obj_iss.diagnos

        opinion = [
            [Paragraph('Цель посещения', styleT), Paragraph('{}'.format(purpose), styleT)],
            [Paragraph('Исход заболевания', styleT), Paragraph('{}'.format(outcome_illness), styleT)],
            [Paragraph('Результат обращения', styleT), Paragraph('{}'.format(result_reception), styleT)],
            [Paragraph('Основной диагноз', styleT), Paragraph('{}'.format(diagnos), styleT)],
        ]

        tbl = Table(opinion, colWidths=(60 * mm, 123 * mm))
        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
        ]))
        objs.append(tbl)

       # Добавить Дополнительные услуги
        add_research = Issledovaniya.objects.filter(parent_id__napravleniye=obj_dir)
        if add_research:
            objs.append(Spacer(1, 3 * mm))
            objs.append(Paragraph('<font size=11>Дополнительные услуги:</font>', styleBold))
            objs.append(Spacer(1, 1 * mm))
            for i in add_research:
                objs.append(Paragraph('{} <font face="Symbola">\u2013</font> {}'.format(i.research.code, i.research.title), style))

        objs.append(Spacer(1, 5 * mm))
        objs.append(
            HRFlowable(width=185 * mm, thickness=0.7 * mm, spaceAfter=1.3 * mm, spaceBefore=0.5 * mm, color=colors.black, hAlign=TA_LEFT))
        objs.append(Paragraph('<font size=11>Лечащий врач:</font>', styleBold))
        objs.append(Spacer(1, 1 * mm))

        personal_code = empty if not obj_iss.doc_confirmation.personal_code else obj_iss.doc_confirmation.personal_code
        objs.append(Paragraph('{} /_____________________/ {} Код врача: {} '. format(obj_iss.doc_confirmation.get_fio(),
             42 * space_symbol, personal_code),style))
        objs.append(PageBreak())


    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf