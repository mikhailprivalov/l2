from typing import Optional
from django.db import models
from appconf.manager import SettingManager
from clients.models import Card
from directory.models import Researches


class Hospitals(models.Model):
    title = models.CharField(max_length=255, help_text="Наименование")
    short_title = models.CharField(max_length=128, blank=True, default='', help_text="Краткое наименование", db_index=True)
    code_tfoms = models.CharField(max_length=128, blank=True, default='', help_text="Код больницы", db_index=True)
    oid = models.CharField(max_length=128, blank=True, default='', help_text="Код больницы", db_index=True)
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие больницы', db_index=True)
    is_default = models.BooleanField(default=False, blank=True, help_text='Больница по умолчанию для пустых полей', db_index=True)
    address = models.CharField(max_length=128, blank=True, default='', help_text="Адрес больницы")
    phones = models.CharField(max_length=128, blank=True, default='', help_text="Телефон больницы")
    ogrn = models.CharField(max_length=16, blank=True, default='', help_text="ОГРН больницы")
    www = models.CharField(max_length=128, blank=True, default='', help_text="Сайт больницы")
    rmis_org_id = models.CharField(max_length=12, blank=True, default='', help_text="ID организации в РМИС")
    email = models.CharField(max_length=12, blank=True, default='', help_text="email")
    remote_url = models.CharField(max_length=128, blank=True, default='', help_text="Адрес L2")
    remote_token = models.CharField(max_length=128, blank=True, default='', help_text="Токен L2")
    license_data = models.CharField(max_length=128, blank=True, default='', help_text="Лицензия")
    client = models.ForeignKey(Card, default=None, blank=True, null=True, db_index=True, help_text='Суррогатный пациент для мониторигна', on_delete=models.SET_NULL)
    research = models.ManyToManyField(Researches, blank=True, default=None, help_text="Обязательные мониторинги")

    @staticmethod
    def get_default_hospital() -> Optional['Hospitals']:
        hosp = Hospitals.objects.filter(hide=False, is_default=True).first()

        if not hosp:
            hosp = Hospitals.objects.filter(hide=False, code_tfoms=SettingManager.get("org_id", default='', default_type='s')).first()
            if hosp:
                hosp.is_default = True
                hosp.save()

        return hosp

    @property
    def safe_full_title(self):
        return self.title or self.short_title

    @property
    def safe_short_title(self):
        return self.short_title or self.title

    @property
    def safe_address(self):
        return self.address or SettingManager.get("org_address")

    @property
    def safe_phones(self):
        return self.phones or SettingManager.get("org_phones")

    @property
    def safe_ogrn(self):
        return self.ogrn or SettingManager.get("org_ogrn")

    @property
    def safe_www(self):
        return self.www or SettingManager.get("org_www")

    @property
    def safe_email(self):
        # если отсутствует email то адрес сайта
        return self.email or SettingManager.get("org_www")

    def __str__(self):
        return f"{self.short_title} – {self.code_tfoms}"

    class Meta:
        verbose_name = 'Больница'
        verbose_name_plural = 'Больницы'
