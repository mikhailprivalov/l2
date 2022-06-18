from openpyxl.styles import Border, Side, Alignment, Font, NamedStyle
from openpyxl.utils.cell import get_column_letter


def monitoring_xlsx(ws1):
    """
    :param ws1:
    :return:
    """
    style_border = NamedStyle(name="style_border")
    bd = Side(style='thin', color="000000")
    style_border.border = Border(left=bd, top=bd, right=bd, bottom=bd)
    style_border.font = Font(bold=False, size=12)
    style_border.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')

    header_size = 8
    ws1.merge_cells(start_row=1, start_column=1, end_row=1, end_column=header_size)
    ws1.cell(row=1, column=1).value = 'Мониторинг - 12121, от 21112122'
    ws1.cell(row=1, column=1).style = style_border

    return ws1
