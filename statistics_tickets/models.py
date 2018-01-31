from django.db import models

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
    purpose = models.ForeignKey(VisitPurpose, blank=True, null=True, on_delete=models.SET_NULL, help_text="Цель посещения")
    result = models.ForeignKey(ResultOfTreatment, blank=True, null=True, on_delete=models.SET_NULL, help_text="Результат обращения")
    info = models.TextField(blank=True, help_text="Диагнозы, виды услуг, виды травм")
    first_time = models.BooleanField(help_text="Впервые")
    primary_visit = models.BooleanField(help_text="Первичное посещение")
    dispensary_registration = models.IntegerField(choices=DISPENSARY_REGISTRATIONS, default=DISPENSARY_NO, blank=True, help_text="Диспансерный учёт")
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, help_text="Врач")

