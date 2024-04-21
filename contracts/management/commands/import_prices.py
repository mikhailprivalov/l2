from django.core.management.base import BaseCommand
from openpyxl import load_workbook
from contracts.models import Company, PriceName
from django.db.models import Q


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        """
        :param path - xlsx файл  со столбцами:
        Плательщик/Контрагент, Тарифный план, Действует С
        """
        fp = kwargs["path"]
        wb = load_workbook(filename=fp)
        ws = wb[wb.sheetnames[0]]
        starts = False
        company_idx, price_name_idx, price_start_idx = '', '', ''
        for row in ws.rows:
            cells = [str(x.value) for x in row]
            if not starts:
                if "Тарифный план" in cells:
                    company_idx = cells.index("Плательщик/Контрагент")
                    price_name_idx = cells.index("Тарифный план")
                    price_start_idx = cells.index("Действует С")
                    starts = True
            else:
                price_title = cells[price_name_idx].strip()
                price_start = cells[price_start_idx].split(" ")[0]
                company_string = cells[company_idx].strip()
                current_price = PriceName.objects.filter(title__iexact=price_title)
                if not current_price.exists():
                    company = Company.objects.filter(Q(title__iexact=company_string) | Q(short_title__iexact=company_string)).first()
                    if company:
                        title_new_price = f"{price_title}-{company.short_title}"
                        new_price = PriceName(title=title_new_price, date_start=price_start, company_id=company.pk)
                        new_price.save()
                        self.stdout.write(f"Прайс {title_new_price} создан")
                    else:
                        self.stdout.write(f"Такого контрагента нет - {company_string}")
                else:
                    self.stdout.write(f"Такой прайс уже есть - {price_title}")
