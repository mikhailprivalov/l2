from django.db import models
from datetime import date


class Mnn(models.Model):
    title = models.CharField(max_length=255, default="", help_text='МНН')

    class Meta:
        verbose_name = 'МНН'
        verbose_name_plural = 'МНН'


class FormRelease(models.Model):
    title = models.CharField(max_length=255, default="", help_text='Форма выпуска')

    class Meta:
        verbose_name = 'Форма выпуска'
        verbose_name_plural = 'Формы выпуска'


class MethodsReception(models.Model):
    title = models.CharField(max_length=255, default="", help_text='Способ применения')

    class Meta:
        verbose_name = 'Способ приема'
        verbose_name_plural = 'Способы приема'


class ProcedureList(models.Model):
    mnn = models.ForeignKey(Mnn, help_text="Стационарная услуга", on_delete=models.CASCADE, db_index=True)
    form_release = models.ForeignKey(FormRelease, help_text="форма выпуска", null=True, on_delete=models.SET_NULL, db_index=True)
    method = models.ForeignKey(MethodsReception, help_text="Способ применения", null=True, on_delete=models.SET_NULL, db_index=True)
    dosage = models.IntegerField(default=0, blank=True)
    units = models.CharField(max_length=16, default="", help_text='Единицы измерения')
    times_receipt = models.CharField(max_length=255, default="", help_text='Время приема')
    date_start = models.DateField(default=date.today, help_text="Дата начала", blank=False, null=False, db_index=True)
    count_day = models.SmallIntegerField(default=1, blank=True)
    date_end = models.DateField(default=date.today, help_text="Дата окончания включительно", blank=False, null=False, db_index=True)

    class Meta:
        verbose_name = 'Назначение'
        verbose_name_plural = 'Назначения'
