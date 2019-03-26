import os
from copy import deepcopy
from io import BytesIO

from django.utils import timezone, dateformat
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer,Table, TableStyle, KeepInFrame, KeepTogether
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT

from clients.models import Individual, Card, Document
# from datetime import *
import datetime
import locale
import sys
import pytils
from . import forms_func
from laboratory import settings
from laboratory.settings import FONTS_FOLDER
from appconf.manager import SettingManager



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
        '{} года рождения, настоящим подтверждаю, что на основании представленной мне информации, свободно и без принуждения, отдавая отчет о последствиях обследования, принял решение пройти тестирование на антитела к ВИЧ. Для этой цели я соглашаюсь сдать анализ крови.<br/>'.format(
            i.bd()),
        'Я подтверждаю, что мне разъяснено, почему важно пройти тестирование на ВИЧ, как проводится тест и какие последствия может иметь тестирование на ВИЧ.',
        'Я проинформирован, что:',
        '- тестирование на ВИЧ проводится в Центре СПИД и других медицинских учреждениях. Тестирование по моему добровольному выбору может быть добровольным анонимным (без предъявления документов и указания имени) или конфиденциальным (при предъявлении паспорта, результат будет известен обследуемому и лечащему врачу). В государственных медицинских учреждениях тестирование на ВИЧ проводится бесплатно;',
        '- доказательством наличия ВИЧ-инфекции является присутствие антител к ВИЧ в крови обследуемого лица. Вместе с тем, в период между заражением и появлением антител к ВИЧ (так называемое "серонегативное окно, обычно 3 месяца) при тестировании не обнаруживаются антитела к ВИЧ и обследуемое лицо может заразить других лиц.',
        '- ВИЧ-инфекция передается только тремя путями:',
        '- парентеральный - чаще всего при употреблении наркотиков, но может передаваться также при использовании нестерильного медицинского инструментария, переливании компонентов крови, нанесении татуировок, пирсинге зараженным инструментом, использовании чужих бритвенных и маникюрных принадлежностей;',
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
    pass


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
    # ind = Individual.objects.get(pk=request_data["individual"])
    ind = ind_card.individual
    ind_doc = Document.objects.filter(individual=ind, is_active=True)
    individual_age = ind.age()

    # Касьяненко
    # # передать законного представителья, если возраст меньше 15 лет, или имеется опекун, или доверенность
    # if request_data["agent_pk"]:
    #     ind_agent_card = Card.objects.get(pk=request_data["agent_pk"])
    #
    #
    # #Если пациенту меньше 15 лет у него д.б. законный прелстаитель
    # if individual_age < 15:
    #     patient_agent = ind_card.patient_agent
    #     ind_card = patient_agent
    #     ind = ind_card.individual
    #Касьяненко

    individual_fio = ind.fio()
    individual_date_born = ind.bd()


    if individual_age < 15:
        patient_agent = " Иванова Марья Ивановна"

    document_passport = "Паспорт РФ"
    documents = forms_func.get_all_doc(ind_doc)
    document_passport_num = documents['passport']['num']
    document_passport_serial = documents['passport']['serial']
    document_passport_date_start = documents['passport']['date_start']
    document_passport_issued = documents['passport']['issued']

    if ind_card.main_address:
        ind_address = ind_card.main_address
    else:
        m=0

    if m==0 and ind_card.fact_address:
        ind_address = ind_card.fact_address
    else:
        ind_address = "______________________________________________________________________"

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    # Генерировать pdf-Лист на оплату
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

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

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"

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
        Paragraph('Информированное добровольное согласие на виды медицинских вмешательств,<br/> включенные в Перечень определенных'
                  ' видов медицинских вмешательств,<br/> на которые граждане дают информированное добровольное согласие при '
                  'выборе врача и медицинской организации для получения первичной медико-санитарной помощи ', styleCenterBold),
        ]

    d = datetime.datetime.strptime(individual_date_born,'%d.%m.%Y').date()
    date_individual_born = pytils.dt.ru_strftime(u"\"%d\" %B %Y", inflected=True, date=d )

    objs.append(Spacer(1, 4.5 * mm))
    objs.append(Paragraph('Я, {}&nbsp; {} г. рождения, зарегистрированный по адресу:  {} '.
                          format(individual_fio,date_individual_born,ind_address),style))

    person_agent =''
    patient_agent =''
    if person_agent:
        patient_agent = "лицом, законным представителем которого я являюсь"
    else:
        patient_agent=''
    hospital_name = SettingManager.get("rmis_orgname")
    hospital_address = SettingManager.get("org_address")
    objs.append(Paragraph('даю информированное добровольное согласие на виды медицинских вмешательств, включенные в '
                          '\"Перечень\" определенных видов медицинских вмешательств, на которые граждане дают информированное '
                          'добровольное согласие при выборе врача и медицинской организации для получения первичной '
                          'медико-санитарной помощи, утвержденный  приказом  Министерства здравоохранения и социального развития '
                          'Российской Федерации от 23 апреля 2012 г. N 390н (зарегистрирован Министерством  юстиции '
                          'Российской Федерации 5 мая 2012 г. N 24082) (далее - \"Перечень\"), для  получения  первичной'
                          'медико-санитарной помощи {} в:<br/> {}'.format(patient_agent, hospital_name),style))

    ofname=''
    if ofname:
        doc_ofname = ofname
    else:
        doc_ofname = "________________________________________________________"

    objs.append(Paragraph('Медицинским работником {}'.format(doc_ofname),style))
    objs.append(Paragraph('в доступной для меня форме мне разъяснены цели, методы оказания медицинской помощи, связанный '
                          'с ними риск, возможные варианты медицинских вмешательств, их  последствия,  в  том  числе  '
                          'вероятность  развития  осложнений, а также предполагаемые  результаты оказания медицинской помощи. '
                          'Мне разъяснено, что я  имею  право  отказаться  от  одного  или  нескольких  видов  медицинских вмешательств,  '
                          'включенных в Перечень, или потребовать его (их) прекращения, за  исключением  случаев,  предусмотренных  '
                          'частью 9 статьи 20 Федерального закона  от 21 ноября 2011 г. N 323-ФЗ "Об основах охраны здоровья '
                          'граждан в Российской  Федерации"  (Собрание  законодательства  Российской  Федерации, 2011, '
                          'N 48, ст. 6724; 2012, N 26, ст. 3442, 3446).  ', style))
    if person_agent:
        patient_agent = 'лица,  законным представителем которого я являюсь (ненужное зачеркнуть)'
    else:
        patient_agent='моего здоровья'



    objs.append(Paragraph('Сведения  о  выбранных  мною  лицах, которым в соответствии с пунктом 5 части  5  статьи  19 '
                          'Федерального закона от 21 ноября 2011 г. N 323-ФЗ "Об основах охраны здоровья граждан в '
                          'Российской Федерации" может быть передана информация  о состоянии {}'.format(patient_agent), style))

    styleFCenter = deepcopy(style)
    styleFCenter.alignment = TA_CENTER

    styleBottom = deepcopy(style)
    styleBottom.fontSize = 8

    sign_bottom = ' &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;(подпись) '

    space_bottom = ' &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;'

    sign_fio_person = '(Ф.И.О .гражданина, контактный телефон)'
    sign_patient_agent = '(Ф.И.О. гражданина или законного представителя гражданина)'
    sign_fio_doc = '(Ф.И.О. медицинского работника)'

    objs.append(Spacer(1, 9 * mm))
    objs.append(Paragraph('', styleFCenter))
    objs.append(HRFlowable(width= 190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('{} {}'.format(4 * space_bottom, sign_fio_person), styleBottom))

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('{}'.format(individual_fio), styleFCenter))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('{} {} {}'.format(sign_bottom, 2 * space_bottom, sign_patient_agent), styleBottom))

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph('{}'.format(individual_fio), styleFCenter))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))
    objs.append(Paragraph('{} {} {}'.format( sign_bottom, 2 * space_bottom, sign_fio_doc), styleBottom))

    date_now = pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=datetime.datetime.now())
    objs.append(Spacer(1, 5 * mm))
    objs.append(Paragraph('{} г.'.format(date_now), style))
    objs.append(HRFlowable(width=46 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black, hAlign=TA_LEFT))
    objs.append(Paragraph('(дата оформления)', styleBottom))



    objs.append(Paragraph('', style))
    objs.append(Paragraph('', style))
    objs.append(Paragraph('', style))
    objs.append(Paragraph('', style))




    if document_passport_issued:
        passport_who_give = document_passport_issued
    else:
        passport_who_give = "______________________________________________________________________"



    doc.build(objs)
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