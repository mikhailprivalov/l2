from django.db import models
from directory.models import Researches

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
    TYPES =  (
        ('mbu', 'MBU'),
        ('amd', 'AMD'),
    )

    type_integration = models.CharField(max_length=3, choices=TYPES, db_index=True)
    research = models.ForeignKey(Researches, on_delete=models.CASCADE)


class TempData(models.Model):
    """
    Направления на исследования
    """
    key = models.CharField(max_length=255, default="", blank=True, help_text='Приложение/объект', db_index=True)
    holter_protocol_date = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Последний обработанный протокол')
