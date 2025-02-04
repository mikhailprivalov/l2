import openpyxl
from openpyxl.workbook import Workbook

from researches.models import Tubes


def form_01(request_data) -> Workbook:
    wb: Workbook = openpyxl.Workbook()
    wb.remove(wb.get_sheet_by_name("Sheet"))
    ws = wb.create_sheet("Ёмкости для биоматериала")
    tubes = Tubes.get_all()
    ws.append(["Наименование", "Код", "Цвет (RGB, hex)"])
    for tube in tubes:
        ws.append([tube["label"], tube["shortLabel"], tube["color"]])
    return wb
