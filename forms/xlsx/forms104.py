import openpyxl
from openpyxl.workbook import Workbook


def form_01(request_data) -> Workbook:
    wb: Workbook = openpyxl.Workbook()
    wb.remove(wb.get_sheet_by_name("Sheet"))
    ws = wb.create_sheet("Подразделение")
    ws.append(["наименование"])
    return wb
