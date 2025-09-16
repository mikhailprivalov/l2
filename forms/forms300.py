import locale
import os.path
import sys
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph

from forms.utils import register_fonts
from laboratory.settings import FONTS_FOLDER


def form_01(request_data):
    form_type = request_data.get("type")
    user = request_data.get('user')
    hospital = request_data.get('hospital')
    disable_date = request_data.get('disable_date')
    employee_work_time = request_data.get('employee_work_time')

    register_fonts()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=25 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=6 * mm, allowSplitting=1, title="График рабочего времени")
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.leading = 15
    style.spaceAfter = 0.5 * mm

    objs = []
    objs.append(Paragraph('Привет', style))
    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
