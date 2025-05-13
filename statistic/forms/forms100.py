from copy import deepcopy
import openpyxl
from openpyxl.styles import Border, Side, Alignment, Font, NamedStyle
from openpyxl.utils import get_column_letter
from directory.models import Researches
from utils.dates import normalize_date
from statistic.forms.forms100_sql_func import closed_company_cases_by_date


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

    closed_id = closed_company_cases_by_date(data['start_date'], data['end_date'], data['company_id'])

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
