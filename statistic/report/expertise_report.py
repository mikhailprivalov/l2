from openpyxl.styles import Border, Side, Alignment, Font, NamedStyle
from openpyxl.utils import get_column_letter


def expertise_base(ws1):
    style_border = NamedStyle(name="style_border_ca")
    bd = Side(style='thin', color="000000")
    style_border.border = Border(left=bd, top=bd, right=bd, bottom=bd)
    style_border.font = Font(bold=True, size=12)
    style_border.alignment = Alignment(wrap_text=True, horizontal='justify', vertical='center')

    ws1.cell(row=1, column=1).value = 'Пациентов на Д-учете'

    columns = [
        ('Взрослые 18 и старше', 25),
        ('Дети до 0-17 лет', 25),
    ]
    for idx, column in enumerate(columns, 1):
        ws1.cell(row=4, column=idx).value = column[0]
        ws1.column_dimensions[get_column_letter(idx)].width = column[1]
        ws1.cell(row=4, column=idx).style = style_border

    return ws1


def expertise_data(ws1):
    style_border1 = NamedStyle(name="style_border1")
    bd = Side(style='thin', color="000000")
    style_border1.border = Border(left=bd, top=bd, right=bd, bottom=bd)
    style_border1.font = Font(bold=False, size=11)
    style_border1.alignment = Alignment(wrap_text=True, horizontal='left', vertical='center')

    return ws1