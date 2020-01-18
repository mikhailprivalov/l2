import datetime
import locale
import os.path
import re
import sys
from copy import deepcopy
from io import BytesIO

import simplejson as json
from anytree import Node, RenderTree
from reportlab.lib import colors
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, portrait, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Indenter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable

from appconf.manager import SettingManager
from directions.models import Issledovaniya, Napravleniya, ParaclinicResult
from laboratory import utils
from laboratory.settings import FONTS_FOLDER
from utils import tree_directions
from . import forms_func
from api.stationar.stationar_func import hosp_get_hosp_direction


def form_01(request_data):
    """
    Ведомость статталонов по амбулаторным приемам. Входные параметры врач, дата.
    Выходные: форма
    """

    doc_confirm = request_data['user'].doctorprofile
    req_date = request_data['date']
    str_date = json.loads(req_date)
    date_confirm = datetime.datetime.strptime(str_date, "%d.%m.%Y")
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
            [Paragraph('№ п.п.', styleT), Paragraph('ФИО пациента, дата рождени', styleT),
             Paragraph('Дата осмотра, &nbsp №', styleT),
             Paragraph('№ карты', styleT), Paragraph('Данные полиса', styleT),
             Paragraph('Код услуги', styleT),
             Paragraph('Наименование услуги', styleT), ]
        ]
    else:
        title = 'Ведомость статистических талонов по посещениям пациентов'
        opinion = [
            [Paragraph('№ п.п.', styleT), Paragraph('ФИО пациента, дата рождения ', styleT), Paragraph('Дата осмотра, &nbsp №', styleT),
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
                list_t.append(Paragraph(str(q).replace("\n", "<br/>"), styleT))
            list_g.append(list_t)
        t_opinion.extend(list_g)

        if param:
            tbl = Table(t_opinion,
                        colWidths=(10 * mm, 60 * mm, 19 * mm, 15 * mm, 75 * mm, 30 * mm, 70 * mm,))
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


################################################################################################################
def form_02(request_data):
    """
    Отдельный статталон по отдельному амбулаторному приему.
    Краткая форма - результата проткола. Учитываются те поля, к-рые имеют признак "для статталона"
    -------------------------------
    Вход: Направление.
    Выходные: форма

    в файле .....\Lib\site-packages\anytree\render.py
        class ContStyle(AbstractStyle):
        необходимое мотод super сделать так:(изменить символы)
                super(ContStyle, self).__init__(u'\u2063   ',
                                        u'\u2063   ',
                                        u'\u2063   ')
    """

    # получить направления
    ind_dir = json.loads(request_data["napr_id"])

    hospital_name = SettingManager.get("org_title")
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

        # Добавить сведения о пациента
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

        # добавить данные об услуге
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
            v = f.value.replace("\n", "<br/>")
            if f.field.field_type == 1:
                vv = v.split('-')
                if len(vv) == 3:
                    v = "{}.{}.{}".format(vv[2], vv[1], vv[0])
            list_f = [[Paragraph(f.field.get_title(), styleT), Paragraph(v, styleT)]]
            opinion.extend(list_f)

        tbl = Table(opinion, colWidths=(60 * mm, 123 * mm))
        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
        ]))

        objs.append(tbl)

        # Заключительные положения
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

        personal_code = ''
        doc_fio = ''
        if obj_iss.doc_confirmation:
            personal_code = empty if not obj_iss.doc_confirmation.personal_code else obj_iss.doc_confirmation.personal_code
            doc_fio = obj_iss.doc_confirmation.get_fio()

        objs.append(Paragraph('{} /_____________________/ {} Код врача: {} '.format(doc_fio,
                                                                                    42 * space_symbol, personal_code), style))

        objs.append(Spacer(1, 5 * mm))

        # Получить структуру Направлений если, направление в Дереве не важно в корне в середине или в начале
        root_dir = tree_directions.root_direction(dir)
        num_iss = (root_dir[-1][-2])
        tree_dir = tree_directions.tree_direction(num_iss)
        final_tree = {}
        pattern = re.compile('<font face=\"Symbola\" size=10>\u2713</font>')

        node_dir = Node("Структура направлений")
        for j in tree_dir:
            if len(j[9]) > 47:
                research = j[9][:47] + '...'
            else:
                research = j[9]
            diagnos = '  --' + j[-2] if j[-2] else ""
            temp_s = f"{j[0]} - {research}. Создано {j[1]} в {j[2]} {diagnos}"
            if dir == j[0]:
                temp_s = f"{temp_s} -- <font face=\"Symbola\" size=10>\u2713</font>"
            if not j[3]:
                final_tree[j[5]] = Node(temp_s, parent=node_dir)
            else:
                final_tree[j[5]] = Node(temp_s, parent=final_tree.get(j[3]))

        counter = 0
        opinion = []
        for row in RenderTree(node_dir):
            counter += 1
            result = pattern.search(row.node.name)
            current_style = styleBold if result else styleT
            count_space = len(row.pre) // 2 * 2
            para = [Paragraph('{}{}'.format(space_symbol * count_space, row.node.name), current_style)]
            opinion.append(para)

        tbl = Table(opinion, colWidths=(190 * mm))
        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
        ]))
        objs.append(tbl)

        objs.append(PageBreak())

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


##########################################################################################################################

def form_03(request_data):
    """
    Статистическая форма 066/у Приложение № 5 к приказу Минздрава России от 30 декабря 2002 г. № 413
    """
    num_dir = request_data["dir_pk"]
    direction_obj = Napravleniya.objects.get(pk=num_dir)
    hosp_nums_obj = hosp_get_hosp_direction(num_dir)
    hosp_nums = ''
    for i in hosp_nums_obj:
        hosp_nums = hosp_nums + ' - ' + str(i.get('direction'))

    ind_card = direction_obj.client
    patient_data = ind_card.get_data_individual()

    hospital_name = SettingManager.get("org_title")
    hospital_address = SettingManager.get("org_address")
    hospital_kod_ogrn = SettingManager.get("org_ogrn")

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=25 * mm,
                            rightMargin=5 * mm, topMargin=6 * mm,
                            bottomMargin=4 * mm, allowSplitting=1,
                            title="Форма {}".format("003/у"))
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.leading = 15
    style.spaceAfter = 0.5 * mm
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 12
    styleCenter.leading = 15
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

    print_district = ''
    if SettingManager.get("district", default='True', default_type='b'):
        if ind_card.district is not None:
            print_district = 'Уч: {}'.format(ind_card.district.title)

    opinion = [
        [Paragraph('<font size=11>{}<br/>Адрес: {}<br/>ОГРН: {} <br/><u>{}</u> </font>'.format(
            hospital_name, hospital_address, hospital_kod_ogrn, print_district), styleT),
            Paragraph('<font size=9 >Код формы по ОКУД:<br/>Код организации по ОКПО: 31348613<br/>'
                      'Медицинская документация<br/>форма № 003/у</font>', styleT)],
    ]

    tbl = Table(opinion, 2 * [90 * mm])
    tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
        ('LEFTPADDING', (1, 0), (-1, -1), 80),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    objs.append(tbl)
    space_symbol = '&nbsp;'
    if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i'):
        patient_data['serial'] = patient_data['bc_serial']
        patient_data['num'] = patient_data['bc_num']
    else:
        patient_data['serial'] = patient_data['passport_serial']
        patient_data['num'] = patient_data['passport_num']

    card_num_obj = patient_data['card_num'].split(' ')
    p_card_num = card_num_obj[0]

    sex = patient_data['sex']
    if sex == 'м':
        sex = f'{sex} - 1'
    if sex == 'ж':
        sex = f'{sex} - 2'

    doc_patient = f"{patient_data['type_doc']}, {patient_data['serial']} - {patient_data['num']}"
    polis_data = f"{patient_data['oms']['polis_serial']} {patient_data['oms']['polis_num']}"

    title_page = [
        Indenter(left=0 * mm),
        Spacer(1, 8 * mm),
        Paragraph(
            '<font fontname="PTAstraSerifBold" size=13>СТАТИСТИЧЕСКАЯ КАРТА ВЫБЫВШЕГО ИЗ СТАЦИОНАРА<br/> '
            'круглосуточного пребывания, дневного стационара при больничном<br/> учреждении, дневного стационара при'
            ' амбулаторно-поликлиническом<br/> учреждении, стационара на дому<br/>'
            'N медицинской карты {} {}</font>'.format(p_card_num, hosp_nums), styleCenter),
        Spacer(1, 2 * mm),
        Spacer(1, 2 * mm),
        Spacer(1, 2 * mm),

        Paragraph('1. Код пациента: ________  2. Ф.И.О.: {}'.format(patient_data['fio']), style),
        Paragraph('3. Пол: {} {}4. Дата рождения'.format(sex, space_symbol * 24, patient_data['born']), style),
        Paragraph('5. Документ, удостов. личность: (название, серия, номер) {} {}'.
                  format(space_symbol * 2, doc_patient), style),
        Paragraph('6. Адрес: регистрация по месту жительства: {}'.format(patient_data['main_address']), style),
        Paragraph('7. Код территории проживания: ___ Житель: город - 1; село - 2.', style),
        Paragraph('8. Страховой полис (серия, номер):{}'.format(polis_data), style),
        Paragraph('Выдан: {}'.format(patient_data['oms']['polis_issued']), style),
        Paragraph('9. Вид оплаты:______________', style),
        Paragraph('10. Социальный статус:    дошкольник -  1:    организован -  2;    неорганизован -  3; '
                  'учащийся  -  4;    работает  - 5;    не  работает  - 6;   БОМЖ  - 7;   пенсионер  - 8; '
                  'военнослужащий - 9; Код _______; Член семьи военнослужащего - 10.', style),
        Paragraph('11. Категория льготности: инвалид  ВОВ - 1;  участник ВОВ - 2; воин - интернационалист- 3;  '
                  'лицо,  подвергшееся  радиационному  облучению  - 4;  в  т.ч.  в  Чернобыле  - 5;'
                  'инв. I гр.  - 6;   инв. II гр.  -  7;   инв. III гр.  -  8;   ребенок - инвалид  -  9;'
                  'инвалид с детства - 10; прочие - 11', style),
    ]
    objs.extend(title_page)

    def first_pages(canvas, document):
        canvas.saveState()
        canvas.restoreState()

    def later_pages(canvas, document):
        canvas.saveState()
        canvas.restoreState()

    doc.build(objs, onFirstPage=first_pages, onLaterPages=later_pages)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf
