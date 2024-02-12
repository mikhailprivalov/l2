from django.db import models

from clients.models import Card
from directory.models import Researches
from podrazdeleniya.models import Podrazdeleniya
from users.models import DoctorProfile, Speciality
from utils.models import ChoiceArrayField
from directions.models import Napravleniya


class ScheduleResource(models.Model):
    title = models.CharField(max_length=255, default="", help_text='Название ресурса', db_index=True)
    executor = models.ForeignKey(DoctorProfile, db_index=True, null=True, verbose_name='Исполнитель', on_delete=models.SET_NULL)
    service = models.ManyToManyField(Researches, verbose_name='Услуга', db_index=True)
    room = models.ForeignKey(
        'podrazdeleniya.Room', related_name='scheduleresourceroom', verbose_name='Кабинет', db_index=True, blank=True, null=True, default=None, on_delete=models.SET_NULL
    )
    department = models.ForeignKey(
        'podrazdeleniya.Podrazdeleniya', null=True, blank=True, verbose_name='Подразделение', db_index=True, related_name='scheduleresourcedepartment', on_delete=models.CASCADE
    )
    speciality = models.ForeignKey(Speciality, null=True, blank=True, verbose_name='Специальность', db_index=True, on_delete=models.CASCADE)
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие ресурса', db_index=True)

    def __str__(self):
        parts = [
            f"{self.pk} — {self.executor} — {', '.join([x.get_title() for x in self.service.all()[:5]])} {self.room or ''}".strip(),
            str(self.department),
            str(self.speciality),
            f'"{self.title}"' if self.title else '',
        ]
        return ", ".join([x for x in parts if x])

    class Meta:
        unique_together = (
            'id',
            'executor',
        )
        verbose_name = 'Ресурс'
        verbose_name_plural = 'Ресурсы'
        ordering = ['-id']


class SlotPlan(models.Model):
    GOSUSLUGI = 'gosuslugi'
    PORTAL = 'portal'
    LOCAL = 'local'

    AVAILABLE_RECORDS = (
        (GOSUSLUGI, 'ЕПГУ'),
        (PORTAL, 'Портал пациента'),
        (LOCAL, 'Текущая система L2'),
    )

    resource = models.ForeignKey(ScheduleResource, db_index=True, verbose_name='Ресурс', on_delete=models.CASCADE)
    datetime = models.DateTimeField(db_index=True, verbose_name='Дата/время слота')
    datetime_end = models.DateTimeField(db_index=True, verbose_name='Дата/время окончания слота')
    duration_minutes = models.PositiveSmallIntegerField(verbose_name='Длительность в мин')
    available_systems = ChoiceArrayField(models.CharField(max_length=16, choices=AVAILABLE_RECORDS), verbose_name='Источник записи')
    disabled = models.BooleanField(default=False, blank=True, verbose_name='Не доступно для записи', db_index=True)
    is_cito = models.BooleanField(default=False, blank=True, verbose_name='ЦИТО', db_index=True)

    def __str__(self):
        return f"{self.pk} — {self.datetime} {self.duration_minutes} мин, {self.resource}"

    class Meta:
        unique_together = (
            'id',
            'resource',
        )
        verbose_name = 'Слот'
        verbose_name_plural = 'Слоты'
        ordering = ['-id']


class SlotFact(models.Model):
    RESERVED = 0
    CANCELED = 1
    SUCCESS = 2

    STATUS = (
        (CANCELED, "Отмена"),
        (RESERVED, "Зарезервировано"),
        (SUCCESS, "Выполнено"),
    )
    plan = models.ForeignKey(SlotPlan, db_index=True, verbose_name='Слот-план', on_delete=models.CASCADE)
    patient = models.ForeignKey(Card, verbose_name='Карта пациента', db_index=True, null=True, on_delete=models.SET_NULL)
    status = models.PositiveSmallIntegerField(choices=STATUS, blank=True, db_index=True, verbose_name='Статус')
    external_slot_id = models.CharField(max_length=255, default='', blank=True, verbose_name='Внешний ИД')
    service = models.ForeignKey(Researches, verbose_name='Услуга', db_index=True, null=True, blank=True, on_delete=models.CASCADE)
    direction = models.ForeignKey(Napravleniya, verbose_name='Направление', db_index=True, null=True, blank=True, default=None, on_delete=models.CASCADE)
    is_cito = models.BooleanField(default=False, blank=True, verbose_name='ЦИТО', db_index=True)
    fin_source = models.ForeignKey(
        'directions.IstochnikiFinansirovaniya', verbose_name='Источник финансирования', db_index=True, null=True, blank=True, default=None, on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.pk} — {self.patient} {self.get_status_display()} {self.plan}"

    class Meta:
        unique_together = (
            'id',
            'plan',
        )
        verbose_name = 'Запись на слот'
        verbose_name_plural = 'Записи на слоты'
        ordering = ['-id']


class UserResourceModifyRights(models.Model):
    resources = models.ManyToManyField(ScheduleResource, verbose_name='Ресурсы', db_index=True)
    departments = models.ManyToManyField(Podrazdeleniya, blank=True, default=None, verbose_name='Подразделения', db_index=True)
    services = models.ManyToManyField(Researches, blank=True, default=None, verbose_name='Услуга', db_index=True)

    user = models.OneToOneField(DoctorProfile, unique=True, null=True, verbose_name='Исполнитель', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Права доступа к управлению расписанием'
        verbose_name_plural = 'Права доступа к управлению расписанием'


class ReasonCancelSlot(models.Model):
    title = models.CharField(max_length=255, default="", help_text='Причина отмены', db_index=True)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = 'Причина отмены записи'
        verbose_name_plural = 'Причины отмены записи'


class SlotFactCancel(models.Model):
    plan = models.ForeignKey(SlotPlan, db_index=True, verbose_name='Слот-план', on_delete=models.CASCADE)
    patient = models.ForeignKey(Card, verbose_name='Карта пациента', db_index=True, null=True, on_delete=models.SET_NULL)
    external_slot_id = models.CharField(max_length=255, default='', blank=True, verbose_name='Внешний ИД')
    service = models.ForeignKey(Researches, verbose_name='Услуга', db_index=True, null=True, blank=True, on_delete=models.CASCADE)
    user = models.ForeignKey(DoctorProfile, verbose_name='Отмена записи', default=None, blank=True, null=True, on_delete=models.SET_NULL)
    reason_cancel_slot = models.ForeignKey(ReasonCancelSlot, verbose_name='причина записи', default=None, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.pk} — {self.patient} {self.plan}"

    class Meta:
        verbose_name = 'Отмена записи на слот'
        verbose_name_plural = 'Отмена записей на слоты'

    @staticmethod
    def cancel_slot(plan_id, card_id, service_id, user):
        s = SlotFactCancel(plan_id=plan_id, patient_id=card_id, service_id=service_id, user=user)
        s.save()
        if s:
            slot_fact = SlotFact.objects.filter(plan_id=plan_id).first()
            slot_fact.delete()
        return True
