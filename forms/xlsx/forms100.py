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

    price_template = {}
    price_titles = []
    for price in prices:
        price_template[price.id] = 0
        price_template[f"{price.id}_cito"] = ""
        price_titles.append(f"{price.title}-{price.symbol_code}")
        price_titles.append(f"{price.title}-{price.symbol_code} ЦИТО")

    price_ids = tuple(price.id for price in prices)

    research_dict = {}

    for research in researches:
        if Researches.check_exclude(research):
            research_dict[research.id] = {
                "internal_code": research.internal_code,
                "research_title": research.title,
                "research_code": research.code,
                "fsidi": research.nsi_id,
                "category": research.categoty_title,
                "short_title": research.short_title,
                **price_template,
            }

    coasts = get_coasts(price_ids) if price_ids else []
    for coast in coasts:
        if research_dict.get(coast.research_id):
            research_dict[coast.research_id][coast.price_name_id] = str(coast.coast)
            research_dict[coast.research_id][f"{coast.price_name_id}_cito"] = str(coast.coast_cito) if coast.coast_cito is not None else ""

    headers = ["Код по прайсу", "Услуга", "Код НМУ", "ФСИДИ", "Категория", "Короткое название"]
    headers.extend(price_titles)
    work_sheet.append(headers)

    [work_sheet.append(list(value.values())) for value in research_dict.values()]

    return work_book
