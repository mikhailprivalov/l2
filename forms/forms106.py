from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Frame, KeepInFrame, HRFlowable
from reportlab.platypus import PageBreak, Indenter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import black

from appconf.manager import SettingManager
from directions.models import Napravleniya, Issledovaniya
from directory.models import Fractions
from hospitals.models import Hospitals
from laboratory.settings import FONTS_FOLDER
import locale
import sys
import os.path
from io import BytesIO
from api.stationar.stationar_func import hosp_get_hosp_direction
from api.sql_func import get_fraction_result
from utils.dates import normalize_date
from .forms_func import primary_reception_get_data, hosp_extract_get_data, hosp_get_clinical_diagnos, hosp_get_transfers_data, hosp_get_operation_data, closed_bl


def form_02(request_data):
    """
    Форма 003/у - стационарная карта
    """

    num_dir = request_data["dir_pk"]
    direction_obj = Napravleniya.objects.get(pk=num_dir)
    hosp_nums_obj = hosp_get_hosp_direction(num_dir)
    hosp_nums = f"- {hosp_nums_obj[0].get('direction')}"

    ind_card = direction_obj.client
    patient_data = ind_card.get_data_individual()

    hospital: Hospitals = request_data["hospital"]

    hospital_name = hospital.safe_short_title
    hospital_address = hospital.safe_address
    hospital_kod_ogrn = hospital.safe_ogrn

    if sys.platform == "win32":
        locale.setlocale(locale.LC_ALL, "rus_rus")
    else:
        locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")

    pdfmetrics.registerFont(TTFont("PTAstraSerifBold", os.path.join(FONTS_FOLDER, "PTAstraSerif-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("PTAstraSerifReg", os.path.join(FONTS_FOLDER, "PTAstraSerif-Regular.ttf")))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20 * mm, rightMargin=12 * mm, topMargin=6 * mm, bottomMargin=4 * mm, allowSplitting=1, title="Форма {}".format("003/у"))
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.leading = 15
    style.spaceAfter = 0.5 * mm

    styleLead = deepcopy(style)
    styleLead.leading = 12
    styleLead.alignment = TA_JUSTIFY

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 12
    styleCenter.leading = 15
    styleCenter.spaceAfter = 1 * mm
    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 15
    styleCenterBold.face = "PTAstraSerifBold"
    styleCenterBold.borderColor = black
    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    styleRight = deepcopy(styleJustified)
    styleRight.alignment = TA_RIGHT

    objs = []

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm
    styleT.face = "PTAstraSerifReg"

    print_district = ""
    if SettingManager.get("district", default="True", default_type="b"):
        if ind_card.district is not None:
            print_district = "Уч: {}".format(ind_card.district.title)

    opinion = [
        [
            Paragraph("<font size=11>{}<br/>Адрес: {}<br/>ОГРН: {} <br/><u>{}</u> </font>".format(hospital_name, hospital_address, hospital_kod_ogrn, print_district), styleT),
            Paragraph("<font size=9 >Код формы по ОКУД:<br/>Код организации по ОКПО: 31348613<br/>" "Медицинская документация<br/>форма № 003/у</font>", styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [90 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.75, colors.white),
                ("LEFTPADDING", (1, 0), (-1, -1), 80),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    objs.append(tbl)
    space_symbol = "&nbsp;"
    if patient_data["age"] < SettingManager.get("child_age_before", default="15", default_type="i"):
        patient_data["serial"] = patient_data["bc_serial"]
        patient_data["num"] = patient_data["bc_num"]
    else:
        patient_data["serial"] = patient_data["passport_serial"]
        patient_data["num"] = patient_data["passport_num"]

    p_phone = ""
    if patient_data["phone"]:
        p_phone = "тел.: " + ", ".join(patient_data["phone"])

    p_address = patient_data["main_address"]
    work_place = patient_data["work_place_db"] if patient_data["work_place_db"] else patient_data["work_place"]
    p_work = work_place

    card_num_obj = patient_data["card_num"].split(" ")
    p_card_num = card_num_obj[0]

    # взять самое последнее направленеие из hosp_dirs
    hosp_last_num = hosp_nums_obj[-1].get("direction")
    ############################################################################################################
    # Получение данных из выписки.
    # Взять услугу типа выписка. Из полей "Дата выписки" - взять дату. Из поля "Время выписки" взять время
    hosp_extract_data = hosp_extract_get_data(hosp_last_num)

    extrac_date, extract_time, final_diagnos, other_diagnos, near_diagnos, outcome, doc_fio, manager_depart, room_num, depart_extract = "", "", "", "", "", "", "", "", "", ""
    days_count = "__________________________"

    if hosp_extract_data:
        extrac_date = hosp_extract_data["date_value"]
        extract_time = hosp_extract_data["time_value"]
        final_diagnos = hosp_extract_data["final_diagnos"]
        other_diagnos = hosp_extract_data["other_diagnos"]
        near_diagnos = hosp_extract_data["near_diagnos"]
        days_count = hosp_extract_data["days_count"]
        if hosp_extract_data["outcome"]:
            outcome = hosp_extract_data["outcome"] + " (" + hosp_extract_data["result_hospital"] + ")"
        doc_fio = hosp_extract_data["doc_fio"]
        manager_depart = hosp_extract_data["manager_depart"]
        room_num = hosp_extract_data["room_num"]
        iss_last_hosp = Issledovaniya.objects.filter(napravleniye__pk=hosp_last_num)[0]
        depart_extract = iss_last_hosp.research.title

    # Получить отделение - из названия услуги или самого главного направления
    hosp_depart = hosp_nums_obj[0].get("research_title")

    ############################################################################################################
    # Получить данные из первичного приема (самого первого hosp-направления)
    hosp_first_num = hosp_nums_obj[0].get("direction")
    primary_reception_data = primary_reception_get_data(hosp_first_num)

    ###########################################################################################################
    # Получение данных группы крови
    fcaction_avo_id = Fractions.objects.filter(title="Групповая принадлежность крови по системе АВО").first()
    fcaction_rezus_id = Fractions.objects.filter(title="Резус").first()
    group_blood_avo = get_fraction_result(ind_card.pk, fcaction_avo_id.pk, count=1)
    if group_blood_avo:
        group_blood_avo_value = group_blood_avo[0][5]
    else:
        group_blood_avo_value = primary_reception_data["blood_group"]
    group_blood_rezus = get_fraction_result(ind_card.pk, fcaction_rezus_id.pk, count=1)
    if group_blood_rezus:
        group_rezus_value = group_blood_rezus[0][5].replace("<br/>", " ")
    else:
        group_rezus_value = primary_reception_data["resus_factor"]

    ###########################################################################################################
    # получение данных клинического диагноза
    clinical_diagnos = hosp_get_clinical_diagnos(hosp_nums_obj)[0]

    #####################################################################################################
    # получить даные из переводного эпикриза: Дата перевода, Время перевода, в какое отделение переведен
    # у каждого hosp-направления найти подчиненное эпикриз Перевод*
    transfers_data = hosp_get_transfers_data(hosp_nums_obj)
    transfers = ""
    for i in transfers_data:
        transfers = f"{transfers} в {i['transfer_research_title']} {i['date_transfer_value']}/{i['time_transfer_value']};"

    #####################################################################################################
    title_page = [
        Indenter(left=0 * mm),
        Spacer(1, 8 * mm),
        Paragraph('<font fontname="PTAstraSerifBold" size=15>МЕДИЦИНСКАЯ КАРТА № {} <u>{}</u>, <br/> стационарного больного</font>'.format(p_card_num, hosp_nums), styleCenter),
        Spacer(1, 2 * mm),
        Spacer(1, 2 * mm),
        Spacer(1, 2 * mm),
        Paragraph("Дата и время поступления: {} - {}".format(primary_reception_data["date_entered_value"], primary_reception_data["time_entered_value"]), style),
        Spacer(1, 0.5 * mm),
        Paragraph("Дата и время выписки: {} - {}".format(extrac_date, extract_time), style),
        Spacer(1, 0.5 * mm),
        Paragraph("Отделение: {}".format(hosp_depart), style),
        Spacer(1, 0.5 * mm),
        Paragraph(f"Палата №: {room_num} {depart_extract}", style),
        Spacer(1, 0.5 * mm),
        Paragraph("Переведен в отделение:", style),
        Spacer(1, 8 * mm),
        Paragraph("Проведено койко-дней: {}".format(days_count), style),
        Spacer(1, 0.5 * mm),
        Paragraph("Виды транспортировки(на каталке, на кресле, может идти): {}".format(primary_reception_data["type_transport"]), style),
        Spacer(1, 0.5 * mm),
        Paragraph("Группа крови: {}. Резус-принадлежность: {}".format(group_blood_avo_value, group_rezus_value), style),
        Spacer(1, 1 * mm),
        Paragraph("Побочное действие лекарств(непереносимость):", style),
        Spacer(1, 12 * mm),
        Paragraph("1. Фамилия, имя, отчество:&nbsp;", style),
        Spacer(1, 2 * mm),
        Paragraph("2. Пол: {} {} 3. Дата рождения: {}".format(patient_data["sex"], 3 * space_symbol, patient_data["born"]), style),
        Spacer(1, 0.5 * mm),
        Paragraph("4. Постоянное место жительства: ", style),
        Spacer(1, 3.5 * mm),
        Paragraph("5. Место работы, профессия или должность:", style),
        Spacer(1, 0.5 * mm),
        Paragraph("6. Кем направлен больной:", style),
        Spacer(1, 0.5 * mm),
        Paragraph("7. Доставлен в стационар по экстренным показаниям: {}".format(primary_reception_data["extra_hospital"]), style),
        Spacer(1, 0.5 * mm),
        Paragraph(" через: {} после начала заболевания, получения травмы; ".format(primary_reception_data["time_start_ill"]), style),
        Spacer(1, 0.5 * mm),
        Paragraph(" госпитализирован в плановом порядке (подчеркнуть) {}.".format(primary_reception_data["plan_hospital"]), style),
        Spacer(1, 0.5 * mm),
        Paragraph("8. Диагноз направившего учреждения:", style),
        Spacer(1, 8 * mm),
        Paragraph("9. Диагноз при поступлении:", style),
        Spacer(1, 10 * mm),
        Paragraph("10. Диагноз клинический:", style),
        PageBreak(),
    ]

    closed_bl_result = closed_bl(hosp_nums_obj[0].get("direction"))
    data_bl = ""
    if closed_bl_result["start_date"] and closed_bl_result["end_date"] and closed_bl_result["num"]:
        data_bl = (
            f"<br/>открыт <u>{closed_bl_result['start_date']}</u>{5 * space_symbol}закрыт: <u>{closed_bl_result['end_date']}</u> {3 * space_symbol}"
            f"к труду: <u>{closed_bl_result['start_work']}</u> <br/>Номер ЛН: <u>{closed_bl_result['num']}</u> Выдан кому: {closed_bl_result['who_get']} "
        )

    second_page = [
        Spacer(1, 2 * mm),
        Paragraph("11. Диагноз заключительный клинический:", style),
        Spacer(1, 0.5 * mm),
        Paragraph("а) основной:", style),
        Spacer(1, 45 * mm),
        Paragraph("б) осложнение основного:", style),
        Spacer(1, 18 * mm),
        Paragraph("в) сопутствующий:", style),
        Spacer(1, 19 * mm),
        Paragraph(
            "12. Госпитализирован в данном году по поводу данного заболевания: {}, <br/>"
            "всего  - {} раз.:".format(primary_reception_data["what_time_hospitalized"], primary_reception_data["all_hospitalized"]),
            styleLead,
        ),
        Spacer(1, 1 * mm),
        Paragraph("13. Хирургические операции, методы обезболивания и послеоперационные осложнения:", styleLead),
        Spacer(1, 40 * mm),
        Paragraph("14. Другие виды лечения:___________________________________________", styleLead),
        Spacer(1, 0.2 * mm),
        Paragraph("для больных злокачественными новообразованиями.", styleLead),
        Spacer(1, 0.2 * mm),
        Paragraph(
            " 1.Специальное лечение: хирургическое(дистанционная гамматерапия, рентгенотерапия, быстрые "
            "электроны, контактная и дистанционная гамматерапия, контактная гамматерапия и глубокая "
            "рентгенотерапия); комбинированное(хирургическое и гамматерапия, хирургическое и рентгено - "
            "терапия, хирургическое и сочетанное лучевое); химиопрепаратами, гормональными препаратами.",
            styleLead,
        ),
        Spacer(1, 1 * mm),
        Paragraph("2. Паллиативное", styleLead),
        Spacer(1, 0.2 * mm),
        Paragraph("3. Симптоматическое лечение.", styleLead),
        Spacer(1, 0.2 * mm),
        Paragraph(f"15. Отметка о выдаче листка нетрудоспособности:{data_bl}", styleLead),
        Spacer(1, 1 * mm),
        Paragraph("16. Исход заболевания: {}".format(outcome), styleLead),
        Spacer(1, 1 * mm),
        Paragraph(
            "17.  Трудоспособность восстановлена полностью, снижена, временно утрачена, стойко утрачена в связи " "с данным заболеванием, с другими причинами(подчеркнуть): {}".format(""),
            styleLead,
        ),
        Spacer(1, 1 * mm),
        Paragraph("18. Для поступивших на экспертизу - заключение:___________________", styleLead),
        Spacer(1, 1 * mm),
        Paragraph("___________________________________________________________________", styleLead),
        Spacer(1, 1 * mm),
        Paragraph("19. Особые отметки", style),
        Spacer(1, 2 * mm),
        Paragraph("Лечащий врач: {}".format(doc_fio), style),
        Paragraph("Заведующий отделением: {}".format(manager_depart), style),
    ]
    if primary_reception_data["weight"]:
        second_page.append(Paragraph(f"Вес: {primary_reception_data['weight']}", styleRight))
    objs.extend(title_page)
    objs.extend(second_page)

    closed_bl_result = closed_bl(hosp_nums_obj[0].get("direction"))

    def first_pages(canvas, document):
        canvas.saveState()
        if closed_bl_result.get("is_closed", None):
            canvas.setFont("PTAstraSerifBold", 12)
            canvas.drawString(7 * mm, 290 * mm, "ЛН")
        # Переведен
        transfers_text = [Paragraph("{}".format(transfers), styleJustified)]
        transfers_frame = Frame(27 * mm, 206 * mm, 175 * mm, 7 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, id="diagnos_frame", showBoundary=0)
        transfers_inframe = KeepInFrame(
            175 * mm,
            12 * mm,
            transfers_text,
            hAlign="LEFT",
            vAlign="TOP",
        )
        transfers_frame.addFromList([transfers_inframe], canvas)

        # Побочное действие лекарств(непереносимость) координаты
        medicament_text = [Paragraph("{}".format(primary_reception_data["medicament_allergy"]), styleJustified)]
        medicament_frame = Frame(27 * mm, 171 * mm, 175 * mm, 9 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, id="diagnos_frame", showBoundary=0)
        medicament_inframe = KeepInFrame(
            175 * mm,
            12 * mm,
            medicament_text,
            hAlign="LEFT",
            vAlign="TOP",
        )
        medicament_frame.addFromList([medicament_inframe], canvas)

        # ФИО
        fio_text = [Paragraph("<font size=11.7 fontname ='PTAstraSerifBold'> {}</font> ".format(patient_data["fio"]), style)]
        fio_frame = Frame(77 * mm, 159 * mm, 125 * mm, 8 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, id="diagnos_frame", showBoundary=0)
        fio_inframe = KeepInFrame(
            175 * mm,
            12 * mm,
            fio_text,
            hAlign="LEFT",
            vAlign="TOP",
        )
        fio_frame.addFromList([fio_inframe], canvas)

        # Постоянное место жительства
        live_text = [Paragraph("{}, {}".format(p_address, p_phone), style)]
        live_frame = Frame(88 * mm, 144 * mm, 115 * mm, 9 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, id="diagnos_frame", showBoundary=0)
        live_inframe = KeepInFrame(
            175 * mm,
            12 * mm,
            live_text,
            hAlign="LEFT",
            vAlign="TOP",
        )
        live_frame.addFromList([live_inframe], canvas)

        # Место работы
        work_text = [Paragraph("{}".format(p_work), style)]
        work_frame = Frame(108 * mm, 138.5 * mm, 95 * mm, 5 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, id="diagnos_frame", showBoundary=0)
        work_inframe = KeepInFrame(
            175 * mm,
            12 * mm,
            work_text,
            hAlign="LEFT",
            vAlign="TOP",
        )
        work_frame.addFromList([work_inframe], canvas)

        # Кем направлен больной
        who_directed_text = [Paragraph("{}".format(primary_reception_data["who_directed"]), style)]
        who_directed_frame = Frame(77 * mm, 129.5 * mm, 126 * mm, 7 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, id="diagnos_frame", showBoundary=0)
        who_directed_inframe = KeepInFrame(
            175 * mm,
            12 * mm,
            who_directed_text,
            hAlign="LEFT",
            vAlign="TOP",
        )
        who_directed_frame.addFromList([who_directed_inframe], canvas)

        # Диагноз направившего учреждения координаты
        diagnos_directed_text = [Paragraph("{}".format(primary_reception_data["diagnos_who_directed"]), styleJustified)]
        diagnos_directed_frame = Frame(27 * mm, 98 * mm, 175 * mm, 9 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, id="diagnos_frame", showBoundary=0)
        diagnos_directed_inframe = KeepInFrame(
            175 * mm,
            10 * mm,
            diagnos_directed_text,
            hAlign="LEFT",
            vAlign="TOP",
        )
        diagnos_directed_frame.addFromList([diagnos_directed_inframe], canvas)

        # Диагноз при поступлении координаты
        diagnos_entered_text = [Paragraph("{}".format(primary_reception_data["diagnos_entered"]), styleJustified)]
        diagnos_entered_frame = Frame(27 * mm, 83 * mm, 175 * mm, 10 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, id="diagnos_frame", showBoundary=0)
        diagnos_entered_inframe = KeepInFrame(
            175 * mm,
            10 * mm,
            diagnos_entered_text,
            hAlign="LEFT",
            vAlign="TOP",
        )
        diagnos_entered_frame.addFromList([diagnos_entered_inframe], canvas)

        # клинический диагноз координаты
        diagnos_text = [Paragraph("{}".format(clinical_diagnos), styleJustified)]
        diagnos_frame = Frame(27 * mm, 22 * mm, 175 * mm, 55 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, id="diagnos_frame", showBoundary=0)
        diagnos_inframe = KeepInFrame(175 * mm, 55 * mm, diagnos_text)
        diagnos_frame.addFromList([diagnos_inframe], canvas)

        # представитель пациента
        p_agent = None
        agent_status = ""
        agent = ""
        if ind_card.who_is_agent:
            p_agent = getattr(ind_card, ind_card.who_is_agent)
            agent_status = ind_card.get_who_is_agent_display()
        if p_agent:
            agent_data = p_agent.get_data_individual()
            agent_fio = agent_data["fio"]
            agent_phone = ",".join(agent_data["phone"])
            agent = f"{agent_status}: {agent_fio}, тел.:{agent_phone}"

        agent_text = [Paragraph("<u>{}</u>".format(agent), styleRight)]
        agent_frame = Frame(27 * mm, 5 * mm, 175 * mm, 7 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, id="diagnos_frame", showBoundary=0)
        agent_inframe = KeepInFrame(175 * mm, 10 * mm, agent_text)
        agent_frame.addFromList([agent_inframe], canvas)
        canvas.restoreState()

    # Получить все услуги из категории операции
    styleTO = deepcopy(style)
    styleTO.alignment = TA_LEFT
    styleTO.firstLineIndent = 0
    styleTO.fontSize = 9.5
    styleTO.leading = 10
    styleTO.spaceAfter = 0.2 * mm

    # Таблица для операции
    opinion_oper = [
        [
            Paragraph("№", styleTO),
            Paragraph("Название операции", styleTO),
            Paragraph("Дата, &nbsp час", styleTO),
            Paragraph("Метод обезболивания", styleTO),
            Paragraph("Осложнения", styleTO),
            Paragraph("Оперировал", styleTO),
        ]
    ]

    hosp_operation = hosp_get_operation_data(num_dir)
    x = 0
    operation_result = []
    for i in hosp_operation:
        operation_template = [""] * 6
        x += 1
        operation_template[0] = Paragraph(str(x), styleTO)
        operation_template[1] = Paragraph(f"{i['name_operation']} <br/><font face=\"PTAstraSerifBold\" size=\"8.7\">({i['category_difficult']})</font>", styleTO)
        operation_template[2] = Paragraph(i["date"] + "<br/>" + i["time_start"] + "-" + i["time_end"], styleTO)
        operation_template[3] = Paragraph(i["anesthesia method"], styleTO)
        operation_template[4] = Paragraph(i["complications"], styleTO)
        operation_template[5] = Paragraph(i["doc_fio"], styleTO)
        operation_result.append(operation_template.copy())

    opinion_oper.extend(operation_result)

    t_opinion_oper = opinion_oper.copy()
    tbl_o = Table(
        t_opinion_oper,
        colWidths=(
            7 * mm,
            62 * mm,
            25 * mm,
            30 * mm,
            15 * mm,
            45 * mm,
        ),
    )
    tbl_o.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1.0, colors.black),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.1 * mm),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    def later_pages(canvas, document):
        canvas.saveState()
        # Заключительные диагнозы
        # Основной заключительный диагноз
        final_diagnos_text = [Paragraph("{}".format(final_diagnos), styleJustified)]
        final_diagnos_frame = Frame(27 * mm, 230 * mm, 175 * mm, 45 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
        final_diagnos_inframe = KeepInFrame(
            175 * mm,
            50 * mm,
            final_diagnos_text,
            hAlign="LEFT",
            vAlign="TOP",
        )
        final_diagnos_frame.addFromList([final_diagnos_inframe], canvas)

        # Осложнения основного заключительного диагноза
        other_diagnos_text = [Paragraph("{}".format(other_diagnos), styleJustified)]
        other_diagnos_frame = Frame(27 * mm, 205 * mm, 175 * mm, 20 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
        other_diagnos_inframe = KeepInFrame(
            175 * mm,
            20 * mm,
            other_diagnos_text,
            hAlign="LEFT",
            vAlign="TOP",
        )
        other_diagnos_frame.addFromList([other_diagnos_inframe], canvas)

        # Сопутствующие основного заключительного диагноза
        near_diagnos_text = [Paragraph("{}".format(near_diagnos.replace("<", "&lt;").replace(">", "&gt;")), styleJustified)]
        near_diagnos_frame = Frame(27 * mm, 181 * mm, 175 * mm, 20 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
        near_diagnos_inframe = KeepInFrame(
            175 * mm,
            20 * mm,
            near_diagnos_text,
            vAlign="TOP",
        )
        near_diagnos_frame.addFromList([near_diagnos_inframe], canvas)

        # Таблица операции
        operation_text = [tbl_o]
        operation_frame = Frame(22 * mm, 123 * mm, 170 * mm, 40 * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
        operation_inframe = KeepInFrame(175 * mm, 40 * mm, operation_text, hAlign="CENTRE", vAlign="TOP", fakeWidth=False)
        operation_frame.addFromList([operation_inframe], canvas)

        canvas.setFont("PTAstraSerifBold", 8)
        hospital: Hospitals = request_data["hospital"]
        hospital_name = hospital.safe_short_title
        canvas.drawString(55 * mm, 12 * mm, "{}".format(hospital_name))
        canvas.drawString(55 * mm, 9 * mm, "№ карты : {}; Номер истории: {}".format(p_card_num, hosp_nums))
        canvas.drawString(55 * mm, 6 * mm, "Пациент: {} {}".format(patient_data["fio"], patient_data["born"]))
        canvas.line(55 * mm, 11.5 * mm, 200 * mm, 11.5 * mm)
        canvas.restoreState()

    doc.build(objs, onFirstPage=first_pages, onLaterPages=later_pages)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_01(request_data):
    """
    Форма 003/у - cтационарная карта 530Н
    """

    num_dir = request_data["dir_pk"]
    direction_obj = Napravleniya.objects.get(pk=num_dir)
    hosp_nums_obj = hosp_get_hosp_direction(num_dir)
    hosp_nums = f"- {hosp_nums_obj[0].get('direction')}"

    ind_card = direction_obj.client
    patient_data = ind_card.get_data_individual()

    hospital: Hospitals = request_data["hospital"]

    hospital_name = hospital.safe_short_title
    hospital_address = hospital.safe_address
    hospital_kod_ogrn = hospital.safe_ogrn

    if sys.platform == "win32":
        locale.setlocale(locale.LC_ALL, "rus_rus")
    else:
        locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")

    pdfmetrics.registerFont(TTFont("PTAstraSerifBold", os.path.join(FONTS_FOLDER, "PTAstraSerif-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("PTAstraSerifReg", os.path.join(FONTS_FOLDER, "PTAstraSerif-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("Symbola", os.path.join(FONTS_FOLDER, "Symbola.ttf")))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20 * mm, rightMargin=12 * mm, topMargin=5 * mm, bottomMargin=10 * mm, allowSplitting=1, title="Форма {}".format("003/у"))
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 11
    style.leading = 12
    style.spaceAfter = 0.5 * mm

    styleLead = deepcopy(style)
    styleLead.leading = 12
    styleLead.alignment = TA_JUSTIFY

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 12
    styleCenter.leading = 9
    styleCenter.spaceAfter = 1 * mm
    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 7
    styleCenterBold.leading = 15
    styleCenterBold.face = "PTAstraSerifBold"
    styleCenterBold.borderColor = black
    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    styleRight = deepcopy(styleJustified)
    styleRight.alignment = TA_RIGHT

    objs = []

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm
    styleT.face = "PTAstraSerifReg"

    print_district = ""
    if SettingManager.get("district", default="True", default_type="b"):
        if ind_card.district is not None:
            print_district = "Уч: {}".format(ind_card.district.title)

    opinion = [
        [
            Paragraph("<font size=11>{}<br/>Адрес: {}<br/>ОГРН: {} <br/><u>{}</u> </font>".format(hospital_name, hospital_address, hospital_kod_ogrn, print_district), styleT),
            Paragraph(
                "<font size=9 >Код формы по ОКУД:<br/>"
                "Медицинская документация<br/>форма № 003/у<br/><br/>Утверждена приказом Министерства здравоохранения Российской Федерации от «5» августа 2022г. N 530н</font>",
                styleT,
            ),
        ],
    ]

    tbl = Table(opinion, 2 * [90 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.75, colors.white),
                ("LEFTPADDING", (1, 0), (-1, -1), 80),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    objs.append(tbl)
    if patient_data["age"] < SettingManager.get("child_age_before", default="15", default_type="i"):
        patient_data["serial"] = patient_data["bc_serial"]
        patient_data["num"] = patient_data["bc_num"]
    else:
        patient_data["serial"] = patient_data["passport_serial"]
        patient_data["num"] = patient_data["passport_num"]

    p_phone = ""
    if patient_data["phone"]:
        p_phone = "тел.: " + ", ".join(patient_data["phone"])

    card_num_obj = patient_data["card_num"].split(" ")
    p_card_num = card_num_obj[0]

    # взять самое последнее направленеие из hosp_dirs
    hosp_last_num = hosp_nums_obj[-1].get("direction")
    ############################################################################################################
    # Получение данных из выписки
    # Взять услугу типа выписка. Из полей "Дата выписки" - взять дату. Из поля "Время выписки" взять время
    hosp_extract_data = hosp_extract_get_data(hosp_last_num)

    extrac_date, extract_time, outcome = "", "", ""
    days_count = "__________________________"
    result_hospital = ""
    if hosp_extract_data:
        extrac_date = hosp_extract_data["date_value"]
        extract_time = hosp_extract_data["time_value"]
        days_count = hosp_extract_data["days_count"]
        if hosp_extract_data["outcome"]:
            outcome = hosp_extract_data["outcome"]
        if hosp_extract_data["result_hospital"]:
            result_hospital = hosp_extract_data["result_hospital"]

    # Получить отделение - из названия услуги или самого главного направления
    first_bed_profile = hosp_nums_obj[0].get("research_title")
    iss_first_depart = Issledovaniya.objects.get(pk=hosp_nums_obj[0].get("issledovaniye"))
    first_hosp_depart = iss_first_depart.hospital_department_override.title if iss_first_depart.hospital_department_override else ""

    ############################################################################################################
    # Получить данные из первичного приема (самого первого hosp-направления)
    hosp_first_num = hosp_nums_obj[0].get("direction")
    primary_reception_data = primary_reception_get_data(hosp_first_num)

    ###########################################################################################################
    # Получение данных группы крови
    fcaction_avo_id = Fractions.objects.filter(title="Групповая принадлежность крови по системе АВО").first()
    fcaction_rezus_id = Fractions.objects.filter(title="Резус").first()
    group_blood_avo = get_fraction_result(ind_card.pk, fcaction_avo_id.pk, count=1)
    if group_blood_avo:
        group_blood_avo_value = group_blood_avo[0][5]
    else:
        group_blood_avo_value = primary_reception_data["blood_group"]

    open_symbola = '<font face="Symbola" size=11>'
    close_symbola = "</font>"
    variants = {
        "O<sub>αβ</sub> (I)": f"O<sub>{open_symbola}\u03B1\u03B2{close_symbola}</sub>",
        "Bα (III)": f"B{open_symbola}\u03B1{close_symbola} (III)",
        "A<sub>β</sub> (II)": f"A<sub>{open_symbola}\u03B2{close_symbola}</sub>(II)",
        "A₂β (II)": f"A₂{open_symbola}\u03B2{close_symbola}",
        "AB₀ (IV)": f"AB<sub>{open_symbola}\u2070{close_symbola}</sub> (IV)",
        "A₂B₀ (IV)": f"A₂B<sub>{open_symbola}\u2070{close_symbola}</sub>",
    }
    if variants.get(group_blood_avo_value):
        group_blood_avo_value = variants.get(group_blood_avo_value)

    group_blood_rezus = get_fraction_result(ind_card.pk, fcaction_rezus_id.pk, count=1)
    if group_blood_rezus:
        group_rezus_value = group_blood_rezus[0][5].replace("<br/>", " ")
    else:
        group_rezus_value = primary_reception_data["resus_factor"]

    #####################################################################################################
    # получить даные из переводного эпикриза: Дата перевода, Время перевода, в какое отделение переведен
    # у каждого hosp-направления найти подчиненное эпикриз Перевод*
    transfers_data = hosp_get_transfers_data(hosp_nums_obj)
    transfers = ""
    for i in transfers_data:
        transfers = (
            f"{transfers}<br/> Переведен в отделение {i['transfer_depart']}; профиль коек {i['transfer_research_title']}<br/>Дата и время перевода {i['date_transfer_value']} "
            f"время:{i['time_transfer_value']};<br/>"
        )

    plan_form = primary_reception_data["plan_hospital"]
    extra_hospital = primary_reception_data["extra_hospital"]
    result_form = ""
    if plan_form.lower() == "да":
        result_form = "плановая — 1"
    if extra_hospital.lower() == "да":
        result_form = "экстренная — 2"
    number_direction = normalize_date(primary_reception_data["ext_direction_date"])
    bold_open = '<font fontname ="PTAstraSerifBold">'
    bold_close = "</font>"
    title_page = [
        Indenter(left=0 * mm),
        Spacer(1, 2 * mm),
        Paragraph(
            '<font fontname="PTAstraSerifBold" size=10>МЕДИЦИНСКАЯ КАРТА ПАЦИЕНТА,<br/>ПОЛУЧАЮЩЕГО МЕДИЦННСКУЮ ПОМОЩЬ<br/>В СТАЦИОНАРНЫХ УСЛОВНЯХ<br/> № {} <u>{}</u></font>'.format(
                p_card_num, hosp_nums
            ),
            styleCenterBold,
        ),
        Spacer(1, 2 * mm),
        Paragraph(f"Фамилия, имя, отчество:&nbsp; {patient_data['fio']}", style),
        Spacer(1, 0.2 * mm),
        Paragraph(f"Дата рождения: {patient_data['born']} Пол: {patient_data['sex']}", style),
        Spacer(1, 0.5 * mm),
        Paragraph("Поступил в: стационар - 1", style),
        Spacer(1, 0.5 * mm),
        Paragraph(f"Дата и время поступления: {primary_reception_data['date_entered_value']}, {primary_reception_data['time_entered_value']}", style),
        Spacer(1, 0.5 * mm),
        Paragraph(f"Поступил через <u>{primary_reception_data['time_start_ill']}</u> часов после начала заболевания, получения травмы, отравления.", style),
        Spacer(1, 0.5 * mm),
        Paragraph("Направлен в стационар (дневной стационар):", style),
        Spacer(1, 0.5 * mm),
        Paragraph(f"Наименование медицинской	организации, направившей пациента: {primary_reception_data['who_directed']}", style),
        Spacer(1, 0.5 * mm),
        Paragraph(f"Номер и дата направления: {primary_reception_data['ext_direction_number']}	от {number_direction} г.", style),
        Spacer(1, 0.5 * mm),
        Paragraph(
            f"Поступил в стационар (дневной стационар) для оказания медицинской помощи в текущем году:"
            f"по поводу основного заболевания, указанного в диагнозе при поступлении: {primary_reception_data['what_time_hospitalized']}.",
            style,
        ),
        Spacer(1, 0.5 * mm),
        Paragraph(f"Форма оказания медицинской помощи: {result_form}", style),
        Spacer(1, 0.5 * mm),
        Paragraph(f"Наименование отделения: {first_hosp_depart}; профиль коек {first_bed_profile}; палата № ____", style),
        Spacer(1, 0.5 * mm),
        Paragraph(f"{transfers}", style),
        Spacer(1, 1 * mm),
        Paragraph(f"Выписан: {extrac_date}. время:	{extract_time}", style),
        Spacer(1, 0.5 * mm),
        Paragraph(f"Количество дней нахождения в медицинской организации: {days_count}", style),
        Spacer(1, 0.5 * mm),
        Paragraph(f"Диагноз при направлении: {primary_reception_data['direction_diagnos']}", style),
        Spacer(1, 0.5 * mm),
        Paragraph(f"код по МКБ: {primary_reception_data['direction_mkb_diagnos']}", style),
        Spacer(1, 0.5 * mm),
    ]
    title_page.append(Paragraph(f"{bold_open}Предварительный диагноз (диагноз при поступлении):{bold_close}", style))
    title_page.append(Spacer(1, 0.5 * mm))
    title_page.append(
        Paragraph(
            f"Дата и время установления диагноза при поступлении: {primary_reception_data['date_diagnosis']}г. время:	{primary_reception_data['time_diagnosis']}",
            style,
        )
    )
    title_page.append(Spacer(1, 2.0 * mm))
    title_page.append(Paragraph("Основное заболевание:", style)),
    for i in primary_reception_data["final_diagnos_mkb"]:
        title_page.append(Paragraph(f"{i.get('data')} {bold_open}код по МКБ:{bold_close} {i.get('code')} ", style))
    title_page.append(Spacer(1, 2.0 * mm))
    title_page.append(Paragraph("Осложнения основного заболевания: ", style))
    for i in primary_reception_data["other_diagnos_mkb"]:
        title_page.append(Paragraph(f"{i.get('data')} {bold_open}код по МКБ:{bold_close} {i.get('code')} ", style))
    title_page.append(Spacer(1, 2.0 * mm))
    title_page.append(Paragraph("Внешняя причина при травмах, отравлениях:", style))
    for i in primary_reception_data["external_reason_mkb"]:
        title_page.append(Paragraph(f"{i.get('data')}  {bold_open}код по МКБ:{bold_close} {i.get('code')} ", style))
    title_page.append(Spacer(1, 2.0 * mm))
    title_page.append(Paragraph("Сопутствующие заболевания:", style))
    for i in primary_reception_data["near_diagnos_mkb"]:
        title_page.append(Paragraph(f"{i.get('data')} {bold_open}код по МКБ:{bold_close} {i.get('code')} ", style))

    title_page.append(Spacer(1, 0.5 * mm))
    title_page.append(Paragraph(f"Дополнительные сведения о заболевании {primary_reception_data['additional_data_ill']}", style))

    title_page.append(Spacer(1, 0.5 * mm))
    title_page.append(
        Paragraph(
            f"В анамнезе: туберкулез {bold_open}{primary_reception_data['tuberculosis']}{bold_close};	"
            f"ВИЧ-инфекция {bold_open}{primary_reception_data['hiv_infection']}{bold_close} ;"
            f"вирусные гепатиты {bold_open}{primary_reception_data['viral_infections']}{bold_close}; "
            f"сифилис {bold_open}{primary_reception_data['syphilis']}{bold_close}; "
            f"COVID-19 {bold_open}{primary_reception_data['covid19']}{bold_close}; ",
            style,
        )
    )

    title_page.append(Spacer(1, 0.5 * mm))
    title_page.append(Paragraph(f"Осмотр на педикулез, чесотку: {primary_reception_data['covid19']}, результат осмотра: {primary_reception_data['result_pediculosis_exam']}", style))
    title_page.append(Spacer(1, 0.5 * mm))
    title_page.append(
        Paragraph(
            f"Аллергические реакции на лекарственные препараты, пищевая аллергия или иные виды непереносимости в анамнезе, с указанием типа и вида аллергической реакции: "
            f"{primary_reception_data['medicament_allergy']}",
            style,
        )
    )
    title_page.append(Paragraph("___________________________________________________________", style))
    title_page.append(Paragraph(f"Группа крови: {group_blood_avo_value}; резус-принадлежность {group_rezus_value}; антиген K1 системы Kell _____", style))
    title_page.append(Spacer(1, 0.5 * mm))
    title_page.append(Paragraph("иные сведения групповой принадлежности крови (при наличии) ______________", style))
    title_page.append(Spacer(1, 4 * mm))
    title_page.append(Spacer(1, 2 * mm))
    clinical_diagnos = primary_reception_get_data(hosp_first_num, site_type=6)
    title_page.append(Paragraph(f"{bold_open}Диагноз клинический, установленный в стационаре:{bold_close}", style))
    title_page.append(Paragraph(f"Дата и время установления клинического диагноза: {clinical_diagnos['date_diagnosis']}г. время: {clinical_diagnos['time_diagnosis']}", style))
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(Paragraph("Основное заболевание:", style))
    for i in clinical_diagnos["final_diagnos_mkb"]:
        title_page.append(Paragraph(f"{i.get('data')} {bold_open}код по МКБ:{bold_close} {i.get('code')} ", style))
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(Paragraph("Осложнения основного заболевания:", style))
    for i in clinical_diagnos["other_diagnos_mkb"]:
        title_page.append(Paragraph(f"{i.get('data')} {bold_open}код по МКБ:{bold_close} {i.get('code')} ", style))
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(Paragraph("Внешняя причина при травмах, отравления:", style))
    for i in clinical_diagnos["external_reason_mkb"]:
        title_page.append(Paragraph(f"{i.get('data')}  {bold_open}код по МКБ:{bold_close} {i.get('code')} ", style))
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(Paragraph("Сопутствующие заболевания", style))
    for i in clinical_diagnos["near_diagnos_mkb"]:
        title_page.append(Paragraph(f"{i.get('data')} {bold_open}код по МКБ:{bold_close} {i.get('code')} ", style))
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(Paragraph("Дополнительные сведения о заболевании", style))
    title_page.append(Spacer(1, 2 * mm))

    title_page.append(Paragraph(f"{bold_open}Диагноз окончательный при выписке из стационара:{bold_close}", style))
    title_page.append(Paragraph("Основное заболевание:", style))
    for i in hosp_extract_data["final_diagnos_mkb_dict"]:
        title_page.append(Paragraph(f"{i.get('data')} {bold_open}код по МКБ:{bold_close} {i.get('code')} ", style))
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(Paragraph("Осложнения основного заболевания:", style))
    for i in hosp_extract_data["other_diagnos_mkb_dict"]:
        title_page.append(Paragraph(f"{i.get('data')} {bold_open}код по МКБ:{bold_close} {i.get('code')} ", style))
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(Paragraph("Внешняя причина при травмах, отравления:", style))
    for i in hosp_extract_data["external_reason_mkb_dict"]:
        title_page.append(Paragraph(f"{i.get('data')}  {bold_open}код по МКБ:{bold_close} {i.get('code')} ", style))
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(Paragraph("Сопутствующие заболевания", style))
    for i in hosp_extract_data["near_diagnos_mkb_dict"]:
        title_page.append(Paragraph(f"{i.get('data')} {bold_open}код по МКБ:{bold_close} {i.get('code')} ", style))
    title_page.append(Spacer(1, 2 * mm))

    title_page.append(Paragraph("Проведенные оперативные вмешательства (операции):", style))
    styleTO = deepcopy(style)
    styleTO.alignment = TA_LEFT
    styleTO.firstLineIndent = 0
    styleTO.fontSize = 9.5
    styleTO.leading = 10
    styleTO.spaceAfter = 0.2 * mm

    # Таблица для операции
    opinion_oper = [
        [
            Paragraph("Дата проведения", styleTO),
            Paragraph("Наименование оперативного вмешательства (операции), код согласно номенклатуре медицинских услуг", styleTO),
            Paragraph("Вид анестезиологического пособия", styleTO),
            Paragraph("Кровопотеря во время оперативного вмешательства (операции), мл", styleTO),
        ]
    ]

    hosp_operation = hosp_get_operation_data(num_dir)
    operation_result = []
    for i in hosp_operation:
        operation_template = [""] * 4
        operation_template[0] = Paragraph(i["date"] + "<br/>" + i["time_start"] + "-" + i["time_end"], styleTO)
        operation_template[1] = Paragraph(f"{i['name_operation']} <br/><font face=\"PTAstraSerifBold\" size=\"8.7\">({i['category_difficult']}), {i['doc_fio']}</font>", styleTO)
        operation_template[2] = Paragraph(i["anesthesia method"], styleTO)
        operation_template[3] = Paragraph(i["complications"], styleTO)
        operation_result.append(operation_template.copy())

    opinion_oper.extend(operation_result)

    t_opinion_oper = opinion_oper.copy()
    tbl_o = Table(
        t_opinion_oper,
        colWidths=(
            20 * mm,
            85 * mm,
            45 * mm,
            24 * mm,
        ),
    )
    tbl_o.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1.0, colors.black),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.1 * mm),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    title_page.append(tbl_o),
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(Paragraph(f"Исход госпитализации: {outcome}", style))
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(
        Paragraph(
            "Наименование медицинской	организации	(фамилия,	имя, отчество (при наличии) индивидуального предпринимателя, осуществляющего медицинскую деятельность), "
            f"куда переведен пациент {hosp_extract_data['transfer_to']}",
            style,
        )
    )
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(Paragraph(f"Результат госпитализации: {result_hospital}", style))
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(Paragraph("Умер в	отделении: «	»	20	г. время:	час.	мин.", style))
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(Paragraph("Умерла беременная: 1 — до 22 недель беременности, 2 — после 22 недель беременности.", style))
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(Paragraph("Сведения о листке нетрудоспособности:", style))
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(Paragraph(f"{hosp_extract_data['ln_data']}", style))
    title_page.append(Paragraph(f"{hosp_extract_data['ln_vk_data']}", style))
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(Paragraph("Сведения о лице, которому может быть передана информация о состоянии здоровья пациента:", style))
    title_page.append(Paragraph(f"фамилия, имя, отчество (при наличии), номер контактного телефона {p_phone}", style))
    title_page.append(Paragraph(f"{primary_reception_data['whom_transfer_health_data']}", style))
    title_page.append(Spacer(1, 2 * mm))
    title_page.append(Paragraph("Дополнительные сведения о пациенте", style))

    if primary_reception_data.get("weight"):
        title_page.append(Paragraph(f"Вес: {primary_reception_data['weight']}", styleRight))

    doc.build(title_page)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf
