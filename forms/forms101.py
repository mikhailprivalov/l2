import datetime
import locale
import os
import sys
from copy import deepcopy
from io import BytesIO

import pytils
from django.utils import timezone, dateformat
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus.flowables import HRFlowable

from appconf.manager import SettingManager
from clients.models import Individual, Card
from laboratory import settings
from laboratory.settings import FONTS_FOLDER


def form_01(request_data):
    """
    generate form agreement to Hiv
    :param request_data: GET request data
    :return: pdf
    """
    ind = Individual.objects.get(pk=request_data["individual"])
    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=15 * mm,
                            rightMargin=15 * mm, topMargin=10 * mm,
                            bottomMargin=5 * mm, allowSplitting=1,
                            title="Форма {}".format("Сгласие на вич"))

    pdfmetrics.registerFont(
        TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansBold', os.path.join(FONTS_FOLDER, 'OpenSans-Bold.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansItalic', os.path.join(FONTS_FOLDER, 'OpenSans-Italic.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansBoldItalic', os.path.join(FONTS_FOLDER, 'OpenSans', 'OpenSans-BoldItalic.ttf')))
    pdfmetrics.registerFont(
        TTFont('OpenSansLight', os.path.join(FONTS_FOLDER, 'OpenSans', 'OpenSans-Light.ttf')))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "OpenSans"
    style.fontSize = 10
    style.leading = 15
    styleBold = deepcopy(style)
    styleBold.fontName = "OpenSansBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY

    i = ind
    objs = [
        Paragraph('<font face="OpenSansBold">Информированное согласие<br/>'
                  'пациента на проведение обследования на ВИЧ-инфекцию</font>',
                  styleCenterBold),
        Spacer(1, 5 * mm),
        Paragraph('<font face="OpenSans">Я, {}</font>'.format(i.fio()),
                  styleCenter),
    ]

    stx = [
        '{} года рождения, настоящим подтверждаю, что на основании представленной мне информации, свободно и без принуждения, отдавая отчет о последствиях обследования, принял решение пройти тестирование на антитела к ВИЧ. Для этой цели я соглашаюсь сдать анализ крови.<br/>'.format(  # noqa: E501
            i.bd()),
        'Я подтверждаю, что мне разъяснено, почему важно пройти тестирование на ВИЧ, как проводится тест и какие последствия может иметь тестирование на ВИЧ.',
        'Я проинформирован, что:',
        '- тестирование на ВИЧ проводится в Центре СПИД и других медицинских учреждениях. Тестирование по моему добровольному выбору может быть добровольным анонимным (без предъявления документов и указания имени) или конфиденциальным (при предъявлении паспорта, результат будет известен обследуемому и лечащему врачу). В государственных медицинских учреждениях тестирование на ВИЧ проводится бесплатно;',  # noqa: E501
        '- доказательством наличия ВИЧ-инфекции является присутствие антител к ВИЧ в крови обследуемого лица. Вместе с тем, в период между заражением и появлением антител к ВИЧ (так называемое "серонегативное окно, обычно 3 месяца) при тестировании не обнаруживаются антитела к ВИЧ и обследуемое лицо может заразить других лиц.',  # noqa: E501
        '- ВИЧ-инфекция передается только тремя путями:',
        '- парентеральный - чаще всего при употреблении наркотиков, но может передаваться также при использовании нестерильного медицинского инструментария, переливании компонентов крови, нанесении татуировок, пирсинге зараженным инструментом, использовании чужих бритвенных и маникюрных принадлежностей;',  # noqa: E501
        '- при сексуальных контактах без презерватива;',
        '- от инфицированной ВИЧ матери к ребенку во время беременности, родов и при грудном вскармливании.',
        '________________________________________________ ___________ (Подпись обследуемого на ВИЧ)',
        'Дата: {}'.format(dateformat.format(timezone.now(), settings.DATE_FORMAT))
    ]

    for s in stx:
        objs.append(Paragraph('<font face="OpenSans">{}</font>'.format(s), styleJustified))
        objs.append(Spacer(1, 4 * mm))

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_02(request_data):
    """
    Согласие на обработку персональных данных
    """
    ind_card = Card.objects.get(pk=request_data["card_pk"])
    patient_data = ind_card.get_data_individual()

    agent_status = False
    if ind_card.who_is_agent:
        p_agent = getattr(ind_card, ind_card.who_is_agent)
        agent_status = True

    # Если владельцу карты меньше 15 лет и не передан представитель, то вернуть ошибку
    who_patient = 'пациента'
    if patient_data['age'] < SettingManager.get("child_age_before", default='15',
                                                default_type='i') and not agent_status:
        return False
    elif patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i') and agent_status:
        who_patient = 'ребёнка'

    if agent_status:
        person_data = p_agent.get_data_individual()
    else:
        person_data = patient_data

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    # Генерировать pdf-Лист на оплату
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=13 * mm,
                            rightMargin=4 * mm, topMargin=4 * mm,
                            bottomMargin=4 * mm, allowSplitting=1,
                            title="Форма {}".format("Согласие на обработку ПДн"))
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 11
    style.leading = 12
    style.spaceAfter = 0 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = 15

    styleFL = deepcopy(style)
    styleFL.firstLineIndent = 0

    styleSign = deepcopy(style)
    styleSign.firstLineIndent = 0
    styleSign.alignment = TA_LEFT
    styleSign.leading = 13

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleBold.firstLineIndent = 0

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 9
    styleCenter.leading = 10
    styleCenter.spaceAfter = 0 * mm

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.firstLineIndent = 0
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 13
    styleCenterBold.face = 'PTAstraSerifBold'

    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    objs = []

    objs = [
        Paragraph('СОГЛАСИЕ <br/> на обработку персональных данных {}'.format(who_patient), styleCenterBold),
    ]

    d = datetime.datetime.strptime(person_data['born'], '%d.%m.%Y').date()
    date_individual_born = pytils.dt.ru_strftime(u"\"%d\" %B %Y", inflected=True, date=d)

    objs.append(Spacer(1, 3 * mm))
    objs.append(
        Paragraph('Я, нижеподписавшийся(аяся) {}&nbsp; {} г. рождения'.format(person_data['fio'], date_individual_born),
                  styleSign))

    styleLeft = deepcopy(style)
    styleLeft.alignment = TA_LEFT
    objs.append(Paragraph('Зарегистрированный(ая) по адресу: {}'.format(person_data['main_address']), styleSign))
    objs.append(Paragraph('Проживающий(ая) по адресу: {}'.format(person_data['fact_address']), styleSign))
    objs.append(Paragraph('Документ, удостоверяющий личность {}: серия <u> {}</u> номер: <u>{}</u>'.
                          format(person_data['type_doc'], person_data['passport_serial'], person_data['passport_num']),
                          styleSign))
    objs.append(
        Paragraph('Выдан: {} {}'.format(person_data['passport_date_start'], person_data['passport_issued']), styleSign))
    objs.append(Spacer(1, 2 * mm))

    hospital_name = SettingManager.get("org_title")
    hospital_address = SettingManager.get("org_address")

    if agent_status:
        opinion = [
            Paragraph(
                'являюсь законным представителем ({}) {}:'.format(ind_card.get_who_is_agent_display(), who_patient),
                styleBold),
            Paragraph('{}&nbsp; {} г. рождения'.format(patient_data['fio'], patient_data['born']), styleSign),
            Paragraph('Зарегистрированный(ая) по адресу: {}'.format(patient_data['main_address']), styleSign),
            Paragraph('Проживающий(ая) по адресу: {}'.format(patient_data['fact_address']), styleSign)
        ]

        # Проверить возраст пациента при наличии представителя (ребёнок|взрослый)
        if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i'):
            opinion.append(Paragraph(
                'Документ, удостоверяющий личность {}: серия <u>{}</u> номер <u>{}</u>'.format(patient_data['type_doc'],
                                                                                               patient_data[
                                                                                                   'bc_serial'],
                                                                                               patient_data['bc_num']),
                styleSign))
            opinion.append(
                Paragraph('Выдан: {} {}'.format(patient_data["bc_date_start"], person_data['bc_issued']), styleSign))
        else:
            opinion.append(
                Paragraph('Документ, удостоверяющий личность {}: серия {} номер {}'.format(patient_data['type_doc'],
                                                                                           patient_data[
                                                                                               'passport_serial'],
                                                                                           patient_data[
                                                                                               'passport_num']),
                          styleSign))
            opinion.append(
                Paragraph('Выдан: {} {}'.format(patient_data["passport_date_start"], person_data['passport_issued']),
                          styleSign))

        objs.extend(opinion)

    objs.append(Spacer(1, 2 * mm))
    objs.append(
        Paragraph('в соответствии с требованиями федерального закона от 27.07.2006 г. "О персональных данных" '
                  '№ 152-ФЗ, даю согласие Оператору: {} (далее – Оператор), находящегося по адресу: '
                  '{} на обработку моих и/или лица предствителем, которого я являюсь персональных данных (далее - Персональные данные),'
                  ' включающих: фамилию, имя, отчество, пол, дату рождения, адрес места жительства, контактные '
                  'телефон(ы), реквизиты полиса (ОМС, ДМС), страховой номер индивидуального лицевого счета в '
                  'Пенсионном фонде России (СНИЛС), данные паспорта (свидетельства о рождении ребёнка) '
                  '(номер, серия, кем и когда выдан), место работы (учебы) и должность, социальный статус, '
                  'семейное положение; любые сведения о состоянии '
                  'моего здоровья, и/или лица представителем которого я являюсь, заболеваниях, случаях обращения за медицинской помощью в следующих целях: '
                  'медико-профилактических, установления медицинского диагноза и оказания медицинских и медико-социальных услуг, '
                  'ведения медицинской карты пациента (на бумажных и безбумажных носителях); '
                  'реализации электронной записи к врачу; ведения персонифицированного учета оказанния медицинских '
                  'услуг; для реализации телемедицинских консультаций, электронного документооборота; осуществления '
                  'взаиморасчетов за оказанную медицинскую помощь в системе медицинского страхования (ОМС, ДМС); '
                  'хранения результатов исследований для последующего использования в установлении медицинского диагноза.'.
                  format(hospital_name, hospital_address), styleFL))
    objs.append(Paragraph(
        'Я согласен (согласна) на осмотр с применением телемедицинских технологий, а также на фото - и видеосъемку '
        'в процессе лечения в интересах моего, или лица, представителем которого я являюсь обследования и лечения.',
        style))
    objs.append(
        Paragraph('Предоставляю Оператору право осуществлять любое действие (операцию) или совокупность действий '
                  '(операций) с использованием средств автоматизации и/или без использования таких средств с '
                  'Персональными данными , включая сбор, запись, '
                  'систематизацию, накопление, хранение, уточнение (обновление, изменение), извлечение, использование, '
                  'передачу (распространение, предоставление, доступ), обезличивание, блокирование, удаление, уничтожение',
                  style))
    objs.append(
        Paragraph('В процессе оказания Оператором медицинской помощи субъекту персональных данных я предоставляю '
                  'право медицинским работникам передавать персональные данные, содержащие сведения, составляющие врачебную тайну, '
                  'другим должностным лицам Оператора, в интересах обследования и лечения, обслуживания документации, '
                  'программного обеспечения и технических средств. Я согласен (согласна) с тем, что доступ к Персональным данным '
                  'будут иметь сотрудники Оператора, осуществляющие техническое обслуживание информационной системы.',
                  style))
    objs.append(Paragraph(
        'Я согласен (согласна) с тем, что в соответствии с частью 3 статьи 6 федерального закона от 27.07.2006 г. '
        '"О персональных данных" № 152-ФЗ обработка указанных в настоящем согласии персональных данных '
        'может быть поручена другим лицам, на основании соглашения между оператором и лицом. Я согласен '
        'с тем, что в медико-профилактических целях, в целях установления медицинского диагноза и оказания '
        'медицинских и медико-социальных услуг, указанные в настоящем согласии персональные данные могут '
        'быть переданы в другие лечебно-профилактические учреждения для обработки лицом, профессионально '
        'занимающимся медицинской деятельностью и обязанным в соответствии с законодательством '
        'Российской Федерации сохранять врачебную тайну. Я согласен (согласна) с тем, что в целях осуществления '
        'медицинского страхования(обязательного/добровольного) персональные данные могут быть переданы в страховую медицинскую '
        'организацию и территориальный фонд ОМС с использованием машинных носителей или по каналам связи, '
        'с соблюдением мер, обеспечивающих их защиту от несанкционированного доступа. Я согласен (согласна) '
        'с тем, что в научных целях указанные в настоящем согласии персональные данные могут быть переданы '
        'в научные и образовательные организации, а также предоставляться доступ к ним обучающимся, '
        'ординаторам и аспирантам медицинских учебных учреждений. Срок хранения персональных данных '
        'соответствует сроку хранения первичных медицинских документов и составляет двадцать пять лет. '
        'Настоящее согласие действует со дня его подписания до дня отзыва.', style))
    date_year = datetime.datetime.now().strftime('%Y')
    objs.append(Spacer(1, 5 * mm))
    space_bottom = ' &nbsp;'

    styleSign = deepcopy(style)
    styleSign.firstLineIndent = 0
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph(
        '\"___\"____________{} {} _____________________ /______________________ /'.format(date_year, 30 * space_bottom),
        styleSign))
    objs.append(Paragraph('{} (подпись) '.format(57 * space_bottom), style))

    objs.append(Paragraph('', style))
    objs.append(Paragraph('', style))

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


def form_03(request_data):
    """
    Добровольное согласие на медицинское вмешательство
    --------------------------------------------------------------------------------------------------------------
    Приказ Министерства здравоохранения РФ от 20 декабря 2012 г. N 1177н
    "Об утверждении порядка дачи информированного добровольного согласия на медицинское вмешательство и
    отказа от медицинского вмешательства в отношении определенных видов медицинских вмешательств,
    форм информированного добровольного согласия на медицинское вмешательство и форм отказа
    от медицинского вмешательства" (с изменениями и дополнениями).

    Приказ Министерства здравоохранения и социального развития РФ от 23 апреля 2012 г. N 390н
   "Об утверждении Перечня определенных видов медицинских вмешательств, на которые граждане дают информированное добровольное
    согласие при выборе врача и медицинской организации для получения первичной медико-санитарной помощи
    :param request_date:
    :return:
    """
    ind_card = Card.objects.get(pk=request_data["card_pk"])
    patient_data = ind_card.get_data_individual()

    agent_status = False
    if ind_card.who_is_agent:
        p_agent = getattr(ind_card, ind_card.who_is_agent)
        agent_status = True

    # Если владельцу карты меньше 15 лет и не передан представитель, то вернуть ошибку
    who_patient = 'пациента'
    if patient_data['age'] < SettingManager.get("child_age_before", default='15',
                                                default_type='i') and not agent_status:
        return False
    elif patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i') and agent_status:
        who_patient = 'ребёнка'

    if agent_status:
        person_data = p_agent.get_data_individual()
    else:
        person_data = patient_data

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    # Генерировать pdf-Лист на оплату
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    # hospital_name = SettingManager.get("org_title")
    # hospital_address = SettingManager.get("org_address")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=20 * mm,
                            rightMargin=5 * mm, topMargin=6 * mm,
                            bottomMargin=5 * mm, allowSplitting=1,
                            title="Форма {}".format("Лист на оплату"))
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.leading = 14
    style.spaceAfter = 0 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = 15

    styleFL = deepcopy(style)
    styleFL.firstLineIndent = 0

    styleSign = deepcopy(style)
    styleSign.firstLineIndent = 0
    styleSign.alignment = TA_LEFT
    styleSign.leading = 13

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleBold.firstLineIndent = 0

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 9
    styleCenter.leading = 10
    styleCenter.spaceAfter = 0 * mm

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.firstLineIndent = 0
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 13
    styleCenterBold.face = 'PTAstraSerifBold'

    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    objs = []

    objs = [
        Paragraph(
            'Информированное добровольное согласие на виды медицинских вмешательств,<br/> включенные в Перечень определенных'
            ' видов медицинских вмешательств,<br/> на которые граждане дают информированное добровольное согласие при '
            'выборе врача и медицинской организации для получения первичной медико-санитарной помощи {} '.format(
                who_patient),
            styleCenterBold),
    ]

    objs.append(Spacer(1, 4 * mm))

    d = datetime.datetime.strptime(person_data['born'], '%d.%m.%Y').date()
    date_individual_born = pytils.dt.ru_strftime(u"\"%d\" %B %Y", inflected=True, date=d)

    objs.append(Spacer(1, 3 * mm))
    objs.append(
        Paragraph('Я, нижеподписавшийся(аяся) {}&nbsp; {} г. рождения'.format(person_data['fio'], date_individual_born),
                  styleSign))

    styleLeft = deepcopy(style)
    styleLeft.alignment = TA_LEFT
    objs.append(Paragraph('Зарегистрированный(ая) по адресу: {}'.format(person_data['main_address']), styleSign))
    objs.append(Paragraph('Проживающий(ая) по адресу: {}'.format(person_data['fact_address']), styleSign))
    objs.append(Paragraph('Документ, удостоверяющий личность {}: серия <u> {}</u> номер: <u>{}</u>'.
                          format(person_data['type_doc'], person_data['passport_serial'], person_data['passport_num']),
                          styleSign))
    objs.append(
        Paragraph('Выдан: {} {}'.format(person_data['passport_date_start'], person_data['passport_issued']), styleSign))
    objs.append(Spacer(1, 3 * mm))

    hospital_name = SettingManager.get("org_title")

    opinion = []
    if agent_status:
        opinion = [
            Paragraph(
                'являюсь законным представителем ({}) {}:'.format(ind_card.get_who_is_agent_display(), who_patient),
                styleBold),
            Paragraph('{}&nbsp; {} г. рождения'.format(patient_data['fio'], patient_data['born']), styleSign),
            Paragraph('Зарегистрированный(ая) по адресу: {}'.format(patient_data['main_address']), styleSign),
            Paragraph('Проживающий(ая) по адресу: {}'.format(patient_data['fact_address']), styleSign)
        ]

        # Проверить возраст пациента при наличии представителя (ребёнок|взрослый)
        if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i'):
            opinion.append(Paragraph('Документ, удостоверяющий личность {}: серия {} номер {}'.
                                     format(patient_data['type_doc'], patient_data['bc_serial'],
                                            patient_data['bc_num']), styleSign))
            opinion.append(
                Paragraph('Выдан: {} {}'.format(patient_data["bc_date_start"], person_data['bc_issued']), styleSign))
        else:
            opinion.append(Paragraph('Документ, удостоверяющий личность {}: серия {} номер {}'.
                                     format(patient_data['type_doc'], patient_data['passport_serial'],
                                            patient_data['passport_num']), styleSign))
            opinion.append(
                Paragraph('Выдан: {} {}'.format(patient_data["passport_date_start"], person_data['passport_issued']),
                          styleSign))

        objs.extend(opinion)

    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph('даю информированное добровольное согласие на виды медицинских вмешательств, включенные в '
                          '\"Перечень\" определенных видов медицинских вмешательств, на которые граждане дают информированное '
                          'добровольное согласие при выборе врача и медицинской организации для получения первичной '
                          'медико-санитарной помощи, утвержденный  приказом  Министерства здравоохранения и социального развития '
                          'Российской Федерации от 23 апреля 2012 г. N 390н (зарегистрирован Министерством  юстиции '
                          'Российской Федерации 5 мая 2012 г. N 24082) (далее - \"Перечень\"), для  получения  первичной '
                          'медико-санитарной помощи <font fontname ="PTAstraSerifBold"> Пациентом: </font> {} '
                          '<font fontname ="PTAstraSerifBold">в Учреждении:</font>  {}'.format(patient_data['fio'],
                                                                                               hospital_name), styleFL))

    space_symbol = '&nbsp;'
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph(
        '<font fontname ="PTAstraSerifBold">Медицинским работником </font><u>{}</u>'.format(115 * space_symbol), style))
    objs.append(
        Paragraph('в доступной для меня форме мне разъяснены цели, методы оказания медицинской помощи, связанный '
                  'с ними риск, возможные варианты медицинских вмешательств, их  последствия,  в  том  числе  '
                  'вероятность  развития  осложнений, а также предполагаемые  результаты оказания медицинской помощи. '
                  'Мне разъяснено, что я  имею  право  отказаться  от  одного  или  нескольких  видов  медицинских вмешательств,  '
                  'включенных в Перечень, или потребовать его (их) прекращения, за  исключением  случаев,  предусмотренных  '
                  'частью 9 статьи 20 Федерального закона  от 21 ноября 2011 г. N 323-ФЗ "Об основах охраны здоровья '
                  'граждан в Российской  Федерации"  (Собрание  законодательства  Российской  Федерации, 2011, '
                  'N 48, ст. 6724; 2012, N 26, ст. 3442, 3446).', styleFL))

    objs.append(
        Paragraph('Сведения  о  выбранных  мною  лицах, которым в соответствии с пунктом 5 части  5  статьи  19 '
                  'Федерального закона от 21 ноября 2011 г. N 323-ФЗ "Об основах охраны здоровья граждан в '
                  'Российской Федерации" может быть передана информация о состоянии {}'.format(''), style))

    styleFCenter = deepcopy(style)
    styleFCenter.alignment = TA_CENTER

    styleBottom = deepcopy(style)
    styleBottom.fontSize = 8

    sign_fio_person = '(Ф.И.О .гражданина, контактный телефон)'
    sign_patient_agent = '(Ф.И.О. гражданина или законного представителя гражданина)'
    sign_fio_doc = '(Ф.И.О. медицинского работника)'

    objs.append(Spacer(1, 9 * mm))
    objs.append(Paragraph('', styleFCenter))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('{} {}'.format(73 * space_symbol, sign_fio_person), styleBottom))

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('{}'.format(person_data['fio']), styleFCenter))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(
        Paragraph('{} (подпись) {} {}'.format(16 * space_symbol, 38 * space_symbol, sign_patient_agent), styleBottom))

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('{}'.format(space_symbol), styleFCenter))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('{} (подпись) {} {}'.format(16 * space_symbol, 38 * space_symbol, sign_fio_doc), styleBottom))

    date_now = pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=datetime.datetime.now())
    objs.append(Spacer(1, 5 * mm))
    objs.append(Paragraph('{} г.'.format(date_now), style))
    objs.append(
        HRFlowable(width=46 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black, hAlign=TA_LEFT))
    objs.append(Paragraph('(дата оформления)', styleBottom))

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


def form_04(request_date):
    """
    отказ от медицинского вмешательства в отношении определенных видов медицинских вмешательств
    --------------------------------------------------------------------------------------------------------------
    Приказ Министерства здравоохранения РФ от 20 декабря 2012 г. N 1177н
    "Об утверждении порядка дачи информированного добровольного согласия на медицинское вмешательство и
    отказа от медицинского вмешательства в отношении определенных видов медицинских вмешательств,
    форм информированного добровольного согласия на медицинское вмешательство и форм отказа
    от медицинского вмешательства" (с изменениями и дополнениями)
    :param request_date:
    :return:
    """
    pass
