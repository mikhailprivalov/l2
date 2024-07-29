from django.db import models

from cash_registers import sql_func
from laboratory.utils import current_time
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

    @staticmethod
    def get_cash_registers():
        result = [{"id": cash_register.id, "label": cash_register.title} for cash_register in sql_func.get_cash_registers()]
        return result


class Shift(models.Model):
    cash_register = models.ForeignKey(CashRegister, db_index=True, on_delete=models.CASCADE)
    open_at = models.DateTimeField(verbose_name='Время открытия', help_text='2024-07-28 16:00', db_index=True)
    close_at = models.DateTimeField(verbose_name='Время закрытия', help_text='2024-07-28 23:00', null=True, blank=True, db_index=True)
    operator = models.ForeignKey(DoctorProfile, db_index=True, verbose_name='Оператор', help_text='Сидоров м.п', null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Кассовая смена"
        verbose_name_plural = "Кассовые смены"

    def __str__(self):
        return f"{self.cash_register.title} - {self.open_at} - {self.close_at} - {self.operator}"

    @staticmethod
    def open_shift(cash_register_id: int, operator_id: int):
        new_shift = Shift(cash_register_id=cash_register_id, open_at=current_time(), operator_id=operator_id)
        new_shift.save()
        return {"cash_register_id": new_shift.cash_register_id, "shift_id": new_shift.pk}

    @staticmethod
    def close_shift(operator_id: int):
        shift = Shift.objects.filter(operator_id=operator_id, close_at__isnull=True).last()
        shift.close_at = current_time()
        shift.save()
        return True

    @staticmethod
    def get_shift_data(operator_id: int):
        shift = Shift.objects.filter(operator_id=operator_id, close_at__isnull=True).last()
        if not shift:
            return {"cash_register_id": None, "shift_id": None}
        return {"cash_register_id": shift.cash_register_id, "shift_id": shift.pk}

    @staticmethod
    def check_shift(cash_register_id: int, doctor_profile_id: int):
        shift_exist = Shift.objects.filter(operator_id=doctor_profile_id, close_at__isnull=True).last()
        cash_register_exist = Shift.objects.filter(cash_register_id=cash_register_id, close_at__isnull=True).last()
        if shift_exist:
            return {"ok": False, "message": "У вас уже есть открытая смена"}
        if cash_register_exist:
            return {"ok": False, "message": "На этой кассе уже есть открытая смена"}

