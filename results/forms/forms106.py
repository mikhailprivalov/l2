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
from hospitals.models import Hospitals

pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
pdfmetrics.registerFont(TTFont('digit8', os.path.join(FONTS_FOLDER, 'digit88table.ttf')))
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
styleMicro.leading = 2.1 * mm

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

op_boxed_tagD = '<font face="digit8" size=22.5>'
cl_boxed_tagD = '</font>'
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


def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None, **kwargs):
    # Мед. св-во о смерти 106/-2у
    data = {"ФИО (получатель)": "", "Документ (получатель)": "", "Серия (получатель)": "", "Номер (получатель)": "", "Кем и когда выдан (получатель)": "", "СНИЛС (получатель)": ""}

    title_fields = [
        "Серия",
        "Префикс номера",
        "Номер",
        "Дата выдачи",
        "Вид медицинского свидетельства о смерти",
        "Серия предшествующего",
        "Номер предшествующего",
        "Дата выдачи предшествующего",
        "Фамилия матери",
        "Имя матери",
        "Отчество матери",
        "Дата рождения матери",
        "Полис матери",
        "СНИЛС матери",
        "Тип ДУЛ",
        "ДУЛ матери",
        "Адрес матери",
        "Вид места жительства",
        "Семейное положение",
        "Классификатор образования для медицинских свидетельств",
        "Социальные группы населения в учетной медицинской документации",
        "Которые по счету роды",
        "Родился",
        "Дата рождения",
        "Время рождения (известно)",
        "Время рождения",
        "Дата смерти",
        "Время смерти (известно)",
        "Время смерти",
        "Наступление летального исхода относительно времени родов",
        "Фамилия",
        "Место смерти (адрес)",
        "Местность смерти",
        "Типы мест наступления смерти",
        "Пол",
        "Масса тела ребенка при рождении (г)",
        "Длина тела ребенка при рождении (см)",
        "Рождение мертвым или живорождение произошло",
        "Которыми по счету",
        "Основания для определения причины смерти",
        "Число родившихся (живыми или мертвыми) детей",
        "Которым по счету ребенок был рожден у матери",
        "а) Основной заболевание (плода или ребенка)",
        "б) Другие заболевания плода или ребенка",
        "в) основное заболевание матери",
        "г) другие заболевания матери",
        "д) другие обстоятельства",
        "Тип лица, принимавшего роды",
        "Тип медицинского работника, установившего причины смерти",
        "Род причины смерти",
        "ФИО (получатель)",
        "Документ (получатель)",
        "Серия (получатель)",
        "Номер (получатель)",
        "Кем и когда выдан (получатель)",
        "СНИЛС (получатель)",
        "Проверил",
        "Главный врач",
    ]
    result = fields_result_only_title_fields(iss, title_fields, False)
    for i in result:
        data[i["title"]] = i["value"]

    data["Заполнил"] = iss.doc_confirmation.get_full_fio() if iss.doc_confirmation else ""

    data["Должность"] = iss.doc_position if iss.doc_confirmation else ""

    if not data.get("Проверил", None):
        data["Проверил"] = ""

    if not data.get("Главный врач", None):
        data["Главный врач"] = ""

    if not data.get("Род причины смерти", None):
        data["Род причины смерти"] = '{"code": "", "title": ""}'

    if not data.get("Время рождения", None):
        data["Время рождения"] = ""

    if not data.get("Время смерти", None):
        data["Время смерти"] = ""

    if iss.doc_confirmation:
        hospital_obj: Hospitals = iss.doc_confirmation.get_hospital()
    else:
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
    text = title_data(
        "КОРЕШОК МЕДИЦИНСКОГО СВИДЕТЕЛЬСТВА О ПЕРИНАТАЛЬНОЙ СМЕРТИ",
        "К УЧЕТНОЙ ФОРМЕ № 106-2/У",
        text,
        fields.get("Серия", ""),
        fields.get("Номер", ""),
        fields.get("Дата выдачи", ""),
        fields.get("Вид медицинского свидетельства о смерти", ""),
        fields,
    )
    text.append(Spacer(1, 3 * mm))

    text = death_data_child(text, fields)
    text.append(Spacer(1, 3 * mm))
    mother_fio = mother_fio_data(fields)
    text.append(Paragraph(f"4. Фамилия, имя, отчество (при наличии) матери: {mother_fio}", style))
    text.append(Spacer(1, 1.2 * mm))
    mother_born_date, mother_born_month, mother_born_year = "_______", "_________", "__________"
    mother_born_data = fields.get("Дата рождения матери", None)
    if mother_born_data:
        mother_born_data = mother_born_data.split(".")
        if len(mother_born_data) == 3:
            mother_born_date = f"<u>{space_symbol * 8}{mother_born_data[0]}{space_symbol * 8}</u>"
            mother_born_month = f"<u>{space_symbol * 8}{mother_born_data[1]}{space_symbol * 8}</u>"
            mother_born_year = f"<u>{space_symbol * 8}{mother_born_data[2]}{space_symbol * 8}</u>"

    text.append(Paragraph(f"5.	Дата рождения матери:	число {mother_born_date} месяц {mother_born_month} год {mother_born_year}", style))
    text.append(Spacer(1, 1.2 * mm))

    mother_address = address_get(fields.get("Адрес матери", None))
    text.append(Paragraph("6.	Регистрация по месту жительства (пребывания) матери умершего (мертворожденного) ребенка:", style))
    text.append(Paragraph(f"субъект Российской Федерации {mother_address['region_type']} {mother_address['region']}", style))
    city_mother = " город _____________"
    area_mother = "_______"
    if mother_address['area']:
        area_mother = mother_address['area']
    if mother_address['city']:
        city_mother = f"город {mother_address['city']}"

    text.append(Paragraph(f"район {area_mother} {city_mother}", style))
    locality_part = "________________"
    if mother_address['settlement_type'] and mother_address['settlement']:
        locality_part = f"{mother_address['settlement_type']} {mother_address['settlement']}"
    text.append(Paragraph(f"населенный пункт {locality_part}  улица {mother_address['street']}", style))
    text.append(Paragraph(f"дом {mother_address['house']} стр.______корп. _____ кв. {mother_address['flat']}", style))
    text.append(Spacer(1, 2 * mm))
    type_live = json.loads(fields["Вид места жительства"])
    town, rural = "городская", "сельская"
    if type_live["title"].lower() == "город":
        town = "<u>городская</u>"
    else:
        rural = "<u>сельская</u>"
    text.append(Paragraph(f"7.	Местность: {town} {digit_one} {rural} {digit_two}", style))
    text.append(Spacer(1, 4 * mm))
    child_family = fields.get("Фамилия", "")
    text.append(Paragraph(f"8.	Фамилия, имя, отчество (при наличии) умершего ребенка (фамилия ребенка, родившегося мертвым) {child_family}", style))
    sex_child = fields.get("Пол", "")
    sex_men, sex_woomen = "мужской", "женский"
    if sex_child.lower() == "мужской":
        sex_men = "<u>мужской</u>"
    else:
        sex_woomen = "<u>женский</u>"

    text.append(Paragraph(f"9.	Пол: {sex_men} {digit_one} {sex_woomen} {digit_two}", style))
    text.append(Spacer(1, 1.5 * mm))

    data_place_death = place_death_get(fields)
    text.append(
        Paragraph(
            f"10. Смерть   (мертворождение)  произошла(о):  {data_place_death['stationar']} {digit_one} {data_place_death['home']} {digit_two} "
            f"{data_place_death['other_place']} {digit_three} {data_place_death['not_know']} {digit_four}",
            style,
        )
    )

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
    prefix = data_fields.get("Префикс номера", "")
    text.append(Paragraph(f"СЕРИЯ {serial} № {prefix}{number}", styleCentreBold))
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
    text = title_data(
        "МЕДИЦИНСКОЕ СВИДЕТЕЛЬСТВО О ПЕРИНАТАЛЬНОЙ СМЕРТИ",
        "",
        text,
        fields["Серия"],
        fields.get("Номер", ""),
        fields["Дата выдачи"],
        fields["Вид медицинского свидетельства о смерти"],
        fields,
    )
    text = death_data_child(text, fields)
    text.append(Spacer(1, 3.5 * mm))

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
    mom_data = mother_data(fields)
    child_data = child_data_get(fields)
    opinion = [
        [
            Paragraph(f'{mom_data}', styleT),
            Paragraph('', styleOrg),
            Paragraph(f'{child_data}', styleT),
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

    tbl = who_write_documet("12.", fields["Должность"], fields["Заполнил"])
    text.append(Spacer(1, 4 * mm))
    text.append(tbl)
    tbl = who_writer_about_tbl()
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    tbl = who_get_document("13. Получатель", fields["ФИО (получатель)"])
    text.append(Spacer(1, 4 * mm))
    text.append(tbl)

    tbl = who_get_about_tbl()
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    text = who_get_type_document_para(text, fields)

    text.append(Spacer(1, 2 * mm))
    snils = fields.get("СНИЛС (получатель)", "______________")
    text.append(Paragraph(f"{space_symbol * 3} СНИЛС получателя (при наличии) {snils}", style))

    obj = []
    obj.append(FrameDataUniversal(0 * mm, offset, 190 * mm, 95 * mm, text=text))

    return obj


def death_data2(iss: Issledovaniya, direction, fields, offset=0):
    text = []
    all_child_with_later = fields.get("Которым по счету ребенок был рожден у матери", "")
    text.append(Paragraph(f"23. Которым по счету ребенок был рожден у матери (считая умерших и не считая мертворожденных) <u>{all_child_with_later}</u>", styleT))
    type_happend = json.loads(fields["Род причины смерти"])
    ill, unfortunate, kill, millitary, terrorist, not_know = "от заболевания", "несчастного случая", "убийства", "военных", "террористических", "род смерти не установлен"

    if type_happend["code"] == "1":
        ill = f"{op_bold_tag}<u>{ill}</u>{cl_bold_tag}"
    elif type_happend["code"] == "9":
        unfortunate = f"{op_bold_tag}<u>{unfortunate}</u>{cl_bold_tag}"
    elif type_happend["code"] == "4":
        kill = f"{op_bold_tag}<u>{kill}</u>{cl_bold_tag}"
    elif type_happend["code"] == "6":
        millitary = f"{op_bold_tag}<u>{millitary}</u>{cl_bold_tag}"
    elif type_happend["code"] == "7":
        terrorist = f"{op_bold_tag}<u>{terrorist}</u>{cl_bold_tag}"
    elif type_happend["code"] == "8":
        not_know = f"{op_bold_tag}<u>{not_know}</u>{cl_bold_tag}"

    text.append(
        Paragraph(
            f"24. Смерть ребенка (рождение мертвым) произошла(о): {ill} {op_boxed_tag}1{cl_boxed_tag} {unfortunate} {op_boxed_tag}2{cl_boxed_tag}"
            f"{kill} {op_boxed_tag}3{cl_boxed_tag} в ходе действий: {millitary} {op_boxed_tag}4{cl_boxed_tag} {terrorist} {op_boxed_tag}5{cl_boxed_tag}"
            f" {not_know} {op_boxed_tag}6{cl_boxed_tag}",
            styleT,
        )
    )

    who_get_born = fields.get("Тип лица, принимавшего роды", None)
    if who_get_born:
        who_get_born = json.loads(who_get_born)
    doctor_get, midwife_get, other_get = "врач", "фельдшер, акушерка", "другое"
    if who_get_born:
        if who_get_born["code"] == "1":
            doctor_get = f"{op_bold_tag}<u>{doctor_get}</u>{cl_bold_tag}"
        elif who_get_born["code"] == "2":
            midwife_get = f"{op_bold_tag}<u>{midwife_get}</u>{cl_bold_tag}"
        elif who_get_born["code"] == "3":
            other_get = f"{op_bold_tag}<u>{other_get}</u>{cl_bold_tag}"

    text.append(
        Paragraph(f"25.Лицо, принимавшее роды: {doctor_get} {op_boxed_tag}1{cl_boxed_tag} {midwife_get} {op_boxed_tag}2{cl_boxed_tag} {other_get} {op_boxed_tag}3{cl_boxed_tag}", styleT)
    )
    text = why_death(text, fields, '26')

    only_doc, gin_doc = "врачом, только удостоверившим смерть", "врачом-акушером-гинекологом, принимавшим роды"
    neonatolog_doc = "врачом-неонатологом (или врачом-педиатром), лечившим ребенка"
    patolog_doc, sme_doc, paramedic_doc = "врачом - патологоанатомом", "врачом - судебно-медицинским экспертом", "фельдшером, акушеркой"
    who_fact_death = fields.get("Тип медицинского работника, установившего причины смерти", None)
    if who_fact_death:
        who_fact_death = json.loads(who_fact_death)
        if who_fact_death["code"] == "1":
            only_doc = f"{op_bold_tag}<u>{only_doc}</u>{cl_bold_tag}"
        elif who_fact_death["code"] == "2":
            gin_doc = f"{op_bold_tag}<u>{gin_doc}</u>{cl_bold_tag}"
        elif who_fact_death["code"] == "3":
            neonatolog_doc = f"{op_bold_tag}<u>{neonatolog_doc}</u>{cl_bold_tag}"
        elif who_fact_death["code"] == "4":
            patolog_doc = f"{op_bold_tag}<u>{patolog_doc}</u>{cl_bold_tag}"
        elif who_fact_death["code"] == "5":
            sme_doc = f"{op_bold_tag}<u>{sme_doc}</u>{cl_bold_tag}"
        elif who_fact_death["code"] == "6":
            paramedic_doc = f"{op_bold_tag}<u>{paramedic_doc}</u>{cl_bold_tag}"

    text.append(
        Paragraph(
            f"27. Причины смерти установлены: {only_doc} {op_boxed_tag}1{cl_boxed_tag} "
            f"{gin_doc} {op_boxed_tag}2{cl_boxed_tag} "
            f"{neonatolog_doc} {op_boxed_tag}3{cl_boxed_tag} "
            f"{patolog_doc} {op_boxed_tag}4{cl_boxed_tag} "
            f"{sme_doc} {op_boxed_tag}5{cl_boxed_tag} "
            f"{paramedic_doc} {op_boxed_tag}6{cl_boxed_tag}",
            styleT,
        )
    )
    text.append(Spacer(1, 2 * mm))
    reason_death = fields.get("Основания для определения причины смерти", "")
    if reason_death:
        reason_death = json.loads(reason_death)
    examination_corpse, writer_document = 'осмотр трупа', 'записи в медицинской документации'
    prior_observation, autopsy = 'собственного предшествовавшего наблюдения', 'вскрытие'
    if reason_death:
        if reason_death["code"] == "1":
            examination_corpse = f"{op_bold_tag}<u>{examination_corpse}</u>{cl_bold_tag}"
        elif reason_death["code"] == "2":
            writer_document = f"{op_bold_tag}<u>{writer_document}</u>{cl_bold_tag}"
        elif who_fact_death["code"] == "3":
            prior_observation = f"{op_bold_tag}<u>{prior_observation}</u>{cl_bold_tag}"
        elif reason_death["code"] == "4":
            autopsy = f"{op_bold_tag}<u>{autopsy}</u>{cl_bold_tag}"

    text.append(
        Paragraph(
            f"28. На основании: {examination_corpse} {op_boxed_tag}1{cl_boxed_tag} {writer_document} {op_boxed_tag}2{cl_boxed_tag} "
            f" {prior_observation}{op_boxed_tag}3{cl_boxed_tag} {autopsy} {op_boxed_tag}4{cl_boxed_tag}",
            styleT,
        )
    )

    tbl = who_write_documet("29.", fields["Должность"], fields["Заполнил"])
    text.append(Spacer(1, 8 * mm))
    text.append(tbl)
    tbl = who_writer_about_tbl()
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    text.append(Spacer(1, 2 * mm))
    text.append(Paragraph("Руководитель медицинской организации, индивидуальный предприниматель, осуществляющий медицинскую деятельность (подчеркнуть)", styleT))
    text.append(Spacer(1, 4 * mm))

    tbl = manager_hospital_document(fields["Главный врач"])
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)
    tbl = manager_hospital_about_tbl()
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    text.append(Spacer(1, 4 * mm))
    text.append(Paragraph("30. Свидетельство проверено ответственным за правильность заполнения медицинских свидетельств.", styleT))

    text.append(Spacer(1, 4 * mm))
    person_check = fields["Проверил"]
    data_check = fields.get("Дата выдачи", "")
    check_day, check_month, check_year = "", "", ""
    if person_check:
        data_check = data_check.split(".")
        check_day = f"{data_check[0]}."
        check_month = f"{data_check[1]}."
        check_year = f"{data_check[2]} г."

    tbl = who_check(check_day, check_month, check_year, person_check)
    text.append(tbl)

    tbl = who_check_about()
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    text = bottom_colontitul(
        text,
        '** В случае, установленном частью 10 статьи 9 Федерального закона от 5 июня 2012 г. № 50-ФЗ "О регулировании деятельности российских граждан и '
        'российских юридических лиц в Антарктике" (Собрание законодательства Российской Федерации, 2012, № 24, ст. 3067). ',
    )
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


def mother_data(fields):
    mother_fio = mother_fio_data(fields)
    fio = f"4.Фамилия, имя, отчество (при наличии): {mother_fio}{line_break}{line_break}"
    mother_born = fields.get("Дата рождения матери", None)
    mother_born_date, mother_born_month, mother_born_year = " ", " ", " "
    if mother_born:
        mother_born_data = mother_born.split(".")
        if len(mother_born_data) == 3:
            mother_born_date = mother_born_data[0]
            mother_born_month = mother_born_data[1]
            mother_born_year = mother_born_data[2]

    born = (
        f"5. Дата рождения: {op_boxed_tag}{mother_born_date}{cl_boxed_tag} {space_symbol * 3} {op_boxed_tag}{mother_born_month}{cl_boxed_tag} "
        f"{space_symbol * 3} {op_boxed_tag}{mother_born_year}{cl_boxed_tag}{line_break}{line_break}"
    )
    type_document_mother = fields.get("Тип ДУЛ", "")
    if type_document_mother and "-" in type_document_mother:
        type_document_mother = type_document_mother.split("-")
        type_document_mother = f"<u>{type_document_mother[1]}</u>"
    type_document = f"6. Документ, удостоверяющий личность: {type_document_mother}{line_break}"
    doc_serial, doc_number, doc_who_issued, doc_date = "__________", "______________", "_____________________", ""
    dul = json.loads(fields.get("ДУЛ матери", None))
    if dul:
        doc_serial = f"<u>{dul.get('rows')[0][0]}</u>"
        doc_number = f"<u>{dul.get('rows')[0][1]}</u>"
        doc_who_issued = f"<u>{dul.get('rows')[0][2]}</u>"
        doc_date = f"<u>{dul.get('rows')[0][3]}</u>"

    serial_number = f"{space_symbol * 5}серия {doc_serial} номер {doc_number} кем и когда выдан {doc_who_issued} {doc_date} {line_break}{line_break}"
    doc_snils = "________________"
    doc_data_snils = fields.get("СНИЛС матери", "")
    if doc_data_snils:
        doc_snils = f"<u>{doc_data_snils}</u>"
    snils = f"7. СНИЛС {doc_snils}{line_break}{line_break}"
    doc_polis = "________________"
    doc_data_polis = fields.get("Полис матери", "")
    if doc_data_polis:
        doc_polis = f"<u>{doc_data_polis}</u>"
    polis = f"8. Полис ОМС {doc_polis} {line_break}{line_break}"
    address_title = f"9. Регистрация по месту жительства (пребывания):{line_break}"
    mother_address = address_get(fields.get("Адрес матери", None))
    region_country = f"{space_symbol * 5}субъект Российской Федерации {mother_address['region_type']} {mother_address['region']}{line_break}"
    area_region = f"{space_symbol * 5} район {mother_address['area']} {line_break}"
    city = f"{space_symbol * 5} город {mother_address['city']} {line_break}"
    live_punkt = f"{space_symbol * 5} населенный пункт {mother_address['settlement_type']} {mother_address['settlement']} {line_break}"
    street = f"{space_symbol * 5} улица {mother_address['street']}{line_break}"
    house = f"{space_symbol * 5} дом {mother_address['house']} стр.______ корп.________ кв.{mother_address['flat']} {line_break}{line_break}"

    type_live = json.loads(fields["Вид места жительства"])
    town, rural = "городская", "сельская"
    if type_live["title"].lower() == "город":
        town = "<u>городская</u>"
    else:
        rural = "<u>сельская</u>"

    type_place = f"10. Местность: {town} {digit_one} {rural} {digit_two}{line_break}{line_break}"

    is_married, not_married, not_known = "состоит в зарегистрированном браке", "не состоит в зарегистрированном браке", "неизвестно"
    married_mother = json.loads(fields.get("Семейное положение", None))
    if int(married_mother["code"]) == 1:
        is_married = f"<u>{op_bold_tag}{is_married}{cl_bold_tag}</u>"
    elif int(married_mother["code"]) == 3:
        not_known = f"<u>{op_bold_tag}{not_known}{cl_bold_tag}</u>"
    elif int(married_mother["code"]) == 2:
        not_married = f"<u>{op_bold_tag}{not_married}{cl_bold_tag}</u>"
    married_status = f"11. Семейное положение:{line_break} {is_married} {digit_one}{line_break}"
    married_other_status = f"{not_married} {digit_two} {not_known} {digit_three} {line_break}{line_break}"

    high_school, not_high_school, middle_school = "высшее", "неполное высшее", "среднее профессиональное"
    general_middle, main, initial, not_has_initial, not_known = "среднее", "основное", "начальное", "не имеет начального образования", "неизвестно"
    education_status = json.loads(fields.get("Классификатор образования для медицинских свидетельств", None))
    if education_status["code"] == "1":
        high_school = f"<u>{op_bold_tag}{high_school}{cl_bold_tag}</u>"
    elif education_status["code"] == "2":
        not_high_school = f"<u>{op_bold_tag}{not_high_school}{cl_bold_tag}</u>"
    elif education_status["code"] == "3":
        middle_school = f"<u>{op_bold_tag}{middle_school}{cl_bold_tag}</u>"
    elif education_status["code"] == "5":
        general_middle = f"<u>{op_bold_tag}{general_middle}{cl_bold_tag}</u>"
    elif education_status["code"] == "6":
        main = f"<u>{op_bold_tag}{main}{cl_bold_tag}</u>"
    elif education_status["code"] == "7":
        initial = f"<u>{op_bold_tag}{initial}{cl_bold_tag}</u>"
    elif education_status["code"] == "8":
        not_has_initial = f"<u>{op_bold_tag}{not_has_initial}{cl_bold_tag}</u>"
    elif education_status["code"] == "9":
        not_known = f"<u>{op_bold_tag}{not_known}{cl_bold_tag}</u>"
    education = (
        f"12. Образование: профессиональное: {high_school} {digit_one} {not_high_school} {digit_two} {middle_school} {digit_three} "
        f"{line_break} общее: {general_middle} {digit_four} {main} {digit_five} {initial} {digit_six} {not_has_initial}"
        f"{digit_seven} {not_known} {digit_eight}{line_break}{line_break}"
    )
    is_worked, military, student, not_worked, other = "работала", "проходила военную или приравненную к ней службу", "студентка", "не работала", "прочее"
    social_status = json.loads(fields.get("Социальные группы населения в учетной медицинской документации", None))
    if social_status["code"] == "4":
        student = f"<u>{op_bold_tag}{student}{cl_bold_tag}</u>"
    elif social_status["code"] == "5":
        is_worked = f"<u>{op_bold_tag}{is_worked}{cl_bold_tag}</u>"
    elif social_status["code"] == "8":
        not_worked = f"<u>{op_bold_tag}{not_worked}{cl_bold_tag}</u>"
    elif social_status["code"] == "17":
        military = f"<u>{op_bold_tag}{military}{cl_bold_tag}</u>"
    elif social_status["code"] == "10":
        other = f"<u>{op_bold_tag}{other}{cl_bold_tag}</u>"

    work = f"13. Занятость: {is_worked} {digit_one} {military} {digit_two} студентка {digit_three} {not_worked} {digit_four} {other} {digit_five} {line_break}" f"{line_break}"
    mother_count_birth = f"<u>{op_bold_tag}{fields.get('Которые по счету роды', '')}{cl_bold_tag}</u>"

    count_birth = f"14.	Которые по счету роды {mother_count_birth}"

    return (
        f"{fio}{born}{type_document}{serial_number}{snils}{polis}{address_title}{region_country}{area_region}{city}{live_punkt}{street}{house}{type_place}"
        f"{married_status}{married_other_status}{education}{work}{count_birth}"
    )


def child_data_get(data_fields):
    child_family = data_fields.get("Фамилия", "_____________")
    child_fio = f"15. Фамилия {child_family}{line_break}"
    child_place_death = f"16. Место смерти (рождения мертвого ребенка):{line_break}"
    child_address_death = address_get(data_fields.get("Место смерти (адрес)", None))
    child_region_country = f"{space_symbol * 5} субъект Российской Федерации {child_address_death['region_type']} {child_address_death['region']}{line_break}"
    child_area_region = f"{space_symbol * 5} район {child_address_death['area']} {line_break}"
    child_city = f"{space_symbol * 5} город {child_address_death['city']}{line_break}"
    child_live_punkt = f"{space_symbol * 5} населенный пункт {child_address_death['settlement_type']} {child_address_death['settlement']}{line_break}"
    child_street = f"{space_symbol * 5} улица {child_address_death['street']} {line_break}"
    child_house = f"{space_symbol * 5} дом {child_address_death['house']} стр.______ корп.________ кв.{child_address_death['flat']} {line_break}{line_break}"

    place_death = json.loads(data_fields["Местность смерти"])
    town_death, rural_death = "городская", "сельская"
    if place_death["code"] == "1":
        town_death = f"<u>{op_bold_tag}{town_death}{cl_bold_tag}</u>"
    elif place_death["code"] == "2":
        town_death = f"<u>{op_bold_tag}{rural_death}{cl_bold_tag}</u>"
    child_type_place = f"17. Местность: {town_death} {digit_one} {rural_death} {digit_two}{line_break}{line_break}"
    data_place_death = place_death_get(data_fields)
    where_death = (
        f"18. Смерть (рождение мертвым) произошла(о):{line_break}{data_place_death['stationar']} {digit_one} {data_place_death['home']} {digit_two} "
        f"{data_place_death['other_place']} {digit_three} {data_place_death['not_know']} {digit_four} {line_break}{line_break}"
    )
    sex_men, sex_women = "мужской", "женский"
    if data_fields["Пол"].lower() == "женский":
        sex_women = f"<u>{op_bold_tag}{sex_women}{cl_bold_tag}</u>"
    elif data_fields["Пол"].lower() == "мужской":
        sex_men = f"<u>{op_bold_tag}{sex_men}{cl_bold_tag}</u>"
    sex = f"19.	Пол: {sex_men} {digit_one} {sex_women} {digit_two} {line_break}{line_break}"

    born_mass = data_fields.get("Масса тела ребенка при рождении (г)", "")
    weight = f"20. Масса тела ребенка при рождении (г) {born_mass}{line_break}{line_break}"
    long_body_data = data_fields.get("Длина тела ребенка при рождении (см)", "")
    long_body = f"21. Длина тела ребенка при рождении (см) {long_body_data}{line_break}{line_break}"
    why_death = f"22. Рождение мертвым или живорождение произошло:  {line_break}"

    type_birth = data_fields.get("Рождение мертвым или живорождение произошло", "")
    single_type, multiple_type = "при одноплодных родах", "при многоплодных родах"
    if type_birth == "при одноплодных родах":
        single_type = f"<u>{op_bold_tag}{single_type}{cl_bold_tag}</u>"
    elif type_birth == "при многоплодных родах":
        multiple_type = f"<u>{op_bold_tag}{multiple_type}{cl_bold_tag}</u>"
    singleton_birth = f"{space_symbol * 3} {single_type} {digit_one} {line_break}"
    multiple_birth = f"{space_symbol * 3} {multiple_type} {digit_two} {line_break}"
    what_count = data_fields.get("Которыми по счету", "")
    child_count = f"{space_symbol * 3} которыми по счет <u>{op_bold_tag}{what_count}{cl_bold_tag}</u>{line_break}"

    all_count = data_fields.get("Число родившихся (живыми или мертвыми) детей", "")
    child_all_birth_count = f"{space_symbol * 3} число родившихся (живыми или мертвыми) детей <u>{op_bold_tag}{all_count}{cl_bold_tag}</u> {line_break}"

    return (
        f"{child_fio}{child_place_death}{child_region_country}{child_area_region}{child_city}{child_live_punkt}{child_street}{child_house}{child_type_place}"
        f"{where_death}{sex}{weight}{long_body}{why_death}{singleton_birth}{multiple_birth}{child_count}{child_all_birth_count}"
    )


def back_size(text):
    opinion = [
        [
            Paragraph('Оборотная сторона', styleColontitulBold),
        ],
    ]
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
    tbl = title_table(item_why, "Причины смерти:", "Коды по МКБ")
    text.append(Spacer(1, 5 * mm))
    text.append(tbl)
    text.append(Spacer(1, 2 * mm))
    a_diag = params.get('а) Основной заболевание (плода или ребенка)', None)
    a_diag_title, a_diag_code = "", ""
    if a_diag:
        a_diag = json.loads(a_diag)
        a_diag_title = a_diag["title"]
        a_diag_code = a_diag["code"]
    tbl = diagnos_tbl("а)", a_diag_title, a_diag_code)
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)
    tbl = about_diag_tbl("(основное заболевание или патологическое состояние плода или ребенка)")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    b_diag = params.get('б) Другие заболевания плода или ребенка', None)
    b_diag_title, b_diag_code = "", ""
    if b_diag:
        b_diag = json.loads(b_diag)
        b_diag_title = b_diag["title"]
        b_diag_code = b_diag["code"]

    tbl = diagnos_tbl("б)", b_diag_title, b_diag_code)
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)
    tbl = about_diag_tbl("(другие заболевания или патологические состояния плода или ребенка)")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    v_diag = params.get('в) основное заболевание матери', None)
    v_diag_title, v_diag_code = "", ""
    if v_diag:
        v_diag = json.loads(v_diag)
        v_diag_title = v_diag["title"]
        v_diag_code = v_diag["code"]

    tbl = diagnos_tbl("в)", v_diag_title, v_diag_code)
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)
    tbl = about_diag_tbl("(основное заболевание или патологическое состояние матери, оказавшее неблагоприятное влияние на плод или ребенка)")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    g_diag = params.get('г) другие заболевания матери', None)
    g_diag_title, g_diag_code = "", ""
    if g_diag:
        g_diag = json.loads(g_diag)
        g_diag_title = g_diag["title"]
        g_diag_code = g_diag["code"]

    tbl = diagnos_tbl("г)", g_diag_title, g_diag_code)
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)
    tbl = about_diag_tbl("(другие заболевания или патологические состояния матери, оказавшие неблагоприятное влияние на плод или ребенка)")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    d_diag = params.get('д) другие обстоятельства', None)
    if d_diag:
        d_diag_dict = json.loads(d_diag)
        count = 0
        d_diag_rows = d_diag_dict.get("rows", None)
        for r in d_diag_rows:
            if not r[0]:
                continue
            r = json.loads(r[0])
            d_diag_title = r.get("title", None)
            d_diag_code = r.get("code", None)
            if not d_diag_title or not d_diag_code:
                continue
            if count == 0:
                tbl = diagnos_tbl("д)", d_diag_title, d_diag_code)
            else:
                tbl = diagnos_tbl("", d_diag_title, d_diag_code)
            text.append(Spacer(1, 0 * mm))
            text.append(tbl)
            tbl = about_diag_tbl("(другие обстоятельства, имевшие отношение к мертворождению, смерти)")
            text.append(Spacer(1, 0 * mm))
            text.append(tbl)
            count += 1

    return text


def who_write_documet(item, position_writer, fio):
    opinion = [
        [
            Paragraph(f"{item}", styleT),
            Paragraph(f"{position_writer}", styleT),
            Paragraph("", styleT),
            Paragraph("", styleT),
            Paragraph("", styleT),
            Paragraph(f"{fio}", styleT),
        ],
    ]
    col_width = (
        10 * mm,
        70 * mm,
        7 * mm,
        40 * mm,
        7 * mm,
        70 * mm,
    )
    tbl_style = [
        (
            'VALIGN',
            (0, 0),
            (-1, -1),
            'TOP',
        ),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -1 * mm),
    ]

    tbl = gen_table(opinion, col_width, tbl_style)
    return tbl


def who_writer_about_tbl():
    opinion = [
        [
            Paragraph("", styleMicro),
            Paragraph("(должность врача (фельдшера, акушерки), заполнившего медицинское свидетельство о перинатальной смерти)", styleMicro),
            Paragraph("", styleMicro),
            Paragraph("(подпись)", styleMicro),
            Paragraph("", styleMicro),
            Paragraph("(фамилия, имя, отчество (при наличии)", styleMicro),
        ],
    ]
    col_width = (
        10 * mm,
        65 * mm,
        5 * mm,
        40 * mm,
        5 * mm,
        65 * mm,
    )
    tbl_style = [
        (
            'VALIGN',
            (0, 0),
            (-1, -1),
            'TOP',
        ),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
        ('LINEABOVE', (1, 0), (1, 0), 0.75, colors.black),
        ('LINEABOVE', (3, 0), (3, 0), 0.75, colors.black),
        ('LINEABOVE', (5, 0), (5, 0), 0.75, colors.black),
    ]

    tbl = gen_table(opinion, col_width, tbl_style)
    return tbl


def who_get_document(item, fio):
    opinion = [
        [
            Paragraph(f"{item}", styleT),
            Paragraph(f"{fio}", styleT),
        ],
    ]
    col_width = (
        27 * mm,
        163 * mm,
    )
    tbl_style = [
        (
            'VALIGN',
            (0, 0),
            (-1, -1),
            'TOP',
        ),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -1 * mm),
    ]

    tbl = gen_table(opinion, col_width, tbl_style)
    return tbl


def who_get_about_tbl():
    opinion = [
        [
            Paragraph("", styleT),
            Paragraph("(фамилия, имя, отчество (при наличии) и отношение к мертворожденному (умершему) ребенку", styleMicro),
        ],
    ]
    col_width = (
        27 * mm,
        163 * mm,
    )
    tbl_style = [
        (
            'VALIGN',
            (0, 0),
            (-1, -1),
            'TOP',
        ),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
        ('LINEABOVE', (1, 0), (1, 0), 0.75, colors.black),
    ]

    tbl = gen_table(opinion, col_width, tbl_style)
    return tbl


def who_get_type_document_tbl(param_doc):
    type_document = param_doc.get("Документ (получатель)", "")
    serial_document = param_doc.get("Серия (получатель)", "")
    number_document = param_doc.get("Номер (получатель)", "")
    who_where_document = param_doc.get("Кем и когда выдан (получатель)", "")

    document_data = f"{type_document} {serial_document} {number_document} {who_where_document}"
    opinion = [
        [
            Paragraph("Документ, удостоверяющий личность получателя (вид, серия, номер, кем выдан)", styleT),
            Paragraph(f"{document_data}", styleMicro),
        ],
    ]
    col_width = (
        126 * mm,
        64 * mm,
    )
    tbl_style = [
        (
            'VALIGN',
            (0, 0),
            (-1, -1),
            'TOP',
        ),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 7 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
    ]

    tbl = gen_table(opinion, col_width, tbl_style)
    return tbl


def who_get_type_document_para(text, param_doc):
    type_document = param_doc.get("Документ (получатель)", "")
    serial_document = param_doc.get("Серия (получатель)", "")
    number_document = param_doc.get("Номер (получатель)", "")
    who_where_document = param_doc.get("Кем и когда выдан (получатель)", "")
    doc_data = f"{type_document} {serial_document} {number_document} {who_where_document}"
    text.append(Paragraph(f"{space_symbol * 3}Документ, удостоверяющий личность получателя (вид, серия, номер, кем выдан) {doc_data}", styleT))
    return text


def title_table(item, diag_data, diag_code):
    opinion = [
        [
            Paragraph(f"{item}", styleT),
            Paragraph(f"{diag_data}", styleT),
            Paragraph(f"{diag_code}", styleT),
        ],
    ]
    col_width = (10 * mm, 157 * mm, 26 * mm)
    tbl_style = [
        (
            'VALIGN',
            (0, 0),
            (-1, -1),
            'TOP',
        ),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -1.3 * mm),
    ]

    tbl = gen_table(opinion, col_width, tbl_style)
    return tbl


def diagnos_tbl(item, diag_data, diag_code):
    diag_code = list(diag_code)
    symbol_one = diag_code[0] if len(diag_code) >= 1 else space_symbol
    symbol_two = diag_code[1] if len(diag_code) >= 2 else space_symbol
    symbol_three = diag_code[2] if len(diag_code) >= 3 else space_symbol
    symbol_four = diag_code[4] if len(diag_code) >= 4 else ""

    about_diag_code = (Paragraph(f"{op_boxed_tagD}{space_symbol}{space_symbol}{space_symbol}{cl_boxed_tag} . {op_boxed_tagD}{space_symbol}{cl_boxed_tagD}", styleDiag),)
    if len(diag_code) > 0:
        about_diag_code = (Paragraph(f"{op_boxed_tagD}{symbol_one}{symbol_two}{symbol_three}{cl_boxed_tag} . {op_boxed_tagD}{symbol_four}{cl_boxed_tagD}", styleDiag),)

    opinion = [
        [Paragraph(f"{item}", styleT), Paragraph(f"{diag_data}", styleOrgBold), about_diag_code],
    ]
    col_width = (
        10 * mm,
        154 * mm,
        26 * mm,
    )
    tbl_style = [
        (
            'VALIGN',
            (0, 0),
            (-1, -1),
            'TOP',
        ),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('LEFTPADDING', (2, 0), (2, 0), 5 * mm),
        ('TOPPADDING', (1, 0), (1, 0), -1.2 * mm),
        ('TOPPADDING', (-1, -1), (-1, -1), -4 * mm),
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
    col_width = (
        10 * mm,
        154 * mm,
        26 * mm,
    )
    tbl_style = [
        (
            'VALIGN',
            (0, 0),
            (-1, -1),
            'TOP',
        ),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
        ('LINEABOVE', (1, 0), (1, 0), 0.75, colors.black),
    ]

    tbl = gen_table(opinion, col_width, tbl_style)
    return tbl


def manager_hospital_document(fio):
    opinion = [
        [
            Paragraph("", styleT),
            Paragraph("", styleT),
            Paragraph("", styleT),
            Paragraph("", styleT),
            Paragraph(f"{fio}", styleT),
        ],
    ]
    col_width = (
        65 * mm,
        5 * mm,
        40 * mm,
        5 * mm,
        65 * mm,
    )
    tbl_style = [
        (
            'VALIGN',
            (0, 0),
            (-1, -1),
            'TOP',
        ),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -1 * mm),
    ]

    tbl = gen_table(opinion, col_width, tbl_style)
    return tbl


def manager_hospital_about_tbl():
    opinion = [
        [
            Paragraph("печать", styleMicro),
            Paragraph("", styleMicro),
            Paragraph("(подпись)", styleMicro),
            Paragraph("", styleMicro),
            Paragraph("(фамилия, имя, отчество (при наличии)", styleMicro),
        ],
    ]
    col_width = (
        65 * mm,
        5 * mm,
        40 * mm,
        5 * mm,
        65 * mm,
    )
    tbl_style = [
        (
            'VALIGN',
            (0, 0),
            (-1, -1),
            'TOP',
        ),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
        ('LINEABOVE', (0, 0), (0, 0), 0.75, colors.black),
        ('LINEABOVE', (2, 0), (2, 0), 0.75, colors.black),
        ('LINEABOVE', (4, 0), (4, 0), 0.75, colors.black),
    ]

    tbl = gen_table(opinion, col_width, tbl_style)
    return tbl


def who_check(number, month, year, fio):
    opinion = [
        [
            Paragraph(f"{number}", styleT),
            Paragraph(f"{month}", styleT),
            Paragraph(f"{year}", styleT),
            Paragraph("", styleT),
            Paragraph(f"{fio}", styleT),
        ],
    ]
    col_width = (
        9 * mm,
        9 * mm,
        16 * mm,
        30 * mm,
        65 * mm,
    )
    tbl_style = [
        (
            'VALIGN',
            (0, 0),
            (-1, -1),
            'TOP',
        ),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -1 * mm),
    ]

    tbl = gen_table(opinion, col_width, tbl_style)
    return tbl


def who_check_about():
    opinion = [
        [
            Paragraph("", styleT),
            Paragraph("", styleT),
            Paragraph("", styleT),
            Paragraph("", styleT),
            Paragraph("", styleT),
        ],
    ]
    col_width = (
        10 * mm,
        15 * mm,
        16 * mm,
        20 * mm,
        65 * mm,
    )
    tbl_style = [
        (
            'VALIGN',
            (0, 0),
            (-1, -1),
            'TOP',
        ),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -1 * mm),
        ('LINEABOVE', (0, 0), (0, 0), 0.75, colors.black),
        ('LINEABOVE', (1, 0), (1, 0), 0.75, colors.black),
        ('LINEABOVE', (2, 0), (2, 0), 0.75, colors.black),
        ('LINEABOVE', (4, 0), (4, 0), 0.75, colors.black),
    ]

    tbl = gen_table(opinion, col_width, tbl_style)
    return tbl


def bottom_colontitul(text, params):
    opinion = [
        [
            Paragraph(f'{params}', styleColontitul),
        ],
    ]
    col_width = 190 * mm
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 10 * mm),
        ('LEFTPADDING', (0, 0), (-1, -1), 1 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    return text


def death_data_child(text, fields_data):
    death_date_def, death_month_def, death_year_def = "__________", "______________", " ____________"
    death_hour_def, death_min_def = "__________", "____________"

    death_data = fields_data["Дата смерти"].split(".")
    death_date_result = f"<u>{space_symbol * 8}{death_data[0]}{space_symbol * 8}</u>"
    death_month_result = f"<u>{space_symbol * 12}{death_data[1]}{space_symbol * 12}</u>"
    death_year_result = f"<u>{space_symbol * 8}{death_data[2]}{space_symbol * 8}</u>"
    if fields_data.get("Дата рождения", None):
        death_date = death_date_def
        death_month = death_month_def
        death_year = death_year_def
    if not fields_data.get("Дата рождения", None):
        death_date = death_date_result
        death_month = death_month_result
        death_year = death_year_result
        if fields_data.get("Время смерти", None):
            death_time = fields_data.get("Время смерти").split(":")
            death_hour_def = f"<u>{space_symbol * 8}{death_time[0]}{space_symbol * 8}</u>"
            death_min_def = f"<u>{space_symbol * 8}{death_time[1]}{space_symbol * 8}</u>"
    text.append(Paragraph(f"1. Рождение мертвого ребенка: {space_symbol * 5} число {death_date} месяц{death_month} год{death_year} час {death_hour_def} мин {death_min_def}", style))
    text.append(Spacer(1, 1.2 * mm))
    born_date, born_month, born_year = "__________", "______________", " ____________"
    born_hour, born_min = "__________", "____________"
    death_hour, death_min = "__________", "____________"
    if fields_data.get("Дата рождения", None):
        born_data = fields_data["Дата рождения"].split(".")
        born_date = f"<u>{space_symbol * 8}{born_data[0]}{space_symbol * 8}</u>"
        born_month = f"<u>{space_symbol * 12}{born_data[1]}{space_symbol * 12}</u>"
        born_year = f"<u>{space_symbol * 8}{born_data[2]}{space_symbol * 8}</u>"
        if fields_data.get("Время рождения", None):
            born_time = fields_data.get("Время рождения").split(":")
            born_hour = f"<u>{space_symbol * 8}{born_time[0]}{space_symbol * 8}</u>"
            born_min = f"<u>{space_symbol * 8}{born_time[1]}{space_symbol * 8}</u>"
        death_date = death_date_result
        death_month = death_month_result
        death_year = death_year_result
        if fields_data.get("Время смерти", None):
            death_time = fields_data.get("Время смерти").split(":")
            death_hour = f"<u>{space_symbol * 8}{death_time[0]}{space_symbol * 8}</u>"
            death_min = f"<u>{space_symbol * 8}{death_time[1]}{space_symbol * 8}</u>"
    if fields_data.get("Дата рождения", None) is None:
        death_date = death_date_def
        death_month = death_month_def
        death_year = death_year_def

    text.append(Paragraph(f"2. Ребенок родился живым: {space_symbol * 11} число{born_date} месяц{born_month} год{born_year} час{born_hour} мин{born_min}", style))
    text.append(Spacer(1, 1.2 * mm))
    text.append(Paragraph(f" {space_symbol * 6}и умер (дата): {space_symbol * 28} число {death_date} месяц{death_month} год{death_year} час{death_hour} мин{death_min}", style))
    text.append(Spacer(1, 1.2 * mm))

    regarding_time = json.loads(fields_data["Наступление летального исхода относительно времени родов"])
    before_start_birth, during_birth, after_birth, not_known = "до начала родов", "во время родов", "после родов", "неизвестно"
    if regarding_time["title"].lower() == "до начала родов":
        before_start_birth = "<u>до начала родов</u>"
    elif regarding_time["title"].lower() == "во время родов":
        during_birth = "<u>во время родов</u>"
    elif regarding_time["title"].lower() == "после родов":
        after_birth = "<u>после родов</u>"
    elif regarding_time["title"].lower() == "неизвестно":
        not_known = "<u>неизвестно</u>"
    text.append(Paragraph(f"3. Смерть наступила: {before_start_birth} {digit_one} {during_birth} {digit_two} {after_birth} {digit_three} {not_known} {digit_four}", style))
    return text


def mother_fio_data(fields):
    mother_family = fields.get("Фамилия матери", "")
    mother_name = fields.get("Имя матери", "")
    mother_patronymic = fields.get("Отчество матери", "")
    return f"{mother_family} {mother_name} {mother_patronymic}"


def address_get(address_data):
    address_data = json.loads(address_data)
    area = "__________________"
    city = "____________________"
    street = "____________________"
    house = "______"
    flat = "_________"
    region, region_type, area_type, city_type, street_type, house_type, flat_type, postal_code, settlement, settlement_type = "", "", "", "", "", "", "", "", "", ""
    if address_data:
        address_details = address_data.get("details", None)
        region = address_details.get("region", "")
        region_type = address_details.get("region_type", "")
        area = address_details.get("area", "__________________")
        area_type = address_details.get("area_type", "")
        city = address_details.get("city", "____________________")
        city_type = address_details.get("city_type", "")
        street = address_details.get("street", "____________________")
        street_type = address_details.get("street_type", "")
        house = address_details.get("house", "______")
        house_type = address_details.get("house_type", "")
        flat = address_details.get("flat", "_________")
        flat_type = address_details.get("flat_type", "")
        postal_code = address_details.get("postal_code", "")
        settlement = address_details.get("settlement", None)
        settlement_type = address_details.get("settlement_type", None)
        if settlement and street == "":
            street = f"{settlement} {settlement_type}"
            settlement, settlement_type = "", ""

    return {
        "region": region,
        "region_type": region_type,
        "area": area,
        "area_type": area_type,
        "city": city,
        "city_type": city_type,
        "street": street,
        "street_type": street_type,
        "house": house,
        "house_type": house_type,
        "flat": flat,
        "flat_type": flat_type,
        "settlement": settlement,
        "settlement_type": settlement_type,
        "postal_code": postal_code,
    }


def place_death_get(data_fields):
    place_death = json.loads(data_fields["Типы мест наступления смерти"])
    stationar, home, other_place, not_know = "в  стационаре", "дома", "в другом месте", "неизвестно"
    if place_death["title"].lower() == "в стационаре":
        stationar = "<u>в стационаре</u>"
    elif place_death["title"].lower() == "дома":
        home = "<u>дома</u>"
    elif place_death["title"].lower() == "в другом месте":
        other_place = "<u>в другом месте</u>"
    elif place_death["title"].lower() == "неизвестно":
        not_know = "<u>неизвестно</u>"

    return {"stationar": stationar, "home": home, "other_place": other_place, "not_know": not_know}
