import sys
from django.http import HttpResponse
from clients.models import Individual
from forms.models import FormsGroup, FormsList, FormsTemplate
from forms.forms_agreement import form_agree_hiv
from forms import forms_title_page, forms_agreement, forms_contract


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


def pdf(request):
    response = HttpResponse(content_type='application/pdf')
    t = request.GET.get("type")
    response['Content-Disposition'] = 'inline; filename="form-' + t + '.pdf"'
    i = Individual.objects.get(pk=request.GET.get('individual'))
    type_int = int(t)
    try:
        obj_form_title = FormsList.objects.get(type_number=type_int)
        is_hide = obj_form_title.is_hide
    except FormsList.DoesNotExist:
        obj_form_title = None
        out_form = form_notfound()

    if obj_form_title:
        title_f = obj_form_title.title
        group_f = 'forms_' + obj_form_title.form_group.title
        group_f_obj = str_to_class(group_f)

        if (is_hide==False) and (hasattr(group_f_obj, 'form_%s' % title_f)):
            f = getattr(group_f_obj, 'form_%s' % title_f)
            out_form = f(i)
        else:
            out_form = form_notfound()

    pdf = out_form
    response.write(pdf)
    return response


def str_to_class(classname):
    """
    convwert name module as 'string' to 'module'
    """
    return getattr(sys.modules[__name__], classname)

def form_notfound():

    """
    В случае не верной настройки форм по типам и функциям
    :return:
    """

    buffer = BytesIO()
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=10 * mm,
                            rightMargin=10 * mm, topMargin=10 * mm,
                            bottomMargin=10 * mm, allowSplitting=1,
                            title="Форма {}".format("Паспорт здоровья"))
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifBold"
    style.fontSize = 16
    style.leading = 15
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER

    objs = [
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifBold">Ая-я-я-я-я-я-я-яй!</font>',
                  styleCenter),
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifBold">Что-то Администраторы не верно настроили с типами форм! </font>',
                  styleCenter),
        Spacer(1, 3 * mm),
        Paragraph('<font face="PTAstraSerifBold">А-та-та-та им!</font>',
                  styleCenter),
        ]
    doc.build(objs)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf