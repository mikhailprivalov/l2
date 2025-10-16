import calendar
import datetime

import openpyxl
import pytils
from openpyxl.styles import Alignment, Border, Side, Font
from openpyxl.utils import get_column_letter
from openpyxl.workbook import Workbook

from employees.models import TimeTrackingDocument, WorkDayStatus
from hospitals.models import Hospitals


def set_style_for_area(work_sheet, min_row, max_row, min_col, max_col, border_style=None, alignment_style=None):
    for row in work_sheet.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col):
        for cell in row:
            if border_style:
                cell.border = border_style
            if alignment_style:
                cell.alignment = alignment_style


def merge_cells_by_row(work_sheet, start_row, end_row, start_col, end_col):
    """
    Объединяет построчно для каждой колонки в диапозоне
    """
    for col in range(start_col, end_col + 1):
        work_sheet.merge_cells(start_row=start_row, start_column=col, end_row=end_row, end_column=col)


def _set_work_time_sheet_column_widths(work_sheet) -> None:
    work_sheet.column_dimensions['A'].width = 4.17
    work_sheet.column_dimensions['B'].width = 17.5
    work_sheet.column_dimensions['C'].width = 18.83
    work_sheet.column_dimensions['D'].width = 12.7
    work_sheet.column_dimensions['E'].width = 8.7
    work_sheet.column_dimensions['F'].width = 9.5
    work_sheet.column_dimensions['G'].width = 6.5
    date_cols = []
    col_h_number = 8
    col_al_number = 38
    for col_number in range(col_h_number, col_al_number + 1):
        date_cols.append(get_column_letter(col_number))
    for col_number in date_cols:
        work_sheet.column_dimensions[col_number].width = 5.33
    work_sheet.column_dimensions['AM'].width = 9.83
    work_sheet.column_dimensions['AN'].width = 11.33


def _create_work_time_sheet_header_meta(context):
    work_sheet = context.get("work_sheet")
    alignment_center = context.get("alignment_center")
    font_bold = context.get("font_bold")
    organization_title = context.get("organization_title")
    department_title = context.get("department_title")
    thin_bottom_border = context.get("thin_bottom_border")
    document_year = context.get("document_year")
    document_month_name = context.get("document_month_name")
    document_last_day_month = context.get("document_last_day_month")
    current_date = datetime.datetime.now()
    current_month_name = pytils.dt.ru_strftime(u"%B", inflected=True, date=current_date)
    current_day = current_date.day
    current_year = current_date.year

    work_sheet["AL1"] = "Приложение № 2 к"
    work_sheet["B2"] = "Председатель ППО"
    work_sheet["C2"] = "________________"
    work_sheet["AD2"] = "УТВЕРЖДАЮ"
    work_sheet["AL2"] = "приказу от '20' февраля 2025 г № 37"
    work_sheet.merge_cells('A3:AC3')
    work_sheet["A3"].alignment = alignment_center
    work_sheet["A3"].font = font_bold
    work_sheet["A3"] = "ГРАФИК РАБОЧЕГО ВРЕМЕНИ"
    work_sheet["AD3"].font = font_bold
    work_sheet["AD3"] = "Руководитель учреждения ______________________"
    work_sheet["AK4"] = "подпись"
    work_sheet.merge_cells('A5:AC5')
    work_sheet["A5"].alignment = alignment_center
    work_sheet["A5"].font = font_bold
    work_sheet["A5"] = organization_title
    work_sheet["AF5"].font = font_bold
    work_sheet["AF5"] = f'"{current_day}"{current_month_name} {current_year}г.'
    work_sheet.merge_cells('A7:AC7')
    work_sheet["A7"].alignment = alignment_center
    work_sheet["A7"].font = font_bold
    work_sheet["A7"] = department_title
    cell_a_number = 1
    cell_ag_number = 33
    set_style_for_area(work_sheet, 7, 7, cell_a_number, cell_ag_number, thin_bottom_border)
    work_sheet["AD7"] = f"календарных дней {document_last_day_month}"
    work_sheet.merge_cells('A8:AC8')
    work_sheet["A8"].alignment = alignment_center
    work_sheet["A8"] = "(подразделение)"
    work_sheet["AD8"] = "рабочих дней"
    cell_ad_number = 30
    set_style_for_area(work_sheet, 8, 8, cell_ad_number, cell_ag_number, thin_bottom_border)
    work_sheet.merge_cells('A9:AC9')
    work_sheet["A9"].alignment = alignment_center
    work_sheet["A9"] = f"{document_month_name} {document_year} год"


def _create_work_time_sheet_table_header(context):
    work_sheet = context.get("work_sheet")
    first_row_number = context.get("first_row_number")
    second_row_number = context.get("second_row_number")
    item_number_col_number = context.get("item_number_col_number")
    fio_col_number = context.get("fio_col_number")
    position_col_number = context.get("position_col_number")
    type_employment_col_number = context.get("type_employment_col_number")
    occupied_volume_col_number = context.get("occupied_volume_col_number")
    norm_hours_col_number = context.get("norm_hours_col_number")
    working_shift_col_number = context.get("working_shift_col_number")
    start_date_col_number = context.get("start_date_col_number")
    end_date_col_number = context.get("end_date_col_number")
    amount_hours_col_number = context.get("amount_hours_col_number")
    employees_signature_col_number = context.get("employees_signature_col_number")
    document_last_day_month = context.get("document_last_day_month")

    merge_cells_by_row(work_sheet, first_row_number, second_row_number, item_number_col_number, working_shift_col_number)
    work_sheet.merge_cells(start_row=first_row_number, start_column=start_date_col_number, end_row=first_row_number, end_column=end_date_col_number)
    merge_cells_by_row(work_sheet, first_row_number, second_row_number, amount_hours_col_number, employees_signature_col_number)

    work_sheet.cell(row=first_row_number, column=item_number_col_number, value="№ п/п")
    work_sheet.cell(row=first_row_number, column=fio_col_number, value="Фамилия имя отчество")
    work_sheet.cell(row=first_row_number, column=position_col_number, value="Должность (профессия)")
    work_sheet.cell(row=first_row_number, column=type_employment_col_number, value="Вид занятости (осн, внутр, внеш)")
    work_sheet.cell(row=first_row_number, column=occupied_volume_col_number, value="Занимаемый объем (согл ТД), шт ед")
    work_sheet.cell(row=first_row_number, column=norm_hours_col_number, value="Норма часов на занимаемый объем")
    work_sheet.cell(row=first_row_number, column=working_shift_col_number, value="Рабочая смена")
    work_sheet.cell(row=first_row_number, column=start_date_col_number, value="Числа месяца")
    work_sheet.cell(row=first_row_number, column=amount_hours_col_number, value="Количество часов согласно графика")
    work_sheet.cell(row=first_row_number, column=employees_signature_col_number, value="Подпись работника")
    for date_number in range(document_last_day_month):
        work_sheet.cell(row=second_row_number, column=date_number + start_date_col_number, value=date_number + 1)


def _create_work_time_sheet_table(context) -> None:
    work_sheet = context.get("work_sheet")
    document_last_day_month = context.get("document_last_day_month")
    thin_border = context.get("thin_border")
    alignment_center_wrap = context.get("alignment_center_wrap")
    alignment_left_wrap = context.get("alignment_left_wrap")
    employees_work_time = context.get("employees_work_time")
    work_day_statuses = context.get("work_day_statuses")
    first_row_number = 12
    second_row_number = 13
    third_row_number = 14
    data_end_row_number = third_row_number + len(employees_work_time)
    item_number_col_number = 1
    fio_col_number = 2
    position_col_number = 3
    type_employment_col_number = 4
    occupied_volume_col_number = 5
    norm_hours_col_number = 6
    working_shift_col_number = 7
    start_date_col_number = 8
    end_date_col_number = start_date_col_number + document_last_day_month - 1
    amount_hours_col_number = end_date_col_number + 1
    employees_signature_col_number = amount_hours_col_number + 1

    set_style_for_area(work_sheet, first_row_number, data_end_row_number, item_number_col_number, employees_signature_col_number, thin_border, alignment_center_wrap)
    set_style_for_area(work_sheet, third_row_number, data_end_row_number, fio_col_number, fio_col_number, alignment_style=alignment_left_wrap)

    header_table_context = {
        "work_sheet": work_sheet,
        "first_row_number": first_row_number,
        "second_row_number": second_row_number,
        "item_number_col_number": item_number_col_number,
        "fio_col_number": fio_col_number,
        "position_col_number": position_col_number,
        "type_employment_col_number": type_employment_col_number,
        "occupied_volume_col_number": occupied_volume_col_number,
        "norm_hours_col_number": norm_hours_col_number,
        "working_shift_col_number": working_shift_col_number,
        "start_date_col_number": start_date_col_number,
        "end_date_col_number": end_date_col_number,
        "amount_hours_col_number": amount_hours_col_number,
        "employees_signature_col_number": employees_signature_col_number,
        "document_last_day_month": document_last_day_month
    }
    _create_work_time_sheet_table_header(header_table_context)


def form_01(request_data) -> Workbook:
    """
    Создает xlsx файл по форме графика рабочего времени
    """
    # TODO подумать как разбить по страницам

    request_body = request_data.get("request_body")
    document_id = request_body.get("documentId")
    employees_work_time = request_body.get("employeesWorkTime")
    time_tracking_document: TimeTrackingDocument = TimeTrackingDocument.get_document_for_print(document_id)
    work_day_statuses = WorkDayStatus.get_short_statuses_dict()
    document_date = time_tracking_document.month
    document_month_name = pytils.dt.ru_strftime(u"%B", date=document_date)
    document_year = document_date.year
    document_month = document_date.month
    document_last_day_month = calendar.monthrange(document_year, document_month)[1]
    department_title = time_tracking_document.department.name
    organization: Hospitals = request_data.get("hospital")
    organization_title = organization.safe_short_title

    thin_line = Side(style='thin')
    thin_bottom_border = Border(bottom=thin_line)
    thin_border = Border(left=thin_line, top=thin_line, right=thin_line, bottom=thin_line)
    alignment_center = Alignment(horizontal='center', vertical='center')
    alignment_center_wrap = Alignment(horizontal='center', vertical='center', wrap_text=True)
    alignment_left_wrap = Alignment(horizontal='left', vertical='center', wrap_text=True)
    font_bold = Font(bold=True)

    work_book: Workbook = openpyxl.Workbook()
    work_book.remove(work_book.get_sheet_by_name("Sheet"))
    work_sheet = work_book.create_sheet(f"{department_title}")
    _set_work_time_sheet_column_widths(work_sheet)

    meta_context = {
        "work_sheet": work_sheet,
        "alignment_center": alignment_center,
        "font_bold": font_bold,
        "thin_bottom_border": thin_bottom_border,
        "document_year": document_year,
        "document_month_name": document_month_name,
        "document_last_day_month": document_last_day_month,
        "organization_title": organization_title,
        "department_title": department_title,
    }
    _create_work_time_sheet_header_meta(meta_context)
    table_context = {
        "work_sheet": work_sheet,
        "document_last_day_month": document_last_day_month,
        "thin_border": thin_border,
        "alignment_center_wrap": alignment_center_wrap,
        "alignment_left_wrap": alignment_left_wrap,
        "employees_work_time": employees_work_time,
        "work_day_statuses": work_day_statuses
    }
    _create_work_time_sheet_table(table_context)

    return work_book
