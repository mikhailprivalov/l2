import time

from django.db import models

from appconf.manager import SettingManager
from clients.models import Card
from users.models import DoctorProfile


class VisitPurpose(models.Model):
    title = models.CharField(max_length=255)
    hide = models.BooleanField()

    class Meta:
        verbose_name = 'Цель посещения'
        verbose_name_plural = 'Цели посещений'


class ResultOfTreatment(models.Model):
    title = models.CharField(max_length=255)
    hide = models.BooleanField()

    class Meta:
        verbose_name = 'Результат обращения'
        verbose_name_plural = 'Результаты обращений'


class Outcomes(models.Model):
    title = models.CharField(max_length=255)
    hide = models.BooleanField()

    class Meta:
        verbose_name = 'Исход'
        verbose_name_plural = 'Исходы'


class Causes(models.Model):
    title = models.CharField(max_length=255)
    hide = models.BooleanField()

    class Meta:
        verbose_name = 'Причина обращения'
        verbose_name_plural = 'Причины обращений'


class ExcludePurposes(models.Model):
    title = models.CharField(max_length=255)
    hide = models.BooleanField()

    class Meta:
        verbose_name = 'Причина снятия с учёта'
        verbose_name_plural = 'Причины снятия с учёта'


class StatisticsTicket(models.Model):
    DISPENSARY_NO = 0
    DISPENSARY_IN = 1
    DISPENSARY_TAKE = 2
    DISPENSARY_OUT = 3

    DISPENSARY_REGISTRATIONS = (
        (DISPENSARY_NO, "Не состоит"),
        (DISPENSARY_IN, "Состоит"),
        (DISPENSARY_TAKE, "Взят"),
        (DISPENSARY_OUT, "Снят"),
    )

    card = models.ForeignKey(Card, on_delete=models.CASCADE, help_text="Карта")
    purpose = models.ForeignKey(VisitPurpose, blank=True, null=True, on_delete=models.SET_NULL,
                                help_text="Цель посещения")
    cause = models.ForeignKey(Causes, blank=True, null=True, on_delete=models.SET_NULL,
                              help_text="Цель посещения")
    result = models.ForeignKey(ResultOfTreatment, blank=True, null=True, on_delete=models.SET_NULL,
                               help_text="Результат обращения")
    info = models.TextField(blank=True, help_text="Диагнозы, виды услуг, виды травм")
    first_time = models.BooleanField(help_text="Впервые")
    primary_visit = models.BooleanField(help_text="Первичное посещение")
    dispensary_registration = models.IntegerField(choices=DISPENSARY_REGISTRATIONS, default=DISPENSARY_NO, blank=True,
                                                  help_text="Диспансерный учёт")
    dispensary_diagnos = models.CharField(blank=True, help_text="Диагноз диспансерного учёта", default="",
                                          max_length=255)
    dispensary_exclude_purpose = models.ForeignKey(ExcludePurposes, on_delete=models.SET_NULL,
                                                   help_text="Причина снятия", blank=True, null=True, default=None)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, help_text="Врач")
    date = models.DateTimeField(auto_now_add=True, help_text='Дата создания', db_index=True)
    invalid_ticket = models.BooleanField(default=False, blank=True, help_text='Статталон недействителен')
    outcome = models.ForeignKey(Outcomes, blank=True, null=True, on_delete=models.SET_NULL,
                                help_text="Исход", default=None)

    def can_invalidate(self):
        rt = SettingManager.get("ticket_invalidate_time_min", default='1440.0', default_type='f') * 60
        ctp = time.mktime(self.date.timetuple()) + 8 * 60 * 60
        ctime = int(time.time())
        return ctime - ctp < rt

    class Meta:
        verbose_name = 'Статталон'
        verbose_name_plural = 'Статталоны'
