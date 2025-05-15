from openpyxl.styles import Border, Side, Alignment, Font, NamedStyle
from openpyxl.utils import get_column_letter

from clients.sql_func import researches_by_harmfull_factor_id
from statistic.forms.forms100_sql_func import closed_company_cases_by_date, directions_by_parent_cases_issledovaniye, search_value_where_done_custom_research


def form_01(ws1, data):
    style_border = NamedStyle(name="style_border_ca")
    bd = Side(style="thin", color="000000")
    style_border.border = Border(left=bd, top=bd, right=bd, bottom=bd)
    style_border.font = Font(bold=True, size=10)
    style_border.alignment = Alignment(wrap_text=True, horizontal="left", vertical="center")

    style_border2 = NamedStyle(name="style_border2")
    bd = Side(style="thin", color="000000")
    style_border2.font = Font(bold=False, size=12)
    style_border2.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")

    data1 = {
        "custom_fields": ["ФЛГ", "ФГДС", "ЭЭГ", "Тонометрия (старше 40 лет)",	"Маммография"],
        "executor": 'ОГАУЗ "ИГКБ № 9"',
        "customer": 'АО "Иркутсккабель" ',
    }
    # получить ЗАКРЫТЫЕ случаи за дату по компании
    closed_id = closed_company_cases_by_date(data['start_date'], data['end_date'], data['company_id'])

    # стр-ра по закрытм случаям
    # {"id_case_iss": {"fio": "", "sex": "", "birthday": "", "factors": "",
    #                  "custom_researches": {"id_research": "Да|Нет", "id_research": "Да|Нет"},
    #                  "result_researches": {
    #                                         "id_research": {price: "", "factor": ""}, "id_research": {price: "", "factor": ""}
    #                                        }
    #                  }
    #  }
    closed_case_structure_data = {}
    factors_ids = set()
    cases_issledovaniye_ids = {}
    custom_research_ids = data["custom_research"].keys()
    for i in closed_id:
        if not closed_case_structure_data.get(i.issledovaniye_id):
            closed_case_structure_data[i.issledovaniye_id] = {
                "fio": f"{i.patient_family} {i.patient_name} {i.patient_patronymic}",
                "sex": i.sex,
                "birthday": i.patient_birthday,
                "factors": [i.factor_id]}
        else:
            closed_case_structure_data[i.issledovaniye_id]["factors"].append(i.factor_id)
        factors_ids.add(i.factor_id)
        cases_issledovaniye_ids[i.issledovaniye_id] = i.direction_num

    researches_harmfull_factors = researches_by_harmfull_factor_id(tuple(factors_ids))
    # структура уникальных услуг для всех пациентов по все факторам
    harmfull_factors_research_id_title = {i.research_id: i.research_title for i in researches_harmfull_factors}

    # структура факторы - услуги {factor_id: [research_id, research_id]}
    researches_harmfull_data = {}
    for i in researches_harmfull_factors:
        if not researches_harmfull_data.get(i.harmfull_factor_id):
            researches_harmfull_data[i.harmfull_factor_id] = [i.research_id]
        else:
            researches_harmfull_data[i.harmfull_factor_id].append(i.research_id)

    cases_iss = tuple(cases_issledovaniye_ids.keys())
    # получить все исследования, у к-рых в направлении родитель ссылка на случай
    result_iss_id = directions_by_parent_cases_issledovaniye(cases_iss)


    # выполненные исследование все для всех пациентов
    research_issledovaniye_ids = [i.iss_id for i in result_iss_id]

    # поиск результатов для кастомных услуг среди результатов, в каком учреждении оказана услуга
    result_where_done_custom_research_sql = search_value_where_done_custom_research(tuple(research_issledovaniye_ids), tuple(custom_research_ids))

    # взять значения, в каком учреждении пройдено обследование по исследованию
    result_where_done_custom_research = {i.issledovaniye_id: i.result_value for i in result_where_done_custom_research_sql}

    ws1.merge_cells("A8:Q8")
    megre_cell = ws1["A8"]
    megre_cell.value = f"Спецификация {data['executor']}"
    megre_cell.style = style_border2

    ws1.merge_cells("A9:Q9")
    megre_cell = ws1["A9"]
    megre_cell.value = f"Заказчик: {data['customer_title']}"
    megre_cell.style = style_border2

    ws1.merge_cells("A10:Q10")
    megre_cell = ws1["A10"]
    megre_cell.value = f'Реестр оказанных медицинских услуг за период с {data["start_date"]} по {data["end_date"]}'
    megre_cell.style = style_border2

    columns = [
        ("№ п/п", 5),
        ("№ Договора", 20),
        ("ФИО", 40),
        ("Дата рождения", 10),
        ("Пол", 8),
        ("Вид медосмотра (периодическмй / предварительный и т.д.)", 11),
    ]

    columns2 = [(i, 7) for i in data1.get("custom_fields")]
    columns.extend(columns2)
    columns3 = [
        ("Дата оказания услуги", 10),
        ("Диагноз (код по МКБ)", 10),
        ("Код услуги", 12),
        ("Муж", 6),
        ("Жен", 6),
        ("Номер позиции вредности веществ по Приказу №29н", 11),
        ("Специалисты, обследования", 15),
        ("Кол-во, чел", 6),
        ("Тариф, руб.", 12),
        ("Сумма, руб.", 12),
    ]
    columns.extend(columns3)

    row = 13
    for idx, column in enumerate(columns, 1):
        ws1.cell(row=row, column=idx).value = column[0]
        ws1.column_dimensions[get_column_letter(idx)].width = column[1]
        ws1.cell(row=row, column=idx).style = style_border

    return ws1
