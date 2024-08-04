import uuid

from django.db import models
from jsonfield import JSONField
from cash_registers import sql_func
from laboratory.utils import current_time
from podrazdeleniya.models import Podrazdeleniya
from users.models import DoctorProfile


class CashRegister(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name='Наименование')
    ip_address = models.CharField(max_length=255, default="", verbose_name='IP адрес', help_text='192.168.10.10')
    port = models.CharField(max_length=5, default="", verbose_name='Порт', help_text='16333')
    login = models.CharField(max_length=255, default="", verbose_name='Логин', help_text='login')
    password = models.CharField(max_length=255, default="", verbose_name='Пароль', help_text='123456')
    hide = models.BooleanField(default=False, blank=True, verbose_name='Скрытие')
    address = models.CharField(max_length=128, blank=True, default='', verbose_name="Адрес")
    address_fias = models.CharField(max_length=128, blank=True, default=None, null=True, verbose_name="ФИАС Адрес")
    address_details = JSONField(blank=True, null=True, verbose_name="Детали адреса")
    department = models.ForeignKey(Podrazdeleniya, null=True, db_index=True, verbose_name="Подразделение", on_delete=models.SET_NULL)
    location = models.CharField(max_length=255, default="", verbose_name="Местоположение", help_text="2 этаж регистратура")

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

    @staticmethod
    def get_meta_data(cash_register_id):
        cash_register: CashRegister = CashRegister.objects.get(pk=cash_register_id)
        cash_register_data = {"address": cash_register.ip_address, "port": cash_register.port, "login": cash_register.login, "password": cash_register.password}
        return cash_register_data


class Shift(models.Model):
    cash_register = models.ForeignKey(CashRegister, verbose_name='Касса', help_text='Касса 1', null=True, on_delete=models.SET_NULL, db_index=True)
    open_at = models.DateTimeField(verbose_name='Время открытия', help_text='2024-07-28 16:00', null=True, blank=True, db_index=True)
    close_at = models.DateTimeField(verbose_name='Время закрытия', help_text='2024-07-28 23:00', null=True, blank=True, db_index=True)
    operator = models.ForeignKey(DoctorProfile, verbose_name='Оператор', help_text='Сидоров м.п', null=True, on_delete=models.SET_NULL, db_index=True)
    open_uuid = models.UUIDField(verbose_name='UUID открытия', help_text='abbfg-45fsd2', null=True, blank=True)
    close_uuid = models.UUIDField(verbose_name='UUID Закрытия', help_text='abbfg-45fsd2', null=True, blank=True)
    open_status = models.BooleanField(verbose_name='Статус открытия смены', default=False)
    close_status = models.BooleanField(verbose_name='Статус открытия смены', default=False)

    class Meta:
        verbose_name = "Кассовая смена"
        verbose_name_plural = "Кассовые смены"

    def __str__(self):
        return f"{self.cash_register.title} - {self.open_at} - {self.close_at} - {self.operator}"

    @staticmethod
    def open_shift(uuid_data: str, cash_register_id: int, operator_id: int):
        new_shift: Shift = Shift(cash_register_id=cash_register_id, operator_id=operator_id, open_uuid=uuid_data)
        new_shift.save()
        return {"cash_register_id": new_shift.cash_register_id, "shift_id": new_shift.pk}

    def confirm_open_shift(self):
        self.open_status = True
        self.open_at = current_time()
        self.save()
        return True

    @staticmethod
    def close_shift(uuid_data: str, cash_register_id: int, operator_id: int):
        shift: Shift = Shift.objects.filter(cash_register_id=cash_register_id, operator_id=operator_id, open_status=True, close_status=False).last()
        shift.close_uuid = uuid_data
        shift.save()
        return True

    def confirm_close_shift(self):
        self.close_status = True
        self.close_at = current_time()
        self.save()
        return True

    @staticmethod
    def get_open_shift_by_operator(operator_id: int):
        shift: Shift = Shift.objects.filter(operator_id=operator_id, open_status=True, close_status=False).last()
        if not shift:
            return {"cash_register_id": None, "shift_id": None}
        return {"cash_register_id": shift.cash_register_id, "shift_id": shift.pk}

    @staticmethod
    def check_shift(cash_register_id: int, doctor_profile_id: int):
        shift_exist = Shift.objects.filter(operator_id=doctor_profile_id, close_status=False).last()
        cash_register_exist = Shift.objects.filter(cash_register_id=cash_register_id, close_status=False).last()
        if shift_exist:
            return {"ok": False, "message": "У вас уже есть открытая смена"}
        elif cash_register_exist:
            return {"ok": False, "message": "На этой кассе уже есть открытая смена"}
        return {"ok": True, "message": ""}

    @staticmethod
    def get_shift_job_data(doctor_profile_id: int, cash_register_id):
        operator: DoctorProfile = DoctorProfile.objects.get(pk=doctor_profile_id)
        operator_data = {"name": operator.get_full_fio(), "vatin": operator.inn}
        cash_register_data = CashRegister.get_meta_data(cash_register_id)
        uuid_data = str(uuid.uuid4())
        return operator_data, cash_register_data, uuid_data
