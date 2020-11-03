from django.db import models


class Hospitals(models.Model):
    title = models.CharField(max_length=255, blank=True, default='', help_text="Наименование")
    short_title = models.CharField(max_length=128, blank=True, default='', help_text="Краткое наименование", db_index=True)
    code = models.CharField(max_length=128, blank=True, default='', help_text="код больницы")
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие больницы', db_index=True)

    class Meta:
        verbose_name = 'Больница'
        verbose_name_plural = 'Больницы'


