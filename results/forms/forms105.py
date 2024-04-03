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
styleT.fontSize = 9
styleT.leading = 3 * mm

styleOrg = deepcopy(styleT)
styleOrg.fontSize = 8

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

space_symbol = '&nbsp;'


def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None, **kwargs):
    # Мед. св-во о смерти 106/у
    data_individual = direction.client.get_data_individual()
    data = {}

    title_fields = [
        "Серия",
        "Префикс номера",
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
        "Вид места жительства",
        "Место смерти",
        "Вид места смерти",
        "Типы мест наступления смерти",
        "Новорожденый",
        "Доношенность новорожденного",
        "Место рождения",
        "Масса тела ребёнка при рождении",
        "По счету был ребенок",
        "Дата рождения матери",
        "Возраст матери",
        "ФИО матери",
        "Семейное положение",
        "Образование",
        "Социальная группа",
        "Полис ОМС",
        "СНИЛС",
        "Тип ДУЛ",
        "ДУЛ",
        "Род причины смерти",
        "Смерть от внешних причин",
        "Дата смерти от внешних причин",
        "Время смерти от внешних причин",
        "Дата события",
        "Время события",
        "Место и обстоятельства",
        "Тип медицинского работника",
        "Основания для определения причины смерти",
        "а) Болезнь или состояние, непосредственно приведшее к смерти",
        "б) патологическое состояние, которое привело к возникновению вышеуказанной причины:",
        "в) первоначальная причина смерти:",
        "г) внешняя причина при травмах и отравлениях:",
        "II. Прочие важные состояния, способствовавшие смерти, но не связанные с болезнью или патологическим состоянием, приведшим к ней",
        "ДТП",
        "Связь смерти с ДТП",
        "Беременность",
        "Связь смерти с беременностью",
        "ФИО (получатель)",
        "Документ (получатель)",
        "Серия (получатель)",
        "Номер (получатель)",
        "Кем и когда выдан (получатель)",
        "СНИЛС (получатель)",
        "Заполнил",
        "Проверил",
        "Главный врач",
        "Должность",
        "Время известно",
        "Только год",
    ]
    result = fields_result_only_title_fields(iss, title_fields, False)
    for i in result:
        data[i["title"]] = i["value"]

    data['fio'] = data_individual["fio"]
    data['sex'] = data_individual["sex"]
    diff = None
    if data.get("Только год", "") != "Да":
        ends = datetime.datetime.strptime(data["Дата рождения"], '%d.%m.%Y')
        start = datetime.datetime.strptime(data["Дата смерти"], '%d.%m.%Y')
        diff = relativedelta(start, ends)

    if diff and diff.years == 0:
        data['число месяцев жизни'] = diff.months
        data['число дней жизни'] = diff.days
    else:
        data['число месяцев жизни'] = ""
        data['число дней жизни'] = ""

    if not data.get("Только год", None):
        data["Только год"] = "Нет"

    if not data.get("Место рождения", None):
        data["Место рождения"] = (
            '{"details": {"region": "", "region_type": "", "area": "", "area_type": "", "city": "", "city_type": "", "settlement": "", "settlement_type": "", '
            '"street": "", "street_type": "", "house": "", "house_type": "", "flat": "", "flat_type": "", "postal_code": "", "custom": false}}'
        )

    if not data.get("Место смерти", None):
        data["Место смерти"] = (
            '{"details": {"region": "", "region_type": "", "area": "", "area_type": "", "city": "", "city_type": "", "settlement": "", "settlement_type": "", '
            '"street": "", "street_type": "", "house": "", "house_type": "", "flat": "", "flat_type": "", "postal_code": "", "custom": false}}'
        )

    if not data.get("Доношенность новорожденного", None):
        data["Доношенность новорожденного"] = '{"code": "", "title": ""}'

    if not data.get("Связь смерти с ДТП", None):
        data["Связь смерти с ДТП"] = '{"code": "", "title": ""}'

    if not data.get("Связь смерти с беременностью", None):
        data["Связь смерти с беременностью"] = '{"code": "", "title": ""}'

    if not data.get("Тип медицинского работника", None):
        data["Тип медицинского работника"] = '{"code": "", "title": ""}'

    if not data.get("Основания для определения причины смерти", None):
        data["Основания для определения причины смерти"] = '{"code": "", "title": ""}'

    if not data.get("Род причины смерти", None):
        data["Род причины смерти"] = '{"code": "", "title": ""}'

    if not data.get("Масса тела ребёнка при рождении", None):
        data["Масса тела ребёнка при рождении"] = ""

    if not data.get("По счету был ребенок", None):
        data["По счету был ребенок"] = ""

    if not data.get("Дата рождения матери", None):
        data["Дата рождения матери"] = ""

    if not data.get("Возраст матери", None):
        data["Возраст матери"] = ""

    if not data.get("ФИО (получатель)", None):
        data["ФИО (получатель)"] = ""

    if not data.get("Документ (получатель)", None):
        data["Документ (получатель)"] = ""

    if not data.get("Серия (получатель)", None):
        data["Серия (получатель)"] = ""

    if not data.get("Номер (получатель)", None):
        data["Номер (получатель)"] = ""

    if not data.get("Кем и когда выдан (получатель)", None):
        data["Кем и когда выдан (получатель)"] = ""

    if not data.get("СНИЛС (получатель)", None):
        data["СНИЛС (получатель)"] = ""

    if not data.get("Заполнил", None):
        data["Заполнил"] = iss.doc_confirmation.get_full_fio() if iss.doc_confirmation else ""

    if not data.get("Должность", None):
        data["Должность"] = iss.doc_position if iss.doc_confirmation else ""

    if not data.get("Проверил", None):
        data["Проверил"] = ""

    if not data.get("Главный врач", None):
        data["Главный врач"] = ""

    if not data.get("ФИО матери"):
        data["ФИО матери"] = '{"columns":{"titles":["Фамилия","Имя","Отчество"], "rows":[["иванова","Марья","Олеговна"]]}'

    mother_data = json.loads(data["ФИО матери"])
    data["mother_fio"] = f"{mother_data['rows'][0][0]} {mother_data['rows'][0][1]} {mother_data['rows'][0][2]}"
    data["Фамилия матери"] = ""
    data["Имя матери"] = ""
    data["Отчество матери"] = ""

    if data["Новорожденый"] in ["от 168 час. до 1 года", "от 168 час. до 1 месяца"]:
        data["Фамилия матери"] = mother_data['rows'][0][0]
        data["Имя матери"] = mother_data['rows'][0][1]
        data["Отчество матери"] = mother_data['rows'][0][2]

    if iss.doc_confirmation:
        hospital_obj: Hospitals = iss.doc_confirmation.get_hospital()
    else:
        hospital_obj: Hospitals = user.doctorprofile.get_hospital()

    data['org'] = {"full_title": hospital_obj.title, "org_address": hospital_obj.address, "org_license": hospital_obj.license_data, "org_okpo": hospital_obj.okpo}

    data["а"] = json.loads(data["а) Болезнь или состояние, непосредственно приведшее к смерти"])
    data["б"] = json.loads(data["б) патологическое состояние, которое привело к возникновению вышеуказанной причины:"])
    data["в"] = json.loads(data["в) первоначальная причина смерти:"])
    data["г"] = json.loads(data["г) внешняя причина при травмах и отравлениях:"])
    data["ii"] = json.loads(data["II. Прочие важные состояния, способствовавшие смерти, но не связанные с болезнью или патологическим состоянием, приведшим к ней"])

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
    # Мед. св-во о смерти 106/у
    text = []
    text = title_data(
        "КОРЕШОК МЕДИЦИНСКОГО СВИДЕТЕЛЬСТВА О СМЕРТИ",
        "К УЧЕТНОЙ ФОРМЕ № 106/У",
        text,
        fields.get("Серия", ""),
        fields.get("Номер", ""),
        fields.get("Дата выдачи", ""),
        fields.get("Вид медицинского свидетельства о смерти", ""),
        fields,
    )
    text.append(Spacer(1, 1.7 * mm))
    text = fio_tbl(text, "1. Фамилия, имя, отчество (при наличии) умершего(ей):", fields.get('fio', ''))

    # Пол
    text.append(Spacer(1, 0.3 * mm))
    text = sex_tbl(text, fields.get('sex', ''))

    # Дата рождения
    text = born_tbl(text, fields.get('Дата рождения', ''))
    text.append(Spacer(1, 0.3 * mm))

    # Дата смерти
    text = death_tbl(text, "4. Дата смерти:", fields.get('Дата смерти', '-'), fields.get('Время смерти', '-'))

    text = address_tbl(text, "5. Регистрация по месту жительства (пребывания) умершего(ей):", fields.get("Место постоянного жительства (регистрации)", ""))

    # Смерть наступила
    text = where_death_start_tbl(text, fields.get("Типы мест наступления смерти"), "6")
    text.append(Spacer(1, 0.2 * mm))

    text.append(Paragraph('Для детей, умерших в возрасте до 1 года:', styleBold))
    text.append(Spacer(1, 0.5 * mm))

    opinion = gen_opinion(
        [
            '7. Дата рождения',
            'число',
            fields['Дата рождения'].split('.')[0] if fields["Только год"] != "Да" else "",
            ', месяц',
            fields['Дата рождения'].split('.')[1] if fields["Только год"] != "Да" else "",
            ', год',
            fields['Дата рождения'].split('.')[2] if fields["Только год"] != "Да" else fields['Дата рождения'].split('.')[0],
            ', число месяцев',
            fields["число месяцев жизни"],
            ', число дней',
            fields["число дней жизни"],
            'жизни',
        ]
    )
    col_width = (29 * mm, 17 * mm, 8 * mm, 15 * mm, 8 * mm, 10 * mm, 12 * mm, 24 * mm, 8 * mm, 20 * mm, 8 * mm, 15 * mm)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), 0 * mm),
        ('LINEBELOW', (2, 0), (2, 0), 0.75, colors.black),
        ('LINEBELOW', (4, 0), (4, 0), 0.75, colors.black),
        ('LINEBELOW', (6, 0), (6, 0), 0.75, colors.black),
        ('LINEBELOW', (8, 0), (8, 0), 0.75, colors.black),
        ('LINEBELOW', (10, 0), (10, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    text = address_tbl(text, "8. Место рождения", fields["Место рождения"])
    text = fio_tbl(text, "9. Фамилия, имя, отчество (при наличии) матери:", fields["mother_fio"])

    obj = []
    obj.append(FrameDataUniversal(0 * mm, offset, 190 * mm, 95 * mm, text=text))
    return obj


def add_line_split(iss: Issledovaniya, direction, offset=0):
    # Лини отреза
    text = []
    text = line_split(text)
    obj = [(FrameDataUniversal(0 * mm, offset, 190 * mm, 5 * mm, text=text))]
    return obj


def death_data(iss: Issledovaniya, direction, fields, offset=0):
    # Лини отреза
    text = []
    text = title_med_organization(text, fields['org'])
    text = title_data(
        "МЕДИЦИНСКОЕ СВИДЕТЕЛЬСТВО О СМЕРТИ", "", text, fields["Серия"], fields.get("Номер", ""), fields["Дата выдачи"], fields["Вид медицинского свидетельства о смерти"], fields
    )
    text.append(Spacer(1, 1.7 * mm))
    text = fio_tbl(text, "1. Фамилия, имя, отчество (при наличии) умершего(ей):", fields["fio"])

    # Пол
    text.append(Spacer(1, 0.3 * mm))
    text = sex_tbl(text, fields['sex'])

    # Дата рождения
    text = born_tbl(text, fields['Дата рождения'])

    # print(fields["Тип ДУЛ"])
    dul = json.loads(fields["ДУЛ"])
    text = patient_passport(text, {"type": fields["Тип ДУЛ"], "serial": dul['rows'][0][0], "number": dul['rows'][0][1]})
    text = who_issue_passport(text, {"who_issue": dul['rows'][0][2], "date_issue": dul['rows'][0][3]})
    text = patient_snils(text, fields["СНИЛС"] or "")
    text = patient_polis(text, fields["Полис ОМС"] or "")
    text = death_tbl(text, "7. Дата смерти:", fields.get('Дата смерти', '-'), fields.get('Время смерти', '-'))
    text = address_tbl(text, "8. Регистрация по месту жительства (пребывания) умершего(ей):", fields["Место постоянного жительства (регистрации)"])
    text = type_city(text, "9. Местность:", fields["Вид места жительства"])
    text = address_tbl(text, "10. Место смерти:", fields["Место смерти"])
    text = type_city(text, "11. Местность: ", fields["Вид места смерти"])
    text = where_death_start_tbl(text, fields["Типы мест наступления смерти"], "12")
    text = child_death_befor_month(text, fields["Доношенность новорожденного"])
    text = child_death_befor_year(
        text,
        {
            "weight": fields["Масса тела ребёнка при рождении"],
            "child_count": fields["По счету был ребенок"],
            "mother_born": fields["Дата рождения матери"],
            "mother_age": fields["Возраст матери"],
            "mother_family": fields["Фамилия матери"],
            "mother_name": fields["Имя матери"],
            "mother_patronimyc": fields["Отчество матери"],
        },
    )
    text = family_status(text, fields["Семейное положение"])
    text = education(text, fields["Образование"])
    text = work_position(text, fields["Социальная группа"])
    text = bottom_colontitul(text, "* В случае смерти детей, возраст которых указан в пунктах 13 - 14, пункты 15 - 17 заполняются в отношении их матерей.")

    obj = []
    obj.append(FrameDataUniversal(0 * mm, offset, 190 * mm, 178 * mm, text=text))

    return obj


def second_page_add_template(iss: Issledovaniya, direction, fields, offset=0):
    text = []
    text = back_size(text)
    text = why_death(text, fields, '10', '11', '12', '13')
    text = fio_tbl(text, "14. Фамилия, имя, отчество (при наличии) получателя", fields["ФИО (получатель)"])
    text.append(Paragraph("Документ, удостоверяющий личность получателя (серия, номер, кем выдан)", styleT))
    text = destination_person_passport(text, f'{fields["Документ (получатель)"]} {fields["Серия (получатель)"]} {fields["Номер (получатель)"]} {fields["Кем и когда выдан (получатель)"]}')
    text = destination_person_snils(text, f'{fields["СНИЛС (получатель)"]}')
    text.append(Spacer(1, 2 * mm))
    text.append(Paragraph(f"«___» ___________ 20 ___ г.{space_symbol * 30} Подпись получателя _________________________", styleT))

    obj = []
    obj.append(FrameDataUniversal(0 * mm, offset, 190 * mm, 95 * mm, text=text))

    return obj


def death_data2(iss: Issledovaniya, direction, fields, offset=0):
    text = []
    text = death_happaned(text, fields["Род причины смерти"])
    date, month, year, hour, min = "____", "____", "_________", "____", "____"
    date_event_data = fields.get("Дата события", None)
    time_event_data = fields.get("Время события", None)
    if date_event_data:
        date_event_data = date_event_data.split(".")
        date = f"<u>{space_symbol * 3}{date_event_data[0]}{space_symbol * 3}</u>"
        month = f"<u>{space_symbol * 3}{date_event_data[1]}{space_symbol * 3}</u>"
        year = f"<u>{space_symbol * 3}{date_event_data[2]}{space_symbol * 3}</u>"
    if time_event_data:
        time_event_data = time_event_data.split(":")
        hour = f"<u>{space_symbol * 3}{time_event_data[0]}{space_symbol * 3}</u>"
        min = f"<u>{space_symbol * 3}{time_event_data[1]}{space_symbol * 3}</u>"

    text.append(
        Paragraph(
            f"19. В случае смерти от несчастного случая, убийства, самоубийства, от военных и террористических действий, при неустановленном роде смерти - указать дату травмы (отравления): "
            f"число {date} месяц {month} год {year} час. {hour} мин. {min} , а также место и обстоятельства, при которых произошла травма (отравление)",
            styleT,
        )
    )

    unfortunate_and_other_info = "________________________________________________________________________________________________________________________"
    place_and_reasons = fields.get("Место и обстоятельства", None)
    if place_and_reasons:
        unfortunate_and_other_info = f"<u>{space_symbol * 2}{place_and_reasons} {space_symbol * 2}</u>"
    text.append(Paragraph(f"{unfortunate_and_other_info}", styleT))
    text = who_set_death(text, fields["Тип медицинского работника"])
    text = doctor_fio(text, fields, iss)
    text.append(Spacer(1, 1 * mm))
    text = why_death(text, fields, "22", "23", "24", "25")
    text.append(Spacer(1, 2 * mm))
    text.append(
        Paragraph("<u>Руководитель (иное уполномоченное лицо **) медицинской организации</u>, индивидуальный предприниматель, осуществляющий медицинскую деятельность (подчеркнуть)", styleT)
    )
    text.append(Spacer(1, 2 * mm))
    text = hospital_manager_stamp(text, fields["Главный врач"])
    text.append(Spacer(1, 2 * mm))
    text.append(Paragraph("26 Свидетельство проверено ответственным за правильность заполнения медицинских свидетельств.", styleT))
    text = check_person_data(text, fields["Проверил"])
    text = bottom_colontitul(
        text,
        '** В случае, установленном частью 10 статьи 9 Федерального закона от 5 июня 2012 г. № 50-ФЗ "О регулировании деятельности российских граждан и '
        'российских юридических лиц в Антарктике" (Собрание законодательства Российской Федерации, 2012, № 24, ст. 3067). ',
    )
    obj = []
    obj.append(FrameDataUniversal(0 * mm, offset, 190 * mm, 168 * mm, text=text))
    return obj


# общие функции
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
    if title_name == "МЕДИЦИНСКОЕ СВИДЕТЕЛЬСТВО О СМЕРТИ":
        final, preparatory = "окончательное", "предварительное"

    type_death_document = json.loads(type_document)
    if type_death_document["code"] == '4':
        instead_final = f"<u>{op_bold_tag}{instead_final}{cl_bold_tag}</u>"
    elif type_death_document["code"] == '3':
        instead_preparatory = f"<u>{op_bold_tag}{instead_preparatory}{cl_bold_tag}</u>"
    elif type_death_document["code"] == '1':
        final = f"{op_bold_tag}<u>{final}</u>{cl_bold_tag}"
    elif type_death_document["code"] == '2':
        preparatory = f"<u>{op_bold_tag}{preparatory}{cl_bold_tag}</u>"
    text.append(Paragraph(f"({final}, {preparatory}, {instead_preparatory}, {instead_final}) (подчеркнуть)", styleCentre))
    if data_fields.get("Серия предшествующего", None):
        text.append(Paragraph("ранее выданное свидетельство", styleCentre))
        text.append(Paragraph(f"серия {data_fields['Серия предшествующего']} No {data_fields['Номер предшествующего']} от {data_fields['Дата выдачи предшествующего']} г.", styleCentre))
    else:
        text.append(Paragraph("ранее выданное свидетельство", styleCentre))
        text.append(Paragraph('серия _____  No___________ от "___"__________" г.', styleCentre))
    return text


def gen_opinion(data):
    opinion = [[Paragraph(f"{k}", styleT) for k in data]]
    return opinion


def gen_opinion_diag(data):
    opinion = [[Paragraph(f"{k}", styleOrgBold) for k in data]]
    return opinion


def gen_table(opinion, col_width, tbl_style, row_height=None):
    tbl = Table(
        opinion,
        colWidths=col_width,
        rowHeights=row_height,
        hAlign='LEFT',
    )
    tbl.setStyle(TableStyle(tbl_style))
    return tbl


def fio_tbl(text, type, fio):
    opinion = gen_opinion([type, fio])
    col_width = (80 * mm, 110 * mm)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)
    return text


def sex_tbl(text, sex):
    if sex == "м":
        sex_m = f'{op_bold_tag}<u>мужской</u>{cl_bold_tag}'
    else:
        sex_m = ' мужской'
    if sex == "ж":
        sex_w = f'{op_bold_tag}<u>женский</u>{cl_bold_tag}'
    else:
        sex_w = ', женский'

    opinion = gen_opinion(['2.Пол:', sex_m, '1', sex_w, '2'])
    col_width = (11 * mm, 17 * mm, 6 * mm, 19 * mm, 6 * mm)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (-1, -1), (-1, -1), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)
    return text


def born_tbl(text, born_data):
    # Дата рождения
    born = born_data.split('.')
    born_day = ""
    born_month = ""
    born_year = ""
    if len(born) > 1:
        born_day = born[0]
        born_month = born[1]
        born_year = born[2]
    if len(born) == 1:
        born_year = born[0]

    opinion = gen_opinion(['3.Дата рождения:', 'число', born_day, 'месяц', born_month, 'год', born_year])

    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LEFTPADDING', (0, 1), (0, 1), 0 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LINEBELOW', (2, 0), (2, 0), 0.75, colors.black),
        ('LINEBELOW', (4, 0), (4, 0), 0.75, colors.black),
        ('LINEBELOW', (6, 0), (6, 0), 0.75, colors.black),
        ('LINEBELOW', (2, 1), (2, 1), 0.75, colors.black),
        ('LINEBELOW', (4, 1), (4, 1), 0.75, colors.black),
        ('LINEBELOW', (6, 1), (6, 1), 0.75, colors.black),
        ('LINEBELOW', (8, 1), (8, 1), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    col_width = (28 * mm, 14 * mm, 8 * mm, 14 * mm, 8 * mm, 10 * mm, 12 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)
    return text


def death_tbl(text, number, death_data, death_time):
    # Дата смерти
    death_data = death_data.split('.')
    death_day = death_data[0]
    death_month = death_data[1]
    death_year = death_data[2]
    death_hour, death_min = "", ""
    if death_time:
        death_time = death_time.split(":")
        death_hour = death_time[0] if len(death_time) >= 1 else " "
        death_min = death_time[1] if len(death_time) >= 2 else " "

    opinion = gen_opinion([number, 'число', death_day, 'месяц', death_month, 'год', death_year, 'час.', death_hour, 'мин.', death_min])

    tbl_style = [
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LEFTPADDING', (0, 1), (0, 1), 0 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -1 * mm),
        ('LINEBELOW', (2, 0), (2, 0), 0.75, colors.black),
        ('LINEBELOW', (4, 0), (4, 0), 0.75, colors.black),
        ('LINEBELOW', (6, 0), (6, 0), 0.75, colors.black),
        ('LINEBELOW', (8, 0), (8, 0), 0.75, colors.black),
        ('LINEBELOW', (10, 0), (10, 0), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    col_width = (28 * mm, 14 * mm, 8 * mm, 14 * mm, 8 * mm, 10 * mm, 12 * mm, 10 * mm, 8 * mm, 12 * mm, 8 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    return text


def address_tbl(text, type_address, address):
    data_address = json.loads(address)
    address_details = data_address["details"]
    opinion = gen_opinion([f'{type_address} субъект Российской Федерации:', f"{address_details['region_type']} {address_details['region']}"])
    col_widths = (135 * mm, 55 * mm)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_widths, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    # город
    opinion = gen_opinion(['район', f"{address_details['area_type']} {address_details['area']}", 'город', f"{address_details['city_type']} {address_details['city']}"])
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('LINEBELOW', (3, 0), (3, 0), 0.75, colors.black),
    ]
    col_width = (
        17 * mm,
        77 * mm,
        16 * mm,
        80 * mm,
    )
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    # населенный пунк
    opinion = gen_opinion(
        ['населенный пункт', f"{address_details['settlement_type']} {address_details['settlement']}", 'улица', f"{address_details['street_type']} {address_details['street']}"]
    )
    col_width = (
        37 * mm,
        67 * mm,
        16 * mm,
        70 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('LINEBELOW', (3, 0), (3, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    # дом, стр, корп, кв, комн
    opinion = gen_opinion(['дом', address_details['house'], 'стр.', '', 'корп.', '', 'кв.', address_details.get("flat", ""), 'комн.', ''])
    col_width = (
        14 * mm,
        15 * mm,
        12 * mm,
        12 * mm,
        14 * mm,
        15 * mm,
        12 * mm,
        15 * mm,
        14 * mm,
        15 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('LINEBELOW', (3, 0), (3, 0), 0.75, colors.black),
        ('LINEBELOW', (5, 0), (5, 0), 0.75, colors.black),
        ('LINEBELOW', (7, 0), (7, 0), 0.75, colors.black),
        ('LINEBELOW', (9, 0), (9, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)
    return text


def where_death_start_tbl(text, params, item_param):
    whera_data = json.loads(params)
    place, car, hospital, home = ' на месте происшествия', ', в машине скорой помощи', ', в стационаре', ', дома'
    if whera_data["code"] == '1':
        place = f"<u>{op_bold_tag}{place}{cl_bold_tag}</u>"
    elif whera_data["code"] == '2':
        car = f"<u>{op_bold_tag}{car}{cl_bold_tag}</u>"
    elif whera_data["code"] == '3':
        hospital = f"<u>{op_bold_tag}{hospital}{cl_bold_tag}</u>"
    elif whera_data["code"] == '4':
        home = f"<u>{op_bold_tag}{home}{cl_bold_tag}</u>"
    opinion = gen_opinion([f'{item_param}.Смерть наступила:', place, '1', car, '2', hospital, '3', home, '4'])
    col_width = (
        32 * mm,
        37 * mm,
        6 * mm,
        42 * mm,
        6 * mm,
        24 * mm,
        6 * mm,
        12 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),
        ('GRID', (6, 0), (6, 0), 0.75, colors.black),
        ('GRID', (8, 0), (8, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    # Смерть наступила
    education_place, other_place = 'в образовательной организации', 'в другом месте'
    if whera_data["code"] == '7':
        education_place = f"<u>{op_bold_tag}{education_place}{cl_bold_tag}</u>"
    elif whera_data["code"] == '5':
        other_place = f"<u>{op_bold_tag}{other_place}{cl_bold_tag}</u>"

    opinion = gen_opinion([education_place, '5', other_place, '6'])
    col_width = (
        55 * mm,
        6 * mm,
        24 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)
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


def patient_passport(text, data_document):
    if "-" in data_document["type"]:
        document_type = data_document["type"].split("-")
        document_type_print = document_type[1]
    else:
        document_type_print = data_document["type"]
    opinion = gen_opinion(['4.Документ, удостоверяющий личность умершего:', document_type_print, 'серия', data_document["serial"], 'номер', data_document['number']])
    tbl_style = [
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('LINEBELOW', (3, 0), (3, 0), 0.75, colors.black),
        ('LINEBELOW', (5, 0), (5, 0), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    col_width = (71 * mm, 68 * mm, 12 * mm, 11 * mm, 14 * mm, 14 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)
    return text


def who_issue_passport(text, data_document):
    opinion = gen_opinion(['кем и когда выдан', f"{data_document['who_issue']} {data_document['date_issue']}"])
    tbl_style = [
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    col_width = (33 * mm, 157 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)
    return text


def patient_snils(text, snils_number):
    opinion = gen_opinion(['5.СНИЛС', snils_number])
    tbl_style = [
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    col_width = (23 * mm, 167 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)
    return text


def patient_polis(text, polis_number):
    opinion = gen_opinion(['6.Полис ОМС:', polis_number])

    tbl_style = [
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    col_width = (23 * mm, 167 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)
    return text


def type_city(
    text,
    type_value,
    type,
):
    type_gorod, type_selo = ' городская', ', сельская'
    type = json.loads(type)
    if type["code"] == "1":
        type_gorod = f'{op_bold_tag}<u>городская</u>{cl_bold_tag}'
    if type["code"] == "2":
        type_selo = f'{op_bold_tag}<u>сельская</u>{cl_bold_tag}'

    opinion = gen_opinion([type_value, type_gorod, '1', type_selo, '2'])
    col_width = (23 * mm, 19 * mm, 6 * mm, 18 * mm, 6 * mm)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (-1, -1), (-1, -1), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)
    return text


def child_death_befor_month(text, params):
    params = json.loads(params)
    week37_41, week_smaller, week_more_42 = ' доношенный (37-41 недель)', ' , недоношенный (менее 37 недель)', ', переношенный (42 недель и более)'
    if params["code"] == "1":
        week37_41 = f"{op_bold_tag}<u>{week37_41}</u>{cl_bold_tag}"
    if params["code"] == "2":
        week_smaller = f"{op_bold_tag}<u>{week_smaller}</u>{cl_bold_tag}"
    if params["code"] == "3":
        week_more_42 = f"{op_bold_tag}<u>{week_more_42}</u>{cl_bold_tag}"
    opinion = gen_opinion(['13. * Для детей, умерших в возрасте от 168 час. до 1 месяца:', week37_41, '1'])
    col_width = (85 * mm, 42 * mm, 6 * mm)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    opinion = gen_opinion([week_smaller, '2', week_more_42, '3'])
    col_width = (57 * mm, 6 * mm, 55 * mm, 6 * mm)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (4, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)
    return text


def child_death_befor_year(text, params):
    opinion = gen_opinion(['14.*Для детей, умерших в возрасте от 168 час. до 1 года:', ' масса тела ребёнка при рождении', params["weight"], ' грамм', '1'])
    col_width = (
        82 * mm,
        50 * mm,
        12 * mm,
        12 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('LINEBELOW', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    opinion = gen_opinion(['каким по счету был ребенок у матери (считая умерших и не считая мертворождённых)', params["child_count"], '', '2'])
    col_width = (
        125 * mm,
        6 * mm,
        5 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    opinion = gen_opinion(['дата рождения матери', params["mother_born"], '', '3', 'возраст матери (полных лет)', params["mother_age"], '', '4'])
    col_width = (
        40 * mm,
        19 * mm,
        5 * mm,
        6 * mm,
        45 * mm,
        15 * mm,
        5 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
        ('LINEBELOW', (5, 0), (5, 0), 0.75, colors.black),
        ('GRID', (7, 0), (7, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.5 * mm))
    text.append(tbl)

    opinion = gen_opinion(['фамилия матери', params["mother_family"], '', '5', ', имя', params["mother_name"], '', '6', ' , отчество (при наличии)', params["mother_patronimyc"], '', '7'])
    col_width = (
        30 * mm,
        25 * mm,
        5 * mm,
        6 * mm,
        14 * mm,
        20 * mm,
        5 * mm,
        6 * mm,
        40 * mm,
        25 * mm,
        5 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
        ('LINEBELOW', (5, 0), (5, 0), 0.75, colors.black),
        ('GRID', (7, 0), (7, 0), 0.75, colors.black),
        ('LINEBELOW', (9, 0), (9, 0), 0.75, colors.black),
        ('GRID', (11, 0), (11, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.5 * mm))
    text.append(tbl)
    return text


def family_status(text, params):
    params = json.loads(params)
    brak, not_brak, not_known = "состоял(а) в зарегистрированном браке", "не состоял(а) в зарегистрированном браке", "неизвестно"
    if params["code"] == '3':
        not_known = f"{op_bold_tag}<u>{not_known}</u>{cl_bold_tag}"
    elif params["code"] == '4':
        brak = f"{op_bold_tag}<u>{brak}</u>{cl_bold_tag}"
    elif params["code"] == '5':
        not_brak = f"{op_bold_tag}<u>{not_brak}</u>{cl_bold_tag}"
    opinion = gen_opinion(['15.*Семейное положение:', brak, '1', not_brak, '2', not_known, '3'])
    col_width = (
        38 * mm,
        60 * mm,
        6 * mm,
        60 * mm,
        6 * mm,
        18 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),
        ('GRID', (6, 0), (6, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)
    return text


def education(text, params):
    high_prof, not_high_prof, middle_prof, middle_common = "профессиональное: высшее", ", неполное высшее", ", среднее профессиональное", "общее: среднее"
    params = json.loads(params)
    if params["code"] == '1':
        high_prof = f"{op_bold_tag}<u>{high_prof}</u>{cl_bold_tag}"
    elif params["code"] == '2':
        not_high_prof = f"{op_bold_tag}<u>{not_high_prof}</u>{cl_bold_tag}"
    elif params["code"] == '3':
        middle_prof = f"{op_bold_tag}<u>{middle_prof}</u>{cl_bold_tag}"
    elif params["code"] == '5':
        middle_common = f"{op_bold_tag}<u>{middle_common}</u>{cl_bold_tag}"

    opinion = gen_opinion(['16.* Образование:', high_prof, '1', not_high_prof, '2', middle_prof, '3', middle_common, '4'])
    col_width = (
        29 * mm,
        42 * mm,
        6 * mm,
        30 * mm,
        6 * mm,
        41 * mm,
        6 * mm,
        25 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -1 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),
        ('GRID', (6, 0), (6, 0), 0.75, colors.black),
        ('GRID', (8, 0), (8, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    common, start, before_school, not_has_start, not_known = "основное", ", начальное", ", дошкольное", ", не имеет начального образования", ", неизвестно"
    if params["code"] == '6':
        common = f"{op_bold_tag}<u>{common}</u>{cl_bold_tag}"
    elif params["code"] == '7':
        start = f"{op_bold_tag}<u>{start}</u>{cl_bold_tag}"
    elif params["code"] == '10':
        before_school = f"{op_bold_tag}<u>{before_school}</u>{cl_bold_tag}"
    elif params["code"] == '11':
        not_has_start = f"{op_bold_tag}<u>{not_has_start}</u>{cl_bold_tag}"
    elif params["code"] == '9':
        not_known = f"{op_bold_tag}<u>{not_known}</u>{cl_bold_tag}"
    opinion = gen_opinion([common, '5', start, '6', before_school, '7', not_has_start, '8', not_known, '9'])
    col_width = (
        20 * mm,
        6 * mm,
        20 * mm,
        6 * mm,
        21 * mm,
        6 * mm,
        50 * mm,
        6 * mm,
        19 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
        ('GRID', (5, 0), (5, 0), 0.75, colors.black),
        ('GRID', (7, 0), (7, 0), 0.75, colors.black),
        ('GRID', (9, 0), (9, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)
    return text


def work_position(text, params):
    params = json.loads(params)
    worked, military, pensioner, student = "работал(а)", ", проходил(а) военную или приравненную к ней службу", ", пенсионер(ка)", "студент(ка)"
    if params["code"] == '5':
        worked = f"{op_bold_tag}<u>{worked}</u>{cl_bold_tag}"
    elif params["code"] == '17':
        military = f"{op_bold_tag}<u>{military}</u>{cl_bold_tag}"
    elif params["code"] == '7':
        pensioner = f"{op_bold_tag}<u>{pensioner}</u>{cl_bold_tag}"
    elif params["code"] == '4':
        student = f"{op_bold_tag}<u>{student}</u>{cl_bold_tag}"
    opinion = gen_opinion(['17. * Занятость:', worked, '1', military, '2', pensioner, '3', student, '4'])

    col_width = (
        24 * mm,
        18 * mm,
        6 * mm,
        80 * mm,
        6 * mm,
        24 * mm,
        6 * mm,
        20 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),
        ('GRID', (6, 0), (6, 0), 0.75, colors.black),
        ('GRID', (8, 0), (8, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    not_work, others, not_known = "не работал(а)", ", прочие", ", неизвестно"
    if params["code"] == '8':
        not_work = f"{op_bold_tag}<u>{not_work}</u>{cl_bold_tag}"
    elif params["code"] == '10':
        others = f"{op_bold_tag}<u>{others}</u>{cl_bold_tag}"
    elif params["code"] == '22':
        not_known = f"{op_bold_tag}<u>{not_known}</u>{cl_bold_tag}"

    opinion = gen_opinion([not_work, '5', others, '6', not_known, '7'])
    col_width = (
        28 * mm,
        6 * mm,
        17 * mm,
        6 * mm,
        21 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
        ('GRID', (5, 0), (5, 0), 0.75, colors.black),
        ('GRID', (7, 0), (7, 0), 0.75, colors.black),
        ('GRID', (9, 0), (9, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)
    return text


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
                'Код формы по ОКУД _______<br/>Медицинская документация<br/>Учётная форма № 106/У<br/>Утверждена приказом Минздрава России <br/>от «15» апреля 2021 г. № 352н', styleOrg
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


def why_death(text, params, item_why, item_dtp, item_pregnant, item_doc):
    opinion = [
        [
            Paragraph(f"{item_why}. Причины смерти:", styleT),
            Paragraph('Приблизительный период времени между началом патологического процесса и смертью', styleOrg),
            Paragraph('Коды по МКБ', styleOrg),
        ],
    ]
    col_width = (
        114 * mm,
        36 * mm,
        40 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
        ('LEFTPADDING', (2, 0), (2, 0), 8 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)
    tbl = diagnos_tbl({"para": "I", "item": "а)", "result": params["а"]["rows"][0]})
    text.append(Spacer(1, 0.3 * mm))
    text.append(tbl)

    tbl = about_diagnos("(болезнь или состояние, непосредственно приведшее к смерти)")
    text.append(Spacer(1, 0.1 * mm))
    text.append(tbl)
    tbl = diagnos_tbl({"para": "", "item": "б)", "result": params["б"]["rows"][0]})
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    tbl = about_diagnos("(патологическое состояние, которое привело к возникновению причины, указанной в пункте «а»)")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    tbl = diagnos_tbl({"para": "", "item": "в)", "result": params["в"]["rows"][0]})
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    tbl = about_diagnos("(первоначальная причина смерти указывается последней)")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)
    tbl = diagnos_tbl({"para": "", "item": "г)", "result": params["г"]["rows"][0]})
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    tbl = about_diagnos("(внешняя причина при травмах и отравлениях)")
    text.append(Spacer(1, 0 * mm))
    text.append(tbl)

    opinion = [
        [
            Paragraph(
                'II. Прочие важные состояния, способствовавшие смерти, но не связанные с болезнью или патологическим состоянием, приведшим к ней, включая употребление '
                'алкоголя, наркотических средств, психотропных и других токсических веществ, содержание их в крови, а также операции (название, дата)',
                styleColontitul,
            ),
        ],
    ]
    col_width = (190 * mm,)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (-1, -1), (-1, -1), 1 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.1 * mm))
    text.append(tbl)
    text.append(Spacer(1, 0.6 * mm))

    data_ii = params["ii"]["rows"]
    for k in range(len(data_ii)):
        tbl = diagnos_tbl({"para": "", "item": "", "result": data_ii[k], "top_padd": -1.2 * mm})
        text.append(Spacer(1, 0 * mm))
        text.append(tbl)

    days30, days7 = "смерть наступила - в течение 30 суток", ", из них в течение 7 суток"
    dtp_death = json.loads(params["Связь смерти с ДТП"])

    if dtp_death["code"] == "1":
        days30 = f"{op_bold_tag}<u>{days30}</u>{cl_bold_tag}"
    elif dtp_death["code"] == "2":
        days7 = f"{op_bold_tag}<u>{days7}</u>{cl_bold_tag}"

    opinion = gen_opinion([f'{item_dtp}.В случае смерти в результате ДТП:', days30, '1', days7, '2'])
    col_width = (
        55 * mm,
        55 * mm,
        6 * mm,
        40 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    pregnant, process_birth = "(независимо от срока и локализации)", ", в процессе родов"
    pregnant_data = json.loads(params["Связь смерти с беременностью"])
    if pregnant_data["code"] == "1":
        pregnant = f"{op_bold_tag}<u>{pregnant}</u>{cl_bold_tag}"
    elif pregnant_data["code"] == "2":
        process_birth = f"{op_bold_tag}<u>{process_birth}</u>{cl_bold_tag}"

    opinion = gen_opinion([f'{item_pregnant}.В случае смерти беременной', pregnant, '1', process_birth, '2'])
    col_width = (
        50 * mm,
        52 * mm,
        6 * mm,
        30 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LEFTPADDING', (1, 0), (1, 0), -2 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    final_process_birth_42days, final_process_birth_365days = "в течение 42 дней после окончания беременности, родов", ", кроме того в течение 43-365 дней после окончания беременности"
    if pregnant_data["code"] == "3":
        final_process_birth_42days = f"{op_bold_tag}<u>{final_process_birth_42days}</u>{cl_bold_tag}"
    elif pregnant_data["code"] == "4":
        final_process_birth_365days = f"{op_bold_tag}<u>{final_process_birth_365days}</u>{cl_bold_tag}"

    opinion = gen_opinion([final_process_birth_42days, '3', final_process_birth_365days, '4'])
    col_width = (
        84 * mm,
        6 * mm,
        98 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 4 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    opinion = gen_opinion([f'{item_doc}.Фамилия, имя, отчество (при наличии) врача (фельдшера, акушерки), заполнившего Медицинское свидетельство о смерти'])
    col_width = (190 * mm,)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    opinion = gen_opinion([f'{params["Заполнил"]}', 'Подпись', ''])
    col_width = (140 * mm, 20 * mm, 30 * mm)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LINEBELOW', (0, 0), (0, 0), 0.75, colors.black),
        ('LINEBELOW', (2, 0), (2, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)

    return text


def diagnos_tbl(data):
    description_diag = data["result"][2]
    description_diag_json = None
    if len(description_diag) > 1:
        description_diag_json = json.loads(description_diag)
    decription = ''
    period = ""
    top_padd = 0 * mm
    mkb10 = ["", "", "", "", ""]
    if len(description_diag) > 1:
        decription = description_diag_json["title"]
        mkb10 = list(description_diag_json["code"])
        if len(list(decription)) > 72:
            top_padd = -2 * mm
        period = f'{data["result"][0]} {data["result"][1]}'

    if data.get("top_padd", None):
        top_padd = data.get("top_padd")

    elements = []
    for element in range(5):
        try:
            elements.insert(element, mkb10[element])
        except:
            elements.insert(element, "")

    opinion = gen_opinion_diag([data["para"], data["item"], decription, period, '', elements[0], elements[1], elements[2], '.', elements[4]])
    col_width = (
        6 * mm,
        7 * mm,
        102 * mm,
        36 * mm,
        5 * mm,
        8 * mm,
        7 * mm,
        7 * mm,
        6 * mm,
        7 * mm,
    )
    tbl_style = [
        ('GRID', (5, 0), (5, 0), 0.75, colors.black),
        ('GRID', (6, 0), (6, 0), 0.75, colors.black),
        ('GRID', (7, 0), (7, 0), 0.75, colors.black),
        ('GRID', (9, 0), (9, 0), 0.75, colors.black),
        ('LINEBELOW', (0, 0), (3, 0), 0.75, colors.black),
        ('LINEBEFORE', (3, 0), (3, 0), 0.75, colors.black),
        ('LINEAFTER', (3, 0), (3, 0), 0.75, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('TOPPADDING', (2, 0), (2, 0), top_padd),
        ('LEFTPADDING', (2, 0), (2, 0), -2 * mm),
        ('LEFTPADDING', (3, 0), (3, 0), 10 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style, 4 * mm)
    return tbl


def about_diagnos(data):
    styleMicro = deepcopy(styleT)
    styleMicro.fontSize = 5.5
    styleMicro.alignment = TA_CENTER
    opinion = [
        [
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph(f'{data}', styleMicro),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
        ],
    ]
    col_width = (
        6 * mm,
        7 * mm,
        102 * mm,
        36 * mm,
        5 * mm,
        7 * mm,
        7 * mm,
        7 * mm,
        6 * mm,
        7 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), -0.5 * mm),
        ('LINEBEFORE', (3, 0), (3, 0), 0.75, colors.black),
        ('LINEAFTER', (3, 0), (3, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    return tbl


def destination_person_passport(text, data):
    opinion = gen_opinion([data])
    tbl_style = [
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LINEBELOW', (0, 0), (-1, -1), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    col_width = 190 * mm
    tbl = gen_table(opinion, col_width, tbl_style, 8 * mm)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)
    return text


def destination_person_snils(text, data):
    opinion = gen_opinion(['СНИЛС получателя (при наличии)', data])
    tbl_style = [
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
    ]
    col_width = (50 * mm, 140 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.2 * mm))
    text.append(tbl)
    return text


def death_happaned(text, params):
    ill, unfortunate_not_work, unfortunate_work = "от заболевания", "несчастного случая: не связанного с производством", "связанного с производством"
    type_happend = json.loads(params)
    if type_happend["code"] == "1":
        ill = f"{op_bold_tag}<u>{ill}</u>{cl_bold_tag}"
    elif type_happend["code"] == "2":
        unfortunate_not_work = f"{op_bold_tag}<u>{unfortunate_not_work}</u>{cl_bold_tag}"
    elif type_happend["code"] == "3":
        unfortunate_work = f"{op_bold_tag}<u>{unfortunate_work}</u>{cl_bold_tag}"

    opinion = gen_opinion(['18. Смерть произошла:', ill, '1', unfortunate_not_work, '2', unfortunate_work, '3'])

    col_width = (
        34 * mm,
        24 * mm,
        6 * mm,
        74 * mm,
        6 * mm,
        43 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),
        ('GRID', (6, 0), (6, 0), 0.75, colors.black),
        ('GRID', (8, 0), (8, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    kill, self_kill, military, terrorist, not_know = "убийства", "самоубийства", ", в ходе действий: военных", "террористических", ", род смерти не установлен"
    if type_happend["code"] == "4":
        kill = f"{op_bold_tag}<u>{kill}</u>{cl_bold_tag}"
    elif type_happend["code"] == "5":
        self_kill = f"{op_bold_tag}<u>{self_kill}</u>{cl_bold_tag}"
    elif type_happend["code"] == "6":
        military = f"{op_bold_tag}<u>{military}</u>{cl_bold_tag}"
    elif type_happend["code"] == "7":
        terrorist = f"{op_bold_tag}<u>{terrorist}</u>{cl_bold_tag}"
    elif type_happend["code"] == "8":
        not_know = f"{op_bold_tag}<u>{not_know}</u>{cl_bold_tag}"

    opinion = gen_opinion([kill, '4', self_kill, '5', military, '6', terrorist, '7', not_know, '8'])
    col_width = (
        22 * mm,
        6 * mm,
        23 * mm,
        6 * mm,
        40 * mm,
        6 * mm,
        30 * mm,
        6 * mm,
        40 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
        ('GRID', (5, 0), (5, 0), 0.75, colors.black),
        ('GRID', (7, 0), (7, 0), 0.75, colors.black),
        ('GRID', (9, 0), (9, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)
    return text


def who_set_death(text, params):
    only_doc_death, doc_work, paramedic = "врачом, только установившем смерть", "лечащим врачом", "фельдшером (акушеркой)"
    param_who_set = json.loads(params)
    if param_who_set["code"] == "1":
        only_doc_death = f"{op_bold_tag}<u>{only_doc_death}</u>{cl_bold_tag}"
    elif param_who_set["code"] == "2" or param_who_set["code"] == "7":
        doc_work = f"{op_bold_tag}<u>{doc_work}</u>{cl_bold_tag}"
    elif param_who_set["code"] == "3" or param_who_set["code"] == "8" or param_who_set["code"] == "9":
        paramedic = f"{op_bold_tag}<u>{paramedic}</u>{cl_bold_tag}"

    opinion = gen_opinion(['20. Причины смерти установлены:', only_doc_death, '1', doc_work, '2', paramedic, '3'])

    col_width = (
        49 * mm,
        58 * mm,
        6 * mm,
        27 * mm,
        6 * mm,
        40 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),
        ('GRID', (6, 0), (6, 0), 0.75, colors.black),
        ('GRID', (8, 0), (8, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.9 * mm))
    text.append(tbl)

    doc_anatomy, expert = "врачом-патологоанатомом", "судебно-медицинским экспертом"
    if param_who_set["code"] == "4":
        doc_anatomy = f"{op_bold_tag}<u>{doc_anatomy}</u>{cl_bold_tag}"
    elif param_who_set["code"] == "5" or param_who_set["code"] == "7":
        expert = f"{op_bold_tag}<u>{expert}</u>{cl_bold_tag}"
    opinion = gen_opinion([doc_anatomy, '4', expert, '5'])
    col_width = (
        50 * mm,
        6 * mm,
        50 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('RIGHTPADDING', (1, 0), (-1, -1), -2 * mm),
        ('GRID', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
        ('GRID', (5, 0), (5, 0), 0.75, colors.black),
        ('GRID', (7, 0), (7, 0), 0.75, colors.black),
        ('GRID', (9, 0), (9, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)
    return text


def doctor_fio(text, params, iss: Issledovaniya):
    doc_fio = params["Заполнил"]
    opinion = gen_opinion(['21. Я, врач (фельдшер, акушерка)', doc_fio])

    col_width = (
        50 * mm,
        140 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 0 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    doc_position = params["Должность"]
    opinion = gen_opinion(['должность', doc_position])
    col_width = (
        25 * mm,
        165 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    see_body, write_medical_dicument = (
        'осмотра трупа',
        ', записей в медицинской документации',
    )

    base_diagnos = json.loads(params["Основания для определения причины смерти"])
    if base_diagnos["code"] == "1":
        see_body = f"{op_bold_tag}<u>{see_body}</u>{cl_bold_tag}"
    elif base_diagnos["code"] == "2":
        write_medical_dicument = f"{op_bold_tag}<u>{write_medical_dicument}</u>{cl_bold_tag}"
    opinion = gen_opinion(['удостоверяю, что на основании:', see_body, '1', write_medical_dicument, '2'])

    col_width = (
        53 * mm,
        26 * mm,
        6 * mm,
        61 * mm,
        6 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('GRID', (2, 0), (2, 0), 0.75, colors.black),
        ('GRID', (4, 0), (4, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    see_patient, open_body = (
        'предшествующего наблюдения за больным(ой)',
        ', вскрытия',
    )
    if base_diagnos["code"] == "3" or base_diagnos["code"] == "5":
        see_patient = f"{op_bold_tag}<u>{see_patient}</u>{cl_bold_tag}"
    elif base_diagnos["code"] == "4":
        open_body = f"{op_bold_tag}<u>{open_body}</u>{cl_bold_tag}"
    opinion = gen_opinion([see_patient, '3', open_body, '4', ' мною установлены причины смерти'])

    col_width = (75 * mm, 6 * mm, 21 * mm, 6 * mm, 70 * mm)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('GRID', (1, 0), (1, 0), 0.75, colors.black),
        ('GRID', (3, 0), (3, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    return text


def hospital_manager_stamp(text, fio_manager):
    opinion = gen_opinion(['', '', '', '', fio_manager])
    col_width = (
        45 * mm,
        5 * mm,
        45 * mm,
        5 * mm,
        90 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('LINEBELOW', (0, 0), (0, 0), 0.75, colors.black),
        ('LINEBELOW', (2, 0), (2, 0), 0.75, colors.black),
        ('LINEBELOW', (4, 0), (4, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 3 * mm))
    text.append(tbl)

    opinion = gen_opinion(['печать', 'подпись', '(фамилия, имя, отчество (при наличии)'])
    col_width = (
        45 * mm,
        45 * mm,
        100 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 15 * mm),
        ('LEFTPADDING', (1, 0), (1, 0), 15 * mm),
        ('LEFTPADDING', (2, 0), (2, 0), 15 * mm),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 0.4 * mm))
    text.append(tbl)

    return text


def check_person_data(text, fio_check):
    date_value = "«___» ___________ 20 ___ г."
    opinion = gen_opinion([date_value, fio_check])
    col_width = (
        60 * mm,
        130 * mm,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('LINEBELOW', (1, 0), (1, 0), 0.75, colors.black),
    ]
    tbl = gen_table(opinion, col_width, tbl_style)
    text.append(Spacer(1, 3 * mm))
    text.append(tbl)
    return text
