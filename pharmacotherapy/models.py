from django.db import models
from clients.models import Card
from directions.models import Napravleniya
from users.models import DoctorProfile


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
    history_num = models.ForeignKey(Napravleniya, default=None, related_name='history_number', help_text='Номер истории', db_index=True, on_delete=models.CASCADE)
    diaries_num = models.ForeignKey(Napravleniya, default=None, related_name='diaries_number', help_text='Номер дневника', db_index=True, on_delete=models.CASCADE)
    client = models.ForeignKey(Card, default=None, db_index=True, help_text='Пациент', on_delete=models.CASCADE)
    mnn = models.ForeignKey(Mnn, help_text="Стационарная услуга", on_delete=models.CASCADE, db_index=True)
    form_release = models.ForeignKey(FormRelease, help_text="форма выпуска", null=True, on_delete=models.SET_NULL, db_index=True)
    method = models.ForeignKey(MethodsReception, help_text="Способ применения", null=True, on_delete=models.SET_NULL, db_index=True)
    dosage = models.IntegerField(default=0, blank=True)
    units = models.CharField(max_length=16, default="", help_text='Единицы измерения')
    date_start = models.DateField(help_text="Дата начала", db_index=True)
    count_day = models.SmallIntegerField(default=1, blank=True)
    date_end = models.DateField(help_text="Дата окончания включительно", db_index=True)
    doc_create = models.ForeignKey(DoctorProfile, related_name="doc_create_prescription", default=None, blank=True, null=True, help_text='Создатель назначения', on_delete=models.SET_NULL)
    time_create = models.DateTimeField(auto_now_add=True, help_text='Дата создания', db_index=True)
    time_cancel = models.DateTimeField(auto_now_add=True, help_text='Дата отмены', db_index=True)

    class Meta:
        verbose_name = 'Назначение'
        verbose_name_plural = 'Назначения'


class ProcedureListTimes(models.Model):
    prescription = models.ForeignKey(ProcedureList, null=True, blank=True, help_text='Назначение из процедурного листа', on_delete=models.SET_NULL)
    times_medication = models.DateTimeField(help_text='Время приема', db_index=True)
    executor = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_executor_prescription", help_text='Исполнитель', on_delete=models.SET_NULL)
    cancel = models.BooleanField(default=False, blank=True, help_text='Отмена времени')

    class Meta:
        verbose_name = 'Время из процедурного листа'
        verbose_name_plural = 'Время из процедурного листа'
