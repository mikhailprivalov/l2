from directions.models import Napravleniya
import uuid

from django.db import models

from directory.models import Researches
from utils.models import ChoiceArrayField


class IntegrationNamespace(models.Model):
    key = models.CharField(max_length=128, primary_key=True)
    active = models.BooleanField()


class IntegrationJournal(models.Model):
    TYPE_DIRECTION = 0
    TYPE_RESULT = 1
    TYPES = ((TYPE_DIRECTION, 'DIRECTION'), (TYPE_RESULT, 'RESULT'))

    STATUS_NONE = 0
    STATUS_PENDING = 1
    STATUS_UPLOADED = 2
    STATUSES = ((STATUS_NONE, 'NONE'), (STATUS_PENDING, 'PENDING'), (STATUS_UPLOADED, 'UPLOADED'))

    namespace = models.ForeignKey(IntegrationNamespace, db_index=True, on_delete=models.CASCADE)
    type = models.SmallIntegerField(choices=TYPES, db_index=True)
    key = models.IntegerField(db_index=True)


class IntegrationResearches(models.Model):
    TYPES = (
        ('mbu', 'MBU'),
        ('amd', 'AMD'),
        ('crie', 'CRIE'),
    )

    type_integration = models.CharField(max_length=4, choices=TYPES, db_index=True)
    research = models.ForeignKey(Researches, on_delete=models.CASCADE)


class TempData(models.Model):
    key = models.CharField(max_length=50, default="", blank=True, help_text='Приложение/объект', db_index=True)
    holter_protocol_date = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Последний обработанный протокол')


class ExternalService(models.Model):
    ACCESS_RIGHT_QR_CHECK_RESULT = 'qr_check_result'

    ACCESS_RIGHTS = (
        (ACCESS_RIGHT_QR_CHECK_RESULT, 'QR check result'),
    )

    title = models.CharField(max_length=127, help_text="Название")
    token = models.UUIDField(default=uuid.uuid4, editable=False, help_text="Токен, генерируется автоматически", db_index=True)
    rights = ChoiceArrayField(
        models.CharField(max_length=16, choices=ACCESS_RIGHTS),
        help_text='Права доступа'
    )
    is_active = models.BooleanField(default=True, help_text="Сервис активен")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Внешний сервис'
        verbose_name_plural = 'Внешние сервисы'


class CrieOrder(models.Model):
    local_direction = models.ForeignKey(Napravleniya, db_index=True, on_delete=models.CASCADE)
    system_id = models.IntegerField(db_index=True, null=True, blank=True)
    status = models.CharField(max_length=12, blank=True, default='null', db_index=True)
    error = models.TextField(blank=True, default='')
