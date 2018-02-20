from django.db import models


class Podrazdeleniya(models.Model):  # Модель подразделений
    HIDDEN = 0
    DEPARTMENT = 1
    LABORATORY = 2
    PARACLINIC = 3
    TYPES = (
        (HIDDEN, "Скрыто"),
        (DEPARTMENT, "Направляющее отделение"),
        (LABORATORY, "Лаборатория"),
        (PARACLINIC, "Параклиника"),
    )

    title = models.CharField(max_length=255)  # Название подразделения
    short_title = models.CharField(max_length=50, default='', blank=True)
    gid_n = models.IntegerField(default=None, null=True, blank=True)  # gidNumber в LDAP
    hide = models.BooleanField(default=False, blank=True, db_index=True)  # DEPRECATED. True=Скрывать подразделение
    p_type = models.PositiveSmallIntegerField(choices=TYPES, default=HIDDEN, blank=True)
    rmis_id = models.CharField(max_length=15, default=None, blank=True, null=True)
    rmis_direction_type = models.CharField(max_length=255, default="Направление в лабораторию", blank=True)

    def get_title(self):
        return self.short_title if self.short_title != '' else self.title

    def __str__(self):  # Функция перевода экземпляра класса Podrazdeleniya в строку
        return self.title  # Возврат поля Podrazdeleniya.title

    class Meta:
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'

