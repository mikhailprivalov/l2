from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_JUSTIFY
import directory.models as directory
from directions.models import ParaclinicResult
from utils.dates import normalize_date
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus import PageBreak, Spacer, KeepTogether, Flowable, Frame, PageTemplate, NextPageTemplate, SimpleDocTemplate, FrameBreak
from reportlab.lib.pagesizes import A4, landscape, portrait
import datetime
from appconf.manager import SettingManager
import simplejson as json
from io import BytesIO


def form_01(direction, iss, fwb, doc, leftnone, count_direction, is_different_form):
    # Форма для печати наркозной карты - течения Анестези при операции

    # p_frame = Frame(5 * mm, 30 * mm, 200 * mm, 277 * mm, leftPadding=10 * mm, rightPadding=10 * mm, topPadding=10 * mm, bottomPadding=10 * mm, id='portrait_frame', showBoundary=1)
    #
    # l_frame = Frame(0 * mm, 0 * mm, 297 * mm, 210 * mm, leftPadding=20 * mm, rightPadding=10 * mm, topPadding=10 * mm, bottomPadding=10 * mm, id='landscape_frame', showBoundary=1)
    #
    # portrait_tmpl = PageTemplate(id='portrait_tmpl', frames=[p_frame], pagesize=portrait(A4))
    # landscape_tmpl = PageTemplate(id='landscape_tmpl', frames=[l_frame], pagesize=landscape(A4))
    #
    # # if is_different_form and count_direction > 1:
    # doc.addPageTemplates(landscape_tmpl)
    # fwb.append(NextPageTemplate('landscape_tmpl'))
    # fwb.append(PageBreak())


    # size_form = {0: portrait(A4), 1: landscape(A4)}
    # page_templates = {0: portrait_tmpl, 1: landscape_tmpl}

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "FreeSans"
    style.fontSize = 9
    style.alignment = TA_JUSTIFY
    style_ml = deepcopy(style)
    style_ml.leftIndent = 5 * mm
    styleBold = deepcopy(style)
    styleBold.fontName = "FreeSansBold"

    date, time = '', ''
    patient_fio = direction.client.individual.fio()

    fwb.append(Paragraph('Наркозная карта', style))
    fwb.append(Spacer(1, 10 * mm))

    txt = ''
    for group in directory.ParaclinicInputGroups.objects.filter(research=iss.research).order_by("order"):
        results = ParaclinicResult.objects.filter(issledovaniye=iss, field__group=group).exclude(value="").order_by("field__order")
        if results.exists():
            if group.show_title and group.title != "":
                txt += "<font face=\"FreeSansBold\">{}:</font>&nbsp;".format(group.title.replace('<', '&lt;').replace('>', '&gt;'))
            vals = []
            for r in results:
                field_type = r.get_field_type()
                v = r.value.replace('<', '&lt;').replace('>', '&gt;').replace("\n", "<br/>")
                v = v.replace('&lt;sub&gt;', '<sub>')
                v = v.replace('&lt;/sub&gt;', '</sub>')
                v = v.replace('&lt;sup&gt;', '<sup>')
                v = v.replace('&lt;/sup&gt;', '</sup>')

                if field_type == 1:
                    vv = v.split('-')
                    if len(vv) == 3:
                        v = "{}.{}.{}".format(vv[2], vv[1], vv[0])
                if field_type in [11, 13]:
                    v = '<font face="FreeSans" size="8">{}</font>'.format(v.replace("&lt;br/&gt;", " "))

                if r.field.get_title(force_type=field_type) != "":
                    vals.append("{}:&nbsp;{}".format(r.field.get_title().replace('<', '&lt;').replace('>', '&gt;'), v))
                else:
                    vals.append(v)
            txt += "; ".join(vals)
            txt = txt.strip()
            if len(txt) > 0 and txt.strip()[-1] != ".":
                txt += ". "
            elif len(txt) > 0:
                txt += " "

    fwb.append(Paragraph(txt, style))

    # doc.addPageTemplates(portrait_tmpl)
    # fwb.append(NextPageTemplate('portrait_tmpl'))
    # fwb.append(FrameBreak())

    return fwb


def form_02():
    # Форма для печати реанимационной карты - за 1 день
    return ''
