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


def form_01(direction, iss: Issledovaniya, fwb, doc, leftnone, user=None):
    # Заключение на ВМП
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

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

    title_field_result = ["Дата"]
    data_fields_result = fields_result_only_title_fields(iss, title_field_result)
    date_protocol = ""
    for i in data_fields_result:
        if i["title"] == "Дата":
            date_protocol = i["value"]

    history_num = ''
    if direction.parent and direction.parent.research.is_hospital:
        history_num = f"(cтационар-{str(direction.parent.napravleniye_id)})"

    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f'ЗАКЛЮЧЕНИЕ № {direction.pk} {history_num} ', styleCenterBold))
    fwb.append(Paragraph('медицинского специалиста соответствующего профиля', styleCenterBold))
    doc_profile = iss.doc_confirmation.specialities.title
    doc_fio = iss.doc_confirmation.get_full_fio()
    fwb.append(Paragraph(f'{doc_profile} {doc_fio}', styleCenterBold))

    open_bold_tag = "<font face =\"PTAstraSerifBold\">"
    close_tag_bold = "</font>"
    fwb.append(Spacer(1, 4 * mm))
    fwb.append(Paragraph(f'{open_bold_tag}Дата:{close_tag_bold} {date_protocol}', style_ml))
    fwb.append(Paragraph(f'{open_bold_tag}ФИО пациента:{close_tag_bold} {direction.client.individual.fio()}', style_ml))
    sex = direction.client.individual.sex
    space_symbol = '&nbsp;'
    fwb.append(Paragraph(f'{open_bold_tag}Дата рождения:{close_tag_bold} {direction.client.individual.bd()}, {space_symbol * 5} {open_bold_tag}Пол:{close_tag_bold} {sex}', style_ml))
    polis_num = ''
    polis_issue = ''
    snils = ''
    ind_data = direction.client.get_data_individual()
    if ind_data['oms']['polis_num']:
        polis_num = ind_data['oms']['polis_num']
    if ind_data['oms']['polis_issued']:
        polis_issue = ind_data['oms']['polis_issued']
    if ind_data['snils']:
        snils = ind_data['snils']
    fwb.append(Paragraph(f'{open_bold_tag}Полис ОМС:{close_tag_bold}{polis_num}-{polis_issue} {space_symbol * 4} {open_bold_tag}6. СНИЛС:{close_tag_bold} {snils}', style_ml))
    address = ind_data['main_address']
    fwb.append(Paragraph(f'{open_bold_tag}Место регистрации:{close_tag_bold} {address}', style_ml))

    fwb = fields_result(iss, fwb, title_field_result)

    fwb.append(Spacer(1, 15 * mm))
    fwb.append(Paragraph(f"Медицинский специалист ___________________ {doc_fio}", style))

    return fwb


def form_02(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None):
    # Направление на ВМП
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.alignment = TA_JUSTIFY

    style_ml = deepcopy(style)
    style_ml.spaceAfter = 2 * mm

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 15
    styleCenterBold.fontName = 'PTAstraSerifBold'

    hospital_name = direction.hospital.title
    phones = direction.hospital.phones
    hospital_address = direction.hospital.address

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    fwb.append(Spacer(1, 5 * mm))
    open_bold_tag = "<font face =\"PTAstraSerifBold\">"
    close_tag_bold = "</font>"

    fwb.append(Spacer(1, 4 * mm))
    fwb.append(Paragraph(f'{hospital_name.upper()}', styleCenterBold))
    fwb.append(Paragraph(f'{hospital_address} тел: {phones}', styleCenter))
    fwb.append(Paragraph(f'{direction.doc.podrazdeleniye.title.upper()}', styleCenter))
    fwb.append(HRFlowable(width=190 * mm, spaceAfter=3 * mm, spaceBefore=3 * mm, color=colors.black, thickness=1.5))

    fwb.append(Spacer(1, 2 * mm))

    title_field_result = ["Руководитель медицинской организации", "Дата"]
    data_fields_result = fields_result_only_title_fields(iss, title_field_result)
    main_manager, date_protocol = "", ""
    for i in data_fields_result:
        if i["title"] == "Руководитель медицинской организации":
            main_manager = i["value"]
        if i["title"] == "Дата":
            date_protocol = normalize_date(i["value"])

    fwb.append(Paragraph(f'Исх.№ <u>{direction.pk}</u> от <u>{date_protocol or str(iss.medical_examination)}</u>', style))
    fwb.append(Spacer(1, 2 * mm))
    fwb.append(Paragraph('НАПРАВЛЕНИЕ', styleCenterBold))
    fwb.append(Paragraph('на госпитализацию для оказания высокотехнологичной медицинской помощи', styleCenterBold))
    fwb.append(Spacer(1, 4 * mm))
    fwb.append(Paragraph(f'{open_bold_tag}ФИО пациента:{close_tag_bold} {direction.client.individual.fio()}', style_ml))
    sex = direction.client.individual.sex
    space_symbol = '&nbsp;'
    fwb.append(Paragraph(f'{open_bold_tag}Дата рождения:{close_tag_bold} {direction.client.individual.bd()} {open_bold_tag} - Пол:{close_tag_bold} {sex}, {space_symbol * 5}', style_ml))
    polis_num = ''
    polis_issue = ''
    snils = ''
    ind_data = direction.client.get_data_individual()
    if ind_data['oms']['polis_num']:
        polis_num = ind_data['oms']['polis_num']
    if ind_data['oms']['polis_issued']:
        polis_issue = ind_data['oms']['polis_issued']
    if ind_data['snils']:
        snils = ind_data['snils']
    fwb.append(Paragraph(f'{open_bold_tag}Полис ОМС:{close_tag_bold} {polis_num}', style_ml))
    fwb.append(Paragraph(f'{open_bold_tag}Название страховой медицинской организации:{close_tag_bold} {polis_issue}', style_ml))
    fwb.append(Paragraph(f'{open_bold_tag}СНИЛС:{close_tag_bold} {snils}', style_ml))
    address = ind_data['main_address']
    fwb.append(Paragraph(f'{open_bold_tag}Адрес регистрации:{close_tag_bold} {address}', style_ml))

    fwb = fields_result(iss, fwb, title_field_result)
    fwb.append(Spacer(1, 10 * mm))

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.leading = 5 * mm

    opinion = [
        [
            Paragraph('Руководитель медицинской организации', styleT),
            Paragraph('___________________', styleT),
            Paragraph(f'{main_manager}', styleT),
        ],
        [
            Paragraph('Лечащий врач', styleT),
            Paragraph('___________________', styleT),
            Paragraph(f'{iss.doc_confirmation.get_full_fio()}', styleT),
        ],
    ]

    tbl = Table(opinion, hAlign='LEFT', colWidths=[57 * mm, 45 * mm, 57 * mm], rowHeights=[13 * mm, 13 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (0, 0), (-1, -1), 0 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ]
        )
    )

    fwb.append(tbl)
    fwb.append(Spacer(1, 10 * mm))
    fwb.append(Paragraph("Печать направляющей медицинской организации", style_ml))

    return fwb


def form_03(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None):
    # Рапорт ВМП
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.alignment = TA_JUSTIFY

    style_ml = deepcopy(style)
    style_ml.spaceAfter = 2 * mm

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 15
    styleCenterBold.fontName = 'PTAstraSerifBold'

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.leading = 5 * mm

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    fwb.append(Spacer(1, 3 * mm))
    title_field_result = ["Кому", "От кого", "Отделение", "Дата"]
    data_fields_result = fields_result_only_title_fields(iss, title_field_result)
    main_manager, from_who, departmnet, date_protocol = "", "", "", ""
    for i in data_fields_result:
        if i["title"] == "Кому":
            main_manager = i["value"]
        if i["title"] == "От кого":
            from_who = i["value"]
        if i["title"] == "Отделение":
            departmnet = i["value"]
        if i["title"] == "Дата":
            date_protocol = normalize_date(i["value"])

    opinion = [
        [
            Paragraph(' ', styleT),
            Paragraph(f'{main_manager}<br/>от<br/>{from_who}', styleT),
        ],
    ]

    tbl = Table(opinion, colWidths=[120 * mm, 60 * mm])
    tbl.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.75, colors.white), ('LEFTPADDING', (1, 0), (-1, -1), 2 * mm), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))

    fwb.append(tbl)
    fwb.append(Spacer(1, 3 * mm))

    open_bold_tag = "<font face =\"PTAstraSerifBold\">"
    close_tag_bold = "</font>"

    fwb.append(Spacer(1, 4 * mm))
    fwb.append(Paragraph('Рапорт', styleCenterBold))
    fwb.append(Spacer(1, 4 * mm))
    fwb.append(Paragraph(f'Довожу до Вашего сведения, что в отделение {departmnet} поступил пациент, нуждающийся в оказании ВМП', style_ml))
    fwb.append(Spacer(1, 2 * mm))
    fwb.append(Paragraph(f'{open_bold_tag}ФИО пациента:{close_tag_bold} {direction.client.individual.fio()}', style_ml))
    sex = direction.client.individual.sex
    space_symbol = '&nbsp;'
    fwb.append(Paragraph(f'{open_bold_tag}Дата рождения:{close_tag_bold} {direction.client.individual.bd()} {open_bold_tag} - Пол:{close_tag_bold} {sex}, {space_symbol * 5}', style_ml))
    polis_num = ''
    polis_issue = ''
    snils = ''
    ind_data = direction.client.get_data_individual()
    if ind_data['oms']['polis_num']:
        polis_num = ind_data['oms']['polis_num']
    if ind_data['oms']['polis_issued']:
        polis_issue = ind_data['oms']['polis_issued']
    if ind_data['snils']:
        snils = ind_data['snils']
    fwb.append(Paragraph(f'{open_bold_tag}Полис ОМС:{close_tag_bold} {polis_num}', style_ml))
    fwb.append(Paragraph(f'{open_bold_tag}Название страховой медицинской организации:{close_tag_bold} {polis_issue}', style_ml))
    fwb.append(Paragraph(f'{open_bold_tag}СНИЛС:{close_tag_bold} {snils}', style_ml))
    address = ind_data['main_address']
    fwb.append(Paragraph(f'{open_bold_tag}Адрес регистрации:{close_tag_bold} {address}', style_ml))

    fwb = fields_result(iss, fwb, title_field_result)

    fwb.append(Spacer(1, 7 * mm))
    opinion = [
        [
            Paragraph('Лечащий врач', styleT),
            Paragraph('___________________', styleT),
            Paragraph(f'{iss.doc_confirmation.get_full_fio()}', styleT),
        ],
        [
            Paragraph(f'{date_protocol} ', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
        ],
    ]

    tbl = Table(opinion, hAlign='LEFT', colWidths=[57 * mm, 45 * mm, 57 * mm], rowHeights=[10 * mm, 10 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (0, 0), (-1, -1), 2 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ]
        )
    )
    fwb.append(tbl)

    return fwb
