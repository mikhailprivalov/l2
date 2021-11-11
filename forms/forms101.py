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
    """
    ind_card = Card.objects.get(pk=request_data["card_pk"])
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

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    # Генерировать pdf-Лист на оплату
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    hospital_name = SettingManager.get("org_title")
    hospital_address = SettingManager.get("org_address")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=5 * mm, allowSplitting=1, title="Форма {}".format("информированное добровольное согласие на медицинское вмешательство"))
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

    objs = [
        Paragraph(
            'Информированное добровольное согласие на медицинское вмешательство<br/>'
			'(для лиц старше 15 лет)'.format(who_patient),
            styleCenterBold,
        ),
    ]

    objs.append(Spacer(1, 4 * mm))

    d = datetime.datetime.strptime(person_data['born'], '%d.%m.%Y').date()
    date_individual_born = pytils.dt.ru_strftime(u"\"%d\" %B %Y", inflected=True, date=d)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Я, {}&nbsp; {} г. рождения'.format(person_data['fio'], date_individual_born), styleSign))
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
            'Даю свое добровольное согласие на госпитализацию в _____________________________ отделение '
			'в условиях ___________________________________________________________________________ '
			'в целях ______________________________________________________________________________ ',
            styleSign,
        )
    )

    space_symbol = '&nbsp;'
    objs.append(Spacer(5, 5 * mm))
    objs.append(
        Paragraph(
            'Даю  свое добровольное согласие (основанное на  полной и всесторонней информации о целях, методах '
            'оказания медицинской помощи, связанном с ними риске, возможных вариантах медицинского вмешательства, о '
            'их последствиях, а также о предполагаемых результатах оказания медицинской помощи) на диагностику и/или '
            'лечение и/или профилактику моего заболевания (состояния) ___________________________________________________'
			'____________________________________________________________________________________________________________',
            styleFL,
        )
    )

    space_symbol = '&nbsp;'
    objs.append(Spacer(0, 0 * mm))
    objs.append(
        Paragraph(
            'заболевание (состояние) вписывается медицинским работником',
            styleCenter,
        )
    )
	
    space_symbol = '&nbsp;'
    objs.append(Spacer(0, 0 * mm))
    objs.append(
        Paragraph(
			'_____________________________________________________________________________________'
			'_____________________________________________________________________________________',
            styleFL,
        )
    )

    space_symbol = '&nbsp;'
    objs.append(Spacer(0, 0 * mm))
    objs.append(
        Paragraph(
            'указываются цель, методы, риски, варианты мед.вмешательства, последствия, предполагаемые результаты(заполняется медицинским работником)',
            styleCenter,
        )
    )
    
    objs.append(Spacer(4, 4 * mm))
    objs.append(
        Paragraph(
            '1.	Я информирован(а) о цели моей госпитализации; <br/>'
            '2.	Мне разъяснены и понятны мои права и обязанности в сфере охраны здоровья: <br/>'
            '3. Я добровольно даю согласие на проведение мне предварительных медицинских вмешательств '
			'(опрос, в том числе выявление жалоб, сбор анамнеза, осмотр, в том числе пальпация, перкуссия,' 
			'аускультация, и иные медицинские вмешательства, связанные с госпитализацией); <br/>'
			'4. Мне, согласно моей воле, даны полные и всесторонние разъяснения о характере, степени '
			'тяжести и возможных осложнениях моего заболевания;<br/>'
			'5.	Я ознакомлен(а) с распорядком и правилами лечебно-охранительного режима, установленного '
			'в ГБУЗ ИГОДКБ, и обязуюсь неукоснительно их соблюдать; <br/>'
			'6.	Я добровольно даю согласие на проведение мне (моему представляемому) в соответствии с '
			'назначениями врача диагностических исследований: анализа крови общего и биохимического, '
			'иммунологического, в том числе исследований крови на наличие вирусных гепатитов, бледной '
			'трепонемы, анализа мочи общего и др. видов исследования мочи, бактериологическое, бактериоскопическое '
			'исследование биологического матерала,  электрокардиографии, электронейромиографии, электроэнцефалографии, '
			'проведения рентгеновских, радиологических, КТ, MPT, МСКТ, ультразвуковых исследований <br/>'
			'7. Я добровольно даю согласие на проведение мне в соответствии с назначениями врача лечебных мероприятий: '
			'прием таблетированных препаратов, инъекций, внутривенных вливаний, нанесение на кожу и слизистые лекарственных '
			'препаратов, физиотерапевтических процедур, массажа и ЛФК, бальнеотерапии, перевязки, в том числе с применением '
			'лекарственных препаратов, повязок разного типа и назначения. <br/>'
			'8. Я понимаю, что необходимость в других методах обследования и лечения будет мне разъяснена дополнительно.<br/>'
			'9. Я информирован(а) о целях, характере и неблагоприятных эффектах диагностических и лечебных процедур, возможности '
			'непреднамеренного причинения вреда здоровью, а также о том, что предстоит мне делать во время их проведения.<br/>'
			'10. Я извещен(а), о том, что мне необходимо регулярно принимать назначенные лекарственные препараты и другие методы '
			'лечения, при необходимости немедленно сообщить врачу о любом ухудшении самочувствия, согласовывать с врачом прием '
			'любых, не прописанных им лекарств.<br/>'
			'11. Я предупрежден(а) и осознаю, что отказ от лечения, несоблюдение лечебно-охранительного режима, рекомендаций '
			'медицинских работников, режима приема препаратов, самовольное использование медицинского инструментария и оборудования, '
			'бесконтрольное самолечение могут осложнить процесс лечения и отрицательно сказаться на состоянии здоровья.<br/>'
			'12. Я поставил(а) в известность врача обо всех проблемах, связанных моего здоровья, в том числе об аллергических '
			'проявлениях и/или индивидуальной непереносимости лекарственных препаратов, обо всех перенесенных мною (им) и известных '
			'мне травмах, операциях, заболеваниях, об экологических факторах физической, химической или биологической природы, '
			'воздействующих на меня во время жизнедеятельности, о принимаемых лекарственных средствах. <br/>'
			'13. разрешаю, в случае необходимости, предоставить информацию о моем диагнозе, степени тяжести и характере заболевания '
			'законным представителям, и другим гражданам:____________________________________________<br/>'
			'14. Я ознакомлен(а) и согласен(а) со всеми пунктами настоящего документа, положения которого мне разъяснены, мне понятны.<br/>',
            styleFL,
        )
    )

    styleFCenter = deepcopy(style)
    styleFCenter.alignment = TA_CENTER

    styleBottom = deepcopy(style)
    styleBottom.fontSize = 8

    sign_fio_person = '(Ф.И.О .гражданина, контактный телефон)'
    sign_patient_agent = '(Ф.И.О. гражданина или законного представителя гражданина)'
    sign_fio_doc = '(Ф.И.О. медицинского работника)'

  # objs.append(Spacer(1, 9 * mm))
  # objs.append(Paragraph('', styleFCenter))
  # objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
  # objs.append(Paragraph('{} {}'.format(73 * space_symbol, sign_fio_person), styleBottom)) 

    objs.append(Spacer(4, 4 * mm))
    objs.append(Paragraph('{}'.format(person_data['fio']), styleFCenter))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('{} (подпись) {} {}'.format(16 * space_symbol, 38 * space_symbol, sign_patient_agent), styleBottom))

  # objs.append(Spacer(1, 3 * mm))
  # objs.append(Paragraph('{}'.format(space_symbol), styleFCenter))
  # objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
  # objs.append(Paragraph('{} (подпись) {} {}'.format(16 * space_symbol, 38 * space_symbol, sign_fio_doc), styleBottom))

    date_now = pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=datetime.datetime.now())
    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('{} г.'.format(date_now), style))
    objs.append(HRFlowable(width=46 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black, hAlign=TA_LEFT))
    objs.append(Paragraph('(дата оформления)', styleBottom))

    space_symbol = '&nbsp;'
    objs.append(Spacer(2, 2 * mm))
    objs.append(
        Paragraph(
            'Дополнительная информация',
            styleBold,
        )
    )
    
    objs.append(Spacer(1, 1 * mm))
    objs.append(
        Paragraph(
            '_____________________________________________________________________________________'
			'_____________________________________________________________________________________'
			'_____________________________________________________________________________________<br/><br/>'
			'Примечание: Согласие на медицинское вмешательство в отношении лиц, не достигших возраста '
			'15 лет, и граждан, признанных в установленном законом порядке недееспособными, дают их законные '
			'представители (родители, усыновители, опекуны или попечители) с указанием Ф.И.О., паспортных '
			'данных, родственных отношений после сообщения им сведений о результатах обследования, наличии '
			'заболевания, его диагнозе и прогнозе, методах лечения, связанном с ними риске, возможных вариантах '
			'медицинского вмешательства, их последствиях и результатах проведенного лечения.<br/>'
			'При отсутствии законных представителей решение о необходимости диагностики и/или лечения и/или '
			'профилактики заболевания (состояния) принимает консилиум, а при невозможности собрать консилиум – '
			'непосредственно лечащий (дежурный) врач с последующим уведомлением главного врача/руководителя ЛПУ, '
			'а в выходные, праздничные дни, вечернее и ночное время – ответственного дежурного врача и законных представителей.<br/>'
			'В случаях, когда состояние гражданина не позволяет ему выразить свою волю, а необходимость  диагностики '
			'и/или лечение и/или профилактики заболевания (состояния) неотложна, вопрос  диагностики и/или лечение и/или '
			'профилактики заболевания (состояния) в интересах гражданина решает консилиум, а при невозможности собрать '
			'консилиум – непосредственно лечащий (дежурный) врач с последующим уведомлением главного врача/ руководителя ЛПУ, '
			'а в выходные, праздничные дни, вечернее и ночное время – ответственного дежурного врача.<br/>'
			'15. Я согласен(а) на осмотр другими медицинскими работниками и студентами медицинских вузов и колледжей '
			'исключительно в медицинских, научных или обучающих целях с учетом сохранения врачебной тайны;<br/>'
			'16. Я согласен(а) / не согласен(а) (ненужное зачеркнуть)  на обсуждение моего состояния здоровья, диагноза, '
			'данных результатов обследований в ходе прикроватного клинического обхода медицинским персоналом в  присутствии '
			'студентов, клинических ординаторов, врачей курсантов, пациентов и их законных представителей в палате во '
			'время врачебного обхода.<br/>',
            styleFL,
        )
    )
	
    objs.append(
        Paragraph(
			'<br/>Расписался в моем присутствии:',
			styleBold,
		)
	)
  
    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('{}'.format(space_symbol), styleFCenter))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('{} (подпись) {} {}'.format(16 * space_symbol, 38 * space_symbol, sign_fio_doc), styleBottom))
	
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
        (30007, "Данные карты"),
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
                print(e)  # noqa: T001
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
            '3. Мне даны разъяснения врачом-акушером-гинекологом о:',
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


def form_10(request_data):
    """
    Карта учета профилактического медицинского осмотра (диспансеризации)
    """                      
    ind_card = Card.objects.get(pk=request_data["card_pk"])
    patient_data = ind_card.get_data_individual()

    hospital: Hospitals = request_data["hospital"]
    hospital_name = hospital.safe_short_title
    hospital_address = hospital.safe_address
    agent_status = False
    if ind_card.who_is_agent:
        p_agent = getattr(ind_card, ind_card.who_is_agent)
        agent_status = bool(p_agent)

    if agent_status:
        person_data = p_agent.get_data_individual()
    else:
        person_data = patient_data

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

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
        title="Форма {}".format("Карта учета профилактического медицинского осмотра (диспансеризации)")
    )
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10
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
    style.fontSize = 10

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleBold.firstLineIndent = 0

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 9
    styleCenter.leading = 10
    styleCenter.spaceAfter = 0 * mm

    styleRight = deepcopy(style)
    styleRight.aligment = TA_RIGHT

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

    styleT = deepcopy(style)
    styleT.firstLineIndent = 0

    styleSingBold = deepcopy(styleSign)
    styleSingBold.fontName = "PTAstraSerifBold"

    styleSmallFont = deepcopy(style)
    styleSmallFont.fontSize = 7

    objs = []
    opinion = [
        [
            Paragraph('', style),
            Paragraph('<b>Приложение №1<br/> к приказу Министерства здравоохранения<br/>Российской Федерации<br/>от 10 ноября 2020 г. N 1207н</b>', styleSingBold),
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

    opinion = [
        [
            Paragraph('Наименование медицинской организации', style),
            Paragraph('Код формы по ОКУД _______________ <br/> Код организации по ОКПО __________', styleSign),
        ],
        [
            Paragraph('{}»'.format(hospital_name), style),
            Paragraph('Медицинская документация Учетная форма N 131/у', styleSign),
        ],
        [
            Paragraph('Адрес: {}'.format(hospital_address), style),
            Paragraph('Утверждена приказом Минздрава России от "__"___ 2020__ г. N ___', styleSign),
        ],
    ]
    tbl = Table(opinion, 2 * [100 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )                   

    objs.append(tbl)

    objs.append(Paragraph('Карта учета <br/> профилактического медицинского осмотра (диспансеризации)', styleCenterBold,))
    objs.append(Paragraph('1. Дата начала профилактического медицинского осмотра (диспансеризации) "___"___________ 20__ г. ', style,))

    d = datetime.datetime.strptime(person_data['born'], '%d.%m.%Y').date()
    date_individual_born = pytils.dt.ru_strftime(u"\"%d\" %B %Y", inflected=True, date=d)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('2. Фамилия, имя, отчество (при наличии): {}&nbsp; {} г. рождения'.format(person_data['fio'], date_individual_born), style))
    objs.append(Paragraph('3. Пол: <u>{}</u> '.format(patient_data['sex']), style,))
    objs.append(Paragraph('4. Дата рождения  <u>{}</u> '.format(date_individual_born), style,))
    objs.append(Paragraph('5. Местность: городская - 1, сельская - 2 ', style,))
    objs.append(Paragraph('6. Адрес регистрации по месту жительства {}'.format(person_data['fact_address']), style,))
    objs.append(Paragraph('7. Код категории льготы: _____________', style,))
    objs.append(Paragraph('8. Принадлежность к коренным малочисленным народам Севера, Сибири и Дальнего Востока Российской Федерации:да - 1; нет - 2', style,))
    objs.append(Paragraph('9. Занятость: 1 - работает; 2 - не работает; 3 - обучающийся в образовательной организации по очной форме', style,))
    objs.append(Paragraph('10. Профилактический медицинский осмотр (первый этап диспансеризации) проводится мобильной медицинской бригадой: да - 1; нет – 2', style,))
    objs.append(Paragraph('11. Результаты исследований и иных медицинских вмешательств, выполненных при проведении профилактического медицинского осмотра '
                          '(первого этапа диспансеризации):', style))
    objs.append(Spacer(1, 2 * mm))

    styleTCenter = deepcopy(styleT)
    styleTCenter.alignment = TA_CENTER
    styleTCenter.leading = 3.5 * mm

    opinion = [
        [
            Paragraph('Рост ___см ', styleTCenter),
            Paragraph('Масса тела ____ кг', styleTCenter),
            Paragraph('индекс массы тела _______ кг/м<sup><small>2</small></sup>', styleTCenter),
        ],
        [
            Paragraph('артериальное давление на периферических артериях __________ мм рт.ст. ', styleSign),
            Paragraph('прием гипотензивных лекарственных препаратов:да      нет', styleSign),
            Paragraph('внутриглазное давление _____ мм рт.с', styleSign),
        ],
        [
            Paragraph('Сатурация ____ ___% ', styleSign),
        ],
        [
            Paragraph('уровень общего холестери на в крови _____ ммоль/л ', styleSign),
            Paragraph('прием гипогликемических лекарственных препаратов: да      нет', styleSign),
            Paragraph('уровень глюкозы в крови натощак _____ ммоль/л', styleSign),
        ],
        [
            Paragraph('прием гиполипидемических лекарственных препаратов: да      нет', styleSign),
            Paragraph(
                'относительный сердечно-сосудистый риск (от 18 лет до 39 лет) _____ %<br/>'
                'абсолютный сердечно-сосудистый риск (от 40 лет до 64 лет включительно) _____ %', 
                styleSign
            ),
        ],
    ]

    row_height = []
    for i in opinion:
        row_height.append(16 * mm)
    row_height[4] = None
    row_height[3] = None
    row_height[2] = None
    row_height[1] = None
    row_height[0] = None

    tbl = Table(opinion, colWidths=(40 * mm, 30 * mm, 75 * mm), rowHeights=row_height)

    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                ('SPAN', (1, 4), (2, 4)),
            ]
        )
    )

    objs.append(tbl)

    styleLeft = deepcopy(style)
    styleLeft.alignment = TA_LEFT

    objs.append(Paragraph(
        '12. Сведения о проведенных приёмах (осмотрах, консультациях), исследованиях и иных медицинских'
        ' вмешательствах при профилактическом медицинском осмотре (на первом этапе диспансеризации)', 
        style
    ))
    objs.append(Spacer(1, 2 * mm))

    opinion = [
        [
            Paragraph(
                'Приём (осмотр, консультация), исследование и иное медицинское вмешательство, входящее'
                ' в объем профилактического медицинского осмотра / первого этапа диспансеризации', 
                styleTCenter
            ),
            Paragraph('', styleTCenter),
            Paragraph('N строки', styleTCenter),
            Paragraph('Отметка о проведении (дата/(-)', styleTCenter),
            Paragraph('Примечание', styleTCenter),
            Paragraph('', styleSign),
            Paragraph('Выявлено патологическое состояние (+/-)', styleTCenter),
        ],
        [
            Paragraph('', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph('Отказ от проведения (+/-)', styleTCenter),
            Paragraph('Проведено ранее (дата)', styleTCenter),
            Paragraph('', styleTCenter),
        ],
        [
            Paragraph('1', styleTCenter),
            Paragraph('', styleSign),
            Paragraph('2', styleTCenter),
            Paragraph('3', styleTCenter),
            Paragraph('4', styleTCenter),
            Paragraph('5', styleTCenter),
            Paragraph('6', styleTCenter),
        ],
        [
            Paragraph('Опрос (анкетирование), 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('01', styleTCenter),
        ],
        [
            Paragraph('Расчет на основании антропометрии (измерение роста, массы тела, окружности талии) индекса массы тела, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('02', styleTCenter),
        ],
        [
            Paragraph('Измерение артериального давления на периферических артериях, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('03', styleTCenter),
        ],
        [
            Paragraph('Определение уровня общего холестерина в крови, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('04', styleTCenter),
        ],
        [
            Paragraph('Определение уровня глюкозы в крови натощак, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('05', styleTCenter),
        ],
        [
            Paragraph('Определение относительного сердечно-сосудистого риска у граждан в возрасте от 18 до 39 лет включительно, 1 раз год', styleSign),
            Paragraph('', styleSign),
            Paragraph('06', styleTCenter),
        ],
        [
            Paragraph('Определение абсолютного сердечно-сосудистого риска у граждан в возрасте от 40 до 64 лет включительно, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('07', styleTCenter),
        ],
        [
            Paragraph('Флюорография легких или рентгенография легких, 1 раз в 2 года', styleSign),
            Paragraph('', styleSign),
            Paragraph('08', styleTCenter),
        ],
        [
            Paragraph('Спирография, 1 раз в 2 года', styleSign),
            Paragraph('', styleSign),
            Paragraph('09', styleTCenter),
        ],
        [
            Paragraph('6 минутная ходьба', styleSign),
            Paragraph('', styleSign),
            Paragraph('10', styleTCenter),
        ],
        [
            Paragraph('Электрокардиография в покое (при первом прохождении профилактического медицинского осмотра, далее в возрасте 35 лет и старше),'
                      ' 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('11', styleTCenter),
        ],
        [
            Paragraph('Измерение внутриглазного давления (при первом прохождении профилактического медицинского осмотра, далее в возрасте'
                      ' 40 лет и старше), 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('12', styleTCenter),
        ],
        [
            Paragraph('Осмотр фельдшером (акушеркой) или врачом акушером-гинекологом женщин в возрасте от 18 лет и старше, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('13', styleTCenter),
        ],
        [
            Paragraph('Взятие с использованием щетки цитологической цервикальной мазка (соскоба) с поверхности шейки матки (наружного маточного зева) и '
                      'цервикального канала на цитологическое исследование, цитологическое исследование мазка с шейки матки в возрасте от 18 до 64 лет,1 раз в 3 года', styleSign),
            Paragraph('', styleSign),
            Paragraph('14', styleTCenter),
        ],
        [
            Paragraph('Маммография обеих молочных желез в двух проекциях у женщин в возрасте от 40 до 75 лет включительно, 1 раз в 2 года', styleSign),
            Paragraph('', styleSign),
            Paragraph('15', styleTCenter),
        ],
        [
            Paragraph('Исследование кала на скрытую кровь иммунохимическим методом', styleSign),
            Paragraph('а) в возрасте от 40 до 64 лет включительно, 1 раз в 2 года', styleSign),
            Paragraph('16.1', styleTCenter),
        ],
        [
            Paragraph('', styleSign),
            Paragraph('б) в возрасте от 65 до 75 лет включительно, 1 раз в год', styleSign),
            Paragraph('16.2', styleTCenter),
        ],
        [
            Paragraph('Определение простат-специфического антигена в крови у мужчин в возрасте 45, 50, 55, 60 и 64 лет', styleSign),
            Paragraph('', styleSign),
            Paragraph('15', styleTCenter),
        ],
        [
            Paragraph('Эзофагогастродуоденоскопия в возрасте 45 лет однократно', styleSign),
            Paragraph('', styleSign),
            Paragraph('16', styleTCenter),
        ],
        [
            Paragraph('Общий анализ крови в возрасте 40 лет и старше, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('17', styleTCenter),
        ],
        [
            Paragraph('Биохимический анализ крови, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('18', styleTCenter),
        ],
        [
            Paragraph('Д-Димер, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('19', styleTCenter),
        ],
        [
            Paragraph('Краткое индивидуальное профилактическое консультирование в возрасте 18 лет и старше', styleSign),
            Paragraph('', styleSign),
            Paragraph('20', styleTCenter),
        ],
        [
            Paragraph('Прием (осмотр) по результатам профилактического медицинского осмотра фельдшером фельдшерского здравпункта или '
                      'фельдшерско-акушерского пункта, врачом-терапевтом или врачом по медицинской профилактике отделения (кабинета) медицинской профилактики'
                      'или центра здоровья граждан в возрасте 18 лет и старше, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('21', styleTCenter),
        ],
        [
            Paragraph('Прием (осмотр) врачом-терапевтом по результатам первого этапа диспансеризации', styleSign),
            Paragraph('а) граждан в возрасте от 18 лет до 39 лет 1 раз в 3 года', styleSign),
            Paragraph('22.1', styleTCenter),
        ],
        [
            Paragraph('', styleSign),
            Paragraph('б) граждан в возрасте 40 лет и старше 1 раз в год', styleSign),
            Paragraph('22.2', styleTCenter),
        ],
        [
            Paragraph('Осмотр на выявление визуальных и иных локализаций онкологических заболеваний, включающий осмотр кожных покровов, слизистых губ'
                      'и ротовой полости, пальпацию щитовидной железы, лимфатических узлов, граждан в возрасте 18 лет и старше, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('23', styleTCenter),
        ],
    ]

    row_height = []
    for i in opinion:
        row_height.append(None)

    tbl = Table(opinion, colWidths=(45 * mm, 45 * mm, 15 * mm, 20 * mm, 20 * mm, 20 * mm, 25 * mm), rowHeights=row_height)

    table_style = [
        ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('SPAN', (4, 0), (5, 0)),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('SPAN', (2, 0), (2, 1)),
        ('SPAN', (3, 0), (3, 1)),
        ('SPAN', (0, 0), (1, 1)),
        ('SPAN', (0, 18), (0, 19)),
        ('SPAN', (0, 27), (0, 28)),
        ('SPAN', (0, 29), (1, 29)),
    ]

    table_style += [
        ('SPAN', (0, i + 1), (1, i + 1)) for i in range(17)
    ]

    table_style += [
        ('SPAN', (0, i + 20), (1, i + 20)) for i in range(7)
    ]

    tbl.setStyle(TableStyle(table_style))

    objs.append(tbl)
    objs.append(
        Paragraph(
            '13. Направлен на второй этап диспансеризации: да - 1, нет - 2', style,
        )
    )

    objs.append(
        Paragraph(
            '14. Сведения о проведенных приёмах (осмотрах, консультациях), исследованиях и иных медицинских вмешательствах на втором этапе диспансеризации', style,
        )
    )

    opinion = [
        [
            Paragraph('Приём (осмотр, консультация), исследование и иное медицинское вмешательство, входящее в объем второго этапа диспансеризации', styleTCenter),
            Paragraph('N строки', styleTCenter),
            Paragraph('Выявлено медицинское показание в рамках первого этапа диспансеризации (+/-)', styleTCenter),
            Paragraph('Дата проведения', styleTCenter),
            Paragraph('Отказ (+/-)', styleTCenter),
            Paragraph('Проведено ранее (дата)', styleTCenter),
            Paragraph('Выявлено патологическое состояние (+/-)', styleTCenter),
        ],
        [
            Paragraph('1', styleTCenter),
            Paragraph('2', styleTCenter),
            Paragraph('3', styleTCenter),
            Paragraph('4', styleTCenter),
            Paragraph('5', styleTCenter),
            Paragraph('6', styleTCenter),
            Paragraph('7', styleTCenter),
        ],
        [
            Paragraph(' Осмотр (консультация) врачом-неврологом', styleSign),
            Paragraph('01', styleSign),
        ],
        [
            Paragraph('Дуплексное сканирование брахиоцефальных артерий ', styleSign),
            Paragraph('02', styleSign),
        ],
        [
            Paragraph('Осмотр (консультация) врачом-хирургом или врачом-урологом', styleSign),
            Paragraph('03', styleSign),
        ],

        [
            Paragraph('Осмотр (консультация) врачом-хирургом или врачом-колопроктологом, включая проведение ректороманоскопии', styleSign),
            Paragraph('04', styleSign),
        ],
        [
            Paragraph('Колоноскопия', styleSign),
            Paragraph('05', styleSign),
        ],
        [
            Paragraph('Эзофагогастродуоденоскопия', styleSign),
            Paragraph('06', styleSign),
        ],
        [
            Paragraph('Рентгенография легких', styleSign),
            Paragraph('07', styleSign),
        ],
        [
            Paragraph('Компьютерная томография легких', styleSign),
            Paragraph('08', styleSign),
        ],
        [
            Paragraph('Эхокардиография', styleSign),
            Paragraph('09', styleSign),
        ],
        [
            Paragraph('Дуплексное сканирование вен нижних конечностей', styleSign),
            Paragraph('10', styleSign),
        ],
        [
            Paragraph('Спирометрия', styleSign),
            Paragraph('11', styleSign),
        ],
        [
            Paragraph('Осмотр (консультация) врачом-акушером-гинекологом', styleSign),
            Paragraph('12', styleSign),
        ],
        [
            Paragraph('Осмотр (консультация) врачом-оториноларингологом', styleSign),
            Paragraph('13', styleSign),
        ],
        [
            Paragraph('Осмотр (консультация) врачом-офтальмологом', styleSign),
            Paragraph('14', styleSign),
        ],
        [
            Paragraph('Индивидуальное или групповое (школа для пациентов) углубленное профилактическое консультирование для граждан:', styleSign),
            Paragraph('15', styleSign),
        ],
        [
            Paragraph('с выявленной ишемической болезнью сердца, цереброваскулярными заболеваниями, хронической ишемией нижних конечностей атеросклеротического'
                      'генеза или болезнями, характеризующимися повышенным кровяным давлением', styleSign),
            Paragraph('15.1', styleSign),
        ],
        [
            Paragraph('с выявленным по результатам анкетирования риском пагубного потребления алкоголя и (или) потребления наркотических средств '
                      'и психотропных веществ без назначения врача', styleSign),
            Paragraph('15.2', styleSign),
        ],
        [
            Paragraph('в возрасте 65 лет и старше в целях коррекции выявленных факторов риска и (или) профилактики старческой астении', styleSign),
            Paragraph('15.3', styleSign),
        ],
        [
            Paragraph('при выявлении высокого относительного, высокого и очень высокого абсолютного сердечно-сосудистого риска, и (или) ожирения,'
                      'и (или) гиперхолестеринемии с уровнем общего холестерина 8 ммоль/л и более, а также установленном по результатам анкетирования курении более'
                      '20 сигарет в день, риске пагубного потребления алкоголя и (или) риске немедицинского потребления наркотических средств и психотропных веществ', styleSign),
            Paragraph('15.4', styleSign),
        ],
        [
            Paragraph('Прием (осмотр) врачом-терапевтом по результатам второго этапа диспансеризации', styleSign),
            Paragraph('16', styleSign),
        ],
        [
            Paragraph('Направление на осмотр (консультацию) врачом-онкологом при подозрении на онкологические заболевания.', styleSign),
            Paragraph('17', styleSign),
        ],
        [
            Paragraph('Oсмотр (консультацию) врачом-дерматовенерологом, включая проведение дерматоскопии (для граждан с подозрением'
                      'на злокачественные новообразования кожи и (или) слизистых оболочек по назначению врача-терапевта по результатам осмотра на'
                      'выявление визуальных и иных локализаций онкологических заболеваний, включающего осмотр кожных покровов, слизистых губ и ротовой '
                      'полости, пальпацию щитовидной железы, лимфатических узлов);', styleSign),
            Paragraph('18', styleSign),
        ],
        [
            Paragraph('Проведение исследования уровня гликированного гемоглобина в крови (для граждан с подозрением на сахарный диабет'
                      'по назначению врача-терапевта по результатам осмотров и исследований первого этапа диспансеризации);', styleSign),
            Paragraph('19', styleSign),
        ],
    ]

    row_height = []
    for i in opinion:
        row_height.append(None)

    tbl = Table(opinion, colWidths=(70 * mm, 15 * mm, 25 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm), rowHeights=row_height)

    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ]
        )
    )

    objs.append(tbl)

    objs.append(Paragraph('15. Дата окончания профилактического медицинского осмотра __________________', style,))
    objs.append(Paragraph('Дата окончания первого этапа диспансеризации _________________', style,))
    objs.append(Paragraph('Дата окончания второго этапа диспансеризации _________________', style,))
    objs.append(Paragraph('16. Профилактический медицинский осмотр (диспансеризация) проведен(а): в полном объеме - 1, в неполном объеме - 2', style,))
    objs.append(Paragraph(
        '17. Выявленные при проведении профилактического медицинского осмотра (диспансеризации) факторы риска и другие патологические '
        'состояния и заболевания, повышающие вероятность развития хронических неинфекционных заболеваний', style,))

    opinion = [
        [
            Paragraph('Наименование фактора риска, другого патологического состояния и заболевания', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph('№ строки', styleTCenter),
            Paragraph('Код МКБ-10<sup>1</sup>', styleTCenter),
            Paragraph('Выявлен фактор риска, другое патологическое состояние и заболевание (+/-)', styleTCenter),
        ],
        [
            Paragraph('1', styleTCenter),
            Paragraph('', styleSign),
            Paragraph('2', styleTCenter),
            Paragraph('3', styleTCenter),
            Paragraph('4', styleTCenter),
        ],
        [
            Paragraph('Гиперхолестеринемия', styleSign),
            Paragraph('', styleSign),
            Paragraph('01', styleTCenter),
            Paragraph('Е78', styleTCenter),
        ],
        [
            Paragraph('Гипергликемия ', styleSign),
            Paragraph('', styleSign),
            Paragraph('02', styleTCenter),
            Paragraph('R73.9', styleTCenter),
        ],        
        [
            Paragraph('Курение табака', styleSign),
            Paragraph('', styleSign),
            Paragraph('03', styleTCenter),
            Paragraph('Z72.0', styleTCenter),
        ],        
        [
            Paragraph('Нерациональное питание ', styleSign),
            Paragraph('', styleSign),
            Paragraph('04', styleTCenter),
            Paragraph('Z72.4', styleTCenter),
        ],        
        [
            Paragraph('Избыточная масса тела', styleSign),
            Paragraph('', styleSign),
            Paragraph('05', styleTCenter),
            Paragraph('R63.5', styleTCenter),
        ],        
        [
            Paragraph('Ожирение', styleSign),
            Paragraph('', styleSign),
            Paragraph('06', styleTCenter),
            Paragraph('Е66', styleTCenter),
        ],        
        [
            Paragraph('Низкая физическая активность', styleSign),
            Paragraph('', styleSign),
            Paragraph('07', styleTCenter),
            Paragraph('Z72.3', styleTCenter),
        ],        
        [
            Paragraph('Риск пагубного потребления алкоголя', styleSign),
            Paragraph('', styleSign),
            Paragraph('08', styleTCenter),
            Paragraph('Z72.1', styleTCenter),
        ],        
        [
            Paragraph('Риск потребления наркотических средств и психотропных веществ без назначения врача', styleSign),
            Paragraph('', styleSign),
            Paragraph('09', styleTCenter),
            Paragraph('Z72.2', styleTCenter),
        ],      
        [
            Paragraph('Отягощенная наследственность по сердечно-сосудистым заболеваниям', styleSign),
            Paragraph('инфаркт миокарда', styleSign),
            Paragraph('10', styleTCenter),
            Paragraph('Z82.4', styleTCenter),
        ],       
        [
            Paragraph('', styleSign),
            Paragraph('мозговой инсульт', styleSign),
            Paragraph('11', styleTCenter),
            Paragraph('Z82.3', styleTCenter),
        ],       
        [
            Paragraph('Отягощенная наследственность по злокачественным новообразованиям', styleSign),
            Paragraph('колоректальной области', styleSign),
            Paragraph('12', styleTCenter),
            Paragraph('Z80.0', styleTCenter),
        ],       
        [
            Paragraph('', styleSign),
            Paragraph('других локализации', styleSign),
            Paragraph('13', styleTCenter),
            Paragraph('Z80.9', styleTCenter),
        ],       
        [
            Paragraph('Отягощенная наследственность по хроническим болезням нижних дыхательных путей', styleSign),
            Paragraph('', styleSign),
            Paragraph('14', styleTCenter),
            Paragraph('Z82.5', styleTCenter),
        ],       
        [
            Paragraph('Отягощенная наследственность по сахарному диабету', styleSign),
            Paragraph('', styleSign),
            Paragraph('15', styleTCenter),
            Paragraph('Z83.3', styleTCenter),
        ],       
        [
            Paragraph('Высокий (5% -10%) или очень высокий (10% и более) абсолютный сердечно-сосудистый риск', styleSign),
            Paragraph('', styleSign),
            Paragraph('16', styleTCenter),
            Paragraph('-', styleTCenter),
        ],
        [
            Paragraph('Высокий (более 1 ед.) относительный сердечно-сосудистый риск', styleSign),
            Paragraph('', styleSign),
            Paragraph('17', styleTCenter),
            Paragraph('-', styleTCenter),
        ],
        [
            Paragraph('Старческая астения', styleSign),
            Paragraph('', styleSign),
            Paragraph('18', styleTCenter),
            Paragraph('R54', styleTCenter),
        ],
    ]

    row_height = []
    for i in opinion:
        row_height.append(None)

    tbl = Table(opinion, colWidths=(70 * mm, 50 * mm, 20 * mm, 20 * mm, 30 * mm), rowHeights=row_height)
    table_style = [
        ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('SPAN', (0, 11), (0, 12)),
        ('SPAN', (0, 13), (0, 14)),
    ]

    table_style += [
        ('SPAN', (0, i), (1, i)) for i in range(11)
    ]

    table_style += [
        ('SPAN', (0, i + 15), (1, i + 15)) for i in range(5)
    ]

    tbl.setStyle(TableStyle(table_style))

    objs.append(tbl)

    objs.append(Paragraph('17.1. Все факторы риска, указанные в строках 03, 04, 07, 08, 09 настоящей таблицы: отсутствуют - 1,присутствуют - 2', style,))
    objs.append(Paragraph('18. Заболевания, выявленные при проведении профилактического медицинского осмотра (диспансеризации),установление диспансерного наблюдения', style,))

    opinion = [
        [
            Paragraph('Наименование классов и отдельных заболеваний', styleTCenter),
            Paragraph('№ строки', styleTCenter),
            Paragraph('Код МКБ-10', styleTCenter),
            Paragraph('Отметка о наличии заболевания (+/-)', styleTCenter),
            Paragraph('Отметка об установлении диспансерного наблюдения (+/-)', styleTCenter),
            Paragraph('Отметка о впервые выявленном заболевании (+/-)', styleTCenter),
            Paragraph('Отметка о впервые установленном диспансерном наблюдении (+/-)', styleTCenter),
        ],
        [
            Paragraph('1', styleTCenter),
            Paragraph('2', styleTCenter),
            Paragraph('3', styleTCenter),
            Paragraph('4', styleTCenter),
            Paragraph('5', styleTCenter),
            Paragraph('6', styleTCenter),
            Paragraph('7', styleTCenter),
        ],
        [
            Paragraph('Туберкулез органов дыхания', styleSign),
            Paragraph('01', styleTCenter),
            Paragraph('А15-А16', styleTCenter),
        ],
        [
            Paragraph('Злокачественные новообразования', styleSign),
            Paragraph('02', styleTCenter),
            Paragraph('С00-С97', styleTCenter),
        ],        
        [
            Paragraph('Из них губы, полости рта и глотки', styleSign),
            Paragraph('2.1', styleTCenter),
            Paragraph('С00-С14', styleTCenter),
        ],        
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.2', styleTCenter),
            Paragraph('', styleTCenter),
        ],        
        [
            Paragraph('пищевода', styleSign),
            Paragraph('2.3', styleTCenter),
            Paragraph('С15', styleTCenter),
        ],        
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.4', styleTCenter),
            Paragraph('', styleTCenter),
        ],       
        [
            Paragraph('желудка', styleSign),
            Paragraph('2.5', styleTCenter),
            Paragraph('С16', styleTCenter),
        ],          
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.6', styleTCenter),
            Paragraph('', styleTCenter),
        ],        
        [
            Paragraph('тонкого кишечника', styleSign),
            Paragraph('2.7', styleTCenter),
            Paragraph('С17', styleTCenter),
        ],        
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.8', styleTCenter),
            Paragraph('', styleTCenter),
        ],        
        [
            Paragraph('ободочной кишки', styleSign),
            Paragraph('2.9', styleTCenter),
            Paragraph('С18', styleTCenter),
        ],        
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.10', styleTCenter),
            Paragraph('', styleTCenter),
        ],        
        [
            Paragraph('ректосигмоидного соединения, прямой кишки, заднего прохода (ануса) и анального канала', styleSign),
            Paragraph('2.11', styleTCenter),
            Paragraph('С19-С21', styleTCenter),
        ],        
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.12', styleTCenter),
            Paragraph('', styleTCenter),
        ],        
        [
            Paragraph('трахеи, бронхов, легкого', styleSign),
            Paragraph('2.13', styleTCenter),
            Paragraph('С33, С34', styleTCenter),
        ],        
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.14', styleTCenter),
            Paragraph('', styleTCenter),
        ],        
        [
            Paragraph('кожи', styleSign),
            Paragraph('2.15', styleTCenter),
            Paragraph('С43-С44', styleTCenter),
        ],        
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.16', styleTCenter),
            Paragraph('', styleTCenter),
        ],        
        [
            Paragraph('молочной железы', styleSign),
            Paragraph('2.17', styleTCenter),
            Paragraph('С50', styleTCenter),
        ],        
        [
            Paragraph('из них в 0-1 стадии', styleSign),
            Paragraph('2.18', styleTCenter),
            Paragraph('', styleTCenter),
        ],        
        [
            Paragraph('2 стадии', styleSign),
            Paragraph('2.19', styleTCenter),
            Paragraph('', styleTCenter),
        ],        
        [
            Paragraph('шейки матки', styleSign),
            Paragraph('2.20', styleTCenter),
            Paragraph('С53', styleTCenter),
        ],        
        [
            Paragraph('из них в 0-1 стадии', styleSign),
            Paragraph('2.21', styleTCenter),
            Paragraph('', styleTCenter),
        ],        
        [
            Paragraph('2 стадии', styleSign),
            Paragraph('2.22', styleTCenter),
            Paragraph('', styleTCenter),
        ],        
        [
            Paragraph('предстательной железы', styleSign),
            Paragraph('2.23', styleTCenter),
            Paragraph('С61', styleTCenter),
        ],        
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.24', styleTCenter),
            Paragraph('', styleTCenter),
        ],        
        [
            Paragraph('Сахарный диабет', styleSign),
            Paragraph('03', styleTCenter),
            Paragraph('Е10-Е14Е10-Е14', styleTCenter),
        ],        
        [
            Paragraph('из него: инсулиннезависимый сахарный диабет', styleSign),
            Paragraph('3.1', styleTCenter),
            Paragraph('Е11', styleTCenter),
        ],        
        [
            Paragraph('Преходящие церебральные ишемические приступы (атаки) и родственные синдромыvv', styleSign),
            Paragraph('04', styleTCenter),
            Paragraph('G45', styleTCenter),
        ],        
        [
            Paragraph('Старческая катаракта и другие катаракты', styleSign),
            Paragraph('05', styleTCenter),
            Paragraph('Н25, Н26', styleTCenter),
        ],        
        [
            Paragraph('Глаукома', styleSign),
            Paragraph('06', styleTCenter),
            Paragraph('Н40', styleTCenter),
        ],        
        [
            Paragraph('Слепота и пониженное зрение', styleSign),
            Paragraph('07', styleTCenter),
            Paragraph('Н54', styleTCenter),
        ],        
        [
            Paragraph('Кондуктивная и нейросенсорная потеря слуха', styleSign),
            Paragraph('08', styleTCenter),
            Paragraph('Н90', styleTCenter),
        ],        
        [
            Paragraph('Болезни системы кровообращения', styleSign),
            Paragraph('09', styleTCenter),
            Paragraph('I00-I99', styleTCenter),
        ],        
        [
            Paragraph('из них: болезни, характеризующиеся повышенным кровяным давлением', styleSign),
            Paragraph('9.1', styleTCenter),
            Paragraph('I10-I13', styleTCenter),
        ],        
        [
            Paragraph('ишемические болезни сердца', styleSign),
            Paragraph('9.2', styleTCenter),
            Paragraph('I20-I25', styleTCenter),
        ],        
        [
            Paragraph('цереброваскулярные болезни', styleSign),
            Paragraph('9.3', styleTCenter),
            Paragraph('I60-I69', styleTCenter),
        ],        
        [
            Paragraph('из них: закупорка и стеноз прецеребральных и (или) церебральных артерий, не приводящие к инфаркту мозга', styleSign),
            Paragraph('9.4', styleTCenter),
            Paragraph('I65, I66', styleTCenter),
        ],        
        [
            Paragraph('Болезни органов дыхания', styleSign),
            Paragraph('10', styleTCenter),
            Paragraph('J00-J99', styleTCenter),
        ],        
        [
            Paragraph(
                'Бронхит, не уточненный как острый и хронический, '
                'простой и слизисто-гнойный хронический бронхит, хронический бронхит неуточненный, эмфизема', 
                styleSign
            ),
            Paragraph('10.1', styleTCenter),
            Paragraph('J40-J43', styleTCenter),
        ],        
        [
            Paragraph('Другая хроническая обструктивная легочная болезнь, астма, астматический статус, бронхоэктатическая болезнь', styleSign),
            Paragraph('10.2', styleTCenter),
            Paragraph('J44-J47', styleTCenter),
        ],        
        [
            Paragraph('Болезни органов пищеварения', styleSign),
            Paragraph('11', styleTCenter),
            Paragraph('К00-К93', styleTCenter),
        ],        
        [
            Paragraph('язва желудка, язва двенадцатиперстной кишки', styleSign),
            Paragraph('11.1', styleTCenter),
            Paragraph('К25, К26', styleTCenter),
        ],        
        [
            Paragraph('гастрит и дуоденит', styleSign),
            Paragraph('12', styleTCenter),
            Paragraph('К29', styleTCenter),
        ],
        [
            Paragraph('Прочие', styleSign),
            Paragraph('13', styleTCenter),
            Paragraph('', styleTCenter),
        ],
    ]

    row_height = []
    for i in opinion:
        row_height.append(None)

    tbl = Table(opinion, colWidths=(60 * mm, 10 * mm, 20 * mm, 20 * mm, 25 * mm, 30 * mm, 30 * mm,), rowHeights=row_height)

    table_style = [
        ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('SPAN', (2, 20), (2, 22)),
        ('SPAN', (2, 23), (2, 25)),
    ] 
    table_style += [
        ('SPAN', (2, 4 + (i * 2)), (2, 4 + (i * 2) + 1)) for i in range(8)
    ]

    tbl.setStyle(TableStyle(table_style))
    objs.append(tbl)

    objs.append(Paragraph('19. Диспансерное наблюдение установлено:', style,))
    objs.append(Paragraph('19.1. врачом (фельдшером) отделения (кабинета) медицинской профилактики или центра здоровья: да - 1; нет - 2.', style,))
    objs.append(Paragraph('Если "да", N строки таблицы пункта 18 ________________', style,))
    objs.append(Paragraph('19.2. врачом-терапевтом: да - 1; нет - 2. Если "да", N строки таблицы пункта 18 _______________________', style,))    
    objs.append(Paragraph('19.3. врачом-специалистом: да - 1; нет - 2. Если "да", N строки таблицы пункта 18 _____________________', style,))    
    objs.append(Paragraph(
        '19.4. фельдшером фельдшерского здравпункта или фельдшерско-акушерского пункта: да - 1; нет - 2.'
        'Если "да", N строки таблицы пункта 18 _________________________', style,
    ))    
    objs.append(Paragraph('20. Группа  здоровья:  I группа - 1,   II группа - 2,   IIIа  группа - 3,   IIIб группа - 4', style,))    
    objs.append(Paragraph(
        '21. Уровень артериального давления ниже 140/90 мм рт. ст. на фоне приема гипотензивных лекарственных препаратов'
        'при наличии болезней, характеризующихся повышенным кровяным давлением (коды I10-I15 по МКБ-10): да- 1; нет - 2', style,
    ))    
    objs.append(Paragraph(
        '22. Направлен   при  наличии  медицинских   показаний   на   дополнительное   обследование,   не  входящее  в объем'
        'диспансеризации,  в том числе  направлен   на  осмотр (консультацию)  врачом-онкологом  при  подозрении на онкологическое заболевание: да - 1; нет - 2', style,
    ))    
    objs.append(Paragraph('Если "да", дата направления "___"___________ 20__ г', style,))    
    objs.append(Paragraph('23. Направлен для получения специализированной, в том числе высокотехнологичной, медицинской помощи: да - 1; нет - 2', style,))
    objs.append(Paragraph('Если "да", дата направления "___"___________ 20__ г', style,))    
    objs.append(Paragraph('24. Направлен на санаторно-курортное лечение: да - 1; нет - 2', style,))

    objs.append(Spacer(1, 10 * mm))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))

    objs.append(Paragraph(
        'Ф.И.О. и подпись врача (фельдшера) отделения (кабинета) медицинской профилактики  (центра здоровья),   а    в случае  отсутствия в'
        'медицинской  организации  отделения  (кабинета)  медицинской профилактики - фельдшера, врача-терапевта, являющегося ответственным'
        'за организацию и проведение профилактического медицинского осмотра (диспансеризации) на участке<sup>2</sup>.', style,
    ))

    objs.append(Spacer(1, 60 * mm))
    objs.append(Paragraph(
        '<sup>1</sup> Международная статистическая классификация болезней и проблем, связанных со здоровьем, 10-го пересмотра (далее - МКБ - 10).', styleSmallFont,))

    objs.append(Paragraph(
        '<sup>2</sup> Абзацы третий и четвертый пункта 12 порядка проведения профилактического медицинского осмотра и диспансеризации определенных групп'
        'взрослого населения, утвержденного приказом Министерства здравоохранения Российской Федерации от 13 марта 2019 г. N 124н "Об утверждении порядка'
        'проведения профилактического медицинского осмотра и диспансеризации определенных групп взрослого населения" (зарегистрирован Министерством'
        'юстиции Российской Федерации 24 апреля 2019 г., регистрационный N 54495), с изменениями, внесенными приказом Министерства здравоохранения'
        'Российской Федерации 2 сентября 2019 г. N 716н (зарегистрирован Министерством юстиции Российской Федерации 16 октября 2019 г., регистрационный '
        '№ 56254).', styleSmallFont,))

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


def form_11(request_data):
    """
	Отказ от медицинского вмешательства/госпитализации
    """
    ind_card = Card.objects.get(pk=request_data["card_pk"])
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

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

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

    styleRight = deepcopy(style)
    styleRight.aligment = TA_RIGHT

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

    styleT = deepcopy(style)
    styleT.firstLineIndent = 0

    objs = []

    opinion = [
        [
            Paragraph('', style),
            Paragraph('Приложение №3 к приказу Министерства здравоохранения <br/> Российской Федерации от 20 декабря 2012г.№ 117н', styleT),
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

    objs.append(
        Paragraph(
			'<br/> ОТКАЗ <br/>' 
			'от медицинского вмешательства/госпитализации <br/>'
			'(для законного представителя) <br/>'
			'заполняется полностью рукой законного представителя!!! <br/>'.format(who_patient),
            styleCenterBold
        ),
    )

    d = datetime.datetime.strptime(person_data['born'], '%d.%m.%Y').date()
    date_individual_born = pytils.dt.ru_strftime(u"\"%d\" %B %Y", inflected=True, date=d)

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Я, {}&nbsp; {} г. рождения'.format(person_data['fio'], date_individual_born), styleSign))

    styleLeft = deepcopy(style)
    styleLeft.alignment = TA_LEFT
    objs.append(Paragraph('Зарегистрированный(ая) по адресу: {}'.format(person_data['main_address']), styleSign))
    objs.append(
        Paragraph(
            'Документ, удостоверяющий личность {}: серия <u> {}</u> номер: <u>{}</u>'.format(person_data['type_doc'], person_data['passport_serial'], person_data['passport_num']), styleSign
        )
    )
    objs.append(Paragraph('Выдан: {} {}'.format(person_data['passport_date_start'], person_data['passport_issued']), styleSign))

    hospital: Hospitals = request_data["hospital"]
	
    hospital_name = hospital.safe_short_title

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

    hospital: Hospitals = request_data["hospital"]

    hospital_name = hospital.safe_short_title

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Отказываюсь от предложенной  госпитализации, медицинского вмешательства моему ребёнку в <br/>', styleSign))  
    objs.append(Paragraph('_________________________________________________________________________________________________', styleSign))
    objs.append(Paragraph('(название отделения, номер палаты, конкретный вид медицинского вмешательства)<br/>', styleCenter))
    objs.append(Paragraph('<br/> О заболевании моего ребёнка <br/>', styleSign))
    objs.append(Paragraph('_________________________________________________________________________________________________', styleSign))
    objs.append(Paragraph('(Диагноз)', styleCenter))
    objs.append(Paragraph('информирован(а).', styleSign))

    objs.append(
        Paragraph(
            '<br/> Медицинским работником _______________________________________________________________________',
            style,
        )
    )

    objs.append(Paragraph(
			'1) в доступной для меня форме мне разъяснены возможные последствия отказа от '
            'вышеуказанных видов медицинских вмешательств, в том числе вероятность '
            'развития осложнений заболевания (состояния). Мне разъяснено, что при '
            'возникновении необходимости в осуществлении одного или нескольких видов '
            'медицинских вмешательств, в отношении которых оформлен настоящий отказ, я'
            'имею право оформить информированное добровольное согласие на такой вид '
            '(такие виды) медицинского вмешательства; <br/>'
			'2) мне были предложены альтернативные методы лечения моего ребёнка:___________________________________________;<br/>'
			'3) Я не имею, и не буду иметь каких-либо претензий к сотрудникам ГБУЗ ИГОДКБ в случае развития негативных последствий'
			'вследствие моего решения об отказе в госпитализации, медицинского вмешательства моего ребёнка;<br/>'
			'4) Ст. 125 УК РФ «Оставление в опасности - заведомое оставление без помощи лица, находящегося в опасном для жизни или здоровья'
			'состоянии и лишенного возможности принять меры к самосохранению по малолетству, старости, болезни или вследствие своей беспомощности,'
			'в случаях, если виновный имел возможность оказать помощь этому лицу и был обязан иметь о нем заботу либо сам поставил его в опасное для'
			'жизни или здоровья состояние», мне разъяснена и понятна;<br/>'
			'5) Я разрешаю, в случае необходимости, предоставить информацию о диагнозе моего ребёнка,'
			'степени тяжести и характере заболевания и другим законным представителям, гражданам_____________________________________________________________________;<br/>'
			'6) Я ознакомлен(а) и согласен (а) со всеми пунктами настоящего документа, положения которого мне разъяснены, мною поняты и добровольно даю свое'
			'согласие на отказ от медицинского вмешательства/госпитализации моего ребёнка.<br/>',
            styleSign,))
    space_bottom = ' &nbsp;'

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('{}'.format(person_data['fio']), styleCenter))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('(подпись){0}(Ф.И.О. гражданина или законного представителя гражданина){1}'.format(22 * space_bottom, 30 * space_bottom), styleCenter))

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('{}'.format(space_bottom), style))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('(подпись){0}(Ф.И.О. медицинского работника){1}'.format(33 * space_bottom, 43 * space_bottom), styleCenter))

    objs.append(Spacer(1, 5 * mm))

    styleSign = deepcopy(style)
    styleSign.firstLineIndent = 0

    date_now = pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=datetime.datetime.now())
    objs.append(Spacer(1, 5 * mm))
    objs.append(Paragraph('{} г.'.format(date_now), style))
    objs.append(HRFlowable(width=46 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black, hAlign=TA_LEFT))
    objs.append(Paragraph('{}(дата оформления)'.format(3 * space_bottom), styleSign))

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


def form_12(request_data):
    """
    Добровольное информированное согласие 
    пациентана вакцинацию против новой
    коронавирусной инфекции или отказ от неё
    """
    ind_card = Card.objects.get(pk=request_data["card_pk"])
    patient_data = ind_card.get_data_individual()

    agent_status = False
    if ind_card.who_is_agent:
        p_agent = getattr(ind_card, ind_card.who_is_agent)
        agent_status = bool(p_agent)

    if agent_status:
        person_data = p_agent.get_data_individual()
    else:
        person_data = patient_data

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=13 * mm, rightMargin=4 * mm, topMargin=4 * mm, bottomMargin=4 * mm, allowSplitting=1, title="Форма {}".format("Согласие на прививку")
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

    styleRight = deepcopy(style)
    styleRight.aligment = TA_RIGHT

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

    styleT = deepcopy(style)
    styleT.firstLineIndent = 0

    objs = []

    objs.append(
        Paragraph(
            'Добровольное информированное согласие пациента <br/>'
            'на вакцинацию против новой коронавирусной инфекции или отказ от неё<br/> ', styleCenterBold),
    )

    d = datetime.datetime.strptime(person_data['born'], '%d.%m.%Y').date()
    date_individual_born = pytils.dt.ru_strftime(u"\"%d\" %B %Y", inflected=True, date=d)

    objs.append(Spacer(1, 3 * mm))
    fio = person_data['fio']
    objs.append(Paragraph(f'Я, нижеподписавшийся(аяся) {fio}&nbsp; {date_individual_born} г. рождения', style))

    styleLeft = deepcopy(style)
    styleLeft.alignment = TA_LEFT
    objs.append(Paragraph('Зарегистрированный(ая) по адресу: {}'.format(person_data['main_address']), style))
    objs.append(Paragraph('Номер телефона для связи: ________________', style,))
    objs.append(Paragraph('Настоящим подтверждаю, что проинформирован врачом:', style,))
    objs.append(Paragraph('- о смысле и цели вакцинации;', style,))

    objs.append(
        Paragraph(
            '- на момент вакцинации я не предъявляю никаких острых жалоб на состояние '
            'здоровья (температура тела нормальная, отсутствуют жалобы на боль, озноб, сильную слабость, '
            'нет иных выраженных жалоб, которые могут свидетельствовать об острых заболеваниях или обострении хронических);',
            style,
        )
    )
    objs.append(
        Paragraph(
            '- я понимаю, что вакцинация - это введение в организм человека '
            'иммунобиологического лекарственного препарата для создания специфической '
            'невосприимчивости к инфекционным заболеваниям;',
            style,
        )
    )
    objs.append(
        Paragraph(
            '- мне ясно, что после вакцинации возможны реакции на прививку, которые могут '
            'быть местными (покраснения, уплотнения, боль, зуд в месте инъекции и другие) и общими '
            '(повышение температуры, недомогание, озноб и другие); крайне редко могут наблюдаться '
            'поствакцинальные осложнения (шок, аллергические реакции и другие), но вероятность '
            'озникновения таких реакций значительно ниже, чем вероятность развития неблагоприятных '
            'исходов заболевания, для предупреждения которого проводится вакцинация;',
            style,
        )
    )
    objs.append(Paragraph('- о всех имеющихся противопоказаниях к вакцинации;', style,))
    objs.append(
        Paragraph(
            '- я поставил (поставила) в известность медицинского работника о ранее выполненных '
            'вакцинациях, обо всех проблемах, связанных со здоровьем, в том числе о любых формах '
            'аллергических проявлений, обо всех перенесенных мною и известных мне заболеваниях, '
            'принимаемых лекарственных средствах, о наличии реакций или осложнений на предшествующие '
            'введения вакцин у меня. Сообщила (для женщин) об отсутствии факта беременности '
            'или кормления грудью.',
            style,
        )
    )
    objs.append(Paragraph('Я имел(а) возможность задавать любые вопросы и на все вопросы получил(а) исчерпывающие ответы.', style,))
    objs.append(
        Paragraph(
            'Получив полную информацию о необходимости проведения профилактической прививки '
            'против новой коронавирусной инфекции, возможных прививочных реакциях, последствиях отказа '
            'от неё, подтверждаю, что мне понятен смысл всех терминов и:',
            style,
        )
    )
    objs.append(
        Paragraph(
            'добровольно соглашаюсь на проведение прививки  _________________________________________________',
            style,
        )
    )
    objs.append(
        Paragraph(
            'добровольно отказываюсь на проведение прививки  ________________________________________________',
            style,
        )
    )
    objs.append(Paragraph('Я, нижеподписавшийся(аяся) {}&nbsp; {} г. рождения'.format(person_data['fio'], date_individual_born), style))
    objs.append(
        Paragraph(
            'Медицинским работником _______________________________________________________________________',
            style,
        )
    )
    space_bottom = ' &nbsp;'
    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('{}'.format(person_data['fio']), styleCenter))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('(подпись){0}(Ф.И.О. гражданина или законного представителя гражданина){1}'.format(22 * space_bottom, 30 * space_bottom), styleCenter))
    date_now = pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=datetime.datetime.now())
    objs.append(Spacer(1, 5 * mm))
    objs.append(Paragraph('Дата {} г.'.format(date_now), styleSign))
    objs.append(HRFlowable(width=46 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black, hAlign=TA_LEFT))
    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('Я свидетельствую, что разъяснил все вопросы, связанные с проведением прививок и дал ответы на все вопросы.', style))

    objs.append(Paragraph('{}'.format(space_bottom), style))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('(подпись){0}(Ф.И.О. врача){1}'.format(33 * space_bottom, 43 * space_bottom), styleCenter))

    objs.append(Spacer(1, 5 * mm))

    styleSign = deepcopy(style)
    styleSign.firstLineIndent = 0

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
