from django.db import models


class Medicament(models.Model):
    """
    Справочник лекарств (медикаментов)
    """

    number_registration = models.CharField(max_length=511, help_text='Номер регистрационного удостоверения', db_index=True)
    date_start_registration = models.DateField(help_text="Дата регистрации", blank=True, null=True)
    date_end_registration = models.DateField(help_text="Дата окончания регистрации", blank=True, null=True)
    trade_name = models.CharField(max_length=511, unique=True, help_text='Торговое наименование', db_index=True)
    international_name = models.CharField(max_length=511, unique=True, help_text='МНН', db_index=True)
    form_release = models.TextField()
    pharm_group = models.CharField(max_length=511, unique=True, help_text='МНН', db_index=True)
