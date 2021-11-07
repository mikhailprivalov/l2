from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from directions.models import Napravleniya
from appconf.manager import SettingManager
import os.path
from laboratory.settings import FONTS_FOLDER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .flowable import FrameDataUniversal
from directions.models import Issledovaniya
from ..prepare_data import fields_result_only_title_fields
import simplejson as json
import datetime
from dateutil.relativedelta import relativedelta
from hospitals.models import Hospitals

pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
pdfmetrics.registerFont(TTFont('digit8', os.path.join(FONTS_FOLDER, 'digit88table.ttf')))
# pdfmetrics.registerFont(TTFont('digit88table', os.path.join(FONTS_FOLDER, 'digit88table.ttf')))
styleSheet = getSampleStyleSheet()
style = styleSheet["Normal"]
style.fontName = "PTAstraSerifReg"
style.fontSize = 9
style.alignment = TA_JUSTIFY
style.leading = 3 * mm

styleCentre = deepcopy(style)
styleCentre.alignment = TA_CENTER

styleBold = deepcopy(style)
styleBold.fontName = "PTAstraSerifBold"

styleCentreBold = deepcopy(styleBold)
styleCentreBold.alignment = TA_CENTER

hospital_name = SettingManager.get("org_title")
hospital_address = SettingManager.get("org_address")
hospital_kod_ogrn = SettingManager.get("org_ogrn")

styleT = deepcopy(style)
styleT.alignment = TA_LEFT
styleT.fontSize = 9.5
styleT.leading = 3.3 * mm

styleDiag = deepcopy(styleT)
styleDiag.fontSize = 11

styleOrg = deepcopy(styleT)
styleOrg.fontSize = 9

styleMicro = deepcopy(styleT)
styleMicro.fontSize = 5.5
styleMicro.alignment = TA_CENTER

styleOrgCentre = deepcopy(styleOrg)
styleOrgCentre.alignment = TA_CENTER

styleColontitul = deepcopy(styleT)
styleColontitul.fontSize = 7
styleColontitul.leading = 2 * mm

styleColontitulBold = deepcopy(styleColontitul)
styleColontitulBold.fontName = "PTAstraSerifBold"

styleTBold = deepcopy(styleT)
styleTBold.fontName = "PTAstraSerifBold"

styleOrgBold = deepcopy(styleOrg)
styleOrgBold.fontName = "PTAstraSerifBold"
styleOrgBold.leading = 2 * mm

op_bold_tag = '<font face="PTAstraSerifBold">'
cl_bold_tag = '</font>'

op_boxed_tag = '<font face="digit8" size=15.5>'
cl_boxed_tag = '</font>'

# op_boxed_tag = '<font face="digit88table" size=8>'
# cl_boxed_tag = '</font>'

digit_one = f"{op_boxed_tag}1{cl_boxed_tag}"
digit_two = f"{op_boxed_tag}2{cl_boxed_tag}"
digit_three = f"{op_boxed_tag}3{cl_boxed_tag}"
digit_four = f"{op_boxed_tag}4{cl_boxed_tag}"
digit_five = f"{op_boxed_tag}5{cl_boxed_tag}"
digit_six = f"{op_boxed_tag}6{cl_boxed_tag}"
digit_seven = f"{op_boxed_tag}7{cl_boxed_tag}"
digit_eight = f"{op_boxed_tag}8{cl_boxed_tag}"
digit_nine = f"{op_boxed_tag}9{cl_boxed_tag}"



space_symbol = '&nbsp;'
line_break = "<br/>"

def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None):
    # Мед. св-во о смерти 106/-2у
    data_individual = direction.client.get_data_individual()
    data = {}

    title_fields = [
        "Серия",
        "Номер",
        "Дата выдачи",
        "Вид медицинского свидетельства о смерти",
        "Серия предшествующего",
        "Номер предшествующего",
        "Дата выдачи предшествующего",
        "Дата рождения",
        "Дата смерти",
        "Время смерти",
        "Место постоянного жительства (регистрации)",
    ]
    result = fields_result_only_title_fields(iss, title_fields, False)
    for i in result:
        data[i["title"]] = i["value"]

    hospital_obj: Hospitals = user.doctorprofile.get_hospital()
    data['org'] = {"full_title": hospital_obj.title, "org_address": hospital_obj.address, "org_license": hospital_obj.license_data, "org_okpo": hospital_obj.okpo}

    template = add_template(iss, direction, data, 5 * mm)
    fwb.extend(template)
    template = add_line_split(iss, direction, 4 * mm)
    fwb.extend(template)
    template = death_data(iss, direction, data, 0 * mm)
    fwb.extend(template)
    fwb.append(PageBreak())

    template = second_page_add_template(iss, direction, data, 0 * mm)
    fwb.extend(template)
    template = add_line_split(iss, direction, -1 * mm)
    fwb.extend(template)
    template = death_data2(iss, direction, data, -5 * mm)
    fwb.extend(template)

    return fwb


def add_template(iss: Issledovaniya, direction, fields, offset=0):
    # Мед. св-во о смерти 106-2/у
    text = []
    text = title_data("КОРЕШОК МЕДИЦИНСКОГО СВИДЕТЕЛЬСТВА О ПЕРИНАТАЛЬНОЙ СМЕРТИ", "К УЧЕТНОЙ ФОРМЕ № 106-2/У", text, fields.get("Серия", ""), fields.get("Номер", ""), fields.get("Дата выдачи", ""),
                      fields.get("Вид медицинского свидетельства о смерти", ""), fields)
    text.append(Spacer(1, 3 * mm))
    text.append(Paragraph(f"1. Рождение мертвого ребенка: {space_symbol * 5} число__________ месяц______________ год____________ час__________ мин____________", style))
    text.append(Spacer(1, 1.2 * mm))
    text.append(Paragraph(f"2. Ребенок родился живым: {space_symbol * 11} число__________ месяц______________ год____________ час__________ мин____________", style))
    text.append(Spacer(1, 1.2 * mm))
    text.append(Paragraph(f" {space_symbol * 6}и умер (дата): {space_symbol * 28} число__________ месяц______________ год____________ час__________ мин____________", style))
    text.append(Spacer(1, 1.2 * mm))
    text.append(Paragraph(f"3.	Смерть наступила: до начала родов {digit_one} во время родов {digit_two} после родов {digit_three} неизвестно {digit_four}", style))
    text.append(Spacer(1, 1.2 * mm))
    text.append(Paragraph(f"4.	Фамилия, имя, отчество (при наличии) матери:", style))
    text.append(Spacer(1, 1.2 * mm))
    text.append(Paragraph(f"5.	Дата рождения матери:	число_______ месяц_________ год __________", style))
    text.append(Spacer(1, 1.2 * mm))
    text.append(Paragraph(f"6.	Регистрация по месту жительства (пребывания) матери умершего (мертворожденного) ребенка:", style))
    text.append(Paragraph(f"субъект Российской Федерации  ", style))
    text.append(Paragraph(f"район__________________ город ____________________", style))
    text.append(Paragraph(f"населенный пункт__________________ улица ____________________", style))
    text.append(Paragraph(f"дом______стр.______корп. _____ кв._________", style))
    text.append(Spacer(1, 1.2 * mm))
    text.append(Paragraph(f"7.	Местность: городская {digit_one} сельская {digit_two}", style))
    text.append(Spacer(1, 1.2 * mm))
    text.append(Paragraph(f"8.	Фамилия, имя, отчество (при наличии) умершего ребенка (фамилия ребенка, родившегося мертвым)", style))
    text.append(Spacer(1, 1.2 * mm))
    text.append(Paragraph(f"9.	Пол: мужской {digit_one} женский {digit_two}", style))
    text.append(Spacer(1, 1.2 * mm))
    text.append(Paragraph(f"10. Смерть   (мертворождение)  произошла(о):  в  стационаре {digit_one} дома {digit_two} в другом месте {digit_three} неизвестно {digit_four}", style))

    obj = []
    obj.append(FrameDataUniversal(0 * mm, offset, 190 * mm, 95 * mm, text=text))
    return obj


def add_line_split(iss: Issledovaniya, direction, offset=0):
    # Лини отреза
    text = []
    text = line_split(text)
    obj = [(FrameDataUniversal(0 * mm, offset, 190 * mm, 5 * mm, text=text))]
    return obj


def title_data(title_name, title_form, text, serial, number, date_issue, type_document, data_fields):
    text.append(Paragraph(f"{title_name}", styleCentreBold))
    text.append(Spacer(1, 0.1 * mm))
    text.append(Paragraph(f"{title_form}", styleCentreBold))
    text.append(Spacer(1, 0.2 * mm))
    text.append(Paragraph(f"СЕРИЯ {serial} № {number}", styleCentreBold))
    text.append(Spacer(1, 0.1 * mm))
    text.append(Paragraph(f"Дата выдачи {date_issue}", styleCentreBold))
    final, preparatory, instead_preparatory, instead_final = "окончательного", "предварительного", "взамен предварительного", "взамен окончательного"

    type_death_document = json.loads(type_document)
    if type_death_document["code"] == '4':
        instead_final = f"<u>{op_bold_tag}взамен окончательного{cl_bold_tag}</u>"
    elif type_death_document["code"] == '3':
        instead_preparatory = f"<u>{op_bold_tag}взамен предварительного{cl_bold_tag}</u>"
    elif type_death_document["code"] == '1':
        final = f"{op_bold_tag}<u>окончательного</u>{cl_bold_tag}"
    elif type_death_document["code"] == '2':
        preparatory = f"<u>{op_bold_tag}предварительного{cl_bold_tag}</u>"
    text.append(Paragraph(f"({final}, {preparatory}, {instead_preparatory}, {instead_final}) (подчеркнуть)", styleCentre))
    if data_fields.get("Серия предшествующего", None):
        text.append(Paragraph("ранее выданное свидетельство", styleCentre))
        text.append(Paragraph(f"серия {data_fields['Серия предшествующего']} No {data_fields['Номер предшествующего']} от {data_fields['Дата выдачи предшествующего']} г.", styleCentre))
    return text


def line_split(text):
    step_round_dash = (1.5 * mm, 1 * mm)

    styleColor = deepcopy(style)
    styleColor.textColor = colors.gray

    opinion = [
        [
            Paragraph('', style),
            Paragraph('линия отреза', styleColor),
            Paragraph('', style),
        ],
    ]
    tbl = Table(opinion, hAlign='LEFT', rowHeights=5 * mm, colWidths=(80 * mm, 25 * mm, 80 * mm))
    tbl.setStyle(
        TableStyle(
            [
                ('LINEBELOW', (0, 0), (0, 0), 0.2 * mm, colors.gray, 'round', step_round_dash),
                ('LINEBELOW', (2, 0), (2, 0), 0.2 * mm, colors.gray, 'round', step_round_dash),
                ('BOTTOMPADDING', (1, 0), (1, 0), -0.5 * mm),
            ]
        )
    )
    text.append(tbl)
    return text


def death_data(iss: Issledovaniya, direction, fields, offset=0):
    text = []

    text = title_med_organization(text, fields['org'])
    text = title_data("МЕДИЦИНСКОЕ СВИДЕТЕЛЬСТВО О ПЕРИНАТАЛЬНОЙ СМЕРТИ", "", text, fields["Серия"], fields.get("Номер", ""), fields["Дата выдачи"], fields["Вид медицинского свидетельства о смерти"],
                      fields)
    text.append(Spacer(1, 1.7 * mm))

    opinion = [
        [
            Paragraph(f'{op_bold_tag}Мать{cl_bold_tag}', styleOrgCentre),
            Paragraph('', styleOrg),
            Paragraph(f'{op_bold_tag}Ребенок{cl_bold_tag}', styleOrgCentre),
        ],
    ]

    col_width = (
        93 * mm,
        5 * mm,
        93 * mm,
    )
    tbl_style = [
        ('GRID', (0, 0), (0, 0), 0.75, colors.white),
        ('GRID', (2, 0), (2, 0), 0.75, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (-1, -1), 1 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    text.append(Spacer(1, 0.3 * mm))
    mom_data = mother_data()
    # baby_data = child_data()
    opinion = [
        [
            Paragraph(f'{mom_data}', styleT),
            Paragraph('', styleOrg),
            Paragraph(f'{child_data()}', styleT),
        ],
    ]

    col_width = (
        93 * mm,
        5 * mm,
        93 * mm,
    )
    tbl_style = [
        ('GRID', (0, 0), (0, 0), 0.75, colors.white),
        ('GRID', (2, 0), (2, 0), 0.75, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (-1, -1), 1 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    obj = []
    obj.append(FrameDataUniversal(0 * mm, offset, 190 * mm, 178 * mm, text=text))

    return obj


def second_page_add_template(iss: Issledovaniya, direction, fields, offset=0):
    text = []
    text = back_size(text)
    text = why_death(text, fields, '11')
    # text = fio_tbl(text, "14. Фамилия, имя, отчество (при наличии) получателя", fields["ФИО (получатель)"])
    # text.append(Paragraph("Документ, удостоверяющий личность получателя (серия, номер, кем выдан)", styleT))
    # text = destination_person_passport(text, f'{fields["Документ (получатель)"]} {fields["Серия (получатель)"]} {fields["Номер (получатель)"]} {fields["Кем и когда выдан (получатель)"]}')
    # text = destination_person_snils(text, f'{fields["СНИЛС (получатель)"]}')
    # text.append(Spacer(1, 2 * mm))
    # text.append(Paragraph(f"«___» ___________ 20 ___ г.{space_symbol * 30} Подпись получателя _________________________", styleT))

    obj = []
    obj.append(FrameDataUniversal(0 * mm, offset, 190 * mm, 95 * mm, text=text))

    return obj


def death_data2(iss: Issledovaniya, direction, fields, offset=0):
    text = []
    # text = death_happaned(text, fields["Род причины смерти"])
    # date, month, year, hour, min = "____", "____", "_________", "____", "____"
    # unfortunate_and_other_info = "________________________________________________________________________________________________________________________"
    # text.append(Paragraph(
    #     f"19. В случае смерти от несчастного случая, убийства, самоубийства, от военных и террористических действий, при неустановленном роде смерти - указать дату травмы (отравления): "
    #     f"число {date} месяц {month} год {year} час. {hour} мин. {min} , а также место и обстоятельства, при",
    #     styleT))
    # text.append(Paragraph(f"{unfortunate_and_other_info}", styleT))
    # text = who_set_death(text, fields["Тип медицинского работника"])
    # text = doctor_fio(text, fields, iss)
    # text.append(Spacer(1, 1 * mm))
    # text = why_death(text, fields, "22", "23", "24", "25")
    # text.append(Spacer(1, 2 * mm))
    # text.append(
    #     Paragraph("<u>Руководитель (иное уполномоченное лицо **) медицинской организации</u>, индивидуальный предприниматель, осуществляющий медицинскую деятельность (подчеркнуть)", styleT))
    # text.append(Spacer(1, 2 * mm))
    # text = hospital_manager_stamp(text, fields["Главный врач"])
    # text.append(Spacer(1, 2 * mm))
    # text.append(Paragraph("26 Свидетельство проверено ответственным за правильность заполнения медицинских свидетельств.", styleT))
    # text = check_person_data(text, fields["Проверил"])
    text = bottom_colontitul(text, '** В случае, установленном частью 10 статьи 9 Федерального закона от 5 июня 2012 г. № 50-ФЗ "О регулировании деятельности российских граждан и '
                                   'российских юридических лиц в Антарктике" (Собрание законодательства Российской Федерации, 2012, № 24, ст. 3067). ')
    obj = []
    obj.append(FrameDataUniversal(0 * mm, offset, 190 * mm, 168 * mm, text=text))

    return obj


def title_med_organization(text, params):
    opinion = [
        [
            Paragraph(
                f'{params["full_title"]}<br/>'
                f'адрес места нахождения {params["org_address"]}<br/>'
                f'Код по ОКПО {params["org_okpo"]}<br/>'
                f'Номер и дата выдачи лицензии на осуществление медицинской деятельности: <br/>{params["org_license"]}<br/>',
                styleOrg,
            ),
            Paragraph('', styleOrg),
            Paragraph(
                'Код формы по ОКУД _______<br/>Медицинская документация<br/>Учётная форма № 106-2/У<br/>Утверждена приказом Минздрава России <br/>от «15» апреля 2021 г. № 352н', styleOrg
            ),
        ],
    ]
    col_width = (
        125 * mm,
        5 * mm,
        60 * mm,
    )
    tbl_style = [
        ('GRID', (0, 0), (0, 0), 0.75, colors.black),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (-1, -1), 1 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    return text


def gen_table(opinion, col_width, tbl_style, row_height=None):
    tbl = Table(
        opinion,
        colWidths=col_width,
        rowHeights=row_height,
        hAlign='LEFT',
    )
    tbl.setStyle(TableStyle(tbl_style))
    return tbl


def mother_data():
    fio = f"4.Фамилия, имя, отчество (при наличии): Соропудова Людмила Феоктистовна {line_break}{line_break}"
    born = f"5. Дата рождения: {op_boxed_tag}1{cl_boxed_tag}{op_boxed_tag}2{cl_boxed_tag} {space_symbol * 3} {op_boxed_tag}0{cl_boxed_tag}{op_boxed_tag}5{cl_boxed_tag} " \
           f"{space_symbol * 3} {op_boxed_tag}1{cl_boxed_tag}{op_boxed_tag}9{cl_boxed_tag}{op_boxed_tag}9{cl_boxed_tag}{op_boxed_tag}3{cl_boxed_tag}{line_break}{line_break}"
    type_document = f"6. Документ, удостоверяющий личность: {line_break}"
    serial_number = f"{space_symbol * 5}серия __________номер ______________ кем и когда выдан _____________________ {line_break}{line_break}"
    snils = f"7. СНИЛС___________{line_break}{line_break}"
    polis = f"8. Полис ОМС ________________ {line_break}{line_break}"
    address_title = f"9. Регистрация по месту жительства (пребывания):{line_break}"
    region_country = f"{space_symbol * 5}субъект Российской Федерации {line_break}"
    area_region = f"{space_symbol * 5} район {line_break}"
    city = f"{space_symbol * 5} город {line_break}"
    live_punkt = f"{space_symbol * 5} населенный пункт {line_break}"
    street = f"{space_symbol * 5} улица {line_break}"
    house = f"{space_symbol * 5} дом ______ стр.______ корп.________ кв._________ {line_break}{line_break}"
    type_place = f"10. Местность: городская {digit_one} сельская {digit_two}{line_break}{line_break}"
    married_status = f"11. Семейное положение:{line_break} состоит в зарегистрированном браке {digit_one}{line_break}"
    married_other_status = f"не состоит в зарегистрированном брак {digit_two} неизвестно {digit_three} {line_break}{line_break}"
    education = f"12. Образование: профессиональное: высшее {digit_one} неполное высшее{digit_two} среднее профессиональное {digit_three} " \
                f"{line_break} общее: среднее {digit_four} основное {digit_five} начальное {digit_six} не имеет начального образования " \
                f"{digit_seven} неизвестно {digit_eight}{line_break}{line_break}"
    work = f"Занятость: работала {digit_one} проходила военную или приравненную к ней службу {digit_two} студентка {digit_three} не работала {digit_four} прочее {digit_five} {line_break}{line_break}"
    count_birth = f"14.	Которые по счету роды __________"

    return f"{fio}{born}{type_document}{serial_number}{snils}{polis}{address_title}{region_country}{area_region}{city}{live_punkt}{street}{house}{type_place}" \
           f"{married_status}{married_other_status}{education}{work}{count_birth}"


def child_data():
    child_fio = f"15. Фамилия _____________{line_break}"
    child_place_death = f"16. Место смерти (рождения мертвого ребенка):{line_break}"
    child_region_country = f"{space_symbol * 5}субъект Российской Федерации {line_break}"
    child_area_region = f"{space_symbol * 5} район {line_break}"
    child_city = f"{space_symbol * 5} город {line_break}"
    child_live_punkt = f"{space_symbol * 5} населенный пункт {line_break}"
    child_street = f"{space_symbol * 5} улица {line_break}"
    child_house = f"{space_symbol * 5} дом ______ стр.______ корп.________ кв._________ {line_break}{line_break}"
    child_type_place = f"17. Местность: городская {digit_one} сельская {digit_two}{line_break}{line_break}"
    where_death = f"18. Смерть (рождение мертвым) произошла(о): в стационаре {digit_one} дома {digit_two} в другом месте {digit_three} неизвестно {digit_four} {line_break}{line_break}"
    sex = f"19.	Пол: мужской {digit_one} женский{digit_two} {line_break}{line_break}"
    weight = f"20. Масса тела ребенка при рождении (г) {line_break}{line_break}"
    long_body = f"21. Длина тела ребенка при рождении (см) {line_break}{line_break}"
    why_death = f"22. Рождение мертвым или живорождение произошло:  {line_break}"
    singleton_birth = f"{space_symbol * 3} при одноплодных родах {digit_one} {line_break}"
    multiple_birth = f"{space_symbol * 3} при многоплодных родах {digit_two} {line_break}"
    child_count = f"{space_symbol * 3} которыми по счет {line_break}"
    child_all_birth_count = f"{space_symbol * 3} число родившихся (живыми или мертвыми) детей {line_break}"

    return f"{child_fio}{child_place_death}{child_region_country}{child_area_region}{child_city}{child_live_punkt}{child_street}{child_house}{child_type_place}" \
           f"{where_death}{sex}{weight}{long_body}{why_death}{singleton_birth}{multiple_birth}{child_count}{child_all_birth_count}"


def back_size(text):
    opinion = [[Paragraph('Оборотная сторона', styleColontitulBold), ], ]
    col_width = (190 * mm,)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 166 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)
    return text


def why_death(text, params, item_why):
    tbl = title_table("Причины смерти:", "Коды по МКБ")
    text.append(Spacer(1, 1.5 * mm))
    text.append(tbl)
    text.append(Spacer(1, 2 * mm))

    tbl = diagnos_tbl("а)", "Скрининг с целью выявления полиомиелита Скрининг с целью выявления полиомиелита Скрининг с целью выявления полиомиелита Скрининг с целью выявления полиомиелита", "")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)
    tbl = about_diag_tbl("(основное заболевание или патологическое состояние плода или ребенка)")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    tbl = diagnos_tbl("б)", " Скрининг с целью иелита Скрининг с целью выявления полиомиелита", "")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)
    tbl = about_diag_tbl("(другие заболевания или патологические состояния плода или ребенка)")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    tbl = diagnos_tbl("в)", "", "")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)
    tbl = about_diag_tbl("(основное заболевание или патологическое состояние матери, оказавшее неблагоприятное влияние на плод или ребенка)")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    tbl = diagnos_tbl("г)", "", "")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)
    tbl = about_diag_tbl("(другие заболевания или патологические состояния матери, оказавшие неблагоприятное влияние на плод или ребенка)")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    tbl = diagnos_tbl("д)", "", "")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)
    tbl = about_diag_tbl("(другие обстоятельства, имевшие отношение к мертворождению, смерти)")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    return text


def title_table(diag_data, diag_code):
    opinion = [
        [
            Paragraph("", styleT),
            Paragraph(f"{diag_data}", styleT),
            Paragraph(f"{diag_code}", styleT),
        ],
    ]
    col_width = (10 * mm, 150 * mm, 30 * mm)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP',),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
        ('LEFTPADDING', (2, 0), (2, 0), 8 * mm),
        ('TOPPADDING', (1, 0), (1, 0), -1.2 * mm),
        ('TOPPADDING', (-1, -1), (-1, -1), -1.5 * mm),
    ]

    tbl = gen_table(opinion, col_width, tbl_style)
    return tbl

def diagnos_tbl(item, diag_data, diag_code):
    opinion = [
        [
            Paragraph(f"{item}", styleT),
            Paragraph(f"{diag_data}", styleOrgBold),
            Paragraph(f"{op_boxed_tag}Y14{cl_boxed_tag} . {op_boxed_tag}3{cl_boxed_tag}", styleDiag),
        ],
    ]
    col_width = (10 * mm, 150 * mm, 30 * mm,)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP', ),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
        ('LEFTPADDING', (2, 0), (2, 0), 8 * mm),
        ('TOPPADDING', (1, 0), (1, 0), -1.2 * mm),
        ('TOPPADDING', (-1, -1), (-1, -1), -1.5 * mm),
    ]

    tbl = gen_table(opinion, col_width, tbl_style, 4 * mm)
    return tbl


def about_diag_tbl(note_title):
    opinion = [
        [
            Paragraph('', styleOrg),
            Paragraph(f"{note_title}", styleMicro),
            Paragraph('', styleOrg),
        ],
    ]
    col_width = (10 * mm, 150 * mm, 30 * mm,)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP', ),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
        ('LEFTPADDING', (2, 0), (2, 0), 8 * mm),
        ('LINEABOVE', (1, 0), (1, 0), 0.75, colors.black),

    ]

    tbl = gen_table(opinion, col_width, tbl_style)
    return tbl



def bottom_colontitul(text, params):
    opinion = [[Paragraph(f'{params}', styleColontitul), ], ]
    col_width = (190 * mm)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 10 * mm),
        ('LEFTPADDING', (0, 0), (-1, -1), 1 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    return text
