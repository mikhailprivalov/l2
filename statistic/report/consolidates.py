from openpyxl.styles import Border, Side, Alignment, Font, NamedStyle
from openpyxl.utils import get_column_letter


def consolidate_base(ws1, d1, d2, fin_source):
    style_border = NamedStyle(name="style_border_ca5")
    bd = Side(style='thin', color="000000")
    style_border.border = Border(left=bd, top=bd, right=bd, bottom=bd)
    style_border.font = Font(bold=True, size=11)
    style_border.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')

    ws1.cell(row=1, column=1).value = f'Сводный: {fin_source}'
    ws1.cell(row=2, column=1).value = 'Период:'
    ws1.cell(row=3, column=1).value = f'c {d1} по {d2}'

    columns = [
        ('Номер карты', 10),
        ('Возраст', 8),
        ('Фамилия', 16),
        ('Имя', 16),
        ('Отчество', 16),
        ('Комментарий_в_карте', 20),
        ('Наимен. услуги', 30),
        ('№ напраления', 15),
        ('Дата подтверждения', 15),
        ('Врач', 25),
        ('Место работы', 55),
        ('Профиль_мед.помощи', 15),
        ('Спец_врача', 25),
        ('Основное', 15),
        ('Подчинение', 15),
        ('Цель', 15),
        ('Категория', 25),
    ]

    row = 5
    for idx, column in enumerate(columns, 1):
        ws1.cell(row=row, column=idx).value = column[0]
        ws1.column_dimensions[get_column_letter(idx)].width = column[1]
        ws1.cell(row=row, column=idx).style = style_border

    return ws1


def consolidate_fill_data(ws1, result_query):
    style_border1 = NamedStyle(name="style_border1")
    bd = Side(style='thin', color="000000")
    style_border1.border = Border(left=bd, top=bd, right=bd, bottom=bd)
    style_border1.font = Font(bold=False, size=11)
    style_border1.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')

    r = 5
    tmp_data = {}
    for i in result_query:
        if i.dir_id:
            tmp_data[i.id_iss] = {
                "patient_card_num": i.patient_card_num,
                "patient_age": i.patient_age,
                "patient_family": i.patient_family,
                "patient_name": i.patient_name,
                "patient_patronymic": i.patient_patronymic,
                "dir_harmful_factor": i.dir_harmful_factor,
                "research_title": i.research_title,
                "dir_id": i.dir_id,
                "date_confirm": i.date_confirm,
                "fio": f"{i.doc_f} {i.doc_n} {i.doc_p}",
                "patient_workplace": i.patient_workplace,
                "doc_speciality": i.doc_speciality,
                "purpose": i.purpose,
            }
            r += 1
            ws1.cell(row=r, column=1).value = i.patient_card_num
            ws1.cell(row=r, column=2).value = i.patient_age
            ws1.cell(row=r, column=3).value = i.patient_family
            ws1.cell(row=r, column=4).value = i.patient_name
            ws1.cell(row=r, column=5).value = i.patient_patronymic
            ws1.cell(row=r, column=6).value = i.dir_harmful_factor
            ws1.cell(row=r, column=7).value = i.research_title
            ws1.cell(row=r, column=8).value = i.dir_id
            ws1.cell(row=r, column=9).value = i.date_confirm
            ws1.cell(row=r, column=10).value = f"{i.doc_f} {i.doc_n} {i.doc_p}"
            ws1.cell(row=r, column=11).value = i.patient_workplace
            ws1.cell(row=r, column=12).value = ""
            ws1.cell(row=r, column=13).value = i.doc_speciality
            ws1.cell(row=r, column=14).value = i.id_iss
            ws1.cell(row=r, column=15).value = i.parent_iss
            ws1.cell(row=r, column=16).value = i.purpose
            ws1.cell(row=r, column=17).value = i.category_title
            for j in range(1, 18):
                ws1.cell(row=r, column=j).style = style_border1

        if i.parent_iss:
            data = tmp_data.get(i.parent_iss)
            if not data:
                continue
            r += 1
            ws1.cell(row=r, column=1).value = data["patient_card_num"]
            ws1.cell(row=r, column=2).value = data["patient_age"]
            ws1.cell(row=r, column=3).value = data["patient_family"]
            ws1.cell(row=r, column=4).value = data["patient_name"]
            ws1.cell(row=r, column=5).value = data["patient_patronymic"]
            ws1.cell(row=r, column=6).value = data["dir_harmful_factor"]
            ws1.cell(row=r, column=7).value = i.research_title
            ws1.cell(row=r, column=8).value = data["dir_id"]
            ws1.cell(row=r, column=9).value = data["date_confirm"]
            ws1.cell(row=r, column=10).value = data["fio"]
            ws1.cell(row=r, column=11).value = data["patient_workplace"]
            ws1.cell(row=r, column=12).value = ""
            ws1.cell(row=r, column=13).value = data["doc_speciality"]
            ws1.cell(row=r, column=14).value = i.id_iss
            ws1.cell(row=r, column=15).value = i.parent_iss
            ws1.cell(row=r, column=16).value = data["purpose"]
            ws1.cell(row=r, column=17).value = i.category_title
            for j in range(1, 18):
                ws1.cell(row=r, column=j).style = style_border1

    return ws1
