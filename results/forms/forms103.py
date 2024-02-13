from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from laboratory.settings import FONTS_FOLDER
from laboratory.utils import strdate
from medical_certificates.forms.forms380 import protocol_fields_result
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from appconf.manager import SettingManager
import os.path
from .flowable import FrameData
from directions.models import Issledovaniya


def form_01(direction, iss: Issledovaniya, fwb, doc, leftnone, user=None, **kwargs):
    # Справка-вождение
    template = add_template(iss, direction, 0)
    fwb.extend(template)
    template = add_template(iss, direction, 107)
    fwb.extend(template)

    return fwb


def add_template(iss: Issledovaniya, direction, offset=0):
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
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

    text = (
        f'<font size=10>{hospital_full_name}<br/>{hospital_short_name}<br/>Адрес: {hospital_doc_confirm.address}'
        f'{hospital_doc_confirm.phones}<br/>Лицензия на осуществление медицинской деятельности <br/> {hospital_doc_confirm.license_data}<br/>'
        f'</font>'
    )

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 15
    styleCenterBold.fontName = 'PTAstraSerifBold'

    styleCenter = deepcopy(styleCenterBold)
    styleCenter.fontName = 'PTAstraSerifReg'
    obj = []
    obj.append(FrameData(0, (-15 - offset) * mm, 120, 28, text=text, style=style))
    obj.append(FrameData(0, (-20 - offset) * mm, 180, 5, text='Медицинская справка', style=styleCenterBold))
    obj.append(FrameData(0, (-23 - offset) * mm, 180, 5, text=f'№ {direction.pk}', style=styleCenter))
    obj.append(
        FrameData(
            0,
            (-32 - offset) * mm,
            180,
            15,
            text='по результатам обследования водителя<br/>транспартнго средства (кандидата в водители траспортного средства)<br/><u>врачом-психиатром</u>',
            style=styleCenter,
        )
    )
    result = protocol_fields_result(iss)
    main_address, identified_final = '', ''
    for i in result:
        if i["title"] == "Медицинское заключение":
            identified_final = i["value"].replace('<', '&lt;').replace('>', '&gt;')
        elif i["title"] == "Место регистрации":
            main_address = i["value"]

    text = (
        f'1. Фамилия, имя, отчество (при наличии): {direction.client.individual.fio()}<br/>'
        f'2. Дата рождения: {direction.client.individual.bd()}<br/>'
        f'3. Место регистрации: {main_address}<br/>'
        f'4. Медицинское заключение: {identified_final}'
    )
    obj.append(FrameData(0, (-60 - offset) * mm, 180, 40, text=text, style=style))

    date_confirm = strdate(iss.time_confirmation)
    opinion = [
        [
            Paragraph(f'<u>{date_confirm}</u>', styleCenter),
            Paragraph(f'<u>врач-психиатр, {iss.doc_confirmation.get_full_fio()}</u>', styleCenter),
        ],
        [
            Paragraph('(Дата)', styleCenter),
            Paragraph('Должность (ФИО)', styleCenter),
        ],
    ]
    tbl = Table(opinion, colWidths=(90 * mm, 90 * mm))

    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
    )
    obj.append(FrameData(0, (-75 - offset) * mm, 180, 20, text=text, style=style, tbl=tbl))

    return obj
