import datetime
from openpyxl import Workbook

from forms.sql_func import get_researches, get_coasts, get_prices


def form_01(request_data) -> Workbook:
    work_book = Workbook()
    work_sheet = work_book[work_book.sheetnames[0]]

    current_day = datetime.datetime.now()
    researches = get_researches()
    prices = get_prices(current_day)
    price_template = {price.id: 0 for price in prices}
    price_ids = tuple(price_template.keys())
    price_titles = [f"{price.title}-{price.symbol_code}" for price in prices]

    research_dict = {research.id: {"internal_code": research.internal_code, "research_title": research.title, "research_code": research.code, **price_template} for research in researches}

    coasts = get_coasts(price_ids)
    for coast in coasts:
        research_dict[coast.research_id][coast.price_name_id] = str(coast.coast)

    headers = ["Код по прайсу", "Услуга", "Код ОКМУ"]
    headers.extend(price_titles)
    work_sheet.append(headers)

    [work_sheet.append(list(value.values())) for value in research_dict.values()]

    return work_book
