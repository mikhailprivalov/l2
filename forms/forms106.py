from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Frame, KeepInFrame
from reportlab.platypus import PageBreak, Indenter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import black

from appconf.manager import SettingManager
from directions.models import Napravleniya, Issledovaniya
from directory.models import Fractions
from laboratory.settings import FONTS_FOLDER
import locale
import sys
import os.path
from io import BytesIO
from api.stationar.stationar_func import hosp_get_hosp_direction, hosp_get_data_direction
from api.stationar.sql_func import get_result_value_iss
from api.sql_func import get_fraction_result
from utils.dates import normalize_date
from .forms_func import primary_reception_get_data, hosp_extract_get_data, hosp_get_clinical_diagnos, hosp_get_transfers_data


def form_01(request_data):
    """
    Форма 003/у - cстационарная карта
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

    styleRight = deepcopy(styleJustified)
    styleRight.alignment = TA_RIGHT

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

    p_phone = ''
    if patient_data['phone']:
        p_phone = 'тел.: ' + ", ".join(patient_data['phone'])

    p_address = patient_data['main_address']
    work_place = patient_data['work_place_db'] if patient_data['work_place_db'] else patient_data['work_place']
    p_work = work_place

    card_num_obj = patient_data['card_num'].split(' ')
    p_card_num = card_num_obj[0]

    # взять самое последнее направленеие из hosp_dirs
    hosp_last_num = hosp_nums_obj[-1].get('direction')
    ############################################################################################################
    # Получение данных из выписки
    # Взять услугу типа выписка. Из полей "Дата выписки" - взять дату. Из поля "Время выписки" взять время
    # 'Время выписки', 'Дата выписки', 'Основной диагноз (описание)', 'Осложнение основного диагноза (описание)', 'Сопутствующий диагноз (описание)'
    hosp_extract_data = hosp_extract_get_data(hosp_last_num)

    # Получить отделение - из названия услуги или самого главного направления
    hosp_depart = hosp_nums_obj[0].get('research_title')

    ############################################################################################################
    # Получить данные из первичного приема (самого первого hosp-направления)
    # 'Дата поступления', 'Время поступления', 'Виды транспортировки','Побочное действие лекарств (непереносимость)', 'Кем направлен больной',
    # 'Вид госпитализации','Время через, которое доставлен после начала заболевания, получения травмы',
    # 'Диагноз направившего учреждения', 'Диагноз при поступлении'
    hosp_first_num = hosp_nums_obj[0].get('direction')
    primary_reception_data = primary_reception_get_data(hosp_first_num)

    ###########################################################################################################
    # Получение данных группы крови
    fcaction_avo_id = Fractions.objects.filter(title='Групповая принадлежность крови по системе АВО').first()
    fcaction_rezus_id = Fractions.objects.filter(title='Резус').first()
    group_blood_avo = get_fraction_result(ind_card.pk, fcaction_avo_id.pk, count=1)
    group_blood_avo_value = ''
    if group_blood_avo:
        group_blood_avo_value = group_blood_avo[0][5]
    group_blood_rezus = get_fraction_result(ind_card.pk, fcaction_rezus_id.pk, count=1)
    group_rezus_value = ''
    if group_blood_rezus:
        group_rezus_value = group_blood_rezus[0][5].replace('<br/>', ' ')

    ###########################################################################################################
    # получение данных клинического диагноза
    clinical_diagnos = hosp_get_clinical_diagnos(hosp_first_num)

    #####################################################################################################
    # получить даные из переводного эпикриза: Дата перевода, Время перевода, в какое отделение переведен
    # у каждого hosp-направления найти подчиненное эпикриз Перевод*
    transfers = hosp_get_transfers_data(hosp_nums_obj)

    #####################################################################################################
    title_page = [
        Indenter(left=0 * mm),
        Spacer(1, 8 * mm),
        Paragraph(
            '<font fontname="PTAstraSerifBold" size=15>МЕДИЦИНСКАЯ КАРТА № {} <u>{}</u>, <br/> стационарного больного</font>'.format(
                p_card_num, hosp_nums), styleCenter),
        Spacer(1, 2 * mm),
        Spacer(1, 2 * mm),
        Spacer(1, 2 * mm),

        Paragraph('Дата и время поступления: {} - {}'.format(primary_reception_data['date_entered_value'], primary_reception_data['time_entered_value']), style),
        Spacer(1, 0.5 * mm),

        Paragraph('Дата и время выписки: {} - {}'.format(hosp_extract_data['date_value'], hosp_extract_data['time_value']), style),
        Spacer(1, 0.5 * mm),
        Paragraph('Отделение: {}'.format(hosp_depart), style),
        Spacer(1, 0.5 * mm),
        Paragraph('Палата №: {}'.format('_________________________'), style),
        Spacer(1, 0.5 * mm),
        Paragraph('Переведен в отделение:', style),
        Spacer(1, 8 * mm),
        Paragraph('Проведено койко-дней: {}'.format('______________________________________________'), style),
        Spacer(1, 0.5 * mm),
        Paragraph('Виды транспортировки(на каталке, на кресле, может идти): {}'.format(primary_reception_data['type_transport']), style),
        Spacer(1, 0.5 * mm),
        Paragraph('Группа крови: {}. Резус-принадлежность: {}'.format(group_blood_avo_value, group_rezus_value), style),
        Spacer(1, 1 * mm),
        Paragraph('Побочное действие лекарств(непереносимость):', style),
        Spacer(1, 12 * mm),
        Paragraph("1. Фамилия, имя, отчество:&nbsp;", style),
        Spacer(1, 2 * mm),
        Paragraph(
            '2. Пол: {} {} 3. Дата рождения: {}'.format(patient_data['sex'], 3 * space_symbol, patient_data['born']),
            style),
        Spacer(1, 0.5 * mm),
        Paragraph('4. Постоянное место жительства: ', style),
        Spacer(1, 3.5 * mm),
        Paragraph('5. Место работы, профессия или должность:', style),
        Spacer(1, 0.5 * mm),
        Paragraph('6. Кем направлен больной:', style),
        Spacer(1, 0.5 * mm),
        Paragraph('7. Доставлен в стационар по экстренным показаниям: {}'.format(primary_reception_data['extra_hospital']), style),
        Spacer(1, 0.5 * mm),
        Paragraph(' через: {} часов после начала заболевания, получения травмы; '.format(primary_reception_data['time_start_ill']), style),
        Spacer(1, 0.5 * mm),
        Paragraph(' госпитализирован в плановом порядке (подчеркнуть) {}.'.format(primary_reception_data['plan_hospital']), style),
        Spacer(1, 0.5 * mm),
        Paragraph('8. Диагноз направившего учреждения:', style),
        Spacer(1, 8 * mm),
        Paragraph('9. Диагноз при поступлении:', style),
        Spacer(1, 10 * mm),
        Paragraph('10. Диагноз клинический:', style),
        PageBreak()]

    second_page = [
        Spacer(1, 2 * mm),
        Paragraph('11. Диагноз заключительный клинический:', style),
        Spacer(1, 0.5 * mm),
        Paragraph('а) основной:', style),
        Spacer(1, 45 * mm),
        Paragraph('б) осложнение основного:', style),
        Spacer(1, 18 * mm),
        Paragraph('в) сопутствующий:', style),
        Spacer(1, 19 * mm),
        Paragraph('12. Госпитализирован в данном году по поводу данного заболевания: впервые, повторно (подчеркнуть),'
                  'всего  - ___раз.:{}'.format(''), style),
        Spacer(1, 1 * mm),
        Paragraph('13. Хирургические операции, методы обезболивания и послеоперационные осложнения:', style),
        Spacer(1, 40 * mm),
        Paragraph('14. Другие виды лечения:___________________________________________'.format('Из '), style),
        Spacer(1, 0.2 * mm),
        Paragraph('для больных злокачественными новообразованиями.', style),
        Spacer(1, 0.2 * mm),
        Paragraph(' 1.Специальное лечение: хирургическое(дистанционная гамматерапия, рентгенотерапия, быстрые '
                  'электроны, контактная и дистанционная гамматерапия, контактная гамматерапия и глубокая '
                  'рентгенотерапия); комбинированное(хирургическое и гамматерапия, хирургическое и рентгено - '
                  'терапия, хирургическое и сочетанное лучевое); химиопрепаратами, гормональными препаратами.', style),
        Spacer(1, 1 * mm),
        Paragraph('2. Паллиативное', style),
        Spacer(1, 0.2 * mm),
        Paragraph('3. Симптоматическое лечение.', style),
        Spacer(1, 0.2 * mm),
        Paragraph('15. Отметка о выдаче листка нетрудоспособности: {}'.format(''), style),
        Spacer(1, 1 * mm),
        Paragraph('16. Исход заболевания: {}'.format(''), style),
        Spacer(1, 1 * mm),
        Paragraph('17.  Трудоспособность восстановлена полностью, снижена, временно утрачена, стойко утрачена в связи '
                  'с данным заболеванием, с другими причинами(подчеркнуть): {}'.format(''), style),
        Spacer(1, 1 * mm),
        Paragraph('18. Для поступивших на экспертизу - заключение:___________________', style),
        Spacer(1, 1 * mm),
        Paragraph('___________________________________________________________________', style),
        Spacer(1, 1 * mm),
        Paragraph('19. Особые отметки', style),
        PageBreak()
    ]

    objs.extend(title_page)
    objs.extend(second_page)

    def first_pages(canvas, document):
        canvas.saveState()
        # Переведен
        transfers_text = [Paragraph('{}'.format(transfers), styleJustified)]
        transfers_frame = Frame(27 * mm, 206 * mm, 175 * mm, 7 * mm, leftPadding=0, bottomPadding=0,
                                rightPadding=0, topPadding=0, id='diagnos_frame', showBoundary=0)
        transfers_inframe = KeepInFrame(175 * mm, 12 * mm, transfers_text, hAlign='LEFT', vAlign='TOP', )
        transfers_frame.addFromList([transfers_inframe], canvas)

        # Побочное действие лекарств(непереносимость) координаты
        medicament_text = [Paragraph('{}'.format(primary_reception_data['medicament_allergy']), styleJustified)]
        medicament_frame = Frame(27 * mm, 171 * mm, 175 * mm, 9 * mm, leftPadding=0, bottomPadding=0,
                                 rightPadding=0, topPadding=0, id='diagnos_frame', showBoundary=0)
        medicament_inframe = KeepInFrame(175 * mm, 12 * mm, medicament_text, hAlign='LEFT', vAlign='TOP', )
        medicament_frame.addFromList([medicament_inframe], canvas)

        # ФИО
        fio_text = [Paragraph("<font size=11.7 fontname ='PTAstraSerifBold'> {}</font> ".format(patient_data['fio']), style)]
        fio_frame = Frame(77 * mm, 159 * mm, 125 * mm, 8 * mm, leftPadding=0, bottomPadding=0,
                          rightPadding=0, topPadding=0, id='diagnos_frame', showBoundary=0)
        fio_inframe = KeepInFrame(175 * mm, 12 * mm, fio_text, hAlign='LEFT', vAlign='TOP', )
        fio_frame.addFromList([fio_inframe], canvas)

        # Постоянное место жительства
        live_text = [Paragraph('{}, {}'.format(p_address, p_phone), style)]
        live_frame = Frame(88 * mm, 144 * mm, 115 * mm, 9 * mm, leftPadding=0, bottomPadding=0,
                           rightPadding=0, topPadding=0, id='diagnos_frame', showBoundary=0)
        live_inframe = KeepInFrame(175 * mm, 12 * mm, live_text, hAlign='LEFT', vAlign='TOP', )
        live_frame.addFromList([live_inframe], canvas)

        # Место работы
        work_text = [Paragraph('{}'.format(p_work), style)]
        work_frame = Frame(108 * mm, 138.5 * mm, 95 * mm, 5 * mm, leftPadding=0, bottomPadding=0,
                           rightPadding=0, topPadding=0, id='diagnos_frame', showBoundary=0)
        work_inframe = KeepInFrame(175 * mm, 12 * mm, work_text, hAlign='LEFT', vAlign='TOP', )
        work_frame.addFromList([work_inframe], canvas)

        # Кем направлен больной
        who_directed_text = [Paragraph('{}'.format(primary_reception_data['who_directed']), style)]
        who_directed_frame = Frame(77 * mm, 129.5 * mm, 126 * mm, 7 * mm, leftPadding=0, bottomPadding=0,
                                   rightPadding=0, topPadding=0, id='diagnos_frame', showBoundary=0)
        who_directed_inframe = KeepInFrame(175 * mm, 12 * mm, who_directed_text, hAlign='LEFT', vAlign='TOP', )
        who_directed_frame.addFromList([who_directed_inframe], canvas)

        # Диагноз направившего учреждения координаты
        diagnos_directed_text = [Paragraph('{}'.format(primary_reception_data['diagnos_who_directed']), styleJustified)]
        diagnos_directed_frame = Frame(27 * mm, 98 * mm, 175 * mm, 9 * mm, leftPadding=0, bottomPadding=0,
                                       rightPadding=0, topPadding=0, id='diagnos_frame', showBoundary=0)
        diagnos_directed_inframe = KeepInFrame(175 * mm, 10 * mm, diagnos_directed_text, hAlign='LEFT', vAlign='TOP', )
        diagnos_directed_frame.addFromList([diagnos_directed_inframe], canvas)

        # Диагноз при поступлении координаты
        diagnos_entered_text = [Paragraph('{}'.format(primary_reception_data['diagnos_entered']), styleJustified)]
        diagnos_entered_frame = Frame(27 * mm, 83 * mm, 175 * mm, 10 * mm, leftPadding=0, bottomPadding=0,
                                      rightPadding=0, topPadding=0, id='diagnos_frame', showBoundary=0)
        diagnos_entered_inframe = KeepInFrame(175 * mm, 10 * mm, diagnos_entered_text, hAlign='LEFT',
                                              vAlign='TOP', )
        diagnos_entered_frame.addFromList([diagnos_entered_inframe], canvas)

        # клинический диагноз координаты
        diagnos_text = [Paragraph('{}'.format(clinical_diagnos), styleJustified)]
        diagnos_frame = Frame(27 * mm, 22 * mm, 175 * mm, 55 * mm, leftPadding=0, bottomPadding=0,
                              rightPadding=0, topPadding=0, id='diagnos_frame', showBoundary=0)
        diagnos_inframe = KeepInFrame(175 * mm, 55 * mm, diagnos_text)
        diagnos_frame.addFromList([diagnos_inframe], canvas)

        # представитель пациента
        p_agent = None
        agent_status = ''
        agent = ''
        if ind_card.who_is_agent:
            p_agent = getattr(ind_card, ind_card.who_is_agent)
            agent_status = ind_card.get_who_is_agent_display()
        if p_agent:
            agent_data = p_agent.get_data_individual()
            agent_fio = agent_data['fio']
            agent_phone = ','.join(agent_data['phone'])
            agent = f"{agent_status}: {agent_fio}, тел.:{agent_phone}"

        agent_text = [Paragraph('<u>{}</u>'.format(agent), styleRight)]
        agent_frame = Frame(27 * mm, 5 * mm, 175 * mm, 7 * mm, leftPadding=0, bottomPadding=0,
                            rightPadding=0, topPadding=0, id='diagnos_frame', showBoundary=0)
        agent_inframe = KeepInFrame(175 * mm, 10 * mm, agent_text)
        agent_frame.addFromList([agent_inframe], canvas)
        canvas.restoreState()

    # Получить все услуги из категории операции
    styleTO = deepcopy(style)
    styleTO.alignment = TA_LEFT
    styleTO.firstLineIndent = 0
    styleTO.fontSize = 9.5
    styleTO.leading = 10
    styleTO.spaceAfter = 0.2 * mm

    # Таблица для операции
    opinion_oper = [
        [Paragraph('№', styleTO),
         Paragraph('Название операции', styleTO),
         Paragraph('Дата, &nbsp час', styleTO),
         Paragraph('Метод обезболивания', styleTO),
         Paragraph('Осложнения', styleTO),
         Paragraph('Оперировал', styleTO),
         ]
    ]

    hosp_operation = hosp_get_data_direction(num_dir, site_type=3, type_service='None', level=-1)
    operation_iss = []
    operation_research_id = None
    if hosp_operation:
        for i in hosp_operation:
            # найти протоколы по типу операции
            if i.get('research_title').lower().find('операци') != -1:
                operation_iss.append(i.get('iss'))
                if not operation_research_id:
                    operation_research_id = i.get('research_id')

    titles_field = ['Название операции', 'Дата проведения',
                    'Время начала', 'Время окончания', 'Метод обезболивания', 'Осложнения']
    list_values = []
    if titles_field and operation_research_id and hosp_operation:
        for i in operation_iss:
            list_values.append(get_result_value_iss(i, operation_research_id, titles_field))

        operation_result = []
        x = 0
        operation_template = [''] * len(titles_field)
        for fields_operation in list_values:
            date_time = {}
            date_time['date'], date_time['time_start'], date_time['time_end'] = '', '', ''
            field = None
            iss_obj = Issledovaniya.objects.filter(pk=fields_operation[0][1]).first()
            if not iss_obj.doc_confirmation:
                continue
            x += 1
            for field in fields_operation:
                if field[3] == 'Название операции':
                    operation_template[1] = Paragraph(field[2], styleTO)
                    continue
                if field[3] == 'Дата проведения':
                    date_time['date'] = normalize_date(field[2])
                    continue
                if field[3] == 'Время начала':
                    date_time['time_start'] = field[2]
                    continue
                if field[3] == 'Время окончания':
                    date_time['time_end'] = field[2]
                    continue
                if field[3] == 'Метод обезболивания':
                    operation_template[3] = Paragraph(field[2], styleTO)
                    continue
                if field[3] == 'Осложнения':
                    operation_template[4] = Paragraph(field[2], styleTO)
                    continue
            operation_template[0] = Paragraph(str(x), styleTO)
            operation_template[2] = Paragraph(date_time.get('date') + '<br/>' + date_time.get('time_start') + '-' +
                                              date_time.get('time_end'), styleTO)
            doc_fio = iss_obj.doc_confirmation.get_fio()
            operation_template[5] = Paragraph(doc_fio, styleTO)
            operation_result.append(operation_template.copy())
        opinion_oper.extend(operation_result)

    t_opinion_oper = opinion_oper.copy()
    tbl_o = Table(t_opinion_oper,
                  colWidths=(7 * mm, 62 * mm, 25 * mm, 30 * mm, 15 * mm, 45 * mm,))
    tbl_o.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.1 * mm),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    def later_pages(canvas, document):
        canvas.saveState()
        # Заключительные диагнозы
        # Основной заключительный диагноз
        final_diagnos_text = [Paragraph('{}'.format(hosp_extract_data['final_diagnos']), styleJustified)]
        final_diagnos_frame = Frame(27 * mm, 230 * mm, 175 * mm, 45 * mm, leftPadding=0, bottomPadding=0,
                                    rightPadding=0, topPadding=0, showBoundary=0)
        final_diagnos_inframe = KeepInFrame(175 * mm, 50 * mm, final_diagnos_text, hAlign='LEFT', vAlign='TOP', )
        final_diagnos_frame.addFromList([final_diagnos_inframe], canvas)

        # Осложнения основного заключительного диагноза
        other_diagnos_text = [Paragraph('{}'.format(hosp_extract_data['other_diagnos']), styleJustified)]
        other_diagnos_frame = Frame(27 * mm, 205 * mm, 175 * mm, 20 * mm, leftPadding=0, bottomPadding=0,
                                    rightPadding=0, topPadding=0, showBoundary=0)
        other_diagnos_inframe = KeepInFrame(175 * mm, 20 * mm, other_diagnos_text, hAlign='LEFT', vAlign='TOP', )
        other_diagnos_frame.addFromList([other_diagnos_inframe], canvas)

        # Сопутствующие основного заключительного диагноза
        near_diagnos_text = [Paragraph('{}'.format(hosp_extract_data['near_diagnos']), styleJustified)]
        near_diagnos_frame = Frame(27 * mm, 181 * mm, 175 * mm, 20 * mm, leftPadding=0, bottomPadding=0,
                                   rightPadding=0, topPadding=0, showBoundary=0)
        near_diagnos_inframe = KeepInFrame(175 * mm, 20 * mm, near_diagnos_text, vAlign='TOP', )
        near_diagnos_frame.addFromList([near_diagnos_inframe], canvas)

        # Таблица операции
        operation_text = [tbl_o]
        operation_frame = Frame(27 * mm, 123 * mm, 175 * mm, 40 * mm, leftPadding=0, bottomPadding=0,
                                rightPadding=0, topPadding=0, showBoundary=0)
        operation_inframe = KeepInFrame(175 * mm, 40 * mm, operation_text, hAlign='CENTRE', vAlign='TOP', fakeWidth=False)
        operation_frame.addFromList([operation_inframe], canvas)

        canvas.setFont('PTAstraSerifBold', 8)
        canvas.drawString(55 * mm, 12 * mm, '{}'.format(SettingManager.get("org_title")))
        canvas.drawString(55 * mm, 9 * mm, '№ карты : {}; Номер истории: {}'.format(p_card_num, hosp_nums))
        canvas.drawString(55 * mm, 6 * mm,
                          'Пациент: {} {}'.format(patient_data['fio'], patient_data['born']))
        canvas.line(55 * mm, 11.5 * mm, 200 * mm, 11.5 * mm)

        canvas.restoreState()

    doc.build(objs, onFirstPage=first_pages, onLaterPages=later_pages)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf
