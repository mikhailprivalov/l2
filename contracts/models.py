from decimal import Decimal

from django.db import models

import directory.models as directory
from contracts.sql_func import search_companies


class PriceCategory(models.Model):
    title = models.CharField(max_length=255, unique=True, help_text='Наименование категории Прайса', db_index=True)
    hide = models.BooleanField(default=False, help_text='Скрыть', db_index=True)
    order_weight = models.SmallIntegerField(default=0, verbose_name="Сортировка")

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = 'Категория прайса'
        verbose_name_plural = 'Категории прайса'


class PriceName(models.Model):
    title = models.CharField(max_length=511, unique=True, help_text='Наименование Прайса', db_index=True)
    active_status = models.BooleanField(default=True, help_text='Статус активности', db_index=True)
    date_start = models.DateField(help_text="Дата начала действия докумена", blank=True, null=True)
    date_end = models.DateField(help_text="Дата окончания действия докумена", blank=True, null=True)
    research = models.ManyToManyField(directory.Researches, through='PriceCoast', help_text="Услуга-Прайс", blank=True)

    def __str__(self):
        return "{}".format(self.title)

    def status(self):
        return self.active_status

    class Meta:
        verbose_name = 'Название прайса'
        verbose_name_plural = 'Названия прайса'


class PriceCoast(models.Model):
    price_name = models.ForeignKey(PriceName, on_delete=models.DO_NOTHING, db_index=True)
    research = models.ForeignKey(directory.Researches, on_delete=models.DO_NOTHING, db_index=True)
    coast = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return "{}".format(self.price_name.title)

    @staticmethod
    def get_coast_from_price(dir_research_loc, price_modifier):
        """
        Принимает вид исследования, объект price_modifier: объект прайса, модификатор
        на основании прайса получает базовую цену и умножает на модификатор.
        Возвращает окончательну цену для записи в issledovaniya
        """
        value = 0
        if price_modifier:
            price_name_loc = price_modifier[0]
            price_modifier_loc = price_modifier[1]
            try:
                d = PriceCoast.objects.values_list('coast').get(price_name=price_name_loc, research_id=dir_research_loc)
                res_coast = d[0]
                value = (res_coast * price_modifier_loc).quantize(Decimal("1.00"))
            except PriceCoast.DoesNotExist:
                return value

        return value

    class Meta:
        unique_together = ('price_name', 'research')
        verbose_name = 'Цена прайса'
        verbose_name_plural = 'Цены прайса'


class Contract(models.Model):
    title = models.CharField(max_length=511, unique=True, help_text='Наименование организации', db_index=True)
    number = models.CharField(max_length=255, blank=True, help_text='Номер договора', db_index=False)
    date_start = models.DateField(help_text="Дата начала действия докумена", blank=True, null=True)
    date_end = models.DateField(help_text="Дата окончания действия докумена", blank=True, null=True)
    price = models.ForeignKey(PriceName, blank=True, null=True, db_index=True, on_delete=models.CASCADE)
    modifier = models.DecimalField(max_digits=8, decimal_places=3, default=1, help_text="10000,101")
    active_status = models.BooleanField(default=True, help_text='Действующий', db_index=True)
    show_in_card = models.BooleanField(default=False, help_text='Показывать в карте пациента', db_index=True)
    main = models.BooleanField(default=False, help_text='По умолчанию действует. если несколько.' 'Можно переназначить', db_index=True)

    def __str__(self):
        return "{}".format(self.title)

    class Meta:
        verbose_name = 'Договор'
        verbose_name_plural = 'Договоры'


class Company(models.Model):
    title = models.CharField(max_length=511, unique=True, help_text='Наименование организации', db_index=True)
    short_title = models.CharField(max_length=255, default='', blank=True)
    active_status = models.BooleanField(default=True, help_text='Показывать при выборе', db_index=True)
    legal_address = models.CharField(max_length=511, default='', blank=True)
    fact_address = models.CharField(max_length=511, default='', blank=True)
    inn = models.CharField(max_length=12, default=0, blank=True)
    ogrn = models.CharField(max_length=13, default=0, blank=True)
    kpp = models.CharField(max_length=9, default='', blank=True)
    bik = models.CharField(max_length=9, default='', blank=True)
    contract = models.ForeignKey(Contract, blank=True, null=True, db_index=True, on_delete=models.CASCADE)

    def __str__(self):
        return "{}".format(self.title)

    def get_price(self):
        if self.contract:
            return "{}".format(self.contract.price)
        else:
            return ""

    def get_modifier(self):
        if self.contract:
            return "{}".format(self.contract.modifier)
        else:
            return ""

    @staticmethod
    def search_company(query):
        if not query:
            return []
        company_query = search_companies(company_title=query)
        return [{"id": d.id, "title": d.title} for d in company_query]

    class Meta:
        verbose_name = 'Компания'
        verbose_name_plural = 'Компании'

    @staticmethod
    def as_json(company):
        json_data = {
            "pk": company.pk,
            "title": company.title,
            "shortTitle": company.short_title,
            "legalAddress": company.legal_address,
            "factAddress": company.fact_address,
            "inn": company.inn,
            "ogrn": company.ogrn,
            "kpp": company.kpp,
            "bik": company.bik,
            "contractId": company.contract_id,
        }
        return json_data


class CompanyDepartment(models.Model):
    title = models.CharField(max_length=511, help_text='Наименование отдела', db_index=True)
    hide = models.BooleanField(default=False, help_text='Скрыть', db_index=True)
    company = models.ForeignKey(Company, blank=True, null=True, db_index=True, on_delete=models.CASCADE)

    def __str__(self):
        return "{}".format(self.title)

    @staticmethod
    def search_departments(company_id):
        if not company_id:
            return []
        company_departments = CompanyDepartment.objects.filter(company_id=company_id)
        return [{"id": d.id, "label": d.title} for d in company_departments]

    class Meta:
        verbose_name = 'Отдел компании'
        verbose_name_plural = 'Отделы компаний'
