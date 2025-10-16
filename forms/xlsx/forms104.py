import calendar
import datetime

import openpyxl
import pytils
from openpyxl.styles import Alignment, Border, Side, Font
from openpyxl.utils import get_column_letter
from openpyxl.workbook import Workbook

from employees.models import TimeTrackingDocument, WorkDayStatus
from hospitals.models import Hospitals


def set_thin_bottom_border(work_sheet, border_style: Border, row_number: int, start_col_number: int, end_col_number: int) -> None:
    for col in range(start_col_number, end_col_number + 1):
        cell = work_sheet.cell(row=row_number, column=col)
        cell.border = border_style


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
    set_thin_bottom_border(work_sheet, thin_bottom_border, 7, cell_a_number, cell_ag_number)
    work_sheet["AD7"] = f"календарных дней {document_last_day_month}"
    work_sheet.merge_cells('A8:AC8')
    work_sheet["A8"].alignment = alignment_center
    work_sheet["A8"] = "(подразделение)"
    work_sheet["AD8"] = "рабочих дней"
    cell_ad_number = 30
    set_thin_bottom_border(work_sheet, thin_bottom_border, 8, cell_ad_number, cell_ag_number)
    work_sheet.merge_cells('A9:AC9')
    work_sheet["A9"].alignment = alignment_center
    work_sheet["A9"] = f"{document_month_name} {document_year} год"


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

    thin_bottom_border = Border(bottom=Side(style='thin'))
    alignment_center = Alignment(horizontal='center', vertical='center')
    font_bold = Font(bold=True)

    work_book: Workbook = openpyxl.Workbook()
    work_book.remove(work_book.get_sheet_by_name("Sheet"))
    work_sheet = work_book.create_sheet(f"{department_title}")  # TODO название отделения
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

    return work_book
