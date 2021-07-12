from django.db import models

from clients.models import Card
from directory.models import Researches
from podrazdeleniya.models import Rooms, Podrazdeleniya
from users.models import DoctorProfile, Speciality
from utils.models import ChoiceArrayField


class DoctorScheduleResource(models.Model):
    doctor = models.ForeignKey(DoctorProfile, db_index=True, null=True, help_text='Лечащий врач', on_delete=models.CASCADE)
    research = models.ForeignKey(Researches, null=True, blank=True, help_text='Вид исследования из справочника', db_index=True, on_delete=models.CASCADE)
    room = models.ForeignKey(Rooms, default=None, null=True, blank=True, help_text='Кабинет', db_index=True, on_delete=models.CASCADE)
    departmnent = models.ForeignKey(Podrazdeleniya, null=True, blank=True, help_text='Подразделение', db_index=True, on_delete=models.CASCADE)
    speciality = models.ForeignKey(Speciality, null=True, blank=True, help_text='Специальность', db_index=True, on_delete=models.CASCADE)


class ResourceSlotsPlan(models.Model):
    GOSUSLUGI = 'gosuslugi'
    PORTAL = 'portal'

    AVAILABLE_RECORDS = (
        (GOSUSLUGI, 'Gosuslugi'),
        (PORTAL, 'Portal'),
    )

    doctor_resource = models.ForeignKey(DoctorScheduleResource, db_index=True, null=True, help_text='Лечащий врач', on_delete=models.CASCADE)
    slot_datetime = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Дата/время слота')
    long_time = models.PositiveSmallIntegerField(default=0, help_text='Длительность в мин')
    source_available_records = ChoiceArrayField(models.CharField(max_length=16, choices=AVAILABLE_RECORDS), help_text='Доступна для записи')
    disabled = models.BooleanField(default=False, blank=True, help_text='Не доступно для записи', db_index=True)
    is_cito = models.BooleanField(default=False, blank=True, help_text='ЦИТО', db_index=True)


class ResourceSlotsFact(models.Model):
    RESERVED = 0
    CANCELED = 1

    STATUS = (
        (CANCELED, "Отмена"),
        (RESERVED, "Зарезервировано"),
    )
    resource_plan = models.ForeignKey(ResourceSlotsPlan, db_index=True, null=True, help_text='Лечащий врач', on_delete=models.CASCADE)
    patient = models.ForeignKey(Card, null=True, help_text='Карта пациента', db_index=True, on_delete=models.SET_NULL)
    status = models.PositiveSmallIntegerField(choices=STATUS,  blank=True)
