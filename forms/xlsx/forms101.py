from openpyxl import Workbook
from api.contracts.func import researches_for_billing, structure_table


def form_01(request_data) -> Workbook:
    # Проект счета
    hospital_id = request_data.get("hospitalId")
    date_start = request_data.get("dateStart")
    date_end = request_data.get("dateEnd")
    type_price = request_data.get("typeCompany")
    data = researches_for_billing(type_price, hospital_id, date_start, date_end)
    structure_data = structure_table(data)
    work_book = Workbook()
    work_sheet = work_book[work_book.sheetnames[0]]


    headers = ["№", "Пациент", "Дата рожд.", "Дата вып.", "Код", "Код НМУ", "Наименование услуги", "Лаб. номер", "Кол.", "Цена", "Стоимость, руб"]
    work_sheet.append(headers)
    [work_sheet.append(list(v.values())) for v in structure_data]

    return work_book
