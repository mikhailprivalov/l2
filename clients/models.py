from __future__ import unicode_literals

from django.db import models


class Importedclients(models.Model):
    """Пациенты из DBF"""
    num = models.IntegerField(unique=True, primary_key=False, blank=True, null=True)  # Номер карты
    family = models.CharField(max_length=255, blank=True, null=True)  # Фамилия
    name = models.CharField(max_length=255, blank=True, null=True)  # Имя
    twoname = models.CharField(max_length=255, blank=True, null=True)  # Отчество
    birthday = models.CharField(max_length=255, blank=True, null=True)  # Дата рождения
    client_id = models.AutoField(unique=True, primary_key=True)  # Идентификатор клиента
    type = models.CharField(max_length=64, blank=True, null=True)  # Тип (Поликлиника или стационар)
    sex = models.CharField(max_length=16, blank=True, null=True)  # Пол
    initials = models.CharField(max_length=16, blank=True, null=True)  # Инициалы

    class Meta:
        managed = False
        db_table = 'ImportedClients'
