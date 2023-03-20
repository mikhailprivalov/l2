from openpyxl.styles import Border, Side, Alignment, Font, NamedStyle
from openpyxl.utils import get_column_letter


def offer_base(ws1):
    style_border = NamedStyle(name="style_border_ca5")
    bd = Side(style='thin', color="000000")
    style_border.border = Border(left=bd, top=bd, right=bd, bottom=bd)
    style_border.font = Font(bold=True, size=11)
    style_border.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')

    columns = [
        ('Услуга', 50),
        ('Количество', 18),
        ('Цена', 18),
        ('Сумма', 18),
    ]

    row = 5
    for idx, column in enumerate(columns, 1):
        ws1.cell(row=row, column=idx).value = column[0]
        ws1.column_dimensions[get_column_letter(idx)].width = column[1]
        ws1.cell(row=row, column=idx).style = style_border

    return ws1


def offer_fill_data(ws1, result_query):
    style_border1 = NamedStyle(name="style_border1")
    bd = Side(style='thin', color="000000")
    style_border1.border = Border(left=bd, top=bd, right=bd, bottom=bd)
    style_border1.font = Font(bold=False, size=11)
    style_border1.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')

    r = 5
    start_row = r + 1
    for i in result_query:
        r += 1
        ws1.cell(row=r, column=1).value = i.get("title", "")
        ws1.cell(row=r, column=2).value = i.get("count", 0)
        ws1.cell(row=r, column=3).value = float(i.get("coast", 0))
        ws1.cell(row=r, column=4).value = f'= {get_column_letter(2)}{r} * {get_column_letter(3)}{r}'


        for j in range(1, 5):
            ws1.cell(row=r, column=j).style = style_border1
    r += 1
    ws1.cell(row=r, column=1).value = 'Итого'
    ws1.cell(row=r, column=4).value = f'=SUM({get_column_letter(4)}{start_row}:{get_column_letter(4)}{r - 1})'
    for j in range(1, 5):
        ws1.cell(row=r, column=j).style = style_border1

    return ws1
