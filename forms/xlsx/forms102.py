from openpyxl import Workbook
import openpyxl

from api.directions.sql_func import get_lab_podr
from directory.sql_func import get_lab_research_data
from forms.xlsx.lab_research_data import lab_research_func


def form_01(request_data) -> Workbook:
    department_id = request_data.get("departmentId")
    wb = openpyxl.Workbook()
    wb.remove(wb.get_sheet_by_name("Sheet"))
    ws = wb.create_sheet("Счет")
    ws.set_printer_settings("9", "landscape")
    is_int = False
    result_department_id = 0
    lab_podr = get_lab_podr()
    lab_podr = [i[0] for i in lab_podr]
    if type(department_id) is str:
        try:
            result_department_id = int(department_id)
            is_int = True
        except:
            is_int = False
    if is_int and result_department_id > 0 and result_department_id in lab_podr:
        result_department_id = result_department_id
    else:
        result_department_id = 0

    data_lab_research = get_lab_research_data(result_department_id, tuple(lab_podr))
    ws = lab_research_func.lab_report_base(ws)
    ws = lab_research_func.fill_lab_report(ws, data_lab_research)
    return wb
