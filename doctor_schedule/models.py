from django.db import models

from clients.models import Card
from directory.models import Researches
from users.models import DoctorProfile, Speciality
from utils.models import ChoiceArrayField


class ScheduleResource(models.Model):
    executor = models.ForeignKey(DoctorProfile, db_index=True, null=True, help_text='Исполнитель', on_delete=models.CASCADE)
    service = models.ForeignKey(Researches, help_text='Услуга', db_index=True, on_delete=models.CASCADE)
    room = models.ForeignKey('podrazdeleniya.Room', related_name='scheduleresourceroom', help_text='Кабинет', db_index=True, on_delete=models.CASCADE)
    departmnent = models.ForeignKey('podrazdeleniya.Podrazdeleniya', null=True, blank=True, help_text='Подразделение',
                                    db_index=True, related_name='scheduleresourcedepartmnent', on_delete=models.CASCADE)
    speciality = models.ForeignKey(Speciality, null=True, blank=True, help_text='Специальность', db_index=True, on_delete=models.CASCADE)


class SlotPlan(models.Model):
    GOSUSLUGI = 'gosuslugi'
    PORTAL = 'portal'
    LOCAL = 'local'

    AVAILABLE_RECORDS = (
        (GOSUSLUGI, 'ЕПГУ'),
        (PORTAL, 'Портал пациента'),
        (LOCAL, 'Текущая система L2'),
    )

    resource = models.ForeignKey(ScheduleResource, db_index=True, help_text='Ресурс', on_delete=models.CASCADE)
    datetime = models.DateTimeField(db_index=True, help_text='Дата/время слота')
    duration_minutes = models.PositiveSmallIntegerField(help_text='Длительность в мин')
    available_systems = ChoiceArrayField(models.CharField(max_length=16, choices=AVAILABLE_RECORDS), help_text='Источник записи')
    disabled = models.BooleanField(default=False, blank=True, help_text='Не доступно для записи', db_index=True)
    is_cito = models.BooleanField(default=False, blank=True, help_text='ЦИТО', db_index=True)


class SlotFact(models.Model):
    RESERVED = 0
    CANCELED = 1
    SUCCESS = 2

    STATUS = (
        (CANCELED, "Отмена"),
        (RESERVED, "Зарезервировано"),
        (SUCCESS, "Выполнено"),
    )
    plan = models.ForeignKey(SlotPlan, db_index=True, help_text='Слот-план', on_delete=models.CASCADE)
    patient = models.ForeignKey(Card, help_text='Карта пациента', db_index=True, null=True, on_delete=models.SET_NULL)
    status = models.PositiveSmallIntegerField(choices=STATUS, blank=True, db_index=True)
    external_slot_id = models.CharField(max_length=255, default='', blank=True)
