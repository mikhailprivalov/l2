from django.db import models
from clients.models import Card
from directory.models import Researches
from users.models import DoctorProfile


class DoctorCall(models.Model):
    client = models.ForeignKey(Card, db_index=True, help_text='Пациент', on_delete=models.CASCADE)
    research = models.ForeignKey(Researches, null=True, blank=True, help_text='Вид исследования из справочника', db_index=True, on_delete=models.CASCADE)
    create_at = models.DateTimeField(auto_now_add=True, help_text='Дата создания', db_index=True)
    exec_at = models.DateTimeField(auto_now_add=True, help_text='Дата вызова на дом', db_index=True)
    comment = models.TextField()
    cancel = models.BooleanField(default=False, blank=True, help_text='Отмена вызова')
    doc_who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_who_create", help_text='Создатель направления', on_delete=models.SET_NULL)
    doc = models.ForeignKey(DoctorProfile, db_index=True, null=True, help_text='Лечащий врач', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Вызов'
        verbose_name_plural = 'Вызова на дом'
