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
    history = models.ForeignKey(Napravleniya, default=None, related_name='history_number', help_text='Номер истории', db_index=True, on_delete=models.CASCADE)
    diary = models.ForeignKey(Napravleniya, default=None, related_name='diaries_number', help_text='Номер дневника', db_index=True, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, default=None, db_index=True, help_text='Пациент', on_delete=models.CASCADE)
    mnn = models.ForeignKey(Mnn, help_text="МНН препарата", on_delete=models.CASCADE, db_index=True)
    form_release = models.ForeignKey(FormRelease, help_text="Форма выпуска", on_delete=models.CASCADE)
    method = models.ForeignKey(MethodsReception, help_text="Способ применения", on_delete=models.CASCADE)
    dosage = models.FloatField(help_text='Дозировка')
    units = models.CharField(max_length=8, help_text='Единицы измерения')
    date_start = models.DateField(help_text="Дата начала")
    date_end = models.DateField(help_text="Дата окончания включительно")
    doc_create = models.ForeignKey(DoctorProfile, related_name="doc_create_prescription", help_text='Создатель назначения', on_delete=models.CASCADE)
    time_create = models.DateTimeField(auto_now_add=True, help_text='Дата создания')

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
