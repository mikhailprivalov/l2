import datetime

from django.db.models import Q
from openpyxl import Workbook

from contracts.models import PriceCoast, PriceName
from directory.models import Researches


def form_01(request_data) -> Workbook:
    work_book = Workbook()
    work_sheet = work_book[work_book.sheetnames[0]]
    current_day = datetime.datetime.now()
    active_prices = PriceName.objects.filter(Q(date_end__gte=current_day) | Q(date_end=None)).order_by('title')
    researches = Researches.objects.filter(hide=False, internal_code__isnull=False).order_by('internal_code')
    column = {"internal_code": "Код по прайсу", "title": "Услуга", "code": "Код ОКМУ"}
    price = {price.symbol_code: f"{price.title}-{price.symbol_code}" for price in active_prices}
    column.update(price)
    work_sheet.append(list(column.values()))
    for research in researches:
        tmp = {"internal_code": research.internal_code, "title": research.title, "code": research.code}
        for price in active_prices:
            value = 0
            research_coast: PriceCoast = PriceCoast.objects.filter(research_id=research.pk, price_name_id=price.pk).first()
            if research_coast:
                value = research_coast.coast
            tmp[price.symbol_code] = value
        work_sheet.append(list(tmp.values()))

    return work_book
