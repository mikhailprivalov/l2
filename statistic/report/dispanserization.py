from openpyxl.styles import Border, Side, Alignment, Font, NamedStyle
from openpyxl.utils import get_column_letter


def dispanserization_data(query_sql, pk_service_start, pk_service_end):
    dates = [i.confirm_time for i in query_sql]
    dates = sorted(set(dates))
    dates_val = [{"val_start": 0, "val_end": 0} for i in range(len(dates))]
    result = []
    prev_doc = None
    step = 0
    current_tmp_data = {}
    for i in query_sql:
        current_index = dates.index(i.confirm_time)
        if i.doc_confirmation_id != prev_doc:
            if step != 0:
                result.append(current_tmp_data.copy())
            current_doc = {"fio_doc": i.fio_doctor, "dates": dates.copy(), "dates_val": dates_val.copy()}
            tmp_val = current_doc.get("dates_val", [])[current_index]
            if i.research_id in pk_service_start:
                tmp_val["val_start"] += 1
            else:
                tmp_val["val_end"] += 1
            current_doc["dates_val"][current_index] = tmp_val.copy()
            current_tmp_data = {i.doc_confirmation_id: current_doc.copy()}

        current_doc = current_tmp_data.get(i.doc_confirmation_id)
        tmp_val = current_doc.get("dates_val", [])[current_index]
        if i.research_id in pk_service_start:
            tmp_val["val_start"] += 1
        else:
            tmp_val["val_end"] += 1
        current_doc.get("dates_val", [])[current_index] = tmp_val.copy()
        current_tmp_data = {i.doc_confirmation_id: current_doc.copy()}
        prev_doc = i.doc_confirmation_id
        step += 1
    result.append(current_tmp_data.copy())

    return {"result": result, "dates": list(dates)}


def dispanserization_base(ws1, d1, d2, result_query):
    style_border = NamedStyle(name="style_border_ca")
    bd = Side(style='thin', color="000000")
    style_border.border = Border(left=bd, top=bd, right=bd, bottom=bd)
    style_border.font = Font(bold=True, size=11)
    style_border.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')

    ws1.cell(row=1, column=1).value = 'Диспансеризация:'
    ws1.cell(row=2, column=1).value = 'Период:'
    ws1.cell(row=3, column=1).value = f'c {d1} по {d2}'

    columns = [("Врач", 40)]
    columns_date = [("", 40)]
    for i in result_query["dates"]:
        columns.append(("начато", 8))
        columns.append(("завершено", 13))
        columns_date.append((i, 10))
        columns_date.append(("", 15))

    for idx, column in enumerate(columns, 1):
        ws1.cell(row=6, column=idx).value = column[0]
        ws1.column_dimensions[get_column_letter(idx)].width = column[1]
        ws1.cell(row=6, column=idx).style = style_border

    for idx, column in enumerate(columns_date, 1):
        ws1.cell(row=5, column=idx).value = column[0]
        ws1.column_dimensions[get_column_letter(idx)].width = column[1]
        ws1.cell(row=5, column=idx).style = style_border

    column_count = 0
    for i in result_query["dates"]:
        column_count += 2
        ws1.merge_cells(start_row=5, start_column=column_count, end_row=5, end_column=column_count + 1)

    return ws1


def dispanserization_fill_data(ws1, result_query):
    style_border1 = NamedStyle(name="style_border1")
    bd = Side(style='thin', color="000000")
    style_border1.border = Border(left=bd, top=bd, right=bd, bottom=bd)
    style_border1.font = Font(bold=False, size=11)
    style_border1.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')


    alignment1 = Alignment(wrap_text=True, horizontal='left', vertical='center')
    len_dates_count = len(result_query["dates"]) * 2

    r = 6
    start_row = r + 1
    for i in result_query["result"]:
        r += 1
        for k in i.values():
            ws1.cell(row=r, column=1).value = k["fio_doc"]
            column = 1
            for j in k["dates_val"]:
                column += 1
                ws1.cell(row=r, column=column).value = j["val_start"]
                column += 1
                ws1.cell(row=r, column=column).value = j["val_end"]

        for z in range(1, len_dates_count + 2):
            ws1.cell(row=r, column=z).style = style_border1
            ws1.cell(row=r, column=1).alignment = alignment1

    column = 1
    r += 1

    ws1.cell(row=r, column=column).value = "Итого"
    ws1.cell(row=r, column=column).style = style_border1
    ws1.cell(row=r, column=column).alignment = alignment1

    for i in range(len_dates_count):
        column += 1
        ws1.cell(row=r, column=column).value = f'=SUM({get_column_letter(column)}{start_row}:{get_column_letter(column)}{r - 1})'
        ws1.cell(row=r, column=column).style = style_border1

    return ws1
