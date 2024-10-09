import os
from typing import Optional

from django.core.mail import EmailMessage
from django.db import models
from appconf.manager import SettingManager
from clients.models import Card
from directory.models import Researches
from hospitals.sql_func import search_hospitals
from laboratory.settings import EMAIL_HOST_USER, MEDIA_ROOT


class Hospitals(models.Model):
    title = models.CharField(max_length=255, help_text="Наименование")
    short_title = models.CharField(max_length=128, blank=True, default='', help_text="Краткое наименование", db_index=True)
    code_tfoms = models.CharField(max_length=128, blank=True, default='', help_text="Код больницы", db_index=True)
    oid = models.CharField(max_length=128, blank=True, default='', help_text="Код больницы", db_index=True)
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие больницы', db_index=True)
    is_default = models.BooleanField(default=False, blank=True, help_text='Больница по умолчанию для пустых полей', db_index=True)
    strict_tube_numbers = models.BooleanField(default=False, blank=True, help_text='Требовать наличия выделенного генератора номеров ёмкостей')
    strict_data_ownership = models.BooleanField(default=False, blank=True, help_text='Доступ к данным только с явным указанием владения')
    strict_external_numbers = models.BooleanField(default=True, blank=True, help_text='Требовать наличия выделенного генератора номеров заказов')
    address = models.CharField(max_length=128, blank=True, default='', help_text="Адрес больницы")
    phones = models.CharField(max_length=128, blank=True, default='', help_text="Телефон больницы")
    ogrn = models.CharField(max_length=16, blank=True, default='', help_text="ОГРН больницы")
    www = models.CharField(max_length=128, blank=True, default='', help_text="Сайт больницы")
    rmis_org_id = models.CharField(max_length=12, blank=True, default='', help_text="ID организации в РМИС")
    email = models.CharField(max_length=128, blank=True, default='', help_text="email")
    remote_url = models.CharField(max_length=128, blank=True, default='', help_text="Адрес L2")
    remote_token = models.CharField(max_length=128, blank=True, default='', help_text="Токен L2")
    license_data = models.CharField(max_length=128, blank=True, default='', help_text="Лицензия")
    client = models.ForeignKey(Card, default=None, blank=True, null=True, db_index=True, help_text='Суррогатный пациент для мониторинга', on_delete=models.SET_NULL)
    research = models.ManyToManyField(Researches, blank=True, default=None, help_text="Обязательные мониторинги")
    current_manager = models.CharField(max_length=128, blank=True, default='', help_text="Руководитель/ИО учреждения")
    okpo = models.CharField(max_length=10, blank=True, default='', help_text="ОКПО")
    okato = models.CharField(max_length=11, blank=True, default='', help_text="ОКАТО")
    n3_id = models.CharField(max_length=40, help_text='N3_ID', blank=True, default="")
    ecp_id = models.CharField(max_length=16, default="", blank=True, verbose_name="Код для ECP")
    legal_auth_doc_id = models.CharField(max_length=9, default="", blank=True, verbose_name="Код для кто заверил")
    oktmo = models.CharField(max_length=8, default="", blank=True, verbose_name="ОКТМО")
    need_send_result = models.BooleanField(default=False, blank=True, help_text='Требуется email-отправка результатов', db_index=True)
    is_external_performing_organization = models.BooleanField(default=False, blank=True, help_text='Внешняя исполняющая организация', db_index=True)
    has_price = models.BooleanField(default=False, blank=True, help_text='Прайс для назначивших МО', db_index=True)
    # добавить каталог для переноса заказа
    orders_pull_by_numbers = models.CharField(
        max_length=256, blank=True, default=None, null=True, help_text='URL для FTP директории получения заказов (ftp://user:password@host.example.com/path)'
    )
    orders_push_by_numbers = models.CharField(
        max_length=256, blank=True, default=None, null=True, help_text='URL для FTP директории отправки заказов (ftp://user:password@host.example.com/path)'
    )
    result_pull_by_numbers = models.CharField(
        max_length=256, blank=True, default=None, null=True, help_text='URL для FTP директории получения результатов (ftp://user:password@host.example.com/path)'
    )
    result_push_by_numbers = models.CharField(
        max_length=256, blank=True, default=None, null=True, help_text='URL для FTP директории отрпавки результатов (ftp://user:password@host.example.com/path)'
    )
    hl7_sender_application = models.CharField(max_length=55, blank=True, default=None, null=True, help_text='HL7 приложение отправитель')
    hl7_sender_org = models.CharField(max_length=55, blank=True, default=None, null=True, help_text='HL7 организация отправитель')
    hl7_receiver_appplication = models.CharField(max_length=55, blank=True, default=None, null=True, help_text='HL7 приложение получатель')
    hl7_rule_file = models.CharField(max_length=60, null=True, blank=True, default="default.json", help_text="Название ф-ла правил HL7")
    is_auto_transfer_hl7_file = models.BooleanField(default=False, blank=True, help_text='Автоматическая отправка файла в каталог', db_index=True)
    title_stamp_executor = models.CharField(max_length=255, blank=True, null=True, default=None, help_text="Ссылка на заголовок Исполнителя - клеше")
    title_stamp_customer = models.CharField(max_length=255, blank=True, null=True, default=None, help_text="Ссылка на заголовок Закачика - клеше")
    acronym_title = models.CharField(max_length=128, blank=True, default='', help_text="Акроним (Аббревиатура) наименование", db_index=True)
    send_result_after_time_min = models.PositiveSmallIntegerField(default=0, blank=True, null=True, verbose_name="Время (мин) отправки результатов")
    use_self_generate_tube = models.BooleanField(default=False, blank=True, help_text='Приоритет собственного генератора')

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
        # если отсутствует email, то адрес сайта
        return self.email or SettingManager.get("org_www")

    def send_email_with_pdf_file(self, subject, message, file, to=None):
        email = EmailMessage(
            subject,
            message,
            from_email=f"{self.safe_short_title} <{EMAIL_HOST_USER}>",
            to=[to or self.email],
        )
        email.attach(file.name, file.read(), 'application/pdf')
        email.send()

    @staticmethod
    def hospitals_need_send_result_mail():
        return [
            {"id": i.pk, "mail": i.email, "send_after_time_min": i.send_result_after_time_min} for i in Hospitals.objects.filter(need_send_result=True, email__isnull=False).exclude(email="")
        ]

    def __str__(self):
        return f"{self.short_title} – {self.code_tfoms}"

    @staticmethod
    def search_hospital(query):
        if not query:
            return []
        hospital_query = search_hospitals(hospital_title=query)
        return [{"id": d.id, "title": d.title} for d in hospital_query]

    @staticmethod
    def get_is_external_performing_organization():
        hosp = Hospitals.objects.filter(hide=False, is_external_performing_organization=True)
        return [{"id": h.id, "label": h.title} for h in hosp]

    def get_title_stamp_executor_pdf(self):
        if self.title_stamp_executor:
            return os.path.join(MEDIA_ROOT, 'title_stamp_executor_pdf', self.title_stamp_executor)
        return None

    def get_title_stamp_customer_pdf(self):
        if self.title_stamp_customer:
            return os.path.join(MEDIA_ROOT, 'title_stamp_customer_pdf', self.title_stamp_customer)
        return None

    class Meta:
        verbose_name = 'Больница'
        verbose_name_plural = 'Больницы'


class HospitalsGroup(models.Model):
    REQUIREMENT_MONITORING_HOSP = 'REQUIREMENT_MONITORING_HOSP'
    REGION_HOSP = 'REGION_HOSP'
    CHILD_HOSP = 'CHILD_HOSP'

    HOSPITAL_TYPES = (
        (REQUIREMENT_MONITORING_HOSP, 'Обязательные мониторинги'),
        (REGION_HOSP, 'По районам'),
        (CHILD_HOSP, 'Детские'),
    )

    title = models.CharField(max_length=255, help_text="Наименование")
    hospital = models.ManyToManyField(Hospitals, blank=True, default=None, help_text="Какие больница")
    research = models.ManyToManyField(Researches, blank=True, default=None, help_text="Обязательные мониторинги")
    type_hospital = models.CharField(default=None, blank=True, null=True, max_length=100, db_index=True, choices=HOSPITAL_TYPES, help_text="Тип группы")
    access_black_list_edit_monitoring = models.ManyToManyField(Researches, blank=True, default=None, help_text="Запрещенные мониторинги(Черный список)", related_name='ResearchesBlackList')
    access_white_list_edit_monitoring = models.ManyToManyField(Researches, blank=True, default=None, help_text="Разрешенные мониторинги(Белый список)", related_name='ResearchesWhiteList')

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = 'Группа больница'
        verbose_name_plural = 'Группы больницы'


class DisableIstochnikiFinansirovaniya(models.Model):
    hospital = models.ForeignKey(Hospitals, blank=False, null=False, help_text="Больница", on_delete=models.CASCADE)
    fin_source = models.ForeignKey("directions.IstochnikiFinansirovaniya", blank=False, null=False, help_text="Больница", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.hospital.title}-{self.fin_source}"

    class Meta:
        verbose_name = 'Запрещенные источники оплаты для Больницы'
        verbose_name_plural = 'Запрещенные источники оплаты для Больницы'


class HospitalParams(models.Model):
    hospital = models.ForeignKey(Hospitals, blank=False, null=False, help_text="Больница", on_delete=models.CASCADE)
    param_title = models.CharField(max_length=255, help_text="Наименование параметра")
    param_value = models.CharField(max_length=255, help_text="Значение параметра")

    def __str__(self):
        return f"{self.hospital.title}-{self.param_value}"

    class Meta:
        verbose_name = 'Параметр больницы произвольный'
        verbose_name_plural = 'Параметры больницы произвольные'
