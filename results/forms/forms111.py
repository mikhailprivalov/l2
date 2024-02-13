import json

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from results.prepare_data import fields_result_only_title_fields
from directions.models import Issledovaniya, Napravleniya
from laboratory.settings import FONTS_FOLDER
import os.path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from laboratory.utils import current_time


def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None, **kwargs):
    """
    Карта профилактического медицинского осмотра несовершеннолетнего Учетная форма N 030-ПО/у-17
    к приказу Министерства здравоохранения Российской Федерации от 10 августа 2017 г. N 514н
    """

    pdfmetrics.registerFont(TTFont("PTAstraSerifBold", os.path.join(FONTS_FOLDER, "PTAstraSerif-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("PTAstraSerifReg", os.path.join(FONTS_FOLDER, "PTAstraSerif-Regular.ttf")))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 11
    style.leading = 12
    style.spaceAfter = 1.2 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = 15

    styleFL = deepcopy(style)
    styleFL.firstLineIndent = 0

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleBold.firstLineIndent = 0

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.spaceAfter = 0 * mm

    styleRight = deepcopy(style)
    styleRight.aligment = TA_RIGHT

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.firstLineIndent = 0
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 13
    styleCenterBold.face = "PTAstraSerifBold"

    styleTableCentre = deepcopy(style)
    styleTableCentre.alignment = TA_CENTER
    styleTableCentre.spaceAfter = 4.5 * mm
    styleTableCentre.fontSize = 8
    styleTableCentre.leading = 4.5 * mm

    styleT = deepcopy(style)
    styleT.firstLineIndent = 0

    objs = []
    opinion = [
        [
            Paragraph("", styleFL),
            Paragraph(
                "Приложение №2<br/> "
                "к приказу Министерства<br/>здравоохранения Российской Федерации<br/>"
                "от 10 августа 2017 г. № 514н<br/><br/>"
                "Медицинская документация<br/> Учетная форма № 030-ПО/у-17",
                styleFL,
            ),
        ],
    ]
    tbl = Table(
        opinion,
        colWidths=(
            70 * mm,
            110 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.75, colors.white),
                ("LEFTPADDING", (1, 0), (-1, -1), 35 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    objs.append(tbl)

    title_fields = ["Дата начала", "Диагноз", "Группа здоровья", "Главный врач"]
    result = fields_result_only_title_fields(iss, title_fields, False)
    data = {}
    for i in result:
        data[i["title"]] = i["value"]

    objs.append(Spacer(1, 3 * mm))
    objs.append(
        Paragraph(
            "Карта учета <br/> профилактического медицинского осмотра несовершеннолетнего",
            styleCenterBold,
        )
    )
    objs.append(Spacer(1, 3 * mm))
    patient_data = direction.client.get_data_individual()
    objs.append(
        Paragraph(
            f"1. Фамилия, имя, отчество (при наличии) несовершеннолетнего: <u>{direction.client.individual.fio()}</u>",
            style,
        )
    )
    if direction.client.individual.sex.lower() == "ж":
        sex = "муж. / <u>жен.</u>"
    else:
        sex = "<u>муж.</u> / жен."

    objs.append(
        Paragraph(
            f"Пол: {sex} (нужное подчеркнуть)",
            style,
        )
    )

    objs.append(
        Paragraph(
            f"Дата рождения: <u>{direction.client.individual.bd()}</u>",
            style,
        )
    )

    objs.append(
        Paragraph(
            "2. Полис обязательного медицинского страхования: серия ______" f"№ <u>{patient_data['enp']}</u>",
            style,
        )
    )

    objs.append(
        Paragraph(
            f"Страховая медицинская организация: <u>{patient_data['oms']['polis_issued']}</u>",
            style,
        )
    )

    objs.append(
        Paragraph(
            f"3. Страховой номер индивидуального лицевого счета <u>{patient_data['snils']}</u>",
            style,
        )
    )

    objs.append(
        Paragraph(
            f"4. Адрес места жительства (пребывания): <u>{patient_data['main_address']}</u>",
            style,
        )
    )

    objs.append(
        Paragraph(
            "5. Категория: ребенок-сирота; ребенок, оставшийся без попечения родителей; ребенок, находя-щийся в трудной жизненной ситуации; нет категории (нужное подчеркнуть).",
            style,
        )
    )

    objs.append(
        Paragraph(
            "6. Полное наименование медицинской организации, в которой несовершеннолетний получает первичную медико-санитарную помощь:" f" {iss.doc_confirmation.hospital.title}",
            style,
        )
    )
    objs.append(
        Paragraph(
            "7. Адрес места нахождения медицинской организации, в которой несовершеннолетний получает первичную медико - санитарную помощь: "
            f" {iss.doc_confirmation.hospital.safe_address}",
            style,
        )
    )
    objs.append(
        Paragraph(
            "8. Полное наименование образовательной организации, в которой обучается несовершеннолетний:",
            style,
        )
    )
    objs.append(
        Paragraph(
            "9. Адрес места нахождения образовательной организации, в которой обучается несовершеннолетний:",
            style,
        )
    )
    objs.append(
        Paragraph(
            f"10. Дата начала профилактического медицинского осмотра несовершеннолетнего (далее - профилактический осмотр): <u>{data.get('Дата осомтра', '')}</u>",
            style,
        )
    )
    objs.append(
        Paragraph(
            "11. Полное наименование и адрес места нахождения медицинской организации, проводившей профилактический осмотр:"
            f" <u>{iss.doc_confirmation.hospital.title} {iss.doc_confirmation.hospital.safe_address}</u>",
            style,
        )
    )
    objs.append(
        Paragraph(
            "12. Оценка физического развития с учётом возраста на момент профилактического осмотра:",
            style,
        )
    )
    objs.append(
        Paragraph(
            "12.1. Для детей в возрасте 0—4 лет: масса (кг)		; рост (см)		; окружность",
            style,
        )
    )
    objs.append(
        Paragraph(
            "головы (см)		; физическое развитие нормальное, с нарушениями (дефицит массы тела,",
            style,
        )
    )
    objs.append(
        Paragraph(
            "избыток массы тела, низкий рост, высокий рост — нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "12.2. Для детей в возрасте 5—17 лет включительно: масса (кг)		; рост (см)		;",
            style,
        )
    )
    objs.append(
        Paragraph(
            "нормальное, с нарушениями (дефицит массы тела, избыток массы тела, низкий рост, высокий рост ;",
            style,
        )
    )
    objs.append(
        Paragraph(
            "— нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "13. Оценка психического развития (состояния):",
            style,
        )
    )
    objs.append(
        Paragraph(
            "13.1. Для детей в возрасте 0—4 лет:",
            style,
        )
    )
    objs.append(
        Paragraph(
            "познавательная функция (возраст развития)_________		;",
            style,
        )
    )
    objs.append(
        Paragraph(
            "моторная функция (возраст развития)_________;",
            style,
        )
    )
    objs.append(
        Paragraph(
            "эмоциональная и социальная (контакт с окружающим миром) функции (возраст развития);",
            style,
        )
    )
    objs.append(
        Paragraph(
            "предречевое и речевое развитие (возраст развития)____________",
            style,
        )
    )
    objs.append(
        Paragraph(
            "13.2. Для детей в возрасте 5—17 лет:",
            style,
        )
    )
    objs.append(
        Paragraph(
            "13.2.1. Психомоторная сфера: (норма, нарушения) (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "13.2.2. Интеллект: (норма, нарушения) (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "13.2.3. Эмоционально-вегетативная сфера: (норма, нарушения) (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "14. Оценка полового развития (с 10 лет):",
            style,
        )
    )
    objs.append(
        Paragraph(
            "14.1. Половая формула мальчика: Р		Ах		Fa		.",
            style,
        )
    )
    objs.append(
        Paragraph(
            "14.2. Половая формула девочки:	Р		Ах		Ма		Me		;",
            style,
        )
    )
    objs.append(
        Paragraph(
            "характеристика менструальной функции: menarhe (лет, месяцев)		;",
            style,
        )
    )
    objs.append(
        Paragraph(
            "menses (характеристика): регулярные, нерегулярные, обильные, умеренные, скудные, болезненные и безболезненные (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "15. Состояние здоровья до проведения настоящего профилактического осмотра:",
            style,
        )
    )
    objs.append(
        Paragraph(
            "15.1. Практически здоров ______________________________________ (код по МКБ ).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "15.2. Диагноз ______________________________________ 		 (код по МКБ).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "15.2.1. Диспансерное наблюдение установлено: да, нет (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "15.3. Диагноз ______________________________________ 		 (код по МКБ).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "15.3.1. Диспансерное наблюдение установлено: да, нет (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "15.4. Диагноз ______________________________________ 		 (код по МКБ).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "15.4.1. Диспансерное наблюдение установлено: да, нет (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "15.5. Диагноз ______________________________________ 		 (код по МКБ).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "15.5.1. Диспансерное наблюдение установлено: да, нет (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "15.6. Диагноз ______________________________________ 		 (код по МКБ).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "15.6.1. Диспансерное наблюдение установлено: да, нет (нужное подчеркнуть).",
            style,
        )
    )
    health_group_I, health_group_II, health_group_III, health_group_IV, health_group_V = "I", "II", "III", "IV", "V"
    if data["Группа здоровья"] == "I":
        health_group_I = "<u>I</u>"
    elif data["Группа здоровья"] == "II":
        health_group_II = "<u>II</u>"
    elif data["Группа здоровья"] == "III":
        health_group_III = "<u>III</u>"
    elif data["Группа здоровья"] == "IV":
        health_group_IV = "<u>IV</u>"
    elif data["Группа здоровья"] == "V":
        health_group_V = "<u>V</u>"

    objs.append(
        Paragraph(
            f"15.7. Группа здоровья: {health_group_I}, {health_group_II}, {health_group_III}, {health_group_IV}, {health_group_V} (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "15.8. Медицинская группа для занятий физической культурой: I, II, III, IV, не допущен (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16. Состояние здоровья по результатам проведения настоящего профилактического осмотра:",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.1. Практически здоров ______________________________________ 		 (код по МКБ).",
            style,
        )
    )
    diagnos = json.loads(data["Диагноз"])
    objs.append(
        Paragraph(
            f"16.2. Диагноз {diagnos.get('code')} {diagnos.get('title')}	 (код по МКБ).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.2.1. Диагноз установлен впервые: да, <u>нет</u> (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.2.2. Диспансерное наблюдение: <u>установлено ранее</u>, установлено впервые, не установлено (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.2.3. Дополнительные консультации и исследования назначены: да, нет (нужное подчеркнуть); если «да»: в амбулаторных условиях, в условиях дневного стационара, "
            "в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.2.4. Дополнительные консультации и исследования выполнены: да, нет (нужное подчеркнуть); если «да»: в амбулаторных условиях, в условиях дневного стационара, "
            "в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.2.5. Лечение назначено: да, нет (нужное подчеркнуть); если «да»: в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.2.6. Медицинская реабилитация и (или) санаторно-курортное лечение назначены: да, нет (нуж-ное подчеркнуть); если «да»: "
            "в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            f"16.3. Диагноз {diagnos.get('code')} {diagnos.get('title')} (код по МКБ):",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.3.1. Диагноз установлен впервые: да, <u>нет</u> (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.3.2. Диспансерное наблюдение: <u>установлено ранее</u>, установлено впервые, не установлено (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.3.3. Дополнительные консультации и исследования назначены: да, нет (нужное подчеркнуть); если «да»: "
            "в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.3.4. Дополнительные консультации и исследования выполнены: да, нет (нужное подчеркнуть); если «да»: "
            "в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.3.5. Лечение назначено: да, нет (нужное подчеркнуть); если «да»: в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.3.6. Медицинская реабилитация и (или) санаторно-курортное лечение назначены: да, нет (нуж-ное подчеркнуть); если «да»: "
            "в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.4. Диагноз ______________________________________ (код по МКБ):",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.4.1. Диагноз установлен впервые: да, нет (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.4.2. Диспансерное наблюдение: установлено ранее, установлено впервые, не установлено (нужное подчеркнуть);",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.4.3. Дополнительные консультации и исследования назначены: да, нет (нужное подчеркнуть); если «да»: "
            "в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.4.4. Дополнительные консультации и исследования выполнены: да, нет (нужное подчеркнуть); если «да»: "
            "в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.4.5. Лечение назначено: да, нет (нужное подчеркнуть); если «да»: в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.4.6. Медицинская реабилитация и (или) санаторно-курортное лечение назначены: да, нет (нуж-ное подчеркнуть); если «да»: "
            "в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.5. Диагноз ______________________________________ (код по МКБ):",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.5.1. Диагноз установлен впервые: да, нет (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.5.2. Диспансерное наблюдение: установлено ранее, установлено впервые, не установлено (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.5.3. Дополнительные консультации и исследования назначены: да, нет (нужное подчеркнуть); если «да»: "
            "в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.5.4. Дополнительные консультации и исследования выполнены: да, нет (нужное подчеркнуть); если «да»: "
            "в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.5.5. Лечение назначено: да, нет (нужное подчеркнуть); если «да»: в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.5.6. Медицинская реабилитация и (или) санаторно-курортное лечение назначены: да, нет (нуж-ное подчеркнуть); если «да»: "
            "в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.6. Диагноз ______________________________________ (код по МКБ):",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.6.1. Диагноз установлен впервые: да, нет (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.6.2. Диспансерное наблюдение: установлено ранее, установлено впервые, не установлено (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.6.3. Дополнительные консультации и исследования назначены: да, нет (нужное подчеркнуть); если «да»: "
            "в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.6.4. Дополнительные консультации и исследования выполнены: да, нет (нужное подчеркнуть); если «да»: "
            "в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.6.5. Лечение назначено: да, нет (нужное подчеркнуть); если «да»: в амбулаторных условиях, в условиях дневного стационара, " "в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.6.6. Медицинская реабилитация и (или) санаторно-курортное лечение назначены: да, нет (нуж-ное подчеркнуть); если «да»: "
            "в амбулаторных условиях, в условиях дневного стационара, в стационарных условиях (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.7. Инвалидность: да, нет (нужное подчеркнуть); если «да»:",
            style,
        )
    )
    objs.append(
        Paragraph(
            "с рождения, приобретенная (нужное подчеркнуть);",
            style,
        )
    )
    objs.append(
        Paragraph(
            "установлена впервые (дата) ______________________;",
            style,
        )
    )
    objs.append(
        Paragraph(
            "дата последнего освидетельствования ______________________",
            style,
        )
    )
    objs.append(
        Paragraph(
            f"16.8. Группа здоровья: {health_group_I}, {health_group_II}, {health_group_III}, {health_group_IV}, {health_group_V} (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "16.9. Медицинская группа для занятий физической культурой: I, II, III, IV, не допущен (нужное подчеркнуть).",
            style,
        )
    )
    objs.append(
        Paragraph(
            "17. Рекомендации по формированию здорового образа жизни, режиму дня, питанию, физиче-скому развитию, иммунопрофилактике, занятиям физической культурой:",
            style,
        )
    )
    objs.append(
        Paragraph(
            "________________________________________________________________________________",
            style,
        )
    )
    objs.append(
        Paragraph(
            "18. Рекомендации по проведению диспансерного наблюдения, лечению, медицинской реабилитации и санаторно-курортному лечению:",
            style,
        )
    )
    objs.append(
        Paragraph(
            "________________________________________________________________________________",
            style,
        )
    )
    main_manager = data.get("Главный врач") if data.get("Главный врач") else iss.doc_confirmation.hospital.current_manager
    opinion = [
        [
            Paragraph("Врач", styleT),
            Paragraph(
                "",
                style,
            ),
            Paragraph(
                "",
                style,
            ),
            Paragraph(
                "",
                style,
            ),
            Paragraph(
                f"{iss.doc_confirmation.get_fio()}",
                styleCenter,
            ),
        ],
        [
            Paragraph("", style),
            Paragraph("", style),
            Paragraph(
                "(подпись)",
                styleTableCentre,
            ),
            Paragraph("", style),
            Paragraph(
                "(И.О. Фамилия)",
                styleTableCentre,
            ),
        ],
        [
            Paragraph("Руководитель<br/>медицинской организации", styleT),
            Paragraph(
                "",
                style,
            ),
            Paragraph(
                "",
                style,
            ),
            Paragraph(
                "",
                style,
            ),
            Paragraph(
                f"{main_manager}",
                styleCenter,
            ),
        ],
        [
            Paragraph("", style),
            Paragraph(
                "",
                style,
            ),
            Paragraph(
                "(подпись)",
                styleTableCentre,
            ),
            Paragraph(
                "",
                style,
            ),
            Paragraph(
                "(И.О. Фамилия)",
                styleTableCentre,
            ),
        ],
    ]

    tbl = Table(
        opinion,
        colWidths=(
            70 * mm,
            7 * mm,
            40 * mm,
            7 * mm,
            60 * mm,
        ),
    )
    tbl.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.75, colors.white),
                ("LINEBELOW", (2, 0), (2, 0), 0.5, colors.black),
                ("LINEBELOW", (4, 0), (4, 0), 0.5, colors.black),
                ("LINEBELOW", (2, 2), (2, 2), 0.5, colors.black),
                ("LINEBELOW", (4, 2), (4, 2), 0.5, colors.black),
                ("LEFTPADDING", (1, 0), (-1, -1), 1 * mm),
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ]
        )
    )

    objs.append(Spacer(1, 3 * mm))
    objs.append(tbl)
    objs.append(Spacer(1, 1 * mm))
    objs.append(
        Paragraph(
            f"Дата заполнения <u>{current_time(only_date=True).strftime('%d.%m.%Y')}</u>",
            style,
        )
    )

    fwb.extend(objs)

    return fwb
