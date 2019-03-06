import sys
from django.db.models import Count
from django.http import HttpResponse
from clients.models import Individual, Document, DocumentType, Card
from forms.models import FormsList
from . import forms100_title_page, forms101_agreement, forms102_contract, forms104_pay

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER
import os.path
from io import BytesIO
from laboratory.settings import FONTS_FOLDER
import os, fnmatch
import simplejson as json

from . import forms_func

def pdf(request):
    """
    Get form's number (decimal type: 101.15 - where "101" is form's group and "15"-number itsels).
    Can't use 1,2,3,4,5,6,7,8,9 for number itsels - which stands after the point.
    Bacause in database field store in decimal format xxx.yy - two number after dot, and active status.
    Must use: 01,02,03-09,10,11,12-19,20,21,22-29,30,31.....
    :param request:
    :return:
    """
    response = HttpResponse(content_type='application/pdf')
    t = request.GET.get("type")
    response['Content-Disposition'] = 'inline; filename="form-' + t + '.pdf"'

    forms_file=None
    obj_form_title=None
    forms_module=None
    pdf = forms_func.form_notfound()

#if not found determinated form in base return - form_notfound()

    try:
        obj_form_title = FormsList.objects.get(title=t, is_active=True)
    except Exception:
        response.write(pdf)
        return response
    try:
        i = Individual.objects.get(pk=request.GET.get('individual'))
    except Exception:
        i=None

    try:
        dir = json.loads(request.GET["dir"])
    except Exception:
        dir=None

# get all distinct documents
    try:
        i_doc = list(Document.objects.values('document_type', 'serial', 'number').
                     filter(individual=i,is_active=True).distinct())
    except Document.DoesNotExist:
        i_doc = None
# get data by only rmis-card
    try:
        i_cards = Card.objects.filter(individual=i, is_archive=False)
    except Card.DoesNotExist:
        i_cards = None
# get form's group from "type". It mus be three number
    try:
        tt = str(int(t[0:3]))
    except:
        tt = '0'

    if len(tt)==3:
        for file in os.listdir('./forms/'):
            if fnmatch.fnmatch(file, 'forms'+tt+'*'):
                forms_file = file[0:-3]
                break
        if forms_file:
            try:
                forms_module = str_to_class(forms_file)
            except Exception:
                response.write(pdf)
                return response
    else: # if len of part for group from "type" less then three number
        response.write(pdf)
        return response

    if ((obj_form_title) and (forms_module)):
        tr = str(t).replace('.','_')
        if hasattr(forms_module, 'form_%s' % tr):
            f = getattr(forms_module, 'form_%s' % tr)
            pdf = f(ind=i,ind_doc=i_doc, ind_card=i_cards, ind_dir = dir)

    response.write(pdf)
    return response


def str_to_class(classname):
    """
    convert name module as 'string' to 'module'
    """
    return getattr(sys.modules[__name__], classname)


# def form_notfound():
#
#     """
#     В случае не верной настройки форм по типам и функциям или переданным аргументам в параметры
#     :return:
#     """
#
#     buffer = BytesIO()
#     pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
#     pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
#     doc = SimpleDocTemplate(buffer, pagesize=A4,
#                             leftMargin=10 * mm,
#                             rightMargin=10 * mm, topMargin=10 * mm,
#                             bottomMargin=10 * mm, allowSplitting=1,
#                             title="Форма {}".format("Паспорт здоровья"))
#     styleSheet = getSampleStyleSheet()
#     style = styleSheet["Normal"]
#     style.fontName = "PTAstraSerifBold"
#     style.fontSize = 16
#     style.leading = 15
#     styleBold = deepcopy(style)
#     styleBold.fontName = "PTAstraSerifBold"
#     styleCenter = deepcopy(style)
#     styleCenter.alignment = TA_CENTER
#     styleCenterBold = deepcopy(styleBold)
#     styleCenterBold.alignment = TA_CENTER
#
#     objs = [
#         Spacer(1, 3 * mm),
#         Paragraph('<font face="PTAstraSerifBold">Ая-я-я-я-я-я-я-яй!</font>',
#                   styleCenter),
#         Spacer(1, 3 * mm),
#         Paragraph('<font face="PTAstraSerifBold">Что-то Администраторы не верно настроили с типами форм! </font>',
#                   styleCenter),
#         Spacer(1, 3 * mm),
#         Paragraph('<font face="PTAstraSerifBold">А-та-та-та им!</font>',
#                   styleCenter),
#         ]
#     doc.build(objs)
#
#     pdf = buffer.getvalue()
#     buffer.close()
#     return pdf