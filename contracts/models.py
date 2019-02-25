from django.db import models
import directory.models as directory
from django.core.validators import MaxValueValidator, MinValueValidator, MaxLengthValidator, MinLengthValidator

# Create your models here.

class PriceName(models.Model):
    title = models.CharField(max_length=511,unique=True, help_text='Наименование Прайса',db_index=True)
    active_status = models.BooleanField(default=True, help_text='Статус активности',db_index=True)
    date_start = models.DateField(help_text="Дата начала действия докумена", blank=True, null=True)
    date_end = models.DateField(help_text="Дата окончания действия докумена", blank=True, null=True)
    research = models.ManyToManyField(directory.Researches, through='PriceCoast', help_text="Услуга-Прайс", blank=True)

    def __str__(self):
        return "{}".format(self.title)


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

    class Meta:
        unique_together =('price_name','research','coast')
        verbose_name = 'Прайс - цены'
        verbose_name_plural = 'Прайс - цены'

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


    def __str__(self):
        return "{}".format(self.title)

class Contract(models.Model):
    title = models.CharField(max_length=511, unique=True, help_text='Наименование организации', db_index=True)
    company = models.ForeignKey(Company, db_index=True, on_delete=models.CASCADE)
    number = models.CharField(max_length=255,blank=True, help_text='Номер договора', db_index=False)
    date_start = models.DateField(help_text="Дата начала действия докумена", blank=True, null=True)
    date_end = models.DateField(help_text="Дата окончания действия докумена", blank=True, null=True)
    price = models.ForeignKey(PriceName, db_index=True, on_delete=models.CASCADE)
    active_status = models.BooleanField(default=True, help_text='Действующий', db_index=True)
    show_in_research = models.BooleanField(default=False,help_text='Показывать для переопределения цен в услугах при назначении',
                                         db_index=True)
    show_in_card = models.BooleanField(default=False, help_text='Показывать в карте пациента', db_index=True)

    def __str__(self):
        return "{}".format(self.title)



