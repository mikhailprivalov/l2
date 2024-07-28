from django.db import models

from users.models import DoctorProfile


class CashRegister(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name='Наименование')
    ip_address = models.CharField(max_length=255, default="", verbose_name='IP адрес', help_text='192.168.10.10')
    port = models.CharField(max_length=5, default="", verbose_name='Порт', help_text='16333')
    login = models.CharField(max_length=255, default="", help_text='Логин')
    password = models.CharField(max_length=255, default="", help_text='Пароль')
    hide = models.BooleanField(default=False, blank=True, verbose_name='Скрытие')

    class Meta:
        verbose_name = "Касса"
        verbose_name_plural = "Кассы"

    def __str__(self):
        return f"{self.title}"

    def json(self):
        return {
            "id": self.id,
            "label": self.title,
        }


class Shift(models.Model):
    cash_register = models.ForeignKey(CashRegister, db_index=True, on_delete=models.CASCADE)
    open_at = models.DateTimeField(verbose_name='Время открытия', help_text='2024-07-28 16:00', db_index=True)
    close_at = models.DateTimeField(verbose_name='Время закрытия', help_text='2024-07-28 23:00', db_index=True)
    operator = models.ForeignKey(DoctorProfile, db_index=True, verbose_name='Оператор', help_text='Сидоров м.п', null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Кассовая смена"
        verbose_name_plural = "Кассовые смены"

    def __str__(self):
        return f"{self.cash_register.title} - {self.open_at} - {self.close_at} - {self.operator}"
