from podrazdeleniya.models import Podrazdeleniya, Subgroups
from django.db import models
import jsonfield
import sys

TESTING = 'test' in sys.argv[1:] or 'jenkins' in sys.argv[1:]

class Tubes(models.Model):
    """Таблица типов пробирок"""
    id = models.AutoField(primary_key=True)
    color = models.CharField(max_length=7)  # Цвет в CSS формате (#1122FF)
    title = models.CharField(max_length=255)  # Название

    def __str__(self):
        return self.title + " пробирка"


class Researches(models.Model):
    """Таблица справочника исследований"""
    id_research = models.AutoField(primary_key=True)  # Идентификатор
    # id_lab_fk = models.ForeignKey(Podrazdeleniya, blank=True, null=True, db_column='id_lab_fk')  # Лаборатория
    subgroup_lab = models.ForeignKey(Subgroups, blank=True, null=True, db_column='id_subgroup_lab_fk')
    tubetype = models.ForeignKey(Tubes, blank=True, null=True, db_column='id_tube_fk')  # Пробирка
    tubegroup = models.IntegerField(default=0,
                                    db_column='tube_group')  # Группировка по пробирке.
    # Исследования из одной группы собираются в одну пробирку
    ref_title = models.CharField(max_length=255, blank=True, null=True)  # Название исследования
    ref_fractions = jsonfield.JSONField(blank=True, null=True)  # Фракции
    ref_m = jsonfield.JSONField(blank=True, null=True)  # Референсы М
    ref_f = jsonfield.JSONField(blank=True, null=True)  # Референсы Ж
    ref_units = jsonfield.JSONField(blank=True, null=True)  # Еденицы измерений
    group = models.IntegerField(blank=True, null=True)  # Группировка по направлениям. Исследования из одной группы
    # записываются в одно направление
    short_title = models.CharField(max_length=255, blank=True, null=True)

    tube_weight_group = models.IntegerField(default=0, db_column='tube_weight_group')
    tube_weight = models.IntegerField(default=0, null=True, db_column='tube_weight')

    hide = models.IntegerField(default=0, db_column="hide")
    auto_add = models.IntegerField(default=0, db_column="auto_add")

    class Meta:
        managed = TESTING
        db_table = 'researches'  # Название таблицы

    def __str__(self):
        return self.getlab() + " " + self.ref_title

    def s_title(self):
        if self.short_title:
            return self.short_title
        else:
            return self.ref_title

    def getlab(self):
        return str(self.subgroup_lab)
