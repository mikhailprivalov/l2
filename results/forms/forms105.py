from reportlab.lib.pagesizes import A4

from laboratory.utils import strdate
from utils.dates import normalize_date
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from directions.models import Napravleniya
from results.prepare_data import fields_result_only_title_fields, fields_result
from directions.models import Issledovaniya
from laboratory.settings import FONTS_FOLDER
import os.path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from laboratory.settings import EXTRA_MASTER_RESEARCH_PK, EXTRA_SLAVE_RESEARCH_PK
from django.http import HttpResponse, JsonResponse
import simplejson as json
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, FrameBreak, Table, TableStyle, PageBreak


def form_01(request):
    # Результат Экстренные извещения
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="extra_note.pdf"'

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.alignment = TA_JUSTIFY

    style_ml = deepcopy(style)
    style_ml.spaceAfter = 2 * mm

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 15
    styleCenterBold.fontName = 'PTAstraSerifBold'

    pk = [x for x in json.loads(request.GET["pk"]) if x is not None]

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=25 * mm, rightMargin=5 * mm, topMargin=6 * mm, bottomMargin=6 * mm, allowSplitting=1, title="Форма {}".format("Эпид. извещение"))
    objs = []

    doc.build(objs)

    pdf = buffer.getvalue()
    buffer.close()

    response.write(pdf)  # Запись PDF в ответ

    return response

