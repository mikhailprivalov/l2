from django.db import models
from clients.models import Card
from directory.models import Researches


class ListWait(models.Model):
    client = models.ForeignKey(Card, db_index=True, help_text='Пациент', on_delete=models.CASCADE)
    research = models.ForeignKey(Researches, null=True, blank=True, help_text='Вид исследования из справочника', db_index=True, on_delete=models.CASCADE)
    create_at = models.DateTimeField(auto_now_add=True, help_text='Дата создания', db_index=True)
    exec_at = models.DateTimeField(auto_now_add=True, help_text='Дата создания', db_index=True)
    comment = models.TextField()
    cancel = models.BooleanField(default=False, blank=True, help_text='Отмена ожидания')


    class Meta:
        verbose_name = 'Лист ожидания'
        verbose_name_plural = 'Лист ожидания'
