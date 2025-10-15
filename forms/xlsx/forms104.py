import openpyxl
from openpyxl.styles import Alignment, Border, Side, Font
from openpyxl.utils import get_column_letter
from openpyxl.workbook import Workbook


def add_thin_bottom_border(work_sheet, border_style, row_number, start_col_number, end_col_number):
    for col in range(start_col_number, end_col_number + 1):
        cell = work_sheet.cell(row=row_number, column=col)
        cell.border = border_style


def _set_work_time_sheet_column_widths(work_sheet):
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


def form_01(request_data) -> Workbook:

    organization_title = "ОГАУЗ ГИМДКБ"  # TODO получать динамически
    department_title = "Травмпункт"  # TODO получать динамически

    thin_bottom_border = Border(bottom=Side(style='thin'))
    alignment_center = Alignment(horizontal='center', vertical='center')
    font_bold = Font(bold=True)

    work_book: Workbook = openpyxl.Workbook()
    work_book.remove(work_book.get_sheet_by_name("Sheet"))
    work_sheet = work_book.create_sheet("Подразделение")
    _set_work_time_sheet_column_widths(work_sheet)

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
    work_sheet["AF5"] = '"_____" ___________________ 20____ г.'
    work_sheet.merge_cells('A7:AC7')
    work_sheet["A7"].alignment = alignment_center
    work_sheet["A7"].font = font_bold
    work_sheet["A7"] = department_title
    cell_a_number = 1
    cell_ag_number = 33
    add_thin_bottom_border(work_sheet, thin_bottom_border, 7, cell_a_number, cell_ag_number)
    work_sheet["AD7"] = "календарных дней"
    work_sheet.merge_cells('A8:AC8')
    work_sheet["A8"].alignment = alignment_center
    work_sheet["A8"] = "(подразделение)"
    work_sheet["AD8"] = "рабочих дней"
    cell_ad_number = 30
    add_thin_bottom_border(work_sheet, thin_bottom_border, 8, cell_ad_number, cell_ag_number)
    work_sheet.merge_cells('A9:AC9')
    work_sheet["A9"].alignment = alignment_center
    work_sheet["A9"] = "_______________ 20      год"

    return work_book
