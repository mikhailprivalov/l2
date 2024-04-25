from openpyxl import Workbook


def form_01(request_data) -> Workbook:
    wb = Workbook()
    ws = wb[wb.sheetnames[0]]
    a1 = ws.cell(row=1, column=1)
    a1.value = 'Привет_МИР!'
    return wb
