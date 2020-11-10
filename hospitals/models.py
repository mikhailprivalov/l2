from django.db import models


class Hospitals(models.Model):
    title = models.CharField(max_length=255, help_text="Наименование")
    short_title = models.CharField(max_length=128, blank=True, default='', help_text="Краткое наименование", db_index=True)
    code_tfoms = models.CharField(max_length=128, blank=True, default='', help_text="Код больницы", db_index=True)
    oid = models.CharField(max_length=128, blank=True, default='', help_text="Код больницы", db_index=True)
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие больницы', db_index=True)

    def __str__(self):
        return f"{self.short_title} – {self.code_tfoms}"

    class Meta:
        verbose_name = 'Больница'
        verbose_name_plural = 'Больницы'
