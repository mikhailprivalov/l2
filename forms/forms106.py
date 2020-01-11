from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, FrameBreak, Table, \
    TableStyle, Frame, KeepInFrame
from reportlab.platypus import PageBreak, NextPageTemplate, Indenter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, StyleSheet1
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.colors import HexColor
from reportlab.lib.colors import black

from appconf.manager import SettingManager
from clients.models import Card, Document
from directions.models import Napravleniya, Issledovaniya, ParaclinicResult
from directory.models import Fractions
from laboratory.settings import FONTS_FOLDER
import datetime
import locale
import sys
import pytils
import os.path
from io import BytesIO
from . import forms_func
from reportlab.pdfgen import canvas
from api.stationar.stationar_func import hosp_get_hosp_direction, hosp_get_data_direction, get_direction_attrs
from api.stationar.sql_func import get_result_value_iss
from api.sql_func import get_fraction_result


def form_01(request_data):
    """
    Форма 003/у - cстационарная карта
    """

    num_dir = request_data["dir_pk"]
    direction_obj = Napravleniya.objects.get(pk=num_dir)
    history_num = direction_obj.history_num
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
        if ind_card.district != None:
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

    p_phone = ''
    if patient_data['phone']:
        p_phone = 'тел. ' + ", ".join(patient_data['phone'])

    card_num_obj = patient_data['card_num'].split(' ')
    p_card_num = card_num_obj[0]
    if len(card_num_obj) ==2:
        p_card_type = '('+ str(card_num_obj[1]) + ')'
    else:
        p_card_type =''

    # взять самое последнее направленеие из hosp_dirs
    hosp_last_num = hosp_nums_obj[-1].get('direction')
    ############################################################################################################
    #Получение данных из выписки
    #Взять услугу типа выписка. Из полей "Дата выписки" - взять дату. Из поля "Время выписки" взять время
    hosp_extract = hosp_get_data_direction(hosp_last_num, site_type=7, type_service='None', level=2)
    hosp_extract_iss, extract_research_id = None, None
    if hosp_extract:
        hosp_extract_iss = hosp_extract[0].get('iss')
        extract_research_id = hosp_extract[0].get('research_id')
    titles_field = ['Время выписки', 'Дата выписки']
    list_values = None
    if titles_field and hosp_extract:
        list_values = get_result_value_iss(hosp_extract_iss, extract_research_id, titles_field)
    date_value = None
    time_value = None
    if list_values:
        for i in list_values:
            if i[3] == 'Дата выписки':
                date_value = i[2]
            if i[3] == 'Время выписки':
                time_value = i[2]

        if date_value:
            vv = date_value.split('-')
            if len(vv) == 3:
                date_value = "{}.{}.{}".format(vv[2], vv[1], vv[0])

    #Получить отделение - из названия услуги изи самого главного направления
    hosp_depart = hosp_nums_obj[0].get('research_title')

    ############################################################################################################
    #Получить данные из первичного приема (самого первого hosp-направления)
    hosp_first_num = hosp_nums_obj[0].get('direction')
    hosp_primary_receptions = hosp_get_data_direction(hosp_first_num, site_type=0, type_service='None', level=2)
    hosp_primary_iss, primary_research_id = None, None
    if hosp_primary_receptions:
        hosp_primary_iss = hosp_primary_receptions[0].get('iss')
        primary_research_id = hosp_primary_receptions[0].get('research_id')

    titles_field = ['Дата поступления', 'Время поступления', 'Виды транспортировки',
                    'Побочное действие лекарств (непереносимость)', 'Кем направлен больной',
                    'Вид госпитализации',
                    'Время через, которое доставлен после начала заболевания, получения травмы',
                    'Диагноз направившего учреждения', 'Диагноз при поступлении']
    if titles_field and hosp_primary_receptions:
        list_values = get_result_value_iss(hosp_primary_iss, primary_research_id, titles_field)


    date_entered_value, time_entered_value, type_transport, medicament_allergy = '', '', '', ''
    who_directed, plan_hospital, extra_hospital, type_hospital = '', '', '', ''
    time_start_ill, diagnos_who_directed, diagnos_entered = '', '', ''

    if list_values:
        for i in list_values:
            if i[3] == 'Дата поступления':
                date_entered_value = i[2]
                continue
            if i[3] == 'Время поступления':
                time_entered_value = i[2]
                continue
            if i[3] == 'Виды транспортировки':
                type_transport = i[2]
                continue
            if i[3] == 'Побочное действие лекарств (непереносимость)':
                medicament_allergy = i[2]
                continue
            if i[3] == 'Кем направлен больной':
                who_directed = i[2]
                continue
            if i[3] == 'Вид госпитализации':
                type_hospital = i[2]
            if type_hospital == 'Экстренная':
                time_start_ill_obj = get_result_value_iss(hosp_primary_iss, primary_research_id, ['Время через, которое доставлен после начала заболевания, получения травмы'])
                if time_start_ill_obj:
                    time_start_ill = time_start_ill_obj[0][2]
                extra_hospital = "Да"
                plan_hospital = "Нет"
            else:
                plan_hospital = "Да"
                extra_hospital = "Нет"
                time_start_ill = ''
            if i[3] == 'Диагноз направившего учреждения':
                diagnos_who_directed = i[2]
                continue
            if i[3] =='Диагноз при поступлении':
                diagnos_entered = i[2]
                continue

        if date_entered_value:
            vv = date_entered_value.split('-')
            if len(vv) == 3:
                date_entered_value = "{}.{}.{}".format(vv[2], vv[1], vv[0])

    ###########################################################################################################

    fcaction_avo_id = Fractions.objects.filter(title='Групповая принадлежность крови по системе АВО').first()
    fcaction_rezus_id = Fractions.objects.filter(title='Резус').first()
    group_blood_avo = get_fraction_result(ind_card.pk, fcaction_avo_id.pk, count=1)
    group_blood_rezus = get_fraction_result(ind_card.pk, fcaction_rezus_id.pk, count=1)
    group_rezus_value = group_blood_rezus[0][5].replace('<br/>',' ')
    ###########################################################################################################
    #получение данных клинического диагноза
    hosp_day_entries = hosp_get_data_direction(hosp_first_num, site_type=1, type_service='None', level=-1)
    day_entries_iss = []
    day_entries_research_id = None
    if hosp_day_entries:
        for i in hosp_day_entries:
            #найти дневники совместно с заведующим
            if i.get('research_title').find('заведующ') != -1:
                day_entries_iss.append(i.get('iss'))
                if not day_entries_research_id:
                    day_entries_research_id = i.get('research_id')

    titles_field = ['Диагноз клинический', 'Дата установления диагноза']
    list_values = []
    if titles_field and day_entries_iss:
        for i in day_entries_iss:
            print(i)
            list_values.append(get_result_value_iss(i, day_entries_research_id, titles_field))
    print(list_values)
    s = ''
    for i in list_values:
        date_diag = i[0][2]
        if date_diag:
            vv = date_diag.split('-')
            if len(vv) == 3:
                date_diag = "{}.{}.{}".format(vv[2], vv[1], vv[0])
                s = s + '<br/>'+ i[1][2] + '; дата:' + date_diag
                print(s)



    title_page = [
        Indenter(left=0 * mm),
        Spacer(1, 8 * mm),
        Paragraph(
            '<font fontname="PTAstraSerifBold" size=15>МЕДИЦИНСКАЯ КАРТА № {} <u>{}</u>, <br/> стационарного больного</font>'.format(
                p_card_num, hosp_nums), styleCenter),
        Spacer(1, 2 * mm),
        Spacer(1, 2 * mm),
        Spacer(1, 2 * mm),

        Paragraph('Дата и время поступления: {} - {}'.format(date_entered_value, time_entered_value), style),
        Spacer(1, 2 * mm),

        Paragraph('Дата и время выписки: {} - {}'.format(date_value, time_value), style),
        Spacer(1, 2 * mm),
        Paragraph('Отделение: {}'.format(hosp_depart), style),
        Spacer(1, 2 * mm),
        Paragraph('Палата №: {}'.format('_________________________'), style),
        Spacer(1, 2 * mm),
        Paragraph('Переведен в отделение: {}'.format('______________'), style),
        Spacer(1, 2 * mm),
        Paragraph('Проведено койко-дней: {}'.format('______________________________________________'), style),
        Spacer(1, 2 * mm),
        Paragraph('Виды транспортировки(на каталке, на кресле, может идти): {}'.format(type_transport), style),
        Spacer(1, 2 * mm),
        Paragraph('Группа крови: {}. Резус-принадлежность: {}'.format(group_blood_avo[0][5], group_rezus_value), style),
        Spacer(1, 2 * mm),
        Paragraph('Побочное действие лекарств(непереносимость):', style),
        Spacer(1, 12 * mm),
        Paragraph("1. Фамилия, имя, отчество:&nbsp;  <font size=11.7 fontname ='PTAstraSerifBold'> {} </font> ".format(patient_data['fio']), style),
        Spacer(1, 2 * mm),
        Paragraph(
            '2. Пол: {} {} 3. Дата рождения: {}'.format(patient_data['sex'], 3 * space_symbol, patient_data['born']),
            style),
        Spacer(1, 2 * mm),
        Paragraph('4. Постоянное место жительства: город, село: {}'.format(patient_data['main_address']), style),
        Paragraph('{}'.format(p_phone), style),
        Spacer(1, 2 * mm),
        Paragraph('5. Место работы, профессия или должность', style),
        Spacer(1, 2 * mm),
        Paragraph('6. Кем направлен больной: {}'.format(who_directed), style),
        Spacer(1, 2 * mm),
        Paragraph('7. Доставлен в стационар по экстренным показаниям: {}'.format(extra_hospital), style),
        Spacer(1, 2 * mm),
        Paragraph(' через: {} часов после начала заболевания, получения травмы; '.format(time_start_ill), style),
        Spacer(1, 2 * mm),
        Paragraph(' госпитализирован в плановом порядке (подчеркнуть) {}.'.format(plan_hospital), style),
        Spacer(1, 2 * mm),
        Paragraph('8. Диагноз направившего учреждения:', style),
        Spacer(1, 8 * mm),
        Paragraph('9. Диагноз при поступлении:', style),
        Spacer(1, 10 * mm),
        Paragraph('10. Диагноз клинический:', style),
        PageBreak()]

    second_page = [
        Spacer(1, 2 * mm),
        Paragraph('11. Диагноз заключительный клинический: {}'.format('Из выписки'), style),
        Spacer(1, 2 * mm),
        Paragraph('а) основной: {}'.format('Из выписки'), style),
        Spacer(1, 2 * mm),
        Paragraph('б) осложнение основного: {}'.format('Из выписки'), style),
        Spacer(1, 2 * mm),
        Paragraph('в) сопутствующий: {}'.format('Из выписки'), style),
        Spacer(1, 2 * mm),
        Paragraph('12. Госпитализирован в данном году по поводу данного заболевания: впервые, повторно (подчеркнуть),'
                  'всего  - ___раз.:{}'.format('Из выписки'), style),
        Spacer(1, 2 * mm),
        Paragraph('13. Хирургические операции, методы обезболивания и послеоперационные осложнения.:{}'.format('Из про-токолов операции всех направлений-отделений'), style),
        Spacer(1, 2 * mm),
        Paragraph('14. Другие виды лечения:___________________________________________'.format('Из '), style),
        Spacer(1, 2 * mm),
        Paragraph('_________________________________________________________________', style),
        Spacer(1, 2 * mm),
        Paragraph('для больных злокачественными новообразованиями.', style),
        Spacer(1, 2 * mm),
        Paragraph(' 1.Специальное лечение: хирургическое(дистанционная гамматерапия, рентгенотерапия, быстрые '
                  'электроны, контактная и дистанционная гамматерапия, контактная гамматерапия и глубокая '
                  'рентгенотерапия); комбинированное(хирургическое и гамматерапия, хирургическое и рентгено - '
                  'терапия, хирургическое и сочетанное лучевое); химиопрепаратами, гормональными препаратами.', style),
        Spacer(1, 2 * mm),
        Paragraph('2. Паллиативное', style),
        Spacer(1, 2 * mm),
        Paragraph('3. Симптоматическое лечение.', style),
        Spacer(1, 2 * mm),
        Paragraph('15. Отметка о выдаче листка нетрудоспособности: {}'.format('из протоколов БЛ всех направлений-отделений'), style),
        Spacer(1, 2 * mm),
        Paragraph('16. Исход заболевания: {}'.format('из выписки'), style),
        Spacer(1, 2 * mm),
        Paragraph('17.  Трудоспособность восстановлена полностью, снижена, временно утрачена, стойко утрачена в связи '
                  'с данным заболеванием, с другими причинами(подчеркнуть): {}'.format('из выписки'), style),
        Spacer(1, 2 * mm),
        Paragraph('18. Для поступивших на экспертизу - заключение:___________________', style),
        Spacer(1, 2 * mm),
        Paragraph('___________________________________________________________________', style),
        Spacer(1, 2 * mm),
        Paragraph('19. Особые отметки', style)
    ]

    objs.extend(title_page)
    objs.extend(second_page)


    def first_pages(canvas, document):
        canvas.saveState()
        #Побочное действие лекарств(непереносимость) координаты
        medicament_text = [Paragraph('{}'.format(medicament_allergy), styleJustified)]
        medicament_frame = Frame(27 * mm, 163 * mm, 175 * mm, 12 * mm, leftPadding=0, bottomPadding=0,
                              rightPadding=0, topPadding=0, id='diagnos_frame', showBoundary=0)
        medicament_inframe = KeepInFrame(175 * mm, 12 * mm, medicament_text, hAlign='LEFT', vAlign='TOP', )
        medicament_frame.addFromList([medicament_inframe], canvas)

        #Диагноз направившего учреждения координаты
        diagnos_directed_text = [Paragraph('{}'.format(diagnos_who_directed), styleJustified)]
        diagnos_directed_frame = Frame(27 * mm, 81 * mm, 175 * mm, 10 * mm, leftPadding=0, bottomPadding=0,
                                rightPadding=0, topPadding=0, id='diagnos_frame', showBoundary=0)
        diagnos_directed_inframe = KeepInFrame(175 * mm, 10 * mm, diagnos_directed_text, hAlign='LEFT', vAlign='TOP', )
        diagnos_directed_frame.addFromList([diagnos_directed_inframe], canvas)

        # Диагноз при поступлении координаты
        diagnos_entered_text = [Paragraph('{}'.format(diagnos_entered), styleJustified)]
        diagnos_entered_frame = Frame(27 * mm, 67 * mm, 175 * mm, 10 * mm, leftPadding=0, bottomPadding=0,
                                       rightPadding=0, topPadding=0, id='diagnos_frame', showBoundary=0)
        diagnos_entered_inframe = KeepInFrame(175 * mm, 10 * mm, diagnos_entered_text, hAlign='LEFT',
                                               vAlign='TOP', )
        diagnos_entered_frame.addFromList([diagnos_entered_inframe], canvas)

        #клинический диагноз координаты
        diagnos_text = [Paragraph('{}'.format(s * 1), styleJustified)]
        diagnos_frame = Frame(27 * mm, 5 * mm, 175 * mm, 60 * mm, leftPadding=0, bottomPadding=0,
                              rightPadding=0, topPadding=0, id='diagnos_frame', showBoundary=0)
        diagnos_inframe = KeepInFrame(175 * mm, 60 * mm, diagnos_text)
        diagnos_frame.addFromList([diagnos_inframe], canvas)
        canvas.restoreState()

    def later_pages(canvas, document):
        canvas.saveState()
        canvas.restoreState()

    doc.build(objs, onFirstPage=first_pages, onLaterPages=later_pages)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
