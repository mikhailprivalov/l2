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
        Плательщик/Контрагент, Тариф, Действует С
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
                    price_name_idx = cells.index("Тариф")
                    price_start_idx = cells.index("Действует С")
                    starts = True
            else:
                price_title = None
                current_price = None
                price_start = cells[price_start_idx].split(" ")[0]
                company_string = cells[company_idx].strip()
                company = Company.objects.filter(Q(title__iexact=company_string) | Q(short_title__iexact=company_string)).first()
                if company:
                    price_title = f"{cells[price_name_idx].strip()}-{company.short_title}"
                if price_title:
                    current_price = PriceName.objects.filter(title__iexact=price_title)
                if not current_price.exists():
                    new_price = PriceName(title=price_title, date_start=price_start, company_id=company.pk)
                    new_price.save()
                    self.stdout.write(f"Прайс {price_title} создан")
                else:
                    self.stdout.write(f"Такой прайс уже есть - {price_title}")
