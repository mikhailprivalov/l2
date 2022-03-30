from laboratory.utils import strdate
from utils.dates import normalize_date
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from directions.models import Napravleniya
from results.prepare_data import fields_result_only_title_fields, fields_result, previous_doc_refferal_result, previous_laboratory_result, table_part_result
from directions.models import Issledovaniya
from laboratory.settings import FONTS_FOLDER
import os.path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def form_01(direction, iss: Issledovaniya, fwb, doc, leftnone, user=None):
    # Утверждено Приказом Министерства здравоохранения Иркутской области от 22 мая 2013 г. N 83-МПР
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    
    title_research = iss.research.title

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 11
    style.leading = 12
    style.spaceAfter = 1.5 * mm

    styleBold = deepcopy(style)
    styleBold.fontName = 'PTAstraSerifBold'

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 15
    styleCenterBold.fontName = 'PTAstraSerifBold'

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm
    styleT.face = 'PTAstraSerifReg'

    styleTCentre = deepcopy(styleT)
    styleTCentre.alignment = TA_CENTER
    styleTCentre.fontSize = 13

    data = title_fields(iss)

    opinion = [
        [
            Paragraph(f'<font size=11>{direction.hospital_title}<br/>Адрес: {direction.hospital_address}<br/>ОГРН: {direction.hospital.ogrn} <br/> </font>', styleT),
            Paragraph('<font size=9 >Утверждено<br/>Приказом Министерства здравоохранения<br/>Иркутской области от 22 мая 2013 г. N 83-МПР</font>', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [100 * mm])
    tbl.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.75, colors.white), ('LEFTPADDING', (1, 0), (-1, -1), 55 * mm), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))

    fwb.append(tbl)
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph(f'НАПРАВЛЕНИЕ № {direction.pk}', styleCenterBold))
    fwb.append(Paragraph('в медицинские организации Иркутской области', styleCenterBold))
    fwb.append(Spacer(1, 3 * mm))
    space_symbol = '&nbsp;'
    fwb.append(Paragraph(f'От: {strdate(direction.data_sozdaniya)}', style))
    fwb.append(Paragraph(f'Фамилия, Имя, Отчество: {direction.client.individual.fio()}', style))
    sex = direction.client.individual.sex
    if sex == "м":
        sex = f'{sex}-1'
    else:
        sex = f'{sex}-2'
    born = direction.client.individual.bd().split('.')
    fwb.append(Paragraph(f'Дата <u>{born[0]}</u> Месяц <u>{born[1]}</u> Год рождения <u>{born[2]}</u> Пол {sex} ', style))
    fwb.append(Paragraph(f'Рабочий, домашний телефон : {direction.client.phone}', style))
    polis_num = ''
    polis_issue = ''
    ind_data = direction.client.get_data_individual()
    if ind_data['oms']['polis_num']:
        polis_num = ind_data['oms']['polis_num']
    if ind_data['oms']['polis_issued']:
        polis_issue = ind_data['oms']['polis_issued']
    address = ind_data['main_address']
    fwb.append(Paragraph(f'Регистрация по месту жительства: {address}', style))
    fwb.append(Paragraph(f"Страховой полис серия: _______ №{polis_num}", style))
    fwb.append(Paragraph(f"Страховая компания (наименование): {polis_issue}", style))
    external_org = direction.external_organization.title if direction.external_organization else ""
    fwb.append(Paragraph(f"Направляется в: ", style))
    fwb.append(Paragraph("Дата приема _______________________ Время приема _________________", style))
    fwb.append(Paragraph(f"Наименование медицинской организации по месту прикрепления: {direction.hospital_address} {direction.hospital_title}", style))
    fwb.append(Paragraph(f"Наименование направившей медицинской организации: {direction.hospital_address} {direction.hospital_title}", style))
    fwb.append(Paragraph("Направлен(а) на:", style))
    fwb.append(Paragraph("1) консультацию (вписать специалистов)", style))
    if iss.research.is_doc_refferal:
        fwb.append(Paragraph(f"{title_research}", styleBold))
    fwb.append(Paragraph("2) исследование (указать вид исследования)", style))
    if iss.research.is_doc_refferal:
        fwb.append(Paragraph(f"{title_research}", styleBold))
    fwb.append(Paragraph("3) госпитализацию", style))
    fwb.append(Paragraph("____________________________________________________", style))
    fwb.append(Paragraph("Цель консультации (и, или) исследования (нужное обвести):", style))
    descriptive_values = []
    laboratory_value, purpose, table_value = None, None, None
    main_diagnos, near_diagnos, anamnes, other_purpose = '', '', '', ''

    # for param in directionection_params:
    #     if param.field_type == 24:
    #         laboratory_value = param.value
    #     if param.field_type == 27:
    #         table_value = param.value
    #     if param.field_type in [26, 25]:
    #         descriptive_values.append(param.value)
    #     if param.title == 'Цель':
    #         purpose = param.value
    #     if param.title == 'Прочие цели':
    #         other_purpose = param.value
    #     if param.title == 'Диагноз основной':
    #         main_diagnos = param.value
    #     if param.title == 'Диагноз сопутствующий':
    #         near_diagnos = f"{near_diagnos} {param.value}"
    #     if param.title == 'Данные анамнеза':
    #         anamnes = param.value

    if purpose:
        fwb.append(Paragraph(f"{space_symbol * 10} {purpose} {other_purpose}", style))
    else:
        fwb.append(Paragraph(f"{space_symbol * 10}01 - дообследование при неясном диагнозе;", style))
        fwb.append(Paragraph(f"{space_symbol * 10}02 - уточнение диагноза;", style))
        fwb.append(Paragraph(f"{space_symbol * 10}03 - для коррекции лечения;", style))
        fwb.append(Paragraph(f"{space_symbol * 10}04 - дообследование для госпитализации;", style))
        fwb.append(Paragraph(f"{space_symbol * 10}05 - и прочие цели (нужное вписать) __________________", style))
    fwb.append(Paragraph("Диагноз направившей медицинской организации (диагноз/ код диагноза в соответствии с МКБ10):", style))
    if main_diagnos:
        fwb.append(Paragraph(f"Основной{main_diagnos}", style))
    else:
        fwb.append(Paragraph("Основной ______________________________________________________________________________________", style))
    if near_diagnos:
        fwb.append(Paragraph(f"Сопутствующий {near_diagnos}", style))
    else:
        fwb.append(Paragraph("Сопутствующий ______________________________________________________________________________________", style))
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph("Выписка из амбулаторной карты:", style))
    fwb.append(Paragraph("(данные анамнеза, клиники, предварительного обследования и проведенного лечения)", style))
    if anamnes:
        fwb.append(Paragraph(f"{anamnes}", style))
    else:
        fwb.append(Paragraph("______________________________________________________________________________________", style))
        fwb.append(Paragraph("______________________________________________________________________________________", style))
        fwb.append(Paragraph("______________________________________________________________________________________", style))
        fwb.append(Paragraph("______________________________________________________________________________________", style))
        fwb.append(Paragraph("______________________________________________________________________________________", style))
    for v in descriptive_values:
        fwb = previous_doc_refferal_result(v, fwb)
    if laboratory_value:
        lab_values = previous_laboratory_result(laboratory_value)
        if lab_values:
            fwb.extend(lab_values)
    if table_value:
        table_value_result = table_part_result(table_value)
        if table_value_result:
            fwb.extend(table_value_result)

    fwb.append(Paragraph("______________________________________________________________________________________", style))
    fwb.append(Paragraph("Сведения о профилактических прививках (для детей до 18 лет) ________________________", style))
    fwb.append(Paragraph("______________________________________________________________________________________", style))
    fwb.append(Paragraph("______________________________________________________________________________________", style))
    fwb.append(Paragraph("______________________________________________________________________________________", style))
    fwb.append(Paragraph("Справка об отсутствии инфекционных контактов (для детей до 18 лет), выданная не ранее 3 дней на дату поступления в ОГУЗ ", style))
    fwb.append(Paragraph("______________________________________________________________________________________", style))
    fwb.append(Paragraph("Врач ___________________________________________________________________________", style))
    fwb.append(Paragraph('телефон ____________________________ "_____" _____________ 20__ г.', style))
    fwb.append(Paragraph("Руководитель направившей медицинской организации", style))
    fwb.append(Paragraph("Согласие пациента на передачу сведений электронной почтой для осуществления предварительной записи и передачи заключения:", style))

    return fwb


def title_fields(iss):
    title_fields = [
        "Куда направляется"
        "Цель",
        "Диагноз основной",
        "Дата приема",
        "Направлен(а) на",
        "Наименование (консультации, исследования, отделения)",
        "Данные анамнеза",
        "Результаты лабораторные",
        "Результаты диагностические",
        "Результаты консультационные",
    ]

    result = fields_result_only_title_fields(iss, title_fields, False)

    data = {i['title']: i['value'] for i in result}
    print(data)

    return result

