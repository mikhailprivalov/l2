from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate
from io import BytesIO

from integration_framework.common_func import direction_pdf_content
from results.prepare_data import lab_iss_to_pdf


def form_01(request_data):
    direction_id = int(request_data.get("direction"))
    if direction_id:
        return direction_pdf_content(direction_id)


def form_02(request_data):
    directions = request_data.get("directions")
    directions = directions.split(",")
    directions = [int(i) for i in directions]
    data = {'directions': directions, 'excluded': {'dateDir': [], 'titles': []}}
    aggr_lab = lab_iss_to_pdf(data)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=12 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=28 * mm, allowSplitting=1, title="Форма {}".format("Лабораторные анализы")
    )

    doc.build(aggr_lab)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
