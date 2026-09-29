from openpyxl.styles import Border, Side, Alignment, Font, NamedStyle
from openpyxl.utils.cell import get_column_letter
import json


def monitoring_direction_xlsx(ws1, header, groups):
    label_font = Font(name="Times New Roman", size=14, bold=True)
    value_font = Font(name="Times New Roman", size=14, bold=False)
    label_align = Alignment(horizontal="left", vertical="center", wrap_text=True)
    value_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    table_font = Font(name="Calibri", size=12, bold=False)
    table_align = Alignment(horizontal="left", vertical="center", wrap_text=True)
    thin = Side(style="thin", color="000000")
    border = Border(left=thin, top=thin, right=thin, bottom=thin)

    ws1.column_dimensions["A"].width = 46.6640625
    ws1.column_dimensions["B"].width = 84.99609375
    ws1.column_dimensions["C"].width = 26.6640625

    header_rows = (
        ("Название мониторинга", header.get("title") or ""),
        ("Параметры направления", header.get("params") or ""),
        ("Медицинская организация", header.get("hospital") or ""),
        ("Дата отчета", header.get("report_date") or ""),
        ("Дата заполнения", header.get("filled_at") or ""),
    )
    for index, (label, value) in enumerate(header_rows, start=1):
        ws1.merge_cells(start_row=index, start_column=2, end_row=index, end_column=3)
        label_cell = ws1.cell(row=index, column=1, value=label)
        label_cell.font = label_font
        label_cell.alignment = label_align
        value_cell = ws1.cell(row=index, column=2, value=value)
        value_cell.font = value_font
        value_cell.alignment = value_align
        merged_cell = ws1.cell(row=index, column=3)
        merged_cell.font = value_font
        merged_cell.alignment = value_align
        line_count = max(1, str(label).count("\n") + 1, str(value).count("\n") + 1)
        ws1.row_dimensions[index].height = max(36, 36 * line_count)

    current_row = 7
    for column, title in enumerate(("Группа", "Поле", "Значение"), start=1):
        cell = ws1.cell(row=current_row, column=column, value=title)
        cell.font = table_font
        cell.alignment = table_align
        cell.border = border
    ws1.row_dimensions[current_row].height = 36

    for group in groups:
        current_row += 1
        _write_monitoring_table_row(ws1, current_row, group.get("title") or "", None, None, table_font, table_align, border)
        for field in group.get("fields") or []:
            current_row += 1
            _write_monitoring_table_row(ws1, current_row, None, field.get("title") or "", field.get("value") or "", table_font, table_align, border)

    return ws1


def _write_monitoring_table_row(ws1, row, group_title, field_title, field_value, font, alignment, border):
    values = (group_title, field_title, field_value)
    line_count = 1
    for column, value in enumerate(values, start=1):
        cell = ws1.cell(row=row, column=column, value=value or None)
        cell.font = font
        cell.alignment = alignment
        cell.border = border
        line_count = max(line_count, str(value or "").count("\n") + 1)
    ws1.row_dimensions[row].height = max(36, 32 * line_count)


def monitoring_xlsx(ws1, monitoring_title, table_data, date):
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
    ws1.cell(row=1, column=1).value = f'Мониторинг - {monitoring_title}, от {date}'
    for i in range(header_size):
        ws1.cell(row=1, column=1 + i).style = style_border

    ws1.column_dimensions[get_column_letter(1)].width = 22

    current_row = 3
    ws1.cell(row=current_row, column=1).value = "МО"
    ws1.cell(row=current_row, column=1).style = style_border

    current_column = 2
    # строим заголовки
    for column_group in table_data['titles']:
        end_column = current_column + len(column_group['fields']) - 1
        # Заголовок группы
        ws1.merge_cells(start_row=current_row, start_column=current_column, end_row=current_row, end_column=end_column)
        ws1.cell(row=current_row, column=current_column).value = f'{column_group["groupTitle"]}'
        for i in range(end_column - current_column + 1):
            ws1.cell(row=current_row, column=current_column + i).style = style_border

        # Заголовок поля
        current_row += 1
        current_column = end_column - len(column_group['fields'])
        for field_colimn in column_group['fields']:
            current_column += 1
            ws1.column_dimensions[get_column_letter(current_column)].width = 15
            ws1.cell(row=current_row, column=current_column).value = f'{field_colimn}'
            ws1.cell(row=current_row, column=current_column).style = style_border
        current_row -= 1
        current_column += 1

    current_column = 1
    current_row += 1
    is_show_tables_title = False
    json_data = {}
    for row in table_data['rows']:
        current_row += 1
        ws1.cell(row=current_row, column=current_column).value = row['hospTitle']
        ws1.cell(row=current_row, column=current_column).style = style_border
        for value in row['values']:
            for v in value:
                is_dict = False
                if type(v) is str and "columns" in v:
                    try:
                        json_data = json.loads(v)
                        is_dict = True
                    except:
                        is_dict = False
                if not is_dict:
                    current_column += 1
                    ws1.cell(row=current_row, column=current_column).value = v
                    ws1.cell(row=current_row, column=current_column).style = style_border
                if is_dict:
                    col_title_data = json_data.get("columns")
                    col_title = col_title_data.get("titles")
                    start_col = current_column
                    if not is_show_tables_title:
                        for c_title in col_title:
                            start_col += 1
                            ws1.cell(row=current_row - 1, column=start_col).value = c_title
                            ws1.cell(row=current_row - 1, column=start_col).style = style_border
                            is_show_tables_title = True
                    rows_data = json_data.get("rows")
                    for r_data in rows_data:
                        start_col = current_column
                        for rd in r_data:
                            start_col += 1
                            ws1.cell(row=current_row, column=start_col).value = rd
                            ws1.cell(row=current_row, column=start_col).style = style_border
                        current_row += 1
        current_column = 1

    current_row += 1
    current_column = 1
    ws1.cell(row=current_row, column=current_column).value = "Итого"
    ws1.cell(row=current_row, column=current_column).style = style_border

    for total in table_data['total']:
        for v in total:
            current_column += 1
            ws1.cell(row=current_row, column=current_column).value = v
            ws1.cell(row=current_row, column=current_column).style = style_border

    current_row += 2
    current_column = 1
    for empty_hospital in table_data['empty_hospital']:
        current_row += 1
        ws1.cell(row=current_row, column=current_column).value = empty_hospital

    return ws1
