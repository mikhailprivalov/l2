from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, FrameBreak, Table, \
    TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, StyleSheet1
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.graphics.barcode import code128
import datetime
import locale
import sys
import os.path
from io import BytesIO
from . import forms_func
from datetime import *
from dateutil.relativedelta import *
from directions.models import Napravleniya, IstochnikiFinansirovaniya, Issledovaniya
from clients.models import Card, Document
from laboratory.settings import FONTS_FOLDER
from appconf.manager import SettingManager

from datetime import *
import locale
import sys
import pytils
import os.path
from io import BytesIO
from . import forms_func


def form_01(request_data):
    """
    Договор на оказание улуг
    """
    form_name = "Договор оказание медицинских услуг"

    ind_card = Card.objects.get(pk=request_data["card_pk"])
    ind = ind_card.individual
    ind_doc = Document.objects.filter(individual=ind, is_active=True)

    hospital_name = SettingManager.get("org_title")
    hospital_address = SettingManager.get("org_address")
    hospital_kod_ogrn = SettingManager.get("org_ogrn", "<TODO:OGRN>")
    hospital_okpo = SettingManager.get("org_ogrn", "<TODO:OKPO>")

    individual_fio = ind.fio()
    individual_sex = ind.sex
    individual_date_born = ind.bd()

    document_passport = "Паспорт РФ"

    documents = forms_func.get_all_doc(ind_doc)
    document_passport_num = documents['passport']['num']
    document_passport_serial = documents['passport']['serial']
    document_passport_date_start = documents['passport']['date_start']
    document_passport_issued = documents['passport']['issued']
    document_polis = documents['polis']['num']
    document_snils = documents['snils']['num']

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    # http://www.cnews.ru/news/top/2018-12-10_rossijskim_chinovnikam_zapretili_ispolzovat
    # Причина PTAstraSerif использовать

    buffer = BytesIO()
    individual_fio = ind.fio()
    individual_date_born = ind.bd()
    date_now1 = datetime.strftime(datetime.now(), "%d%m%H%M%S")
    num_contract = request_data["card_pk"]+'-'+date_now1
    print(num_contract)