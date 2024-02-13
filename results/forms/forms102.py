import pytils

from users.models import DoctorProfile
from utils.dates import normalize_date
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Indenter, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import directory.models as directory
from directions.models import ParaclinicResult, Issledovaniya
from appconf.manager import SettingManager
from results.prepare_data import text_to_bold, fields_result_only_title_fields, table_part_result
import simplejson as json


def form_01(direction, iss, fwb, doc, leftnone, user=None, **kwargs):
    # ПАТОЛОГО-АНАТОМИЧЕСКОЕ заключение
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "FreeSans"
    style.fontSize = 10
    style.alignment = TA_JUSTIFY

    style_ml = deepcopy(style)
    style_ml.leftIndent = 5 * mm
    style_ml.spaceAfter = 0.5 * mm

    styleBold = deepcopy(style)
    styleBold.fontName = "FreeSansBold"

    hospital_name = SettingManager.get("org_title")
    hospital_address = SettingManager.get("org_address")
    hospital_kod_ogrn = SettingManager.get("org_ogrn")

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    opinion = [
        [
            Paragraph(f'<font size=10>{hospital_name}<br/>Адрес: {hospital_address}<br/>ОГРН: {hospital_kod_ogrn} <br/> </font>', styleT),
            Paragraph('<font size=9 >Медицинская документация <br/> Учетная форма № 014/1-у<br/>Утверждена приказом Минздрава России<br/>от 24 марта 2016г. № 179н</font>', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [100 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (1, 0), (-1, -1), 35 * mm),
                ('LEFTPADDING', (0, 0), (0, -1), 15 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )

    fwb.append(tbl)
    fwb.append(Spacer(1, 5 * mm))

    history_num = ''
    if direction.parent and direction.parent.research.is_hospital:
        history_num = f"(cтационар-{str(direction.parent.napravleniye_id)})"

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 11.5
    styleCenterBold.leading = 15
    styleCenterBold.fontName = 'FreeSansBold'

    fwb.append(Paragraph(f'ПРОТОКОЛ № {direction.pk} {history_num} ', styleCenterBold))
    fwb.append(Paragraph('ПРИЖИЗНЕННОГО ПАТОЛОГО-АНАТОМИЧЕСКОГО<br/> ИССЛЕДОВАНИЯ БИОПСИЙНОГО (ОПЕРАЦИОННОГО) МАТЕРИАЛА', styleCenterBold))
    short_title = iss.research.short_title
    fwb.append(Paragraph(f'{short_title.upper()}', styleCenterBold))

    open_bold_tag = "<font face =\"FreeSansBold\">"
    close_tag_bold = "</font>"

    fwb.append(Spacer(1, 4 * mm))
    fwb.append(Paragraph(f'{open_bold_tag}1. Отделение, направившее биопсийный (операционный) материал:{close_tag_bold}{direction.doc.podrazdeleniye.title}', style_ml))
    fwb.append(Paragraph(f'{open_bold_tag}2. Фамилия, имя, отчество (при наличии) пациента:{close_tag_bold} {direction.client.individual.fio()}', style_ml))
    sex = direction.client.individual.sex
    if sex == "м":
        sex = f'{sex}-1'
    else:
        sex = f'{sex}-2'
    space_symbol = '&nbsp;'
    fwb.append(Paragraph(f'{open_bold_tag}3. Пол:{close_tag_bold} {sex}, {space_symbol * 5} {open_bold_tag}4. Дата рождения:{close_tag_bold} {direction.client.individual.bd()}', style_ml))
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
    fwb.append(Paragraph(f'{open_bold_tag}5. Полис ОМС:{close_tag_bold}{polis_num}-{polis_issue} {space_symbol * 4} {open_bold_tag}6. СНИЛС:{close_tag_bold} {snils}', style_ml))
    address = ind_data['main_address']
    fwb.append(Paragraph(f'{open_bold_tag}7. Место регистрации:{close_tag_bold} {address}', style_ml))
    fwb.append(Paragraph(f'{open_bold_tag}8. Местность:{close_tag_bold} городская — 1, сельская — 2.', style_ml))

    for group in directory.ParaclinicInputGroups.objects.filter(research=iss.research).order_by("order"):
        results = ParaclinicResult.objects.filter(issledovaniye=iss, field__group=group).order_by("field__order")
        group_title = False
        if results.exists():
            fwb.append(Spacer(1, 1 * mm))
            if group.show_title and group.show_title != "":
                fwb.append(Paragraph(group.title.replace('<', '&lt;').replace('>', '&gt;'), styleBold))
                fwb.append(Spacer(1, 0.25 * mm))
                group_title = True
            for r in results:
                field_type = r.get_field_type()
                if field_type == 15:
                    continue
                else:
                    v = r.value.replace('<', '&lt;').replace('>', '&gt;').replace("\n", "<br/>")
                    v = v.replace('&lt;sub&gt;', '<sub>')
                    v = v.replace('&lt;/sub&gt;', '</sub>')
                    v = v.replace('&lt;sup&gt;', '<sup>')
                    v = v.replace('&lt;/sup&gt;', '</sup>')
                    v = text_to_bold(v)
                    if field_type == 16:
                        continue
                    if field_type == 17:
                        continue
                    if field_type == 1:
                        v = normalize_date(v)
                    if field_type in [11, 13]:
                        v = '<font face="FreeSans" size="8">{}</font>'.format(v.replace("&lt;br/&gt;", " "))
                    if r.field.get_title(force_type=field_type) != "":
                        fwb.append(
                            Paragraph(
                                "<font face=\"FreeSansBold\">{}:</font>{}".format(r.field.get_title(force_type=field_type).replace('<', '&lt;').replace('>', '&gt;'), v),
                                style_ml if group_title else style,
                            )
                        )
                    else:
                        fwb.append(Paragraph(v, style))

    return fwb


def form_02(direction, iss: Issledovaniya, fwb, doc, leftnone, user=None, **kwargs):
    # ПАТОЛОГО-АНАТОМИЧЕСКОЕ заключение
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "FreeSans"
    style.fontSize = 10
    style.alignment = TA_JUSTIFY

    style_ml = deepcopy(style)
    style_ml.leftIndent = 5 * mm
    style_ml.spaceAfter = 0.5 * mm

    styleBold = deepcopy(style)
    styleBold.fontName = "FreeSansBold"

    hospital_name = SettingManager.get("org_title")
    hospital_address = SettingManager.get("org_address")
    hospital_kod_ogrn = SettingManager.get("org_ogrn")

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    opinion = [
        [
            Paragraph(f'<font size=10>{hospital_name}<br/>Адрес: {hospital_address}<br/>ОГРН: {hospital_kod_ogrn} <br/> </font>', styleT),
            Paragraph('<font size=9 >Медицинская документация <br/> Учетная форма № 014/1-у<br/>Утверждена приказом Минздрава России<br/>от 24 марта 2016г. № 179н</font>', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [100 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (1, 0), (-1, -1), 35 * mm),
                ('LEFTPADDING', (0, 0), (0, -1), 15 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )

    fwb.append(tbl)
    fwb.append(Spacer(1, 5 * mm))

    history_num = ''
    if direction.parent and direction.parent.research.is_hospital:
        history_num = f"(cтационар-{str(direction.parent.napravleniye_id)})"

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 11.5
    styleCenterBold.leading = 15
    styleCenterBold.fontName = 'FreeSansBold'

    fwb.append(Paragraph(f'ПРОТОКОЛ № {direction.pk} {history_num} ', styleCenterBold))
    fwb.append(Paragraph('ПРИЖИЗНЕННОГО ПАТОЛОГО-АНАТОМИЧЕСКОГО<br/> ИССЛЕДОВАНИЯ БИОПСИЙНОГО (ОПЕРАЦИОННОГО) МАТЕРИАЛА', styleCenterBold))
    short_title = iss.research.short_title
    fwb.append(Paragraph(f'{short_title.upper()}', styleCenterBold))

    open_bold_tag = "<font face =\"FreeSansBold\">"
    close_tag_bold = "</font>"

    title_fields = [
        "Отделение направившее",
        "ФИО пациента",
        "Пол",
        "Дата рождения",
        "Полис ОМС",
        "СНИЛС",
        "Место регистрации",
        "Местность",
        "Диагноз по направлению",
        "Код по МКБ из направления",
        "Дата забора",
        "Время забора",
        "Материал в 10% растворе",
        "Загрязнен",
        "Дата поступления",
        "Время поступления",
        "Сохранность упаковки",
        "Дата регистрации",
        "Время регистрации",
        "Регистрационный номер",
        "Медицинские услуги",
        "Категория сложности",
        "Дата вырезки",
        "Время вырезки",
        "В проводку взято",
        "Окраски",
        "Макроскопическое описание",
        "Микроскопическое описание",
        "Заключение",
        "Код по МКБ",
        "Комментарии к заключению и рекомендации",
        "Врач-консультант",
    ]
    result = fields_result_only_title_fields(iss, title_fields, False)
    data = {}
    for i in result:
        data[i["title"]] = i["value"]

    if not data.get("Отделение направившее"):
        data["Отделение направившее"] = "не указано"

    if not data.get("Макроскопическое описание"):
        data["Макроскопическое описание"] = ""

    if not data.get("Микроскопическое описание"):
        data["Микроскопическое описание"] = ""

    if not data.get("Заключение"):
        data["Заключение"] = ""

    if not data.get("Комментарии к заключению и рекомендации"):
        data["Комментарии к заключению и рекомендации"] = ""

    if not data.get("Врач-консультант"):
        data["Врач-консультант"] = ""

    fwb.append(Spacer(1, 4 * mm))
    fwb.append(Paragraph(f'{open_bold_tag}1. Отделение, направившее биопсийный (операционный) материал:{close_tag_bold}{data["Отделение направившее"]}', style_ml))
    fwb.append(Paragraph(f'{open_bold_tag}2. Фамилия, имя, отчество (при наличии) пациента:{close_tag_bold} {data["ФИО пациента"]}', style_ml))
    if data["Пол"] == "м":
        sex = f'{data["Пол"]}-1'
    else:
        sex = f'{data["Пол"]}-2'
    space_symbol = '&nbsp;'
    fwb.append(Paragraph(f'{open_bold_tag}3. Пол:{close_tag_bold} {sex}, {space_symbol * 5} {open_bold_tag}4. Дата рождения:{close_tag_bold} {data["Дата рождения"]}', style_ml))
    if not data.get("Полис ОМС"):
        data["Полис ОМС"] = ""
    if not data.get("СНИЛС"):
        data["СНИЛС"] = ""
    fwb.append(Paragraph(f'{open_bold_tag}5. Полис ОМС:{close_tag_bold}{data["Полис ОМС"]} {space_symbol * 4} {open_bold_tag}6. СНИЛС:{close_tag_bold} {data["СНИЛС"]}', style_ml))
    data_address = {}
    try:
        data_address = json.loads(data["Место регистрации"])
    except:
        data_address["address"] = ""
    fwb.append(Paragraph(f'{open_bold_tag}7. Место регистрации:{close_tag_bold} {data_address["address"]}', style_ml))
    try:
        place = json.loads(data["Местность"])
    except:
        place = {"code": "1"}
    if place["code"] == "1":
        place_fact = "городская — 1"
    else:
        place_fact = "сельская — 2"
    fwb.append(Paragraph(f'{open_bold_tag}8. Местность:{close_tag_bold} {place_fact}', style_ml))
    fwb.append(Paragraph(f'{open_bold_tag}9. Диагноз заболевания (состояния) по данным направления:{close_tag_bold} {data["Диагноз по направлению"]}', style_ml))
    direction_mkb = json.loads(data["Код по МКБ из направления"])
    fwb.append(Paragraph(f'{open_bold_tag}10. Код по МКБ:{close_tag_bold} {direction_mkb["code"]}', style_ml))
    fwb.append(
        Paragraph(
            f'{open_bold_tag}11. Дата забора материала по данным направления:{close_tag_bold} {space_symbol * 2}{normalize_date(data["Дата забора"])} {space_symbol * 4} '
            f'{open_bold_tag}время{close_tag_bold} {data["Время забора"]}',
            style_ml,
        )
    )
    fwb.append(
        Paragraph(
            f'{open_bold_tag}12. Материал доставлен в 10%-ный раствор нейтрального формалина:{close_tag_bold}{space_symbol * 2}{data.get("Материал в 10% растворе", "Да")}{space_symbol * 4}'
            f'{open_bold_tag}загрязнен{close_tag_bold} {data.get("Загрязнен", "Нет")}',
            style_ml,
        )
    )
    fwb.append(
        Paragraph(
            f'{open_bold_tag}13. Дата поступления биопсийного (операционного) материала:{close_tag_bold} {space_symbol * 2}{normalize_date(data["Дата поступления"])} {space_symbol * 4}'
            f'{open_bold_tag}время{close_tag_bold} {data["Время поступления"]}',
            style_ml,
        )
    )
    fwb.append(Paragraph(f'{open_bold_tag}14. Отметка о сохранности упаковки:{close_tag_bold} {space_symbol * 2}{data.get("Сохранность упаковки", "Да")}', style_ml))
    fwb.append(
        Paragraph(
            f'{open_bold_tag}15. Дата регистрации биопсийного (операционного) материала:{close_tag_bold} {space_symbol * 2}{normalize_date(data["Дата регистрации"])} {space_symbol * 4}'
            f'{open_bold_tag}время{close_tag_bold} {data["Время регистрации"]}',
            style_ml,
        )
    )
    fwb.append(Paragraph(f'{open_bold_tag}16. Регистрационный номер:{close_tag_bold} {space_symbol * 2}{data["Регистрационный номер"]}', style_ml))
    med_service = json.loads(data["Медицинские услуги"])
    fwb.append(Paragraph(f'{open_bold_tag}17. Медицинские услуги:{close_tag_bold} {space_symbol * 2}{med_service["code"]} {med_service["title"]}', style_ml))
    category = json.loads(data["Категория сложности"])
    fwb.append(Paragraph(f'{open_bold_tag}18. Категория сложности:{close_tag_bold} {space_symbol * 2}{category["title"]}', style_ml))
    fwb.append(
        Paragraph(
            f'{open_bold_tag}19. Вырезка проводилась:{close_tag_bold} {space_symbol * 2}{normalize_date(data["Дата вырезки"])} {space_symbol * 4} {open_bold_tag}время{close_tag_bold} '
            f'{data["Время вырезки"]} {open_bold_tag}20. В проводку взято:{close_tag_bold} {space_symbol * 2} {data.get("В проводку взято", "0")} объектов',
            style_ml,
        )
    )

    table_results = table_part_result(data["Окраски"])
    fwb.append(Paragraph(f'{open_bold_tag}21. Назначенные окраски (реакции, определения):{close_tag_bold}', style_ml))
    fwb.append(Indenter(left=5 * mm))
    fwb.append(table_results)
    fwb.append(Indenter(left=-5 * mm))
    fwb.append(Paragraph(f'{open_bold_tag}22. Макроскопическое описание:{close_tag_bold}', style_ml))
    fwb.append(Paragraph(f'{data["Макроскопическое описание"]}', style_ml))
    fwb.append(Paragraph(f'{open_bold_tag}23. Микроскопическое описание:{close_tag_bold}', style_ml))
    fwb.append(Paragraph(f'{data["Микроскопическое описание"]}', style_ml))
    result_mkb = json.loads(data["Код по МКБ"])
    fwb.append(Paragraph(f'{open_bold_tag}24. Заключение:{close_tag_bold} {space_symbol * 110} {open_bold_tag}25. Код по МКБ:{close_tag_bold} {result_mkb["code"]}', style_ml))
    fwb.append(Paragraph(f'{data["Заключение"]}', style_ml))
    fwb.append(Paragraph(f'{open_bold_tag}26. Комментарии к заключению и рекомендации:{close_tag_bold}', style_ml))
    fwb.append(Paragraph(f'{data["Комментарии к заключению и рекомендации"]}', style_ml))
    fwb.append(Paragraph(f'{open_bold_tag}27. Прижизненное патолого-анатомическое исследование выполнили:{close_tag_bold}', style_ml))
    fwb.append(Spacer(1, 3 * mm))

    has_any_signature = kwargs.get('has_any_signature', False)

    tbl = gen_table("Врач-патологоанатом", iss.doc_confirmation_fio, styleT, iss.doc_confirmation, has_any_signature=has_any_signature)
    fwb.append(tbl)
    fwb.append(Spacer(1, 7 * mm))
    tbl = gen_table("Врач-специалист, <br/>осуществляющий консультирование", data["Врач-консультант"], styleT, has_any_signature=has_any_signature)
    fwb.append(tbl)
    fwb.append(Spacer(1, 3 * mm))
    date_str = pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=iss.time_confirmation)
    fwb.append(Paragraph(f'{open_bold_tag}28. Дата проведения прижизненного патолого-анатомического исследования:{close_tag_bold} {date_str} г.', style_ml))

    return fwb


def gen_table(title, param, styleT, doctor: DoctorProfile = None, has_any_signature=False):
    img = ""
    if doctor and not has_any_signature:
        file_jpg = doctor.get_signature_stamp_pdf()
        if file_jpg:
            img = Image(
                file_jpg,
                34 * mm,
                34 * mm,
            )

    opinion = [
        [
            Paragraph(f'{title}', styleT),
            Paragraph('', styleT),
            Paragraph(f'{param}', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('', styleT),
            img,
        ],
        [
            Paragraph('', styleT),
            Paragraph('', styleT),
            Paragraph('<font size=8>(фамилия, инициалы)</font>', styleT),
            Paragraph('', styleT),
            Paragraph('м.п.', styleT),
            Paragraph('', styleT),
            Paragraph('<font size=8>(подпись)</font>', styleT),
        ],
    ]
    gentbl = Table(opinion, colWidths=(62 * mm, 5 * mm, 58 * mm, 5 * mm, 15 * mm, 5 * mm, 37 * mm))
    gentbl.setStyle(
        TableStyle(
            [
                ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
                ('LINEBELOW', (2, 0), (2, 0), 0.75, colors.black),
                ('LINEBELOW', (6, 0), (6, 0), 0.75, colors.black),
                ('BOTTOMPADDING', (-1, 0), (-1, 0), -12 * mm),
                ('LEFTPADDING', (-1, 0), (-1, 0), -4 * mm),
            ]
        )
    )
    return gentbl
