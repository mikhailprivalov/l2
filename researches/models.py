import sys

from django.db import models

TESTING = 'test' in sys.argv[1:] or 'jenkins' in sys.argv[1:]


class Tubes(models.Model):
    """Таблица типов пробирок"""
    id = models.AutoField(primary_key=True, db_index=True)
    color = models.CharField(max_length=7)  # Цвет в CSS формате (#1122FF)
    title = models.CharField(max_length=255)  # Название

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Вид пробирки'
        verbose_name_plural = 'Виды пробирок'
