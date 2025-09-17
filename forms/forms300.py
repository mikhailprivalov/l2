from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph

from forms.utils import register_fonts, create_style


def form_01(request_data):
    """
    Создание печатной формы графика рабочего времени
    """
    register_fonts()
    style = create_style()

    objs = []
    objs.append(Paragraph('Привет', style))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=25 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=6 * mm, allowSplitting=1, title="График рабочего времени")
    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
