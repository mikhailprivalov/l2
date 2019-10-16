from django.db import models

# Create your models here.
class holter_date(models.Model):
    """
    Направления на исследования
    """
    key = models.CharField(max_length=255, default="", blank=True, help_text='Приложение/объект', db_index=True)
    holter_protocol = models.DateField(null=True, blank=True, db_index=True, help_text='Последний обработанный протокол')