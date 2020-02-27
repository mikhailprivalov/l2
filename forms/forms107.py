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
from laboratory import utils
from laboratory.settings import FONTS_FOLDER
from utils import tree_directions
from .forms_func import get_doc_results, get_finaldata_talon, primary_reception_get_data, hosp_extract_get_data, hosp_patient_movement, hosp_get_operation_data
from api.stationar.stationar_func import hosp_get_hosp_direction


def form_01(request_data):
    """
    Температурный лист (АД, Пульс)
    """
    num_dir = request_data["dir_pk"]
    direction_obj = Napravleniya.objects.get(pk=num_dir)
    hosp_nums_obj = hosp_get_hosp_direction(num_dir)

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
                            bottomMargin=10 * mm, allowSplitting=1,
                            title="Форма {}".format("066/у-02"))
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
                      'Медицинская документация<br/>форма № 066/у-02</font>', styleT)],
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

    ############################################################################################################
    # Получить данные из первичного приема (самого первого hosp-направления)
    hosp_first_num = hosp_nums_obj[0].get('direction')
    primary_reception_data = primary_reception_get_data(hosp_first_num)

    hospitalized = 'первично — 1; повторно — 2; по экстренным показаниям — 3; в плановом порядке — 4.'
    if primary_reception_data['what_time_hospitalized'] and primary_reception_data['plan_hospital']:
        if primary_reception_data['what_time_hospitalized'] == 'впервые':
            hospitalized = "первично - 1"
        if primary_reception_data['what_time_hospitalized'] == 'повторно':
            hospitalized = "повторно - 2"
        if primary_reception_data['plan_hospital'] == 'Да':
            hospitalized = f"{hospitalized}; в плановом порядке -4"
        if primary_reception_data['extra_hospital'] == 'Да':
            hospitalized = f"{hospitalized}; по экстренным показаниям - 3"

    # Получить отделение - из названия услуги или самого главного направления
    hosp_depart = hosp_nums_obj[0].get('research_title')

    # взять самое последнее направленеие из hosp_dirs
    hosp_last_num = hosp_nums_obj[-1].get('direction')
    # 'Время выписки', 'Дата выписки', 'Основной диагноз (описание)', 'Осложнение основного диагноза (описание)', 'Сопутствующий диагноз (описание)'
    date_value, time_value, outcome, result_hospital = '', '', '', ''
    hosp_extract_data = hosp_extract_get_data(hosp_last_num)
    days_count = '__________________________'
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
        Paragraph('3. Пол: {} {}4. Дата рождения {}'.format(sex, space_symbol * 24, patient_data['born']), style),
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
        Paragraph('12. Кем направлен больной: {}'.format(primary_reception_data['who_directed']), style),
        Paragraph('13. Кем доставлен: _________________________________ Код______ Номер наряда__________', style),
        Paragraph('14. Диагноз направившего учреждения: {}'.format(primary_reception_data['diagnos_who_directed']), style),
        Paragraph('14.1 Состояние при поступлении: {}'.format(primary_reception_data['state']), style),
        Paragraph('15. Диагноз приемного отделения:{}'.format(primary_reception_data['diagnos_entered']), style),
        Paragraph('16. Доставлен в состоянии опьянения: Алкогольного — 1; Наркотического — 2.', style),
        Paragraph('17. Госпитализирован по поводу данного заболевания в текущем году: {}'.format(hospitalized), style),
        Paragraph('18.Доставлен в стационар от начала заболевания(получения травмы):  первые 6 часов — 1; в теч. 7— 24 часов — 2; позднее 24-х часов — 3.', style),
        Paragraph('19. Травма: — производственная: промышленная — 1; транспортная — 2, в т. ч. ДТП — 3; с/хоз — 4; прочие — 5;', style),
        Paragraph('— непроизводственная: бытовая — 6; уличная — 7; транспортная — 8, в т. ч. ДТП — 9; школьная — 10; спортивная — 11; противоправная травма — 12; прочие — 13.', style),
        Paragraph('20. Дата поступления в приемное отделение:______________ Время__________', style),
        Paragraph('21. Название отделения: <u>{}</u>; дата поступления: <u>{}</u>; время: <u>{}</u>'.format(hosp_depart, primary_reception_data['date_entered_value'],
                                                                                                            primary_reception_data['time_entered_value']), style),
        Paragraph('Подпись врача приемного отделения ______________ Код __________', style),
        Paragraph('22. Дата выписки (смерти): {}; Время {}'.format(date_value, time_value), style),
        Paragraph('23. Продолжительность госпитализации (койко - дней): {}'.format(days_count), style),
        Paragraph('24. Исход госпитализации: {}'.format(outcome), style),
        Paragraph('24.1. Результат госпитализации: {}'.format(result_hospital), style),
        Paragraph('25. Листок нетрудоспособности: открыт _ _._ _._ _ _ _ закрыт:_ _._ _._ _ _ _', style),
        Paragraph('25.1. По уходу за больным Полных лет: _____ Пол: {}'.format(sex), style),
        Paragraph('26. Движение пациента по отделениям:', style),
    ]
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

    opinion = [[Paragraph('N', styleTB), Paragraph('Код отделения', styleTB), Paragraph('Профиль коек', styleTB), Paragraph('Код врача', styleTB), Paragraph('Дата поступления', styleTB),
                Paragraph('Дата выписки, перевода', styleTB), Paragraph('Код диагноза по МКБ', styleTB), Paragraph('Код медицинского стандарта', styleTB),
                Paragraph('Код прерванного случая', styleTB), Paragraph('Вид оплаты', styleTB)]]

    patient_movement = hosp_patient_movement(hosp_nums_obj)
    x = 0
    for i in patient_movement:
        x += 1
        doc_code = ''
        if i['doc_confirm_code']:
            doc_code = str(i['doc_confirm_code'])
        tmp_data = [[Paragraph(str(x), styleTB), Paragraph('', styleTB), Paragraph(i['bed_profile_research_title'], styleTB),
                     Paragraph(doc_code, styleTB), Paragraph(i['date_entered_value'], styleTB),
                     Paragraph(i['date_oute'], styleTB), Paragraph(i['diagnos_mkb'], styleTB), Paragraph('', styleTB),
                     Paragraph('', styleTB), Paragraph('ОМС', styleTB),
                     ], ]

        opinion.extend(tmp_data.copy())

    # получить структуру данных для таблицы
    tbl_act = Table(opinion, repeatRows=1, colWidths=(7 * mm, 15 * mm, 30 * mm, 20 * mm, 21 * mm, 21 * mm, 20 * mm, 14 * mm, 14 * mm, 20 * mm))

    tbl_act.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    objs.append(tbl_act)
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph('27. Хирургические операции(обозначить: основную операцию, использование спец.аппаратуры):', style), )

    opinion = [[Paragraph('Дата, Час', styleTB), Paragraph('Код <br/>хирурга', styleTB), Paragraph('Код отделения', styleTB), Paragraph('наименование операции', styleTB),
                Paragraph('код операции', styleTB), Paragraph('наименование осложнения', styleTB), Paragraph('Код ослонения', styleTB), Paragraph('Анестезия (код врача)', styleTB),
                Paragraph('энд.', styleTB), Paragraph('лазер.', styleTB), Paragraph('криог.', styleTB), Paragraph('Вид оплаты', styleTB)]]

    patient_operation = hosp_get_operation_data(num_dir)
    operation_result = []
    for i in patient_operation:
        operation_template = [''] * 12
        operation_template[0] = Paragraph(i['date'] + '<br/>' + i['time_start'] + '-' + i['time_end'], styleTB)
        operation_template[1] = Paragraph(str(i['doc_code']), styleTB)
        operation_template[3] = Paragraph(i['name_operation'], styleTB)
        operation_template[4] = Paragraph('{}'.format(i['code_operation'] + '<br/>' + i['plan_operation']), styleTB)
        operation_template[7] = Paragraph('{}'.format(i['anesthesia method'] + '<br/> (' + i['code_doc_anesthesia'] + ')'), styleTB)
        operation_template[5] = Paragraph(i['complications'], styleTB)
        operation_template[11] = Paragraph(" ОМС", styleTB)
        operation_result.append(operation_template.copy())

    opinion.extend(operation_result)
    tbl_act = Table(opinion, repeatRows=1, colWidths=(22 * mm, 12 * mm, 11 * mm, 26 * mm, 26 * mm, 20 * mm, 10 * mm, 15 * mm, 7 * mm, 7 * mm, 7 * mm, 16 * mm))
    tbl_act.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    objs.append(tbl_act)
    objs.append(Spacer(1, 2 * mm))
    space_symbol = '&nbsp;'

    objs.append(Paragraph('28. Обследован: RW {}  AIDS '.format(space_symbol * 10), style), )
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph('29. Диагноз стационара(при выписке):', style), )

    opinion = [[Paragraph('Клинический заключительный', styleTB), Paragraph('Основное заболевание', styleTB), Paragraph('Код МКБ', styleTB), Paragraph('Осложнение', styleTB),
                Paragraph('Код МКБ', styleTB), Paragraph('Сопутствующее заболевание', styleTB), Paragraph('Код МКБ', styleTB)]]

    hosp_last_num = hosp_nums_obj[-1].get('direction')
    hosp_extract_data = hosp_extract_get_data(hosp_last_num)

    opinion_diagnos = [[Paragraph('', styleTB), Paragraph(hosp_extract_data['final_diagnos'], styleTB), Paragraph(hosp_extract_data['final_diagnos_mkb'], styleTB),
                        Paragraph(hosp_extract_data['other_diagnos'], styleTB), Paragraph(hosp_extract_data['other_diagnos_mkb'], styleTB),
                        Paragraph(hosp_extract_data['near_diagnos'], styleTB), Paragraph(hosp_extract_data['near_diagnos_mkb'], styleTB)]]

    opinion.extend(opinion_diagnos)
    opinion_pathologist = [[Paragraph('Патологоанатомический	', styleTB), Paragraph('', styleTB), Paragraph('', styleTB), Paragraph('', styleTB),
                            Paragraph('', styleTB), Paragraph('', styleTB), Paragraph('', styleTB)]]

    opinion.extend(opinion_pathologist)
    tbl_act = Table(opinion, repeatRows=1, colWidths=(28 * mm, 45 * mm, 15 * mm, 30 * mm, 15 * mm, 30 * mm, 15 * mm))
    tbl_act.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (0, 0), (0, 1)),
    ]))

    objs.append(tbl_act)
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph('30.В случае смерти указать основную причину:______________________________________________________________'
                          'Код МКБ', style), )
    objs.append(Spacer(1, 20 * mm))
    objs.append(Paragraph(
        '31. Дефекты догоспитального этапа: несвоевременность госпитализации - 1; недостаточный объем клинико - диагностического обследования - 2; '
        'неправильная тактика лечения - 3; несовпадение диагноза - 4.', style), )
    objs.append(Spacer(1, 7 * mm))
    objs.append(Paragraph('Подпись лечащего врача ({}) ____________________________'. format(doc_fio), style), )
    objs.append(Spacer(1, 7 * mm))
    objs.append(Paragraph('Подпись заведующего отделением', style), )

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
