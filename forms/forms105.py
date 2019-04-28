from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.graphics.barcode import code128, qr
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
import os.path
from io import BytesIO
from . import forms_func
from directions.models import Napravleniya, IstochnikiFinansirovaniya, Issledovaniya, PersonContract
from clients.models import Card, Document
from laboratory.settings import FONTS_FOLDER
import simplejson as json
from dateutil.relativedelta import *
from datetime import *
import datetime
import locale
import sys
import pytils
from appconf.manager import SettingManager
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.colors import white, black
import zlib

def form_01(request_data):
    """
    Печать статталона по амбулаторному приему. Входные параметры врач, дата.
    Выходные: форма
    """

    exec_person = request_data['user'].doctorprofile.fio
    doc_confirm = request_data['user'].doctorprofile
    str_date = request_data['date']
    date_confirm = datetime.datetime.strptime(str_date, "%d%m%Y")
    doc_results = forms_func.get_doc_results(doc_confirm, date_confirm)
    talon = forms_func.get_finaldata_talon(doc_results)