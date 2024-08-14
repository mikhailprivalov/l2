from openpyxl import Workbook
import openpyxl
from api.contracts.func import get_confirm_data_for_billing, structure_table
from contracts.models import BillingRegister
from directory.sql_func import get_lab_research_data
from forms.xlsx.lab_research_data import lab_research_func


def form_01(request_data) -> Workbook:
    department_id = request_data.get("departmentId")
    wb = openpyxl.Workbook()
    wb.remove(wb.get_sheet_by_name("Sheet"))
    ws = wb.create_sheet("Счет")
    ws.set_printer_settings("9", "landscape")

    data_lab_research = get_lab_research_data(department_id)
    ws = lab_research_func.lab_report_base(ws)
    ws = lab_research_func.fill_lab_report(ws, data_lab_research)
    return wb
