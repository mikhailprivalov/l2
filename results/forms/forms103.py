from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from laboratory.settings import FONTS_FOLDER
from medical_certificates.forms.forms380 import protocol_fields_result
from utils.dates import normalize_date
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Frame, KeepInFrame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import directory.models as directory
from directions.models import ParaclinicResult
from appconf.manager import SettingManager
from results.prepare_data import text_to_bold
import os.path

from utils.flowable import InteractiveTextField
from .flowable import insertOwnFrame


def form_01(direction, iss, fwb, doc, leftnone, user=None, canv=None):
    # Справка-вождение
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10
    style.alignment = TA_JUSTIFY

    style_ml = deepcopy(style)
    style_ml.leftIndent = 5 * mm
    style_ml.spaceAfter = 0.5 * mm

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"

    hospital_full_name = SettingManager.get("rmis_orgname")
    hospital_short_name = SettingManager.get("org_title")
    hospital_doc_confirm = iss.doc_confirmation.hospital

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    opinion = [
        [
            Paragraph(f'<font size=10>{hospital_full_name}<br/>{hospital_short_name}<br/>Адрес: {hospital_doc_confirm.address}, '
                      f'{hospital_doc_confirm.phones}<br/>Лицензия на осуществление медицинской деятельности <br/> {hospital_doc_confirm.license_data}</font>', styleT),
            Paragraph('', styleT),
        ],
    ]
    tbl = Table(opinion,  colWidths=[130 * mm, 60 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                ('LEFTPADDING', (1, 0), (-1, -1), 2 * mm),
                ('LEFTPADDING', (0, 0), (0, -1), 2 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )

    fwb.append(tbl)

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 15
    styleCenterBold.fontName = 'PTAstraSerifBold'

    styleCenter = deepcopy(styleCenterBold)
    styleCenter.fontName = 'PTAstraSerifReg'

    fwb.append(Paragraph(f'Медицинская справка', styleCenterBold))
    fwb.append(Paragraph(f'№ {direction.pk}', styleCenter))
    fwb.append(Paragraph(f'по результатам обследования водителя<br/>транспартнго средства (кандидата в водители траспортного средства)<br/><u>врачом-психиатром</u>', styleCenter))

    fwb.append(Spacer(1, 4 * mm))
    result = protocol_fields_result(iss)
    main_address, identified_final = '', ''
    for i in result:
        if i["title"] == "Медицинское заключение":
            identified_final = i["value"].replace('<', '&lt;').replace('>', '&gt;')
        elif i["title"] == "Место регистрации":
            main_address = i["value"]

    fwb.append(Paragraph(f'1. Фамилия, имя, отчество (при наличии): {direction.client.individual.fio()}', style))
    fwb.append(Paragraph(f'2. Дата рождения: {direction.client.individual.bd()}', style))
    fwb.append(Paragraph(f'3. Место регистрации: {main_address}', style))
    # fwb.append(Paragraph(f'4. Медицинское заключение: {identified_final}', style))

    # medical_text_frame = Frame(5 * mm, 181 * mm, 175 * mm, 20 * mm, id='med_text', leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=1)
    box = insertOwnFrame(text=identified_final)
    fwb.append(box)

    return fwb
