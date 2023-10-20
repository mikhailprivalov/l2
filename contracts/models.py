import calendar
import datetime
from decimal import Decimal

from django.db import models

import directory.models as directory
from contracts.sql_func import search_companies, get_examination_data
from clients.models import Card


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
    date_start = models.DateField(help_text="Дата начала действия документа", blank=True, null=True)
    date_end = models.DateField(help_text="Дата окончания действия документа", blank=True, null=True)
    research = models.ManyToManyField(directory.Researches, through='PriceCoast', help_text="Услуга-Прайс", blank=True)
    company = models.ForeignKey('contracts.Company', blank=True, null=True, db_index=True, on_delete=models.SET_NULL)
    hospital = models.ForeignKey('hospitals.Hospitals', blank=True, null=True, default=None, db_index=True, on_delete=models.SET_NULL)
    external_performer = models.BooleanField(default=False, blank=True, help_text='Прайс внешний исполнитель', db_index=True)
    subcontract = models.BooleanField(default=False, blank=True, help_text='Прайс субподряд', db_index=True)
    symbol_code = models.CharField(max_length=55, unique=True, blank=True, null=True, default=None, help_text='Код прайса', db_index=True)

    def __str__(self):
        return "{}".format(self.title)

    def status(self):
        return self.active_status

    @staticmethod
    def get_company_price_by_date(company_id, date_start, date_end):
        return PriceName.objects.filter(company_id=company_id, date_start__lte=date_start, date_end__gte=date_end).first()

    @staticmethod
    def get_hospital_price_by_date(hospital_id, date_start, date_end, is_subcontract=False):
        return PriceName.objects.filter(hospital_id=hospital_id, date_start__lte=date_start, date_end__gte=date_end, subcontract=is_subcontract).first()

    class Meta:
        verbose_name = 'Название прайса'
        verbose_name_plural = 'Названия прайса'

    @staticmethod
    def as_json(price):
        if price.company:
            company_title = price.company.title
            company_id = price.company_id
        elif price.hospital:
            company_title = price.hospital.title
            company_id = price.hospital_id
        else:
            company_title = ""
            company_id = ""
        json_data = {"id": price.id, "title": price.title, "start": price.date_start, "end": price.date_end, "company": company_id, "companyTitle": company_title}
        return json_data

    @staticmethod
    def get_price_by_id_symbol_code(price_code, price_id):
        price = None
        if price_id:
            price = PriceName.objects.filter(pk=price_id).first()
        elif price_code:
            price = PriceName.objects.filter(symbol_code=price_code).first()
        return price


class PriceCoast(models.Model):
    price_name = models.ForeignKey(PriceName, on_delete=models.DO_NOTHING, db_index=True)
    research = models.ForeignKey(directory.Researches, on_delete=models.DO_NOTHING, db_index=True)
    coast = models.DecimalField(max_digits=10, decimal_places=2)
    number_services_by_contract = models.PositiveIntegerField(default=0, help_text="Кол-во услуг по контракту")

    def __str__(self):
        return "{}".format(self.price_name.title)

    @staticmethod
    def get_coast_from_price(dir_research_loc, price_modifier):
        """
        Принимает вид исследования, объект price_modifier: объект прайса, модификатор
        на основании прайса получает базовую цену и умножает на модификатор.
        Возвращает окончательную цену для записи в issledovaniya
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

    @staticmethod
    def get_coast_by_researches(price, researches):
        return {i.research_id: i.coast for i in PriceCoast.objects.filter(price_name=price, research_id__in=researches)}

    class Meta:
        unique_together = ('price_name', 'research')
        verbose_name = 'Цена прайса'
        verbose_name_plural = 'Цены прайса'


class Contract(models.Model):
    title = models.CharField(max_length=511, unique=True, help_text='Наименование организации', db_index=True)
    number = models.CharField(max_length=255, blank=True, help_text='Номер договора', db_index=False)
    date_start = models.DateField(help_text="Дата начала действия документа", blank=True, null=True)
    date_end = models.DateField(help_text="Дата окончания действия документа", blank=True, null=True)
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
    email = models.CharField(max_length=128, blank=True, default='', help_text="email")

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


class MedicalExamination(models.Model):
    card = models.ForeignKey(Card, help_text="Карта пациента", db_index=True, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, help_text="Компания", db_index=True, on_delete=models.CASCADE)
    date = models.DateField(help_text="Дата мед. осмотра", db_index=True)

    def __str__(self):
        return f"{self.card} - {self.company} - {self.date}"

    @staticmethod
    def get_by_date(date: str, company_id: int, month: bool = False) -> list[dict]:
        if not date or not company_id:
            return []
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        if month:
            _, num_day = calendar.monthrange(date.year, date.month)
            date_start = date.replace(day=1)
            date_end = date.replace(day=num_day)
        else:
            date_start = date
            date_end = date
        result = []
        prev_card_id = -1
        examination_data = get_examination_data(company_id, date_start, date_end)
        for data in examination_data:
            if prev_card_id != data.card_id:
                result.append(
                    {
                        "card_id": data.card_id,
                        "fio": data.family + " " + data.name + " " + data.patronymic,
                        "harmful_factors": [f"{data.harmful_factor}; "],
                        "research_id": [data.research_id],
                        "research_titles": [f"{data.research_title}; "],
                        "date": data.examination_date.strftime("%d.%m.%Y"),
                    }
                )
            else:
                if f"{data.harmful_factor}; " not in result[-1]["harmful_factors"]:
                    result[-1]["harmful_factors"].append(f"{data.harmful_factor}; ")
                if data.research_id not in result[-1]["research_id"]:
                    result[-1]["research_id"].append(data.research_id)
                    result[-1]["research_titles"].append(f"{data.research_title}; ")
            prev_card_id = data.card_id
        if month:
            result = sorted(result, key=lambda d: d["date"])
        else:
            result = sorted(result, key=lambda d: d["fio"])

        return result

    @staticmethod
    def save_examination(card: Card, company: Company, date: str):
        current_exam = MedicalExamination.objects.filter(card=card).first()
        if current_exam:
            current_exam.company = company
            current_exam.date = date
            current_exam.save()
        else:
            MedicalExamination(card=card, company=company, date=date).save()

    @staticmethod
    def get_date(card_pk: int):
        result = None
        current_exam = MedicalExamination.objects.filter(card_id=card_pk).first()
        if current_exam:
            result = current_exam.date
        return result

    @staticmethod
    def update_date(card_pk: int, date: str):
        current_exam = MedicalExamination.objects.filter(card_id=card_pk).first()
        if current_exam:
            current_exam.date = date
            current_exam.save()
        elif date != "":
            card = Card.objects.filter(pk=card_pk).first()
            if card.work_place_db:
                MedicalExamination.save_examination(card, card.work_place_db, date)

    class Meta:
        verbose_name = 'Медицинский осмотр'
        verbose_name_plural = 'Медицинские осмотры'
