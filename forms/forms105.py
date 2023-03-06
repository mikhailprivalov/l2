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
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
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
from directory.models import Researches
from hospitals.models import Hospitals
from laboratory import utils
from laboratory.settings import FONTS_FOLDER
from utils import tree_directions
from .forms_func import get_doc_results, get_finaldata_talon, primary_reception_get_data, hosp_extract_get_data, hosp_patient_movement, hosp_get_operation_data
from .forms_func import closed_bl
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
    doc_results = get_doc_results(doc_confirm, date_confirm)
    data_talon = get_finaldata_talon(doc_results)

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Symbola', os.path.join(FONTS_FOLDER, 'Symbola.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4), leftMargin=12 * mm, rightMargin=5 * mm, topMargin=25 * mm, bottomMargin=28 * mm, allowSplitting=1, title="Форма {}".format("Ведомость по статталонам")
    )

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
            [
                Paragraph('№ п.п.', styleT),
                Paragraph('ФИО пациента, дата рождени', styleT),
                Paragraph('Дата осмотра, &nbsp №', styleT),
                Paragraph('№ карты', styleT),
                Paragraph('Данные полиса', styleT),
                Paragraph('Код услуги', styleT),
                Paragraph('Наименование услуги', styleT),
            ]
        ]
    else:
        title = 'Ведомость статистических талонов по посещениям пациентов'
        opinion = [
            [
                Paragraph('№ п.п.', styleT),
                Paragraph('ФИО пациента, дата рождения ', styleT),
                Paragraph('Дата осмотра, &nbsp №', styleT),
                Paragraph('№ карты', styleT),
                Paragraph('Данные полиса', styleT),
                Paragraph('Цель посещения (код)', styleT),
                Paragraph('Первичный прием', styleT),
                Paragraph('Диагноз МКБ', styleT),
                Paragraph('Впервые', styleT),
                Paragraph('Результат обращения (код)', styleT),
                Paragraph('Исход (код)', styleT),
                Paragraph('Д-учет<br/>Стоит', styleT),
                Paragraph('Д-учет<br/>Взят', styleT),
                Paragraph('Д-учет<br/>Снят', styleT),
                Paragraph('Причина снятия', styleT),
                Paragraph('Онко<br/> подозрение', styleT),
            ]
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
            tbl = Table(
                t_opinion,
                colWidths=(
                    10 * mm,
                    60 * mm,
                    19 * mm,
                    15 * mm,
                    75 * mm,
                    30 * mm,
                    70 * mm,
                ),
            )
        else:
            tbl = Table(t_opinion, colWidths=(10 * mm, 30 * mm, 19 * mm, 15 * mm, 46 * mm, 20 * mm, 10 * mm, 13 * mm, 11 * mm, 20 * mm, 18 * mm, 16 * mm, 14 * mm, 14 * mm, 17 * mm, 13 * mm))

        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
                ]
            )
        )

        objs.append(tbl)
        new_page = True
        list_g = []

    styleTatr = deepcopy(style)
    styleTatr.alignment = TA_LEFT
    styleTatr.firstLineIndent = 0
    styleTatr.fontSize = 11

    opinion = [
        [Paragraph('ФИО врача:', styleTatr), Paragraph('{}'.format(doc_confirm.get_full_fio()), styleTatr), Paragraph('{}'.format(date_confirm.strftime('%d.%m.%Y')), styleTatr)],
        [Paragraph('Специальность:', styleTatr), Paragraph('{}'.format(doc_confirm.specialities), styleTatr), Paragraph('', styleTatr)],
    ]

    def later_pages(canvas, document):
        canvas.saveState()
        # вывести Название и данные врача
        width, height = landscape(A4)
        canvas.setFont('PTAstraSerifBold', 14)
        canvas.drawString(99 * mm, 200 * mm, '{}'.format(title))

        tbl = Table(opinion, colWidths=(35 * mm, 220 * mm, 25 * mm), rowHeights=(5 * mm))
        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
                ]
            )
        )
        tbl.wrapOn(canvas, width, height)
        tbl.drawOn(canvas, 30, 530)
        canvas.restoreState()

    doc.build(
        objs,
        onFirstPage=later_pages,
        onLaterPages=later_pages,
    )

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
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=6 * mm, allowSplitting=1, title="Форма {}".format("Статталон пациента")
    )
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
            Paragraph(
                '{}<font size=10>Карта № </font><font fontname="PTAstraSerifBold" size=10>{}</font><font size=10> из {}</font>'.format(3 * space_symbol, p_card_num, p_card_type), styleCenter
            ),
            Spacer(1, 2 * mm),
            Paragraph('<font size=11>Данные пациента:</font>', styleBold),
            Paragraph("1. Фамилия, имя, отчество:&nbsp;  <font size=11.7 fontname ='PTAstraSerifBold'> {} </font> ".format(patient_data['fio']), style),
            Paragraph('2. Пол: {} {} 3. Дата рождения: {}'.format(patient_data['sex'], 3 * space_symbol, patient_data['born']), style),
            Paragraph('4. Место регистрации: {}'.format(patient_data['main_address']), style),
            Paragraph(
                '5. Полис ОМС: серия {} №: {} {}' '6. СНИЛС: {}'.format(patient_data['oms']['polis_serial'], patient_data['oms']['polis_num'], 13 * space_symbol, patient_data['snils']),
                style,
            ),
            Paragraph('7. Наименование страховой медицинской организации: {}'.format(patient_data['oms']['polis_issued']), style),
        ]

        objs.extend(content_title)

        # добавить данные об услуге
        objs.append(Spacer(1, 3 * mm))
        objs.append(Paragraph('<font size=11>Данные об услуге:</font>', styleBold))
        objs.append(Spacer(1, 1 * mm))

        obj_iss = Issledovaniya.objects.filter(napravleniye=obj_dir, parent_id=None).first()
        date_proto = utils.strfdatetime(obj_iss.time_confirmation, "%d.%m.%Y")

        opinion = [
            [
                Paragraph('Основная услуга', styleT),
                Paragraph('<font fontname="PTAstraSerifBold">{}</font> <font face="Symbola">\u2013</font> {}'.format(obj_iss.research.code, obj_iss.research.title), styleT),
            ],
            [Paragraph('Направление №', styleT), Paragraph('{}'.format(dir), styleT)],
            [Paragraph('Дата протокола', styleT), Paragraph('{}'.format(date_proto), styleT)],
        ]

        # Найти и добавить поля у к-рых флаг "for_talon". Отсортировано по 'order' (группа, поле)
        field_iss = ParaclinicResult.objects.filter(issledovaniye=obj_iss, field__for_talon=True).order_by('field__group__order', 'field__order')

        for f in field_iss:
            v = f.value.replace("\n", "<br/>")
            field_type = f.get_field_type()
            if field_type == 1:
                vv = v.split('-')
                if len(vv) == 3:
                    v = "{}.{}.{}".format(vv[2], vv[1], vv[0])
            list_f = [[Paragraph(f.field.get_title(force_type=field_type), styleT), Paragraph(v, styleT)]]
            opinion.extend(list_f)

        tbl = Table(opinion, colWidths=(60 * mm, 123 * mm))
        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
                ]
            )
        )

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
        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
                ]
            )
        )
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
        objs.append(HRFlowable(width=185 * mm, thickness=0.7 * mm, spaceAfter=1.3 * mm, spaceBefore=0.5 * mm, color=colors.black, hAlign=TA_LEFT))
        objs.append(Paragraph('<font size=11>Лечащий врач:</font>', styleBold))
        objs.append(Spacer(1, 1 * mm))

        personal_code = ''
        doc_fio = ''
        if obj_iss.time_confirmation:
            personal_code = empty if not obj_iss.doc_confirmation or not obj_iss.doc_confirmation.personal_code else obj_iss.doc_confirmation.personal_code
            doc_fio = obj_iss.doc_confirmation_fio

        objs.append(Paragraph('{} /_____________________/ {} Код врача: {} '.format(doc_fio, 42 * space_symbol, personal_code), style))

        objs.append(Spacer(1, 5 * mm))

        # Получить структуру Направлений если, направление в Дереве неважно в корне в середине или в начале
        root_dir = tree_directions.root_direction(dir)
        num_iss = root_dir[-1][-2]
        tree_dir = tree_directions.tree_direction(num_iss)
        final_tree = {}
        pattern = re.compile('<font face=\"Symbola\" size=10>\u2713</font>')

        node_dir = Node("Структура направлений")
        for j in tree_dir:
            if not Researches.objects.get(pk=j[8]).is_hospital:
                continue
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
        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
                ]
            )
        )
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
    hosp_nums = f"- {hosp_nums_obj[0].get('direction')}"

    ind_card = direction_obj.client
    patient_data = ind_card.get_data_individual()

    hospital: Hospitals = request_data["hospital"]

    hospital_name = hospital.safe_short_title
    hospital_address = hospital.safe_address
    hospital_kod_ogrn = hospital.safe_ogrn

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=25 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=10 * mm, allowSplitting=1, title="Форма {}".format("066/у-02"))
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
        [
            Paragraph('<font size=11>{}<br/>Адрес: {}<br/>ОГРН: {} <br/><u>{}</u> </font>'.format(hospital_name, hospital_address, hospital_kod_ogrn, print_district), styleT),
            Paragraph('<font size=9 >Код формы по ОКУД:<br/>Код организации по ОКПО: 31348613<br/>' 'Медицинская документация<br/>форма № 066/у-02</font>', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [90 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (1, 0), (-1, -1), 80),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )

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

    ############################################################################################################
    # Получить данные из первичного приема (самого первого hosp-направления)
    hosp_first_num = hosp_nums_obj[0].get('direction')
    primary_reception_data = primary_reception_get_data(hosp_first_num)

    hospitalized = ''
    if primary_reception_data['what_time_hospitalized'] and primary_reception_data['plan_hospital']:
        if primary_reception_data['what_time_hospitalized'].lower().replace(' ', '') == 'впервые':
            hospitalized = "первично - 1"
        if primary_reception_data['what_time_hospitalized'].lower().replace(' ', '') == 'повторно':
            hospitalized = "повторно - 2"
        if primary_reception_data['plan_hospital'].lower().replace(' ', '') == 'да':
            hospitalized = f"{hospitalized}; в плановом порядке -4"
        if primary_reception_data['extra_hospital'].lower().replace(' ', '') == 'да':
            hospitalized = f"{hospitalized}; по экстренным показаниям - 3"

    # Получить отделение - из названия услуги или самого главного направления
    hosp_depart = hosp_nums_obj[0].get('research_title')

    # взять самое последнее направленеие из hosp_dirs
    hosp_last_num = hosp_nums_obj[-1].get('direction')
    # 'Время выписки', 'Дата выписки', 'Основной диагноз (описание)', 'Осложнение основного диагноза (описание)', 'Сопутствующий диагноз (описание)'
    date_value, time_value, outcome, result_hospital = '', '', '', ''
    hosp_extract_data = hosp_extract_get_data(hosp_last_num)
    days_count = '__________________________'
    doc_fio = ''
    manager_depart = ''
    if hosp_extract_data:
        if hosp_extract_data['result_hospital']:
            result_hospital = hosp_extract_data['result_hospital']
        if hosp_extract_data['outcome']:
            outcome = hosp_extract_data['outcome']
        if hosp_extract_data['date_value']:
            date_value = hosp_extract_data['date_value']
        if hosp_extract_data['time_value']:
            time_value = hosp_extract_data['time_value']
        days_count = hosp_extract_data['days_count']
        doc_fio = hosp_extract_data['doc_fio']
        manager_depart = hosp_extract_data['manager_depart']

    title_page = [
        Indenter(left=0 * mm),
        Spacer(1, 8 * mm),
        Paragraph(
            '<font fontname="PTAstraSerifBold" size=13>СТАТИСТИЧЕСКАЯ КАРТА ВЫБЫВШЕГО ИЗ СТАЦИОНАРА<br/> '
            'круглосуточного пребывания, дневного стационара при больничном<br/> учреждении, дневного стационара при'
            ' амбулаторно-поликлиническом<br/> учреждении, стационара на дому<br/>'
            'N медицинской карты {} {}</font>'.format(p_card_num, hosp_nums),
            styleCenter,
        ),
        Spacer(1, 2 * mm),
        Spacer(1, 2 * mm),
        Spacer(1, 2 * mm),
        Paragraph('1. Код пациента: ________  2. Ф.И.О.: {}'.format(patient_data['fio']), style),
        Paragraph('3. Пол: {} {}4. Дата рождения {}'.format(sex, space_symbol * 24, patient_data['born']), style),
        Paragraph('5. Документ, удостов. личность: (название, серия, номер) {} {}'.format(space_symbol * 2, doc_patient), style),
        Paragraph('6. Адрес: регистрация по месту жительства: {}'.format(patient_data['main_address']), style),
        Paragraph('7. Код территории проживания: ___ Житель: город - 1; село - 2.', style),
        Paragraph('8. Страховой полис (серия, номер):{}'.format(polis_data), style),
        Paragraph('Выдан: {}'.format(patient_data['oms']['polis_issued']), style),
        Paragraph('9. Вид оплаты:______________', style),
        Paragraph('10. Социальный статус: {}'.format(primary_reception_data['social_status']), style),
        Paragraph('11. Категория льготности: {}'.format(primary_reception_data['category_privilege']), style),
        Paragraph('12. Кем направлен больной: {}'.format(primary_reception_data['who_directed']), style),
        Paragraph('13. Кем доставлен: _________________________________ Код______ Номер наряда__________', style),
        Paragraph('14. Диагноз направившего учреждения: {}'.format(primary_reception_data['diagnos_who_directed']), style),
        Paragraph('14.1 Состояние при поступлении: {}'.format(primary_reception_data['state']), style),
        Paragraph('15. Диагноз приемного отделения:{}'.format(primary_reception_data['diagnos_entered']), style),
        Paragraph('16. Доставлен в состоянии опьянения: Алкогольного — 1; Наркотического — 2.', style),
        Paragraph('17. Госпитализирован по поводу данного заболевания в текущем году: {}'.format(hospitalized), style),
        Paragraph('18.Доставлен в стационар от начала заболевания(получения травмы): {}'.format(primary_reception_data['time_start_ill']), style),
        Paragraph('19. Травма: {}'.format(primary_reception_data['type_trauma']), style),
        Paragraph('20. Дата поступления в приемное отделение:______________ Время__________', style),
        Paragraph(
            '21. Название отделения: <u>{}</u>; дата поступления: <u>{}</u>; время: <u>{}</u>'.format(
                hosp_depart, primary_reception_data['date_entered_value'], primary_reception_data['time_entered_value']
            ),
            style,
        ),
        Paragraph('Подпись врача приемного отделения ______________ Код __________', style),
        Paragraph('22. Дата выписки (смерти): {}; Время {}'.format(date_value, time_value), style),
        Paragraph('23. Продолжительность госпитализации (койко - дней): {}'.format(days_count), style),
        Paragraph('24. Исход госпитализации: {}'.format(outcome), style),
        Paragraph('24.1. Результат госпитализации: {}'.format(result_hospital), style),
    ]

    closed_bl_result = closed_bl(hosp_nums_obj[0].get('direction'))
    title_page.append(
        Paragraph(
            f"25. Листок нетрудоспособности: открыт <u>{closed_bl_result['start_date']}</u> закрыт: <u>{closed_bl_result['end_date']}</u>"
            f" к труду: <u>{closed_bl_result['start_work']}</u>",
            style,
        )
    )
    title_page.append(Paragraph(f"25.1. Номере ЛН : <u>{closed_bl_result['num']}</u>", style))
    title_page.append(Paragraph(f"25.2. Выдан кому : {closed_bl_result['who_get']}", style))
    title_page.append(Paragraph('25.3. По уходу за больным Полных лет: _____ Пол: {}'.format(sex), style))
    title_page.append(Paragraph('26. Движение пациента по отделениям:', style))

    objs.extend(title_page)

    styleTB = deepcopy(style)
    styleTB.fontSize = 8.7
    styleTB.alignment = TA_CENTER
    styleTB.leading = 3.5 * mm

    styleTC = deepcopy(style)
    styleTC.fontSize = 9.5
    styleTC.alignment = TA_LEFT

    styleTCright = deepcopy(styleTC)
    styleTCright.alignment = TA_RIGHT

    styleTCcenter = deepcopy(styleTC)
    styleTCcenter.alignment = TA_CENTER

    opinion = [
        [
            Paragraph('N', styleTB),
            Paragraph('Код отделения', styleTB),
            Paragraph('Профиль коек', styleTB),
            Paragraph('Код врача', styleTB),
            Paragraph('Дата поступления', styleTB),
            Paragraph('Дата выписки, перевода', styleTB),
            Paragraph('Код диагноза по МКБ', styleTB),
            Paragraph('Код медицинского стандарта', styleTB),
            Paragraph('Код прерванного случая', styleTB),
            Paragraph('Вид оплаты', styleTB),
        ]
    ]

    patient_movement = hosp_patient_movement(hosp_nums_obj)
    x = 0
    for i in patient_movement:
        x += 1
        doc_code = ''
        if i['doc_confirm_code']:
            doc_code = str(i['doc_confirm_code'])
        tmp_data = [
            [
                Paragraph(str(x), styleTB),
                Paragraph('', styleTB),
                Paragraph(i['bed_profile_research_title'], styleTB),
                Paragraph(doc_code, styleTB),
                Paragraph(i['date_entered_value'], styleTB),
                Paragraph(i['date_oute'], styleTB),
                Paragraph(i['diagnos_mkb'], styleTB),
                Paragraph('', styleTB),
                Paragraph('', styleTB),
                Paragraph('ОМС', styleTB),
            ],
        ]

        opinion.extend(tmp_data.copy())

    # получить структуру данных для таблицы
    tbl_act = Table(opinion, repeatRows=1, colWidths=(7 * mm, 15 * mm, 30 * mm, 20 * mm, 21 * mm, 21 * mm, 20 * mm, 14 * mm, 14 * mm, 20 * mm))

    tbl_act.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
    )
    objs.append(tbl_act)
    objs.append(Spacer(1, 2 * mm))
    objs.append(
        Paragraph('27. Хирургические операции(обозначить: основную операцию, использование спец.аппаратуры):', style),
    )

    opinion = [
        [
            Paragraph('Дата, Час', styleTB),
            Paragraph('Код <br/>хирурга', styleTB),
            Paragraph('Код отделения', styleTB),
            Paragraph('наименование операции', styleTB),
            Paragraph('код операции', styleTB),
            Paragraph('наименование осложнения', styleTB),
            Paragraph('Код ослонения', styleTB),
            Paragraph('Анестезия (код врача)', styleTB),
            Paragraph('энд.', styleTB),
            Paragraph('лазер.', styleTB),
            Paragraph('криог.', styleTB),
            Paragraph('Вид оплаты', styleTB),
        ]
    ]

    patient_operation = hosp_get_operation_data(num_dir)
    operation_result = []
    for i in patient_operation:
        operation_template = [''] * 12
        operation_template[0] = Paragraph(i['date'] + '<br/>' + i['time_start'] + '-' + i['time_end'], styleTB)
        operation_template[1] = Paragraph(str(i['doc_code']), styleTB)
        operation_template[3] = Paragraph(f"{i['name_operation']} <br/><font face=\"PTAstraSerifBold\" size=\"8.7\">({i['category_difficult']})</font>", styleTB)
        operation_template[4] = Paragraph('{}'.format(i['code_operation'] + '<br/>' + i['plan_operation']), styleTB)
        operation_template[7] = Paragraph('{}'.format(i['anesthesia method'] + '<br/> (' + i['code_doc_anesthesia'] + ')'), styleTB)
        operation_template[5] = Paragraph(i['complications'], styleTB)
        operation_template[11] = Paragraph(" ОМС", styleTB)
        operation_result.append(operation_template.copy())

    opinion.extend(operation_result)
    tbl_act = Table(opinion, repeatRows=1, colWidths=(22 * mm, 12 * mm, 11 * mm, 26 * mm, 26 * mm, 20 * mm, 10 * mm, 15 * mm, 7 * mm, 7 * mm, 7 * mm, 16 * mm))
    tbl_act.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
    )
    objs.append(tbl_act)
    objs.append(Spacer(1, 2 * mm))
    space_symbol = '&nbsp;'

    objs.append(
        Paragraph('28. Обследован: RW {}  AIDS '.format(space_symbol * 10), style),
    )
    objs.append(Spacer(1, 2 * mm))
    objs.append(
        Paragraph('29. Диагноз стационара(при выписке):', style),
    )

    opinion = [
        [
            Paragraph('Клинический заключительный', styleTB),
            Paragraph('Основное заболевание', styleTB),
            Paragraph('Код МКБ', styleTB),
            Paragraph('Осложнение', styleTB),
            Paragraph('Код МКБ', styleTB),
            Paragraph('Сопутствующее заболевание', styleTB),
            Paragraph('Код МКБ', styleTB),
        ]
    ]

    hosp_last_num = hosp_nums_obj[-1].get('direction')
    hosp_extract_data = hosp_extract_get_data(hosp_last_num)

    opinion_diagnos = []
    if hosp_extract_data:
        opinion_diagnos = [
            [
                Paragraph('', styleTB),
                Paragraph(hosp_extract_data['final_diagnos'], styleTB),
                Paragraph(hosp_extract_data['final_diagnos_mkb'], styleTB),
                Paragraph(hosp_extract_data['other_diagnos'], styleTB),
                Paragraph(hosp_extract_data['other_diagnos_mkb'], styleTB),
                Paragraph(hosp_extract_data['near_diagnos'].replace('<', '&lt;').replace('>', '&gt;'), styleTB),
                Paragraph(hosp_extract_data['near_diagnos_mkb'], styleTB),
            ]
        ]

    opinion.extend(opinion_diagnos)
    opinion_pathologist = [
        [
            Paragraph('Патологоанатомический	', styleTB),
            Paragraph('', styleTB),
            Paragraph('', styleTB),
            Paragraph('', styleTB),
            Paragraph('', styleTB),
            Paragraph('', styleTB),
            Paragraph('', styleTB),
        ]
    ]

    opinion.extend(opinion_pathologist)
    tbl_act = Table(opinion, repeatRows=1, colWidths=(28 * mm, 45 * mm, 15 * mm, 30 * mm, 15 * mm, 30 * mm, 15 * mm))
    tbl_act.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('SPAN', (0, 0), (0, 1)),
            ]
        )
    )

    objs.append(tbl_act)
    objs.append(Spacer(1, 2 * mm))
    objs.append(
        Paragraph('30.В случае смерти указать основную причину:______________________________________________________________' 'Код МКБ', style),
    )
    objs.append(Spacer(1, 20 * mm))
    objs.append(
        Paragraph(
            '31. Дефекты догоспитального этапа: несвоевременность госпитализации - 1; недостаточный объем клинико - диагностического обследования - 2; '
            'неправильная тактика лечения - 3; несовпадение диагноза - 4.',
            style,
        ),
    )
    objs.append(Spacer(1, 7 * mm))
    objs.append(
        Paragraph('Подпись лечащего врача ({}) ____________________________'.format(doc_fio), style),
    )
    objs.append(Spacer(1, 7 * mm))
    objs.append(
        Paragraph(f'Подпись заведующего отделением ({manager_depart}) ____________________________', style),
    )

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
