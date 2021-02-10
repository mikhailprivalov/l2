from django.db import models
from clients.models import Card
from directions.models import Napravleniya
from directory.models import Researches
from users.models import DoctorProfile


class Drugs(models.Model):
    mnn = models.CharField(max_length=255, default="", null=True, blank=True, help_text='МНН препарата')
    trade_name = models.CharField(max_length=255, default="", null=True, blank=True, help_text='Торговое наименование препарата')

    def __str__(self):
        if self.trade_name and self.mnn:
            return f"{self.trade_name} ({self.mnn})"
        if self.mnn:
            return self.mnn
        return self.trade_name

    class Meta:
        verbose_name = 'МНН'
        verbose_name_plural = 'МНН'


class FormRelease(models.Model):
    title = models.CharField(max_length=255, default="", help_text='Форма выпуска')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Форма выпуска'
        verbose_name_plural = 'Формы выпуска'


class MethodsReception(models.Model):
    title = models.CharField(max_length=255, default="", help_text='Способ применения')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Способ приема'
        verbose_name_plural = 'Способы приема'


class ProcedureList(models.Model):
    history = models.ForeignKey(Napravleniya, related_name='history_number', help_text='Номер истории', db_index=True, on_delete=models.CASCADE)
    diary = models.ForeignKey(Napravleniya, related_name='diaries_number', help_text='Номер дневника', db_index=True, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, db_index=True, help_text='Пациент', on_delete=models.CASCADE)
    drug = models.ForeignKey(Drugs, help_text="Препарат", on_delete=models.CASCADE, db_index=True)
    form_release = models.ForeignKey(FormRelease, help_text="Форма выпуска", on_delete=models.CASCADE)
    method = models.ForeignKey(MethodsReception, help_text="Способ применения", on_delete=models.CASCADE)
    dosage = models.FloatField(help_text='Дозировка')
    units = models.CharField(max_length=8, help_text='Единицы измерения')
    date_start = models.DateField(help_text="Дата начала")
    date_end = models.DateField(help_text="Дата окончания включительно")
    doc_create = models.ForeignKey(DoctorProfile, related_name="doc_create_prescription", help_text='Создатель назначения', on_delete=models.CASCADE)
    time_create = models.DateTimeField(auto_now_add=True, help_text='Дата создания')
    cancel = models.BooleanField(default=False, blank=True, help_text='Отмена времени приема')
    who_cancel = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="pl_who_cancel", help_text='Кто отменил', on_delete=models.SET_NULL)
    research = models.ForeignKey(Researches, null=True, blank=True, help_text='Вид исследования из справочника', db_index=True, on_delete=models.CASCADE)
    comment = models.CharField(max_length=70, help_text='Комментарий', default='', blank=True)

    class Meta:
        verbose_name = 'Назначение'
        verbose_name_plural = 'Назначения'


class ProcedureListTimes(models.Model):
    prescription = models.ForeignKey(ProcedureList, help_text='Назначение из процедурного листа', on_delete=models.CASCADE)
    times_medication = models.DateTimeField(help_text='Время приема', db_index=True)
    executor = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_executor_prescription", help_text='Исполнитель', on_delete=models.SET_NULL)
    cancel = models.BooleanField(default=False, blank=True, help_text='Отмена времени приема')
    who_cancel = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="who_cancel", help_text='Кто отменил', on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Время из процедурного листа'
        verbose_name_plural = 'Время из процедурного листа'
