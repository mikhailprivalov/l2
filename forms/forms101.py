import datetime
import locale
import os
import sys
from copy import deepcopy
from io import BytesIO

import pytils
import simplejson
from django.utils import timezone, dateformat
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import HRFlowable

from appconf.manager import SettingManager
from clients.models import Individual, Card, Document, CardDocUsage
from hospitals.models import Hospitals
from laboratory import settings
from laboratory.settings import FONTS_FOLDER
from laboratory.utils import strfdatetime, current_time
from slog.models import Log


def form_01(request_data):
    """
    generate form agreement to Hiv
    :param request_data: GET request data
    :return: pdf
    """
    ind = Individual.objects.get(pk=request_data["individual"])
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=10 * mm, bottomMargin=5 * mm, allowSplitting=1, title="Форма {}".format("Согласие на вич")
    )

    pdfmetrics.registerFont(TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSansBold', os.path.join(FONTS_FOLDER, 'OpenSans-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSansItalic', os.path.join(FONTS_FOLDER, 'OpenSans-Italic.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSansBoldItalic', os.path.join(FONTS_FOLDER, 'OpenSans', 'OpenSans-BoldItalic.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSansLight', os.path.join(FONTS_FOLDER, 'OpenSans', 'OpenSans-Light.ttf')))

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
        Paragraph('<font face="OpenSansBold">Информированное согласие<br/>' 'пациента на проведение обследования на ВИЧ-инфекцию</font>', styleCenterBold),
        Spacer(1, 5 * mm),
        Paragraph('<font face="OpenSans">Я, {}</font>'.format(i.fio()), styleCenter),
    ]

    stx = [
        '{} года рождения, настоящим подтверждаю, что на основании представленной мне информации, свободно и без принуждения, отдавая отчет о последствиях обследования, принял решение пройти тестирование на антитела к ВИЧ. Для этой цели я соглашаюсь сдать анализ крови.<br/>'.format(  # noqa: E501
            i.bd()
        ),
        'Я подтверждаю, что мне разъяснено, почему важно пройти тестирование на ВИЧ, как проводится тест и какие последствия может иметь тестирование на ВИЧ.',
        'Я проинформирован, что:',
        '- тестирование на ВИЧ проводится в Центре СПИД и других медицинских учреждениях. Тестирование по моему добровольному выбору может быть добровольным анонимным (без предъявления документов и указания имени) или конфиденциальным (при предъявлении паспорта, результат будет известен обследуемому и лечащему врачу). В государственных медицинских учреждениях тестирование на ВИЧ проводится бесплатно;',  # noqa: E501
        '- доказательством наличия ВИЧ-инфекции является присутствие антител к ВИЧ в крови обследуемого лица. Вместе с тем, в период между заражением и появлением антител к ВИЧ (так называемое "серонегативное окно, обычно 3 месяца) при тестировании не обнаруживаются антитела к ВИЧ и обследуемое лицо может заразить других лиц.',  # noqa: E501
        '- ВИЧ-инфекция передается только тремя путями:',
        '- парентеральный - чаще всего при употреблении наркотиков, но может передаваться также при использовании нестерильного медицинского инструментария, переливании компонентов крови, нанесении татуировок, пирсинге зараженным инструментом, использовании чужих бритвенных и маникюрных принадлежностей;',  # noqa: E501
        '- при сексуальных контактах без презерватива;',
        '- от инфицированной ВИЧ матери к ребенку во время беременности, родов и при грудном вскармливании.',
        '________________________________________________ ___________ (Подпись обследуемого на ВИЧ)',
        'Дата: {}'.format(dateformat.format(timezone.now(), settings.DATE_FORMAT)),
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
    if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i') and not agent_status:
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
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=13 * mm, rightMargin=4 * mm, topMargin=4 * mm, bottomMargin=4 * mm, allowSplitting=1, title="Форма {}".format("Согласие на обработку ПДн")
    )
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
    objs.append(Paragraph('Я, нижеподписавшийся(аяся) {}&nbsp; {} г. рождения'.format(person_data['fio'], date_individual_born), styleSign))

    styleLeft = deepcopy(style)
    styleLeft.alignment = TA_LEFT
    objs.append(Paragraph('Зарегистрированный(ая) по адресу: {}'.format(person_data['main_address']), styleSign))
    objs.append(Paragraph('Проживающий(ая) по адресу: {}'.format(person_data['fact_address']), styleSign))
    objs.append(
        Paragraph(
            'Документ, удостоверяющий личность {}: серия <u> {}</u> номер: <u>{}</u>'.format(person_data['type_doc'], person_data['passport_serial'], person_data['passport_num']), styleSign
        )
    )
    objs.append(Paragraph('Выдан: {} {}'.format(person_data['passport_date_start'], person_data['passport_issued']), styleSign))
    objs.append(Spacer(1, 2 * mm))

    hospital: Hospitals = request_data["hospital"]

    hospital_name = hospital.safe_short_title
    hospital_address = hospital.safe_address

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
    objs.append(
        Paragraph(
            'в соответствии с требованиями федерального закона от 27.07.2006 г. "О персональных данных" '
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
            'хранения результатов исследований для последующего использования в установлении медицинского диагноза.'.format(hospital_name, hospital_address),
            styleFL,
        )
    )
    objs.append(
        Paragraph(
            'Я согласен (согласна) на осмотр с применением телемедицинских технологий, а также на фото - и видеосъемку '
            'в процессе лечения в интересах моего, или лица, представителем которого я являюсь обследования и лечения.',
            style,
        )
    )
    objs.append(
        Paragraph(
            'Предоставляю Оператору право осуществлять любое действие (операцию) или совокупность действий '
            '(операций) с использованием средств автоматизации и/или без использования таких средств с '
            'Персональными данными , включая сбор, запись, '
            'систематизацию, накопление, хранение, уточнение (обновление, изменение), извлечение, использование, '
            'передачу (распространение, предоставление, доступ), обезличивание, блокирование, удаление, уничтожение',
            style,
        )
    )
    objs.append(
        Paragraph(
            'В процессе оказания Оператором медицинской помощи субъекту персональных данных я предоставляю '
            'право медицинским работникам передавать персональные данные, содержащие сведения, составляющие врачебную тайну, '
            'другим должностным лицам Оператора, в интересах обследования и лечения, обслуживания документации, '
            'программного обеспечения и технических средств. Я согласен (согласна) с тем, что доступ к Персональным данным '
            'будут иметь сотрудники Оператора, осуществляющие техническое обслуживание информационной системы.',
            style,
        )
    )
    objs.append(
        Paragraph(
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
            'Настоящее согласие действует со дня его подписания до дня отзыва.',
            style,
        )
    )
    date_year = datetime.datetime.now().strftime('%Y')
    objs.append(Spacer(1, 5 * mm))
    space_bottom = ' &nbsp;'

    styleSign = deepcopy(style)
    styleSign.firstLineIndent = 0
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph('\"___\"____________{} {} _____________________ /______________________ /'.format(date_year, 30 * space_bottom), styleSign))
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
    if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i') and not agent_status:
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
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=5 * mm, allowSplitting=1, title="Форма {}".format("Лист на оплату"))
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
            'выборе врача и медицинской организации для получения первичной медико-санитарной помощи {} '.format(who_patient),
            styleCenterBold,
        ),
    ]

    objs.append(Spacer(1, 4 * mm))

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
            'Документ, удостоверяющий личность {}: серия <u> {}</u> номер: <u>{}</u>'.format(person_data['type_doc'], person_data['passport_serial'], person_data['passport_num']), styleSign
        )
    )
    objs.append(Paragraph('Выдан: {} {}'.format(person_data['passport_date_start'], person_data['passport_issued']), styleSign))
    objs.append(Spacer(1, 3 * mm))

    hospital: Hospitals = request_data["hospital"]

    hospital_name = hospital.safe_short_title

    opinion = []
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
                Paragraph('Документ, удостоверяющий личность {}: серия {} номер {}'.format(patient_data['type_doc'], patient_data['bc_serial'], patient_data['bc_num']), styleSign)
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
    objs.append(
        Paragraph(
            'даю информированное добровольное согласие на виды медицинских вмешательств, включенные в '
            '\"Перечень\" определенных видов медицинских вмешательств, на которые граждане дают информированное '
            'добровольное согласие при выборе врача и медицинской организации для получения первичной '
            'медико-санитарной помощи, утвержденный  приказом  Министерства здравоохранения и социального развития '
            'Российской Федерации от 23 апреля 2012 г. N 390н (зарегистрирован Министерством  юстиции '
            'Российской Федерации 5 мая 2012 г. N 24082) (далее - \"Перечень\"), для  получения  первичной '
            'медико-санитарной помощи <font fontname ="PTAstraSerifBold"> Пациентом: </font> {} '
            '<font fontname ="PTAstraSerifBold">в Учреждении:</font>  {}'.format(patient_data['fio'], hospital_name),
            styleFL,
        )
    )

    space_symbol = '&nbsp;'
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph('<font fontname ="PTAstraSerifBold">Медицинским работником </font><u>{}</u>'.format(115 * space_symbol), style))
    objs.append(
        Paragraph(
            'в доступной для меня форме мне разъяснены цели, методы оказания медицинской помощи, связанный '
            'с ними риск, возможные варианты медицинских вмешательств, их  последствия,  в  том  числе  '
            'вероятность  развития  осложнений, а также предполагаемые  результаты оказания медицинской помощи. '
            'Мне разъяснено, что я  имею  право  отказаться  от  одного  или  нескольких  видов  медицинских вмешательств,  '
            'включенных в Перечень, или потребовать его (их) прекращения, за  исключением  случаев,  предусмотренных  '
            'частью 9 статьи 20 Федерального закона  от 21 ноября 2011 г. N 323-ФЗ "Об основах охраны здоровья '
            'граждан в Российской  Федерации"  (Собрание  законодательства  Российской  Федерации, 2011, '
            'N 48, ст. 6724; 2012, N 26, ст. 3442, 3446).',
            styleFL,
        )
    )

    objs.append(
        Paragraph(
            'Сведения  о  выбранных  мною  лицах, которым в соответствии с пунктом 5 части  5  статьи  19 '
            'Федерального закона от 21 ноября 2011 г. N 323-ФЗ "Об основах охраны здоровья граждан в '
            'Российской Федерации" может быть передана информация о состоянии {}'.format(''),
            style,
        )
    )

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
    objs.append(Paragraph('{} (подпись) {} {}'.format(16 * space_symbol, 38 * space_symbol, sign_patient_agent), styleBottom))

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('{}'.format(space_symbol), styleFCenter))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('{} (подпись) {} {}'.format(16 * space_symbol, 38 * space_symbol, sign_fio_doc), styleBottom))

    date_now = pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=datetime.datetime.now())
    objs.append(Spacer(1, 5 * mm))
    objs.append(Paragraph('{} г.'.format(date_now), style))
    objs.append(HRFlowable(width=46 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black, hAlign=TA_LEFT))
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


def form_05(request_data):
    """
    История изменения данных пациента
    """
    card = Card.objects.get(pk=request_data["card_pk"])
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=10 * mm,
        bottomMargin=5 * mm,
        allowSplitting=1,
        title="История изменения данных пациента. Карта {}".format(card),
    )
    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSansBold', os.path.join(FONTS_FOLDER, 'OpenSans-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSansItalic', os.path.join(FONTS_FOLDER, 'OpenSans-Italic.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSansBoldItalic', os.path.join(FONTS_FOLDER, 'OpenSans', 'OpenSans-BoldItalic.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSansLight', os.path.join(FONTS_FOLDER, 'OpenSans', 'OpenSans-Light.ttf')))

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

    objs = []

    hospital: Hospitals = request_data["hospital"]

    hospital_name = hospital.safe_short_title
    hospital_address = hospital.safe_address

    objs.append(
        Paragraph(
            f'{hospital_name}, {hospital_address}',
            styleCenter,
        )
    )

    objs.append(Spacer(1, 3 * mm))

    objs.append(
        Paragraph(
            f'История изменений данных пациента (генерация {strfdatetime(current_time(), "%d.%m.%Y %H:%M:%S")})',
            styleCenterBold,
        )
    )

    objs.append(Spacer(1, 3 * mm))

    objs.append(
        Paragraph(
            'Текущие данные:',
            style,
        )
    )

    objs.append(
        Paragraph(
            f'Пациент: {card.individual.fio(full=True)}',
            style,
        )
    )

    objs.append(
        Paragraph(
            f'Загруженная карта: {card.number_with_type()}',
            style,
        )
    )

    def b_font_val(s, v):
        return f'<font face="OpenSansBold">{s}:</font> {v}'

    types = [
        (30010, "Данные физлица"),
        (30008, "Данные документов"),
        (30007, "Данные карт"),
        (30009, "Использование документов в картах"),
    ]

    for t, h in types:
        objs.append(Spacer(1, 3 * mm))

        objs.append(
            Paragraph(
                h,
                styleBold,
            )
        )

        if t == 30010:
            keys = [str(card.individual.pk)]
        elif t == 30008:
            keys = [x.pk for x in Document.objects.filter(individual=card.individual)]
        elif t == 30009:
            keys = [x.pk for x in CardDocUsage.objects.filter(card__in=Card.objects.filter(individual=card.individual, is_archive=False))]
        else:
            keys = [x.pk for x in Card.objects.filter(individual=card.individual, is_archive=False)]

        if not keys:
            continue

        qs = Log.objects.filter(key__in=keys, type=t) if len(keys) > 1 else Log.objects.filter(key=keys[0], type=t)
        lg: Log
        for lg in qs.order_by('pk'):
            try:
                data = simplejson.loads(lg.body)
                if not data or not isinstance(data, dict) or "updates" not in data:
                    continue
                rows = [
                    f'{lg.user or "system"} – {strfdatetime(lg.time, "%d.%m.%Y %H:%M:%S")}',
                ]
                cnt = len(data["updates"])
                n = 0
                for row in data["updates"]:
                    n += 1
                    rows += [
                        f'{b_font_val("Поле", row["help_text"])} ({row["field_name"]})',
                        b_font_val("Старое значение", row["from"]),
                        b_font_val("Новое значение", row["to"]),
                    ]
                    if n < cnt:
                        rows.append("")
                rows.append("<br/>")
                objs.append(
                    Paragraph(
                        "<br/>".join(rows),
                        style,
                    )
                )
            except Exception as e:
                print(e)
                pass

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_06(request_data):
    """
    Добровольное согласие на COVID-19
    """
    ind_card = Card.objects.get(pk=request_data["card_pk"])
    person_data = ind_card.get_data_individual()
    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=10 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=5 * mm, allowSplitting=1, title="Форма {}".format("COVID-19 согласие")
    )
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10.5
    style.leading = 10
    style.spaceAfter = 0 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = 10

    styleFL = deepcopy(style)
    styleFL.firstLineIndent = 0

    styleSign = deepcopy(style)
    styleSign.firstLineIndent = 0
    styleSign.alignment = TA_JUSTIFY
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

    objs = [
        Paragraph(
            "COГЛАСИЕНА<br/> ОКАЗАНИЕ МЕДИЦИНСКОЙ ПОМОЩИ В АМБУЛАТОРНЫЙ<br/> УСЛОВИЯХ И СОБЛЮДЕНИЕ РЕЖИМА ИЗОЛЯЦИИ ПРИ ЛЕЧЕНИИ<br/>"
            "НОВОЙ КОРОНАВИРУСНОЙ ИНФЕКЦИИ (COVID-19) В ПЕРИОД<br/>ПОДЪЕМА ЗАБОЛЕВАЕМОСТИ в 2020 - 2021 ГОДУ",
            styleCenterBold,
        )
    ]

    objs.append(Spacer(1, 3 * mm))
    d = datetime.datetime.strptime(person_data['born'], '%d.%m.%Y').date()
    date_individual_born = pytils.dt.ru_strftime(u"\"%d\" %B %Y", inflected=True, date=d)
    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Я, {}&nbsp; {} г. рождения'.format(person_data['fio'], date_individual_born), styleSign))

    styleLeft = deepcopy(style)
    styleLeft.alignment = TA_LEFT

    objs.append(Paragraph('Зарегистрированный(ая) по адресу: {}'.format(person_data['main_address']), styleSign))
    objs.append(Paragraph('Проживающий(ая) по адресу: {}'.format(person_data['fact_address']), styleSign))
    objs.append(Spacer(1, 3 * mm))
    objs.append(
        Paragraph(
            'В соответствии с частью 2 статьи 22 Федерального закона от 21.11.2011 №323-ФЗ «Об основах охраны здоровья граждан в '
            'Российской Федерации» проинформирован(-а) медицинским работником',
            styleSign,
        )
    )

    hospital: Hospitals = request_data["hospital"]

    hospital_name = hospital.safe_short_title

    objs.append(Paragraph(f"<u>{hospital_name}</u>", styleCenterBold))
    objs.append(Paragraph('<br/>_____________________________________________________________________________________', styleSign))
    objs.append(Paragraph('(должность, фамилия, имя, отчество медицинского работника)', styleCenter))
    objs.append(
        Paragraph(
            'О положительном результате лабораторного исследования моего биологического материала на новую коронавирусную инфекцию (COVID-19) и '
            'постановке мне диагноза:заболевание, вызванное новой коронавирусной инфекцией (COVID-19).',
            styleSign,
        )
    )
    objs.append(Spacer(1, 1.5 * mm))
    objs.append(
        Paragraph(
            'По результатам осмотра и оценки  состояния моего здоровья, в связи с течением заболевания в легкой (средней) форме, '
            'медицинским работником в доступной для меня форме была разъяснена возможность оказания медицинской помощи в амбулаторных условиях (на дому), '
            'после чего я выражаю свое согласие на:',
            styleSign,
        )
    )
    objs.append(Paragraph('-получение медицинской помощи в амбулаторных условиях (на дому) по адресу:', styleSign))
    objs.append(Paragraph(f"{person_data['fact_address']}", styleSign))
    objs.append(Paragraph('-соблюдение режима изоляции на период лечения в указанном выше помещении.', styleSign))
    objs.append(Paragraph('Мне разъяснено, что я обязан(-а):', styleSign))
    objs.append(Paragraph('-не покидать указанное помещение, находиться в отдельной, хорошо проветриваемой комнате;', styleSign))
    objs.append(
        Paragraph(
            '-не посещать работу, учебу, магазины, аптеки, иные общественные места и массовые скопления людей, '
            'не пользоваться общественным транспортом, не контактировать с третьими лицами;',
            styleSign,
        )
    )
    objs.append(Paragraph('-при невозможности избежать кратковременного контакта с третьими лицами в обязательном ' 'порядке использовать медицинскую маску;', styleSign))
    objs.append(
        Paragraph(
            '-соблюдать врачебные и санитарные предписания, изложенные в памятках, врученных мне медицинским работником, '
            'а также предписания, которые будут выданы мне медицинскими работниками в течении всего срока лечения;',
            styleSign,
        )
    )
    objs.append(
        Paragraph(
            '-при первых признаках ухудшения самочувствия (повышение температуры, кашель, затрудненное дыхание) обратиться за медицинской помощью ' 'и не допускать самолечения;', styleSign
        )
    )
    objs.append(Paragraph('-сдать пробы для последующего лабораторного контроля при посещении меня медицинским работником на дому.', styleSign))
    objs.append(Spacer(1, 1.5 * mm))
    objs.append(
        Paragraph(
            'Медицинским работником мне разъяснено, что новая коронавирусная инфекция (COVID-19) представляет опасность для окружающих, '
            'в связи с чем при возможном контакте со мной третьи лица имеют высокий риск заражения, что особо опасно для людей старшего возраста, '
            'а также людей, страдающих хроническими заболеваниями.',
            styleSign,
        )
    )
    objs.append(Spacer(1, 1.5 * mm))
    objs.append(
        Paragraph(
            'Я предупрежден(а), что нарушение санитарно-эпидемиологических правил, повлекшее по неосторожности массовое заболевание, '
            'может повлечь привлечение к уголовной ответственности, предусмотренной статьей 236 Уголовного кодекса Российской Федерации.',
            styleSign,
        )
    )
    objs.append(Spacer(1, 1.5 * mm))
    objs.append(
        Paragraph(
            'Медицинским работником мне предоставлены информационные материалы по вопросам ухода за пациентами – '
            'больными новой коронавирусной инфекцией (COVID-19) и общим рекомендациям по защите от инфекций, передающихся воздушно-капельным и '
            'контактным путем, их содержание мне разъяснено и полностью понятно',
            styleSign,
        )
    )

    objs.append(Spacer(1, 1.5 * mm))
    objs.append(
        Paragraph(
            'Я проинформирован(а) о том, что в случае отказа от подписания настоящего согласия, за мной сохраняется право повторно '
            'обратиться в медицинскую организацию по месту жительства для предоставления лекарственного обеспечения до получения '
            'второго отрицательного результата лабораторного исследования на новую коронавирусную инфекцию (COVID-19).',
            styleSign,
        )
    )

    space_symbol = '&nbsp;'
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
    objs.append(Paragraph('{} (подпись) {} {}'.format(16 * space_symbol, 38 * space_symbol, sign_patient_agent), styleBottom))

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('{}'.format(space_symbol), styleFCenter))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('{} (подпись) {} {}'.format(16 * space_symbol, 38 * space_symbol, sign_fio_doc), styleBottom))

    date_now = pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=datetime.datetime.now())
    objs.append(Spacer(1, 5 * mm))
    objs.append(Paragraph('{} г.'.format(date_now), style))
    objs.append(HRFlowable(width=46 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black, hAlign=TA_LEFT))
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

                          
def form_09(request_data):
    """
    ИНФОРМИРОВАННОЕ СОГЛАСИЕ ПАЦИЕНТА
    на медикаментозное прерывание беременности в I триместре
    """
    ind_card = Card.objects.get(pk=request_data["card_pk"])
    patient_data = ind_card.get_data_individual()

    agent_status = False
    if ind_card.who_is_agent:
        p_agent = getattr(ind_card, ind_card.who_is_agent)
        agent_status = True

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

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    # Генерировать pdf-Лист 
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=13 * mm,
        rightMargin=4 * mm,
        topMargin=4 * mm,
        bottomMargin=4 * mm,
        allowSplitting=1,
        title="Форма {}".format("СОГЛАСИЕ ПАЦИЕНТА на прерывание беременности в I триместре")
    )
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

    objs = [
        Paragraph('ИНФОРМИРОВАННОЕ СОГЛАСИЕ ПАЦИЕНТА <br/> на медикаментозное прерывание беременности в I триместре {}'.format(who_patient), styleCenterBold),
    ]

    d = datetime.datetime.strptime(person_data['born'], '%d.%m.%Y').date()
    date_individual_born = pytils.dt.ru_strftime(u"\"%d\" %B %Y", inflected=True, date=d)

    objs.append(Spacer(1, 3 * mm))
    objs.append(
        Paragraph('Я, {}&nbsp; {} г. рождения подтверждаю,'
                  'что приняла решение о прерывании беременности (аборт).'.format(person_data['fio'], date_individual_born), style))

    styleLeft = deepcopy(style)
    styleLeft.alignment = TA_LEFT

    objs.append(
        Paragraph(
            'Я проинформирована врачом о нижеследующем: ',
            style,
        )
    )
    objs.append(
        Paragraph(
            '- о сроке моей беременности, об отсутствии у меня противопоказаний к вынашиванию данной '
            'беременности и рождению ребенка;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- о сути метода медикаментозного прерывания беременности;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- о том, что в процессе медикаментозного аборта могут отмечаться побочные эффекты: тошнота, рвота, '
            'диарея, боли внизу живота, но все эти эффекты временные;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- медикаментозный аборт сопровождается кровяными выделения из половых путей, которые могут'
            'быть более сильными, чем во время обычной менструации;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- о необходимости прохождения медицинского обследования для контроля за состоянием '
            'здоровья в течение времени, пока аборт не завершится, в соответствии с назначением лечащего врача;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- метод медикаментозного способа прерывания беременности включает: прием 1 таблетки или 3 '
            'таблеток мифепристона и, спустя 36-48 часов, прием 2-х таблеток в сроке до 49 дней задержки или 4  '
            'таблеток в сроке от 49 до 63 дней задержки сокращающего матку препарата - мизопростола. Прием  '
            'препаратов осуществляется в лечебном учреждении в присутствии врача. ',
            style,
        )
    )

    objs.append(
        Paragraph(
            'Мне даны разъяснения:',
            style,
        )
    )
    objs.append(
        Paragraph(
            '- о том, что при условии строжайшего соблюдения соответствующих норм и правил в 2-5 % случаев '
            'медикаментозное прерывание беременности может быть неэффективным (остатки плодного яйца, '
            'прогрессирующая беременность, кровотечение), и в этой ситуации  необходимо завершить аборт'
            'хирургическим путем.',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- о том, что если я приму решение сохранить беременность в случае ее продолжающегося  развития '
            'после медикаментозного аборта, то существует риск для здоровья будущего ребенка.',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- о возможной необходимости приема дополнительных лекарственных препаратов в  соответствии с '
            'предписанием моего лечащего врача;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- о режиме поведения, в том числе половой жизни, в послеабортном периоде и возможных'
            'последствиях при его нарушении.',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- о возможности и целесообразности использования в дальнейшем средств предупреждения '
            'нежелательной беременности. ',
            style,
        )
    )

    objs.append(
        Paragraph(
            'Я, {}  хочу прервать беременость,'
            'медикаментозным способом. Я прочитала и понимаю все, о чем говорится в данном '
            'информационном согласии. На все свои вопросы я получила ответы. Я знаю, куда я могу обратиться в '
            'случае, если мне понадобится неотложная медицинская помощь'.format(person_data['fio']), 
            style,
        )
    )

    space_bottom = ' &nbsp;'

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Пациент {0} {1}'.format(20 * space_bottom, person_data['fio']), style))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('<font size=9 >{0}(Ф.И.О.){1}(Подпись)</font size>'.format(38 * space_bottom, 40 * space_bottom), style))

    objs.append(
        Paragraph(
            'Я свидетельствую, что разъяснил пациентке суть, ход выполнения, риск и альтернативу '
            'проведения медикаментозного аборта, дал ответы на все вопросы.',
            style,
        )
    )

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Врач', style))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('<font size=9 >{0}(Ф.И.О.){1}(Подпись)</font size>'.format(38 * space_bottom, 40 * space_bottom), style))

    date_year = datetime.datetime.now().strftime('%Y')
    objs.append(Spacer(1, 5 * mm))

    styleSign = deepcopy(style)
    styleSign.firstLineIndent = 0
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph('\"___\"____________{} '.format(date_year), styleSign))
 
    objs.append(PageBreak())  # Генерировать втрое согласие pdf-Лист 

    objs.append(
        Paragraph('ИНФОРМИРОВАННОЕ ДОБРОВОЛЬНОЕ СОГЛАСИЕ НА <br/> ПРОВЕДЕНИЕ ИСКУССТВЕННОГО ПРЕРЫВАНИЯ  <br/> БЕРЕМЕННОСТИ ПО ЖЕЛАНИЮ ЖЕНЩИНЫ', styleCenterBold),
    )

    objs.append(Spacer(1, 3 * mm))
    objs.append(
        Paragraph('Я, ниже подписавшаяся {}&nbsp; {} г. рождения,'
                  'в соответствии со статьями 20 и 56 .'
                  'Федерального закона от 21 ноября 2011 г. N 323-ФЗ "Об основах охраны здоровья '
                  'граждан в Российской Федерации" настоящим подтверждаю свое согласие на проведение '
                  'мне искусственного прерывания беременности (нужное подчеркнуть):'.format(person_data['fio'], date_individual_born), style))

    objs.append(
        Paragraph(
            '- медикаментозным методом;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- путем хирургической операции с разрушением и удалением плодного яйца (эмбриона '
            'человека), которая проводится под обезболиванием.',
            style,
        )
    )

    objs.append(
        Paragraph(
            '1. Перед направлением на искусственное прерывание беременности мне предоставлено '
            'время для обдумывания и принятия окончательного решения в течение (нужное '
            'подчеркнуть):',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- 48 часов;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- 7 дней.<sup><small>1</small></sup>',
            style,
        )
    )

    objs.append(
        Paragraph(
            'В течение указанного периода:',
            style,
        )
    )

    objs.append(
        Paragraph(
            'Я проинформирована о сроке моей беременности, об отсутствии у меня медицинских '
            'противопоказаний к вынашиванию данной беременности и рождению ребенка;',
            style,
        )
    )

    objs.append(
        Paragraph(
            'мне проведено / не проведено (нужное подчеркнуть) ультразвуковое исследование (далее - '
            'УЗИ) органов малого таза, в процессе которого продемонстрировано изображение '
            'мэмбриона и его сердцебиение (при наличии сердцебиения)<sup><small>2</small></sup>: "___"__________ 20__ г '
            '(указать дату проведения согласно отметке в медицинской документации или дату отказа '
            'от медицинского вмешательства, оформленного в установленном порядке);',
            style,
        )
    )

    objs.append(
        Paragraph(
            'я проконсультирована психологом (медицинским психологом, специалистом по '
            'социальной работе) по вопросам психологической и социальной поддержки.',
            style,
        )
    )
    objs.append(
        Paragraph(
            '2. Я проинформирована врачом-акушером-гинекологом:',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- о том, что имею право не делать'
            'искусственное прерывание беременности и не прерывать беременность;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- о том, что при условии строжайшего соблюдения правил проведения искусственного '
            'прерывания беременности могут возникнуть следующие осложнения;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- бесплодие',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- хронические воспалительные процессы матки и (или) придатков матки; нарушение '
            'функции яичников; тазовые боли; внематочная беременность; невынашивание'
            'беременности; различные осложнения при вынашивании последующей беременности и в'
            'родах - преждевременные роды, различные осложнения родовой деятельности,'
            'кровотечение в родах и (или) послеродовом периоде; психические расстройства; '
            'опухолевые процессы матки;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- скопление крови в полости матки; остатки плодного яйца в полости матки, острый и (или)'
            'подострый воспалительный процесс матки и (или) придатков матки, вплоть до '
            'перитонита, что потребует повторного оперативного вмешательства, не исключая '
            'удаления придатков матки и матки;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- во время проведения искусственного прерывания беременности:',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- травма и прободение матки с возможным ранением внутренних органов и кровеносных сосудов;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- кровотечение, что может потребовать расширения объема операции вплоть до '
            'чревосечения и удаления матки, хирургического вмешательства на внутренних органах.',
            style,
        )
    )

    objs.append(
        Paragraph(
            'Мне даны разъяснения врачом-акушером-гинекологом о:',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- механизме действия назначаемых мне перед проведением и во время проведения '
            'искусственного прерывания беременности лекарственных препаратов для медицинского '
            'применения и возможных осложнениях при их применении;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- основных этапах обезболивания;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- необходимости прохождения медицинского обследования для контроля за состоянием '
            'моего здоровья после проведения искусственного прерывания беременности;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- необходимости приема лекарственных препаратов для медицинского применения в '
            'соответствии с назначениями лечащего врача;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- режиме поведения, в том числе половой жизни, гигиенических мероприятиях после '
            'проведения искусственного прерывания беременности и возможных последствиях в '
            'случае несоблюдения рекомендаций;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- методах предупреждения нежелательной беременности;',
            style,
        )
    )

    objs.append(
        Paragraph(
            '- сроках контрольного осмотра врачом-акушером-гинекологом.',
            style,
        )
    )

    objs.append(Paragraph('<br/>_________________________________________________________________________________________________', styleSign))

    objs.append(
        Paragraph(
            '<font size=9 > <sup><small>1</small></sup> Часть 3 статьи 56 Федерального закона от 21 ноября 2011 г. № 323-ФЗ "Об основах </font>'
            '<font size=9 >охраны здоровья граждан в Российской Федерации".</font>',
            style,
        )
    )

    objs.append(
        Paragraph(
            '<font size=9 ><sup><small>2</small></sup> Пункт 106 Порядка оказания медицинской помощи по профилю "акушерство и </font>'
            '<font size=9 >гинекология (за исключением использования вспомогательных репродуктивных </font>'
            '<font size=9 >технологий)", утвержденного приказом Министерства здравоохранения Российской </font>'
            '<font size=9 >Федерации от 1 ноября. 2012 г. № 572н (зарегистрирован Министерством юстиции </font>'
            '<font size=9 >Российской Федерации 2 апреля 2013 г., регистрационный № 27960), с изменениями, </font>'
            '<font size=9 >внесенными приказами Министерства здравоохранения Российской Федерации от 17 </font>'
            '<font size=9 >января 2014 г. N 25н (зарегистрирован Министерством юстиции Российской Федерации </font>'
            '<font size=9 >19 марта 2014 г., регистрационный N 31644), от 11 июня 2015 г. № 333н (зарегистрирован </font>'
            '<font size=9 >Министерством юстиции Российской Федерации 10 июля 2015 г., регистрационный № </font>'
            '<font size=9 >37983) и от 12 января 2016 г. N 5н (зарегистрирован Министерством юстиции Российской </font>'
            '<font size=9 >Федерации 10 февраля 2016 г., регистрационный № 41053). </font>',
            style,
        )
    )

    objs.append(PageBreak())  # Генерировать третью страницу

    objs.append(
        Paragraph(
            '4. Я имела возможность задавать любые вопросы и на все вопросы получила '
            'исчерпывающие ответы. Мне разъяснены возможность не прибегать к искусственному '
            'прерыванию беременности и предпочтительность сохранения и вынашивания '
            'беременности и рождения ребенка.',
            style,
        )
    )

    objs.append(
        Paragraph(
            '5. ЗАКЛЮЧЕНИЕ.',
            style,
        )
    )

    objs.append(
        Paragraph(
            'Получив полную информацию о возможных последствиях и осложнениях в связи с '
            'проведением искусственного прерывания беременности, я подтверждаю, что мне понятен '
            'смысл всех терминов, на меня не оказывалось давление и я осознанно принимаю решение'
            'о проведении мне искусственного прерывания беременности.',
            style,
        )
    )

    space_bottom = ' &nbsp;'

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Пациент {0} {1}'.format(20 * space_bottom, person_data['fio']), style))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('<font size=9 >{0}(Ф.И.О.){1}(Подпись)</font size>'.format(38 * space_bottom, 40 * space_bottom), style))

    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph('Дата \"___\"____________{} '.format(date_year), styleSign))

    objs.append(
        Paragraph(
            '6. Я свидетельствую, что разъяснил пациентке суть, ход выполнения, негативные '
            'последствия проведения искусственного прерывания беременности, возможность не '
            'прибегать к нему и предпочтительность вынашивания беременности и рождения ребенка, '
            'дал ответы на все вопросы..',
            style,
        )
    )

    objs.append(
        Paragraph(
            '7. Подтверждаю, что рекомендовал пациентке проведение УЗИ органов малого таза для '
            'демонстрации изображения эмбриона и его сердцебиения (при наличии сердцебиения).',
            style,
        )
    )

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Врач акушер-гинеколог {0}'.format(20 * space_bottom), style))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('<font size=9 >{0}(Ф.И.О.){1}(Подпись)</font size>'.format(38 * space_bottom, 40 * space_bottom), style))

    styleSign = deepcopy(style)
    styleSign.firstLineIndent = 0
    objs.append(Spacer(1, 2 * mm))
    objs.append(Paragraph('\"___\"____________{} '.format(date_year), styleSign))

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

