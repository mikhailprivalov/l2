import time

from django.db import models
from django.utils import timezone

from appconf.manager import SettingManager
from clients.models import Card
from laboratory.utils import localtime
from users.models import DoctorProfile


class VisitPurpose(models.Model):
    title = models.CharField(max_length=255)
    hide = models.BooleanField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Цель посещения'
        verbose_name_plural = 'Цели посещений'


class ResultOfTreatment(models.Model):
    title = models.CharField(max_length=255)
    hide = models.BooleanField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Результат обращения'
        verbose_name_plural = 'Результаты обращений'


class Outcomes(models.Model):
    title = models.CharField(max_length=255)
    hide = models.BooleanField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Исход'
        verbose_name_plural = 'Исходы'


class ExcludePurposes(models.Model):
    title = models.CharField(max_length=255)
    hide = models.BooleanField()

    def __str__(self):
        return self.title

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
    first_time = models.BooleanField(help_text="Впервые")
    result = models.ForeignKey(ResultOfTreatment, blank=True, null=True, on_delete=models.SET_NULL,
                               help_text="Результат обращения")
    outcome = models.ForeignKey(Outcomes, blank=True, null=True, on_delete=models.SET_NULL,
                                help_text="Исход", default=None)
    primary_visit = models.BooleanField(help_text="Первичное посещение")
    info = models.TextField(blank=True, help_text="Диагнозы, виды услуг, виды травм")
    dispensary_registration = models.IntegerField(choices=DISPENSARY_REGISTRATIONS, default=DISPENSARY_NO, blank=True,
                                                  help_text="Диспансерный учёт")
    dispensary_diagnos = models.CharField(blank=True, help_text="Диагноз диспансерного учёта", default="",
                                          max_length=255)
    dispensary_exclude_purpose = models.ForeignKey(ExcludePurposes, on_delete=models.SET_NULL,
                                                   help_text="Причина снятия", blank=True, null=True, default=None)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, help_text="Врач")
    creator = models.ForeignKey(DoctorProfile, on_delete=models.SET_NULL, null=True, default=None, help_text="Создатель талона", related_name="creator")
    date = models.DateTimeField(auto_now_add=True, help_text='Дата создания', db_index=True)
    date_ticket = models.CharField(max_length=10, null=True, blank=True, default=None, help_text='Дата талона')
    invalid_ticket = models.BooleanField(default=False, blank=True, help_text='Статталон недействителен')

    @property
    def date_local(self):
        return localtime(self.date)

    def can_invalidate(self):
        rt = SettingManager.get("ticket_invalidate_time_min", default='1440.0', default_type='f') * 60
        ctp = time.mktime(timezone.localtime(self.date).timetuple())
        ctime = int(time.time())
        return ctime - ctp < rt

    def get_date(self):
        if not self.date_ticket:
            self.date_ticket = timezone.localtime(self.date).strftime('%d.%m.%Y')
            self.save()
        return self.date_ticket

    class Meta:
        verbose_name = 'Статталон'
        verbose_name_plural = 'Статталоны'
