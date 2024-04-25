import datetime
import time

from django.db.models import Q
from openpyxl import Workbook

from contracts.models import PriceCoast, PriceName
from directory.models import Researches
from forms.sql_func import get_researches, get_coasts


def form_01(request_data) -> Workbook:
    start_time = time.time()
    work_book = Workbook()
    work_sheet = work_book[work_book.sheetnames[0]]

    current_day = datetime.datetime.now()
    researches = get_researches()
    prices = PriceName.objects.filter(Q(date_end__gte=current_day) | Q(date_end__isnull=True)).order_by('id')
    price_template = {}
    price_titles = []
    for price in prices:
        price_template[price.pk] = 0
        price_titles.append(price.title)
    research_dict = {research.id: {"internal_code": research.internal_code, "research_title": research.title, "research_code": research.code, **price_template} for research in researches}

    coasts = get_coasts(current_day)
    for coast in coasts:
        research_dict[coast.research_id][coast.price_name_id] = str(coast.coast)

    headers = ["Код по прайсу", "Услуга", "Код ОКМУ"]
    headers.extend(price_titles)
    work_sheet.append(headers)
    for value in research_dict.values():
        work_sheet.append(list(value.values()))

    print("--- %s seconds ---" % (time.time() - start_time))
    return work_book
