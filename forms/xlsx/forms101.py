import datetime
from openpyxl import Workbook
import openpyxl
from api.contracts.func import get_confirm_data_for_billing, structure_table
from contracts.models import PriceName, BillingRegister
from forms.xlsx.billing import billing_func

def form_01(request_data) -> Workbook:
    billing_id = request_data.get("billingId")
    wb = openpyxl.Workbook()
    wb.remove(wb.get_sheet_by_name('Sheet'))
    ws = wb.create_sheet("Счет")
    ws.set_printer_settings('9', 'landscape')

    billing_data = BillingRegister.objects.filter(pk=billing_id).first()
    data_confirm_billing = get_confirm_data_for_billing(billing_data.price_id, billing_id)
    structure_data = structure_table(data_confirm_billing)
    ws = billing_func.billing_base(ws, structure_data.get("columns"))
    ws = billing_func.fill_billing(ws, structure_data.get("tableData"))
    return wb
