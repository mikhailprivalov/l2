import datetime
from openpyxl import Workbook

from contracts.models import PriceName
from directory.models import Researches
from forms.sql_func import get_researches, get_coasts, get_prices


def form_01(request_data) -> Workbook:
    price_id = request_data.get("priceId")
    work_book = Workbook()
    work_sheet = work_book[work_book.sheetnames[0]]

    current_day = datetime.datetime.now()
    researches = get_researches()
    if price_id and price_id != 'null':
        prices = PriceName.objects.filter(pk=price_id)
    else:
        prices = get_prices(current_day)
    price_template = {price.id: 0 for price in prices}
    price_ids = tuple(price_template.keys())
    price_titles = [f"{price.title}-{price.symbol_code}" for price in prices]

    research_dict = {}

    for research in researches:
        if Researches.check_exclude(research):
            research_dict[research.id] = {
                "internal_code": research.internal_code,
                "research_title": research.title,
                "research_code": research.code,
                **price_template
            }

    coasts = get_coasts(price_ids)
    for coast in coasts:
        if research_dict.get(coast.research_id):
            research_dict[coast.research_id][coast.price_name_id] = str(coast.coast)

    headers = ["Код по прайсу", "Услуга", "Код ОКМУ"]
    headers.extend(price_titles)
    work_sheet.append(headers)

    [work_sheet.append(list(value.values())) for value in research_dict.values()]

    return work_book
