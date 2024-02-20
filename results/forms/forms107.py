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
from directions.models import Issledovaniya
from ..prepare_data import fields_result_only_title_fields
from hospitals.models import Hospitals

pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
pdfmetrics.registerFont(TTFont('digit8', os.path.join(FONTS_FOLDER, 'digit88table.ttf')))
styleSheet = getSampleStyleSheet()
style = styleSheet["Normal"]
style.fontName = "PTAstraSerifReg"
style.fontSize = 9
style.alignment = TA_JUSTIFY

styleCentre = deepcopy(style)
styleCentre.alignment = TA_CENTER
styleCentre.fontSize = 13
styleCentre.leading = 5 * mm

styleBold = deepcopy(style)
styleBold.fontName = "PTAstraSerifBold"

styleCentreBold = deepcopy(styleCentre)
styleCentreBold.alignment = TA_CENTER
styleCentreBold.fontName = "PTAstraSerifBold"


hospital_name = SettingManager.get("org_title")
hospital_address = SettingManager.get("org_address")
hospital_kod_ogrn = SettingManager.get("org_ogrn")

styleT = deepcopy(style)
styleT.alignment = TA_LEFT
styleT.fontSize = 11
styleT.leading = 4 * mm

styleOrg = deepcopy(styleT)
styleOrg.fontSize = 10

styleOrgCentre = deepcopy(styleOrg)
styleOrgCentre.alignment = TA_CENTER

styleOrgBold = deepcopy(styleOrg)
styleOrgBold.fontName = "PTAstraSerifBold"
styleOrgBold.leading = 1.5 * mm
styleOrgBold.fontSize = 13

styleText = deepcopy(style)
styleText.fontSize = 12


op_bold_tag = '<font face="PTAstraSerifBold">'
cl_bold_tag = '</font>'

op_boxed_tag = '<font face="digit8" size=20.5>'
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
    # МСЭ 088/у
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

    hospital_obj: Hospitals = user.doctorprofile.get_hospital()
    data['org'] = {
        "full_title": hospital_obj.title,
        "org_address": hospital_obj.address,
        "org_license": hospital_obj.license_data,
        "org_okpo": hospital_obj.okpo,
        "org_ogrn": hospital_obj.ogrn,
    }
    opinion = [
        [
            Paragraph('', styleT),
            Paragraph('<font size=9 >Медицинская документация<br/>Форма N 088/у</font>', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [100 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (1, 0), (-1, -1), 55 * mm),
                ('LEFTPADDING', (0, 0), (0, -1), 15 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )

    fwb.append(tbl)
    fwb.append(Spacer(1, 5 * mm))

    opinion = gen_opinion([data["org"]["full_title"]], styleCentre)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LINEBELOW', (0, 0), (-1, -1), 0.75, colors.black),
    ]
    col_width = (180 * mm,)
    tbl = gen_table(opinion, col_width, tbl_style)
    fwb.append(Spacer(1, 0.2 * mm))
    fwb.append(tbl)
    fwb.append(Paragraph("(наименование медицинской организации)", styleOrgCentre))

    fwb.append(Spacer(1, 2 * mm))
    opinion = gen_opinion([data["org"]["org_address"]], styleCentre)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LINEBELOW', (0, 0), (-1, -1), 0.75, colors.black),
    ]
    col_width = (180 * mm,)
    tbl = gen_table(opinion, col_width, tbl_style)
    fwb.append(Spacer(1, 0.2 * mm))
    fwb.append(tbl)
    fwb.append(Paragraph("(адрес медицинской организации)", styleOrgCentre))

    fwb.append(Spacer(1, 2 * mm))
    opinion = gen_opinion([data["org"]["org_ogrn"]], styleCentre)
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 5 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 0 * mm),
        ('LINEBELOW', (0, 0), (-1, -1), 0.75, colors.black),
    ]
    col_width = (80 * mm,)
    tbl = gen_table_centre(opinion, col_width, tbl_style)
    fwb.append(Spacer(1, 0.2 * mm))
    fwb.append(tbl)
    fwb.append(Paragraph("(ОГРН медицинской организации)", styleOrgCentre))

    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("НАПРАВЛЕНИЕ НА МЕДИКО-СОЦИАЛЬНУЮ ЭКСПЕРТИЗУ МЕДИЦИНСКОЙ ОРГАНИЗАЦИЕЙ", styleCentreBold))
    fwb.append(
        Paragraph(
            "1. Номер и дата протокола врачебной комиссии медицинской организации, содержащего решение о направлении гражданина на медико-социальную экспертизу: No 1112/s от 18.10.2021",
            styleText,
        )
    )
    fwb.append(Spacer(1, 2 * mm))
    fwb.append(
        Paragraph(
            "2. Гражданин по состоянию здоровья не может явиться в бюро (главное бюро, Федеральное бюро) медико- социальной экспертизы: медико-социальную экспертизу необходимо проводить на дому",  # noqa: E501
            styleText,
        )
    )
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(
        Paragraph(
            f"3. Гражданин нуждается в оказании паллиативной медицинской помощи {op_boxed_tag}{space_symbol}{cl_boxed_tag} (при нуждаемости в оказании паллиативной медицинской помощи)",
            styleText,
        )
    )
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(Paragraph("4. Дата выдачи гражданину направления на медико-социальную экспертизу медицинской организацией: 18.10.2021", styleText))
    fwb.append(Spacer(1, 2 * mm))
    fwb.append(Paragraph("5. Цель направления гражданина на медико-социальную экспертизу (нужное отметить):", styleText))

    # Таблица Цели

    opinion = gen_opinion_2(
        [
            [
                f"5.1. {op_boxed_tag}X{cl_boxed_tag} установление группы инвалидности",
                f'5.2. {op_boxed_tag}{space_symbol}{cl_boxed_tag} установление категории "ребенок-инвалид"',
                f'5.3. {op_boxed_tag}{space_symbol}{cl_boxed_tag} установление причины инвалидности',
            ],
            [
                f"5.4. {op_boxed_tag}X{cl_boxed_tag} установление времени наступления инвалидности",
                f'5.5. {op_boxed_tag}{space_symbol}{cl_boxed_tag} установление срока инвалидности',
                f'5.6. {op_boxed_tag}{space_symbol}{cl_boxed_tag}определение степени утраты профессиональной трудоспособности в процентах',
            ],
            [
                f"5.7. {op_boxed_tag}V{cl_boxed_tag} определение стойкой утраты трудоспособности сотрудника органа внутренних дел Российской Федерациии",
                f'5.8. {op_boxed_tag}{space_symbol}{cl_boxed_tag} определение нуждаемости по состоянию здоровья в постоянном постороннем уходе (помощи, надзоре) отца, матери, жены, родного брата, родной сестры, дедушки, бабушки или усыновителя гражданина, призываемого на военную службу (военнослужащего, проходящего военную службу по контракту)',  # noqa: E501
                f'5.9. {op_boxed_tag}{space_symbol}{cl_boxed_tag} определение причины смерти инвалида, а также лица, пострадавшего в результате несчастного случая на производстве, профессионального заболевания, катастрофы на Чернобыльской атомной электростанции (далее - АЭС) и других радиационных и техногенных катастроф либо в результате ранения, контузии, увечья или заболевания, полученных в период прохождения военной службы, в случаях, когда законодательством Российской Федерации предусматривается предоставление семье умершего мер социальной поддержки',  # noqa: E501
            ],
            [
                f"5.10. {op_boxed_tag}V{cl_boxed_tag} разработка индивидуальной программы реабилитации или абилитации инвалида (ребенка-инвалида)",
                f'5.11. {op_boxed_tag}{space_symbol}{cl_boxed_tag} разработка программы реабилитации лица, пострадавшего в результате несчастного случая на производстве и профессионального заболевания',  # noqa: E501
                f'5.12. {op_boxed_tag}{space_symbol}{cl_boxed_tag} выдача дубликата справки, подтверждающей факт установления инвалидности, степени утраты профессиональной трудоспособности в процентах',  # noqa: E501
            ],
            [
                f"5.13. {op_boxed_tag}V{cl_boxed_tag} выдача новой справки, подтверждающей факт установления инвалидности, в случае изменения фамилии, имени, отчества (при наличии), даты рождения гражданина",  # noqa: E501
                f'5.14. {op_boxed_tag}{space_symbol}{cl_boxed_tag} иные цели, установленные законодательством Российской Федерации (указать):',
                '',
            ],
        ],
        styleT,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0.7 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -3 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5 * mm),
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('SPAN', (1, -1), (-1, -1)),
    ]
    col_width = (
        62 * mm,
        62 * mm,
        62 * mm,
    )
    tbl = gen_table(opinion, col_width, tbl_style)
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(tbl)

    fwb.append(PageBreak())
    fwb.append(Paragraph("Раздел I. Данные о гражданине", styleCentreBold))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("6. Фамилия, имя, отчество (при наличии):", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("7. Дата рождения (день, месяц, год): ", styleText))
    fwb.append(Paragraph("возраст (число полных лет, для ребенка в возрасте до 1 года - число полных месяцев):", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("8. Пол (нужное отметить):", styleText))

    opinion = gen_opinion_2(
        [
            [
                f"8.1. {op_boxed_tag}X{cl_boxed_tag} мужской",
                f'8.2. {op_boxed_tag}{space_symbol}{cl_boxed_tag} женский',
            ],
        ],
        styleT,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0.7 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -3 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5 * mm),
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('SPAN', (1, -1), (-1, -1)),
    ]
    col_width = (93 * mm, 93 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(tbl)
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("9. Гражданство (нужное отметить):", styleText))
    opinion = gen_opinion_2(
        [
            [
                f"9.1. {op_boxed_tag}X{cl_boxed_tag} гражданин Российской Федерации",
                f'9.2. {op_boxed_tag}{space_symbol}{cl_boxed_tag} гражданин иностранного государства, находящийся на территории Российской Федерации',
                f'9.3. {op_boxed_tag}{space_symbol}{cl_boxed_tag} лицо без гражданства, находящееся на территории Российской Федерации',
            ],
        ],
        styleT,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0.7 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -3 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5 * mm),
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('SPAN', (1, -1), (-1, -1)),
    ]
    col_width = (
        62 * mm,
        62 * mm,
        62 * mm,
    )
    tbl = gen_table(opinion, col_width, tbl_style)
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(tbl)

    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("10. Отношение к воинской обязанности (нужное отметить):", styleText))
    opinion = gen_opinion_2(
        [
            [
                f"10.1. {op_boxed_tag}X{cl_boxed_tag} гражданин, состоящий на воинском учете",
                f'10.2. {op_boxed_tag}{space_symbol}{cl_boxed_tag} гражданин, не состоящий на воинском учете, но обязанный состоять на воинском учете',
            ],
            [
                f"10.3. {op_boxed_tag}X{cl_boxed_tag} гражданин, поступающий на воинской учет",
                f'10.4. {op_boxed_tag}{space_symbol}{cl_boxed_tag} гражданин, не состоящий на воинском учете',
            ],
        ],
        styleT,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0.7 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -3 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5 * mm),
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('SPAN', (1, -1), (-1, -1)),
    ]
    col_width = (93 * mm, 93 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(tbl)

    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(
        Paragraph(
            "11. Адрес места жительства (при отсутствии места жительства указывается адрес пребывания, фактического проживания на территории Российской Федерации, место нахождения пенсионного дела инвалида, выехавшего на постоянное жительство за пределы территории Российской Федерации):",  # noqa: E501
            styleText,
        )
    )
    fwb.append(Paragraph("11.1. государство: Страна Российская Федерация", styleText))
    fwb.append(Paragraph("11.2. почтовый индекс: 664007", styleText))
    fwb.append(Paragraph("11.3. субъект Российской Федерации: Область Иркутская:", styleText))
    fwb.append(Paragraph("1.4. район:", styleText))
    fwb.append(Paragraph("11.5. наименование населенного пункта: Город Иркутск", styleText))
    fwb.append(Paragraph("11.6. улица: Улица Байкальская", styleText))
    fwb.append(Paragraph("11.7. дом (корпус, строение): 213", styleText))
    fwb.append(Paragraph("11.8. квартира: 7", styleText))

    fwb.append(Spacer(1, -1 * mm))
    fwb.append(
        Paragraph(f"12. Лицо без определенного места жительства {op_boxed_tag}{space_symbol}{cl_boxed_tag} (в случае если гражданин не имеет определенного места жительства)", styleText)
    )
    fwb.append(Spacer(1, 4.5 * mm))
    fwb.append(Paragraph("13. Гражданин находится (нужное отметить и указать):", styleText))
    opinion = gen_opinion_2(
        [
            [
                f"13.1. {op_boxed_tag}X{cl_boxed_tag} в медицинской организации, оказывающей медицинскую помощь в стационарных условиях",
                f'13.1.1. {op_boxed_tag}{space_symbol}{cl_boxed_tag} адрес медицинской организации:',
                f'13.1.2. {op_boxed_tag}{space_symbol}{cl_boxed_tag} ОГРН медицинской организации',
            ],
            [
                f"13.2. {op_boxed_tag}X{cl_boxed_tag}  организации социального обслуживания, оказывающей социальные услуги в стационарной форме социального обслуживания",
                f'13.2.1 {op_boxed_tag}{space_symbol}{cl_boxed_tag} адрес организации социального обслуживания:',
                f'13.2.2 {op_boxed_tag}{space_symbol}{cl_boxed_tag} ОГРН организации социального обслуживания:',
            ],
            [
                f"13.3. {op_boxed_tag}X{cl_boxed_tag} в исправительном учреждении",
                f'13.3.1 {op_boxed_tag}{space_symbol}{cl_boxed_tag} адрес исправительного учреждения:',
                f'13.3.2 {op_boxed_tag}{space_symbol}{cl_boxed_tag} ОГРН исправительного учреждения:',
            ],
            [
                f"13.4. {op_boxed_tag}X{cl_boxed_tag} Иная организация",
                f'13.4.1 {op_boxed_tag}{space_symbol}{cl_boxed_tag} адрес организации:',
                f'13.4.2 {op_boxed_tag}{space_symbol}{cl_boxed_tag} ОГРН организации:',
            ],
            [
                f"13.5. {op_boxed_tag}X{cl_boxed_tag} по месту жительства (по месту пребывания, фактического проживания на территории Российской Федерации)",
                '',
                '',
            ],
        ],
        styleT,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0.7 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -3 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5 * mm),
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('SPAN', (0, -1), (-1, -1)),
    ]
    col_width = (62 * mm, 62 * mm, 62 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(tbl)
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("14. Контактная информация:", styleText))
    fwb.append(Paragraph("14.1. номера телефонов: 79027604013", styleText))
    fwb.append(Paragraph("14.2. адрес электронной почты (при наличии): Lenta-irk@mail.ru", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("15. Страховой номер индивидуального лицевого счета (СНИЛС): 056-747-396 03", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("16. Документ, удостоверяющий личность", styleText))
    fwb.append(Paragraph("16.1. наименование: Паспорт гражданина РФ (России)", styleText))
    fwb.append(Paragraph("16.2. серия 2509, номер 311255", styleText))
    fwb.append(Paragraph("16.3. кем выдан: отделом в УФМС России по Иркутской области в гор. Усолье-Сибирское и Усольском р-не", styleText))
    fwb.append(Paragraph("16.4. дата выдачи (день, месяц, год): 25.01.2010", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("17. Сведения о законном (уполномоченном) представителе гражданина, направляемого на медико- социальную экспертизу:", styleText))
    fwb.append(Paragraph("17.1. Фамилия, имя, отчество (при наличии):", styleText))
    fwb.append(Paragraph("17.2. документ, удостоверяющий полномочия законного (уполномоченного) представителя:", styleText))
    fwb.append(Paragraph("17.2.1. наименование:", styleText))
    fwb.append(Paragraph("17.2.2. серия , номер", styleText))
    fwb.append(Paragraph("17.2.3. кем выдан:", styleText))
    fwb.append(Paragraph("17.3. документ, удостоверяющий личность:", styleText))
    fwb.append(Paragraph("17.3.1. наименование:", styleText))
    fwb.append(Paragraph("17.3.2. серия , номер", styleText))
    fwb.append(Paragraph("17.3.3. кем выдан:", styleText))
    fwb.append(Paragraph("17.4. контактная информация:", styleText))
    fwb.append(Paragraph("17.4.1. номера телефонов:", styleText))
    fwb.append(Paragraph("17.4.2. адрес электронной почты (при наличии):", styleText))
    fwb.append(Paragraph("17.5. страховой номер индивидуального лицевого счета (СНИЛС):", styleText))
    fwb.append(Paragraph("17.6. сведения об организации в случае возложения опеки (попечительства) на юридическое лицо:", styleText))
    fwb.append(Paragraph("17.6.1. наименование:", styleText))
    fwb.append(Paragraph("17.6.2. адрес:", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("18. Гражданин направляется на медико-социальную экспертизу (нужное отметить):", styleText))
    opinion = gen_opinion_2(
        [
            [
                f"18.1. {op_boxed_tag}X{cl_boxed_tag} первично",
                f"18.2. {op_boxed_tag}{space_symbol}{cl_boxed_tag} повторно",
            ],
        ],
        styleT,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0.7 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -3 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5 * mm),
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
    ]
    col_width = (93 * mm, 93 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(tbl)
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("19. Сведения о результатах предыдущей медико-социальной экспертизы (в случае направления на медико- социальную экспертизу повторно):", styleText))
    fwb.append(Paragraph("19.1. наличие инвалидности на момент направления на медико-социальную экспертизу (нужное отметить):", styleText))
    opinion = gen_opinion_2(
        [
            [
                f"19.1.1. {op_boxed_tag}X{cl_boxed_tag} первая группа",
                f"19.1.2. {op_boxed_tag}{space_symbol}{cl_boxed_tag} вторая группа",
                f"19.1.3. {op_boxed_tag}{space_symbol}{cl_boxed_tag} третья группа",
                f"19.1.4. {op_boxed_tag}{space_symbol}{cl_boxed_tag} категория ребенок-инвалид",
            ],
        ],
        styleT,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0.7 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -3 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5 * mm),
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
    ]
    col_width = (46.5 * mm, 46.5 * mm, 46.5 * mm, 46.5 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(tbl)
    fwb.append(Paragraph("19.2. дата, до которой установлена инвалидность (день, месяц, год):", styleText))
    fwb.append(Paragraph("19.3. период, в течение которого гражданин находился на инвалидности на момент направления на медико-социальную экспертизу (нужное отметить):", styleText))
    opinion = gen_opinion_2(
        [
            [
                f"19.3.1. {op_boxed_tag}X{cl_boxed_tag} один год",
                f"19.3.2. {op_boxed_tag}{space_symbol}{cl_boxed_tag} два года",
                f"19.3.3. {op_boxed_tag}{space_symbol}{cl_boxed_tag} три года",
                f"19.3.4. {op_boxed_tag}{space_symbol}{cl_boxed_tag} четыре и более лет",
            ],
        ],
        styleT,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0.7 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -3 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5 * mm),
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
    ]
    col_width = (46.5 * mm, 46.5 * mm, 46.5 * mm, 46.5 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(tbl)
    fwb.append(Paragraph("19.4. формулировка причины инвалидности, имеющейся на момент направления на медико-социальную экспертизу (нужное отметить):", styleText))
    opinion = gen_opinion_2(
        [
            [
                f"19.4.1. {op_boxed_tag}X{cl_boxed_tag} общее заболевание",
                f"19.4.2. {op_boxed_tag}{space_symbol}{cl_boxed_tag} инвалидность с детства",
                f"19.4.3. {op_boxed_tag}{space_symbol}{cl_boxed_tag} профессиональное заболевание",
                f"19.4.4. {op_boxed_tag}{space_symbol}{cl_boxed_tag} трудовое увечье",
            ],
            [
                f"19.4.5. {op_boxed_tag}X{cl_boxed_tag} военная травма",
                f"19.4.6. {op_boxed_tag}{space_symbol}{cl_boxed_tag} заболевание получено в период военной службы",
                f"19.4.7. {op_boxed_tag}{space_symbol}{cl_boxed_tag} заболевание, полученное при исполнении иных обязанностей военной службы (служебных обязанностей), связано с катастрофой на Чернобыльской АЭС",  # noqa: E501
                f"19.4.8. {op_boxed_tag}{space_symbol}{cl_boxed_tag} заболевание радиационно обусловленное получено при исполнении обязанностей военной службы (служебных обязанностей) в связи с катастрофой на Чернобыльской АЭС",  # noqa: E501
            ],
            [
                f"19.4.9. {op_boxed_tag}X{cl_boxed_tag} заболевание связано с катастрофой на Чернобыльской АЭС",
                f'19.4.10. {op_boxed_tag}{space_symbol}{cl_boxed_tag} заболевание связано с аварией на производственном объединении "Маяк"',
                f'19.4.11. {op_boxed_tag}{space_symbol}{cl_boxed_tag} заболевание, полученное при исполнении иных обязанностей военной службы (служебных обязанностей), связано с аварией на производственном объединении "Маяк"',  # noqa: E501
                f"19.4.12. {op_boxed_tag}{space_symbol}{cl_boxed_tag} заболевание связано с последствиями радиационных воздействий",
            ],
            [
                f"19.4.13. {op_boxed_tag}X{cl_boxed_tag} аболевание радиационно обусловленное получено при исполнении обязанностей военной службы (служебных обязанностей) в связи с непосредственным участием в действиях подразделений особого риска",  # noqa: E501
                f"19.4.14. {op_boxed_tag}{space_symbol}{cl_boxed_tag} инвалидность с детства вследствие ранения (контузии, увечья), связанная с боевыми действиями в период Великой Отечественной войны 1941-1945 годов",  # noqa: E501
                f"19.4.15. {op_boxed_tag}{space_symbol}{cl_boxed_tag} заболевание (ранение, контузия, увечье), полученное лицом, обслуживавшим действующие воинские части Вооруженных Сил СССР и Вооруженных Сил Российской Федерации, находившиеся на территориях других государств в период ведения в этих государствах боевых действий",  # noqa: E501
                f"19.4.16. {op_boxed_tag}{space_symbol}{cl_boxed_tag} иные причины, установленные законодательством Российской Федерации (указать):",
            ],
            [
                f"19.4.17. {op_boxed_tag}X{cl_boxed_tag} формулировки причин инвалидности, установленные в соответствии с законодательством, действовавшим на момент установления инвалидности (указать):",  # noqa: E501
                "",
                "",
                "",
            ],
        ],
        styleT,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0.7 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -3 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5 * mm),
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('SPAN', (0, -1), (-1, -1)),
    ]
    col_width = (46.5 * mm, 46.5 * mm, 46.5 * mm, 46.5 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(tbl)
    fwb.append(Paragraph("19.5. степень утраты профессиональной трудоспособности в процентах на момент направления гражданина на медико-социальную экспертизу:", styleText))
    fwb.append(Paragraph("19.6. срок, на который установлена степень утраты профессиональной трудоспособности в процентах:", styleText))
    fwb.append(Paragraph("19.7. дата, до которой установлена степень утраты профессиональной трудоспособности в процентах (день, месяц, год):", styleText))
    fwb.append(
        Paragraph(
            "19.8. степени утраты профессиональной трудоспособности (в процентах), установленные по повторным несчастным случаям на производстве и профессиональным заболеваниям, и даты, до которых они установлены:",  # noqa: E501
            styleText,
        )
    )
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("20. Сведения о получении образования (при получении образования):", styleText))
    fwb.append(Paragraph("20.1. наименование и адрес образовательной организации, в которой гражданин получает образование:", styleText))
    fwb.append(Paragraph("20.2. курс, класс, возрастная группа детского дошкольного учреждения (нужное подчеркнуть и указать):", styleText))
    fwb.append(Paragraph("20.3. профессия (специальность), для получения которой проводится обучение:", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("21. Сведения о трудовой деятельности (при осуществлении трудовой деятельности):", styleText))
    fwb.append(Paragraph("21.1. основная профессия (специальность, должность): артиска-вокалистка(солистка)", styleText))
    fwb.append(Paragraph("21.2. квалификация (класс, разряд, категория, звание): 1 категория", styleText))
    fwb.append(Paragraph("21.3. стаж работы: 15", styleText))
    fwb.append(Paragraph("21.4. выполняемая работа на момент направления на медико-социальную экспертизу с указанием профессии (специальности, должности):", styleText))
    fwb.append(Paragraph("21.5. условия и характер выполняемого труда:", styleText))
    fwb.append(Paragraph("21.6. место работы (наименование организации):", styleText))
    fwb.append(Paragraph("21.7. адрес места работы:", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("Раздел II. Клинико-функциональные данные гражданина", styleCentreBold))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("22. Наблюдается в медицинской организации с", styleText))
    fwb.append(Paragraph("23. Анамнез заболевания:", styleText))
    fwb.append(Paragraph("--------", styleText))
    fwb.append(Paragraph("24. Анамнез жизни:", styleText))
    fwb.append(Paragraph("---------", styleText))
    fwb.append(Paragraph("25. Частота и длительность временной нетрудоспособности (сведения за последние 12 месяцев):", styleText))
    fwb.append(Paragraph("25.1. Наличие листка нетрудоспособности в форме электронного документа (далее - ЭЛН):", styleText))
    fwb.append(Paragraph("25.2. No ЭЛН:", styleText))
    fwb.append(Paragraph("25.1. Наличие листка нетрудоспособности в форме электронного документа (далее - ЭЛН)25.2. No ЭЛН:", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(
        Paragraph(
            "26. Результаты и эффективность проведенных мероприятий медицинской реабилитации, рекомендованных индивидуальной программой реабилитации или абилитации инвалида (ребенка- инвалида) No к протоколу проведения медико-социальной экспертизы No от (нужное отметить):",  # noqa: E501
            styleText,
        )
    )
    opinion = gen_opinion_2(
        [
            [
                f"26.1. {op_boxed_tag}X{cl_boxed_tag} востановление нарушенных функций",
                f"26.1.1. {op_boxed_tag}{space_symbol}{cl_boxed_tag} полное",
                f"26.1.2. {op_boxed_tag}{space_symbol}{cl_boxed_tag} частичное",
                f"26.1.3. {op_boxed_tag}{space_symbol}{cl_boxed_tag} положительные результаты отсутствуют",
            ],
            [
                f"26.2. {op_boxed_tag}X{cl_boxed_tag} достижение компенсации утраченных либо отсутствующих функций",
                f"26.2.1. {op_boxed_tag}{space_symbol}{cl_boxed_tag} полное",
                f"26.2.2. {op_boxed_tag}{space_symbol}{cl_boxed_tag} частичное",
                f"26.2.3. {op_boxed_tag}{space_symbol}{cl_boxed_tag} положительные результаты отсутствуют",
            ],
        ],
        styleT,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0.7 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -3 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5 * mm),
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('SPAN', (0, -1), (-1, -1)),
    ]
    col_width = (46.5 * mm, 46.5 * mm, 46.5 * mm, 46.5 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(tbl)
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("27. Антропометрические данные и физиологические параметры:", styleText))
    opinion = gen_opinion_2(
        [
            [
                f"27.1. {op_boxed_tag}X{cl_boxed_tag} врост:",
                f"27.2. {op_boxed_tag}{space_symbol}{cl_boxed_tag} вес:",
                f"27.3. {op_boxed_tag}{space_symbol}{cl_boxed_tag} индекс массы тела:",
            ],
            [
                f"27.4. {op_boxed_tag}X{cl_boxed_tag} телосложение:",
                f"27.5. {op_boxed_tag}{space_symbol}{cl_boxed_tag} суточный объем физиологических отправлений (мл) (при наличии медицинских показаний в обеспечении абсорбирующим бельем):",
                f"27.6. {op_boxed_tag}{space_symbol}{cl_boxed_tag} объем талии/бедер (при наличии медицинских показаний в обеспечении абсорбирующим бельем):",
            ],
        ],
        styleT,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0.7 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -3 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5 * mm),
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
    ]
    col_width = (62 * mm, 62 * mm, 62 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    fwb.append(Spacer(1, 1 * mm))
    fwb.append(tbl)
    opinion = gen_opinion_2(
        [
            [
                f"27.7. {op_boxed_tag}X{cl_boxed_tag} масса тела при рождении (в отношении детей в в возрасте до 3 лет):",
                f"27.8. {op_boxed_tag}{space_symbol}{cl_boxed_tag} физическое развитие (в отношении детей в в возрасте до 3 лет):",
            ],
        ],
        styleT,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0.7 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), -3 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5 * mm),
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
    ]
    col_width = (93 * mm, 93 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    fwb.append(tbl)
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("28. Состояние здоровья гражданина при направлении на медико-социальную экспертизу:", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(
        Paragraph(
            "29. Сведения о медицинских обследованиях, необходимых для получения клинико-функциональных данных в зависимости от заболевания при проведении медико-социальной экспертизы:",
            styleText,
        )
    )
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("30. Диагноз при направлении на медико-социальную экспертизу:", styleText))
    fwb.append(Paragraph("30.1. основное заболевание:", styleText))
    fwb.append(Paragraph("30.2. код основного заболевания по МКБ:", styleText))
    fwb.append(Paragraph("30.3. осложнения основного заболевания:", styleText))
    fwb.append(Paragraph("30.4. сопутствующие заболевания:", styleText))
    fwb.append(Paragraph("30.5. коды сопутствующих заболеваний по МКБ:", styleText))
    fwb.append(Paragraph("30.6. осложнения сопутствующих заболеваний:", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("31. Клинический прогноз: Благоприятный, Относительно благоприятный, Сомнительный (неопределенный), Неблагоприятный (нужное подчеркнуть).", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("32. Реабилитационный потенциал: Высокий, Удовлетворительный, Низкий (нужное подчеркнуть).", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("33. Реабилитационный прогноз: Благоприятный, Относительно благоприятный, Сомнительный (неопределенный), Неблагоприятный (нужное подчеркнуть).", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("34. Рекомендуемые мероприятия по медицинской реабилитации:", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("35. Рекомендуемые мероприятия по реконструктивной хирургии:", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("36. Рекомендуемые мероприятия по протезированию и ортезированию:", styleText))
    fwb.append(Spacer(1, 1.5 * mm))
    fwb.append(Paragraph("37. Санаторно-курортное лечение:", styleText))

    opinion = gen_opinion_2(
        [
            [
                "Председатель врачебной комиссии:",
                "",
                "",
                "",
                "Иванов И.И.",
            ],
            [
                "",
                "",
                "(подпись)",
                "",
                "(расшифровка подписи)",
            ],
        ],
        styleT,
    )
    tbl_style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0.7 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 1 * mm),
        ('TOPPADDING', (1, 1), (-1, -1), -1 * mm),
        ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
        ('LINEBELOW', (2, 0), (2, 0), 0.75, colors.black),
        ('LINEBELOW', (4, 0), (4, 0), 0.75, colors.black),
    ]
    col_width = (69 * mm, 5 * mm, 49 * mm, 5 * mm, 59 * mm)
    tbl = gen_table(opinion, col_width, tbl_style)
    fwb.append(Spacer(1, 3 * mm))
    fwb.append(tbl)

    for k in range(4):
        fwb.append(Spacer(1, 3 * mm))
        members = "Члены врачебной комиссии:" if k == 0 else ""
        opinion = gen_opinion_2(
            [
                [
                    f"{members}",
                    "",
                    "",
                    "",
                    f"первый{k}",
                ],
                [
                    "",
                    "",
                    "(подпись)",
                    "",
                    "(расшифровка подписи)",
                ],
            ],
            styleT,
        )
        tbl_style = [
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0.7 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 1 * mm),
            ('TOPPADDING', (1, 1), (-1, -1), -1 * mm),
            ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
            ('LINEBELOW', (2, 0), (2, 0), 0.75, colors.black),
            ('LINEBELOW', (4, 0), (4, 0), 0.75, colors.black),
        ]
        col_width = (69 * mm, 5 * mm, 49 * mm, 5 * mm, 59 * mm)
        tbl = gen_table(opinion, col_width, tbl_style)
        fwb.append(Spacer(1, 3 * mm))
        fwb.append(tbl)

    return fwb


def gen_opinion(data, type_style):
    opinion = [[Paragraph(f"{k}", type_style) for k in data]]
    return opinion


def gen_opinion_2(data, type_style):
    opinion = []
    for element in data:
        opinion.append([Paragraph(f"{k}", type_style) for k in element])
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


def gen_table_centre(opinion, col_width, tbl_style, row_height=None):
    tbl = Table(
        opinion,
        colWidths=col_width,
        rowHeights=row_height,
    )
    tbl.setStyle(TableStyle(tbl_style))
    return tbl
