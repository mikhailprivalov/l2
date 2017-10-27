from django.db import models


class Podrazdeleniya(models.Model):  # Модель подразделений
    title = models.CharField(max_length=255)  # Название подразделения
    gid_n = models.IntegerField(default=None, null=True, blank=True)  # gidNumber в LDAP
    isLab = models.BooleanField(default=False, blank=True)  # True=Это лаборатория
    hide = models.BooleanField(default=False, blank=True)  # True=Скрывать подразделение
    rmis_id = models.CharField(max_length=15, default=None, blank=True, null=True)

    def __str__(self):  # Функция перевода экземпляра класса Podrazdeleniya в строку
        return self.title  # Возврат поля Podrazdeleniya.title

    class Meta:
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'


class Subgroups(models.Model):  # Модель подгрупп подразделений
    title = models.CharField(max_length=255)  # Название подгруппы
    podrazdeleniye = models.ForeignKey(Podrazdeleniya)  # Подразделение группы

    def __str__(self):
        if self.podrazdeleniye.title != self.title:
            return self.podrazdeleniye.title + " - " + self.title
        return self.title

    class Meta:
        verbose_name = 'Подгруппа (DEPRECATED)'
        verbose_name_plural = 'Подгруппы (DEPRECATED)'
