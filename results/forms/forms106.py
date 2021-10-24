from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from directions.models import Napravleniya
from appconf.manager import SettingManager
import os.path
from laboratory.settings import FONTS_FOLDER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .flowable import FrameDataUniversal
from directions.models import Issledovaniya
from ..prepare_data import fields_result_only_title_fields
import simplejson as json
import datetime
from dateutil.relativedelta import relativedelta
from hospitals.models import Hospitals

pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
pdfmetrics.registerFont(TTFont('BoxedIn', os.path.join(FONTS_FOLDER, 'BoxedIn.ttf')))
styleSheet = getSampleStyleSheet()
style = styleSheet["Normal"]
style.fontName = "PTAstraSerifReg"
style.fontSize = 9
style.alignment = TA_JUSTIFY
style.leading = 3 * mm

styleCentre = deepcopy(style)
styleCentre.alignment = TA_CENTER

styleBold = deepcopy(style)
styleBold.fontName = "PTAstraSerifBold"

styleCentreBold = deepcopy(styleBold)
styleCentreBold.alignment = TA_CENTER

hospital_name = SettingManager.get("org_title")
hospital_address = SettingManager.get("org_address")
hospital_kod_ogrn = SettingManager.get("org_ogrn")

styleT = deepcopy(style)
styleT.alignment = TA_LEFT
styleT.fontSize = 9
styleT.leading = 3 * mm

styleOrg = deepcopy(styleT)
styleOrg.fontSize = 8

styleColontitul = deepcopy(styleT)
styleColontitul.fontSize = 7
styleColontitul.leading = 2 * mm

styleColontitulBold = deepcopy(styleColontitul)
styleColontitulBold.fontName = "PTAstraSerifBold"

styleTBold = deepcopy(styleT)
styleTBold.fontName = "PTAstraSerifBold"

styleOrgBold = deepcopy(styleOrg)
styleOrgBold.fontName = "PTAstraSerifBold"
styleOrgBold.leading = 2 * mm

op_bold_tag = '<font face="PTAstraSerifBold">'
cl_bold_tag = '</font>'

op_boxed_tag = '<font face="BoxedIn" size=17>'
cl_boxed_tag = '</font>'

space_symbol = '&nbsp;'


def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None):
    # Мед. св-во о смерти 106/у
    data_individual = direction.client.get_data_individual()
    data = {}

    title_fields = [
        "Серия",
        "Номер",
        "Дата выдачи",
        "Вид медицинского свидетельства о смерти",
        "Серия предшествующего",
        "Номер предшествующего",
        "Дата выдачи предшествующего",
        "Дата рождения",
        "Дата смерти",
        "Время смерти",
        "Место постоянного жительства (регистрации)",
        "Вид места жительства",
        "Место смерти",
        "Вид места смерти",
        "Типы мест наступления смерти",
        "Новорожденый",
        "Доношенность новорожденного",
        "Место рождения",
        "Масса тела ребёнка при рождении",
        "По счету был ребенок",
        "Дата рождения матери",
        "Возраст матери",
        "ФИО матери",
        "Семейное положение",
        "Образование",
        "Социальная группа",
        "Полис ОМС",
        "СНИЛС",
        "Тип ДУЛ",
        "ДУЛ",
        "Род причины смерти",
        "Смерть от внешних причин",
        "Дата смерти от внешних причин",
        "Время смерти от внешних причин",

        "Тип медицинского работника",
        "Основания для определения причины смерти",
        "а) Болезнь или состояние, непосредственно приведшее к смерти",
        "б) патологическое состояние, которое привело к возникновению вышеуказанной причины:",
        "в) первоначальная причина смерти:",
        "г) внешняя причина при травмах и отравлениях:",
        "II. Прочие важные состояния, способствовавшие смерти, но не связанные с болезнью или патологическим состоянием, приведшим к ней",
        "ДТП",
        "Связь смерти с ДТП",
        "Беременность",
        "Связь смерти с беременностью",
        "ФИО (получатель)",
        "Документ (получатель)",
        "Серия (получатель)",
        "Номер (получатель)",
        "Кем и когда выдан (получатель)",
        "СНИЛС (получатель)",
        "Заполнил",
        "Проверил",
        "Главный врач",
        "Должность",
    ]
    result = fields_result_only_title_fields(iss, title_fields, False)
    for i in result:
        data[i["title"]] = i["value"]


    return ""
