from django.db import models
import directory.models as directory
from decimal import Decimal


# Create your models here.

class PriceName(models.Model):
    title = models.CharField(max_length=511,unique=True, help_text='Наименование Прайса',db_index=True)
    active_status = models.BooleanField(default=True, help_text='Статус активности',db_index=True)
    date_start = models.DateField(help_text="Дата начала действия докумена", blank=True, null=True)
    date_end = models.DateField(help_text="Дата окончания действия докумена", blank=True, null=True)
    research = models.ManyToManyField(directory.Researches, through='PriceCoast', help_text="Услуга-Прайс", blank=True)

    def __str__(self):
        return "{}".format(self.title)

    def get_price(istochnik_f_local):
        """
        На основании источника финансирования возвращает прайс
        Если источник финансирования ДМС поиск осуществляется по цепочке company-contract. Company(Страховая организация)
        Если источник финансирования МЕДОСМОТР поиск осуществляется по цепочке company-contract. Company(место работы)
        Если источник финансирования ПЛАТНО поиск осуществляется по цепочке contract
        Если источник финансирования ОМС, ДИСПАНСЕРИЗАЦИЯ поиск осуществляется по цепочке contract
        Если источник финансирования Бюджет поиск осуществляется по цепочке contract

        :param **kwargs: istochnik_f, место работы, страховая организация
        :return:
        """

        from directions.models import IstochnikiFinansirovaniya

        try:
            contract_l = IstochnikiFinansirovaniya.objects.values_list('contracts_id').get(pk=istochnik_f_local)
            price_modifier = Contract.objects.values_list('price', 'modifier').get(id=contract_l[0])
        except Exception:
            price_modifier = ""

        return price_modifier


    def status(self):
        return self.active_status

    class Meta:
        verbose_name = 'Прайс - название'
        verbose_name_plural = 'Прайс - название'

class PriceCoast(models.Model):
    price_name = models.ForeignKey(PriceName, on_delete=models.DO_NOTHING,db_index=True)
    research = models.ForeignKey(directory.Researches, on_delete=models.DO_NOTHING,db_index=True)
    coast = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return "{}".format(self.price_name.title)

    def get_coast_from_price(dir_research_loc, price_modifier_loc):
        price_name_loc = price_modifier_loc[0]
        price_modifier_loc = price_modifier_loc[1]
        try:
            d = PriceCoast.objects.values_list('coast').get(price_name=price_name_loc, research_id=dir_research_loc)
            res_coast = d[0]
        except Exception:
            res_coast = 0
        dd = (res_coast * price_modifier_loc).quantize(Decimal("1.00"))
        return dd



    class Meta:
        unique_together =('price_name','research')
        verbose_name = 'Прайс - цены'
        verbose_name_plural = 'Прайс - цены'



class Contract(models.Model):
    title = models.CharField(max_length=511, unique=True, help_text='Наименование организации', db_index=True)
    number = models.CharField(max_length=255,blank=True, help_text='Номер договора', db_index=False)
    date_start = models.DateField(help_text="Дата начала действия докумена", blank=True, null=True)
    date_end = models.DateField(help_text="Дата окончания действия докумена", blank=True, null=True)
    price = models.ForeignKey(PriceName, blank=True, null=True, db_index=True, on_delete=models.CASCADE)
    modifier = models.DecimalField(max_digits=8,decimal_places=3,default=1, help_text="10000,101")
    active_status = models.BooleanField(default=True, help_text='Действующий', db_index=True)
    show_in_card = models.BooleanField(default=False, help_text='Показывать в карте пациента', db_index=True)
    main = models.BooleanField(default=False, help_text='По умолчанию действует. если несколько.'
                                                        'Можно переназначить', db_index=True)

    def __str__(self):
        return "{}".format(self.title)


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
