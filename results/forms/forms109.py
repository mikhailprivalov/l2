import json


from hospitals.models import Hospitals
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from results.prepare_data import fields_result_only_title_fields
from directions.models import Issledovaniya, Napravleniya
from laboratory.settings import FONTS_FOLDER
import os.path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None, **kwargs):
    """
    Карта учета профилактического медицинского осмотра (диспансеризации)
    """

    hospital: Hospitals = direction.hospital
    hospital_name = hospital.safe_short_title
    hospital_address = hospital.safe_address

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10
    style.leading = 12
    style.spaceAfter = 0 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = 15

    styleFL = deepcopy(style)
    styleFL.firstLineIndent = 0

    styleSign = deepcopy(style)
    styleSign.firstLineIndent = 0
    styleSign.alignment = TA_LEFT
    styleSign.leading = 13
    style.fontSize = 10

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleBold.firstLineIndent = 0

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 9
    styleCenter.leading = 10
    styleCenter.spaceAfter = 0 * mm

    styleRight = deepcopy(style)
    styleRight.aligment = TA_RIGHT

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.firstLineIndent = 0
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 13
    styleCenterBold.face = 'PTAstraSerifBold'

    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    styleT = deepcopy(style)
    styleT.firstLineIndent = 0

    styleSingBold = deepcopy(styleSign)
    styleSingBold.fontName = "PTAstraSerifBold"

    styleSmallFont = deepcopy(style)
    styleSmallFont.fontSize = 7

    data = title_fields(iss)
    objs = []
    opinion = [
        [
            Paragraph('', style),
            Paragraph('<b>Приложение №1<br/> к приказу Министерства здравоохранения<br/>Российской Федерации<br/>от 10 ноября 2020 г. N 1207н</b>', styleSingBold),
        ],
    ]
    tbl = Table(opinion, 2 * [90 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (1, 0), (-1, -1), 80),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )

    opinion = [
        [
            Paragraph('Наименование медицинской организации', style),
            Paragraph('Код формы по ОКУД _______________ <br/> Код организации по ОКПО __________', styleSign),
        ],
        [
            Paragraph('{}»'.format(hospital_name), style),
            Paragraph('Медицинская документация Учетная форма N 131/у', styleSign),
        ],
        [
            Paragraph('Адрес: {}'.format(hospital_address), style),
            Paragraph('Утверждена приказом Минздрава России от "__"___ 2020__ г. N ___', styleSign),
        ],
    ]
    tbl = Table(opinion, 2 * [100 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )

    objs.append(tbl)

    objs.append(
        Paragraph(
            'Карта учета <br/> профилактического медицинского осмотра (диспансеризации)',
            styleCenterBold,
        )
    )
    objs.append(
        Paragraph(
            f'1. Дата начала профилактического медицинского осмотра (диспансеризации) {data["Дата начала "]}',
            style,
        )
    )

    objs.append(Spacer(1, 3 * mm))
    objs.append(Paragraph(f'2. Фамилия, имя, отчество (при наличии): {data["ФИО пациента"]}&nbsp; {data["Дата рождения"]} г. рождения', style))
    objs.append(
        Paragraph(
            f'3. Пол: <u>{data["Пол"]}</u> ',
            style,
        )
    )
    objs.append(Paragraph(f'4. Дата рождения  <u>{data["Дата рождения"]}</u>', style))

    place_data = json.loads(data["Местность"])
    objs.append(
        Paragraph(
            f'5. Местность: {place_data["title"]}-{place_data["code"]}',
            style,
        )
    )

    address_data = json.loads(data["Адрес регистрации"])
    objs.append(Paragraph(f'6. Адрес регистрации по месту жительства {address_data["address"]}', style))
    objs.append(
        Paragraph(
            f'7. Код категории льготы: {data["Код категории льготы"]}',
            style,
        )
    )
    objs.append(
        Paragraph(f'8. Принадлежность к коренным малочисленным народам Севера, Сибири и Дальнего Востока Российской Федерации: {data["Принадлежность малочисленным народам "]}', style)
    )
    objs.append(
        Paragraph(
            f'9. Занятость: {data["Занятость"]}',
            style,
        )
    )
    objs.append(
        Paragraph(
            f'10. Профилактический медицинский осмотр (первый этап диспансеризации) проводится мобильной медицинской бригадой: {data["Медосмотр (1 этап) мобильно"]}',
            style,
        )
    )
    objs.append(
        Paragraph('11. Результаты исследований и иных медицинских вмешательств, выполненных при проведении профилактического медицинского осмотра ' '(первого этапа диспансеризации):', style)
    )
    objs.append(Spacer(1, 2 * mm))

    styleTCenter = deepcopy(styleT)
    styleTCenter.alignment = TA_CENTER
    styleTCenter.leading = 3.5 * mm
    glucose = data["Глюкоза, Глюкоза"]
    glucose = glucose.split(" ")[0]
    holesterin = data["Холестерин (ммоль/л), Холестерин общий"]
    holesterin = holesterin.split(" ")[0]
    opinion = [
        [
            Paragraph(f'Рост {data["рост (см)"]} см ', styleTCenter),
            Paragraph(f'Масса тела {data["масса тела (кг)"]} кг', styleTCenter),
            Paragraph(f'индекс массы тела {data["ИМТ"]} кг/м<sup><small>2</small></sup>', styleTCenter),
        ],
        [
            Paragraph(f'артериальное давление на периферических артериях {data["АД (мм рт.ст)"]} мм рт.ст. ', styleSign),
            Paragraph(f'прием гипотензивных лекарственных препаратов: {data["прием гипотензивных ЛП"]}', styleSign),
            Paragraph(f'внутриглазное давление {data["внутриглазное давление (мм рт.ст.)"]} мм рт.с', styleSign),
        ],
        [
            Paragraph(f'уровень общего холестерина в крови {holesterin} ммоль/л', styleSign),
            Paragraph(f'прием гипогликемических лекарственных препаратов: {data["Прием гипогликемических ЛП"]}', styleSign),
            Paragraph(f'уровень глюкозы в крови натощак {glucose} ммоль/л', styleSign),
        ],
        [
            Paragraph(f'прием гиполипидемических лекарственных препаратов: {data["Прием гиполипидемических ЛП"]}', styleSign),
            Paragraph(
                f'относительный сердечно-сосудистый риск (от 18 лет до 39 лет) {data["относительный С-С риск (%)"]} абсолютный сердечно-сосудистый риск (от 40 лет до 64 лет включительно) '
                f'{data["абсолютный С-С риск (%)"]} %',
                styleSign,
            ),
        ],
    ]

    row_height = []
    for i in opinion:
        row_height.append(16 * mm)
    row_height[3] = None
    row_height[2] = None
    row_height[1] = None
    row_height[0] = None

    tbl = Table(opinion, colWidths=(50 * mm, 50 * mm, 90 * mm), rowHeights=row_height)

    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                ('SPAN', (1, 3), (2, 3)),
            ]
        )
    )

    objs.append(tbl)

    styleLeft = deepcopy(style)
    styleLeft.alignment = TA_LEFT

    objs.append(
        Paragraph(
            '12. Сведения о проведенных приёмах (осмотрах, консультациях), исследованиях и иных медицинских'
            ' вмешательствах при профилактическом медицинском осмотре (на первом этапе диспансеризации)',
            style,
        )
    )
    objs.append(Spacer(1, 2 * mm))

    opinion = [
        [
            Paragraph(
                'Приём (осмотр, консультация), исследование и иное медицинское вмешательство, входящее' ' в объем профилактического медицинского осмотра / первого этапа диспансеризации',
                styleTCenter,
            ),
            Paragraph('', styleTCenter),
            Paragraph('N строки', styleTCenter),
            Paragraph('Отметка о проведении (дата/(-)', styleTCenter),
            Paragraph('Примечание', styleTCenter),
            Paragraph('', styleSign),
            Paragraph('Выявлено патологическое состояние (+/-)', styleTCenter),
        ],
        [
            Paragraph('', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph('Отказ от проведения (+/-)', styleTCenter),
            Paragraph('Проведено ранее (дата)', styleTCenter),
            Paragraph('', styleTCenter),
        ],
        [
            Paragraph('1', styleTCenter),
            Paragraph('', styleSign),
            Paragraph('2', styleTCenter),
            Paragraph('3', styleTCenter),
            Paragraph('4', styleTCenter),
            Paragraph('5', styleTCenter),
            Paragraph('6', styleTCenter),
        ],
        [
            Paragraph('Опрос (анкетирование), 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('01', styleTCenter),
            Paragraph(f'{data["Анкета проведено"]}', styleTCenter),
            Paragraph(f'{data["Анкета отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["Анкета патология"]}', styleTCenter),
        ],
        [
            Paragraph('Расчет на основании антропометрии (измерение роста, массы тела, окружности талии) индекса массы тела, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('02', styleTCenter),
            Paragraph(f'{data["антропометрия проведено"]}', styleTCenter),
            Paragraph(f'{data["антропометрия отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["антропометрия патология"]}', styleTCenter),
        ],
        [
            Paragraph('Измерение артериального давления на периферических артериях, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('03', styleTCenter),
            Paragraph(f'{data["давление проведено"]}', styleTCenter),
            Paragraph(f'{data["давление отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["давление патология"]}', styleTCenter),
        ],
        [
            Paragraph('Определение уровня общего холестерина в крови, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('04', styleTCenter),
            Paragraph(f'{data["холестерин проведено"]}', styleTCenter),
            Paragraph(f'{data["холестерин отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["холестерин патология"]}', styleTCenter),
        ],
        [
            Paragraph('Определение уровня глюкозы в крови натощак, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('05', styleTCenter),
            Paragraph(f'{data["глюкоза проведено"]}', styleTCenter),
            Paragraph(f'{data["глюкоза отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["глюкоза патология"]}', styleTCenter),
        ],
        [
            Paragraph('Определение относительного сердечно-сосудистого риска у граждан в возрасте от 18 до 39 лет включительно, 1 раз год', styleSign),
            Paragraph('', styleSign),
            Paragraph('06', styleTCenter),
            Paragraph(f'{data["относительный проведено"]}', styleTCenter),
            Paragraph(f'{data["относительный отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["относительный патология"]}', styleTCenter),
        ],
        [
            Paragraph('Определение абсолютного сердечно-сосудистого риска у граждан в возрасте от 40 до 64 лет включительно, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('07', styleTCenter),
            Paragraph(f'{data["абсолютное проведено"]}', styleTCenter),
            Paragraph(f'{data["абсолютное отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["абсолютное патология"]}', styleTCenter),
        ],
        [
            Paragraph('Флюорография легких или рентгенография легких, 1 раз в 2 года', styleSign),
            Paragraph('', styleSign),
            Paragraph('08', styleTCenter),
            Paragraph(f'{data["флюра проведено"]}', styleTCenter),
            Paragraph(f'{data["флюра отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["флюра патология"]}', styleTCenter),
        ],
        [
            Paragraph('Электрокардиография в покое (при первом прохождении профилактического медицинского осмотра, далее в возрасте 35 лет и старше),' ' 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('09', styleTCenter),
            Paragraph(f'{data["экг проведено"]}', styleTCenter),
            Paragraph(f'{data["экг отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["экг патология"]}', styleTCenter),
        ],
        [
            Paragraph('Измерение внутриглазного давления (при первом прохождении профилактического медицинского осмотра, далее в возрасте' ' 40 лет и старше), 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('10', styleTCenter),
            Paragraph(f'{data["тонометрия проведено"]}', styleTCenter),
            Paragraph(f'{data["тонометрия отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["тонометрия патология"]}', styleTCenter),
        ],
        [
            Paragraph('Осмотр фельдшером (акушеркой) или врачом акушером-гинекологом женщин в возрасте от 18 лет и старше, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('11', styleTCenter),
            Paragraph(f'{data["тонометрия проведено"]}', styleTCenter),
            Paragraph(f'{data["тонометрия отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["тонометрия патология"]}', styleTCenter),
        ],
        [
            Paragraph(
                'Взятие с использованием щетки цитологической цервикальной мазка (соскоба) с поверхности шейки матки (наружного маточного зева) и '
                'цервикального канала на цитологическое исследование, цитологическое исследование мазка с шейки матки в возрасте от 18 до 64 лет,1 раз в 3 года',
                styleSign,
            ),
            Paragraph('', styleSign),
            Paragraph('12', styleTCenter),
            Paragraph(f'{data["мазок проведено"]}', styleTCenter),
            Paragraph(f'{data["мазок отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["мазок патология"]}', styleTCenter),
        ],
        [
            Paragraph('Маммография обеих молочных желез в двух проекциях у женщин в возрасте от 40 до 75 лет включительно, 1 раз в 2 года', styleSign),
            Paragraph('', styleSign),
            Paragraph('13', styleTCenter),
            Paragraph(f'{data["маммография проведено"]}', styleTCenter),
            Paragraph(f'{data["маммография отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["маммография патология"]}', styleTCenter),
        ],
        [
            Paragraph('Исследование кала на скрытую кровь иммунохимическим методом', styleSign),
            Paragraph('а) в возрасте от 40 до 64 лет включительно, 1 раз в 2 года', styleSign),
            Paragraph('14.1', styleTCenter),
            Paragraph(f'{data["Исследование кала от 40 до 64 лет проведено"]}', styleTCenter),
            Paragraph(f'{data["Исследование кала от 40 до 64 лет отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["Исследование кала от 40 до 64 лет патология"]}', styleTCenter),
        ],
        [
            Paragraph('', styleSign),
            Paragraph('б) в возрасте от 65 до 75 лет включительно, 1 раз в год', styleSign),
            Paragraph('14.2', styleTCenter),
            Paragraph(f'{data["Исследование кала от 65 до 75 лет проведено"]}', styleTCenter),
            Paragraph(f'{data["Исследование кала от 65 до 75 лет отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["Исследование кала от 65 до 75 лет патология"]}', styleTCenter),
        ],
        [
            Paragraph('Определение простат-специфического антигена в крови у мужчин в возрасте 45, 50, 55, 60 и 64 лет', styleSign),
            Paragraph('', styleSign),
            Paragraph('15', styleTCenter),
            Paragraph(f'{data["простат проведено"]}', styleTCenter),
            Paragraph(f'{data["простат отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["маммография патология"]}', styleTCenter),
        ],
        [
            Paragraph('Эзофагогастродуоденоскопия в возрасте 45 лет однократно', styleSign),
            Paragraph('', styleSign),
            Paragraph('16', styleTCenter),
            Paragraph(f'{data["ФГДС проведено"]}', styleTCenter),
            Paragraph(f'{data["ФГДС отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["ФГДС патология"]}', styleTCenter),
        ],
        [
            Paragraph('Общий анализ крови в возрасте 40 лет и старше, 1 раз в год', styleSign),
            Paragraph('', styleSign),
            Paragraph('17', styleTCenter),
            Paragraph(f'{data["оак проведено"]}', styleTCenter),
            Paragraph(f'{data["оак отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["оак патология"]}', styleTCenter),
        ],
        [
            Paragraph('Краткое индивидуальное профилактическое консультирование в возрасте 18 лет и старше', styleSign),
            Paragraph('', styleSign),
            Paragraph('18', styleTCenter),
            Paragraph(f'{data["краткое проведено"]}', styleTCenter),
            Paragraph(f'{data["краткое отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["краткое патология"]}', styleTCenter),
        ],
        [
            Paragraph(
                'Прием (осмотр) по результатам профилактического медицинского осмотра фельдшером фельдшерского здравпункта или '
                'фельдшерско-акушерского пункта, врачом-терапевтом или врачом по медицинской профилактике отделения (кабинета) медицинской профилактики'
                'или центра здоровья граждан в возрасте 18 лет и старше, 1 раз в год',
                styleSign,
            ),
            Paragraph('', styleSign),
            Paragraph('19', styleTCenter),
            Paragraph(f'{data["центр здоровья проведено"]}', styleTCenter),
            Paragraph(f'{data["центр здоровья отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["центр здоровья патология"]}', styleTCenter),
        ],
        [
            Paragraph('Прием (осмотр) врачом-терапевтом по результатам первого этапа диспансеризации', styleSign),
            Paragraph('а) граждан в возрасте от 18 лет до 39 лет 1 раз в 3 года', styleSign),
            Paragraph('20.1', styleTCenter),
            Paragraph(f'{data["терапевт от 18 лет до 39 лет проведено"]}', styleTCenter),
            Paragraph(f'{data["терапевт от 18 лет до 39 лет отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["терапевт от 18 лет до 39 лет патология"]}', styleTCenter),
        ],
        [
            Paragraph('', styleSign),
            Paragraph('б) граждан в возрасте 40 лет и старше 1 раз в год', styleSign),
            Paragraph('20.2', styleTCenter),
            Paragraph(f'{data["терапевт от 40 лет и старше проведено"]}', styleTCenter),
            Paragraph(f'{data["терапевт от 40 лет и старше отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["терапевт от 40 лет и старше патология"]}', styleTCenter),
        ],
        [
            Paragraph(
                'Осмотр на выявление визуальных и иных локализаций онкологических заболеваний, включающий осмотр кожных покровов, слизистых губ'
                'и ротовой полости, пальпацию щитовидной железы, лимфатических узлов, граждан в возрасте 18 лет и старше, 1 раз в год',
                styleSign,
            ),
            Paragraph('', styleSign),
            Paragraph('21', styleTCenter),
            Paragraph(f'{data["онко проведено"]}', styleTCenter),
            Paragraph(f'{data["онко отказ"]}', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph(f'{data["онко патология"]}', styleTCenter),
        ],
    ]

    row_height = []
    for i in opinion:
        row_height.append(None)

    tbl = Table(opinion, colWidths=(43 * mm, 45 * mm, 15 * mm, 22 * mm, 20 * mm, 20 * mm, 25 * mm), rowHeights=row_height)

    table_style = [
        ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('SPAN', (4, 0), (5, 0)),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('SPAN', (2, 0), (2, 1)),
        ('SPAN', (3, 0), (3, 1)),
        ('SPAN', (0, 0), (1, 1)),
    ]

    table_style += [('SPAN', (0, i + 1), (1, i + 1)) for i in range(15)]

    table_style += [('SPAN', (0, i + 18), (1, i + 18)) for i in range(5)]
    table_style += [('SPAN', (0, 25), (1, 25))]

    tbl.setStyle(TableStyle(table_style))

    objs.append(tbl)
    objs.append(
        Paragraph(
            f'13. Направлен на второй этап диспансеризации: {data["Направлен на второй этап"]}',
            style,
        )
    )

    objs.append(
        Paragraph(
            '14. Сведения о проведенных приёмах (осмотрах, консультациях), исследованиях и иных медицинских вмешательствах на втором этапе диспансеризации',
            style,
        )
    )

    opinion = [
        [
            Paragraph('Приём (осмотр, консультация), исследование и иное медицинское вмешательство, входящее в объем второго этапа диспансеризации', styleTCenter),
            Paragraph('N строки', styleTCenter),
            Paragraph('Выявлено медицинское показание в рамках первого этапа диспансеризации (+/-)', styleTCenter),
            Paragraph('Дата проведения', styleTCenter),
            Paragraph('Отказ (+/-)', styleTCenter),
            Paragraph('Проведено ранее (дата)', styleTCenter),
            Paragraph('Выявлено патологическое состояние (+/-)', styleTCenter),
        ],
        [
            Paragraph('1', styleTCenter),
            Paragraph('2', styleTCenter),
            Paragraph('3', styleTCenter),
            Paragraph('4', styleTCenter),
            Paragraph('5', styleTCenter),
            Paragraph('6', styleTCenter),
            Paragraph('7', styleTCenter),
        ],
        [
            Paragraph(' Осмотр (консультация) врачом-неврологом', styleSign),
            Paragraph('01', styleSign),
        ],
        [
            Paragraph('Дуплексное сканирование брахиоцефальных артерий ', styleSign),
            Paragraph('02', styleSign),
        ],
        [
            Paragraph('Осмотр (консультация) врачом-хирургом или врачом-урологом', styleSign),
            Paragraph('03', styleSign),
        ],
        [
            Paragraph('Осмотр (консультация) врачом-хирургом или врачом-колопроктологом, включая проведение ректороманоскопии', styleSign),
            Paragraph('04', styleSign),
        ],
        [
            Paragraph('Колоноскопия', styleSign),
            Paragraph('05', styleSign),
        ],
        [
            Paragraph('Эзофагогастродуоденоскопия', styleSign),
            Paragraph('06', styleSign),
        ],
        [
            Paragraph('Рентгенография легких', styleSign),
            Paragraph('07', styleSign),
        ],
        [
            Paragraph('Компьютерная томография легких', styleSign),
            Paragraph('08', styleSign),
        ],
        [
            Paragraph('Эхокардиография', styleSign),
            Paragraph('09', styleSign),
        ],
        [
            Paragraph('Дуплексное сканирование вен нижних конечностей', styleSign),
            Paragraph('10', styleSign),
        ],
        [
            Paragraph('Спирометрия', styleSign),
            Paragraph('11', styleSign),
        ],
        [
            Paragraph('Осмотр (консультация) врачом-акушером-гинекологом', styleSign),
            Paragraph('12', styleSign),
        ],
        [
            Paragraph('Осмотр (консультация) врачом-оториноларингологом', styleSign),
            Paragraph('13', styleSign),
        ],
        [
            Paragraph('Осмотр (консультация) врачом-офтальмологом', styleSign),
            Paragraph('14', styleSign),
        ],
        [
            Paragraph('Индивидуальное или групповое (школа для пациентов) углубленное профилактическое консультирование для граждан:', styleSign),
            Paragraph('15', styleSign),
        ],
        [
            Paragraph(
                'с выявленной ишемической болезнью сердца, цереброваскулярными заболеваниями, хронической ишемией нижних конечностей атеросклеротического'
                'генеза или болезнями, характеризующимися повышенным кровяным давлением',
                styleSign,
            ),
            Paragraph('15.1', styleSign),
        ],
        [
            Paragraph(
                'с выявленным по результатам анкетирования риском пагубного потребления алкоголя и (или) потребления наркотических средств ' 'и психотропных веществ без назначения врача',
                styleSign,
            ),
            Paragraph('15.2', styleSign),
        ],
        [
            Paragraph('в возрасте 65 лет и старше в целях коррекции выявленных факторов риска и (или) профилактики старческой астении', styleSign),
            Paragraph('15.3', styleSign),
        ],
        [
            Paragraph(
                'при выявлении высокого относительного, высокого и очень высокого абсолютного сердечно-сосудистого риска, и (или) ожирения,'
                'и (или) гиперхолестеринемии с уровнем общего холестерина 8 ммоль/л и более, а также установленном по результатам анкетирования курении более'
                '20 сигарет в день, риске пагубного потребления алкоголя и (или) риске немедицинского потребления наркотических средств и психотропных веществ',
                styleSign,
            ),
            Paragraph('15.4', styleSign),
        ],
        [
            Paragraph('Прием (осмотр) врачом-терапевтом по результатам второго этапа диспансеризации', styleSign),
            Paragraph('16', styleSign),
        ],
        [
            Paragraph('Направление на осмотр (консультацию) врачом-онкологом при подозрении на онкологические заболевания.', styleSign),
            Paragraph('17', styleSign),
        ],
        [
            Paragraph(
                'Oсмотр (консультацию) врачом-дерматовенерологом, включая проведение дерматоскопии (для граждан с подозрением'
                'на злокачественные новообразования кожи и (или) слизистых оболочек по назначению врача-терапевта по результатам осмотра на'
                'выявление визуальных и иных локализаций онкологических заболеваний, включающего осмотр кожных покровов, слизистых губ и ротовой '
                'полости, пальпацию щитовидной железы, лимфатических узлов);',
                styleSign,
            ),
            Paragraph('18', styleSign),
        ],
        [
            Paragraph(
                'Проведение исследования уровня гликированного гемоглобина в крови (для граждан с подозрением на сахарный диабет'
                'по назначению врача-терапевта по результатам осмотров и исследований первого этапа диспансеризации);',
                styleSign,
            ),
            Paragraph('19', styleSign),
        ],
    ]

    row_height = [None for i in opinion]

    tbl = Table(opinion, colWidths=(70 * mm, 15 * mm, 25 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm), rowHeights=row_height)

    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ]
        )
    )

    objs.append(tbl)

    objs.append(
        Paragraph(
            '15. Дата окончания профилактического медицинского осмотра __________________',
            style,
        )
    )
    objs.append(
        Paragraph(
            f'Дата окончания первого этапа диспансеризации {data["Дата окончания первого этапа диспансеризации"]}',
            style,
        )
    )
    objs.append(
        Paragraph(
            f'Дата окончания второго этапа диспансеризации {data["Дата окончания второго этапа диспансеризации"]}',
            style,
        )
    )
    objs.append(
        Paragraph(
            f'16. Профилактический медицинский осмотр (диспансеризация) проведен(а): {data["Медицинский осмотр проведен"]}',
            style,
        )
    )
    objs.append(
        Paragraph(
            '17. Выявленные при проведении профилактического медицинского осмотра (диспансеризации) факторы риска и другие патологические '
            'состояния и заболевания, повышающие вероятность развития хронических неинфекционных заболеваний',
            style,
        )
    )

    opinion = [
        [
            Paragraph('Наименование фактора риска, другого патологического состояния и заболевания', styleTCenter),
            Paragraph('', styleTCenter),
            Paragraph('№ строки', styleTCenter),
            Paragraph('Код МКБ-10<sup>1</sup>', styleTCenter),
            Paragraph('Выявлен фактор риска, другое патологическое состояние и заболевание (+/-)', styleTCenter),
        ],
        [
            Paragraph('1', styleTCenter),
            Paragraph('', styleSign),
            Paragraph('2', styleTCenter),
            Paragraph('3', styleTCenter),
            Paragraph('4', styleTCenter),
        ],
        [
            Paragraph('Гиперхолестеринемия', styleSign),
            Paragraph('', styleSign),
            Paragraph('01', styleTCenter),
            Paragraph('Е78', styleTCenter),
            Paragraph(f'{data["01 Гиперхолестеринемия (Е78)"]}', styleTCenter),
        ],
        [
            Paragraph('Гипергликемия ', styleSign),
            Paragraph('', styleSign),
            Paragraph('02', styleTCenter),
            Paragraph('R73.9', styleTCenter),
            Paragraph(f'{data["02 Гипергликемия (R73.9)"]}', styleTCenter),
        ],
        [
            Paragraph('Курение табака', styleSign),
            Paragraph('', styleSign),
            Paragraph('03', styleTCenter),
            Paragraph('Z72.0', styleTCenter),
            Paragraph(f'{data["03 Курение табака (Z72.0)"]}', styleTCenter),
        ],
        [
            Paragraph('Нерациональное питание ', styleSign),
            Paragraph('', styleSign),
            Paragraph('04', styleTCenter),
            Paragraph('Z72.4', styleTCenter),
            Paragraph(f'{data["04 Нерациональное питание (Z72.4)"]}', styleTCenter),
        ],
        [
            Paragraph('Избыточная масса тела', styleSign),
            Paragraph('', styleSign),
            Paragraph('05', styleTCenter),
            Paragraph('R63.5', styleTCenter),
            Paragraph(f'{data["05 Избыточная масса тела (R63.5)"]}', styleTCenter),
        ],
        [
            Paragraph('Ожирение', styleSign),
            Paragraph('', styleSign),
            Paragraph('06', styleTCenter),
            Paragraph('Е66', styleTCenter),
            Paragraph(f'{data["06 Ожирение (Е66)"]}', styleTCenter),
        ],
        [
            Paragraph('Низкая физическая активность', styleSign),
            Paragraph('', styleSign),
            Paragraph('07', styleTCenter),
            Paragraph('Z72.3', styleTCenter),
            Paragraph(f'{data["07 Низкая физическая активность (Z72.3)"]}', styleTCenter),
        ],
        [
            Paragraph('Риск пагубного потребления алкоголя', styleSign),
            Paragraph('', styleSign),
            Paragraph('08', styleTCenter),
            Paragraph('Z72.1', styleTCenter),
            Paragraph(f'{data["08 Риск пагубного потребления алкоголя (Z72.1)"]}', styleTCenter),
        ],
        [
            Paragraph('Риск потребления наркотических средств и психотропных веществ без назначения врача', styleSign),
            Paragraph('', styleSign),
            Paragraph('09', styleTCenter),
            Paragraph('Z72.2', styleTCenter),
            Paragraph(f'{data["09 Риск потребления наркотических средств и психотропных веществ без назначения врача (Z72.2)"]}', styleTCenter),
        ],
        [
            Paragraph('Отягощенная наследственность по сердечно-сосудистым заболеваниям', styleSign),
            Paragraph('инфаркт миокарда', styleSign),
            Paragraph('10', styleTCenter),
            Paragraph('Z82.4', styleTCenter),
            Paragraph(f'{data["10 инфаркт миокарда (Z82.4)"]}', styleTCenter),
        ],
        [
            Paragraph('', styleSign),
            Paragraph('мозговой инсульт', styleSign),
            Paragraph('11', styleTCenter),
            Paragraph('Z82.3', styleTCenter),
            Paragraph(f'{data["11 мозговой инсульт (Z82.3)"]}', styleTCenter),
        ],
        [
            Paragraph('Отягощенная наследственность по злокачественным новообразованиям', styleSign),
            Paragraph('колоректальной области', styleSign),
            Paragraph('12', styleTCenter),
            Paragraph('Z80.0', styleTCenter),
            Paragraph(f'{data["12 колоректальной области (Z80.0)"]}', styleTCenter),
        ],
        [
            Paragraph('', styleSign),
            Paragraph('других локализации', styleSign),
            Paragraph('13', styleTCenter),
            Paragraph('Z80.9', styleTCenter),
            Paragraph(f'{data["13 других локализации (Z80.9)"]}', styleTCenter),
        ],
        [
            Paragraph('Отягощенная наследственность по хроническим болезням нижних дыхательных путей', styleSign),
            Paragraph('', styleSign),
            Paragraph('14', styleTCenter),
            Paragraph('Z82.5', styleTCenter),
            Paragraph(f'{data["нижних дыхательных путей (Z82.5)"]}', styleTCenter),
        ],
        [
            Paragraph('Отягощенная наследственность по сахарному диабету', styleSign),
            Paragraph('', styleSign),
            Paragraph('15', styleTCenter),
            Paragraph('Z83.3', styleTCenter),
            Paragraph(f'{data["Z83.3"]}', styleTCenter),
        ],
        [
            Paragraph('Высокий (5% -10%) или очень высокий (10% и более) абсолютный сердечно-сосудистый риск', styleSign),
            Paragraph('', styleSign),
            Paragraph('16', styleTCenter),
            Paragraph('-', styleTCenter),
            Paragraph(f'{data["Абсолютный С-С риск"]}', styleTCenter),
        ],
        [
            Paragraph('Высокий (более 1 ед.) относительный сердечно-сосудистый риск', styleSign),
            Paragraph('', styleSign),
            Paragraph('17', styleTCenter),
            Paragraph('-', styleTCenter),
            Paragraph(f'{data["Относительный С-С риск"]}', styleTCenter),
        ],
        [
            Paragraph('Старческая астения', styleSign),
            Paragraph('', styleSign),
            Paragraph('18', styleTCenter),
            Paragraph('R54', styleTCenter),
            Paragraph(f'{data["R54"]}', styleTCenter),
        ],
    ]

    row_height = []
    for i in opinion:
        row_height.append(None)

    tbl = Table(opinion, colWidths=(70 * mm, 50 * mm, 20 * mm, 20 * mm, 30 * mm), rowHeights=row_height)
    table_style = [
        ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('SPAN', (0, 11), (0, 12)),
        ('SPAN', (0, 13), (0, 14)),
    ]

    table_style += [('SPAN', (0, i), (1, i)) for i in range(11)]

    table_style += [('SPAN', (0, i + 15), (1, i + 15)) for i in range(5)]

    tbl.setStyle(TableStyle(table_style))

    objs.append(tbl)

    objs.append(
        Paragraph(
            f'17.1. Все факторы риска, указанные в строках 03, 04, 07, 08, 09 настоящей таблицы: {data["Факторы риска"]}',
            style,
        )
    )
    objs.append(
        Paragraph(
            '18. Заболевания, выявленные при проведении профилактического медицинского осмотра (диспансеризации),установление диспансерного наблюдения',
            style,
        )
    )

    opinion = [
        [
            Paragraph('Наименование классов и отдельных заболеваний', styleTCenter),
            Paragraph('№ строки', styleTCenter),
            Paragraph('Код МКБ-10', styleTCenter),
            Paragraph('Отметка о наличии заболевания (+/-)', styleTCenter),
            Paragraph('Отметка об установлении диспансерного наблюдения (+/-)', styleTCenter),
            Paragraph('Отметка о впервые выявленном заболевании (+/-)', styleTCenter),
            Paragraph('Отметка о впервые установленном диспансерном наблюдении (+/-)', styleTCenter),
        ],
        [
            Paragraph('1', styleTCenter),
            Paragraph('2', styleTCenter),
            Paragraph('3', styleTCenter),
            Paragraph('4', styleTCenter),
            Paragraph('5', styleTCenter),
            Paragraph('6', styleTCenter),
            Paragraph('7', styleTCenter),
        ],
        [
            Paragraph('Туберкулез органов дыхания', styleSign),
            Paragraph('01', styleTCenter),
            Paragraph('А15-А16', styleTCenter),
        ],
        [
            Paragraph('Злокачественные новообразования', styleSign),
            Paragraph('02', styleTCenter),
            Paragraph('С00-С97', styleTCenter),
        ],
        [
            Paragraph('Из них губы, полости рта и глотки', styleSign),
            Paragraph('2.1', styleTCenter),
            Paragraph('С00-С14', styleTCenter),
        ],
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.2', styleTCenter),
            Paragraph('', styleTCenter),
        ],
        [
            Paragraph('пищевода', styleSign),
            Paragraph('2.3', styleTCenter),
            Paragraph('С15', styleTCenter),
        ],
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.4', styleTCenter),
            Paragraph('', styleTCenter),
        ],
        [
            Paragraph('желудка', styleSign),
            Paragraph('2.5', styleTCenter),
            Paragraph('С16', styleTCenter),
        ],
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.6', styleTCenter),
            Paragraph('', styleTCenter),
        ],
        [
            Paragraph('тонкого кишечника', styleSign),
            Paragraph('2.7', styleTCenter),
            Paragraph('С17', styleTCenter),
        ],
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.8', styleTCenter),
            Paragraph('', styleTCenter),
        ],
        [
            Paragraph('ободочной кишки', styleSign),
            Paragraph('2.9', styleTCenter),
            Paragraph('С18', styleTCenter),
        ],
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.10', styleTCenter),
            Paragraph('', styleTCenter),
        ],
        [
            Paragraph('ректосигмоидного соединения, прямой кишки, заднего прохода (ануса) и анального канала', styleSign),
            Paragraph('2.11', styleTCenter),
            Paragraph('С19-С21', styleTCenter),
        ],
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.12', styleTCenter),
            Paragraph('', styleTCenter),
        ],
        [
            Paragraph('трахеи, бронхов, легкого', styleSign),
            Paragraph('2.13', styleTCenter),
            Paragraph('С33, С34', styleTCenter),
        ],
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.14', styleTCenter),
            Paragraph('', styleTCenter),
        ],
        [
            Paragraph('кожи', styleSign),
            Paragraph('2.15', styleTCenter),
            Paragraph('С43-С44', styleTCenter),
        ],
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.16', styleTCenter),
            Paragraph('', styleTCenter),
        ],
        [
            Paragraph('молочной железы', styleSign),
            Paragraph('2.17', styleTCenter),
            Paragraph('С50', styleTCenter),
        ],
        [
            Paragraph('из них в 0-1 стадии', styleSign),
            Paragraph('2.18', styleTCenter),
            Paragraph('', styleTCenter),
        ],
        [
            Paragraph('2 стадии', styleSign),
            Paragraph('2.19', styleTCenter),
            Paragraph('', styleTCenter),
        ],
        [
            Paragraph('шейки матки', styleSign),
            Paragraph('2.20', styleTCenter),
            Paragraph('С53', styleTCenter),
        ],
        [
            Paragraph('из них в 0-1 стадии', styleSign),
            Paragraph('2.21', styleTCenter),
            Paragraph('', styleTCenter),
        ],
        [
            Paragraph('2 стадии', styleSign),
            Paragraph('2.22', styleTCenter),
            Paragraph('', styleTCenter),
        ],
        [
            Paragraph('предстательной железы', styleSign),
            Paragraph('2.23', styleTCenter),
            Paragraph('С61', styleTCenter),
        ],
        [
            Paragraph('из них в 1-2 стадии', styleSign),
            Paragraph('2.24', styleTCenter),
            Paragraph('', styleTCenter),
        ],
        [
            Paragraph('Сахарный диабет', styleSign),
            Paragraph('03', styleTCenter),
            Paragraph('Е10-Е14Е10-Е14', styleTCenter),
        ],
        [
            Paragraph('из него: инсулиннезависимый сахарный диабет', styleSign),
            Paragraph('3.1', styleTCenter),
            Paragraph('Е11', styleTCenter),
        ],
        [
            Paragraph('Преходящие церебральные ишемические приступы (атаки) и родственные синдромыvv', styleSign),
            Paragraph('04', styleTCenter),
            Paragraph('G45', styleTCenter),
        ],
        [
            Paragraph('Старческая катаракта и другие катаракты', styleSign),
            Paragraph('05', styleTCenter),
            Paragraph('Н25, Н26', styleTCenter),
        ],
        [
            Paragraph('Глаукома', styleSign),
            Paragraph('06', styleTCenter),
            Paragraph('Н40', styleTCenter),
        ],
        [
            Paragraph('Слепота и пониженное зрение', styleSign),
            Paragraph('07', styleTCenter),
            Paragraph('Н54', styleTCenter),
        ],
        [
            Paragraph('Кондуктивная и нейросенсорная потеря слуха', styleSign),
            Paragraph('08', styleTCenter),
            Paragraph('Н90', styleTCenter),
        ],
        [
            Paragraph('Болезни системы кровообращения', styleSign),
            Paragraph('09', styleTCenter),
            Paragraph('I00-I99', styleTCenter),
        ],
        [
            Paragraph('из них: болезни, характеризующиеся повышенным кровяным давлением', styleSign),
            Paragraph('9.1', styleTCenter),
            Paragraph('I10-I13', styleTCenter),
        ],
        [
            Paragraph('ишемические болезни сердца', styleSign),
            Paragraph('9.2', styleTCenter),
            Paragraph('I20-I25', styleTCenter),
        ],
        [
            Paragraph('цереброваскулярные болезни', styleSign),
            Paragraph('9.3', styleTCenter),
            Paragraph('I60-I69', styleTCenter),
        ],
        [
            Paragraph('из них: закупорка и стеноз прецеребральных и (или) церебральных артерий, не приводящие к инфаркту мозга', styleSign),
            Paragraph('9.4', styleTCenter),
            Paragraph('I65, I66', styleTCenter),
        ],
        [
            Paragraph('Болезни органов дыхания', styleSign),
            Paragraph('10', styleTCenter),
            Paragraph('J00-J99', styleTCenter),
        ],
        [
            Paragraph('Бронхит, не уточненный как острый и хронический, ' 'простой и слизисто-гнойный хронический бронхит, хронический бронхит неуточненный, эмфизема', styleSign),
            Paragraph('10.1', styleTCenter),
            Paragraph('J40-J43', styleTCenter),
        ],
        [
            Paragraph('Другая хроническая обструктивная легочная болезнь, астма, астматический статус, бронхоэктатическая болезнь', styleSign),
            Paragraph('10.2', styleTCenter),
            Paragraph('J44-J47', styleTCenter),
        ],
        [
            Paragraph('Болезни органов пищеварения', styleSign),
            Paragraph('11', styleTCenter),
            Paragraph('К00-К93', styleTCenter),
        ],
        [
            Paragraph('язва желудка, язва двенадцатиперстной кишки', styleSign),
            Paragraph('11.1', styleTCenter),
            Paragraph('К25, К26', styleTCenter),
        ],
        [
            Paragraph('гастрит и дуоденит', styleSign),
            Paragraph('12', styleTCenter),
            Paragraph('К29', styleTCenter),
        ],
        [
            Paragraph('Прочие', styleSign),
            Paragraph('13', styleTCenter),
            Paragraph('', styleTCenter),
        ],
    ]

    row_height = []
    for i in opinion:
        row_height.append(None)

    tbl = Table(
        opinion,
        colWidths=(
            55 * mm,
            10 * mm,
            20 * mm,
            20 * mm,
            25 * mm,
            30 * mm,
            30 * mm,
        ),
        rowHeights=row_height,
    )

    table_style = [
        ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('SPAN', (2, 20), (2, 22)),
        ('SPAN', (2, 23), (2, 25)),
    ]
    table_style += [('SPAN', (2, 4 + (i * 2)), (2, 4 + (i * 2) + 1)) for i in range(8)]

    tbl.setStyle(TableStyle(table_style))
    objs.append(tbl)

    objs.append(
        Paragraph(
            '19. Диспансерное наблюдение установлено:',
            style,
        )
    )
    objs.append(
        Paragraph(
            '19.1. врачом (фельдшером) отделения (кабинета) медицинской профилактики или центра здоровья: да - 1; нет - 2.',
            style,
        )
    )
    objs.append(
        Paragraph(
            'Если "да", N строки таблицы пункта 18 ________________',
            style,
        )
    )
    objs.append(
        Paragraph(
            '19.2. врачом-терапевтом: да - 1; нет - 2. Если "да", N строки таблицы пункта 18 _______________________',
            style,
        )
    )
    objs.append(
        Paragraph(
            '19.3. врачом-специалистом: да - 1; нет - 2. Если "да", N строки таблицы пункта 18 _____________________',
            style,
        )
    )
    objs.append(
        Paragraph(
            '19.4. фельдшером фельдшерского здравпункта или фельдшерско-акушерского пункта: да - 1; нет - 2.' 'Если "да", N строки таблицы пункта 18 _________________________',
            style,
        )
    )
    objs.append(
        Paragraph(
            f'20. Группа  здоровья: {data["20. Группа здоровья:"]}',
            style,
        )
    )
    objs.append(
        Paragraph(
            '21. Уровень артериального давления ниже 140/90 мм рт. ст. на фоне приема гипотензивных лекарственных препаратов'
            'при наличии болезней, характеризующихся повышенным кровяным давлением (коды I10-I15 по МКБ-10): да- 1; нет - 2',
            style,
        )
    )
    objs.append(
        Paragraph(
            '22. Направлен   при  наличии  медицинских   показаний   на   дополнительное   обследование,   не  входящее  в объем'
            'диспансеризации,  в том числе  направлен   на  осмотр (консультацию)  врачом-онкологом  при  подозрении на онкологическое заболевание: да - 1; нет - 2',
            style,
        )
    )
    objs.append(
        Paragraph(
            'Если "да", дата направления "___"___________ 20__ г',
            style,
        )
    )
    objs.append(
        Paragraph(
            '23. Направлен для получения специализированной, в том числе высокотехнологичной, медицинской помощи: да - 1; нет - 2',
            style,
        )
    )
    objs.append(
        Paragraph(
            'Если "да", дата направления "___"___________ 20__ г',
            style,
        )
    )
    objs.append(
        Paragraph(
            '24. Направлен на санаторно-курортное лечение: да - 1; нет - 2',
            style,
        )
    )

    objs.append(Spacer(1, 10 * mm))
    objs.append(HRFlowable(width=190 * mm, spaceAfter=0.3 * mm, spaceBefore=0.5 * mm, color=colors.black))

    objs.append(
        Paragraph(
            'Ф.И.О. и подпись врача (фельдшера) отделения (кабинета) медицинской профилактики  (центра здоровья),   а    в случае  отсутствия в'
            'медицинской  организации  отделения  (кабинета)  медицинской профилактики - фельдшера, врача-терапевта, являющегося ответственным'
            'за организацию и проведение профилактического медицинского осмотра (диспансеризации) на участке<sup>2</sup>.',
            style,
        )
    )

    objs.append(Spacer(1, 35 * mm))
    objs.append(
        Paragraph(
            '<sup>1</sup> Международная статистическая классификация болезней и проблем, связанных со здоровьем, 10-го пересмотра (далее - МКБ - 10).',
            styleSmallFont,
        )
    )

    objs.append(
        Paragraph(
            '<sup>2</sup> Абзацы третий и четвертый пункта 12 порядка проведения профилактического медицинского осмотра и диспансеризации определенных групп'
            'взрослого населения, утвержденного приказом Министерства здравоохранения Российской Федерации от 13 марта 2019 г. N 124н "Об утверждении порядка'
            'проведения профилактического медицинского осмотра и диспансеризации определенных групп взрослого населения" (зарегистрирован Министерством'
            'юстиции Российской Федерации 24 апреля 2019 г., регистрационный N 54495), с изменениями, внесенными приказом Министерства здравоохранения'
            'Российской Федерации 2 сентября 2019 г. N 716н (зарегистрирован Министерством юстиции Российской Федерации 16 октября 2019 г., регистрационный '
            '№ 56254).',
            styleSmallFont,
        )
    )
    fwb.extend(objs)

    return fwb


def title_fields(iss):
    title_fields = [
        "гинеколог проведено",
        "гинеколог отказ",
        "гинеколог ранее",
        "гинеколог патология",
        "терапевт 2 патология",
        "терапевт 2 проведено",
        "терапевт 2 отказ",
        "направление онко проведено",
        "направление онко отказ",
        "направление онко патология",
        "04 Нерациональное питание (Z72.4)",
        "R54",
        "ЗНО тонкого кишечника С17 из них в 1-2 стадии наличие",
        "ЗНО тонкого кишечника С17 из них в 1-2 стадии поставлен",
        "ЗНО тонкого кишечника С17 из них в 1-2 стадии впервые",
        "ЗНО тонкого кишечника С17 из них в 1-2 стадии впервые поставлен",
        "ЗНО ободочной кишки С18 наличие",
        "ЗНО ободочной кишки С18 поставлен",
        "ЗНО ободочной кишки С18 впервые",
        "ЗНО ободочной кишки С18 впервые поставлен",
        "ЗНО ободочной кишки С18 из них в 1-2 стадии вперве",
        "ЗНО ободочной кишки С18 из них в 1-2 стадии впервые поставлен",
        "ЗНО ободочной кишки С18 из них в 1-2 стадии наличие",
        "ЗНО ободочной кишки С18 из них в 1-2 стадии поставлен",
        "ЗНО прямой кишки -2 стадии впервые",
        "ЗНО прямой кишки -2 стадии впервые поставлен",
        "ЗНО прямой кишки -2 стадии наличие",
        "ЗНО прямой кишки -2 стадии поставлен",
        "Заполнить",
        "ЗНО наличие",
        "ЗНО установление",
        "ЗНО впервые выявлен",
        "ЗНО впервые установлен",
        "ЗНО губы, полости рта и глотки - наличие",
        "ЗНО губы, полости рта и глотки - поставлен",
        "ЗНО губы, полости рта и глотки - впервые выявлен",
        "ЗНО губы, полости рта и глотки - впервые поставлен",
        "ЗНО губы, полости рта и глотки из них в 1-2 стадии - впервые выявлен",
        "ЗНО губы, полости рта и глотки из них в 1-2 стадии - наличие",
        "ЗНО губы, полости рта и глотки из них в 1-2 стадии - поставлен",
        "ЗНО губы, полости рта и глотки из них в 1-2 стадии - впервые поставлен",
        "ЗНО пищевода из них в 1-2 стадии С15 - поставлен",
        "ЗНО пищевода из них в 1-2 стадии С15 -впервые",
        "ЗНО пищевода из них в 1-2 стадии С15 - впервые поставлен",
        "ЗНО пищевода из них в 1-2 стадии С15 - наличие",
        "ЗНО желудка С16 - наличие",
        "ЗНО желудка С16 - впервые",
        "ЗНО желудка С16 впервые поставлен",
        "ЗНО желудка С16 - поставлен",
        "ЗНО желудка С16 из них в 1-2 стадии - наличие",
        "ЗНО желудка С16 из них в 1-2 стадии - поставлен",
        "ЗНО желудка С16 из них в 1-2 стадии - впервые",
        "ЗНО желудка С16 из них в 1-2 стадии - впервые поставлен",
        "ЗНО трахеи, бронхов, легкого наличие",
        "ЗНО трахеи, бронхов, легкого поставлен",
        "ЗНО трахеи, бронхов, легкого впервые",
        "ЗНО трахеи, бронхов, легкого впервые поставлен",
        "ЗНО трахеи, 1-2 стадии С33, С34 наличие",
        "ЗНО трахеи, 1-2 стадии С33, С34 поставлен",
        "ЗНО трахеи, 1-2 стадии С33, С34 впервые",
        "ЗНО трахеи, 1-2 стадии С33, С34 впервые поставлен",
        "ЗНО кожи С43-С44 из них в 1-2 стадии наличие",
        "ЗНО кожи С43-С44 из них в 1-2 стадии поставлен",
        "ЗНО кожи С43-С44 из них в 1-2 стадии впервые",
        "ЗНО кожи С43-С44 из них в 1-2 стадии впервые поставлен",
        "ЗНО молочной железы С50 наличие",
        "ЗНО молочной железы С50 поставлен",
        "ЗНО молочной железы С50 впервые",
        "ЗНО молочной железы С50 впервые поставлен",
        "С50 из них в 0-1 стадии наличие",
        "С50 из них в 0-1 стадии поставлен",
        "С50 из них в 0-1 стадии впервые",
        "С50 из них в 0-1 стадии впервые поставлен",
        "ЗНО С50 из них 2 стадии впервые поставлен",
        "ЗНО С50 из них 2 стадии наличие",
        "ЗНО С50 из них 2 стадии поставлен",
        "ЗНО С50 из них 2 стадии впервые",
        "ЗНО шейки матки С53 наличие",
        "ЗНО шейки матки С53 поставлен",
        "ЗНО шейки матки С53 впервые",
        "ЗНО шейки матки С53 впервые поставлен",
        " С53 из них в 0-1 стадии наличе",
        " С53 из них в 0-1 стадии поставлен",
        " С53 из них в 0-1 стадии впервые",
        " С53 из них в 0-1 стадии впервые поставлен",
        "С53 из них 2 стадии наличие",
        "С53 из них 2 стадии поставлен",
        "С53 из них 2 стадии впервые",
        "С53 из них 2 стадии впервые поставлен",
        "С61 наличие",
        "С61 впервые поставлен",
        "С61 поставлен",
        "С61 впервые",
        "С61 из них в 1-2 стадии наличие",
        "С61 из них в 1-2 стадии поставлен",
        "С61 из них в 1-2 стадии впервые",
        "С61 из них в 1-2 стадии впервые поставлен",
        "Сахарный диабет Е10-Е14 наличие",
        "Сахарный диабет Е10-Е14 впервые поставлен",
        "Сахарный диабет Е10-Е14 поставлен",
        "Сахарный диабет Е10-Е14 впервые",
        "консультирование 65 плюс отказ",
        "консультирование 65 плюс выявлено",
        "консультирование 65 плюс проведено",
        "консультирование 65 плюс ранее",
        "консультирование 65 плюс патология",
        "Туберкулез наличие",
        "Туберкулез установление",
        "Туберкулез впервые выявлен",
        "Туберкулез впервые установлен",
        "ЗНО тонкого кишечника С17 впервые",
        "ЗНО тонкого кишечника С17 - наличие",
        "ЗНО тонкого кишечника С17 впервые поставлен",
        "ЗНО тонкого кишечника С17 поставлен",
        "ЗНО , прямой кишки наличие",
        "ЗНО , прямой кишки наличие поставлен",
        "ЗНО , прямой кишки наличие впервые",
        "ЗНО , прямой кишки наличие впервые поставлен",
        "Болезни органов пищеварения K00-K93 наличие",
        "Болезни органов пищеварения K00-K93 поставлен",
        "Болезни органов пищеварения K00-K93 впервые",
        "Болезни органов пищеварения K00-K93 впервые поставлен",
        "Флюра выявлено",
        "Флюра проведено",
        "Флюра отказ",
        "Флюра ранее",
        "Флюра патология",
        "КТ легких выявлено",
        "КТ легких проведено",
        "КТ легких отказ",
        "КТ легких ранее",
        "КТ легких патология",
        "Спирометрия выявлено",
        "Спирометрия проведено",
        "Спирометрия отказ",
        "Спирометрия ранее",
        "Спирометрия патология",
        "Гинеколог отказ",
        "Гинеколог выявлено",
        "Гинеколог проведено",
        "Гинеколог патология",
        "Гинеколог ранее",
        "лор выявлено",
        "лор проведено",
        "лор отказ",
        "лор  ранее",
        "лор патология",
        "Окулист отказ",
        "Окулист проведено",
        "Окулист ранее",
        "Окулист патология",
        "Окулист выявлено",
        "консультирование для граждан с ИБС выявлено",
        "консультирование для граждан с ИБС проведено",
        "консультирование для граждан с ИБС отказ",
        "консультирование для граждан с ИБС ранее",
        "консультирование для граждан с ИБС птаология",
        "02 Гипергликемия (R73.9)",
        "экг проведено",
        "экг отказ",
        "экг ранее",
        "экг патология",
        "Колоноскопия выявлено",
        "Колоноскопия проведено",
        "Колоноскопия отказ",
        "Колоноскопия ранее",
        "Колоноскопия патология",
        "Дата окончания первого этапа диспансеризации",
        "Дата окончания второго этапа диспансеризации",
        "01 Гиперхолестеринемия (Е78)",
        "03 Курение табака (Z72.0)",
        "05 Избыточная масса тела (R63.5)",
        "06 Ожирение (Е66)",
        "ЗНО пищевода С15 - поставлен",
        "ЗНО пищевода С15 - впервые вявлен",
        "ЗНО пищевода С15 - впервы поставлен",
        "ЗНО пищевода С15 - наличие",
        "Бронхит J40-J43 наличие ",
        "Бронхит J40-J43 поставлен",
        "Бронхит J40-J43 впервые",
        "Бронхит J40-J43 впервые поставлен",
        "астма J44-J47 наличие",
        "астма J44-J47 поставлен",
        "астма J44-J47 впервые",
        "астма J44-J47 впервые поставлен",
        "язва желудка K25, K26 наличие",
        "язва желудка K25, K26 поставлен",
        "язва желудка K25, K26 впервыеязва желудка K25, K26 впервые",
        "язва желудка K25, K26 впервые упоставлен",
        "гастрит и дуоденит K29 наличие",
        "гастрит и дуоденит K29 поставлен",
        "гастрит и дуоденит K29 впервые",
        "гастрит и дуоденит K29 впервые поставлен",
        "фгдс отказ",
        "фгдс проведено",
        "фгдс ранее",
        "фгдс патология",
        "невролог выявлено",
        "невролог проведено",
        "невролог отказ",
        "невролог ранее",
        "невролог патология",
        "консультирование граждан с высокими рисками выявлено",
        "консультирование граждан с высокими рисками проведено",
        "консультирование граждан с высокими рисками отказ",
        "консультирование граждан с высокими рисками ранее",
        "консультирование граждан с высокими рисками патология",
        "07 Низкая физическая активность (Z72.3)",
        "08 Риск пагубного потребления алкоголя (Z72.1)",
        "09 Риск потребления наркотических средств и психотропных веществ без назначения врача (Z72.2)",
        "12 колоректальной области (Z80.0)",
        "13 других локализации (Z80.9)",
        "нижних дыхательных путей (Z82.5)",
        "Z83.3",
        "Абсолютный С-С риск",
        "Относительный С-С риск",
        "ФГДС выявлено",
        "ФГДС проведено",
        "ФГДС отказ",
        "ФГДС ранее",
        "ФГДС патология",
        "ЗНО кожи С43-С44 наличие",
        "ЗНО кожи С43-С44 поставлен",
        "ЗНО кожи С43-С44 впервые",
        "ЗНО кожи С43-С44 впервые поставлен",
        "врачом (фельдшером)",
        "врач N строки таблицы пункта 18",
        "19.2. врачом-терапевтом",
        "терапевт N строки таблицы пункта 18",
        "19.3. врачом-специалистом",
        "врачом-специалистом N строки таблицы пункта 18",
        "20. Группа здоровья:",
        "Уровень АД",
        "дата направления допобследования",
        "Направлен на допобследование",
        "Направление СМП/ВМП",
        "дата направления СМП",
        "Направление на санкур",
        "рост (см)",
        "Медосмотр (1 этап) мобильно",
        "Дата начала ",
        "ФИО пациента",
        "Пол",
        "Дата рождения",
        "Местность",
        "Адрес регистрации",
        "Код категории льготы",
        "Глюкоза",
        "Принадлежность малочисленным народам ",
        "Занятость",
        "масса тела (кг)",
        "ИМТ",
        "АД (мм рт.ст)",
        "прием гипотензивных ЛП",
        "внутриглазное давление (мм рт.ст.)",
        "Холестерин (ммоль/л)",
        "Прием гипогликемических ЛП",
        "Прием гиполипидемических ЛП",
        "относительный С-С риск (%)",
        "абсолютный С-С риск (%)",
        "Анкета проведено",
        "Анкета отказ",
        "Анкета ранее",
        "Анкета патология",
        "антропометрия проведено",
        "антропометрия отказ",
        "антропометрия ранее",
        "антропометрия патология",
        "давление проведено",
        "давление отказ",
        "давление ранее",
        "давление патология",
        "холестерин проведено",
        "холестерин ранее",
        "холестерин патология",
        "холестерин отказ",
        "глюкоза проведено",
        "глюкоза отказ",
        "глюкоза раннее",
        "глюкоза патология",
        "относительный проведено",
        "относительный ранее",
        "относительный патология",
        "относительный отказ",
        "тонометрия проведено",
        "тонометрия отказ",
        "тонометрия ранее",
        "тонометрия патология",
        "мазок ранее",
        "мазок отказ",
        "мазок проведено",
        "мазок патология",
        "маммография проведено",
        "маммография отказ",
        "маммография ранее",
        "маммография патология",
        "Исследование кала от 40 до 64 лет проведено",
        "Исследование кала от 40 до 64 лет отказ",
        "Исследование кала от 40 до 64 лет ранее",
        "Исследование кала от 40 до 64 лет патология",
        "Исследование кала от 65 до 75 лет проведено",
        "Исследование кала от 65 до 75 лет отказ",
        "Исследование кала от 65 до 75 лет ранее",
        "Исследование кала от 65 до 75 лет патология",
        "простат",
        "простат проведено",
        "простат ранее",
        "простат отказ",
        "оак ранее",
        "оак патология",
        "оак проведено",
        "оак отказ",
        "краткое проведено",
        "краткое отказ",
        "краткое ранее",
        "краткое патология",
        "центр здоровья отказ",
        "центр здоровья проведено",
        "центр здоровья патология",
        "Дуплексное сканирование проведено",
        "Дуплексное сканирование отказ",
        "Дуплексное сканирование выявлено",
        "Дуплексное сканирование ранее",
        "Дуплексное сканирование патология",
        "Медицинский осмотр проведен",
        "абсолютное проведено",
        "абсолютное отказ",
        "абсолютное ранее",
        "абсолютное патология",
        "флюра проведено",
        "флюра ранее",
        "флюра патология",
        "флюра отказ",
        "Направлен на второй этап",
        "Инсулиннезависимый сахарный диабет Е11 наличие",
        "Инсулиннезависимый сахарный диабет Е11 поставлен",
        "Инсулиннезависимый сахарный диабет Е11 впервые",
        "Инсулиннезависимый сахарный диабет Е11 впервые поставлен",
        "СД ишемические приступы G45 наличие",
        "СД ишемические приступы G45 впервые",
        "СД ишемические приступы G45 впервые поставлен",
        "СД ишемические приступы G45 поставлен",
        "Старческая катаракта и другие катаракты Н25, Н26 наличие",
        "Старческая катаракта и другие катаракты Н25, Н26 поставлен",
        "Старческая катаракта и другие катаракты Н25, Н26 впервые",
        "Старческая катаракта и другие катаракты Н25, Н26 впервые поставлен",
        "Глаукома Н40 поставлен",
        "Глаукома Н40 впервые",
        "Глаукома Н40 впервые поставлен",
        "Глаукома Н40 наличие",
        "Слепота и пониженное зрение Н54 наличие",
        "Слепота и пониженное зрение Н54 поставлен",
        "Слепота и пониженное зрение Н54 впервые",
        "Слепота и пониженное зрение Н54 впервые поставлен",
        "Кондуктивная и нейросенсорная потеря слуха Н90 наличие",
        "Кондуктивная и нейросенсорная потеря слуха Н90 поставлен",
        "Кондуктивная и нейросенсорная потеря слуха Н90 впервые",
        "Кондуктивная и нейросенсорная потеря слуха Н90 впервые поставлен",
        "Болезни системы кровообращения I00-I99 поставлен",
        "Болезни системы кровообращения I00-I99 впервые",
        "Болезни системы кровообращения I00-I99 впервые поставлен",
        "Болезни системы кровообращения I00-I99 наличие",
        "Повышенным кровяным давлением I10-I13 наличие",
        "Повышенным кровяным давлением I10-I13 поставлен",
        "Повышенным кровяным давлением I10-I13 впервые",
        "Повышенным кровяным давлением I10-I13 впервые поставлен",
        "Ишемические болезни сердца I20-I25 наличие",
        "Ишемические болезни сердца I20-I25 поставлен",
        "Ишемические болезни сердца I20-I25 впервые",
        "Ишемические болезни сердца I20-I25 впервые поставлен",
        "Цереброваскулярные болезни I60-I69 поставлен",
        "Цереброваскулярные болезни I60-I69 впервые",
        "Цереброваскулярные болезни I60-I69 впервые поставлен",
        "Цереброваскулярные болезни I60-I69 наличие",
        "е приводящие к инфаркту мозга I65, I66 наличие",
        "е приводящие к инфаркту мозга I65, I66 поставлен",
        "е приводящие к инфаркту мозга I65, I66 впервые",
        "е приводящие к инфаркту мозга I65, I66 впервые поставлен",
        "Болезни органов дыхания J00-J99 поставлен",
        "Болезни органов дыхания J00-J99 впервые",
        "Болезни органов дыхания J00-J99 впервые поставлен",
        "Болезни органов дыхания J00-J99 наличие",
        "10 инфаркт миокарда (Z82.4)",
        "11 мозговой инсульт (Z82.3)",
        "терапевт от 18 лет до 39 лет проведено",
        "терапевт от 18 лет до 39 лет отказ",
        "терапевт от 18 лет до 39 лет патология",
        "терапевт от 40 лет и старше проведено",
        "терапевт от 40 лет и старше отказ",
        "терапевт от 40 лет и старше патология",
        "онко проведено",
        "онко отказ",
        "онко патология",
        "Хирург-уролог отказ",
        "Хирург-уролог выявлено",
        "Хирург-уролог проведено",
        "Хирург-уролог ранее",
        "Хирург-уролог патология",
        "хирург-колопроктолог выявлено",
        "хирург-колопроктолог проведено",
        "хирург-колопроктолог отказ",
        "хирург-колопроктолог ранее",
        "хирург-колопроктолог патология",
        "нарколыги выявлено",
        "нарколыги проведено",
        "нарколыги отказ",
        "нарколыги ранее",
        "нарколыги патология",
        "Факторы риска",
        "Холестерин (ммоль/л), Холестерин общий" "Глюкоза, Глюкоза",
    ]

    result = fields_result_only_title_fields(iss, title_fields, False)
    data = {i['title']: i['value'] for i in result}

    for t in title_fields:
        if not data.get(t, None):
            data[t] = ""

    return data
