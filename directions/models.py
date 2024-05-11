import base64
import calendar
import collections
import logging
import uuid

from django.db.models import Max

from api.sql_func import dispensarization_research
from cda.integration import get_required_signatures
import datetime
import os
import re
import time
import unicodedata
from datetime import date
from typing import List, Optional, Union
from django.contrib.postgres.fields.array import ArrayField

import simplejson as json
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.db import models, transaction
from django.utils import timezone
from jsonfield import JSONField
import clients.models as Clients
import directory.models as directory
from directions.sql_func import check_limit_assign_researches, get_count_researches_by_doc, check_confirm_patient_research, check_create_direction_patient_by_research
from directions.tasks import send_result
from forms.sql_func import sort_direction_by_file_name_contract
from laboratory.settings import (
    PERINATAL_DEATH_RESEARCH_PK,
    DISPANSERIZATION_SERVICE_PK,
    EXCLUDE_DOCTOR_PROFILE_PKS_ANKETA_NEED,
    RESEARCHES_EXCLUDE_AUTO_MEDICAL_EXAMINATION,
    AUTO_PRINT_RESEARCH_DIRECTION,
    NEED_ORDER_DIRECTION_FOR_DEFAULT_HOSPITAL,
    MEDIA_ROOT,
)
from laboratory.celery import app as celeryapp
from odii.integration import add_task_request, add_task_result
import slog.models as slog
import users.models as umodels
import cases.models as cases
from api.models import Application
from hospitals.models import Hospitals, HospitalsGroup
from laboratory.utils import strdate, localtime, current_time, strdatetime, strfdatetime, current_year, current_month, start_end_year
from podrazdeleniya.models import Podrazdeleniya
from refprocessor.processor import RefProcessor
from users.models import DoctorProfile
import contracts.models as contracts
from statistics_tickets.models import VisitPurpose, ResultOfTreatment, Outcomes, Place

from appconf.manager import SettingManager
from utils.dates import normalize_dots_date

logger = logging.getLogger(__name__)


class FrequencyOfUseResearches(models.Model):
    research = models.ForeignKey(directory.Researches, on_delete=models.CASCADE)
    user = models.ForeignKey(DoctorProfile, db_index=True, on_delete=models.CASCADE)
    cnt = models.IntegerField(default=0)

    def __str__(self):
        return str(self.user) + " - " + str(self.research) + ", " + str(self.cnt)

    @staticmethod
    def inc(research, user):
        if not FrequencyOfUseResearches.objects.filter(research=research, user=user).exists():
            FrequencyOfUseResearches(research=research, user=user, cnt=0).save()

        f = FrequencyOfUseResearches.objects.filter(research=research, user=user)[0]
        f.cnt += 1
        f.save()

    @staticmethod
    def reset(user):
        for f in FrequencyOfUseResearches.objects.filter(user=user):
            f.cnt = 0
            f.save()

    class Meta:
        verbose_name = 'Частота назначения исследований пользователем'
        verbose_name_plural = 'Частоты назначения исследований пользователем'


class CustomResearchOrdering(models.Model):
    research = models.ForeignKey(directory.Researches, on_delete=models.CASCADE)
    user = models.ForeignKey(DoctorProfile, db_index=True, on_delete=models.CASCADE)
    weight = models.IntegerField(default=0)

    def __str__(self):
        return str(self.user) + " - " + str(self.research) + ", " + str(self.weight)

    class Meta:
        verbose_name = 'Пользовательская сортировка исследований'
        verbose_name_plural = 'Пользовательские сортировки исследований'


class NoGenerator(Exception):
    pass


class TubesRegistration(models.Model):
    """
    Таблица с пробирками для исследований
    """

    id = models.AutoField(primary_key=True, db_index=True)
    number = models.BigIntegerField(db_index=True, help_text='Номер ёмкости', blank=True, null=True, default=None)
    chunk_number = models.PositiveSmallIntegerField(db_index=True, blank=True, null=True, default=None, help_text='Номер разложения ёмкости на несколько')
    type = models.ForeignKey(directory.ReleationsFT, help_text='Тип ёмкости', on_delete=models.CASCADE)
    time_get = models.DateTimeField(null=True, blank=True, help_text='Время взятия материала', db_index=True)
    doc_get = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True, related_name='docget', help_text='Кто взял материал', on_delete=models.SET_NULL)
    time_recive = models.DateTimeField(null=True, blank=True, help_text='Время получения материала', db_index=True)
    doc_recive = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True, related_name='docrecive', help_text='Кто получил материал', on_delete=models.SET_NULL)
    barcode = models.CharField(max_length=255, null=True, blank=True, help_text='Штрих-код или номер ёмкости', db_index=True)
    notice = models.CharField(max_length=512, default="", blank=True, help_text='Замечания', db_index=True)
    daynum = models.IntegerField(default=0, blank=True, null=True, help_text='Номер принятия ёмкости среди дня в лаборатории')
    is_defect = models.BooleanField(default=False, blank=True, verbose_name='Дефект')
    defect_text = models.CharField(max_length=50, default="", blank=True, help_text='Замечания')

    @staticmethod
    def make_default_external_tube(number: int):
        external_tube = directory.ReleationsFT.get_default_external_tube()
        return TubesRegistration.objects.create(number=number, type=external_tube)

    @staticmethod
    def make_external_tube(number: int, research):
        fraction = directory.Fractions.objects.filter(research=research).first()
        external_tube = fraction.relation
        return TubesRegistration.objects.create(number=number, type=external_tube)

    @staticmethod
    def get_tube_number_generator_pk(hospital: Hospitals):
        if hospital.is_default:
            if not NumberGenerator.objects.filter(hospital=hospital, key=NumberGenerator.TUBE_NUMBER, is_active=True).exists():
                max_number = TubesRegistration.objects.aggregate(Max('number'))['number__max']
                generator = NumberGenerator.objects.create(hospital=hospital, key=NumberGenerator.TUBE_NUMBER, year=-1, is_active=True, start=1, end=None, last=max_number, prepend_length=0)
            else:
                generator = NumberGenerator.objects.get(hospital=hospital, key=NumberGenerator.TUBE_NUMBER, is_active=True)
        else:
            generator = NumberGenerator.objects.filter(hospital=hospital, key=NumberGenerator.TUBE_NUMBER, is_active=True).first()
            if not generator:
                if hospital.strict_tube_numbers:
                    raise NoGenerator("Generator not found for hospital %s" % hospital.safe_short_title)
                else:
                    def_hospital = Hospitals.get_default_hospital()
                    return TubesRegistration.get_tube_number_generator_pk(def_hospital)
        return generator.pk

    @property
    def time_get_local(self):
        return localtime(self.time_get)

    @property
    def time_recive_local(self):
        return localtime(self.time_recive)

    @property
    def researches_count(self):
        return self.issledovaniya_set.all().count()

    def __str__(self):
        return "%d %s (%s, %s) %s" % (self.number, self.type.tube.title, self.doc_get, self.doc_recive, self.notice)

    def day_num(self, doc, num):
        if not self.getstatus():
            iss = Issledovaniya.objects.filter(tubes=self)
            if iss.count():
                self.set_get(iss[0].napravleniye.doc)
        new_t = False
        if not self.rstatus():
            new_t = True
            self.set_r(doc)
        if not self.daynum:
            self.daynum = num
            self.save()

        return {"n": self.daynum, "new": new_t}

    def set_get(self, doc_get):
        """
        Установка статуса взятия
        :param doc_get: врач/мед сестра, взявшая материал
        :return: None
        """
        from django.utils import timezone

        self.time_get = timezone.now()
        self.doc_get = doc_get
        self.barcode = str(self.number)
        self.save()
        slog.Log(key=str(self.number), type=9, body="", user=doc_get).save()

    def getstatus(self, one_by_one=False):
        """
        Получение статуса взятия
        :return:
        """
        return (self.time_get_local is not None and self.doc_get is not None) or (self.type.receive_in_lab and one_by_one)

    def set_r(self, doc_r):
        """
        Установка статуса принятия материала лабораторией
        :param doc_r: врач/лаборант, принявший материал
        :return:
        """
        from django.utils import timezone

        if not self.getstatus():
            self.set_get(doc_r)

        self.time_recive = timezone.now()
        self.doc_recive = doc_r
        self.save()
        slog.Log(key=str(self.number), user=doc_r, type=11, body=json.dumps({"Замечание не приёма": self.notice}) if self.notice != "" else "").save()

    def set_notice(self, doc_r, notice):
        """
        Установка замечания для пробирки
        :param doc_r: врач/лаборант, указавший замечание
        :param notice: текст замечания
        :return:
        """
        notice = notice.strip()
        if notice != "":
            self.doc_recive = None
            self.time_recive = None
        self.notice = notice
        self.save()
        slog.Log(key=str(self.number), user=doc_r, type=12, body=json.dumps({"Замечание не приёма": self.notice})).save()

    def clear_notice(self, doc_r):
        old_notice = self.notice
        if old_notice == "":
            return
        self.notice = ""
        self.save()
        slog.Log(key=str(self.number), user=doc_r, type=4000, body=json.dumps({"Удалённое замечание": old_notice})).save()

    def rstatus(self, check_not=False):
        """
        Получение статуса принятия материала лабораторией
        :return: статус принятия
        """
        if self.doc_recive and (not check_not or self.notice == ""):
            return True
        return False

    def getbc(self):
        """
        Получение номера штрих-кода
        :return: штрих-код
        """
        if self.barcode and self.barcode.isnumeric():
            return self.barcode
        return self.number

    def get_details(self):
        if not self.time_get or not self.doc_get:
            return None
        return {
            "datetime": strdatetime(self.time_get),
            "executor": str(self.doc_get),
        }

    class Meta:
        verbose_name = 'Ёмкость для направления'
        verbose_name_plural = 'Ёмкости для направлений'


class IstochnikiFinansirovaniya(models.Model):
    """
    Таблица источников финансирования
    """

    title = models.CharField(max_length=511, verbose_name='Название')
    active_status = models.BooleanField(default=True, verbose_name='Статус активности')
    base = models.ForeignKey(Clients.CardBase, verbose_name='База пациентов, к которой относится источник финансирования', db_index=True, on_delete=models.CASCADE)
    hide = models.BooleanField(default=False, blank=True, verbose_name="Скрытие", db_index=True)
    rmis_auto_send = models.BooleanField(default=True, blank=True, verbose_name="Автоматическая отправка в РМИС", db_index=True)
    default_diagnos = models.CharField(max_length=36, verbose_name="Диагноз по умолчанию", default="", blank=True)
    contracts = models.ForeignKey(contracts.Contract, null=True, blank=True, default='', on_delete=models.CASCADE, verbose_name="Договоры")
    order_weight = models.SmallIntegerField(default=0, verbose_name="Сортировка")
    n3_code = models.CharField(max_length=2, default="", blank=True, verbose_name="Код источника финансирования для N3")
    ecp_code = models.CharField(max_length=16, default="", blank=True, verbose_name="Код источника финансирования для ECP")

    def get_n3_code(self):
        codes = {
            'омс': '1',
            'бюджет': '2',
            'платные услуги': '3',
            'платно': '3',
            'дмс': '4',
            'собственные средства': '5',
            'другое': '6',
        }
        if not self.n3_code:
            lower_title = self.title.lower()

            if lower_title in codes:
                self.n3_code = codes[lower_title]
                self.save()

        return self.n3_code or codes['другое']

    def get_ecp_code(self):
        return self.ecp_code or '380101000000023'

    def __str__(self):
        return "{} {} (скрыт: {})".format(self.base, self.title, self.hide)

    @staticmethod
    def get_price_modifier(finsource, work_place_link=None):
        """
        На основании источника финансирования возвращает прайс(объект)+модификатор(множитель цены)
        Если источник финансирования ДМС поиск осуществляется по цепочке company-contract. Company(Страховая организация)
        Если источник финансирования МЕДОСМОТР поиск осуществляется по цепочке company-contract. Company(место работы)
        Если источник финансирования ПЛАТНО поиск осуществляется по цепочке ист.фин-contract-прайс
        Если источник финансирования ОМС, ДИСПАНСЕРИЗАЦИЯ поиск осуществляется по цепочке ист.фин-contract-прайс
        Если источник финансирования Бюджет поиск осуществляется по цепочке contract
        """
        price_modifier = None
        price_contract = set(SettingManager.get("price_contract").split(','))
        price_company = set(SettingManager.get("price_company").split(','))
        if finsource:
            if finsource.title.upper() in price_contract:
                contract_l = IstochnikiFinansirovaniya.objects.values_list('contracts_id').filter(pk=finsource.pk).first()
                if contract_l[0]:
                    price_modifier = contracts.Contract.objects.values_list('price', 'modifier').get(id=contract_l[0])
            elif finsource.title.upper() in price_company and work_place_link:
                contract_l = work_place_link.contract_id
                if contract_l:
                    price_modifier = contracts.Contract.objects.values_list('price', 'modifier').get(id=contract_l)

        return price_modifier

    class Meta:
        verbose_name = 'Источник финансирования'
        verbose_name_plural = 'Источники финансирования'


class Diagnoses(models.Model):
    M = (
        (0, "Диапазон"),
        (1, "Группа"),
        (2, "Значение"),
    )
    code = models.CharField(max_length=255, db_index=True)
    title = models.TextField(db_index=True)
    parent = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    d_type = models.CharField(max_length=255, db_index=True)
    m_type = models.IntegerField(choices=M, db_index=True)
    rmis_id = models.CharField(max_length=128, db_index=True, blank=True, default=None, null=True)
    nsi_id = models.CharField(max_length=128, blank=True, default=None, null=True)
    hide = models.BooleanField(default=False, blank=True, db_index=True)

    def __str__(self):
        return "{} {}".format(self.code, self.title)


class KeyValue(models.Model):
    key = models.CharField(max_length=255, db_index=True)
    value = models.TextField(db_index=True)

    def __str__(self):
        return "{} {}".format(self.key, self.value)


class RMISServiceInactive(models.Model):
    rmis_id = models.CharField(max_length=30, primary_key=True)
    enabled = models.BooleanField(default=True, blank=True)

    @staticmethod
    def checkInactive(serviceId, enabled):
        r = RMISServiceInactive.objects.filter(rmis_id=serviceId)
        if not r.exists() and enabled:
            RMISServiceInactive(rmis_id=serviceId, enabled=enabled).save()
        elif r.exists() and r[0].enabled != enabled:
            r[0].enabled = enabled
            r[0].save()

    @staticmethod
    def isInactive(serviceId):
        r = RMISServiceInactive.objects.filter(rmis_id=serviceId)
        return r.exists() and r[0].enabled

    def __str__(self):
        return "{} {}".format(self.rmis_id, self.enabled)


class RMISOrgs(models.Model):
    rmis_id = models.IntegerField(primary_key=True, editable=False)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class ExternalOrganization(models.Model):
    title = models.CharField(max_length=255)
    hide = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Внешняя организация'
        verbose_name_plural = 'Внешние организации'


class RegisteredOrders(models.Model):
    order_number = models.BigIntegerField(db_index=True, help_text='Номер заказа', blank=True, null=True, default=None)
    organization = models.ForeignKey(Hospitals, on_delete=models.PROTECT, db_index=True)
    services = ArrayField(models.CharField(max_length=255), help_text='Услуги заказа')
    patient_card = models.ForeignKey(Clients.Card, db_index=True, on_delete=models.PROTECT)
    file_name = models.CharField(max_length=255, db_index=True)
    totally_completed = models.BooleanField(default=False, db_index=True, help_text='Все исследования по заказу завершены')
    need_check_for_results_redirection = models.BooleanField(default=False, blank=True, help_text='Требуется проверка на перенаправление результатов')
    created_at = models.DateTimeField(auto_now_add=True)
    hl7 = models.TextField(verbose_name="HL7 в base64", blank=True, null=True, default=None)

    def __str__(self):
        return f"{self.order_number} {self.patient_card}"

    class Meta:
        verbose_name = 'Внешний заказ направления'
        verbose_name_plural = 'Внешние заказы направлений'

    def get_registered_orders_by_file_name(self):
        return RegisteredOrders.objects.values_list("id", flat=True).filter(file_name=self.file_name)


class Napravleniya(models.Model):
    """
    Таблица направлений
    """

    PURPOSE_PRELIMINARY_EXAMINATION = 'PRELIMINARY_EXAMINATION'
    PURPOSE_WORK_EXAMINATION = 'WORK_EXAMINATION'
    PURPOSE_DRIVE_EXAMINATION = 'DRIVE_EXAMINATION'
    PURPOSE_WEAPON_EXAMINATION = 'WEAPON_EXAMINATION'
    PURPOSE_PERIODIC_EXAMINATION = 'PERIODIC_EXAMINATION'
    PURPOSE_CONSULTATION = 'CONSULTATION'
    PURPOSE_SIMPLE_EXAMINATION = 'SIMPLE_EXAMINATION'
    PURPOSE_HOSPITALIZATION = 'OSPITALIZATION'

    PURPOSES = (
        (PURPOSE_PRELIMINARY_EXAMINATION, 'Предварительный медосмотр'),
        (PURPOSE_WORK_EXAMINATION, 'На работу'),
        (PURPOSE_DRIVE_EXAMINATION, 'На водительское'),
        (PURPOSE_WEAPON_EXAMINATION, 'На оружие'),
        (PURPOSE_PERIODIC_EXAMINATION, 'Периодический медосмотр'),
        (PURPOSE_CONSULTATION, 'Консультация'),
        (PURPOSE_SIMPLE_EXAMINATION, 'Обследование'),
        (PURPOSE_HOSPITALIZATION, 'Госпитализация'),
    )

    data_sozdaniya = models.DateTimeField(auto_now_add=True, help_text='Дата создания направления', db_index=True)
    visit_date = models.DateTimeField(help_text='Дата посещения по направлению', db_index=True, default=None, blank=True, null=True)
    visit_who_mark = models.ForeignKey(
        DoctorProfile, related_name="visit_who_mark", default=None, blank=True, null=True, help_text='Профиль, который отметил посещение', on_delete=models.SET_NULL
    )
    diagnos = models.CharField(max_length=511, help_text='Диагноз', default='', blank=True)
    vich_code = models.CharField(max_length=12, help_text='Код для направления на СПИД', default='', blank=True)
    client = models.ForeignKey(Clients.Card, db_index=True, help_text='Пациент', on_delete=models.CASCADE)
    doc = models.ForeignKey(DoctorProfile, db_index=True, null=True, help_text='Лечащий врач', on_delete=models.CASCADE)
    istochnik_f = models.ForeignKey(IstochnikiFinansirovaniya, blank=True, null=True, help_text='Источник финансирования', on_delete=models.CASCADE)
    price_category = models.ForeignKey('contracts.PriceCategory', blank=True, null=True, help_text='Категория прайса', on_delete=models.SET_NULL)
    history_num = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='Номер истории')
    additional_num = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='Дополнительный номер')
    microbiology_num = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='Микробиология номер')
    rmis_case_id = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='РМИС: Номер случая')
    rmis_visit_id = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='РМИС: Номер посещения')
    rmis_hosp_id = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='РМИС: ЗОГ')
    rmis_resend_services = models.BooleanField(default=False, blank=True, help_text='Переотправить услуги?', db_index=True)
    doc_who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_who_create", help_text='Создатель направления', on_delete=models.SET_NULL)
    cancel = models.BooleanField(default=False, blank=True, help_text='Отмена направления')
    rmis_number = models.CharField(max_length=20, default=None, blank=True, null=True, db_index=True, help_text='ID направления в РМИС')
    result_rmis_send = models.BooleanField(default=False, blank=True, help_text='Результат отправлен в РМИС?', db_index=True)
    imported_from_rmis = models.BooleanField(default=False, blank=True, db_index=True, help_text='Направление создано на основе направления из РМИС?')
    imported_org = models.ForeignKey(RMISOrgs, default=None, blank=True, null=True, on_delete=models.SET_NULL)
    imported_directions_rmis_send = models.BooleanField(default=False, blank=True, help_text='Для направления из РМИС отправлен бланк', db_index=True)
    force_rmis_send = models.BooleanField(default=False, blank=True, help_text='Подтверждение ручной отправки в РМИС')
    forcer_rmis_send = models.ForeignKey(
        DoctorProfile, default=None, blank=True, null=True, related_name="doc_forcer_rmis_send", help_text='Исполнитель подтверждения отправки в РМИС', on_delete=models.SET_NULL
    )

    case = models.ForeignKey(cases.Case, default=None, blank=True, null=True, help_text='Случай обслуживания', on_delete=models.SET_NULL)
    num_contract = models.CharField(max_length=25, default=None, blank=True, null=True, db_index=True, help_text='Номер контракта')
    protect_code = models.CharField(max_length=32, default=None, blank=True, null=True, db_index=True, help_text="Контрольная сумма контракта")

    polis_who_give = models.TextField(blank=True, null=True, default=None, help_text="Страховая компания")
    polis_n = models.CharField(max_length=62, blank=True, null=True, default=None, help_text="Полис")
    parent = models.ForeignKey('Issledovaniya', related_name='parent_iss', help_text="Протокол-основание", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    parent_auto_gen = models.ForeignKey(
        'Issledovaniya', related_name='parent_auto_gen', help_text="Авто сгенерированное", db_index=True, blank=True, null=True, default=None, on_delete=models.SET_NULL
    )
    parent_slave_hosp = models.ForeignKey(
        'Issledovaniya', related_name='parent_slave_hosp', help_text="Из стационарного протокола", db_index=True, blank=True, null=True, default=None, on_delete=models.SET_NULL
    )
    parent_case = models.ForeignKey('Issledovaniya', related_name='parent_case', help_text="Случай основание", db_index=True, blank=True, null=True, default=None, on_delete=models.SET_NULL)
    parent_complex_research = models.ForeignKey(
        "Issledovaniya", related_name="parent_complex_research", help_text="Комлексная услуга основание", db_index=True, blank=True, null=True, default=None, on_delete=models.SET_NULL
    )
    rmis_slot_id = models.CharField(max_length=20, blank=True, null=True, default=None, help_text="РМИС слот")
    microbiology_n = models.CharField(max_length=10, blank=True, default='', help_text="Номер в микробиологической лаборатории")
    time_microbiology_receive = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Дата/время приёма материала микробиологии')
    doc_microbiology_receive = models.ForeignKey(
        DoctorProfile, default=None, blank=True, null=True, related_name="doc_microbiology_receive", help_text='Кто принял материал микробиологии', on_delete=models.SET_NULL
    )
    time_gistology_receive = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время приёма материала гистологией')
    doc_gistology_receive = models.ForeignKey(
        DoctorProfile, null=True, blank=True, related_name="doc_gistology_receive", db_index=True, help_text='Профиль, принявший гистологический материал', on_delete=models.SET_NULL
    )
    need_resend_amd = models.BooleanField(default=False, blank=True, help_text='Требуется отправка в АМД?')
    need_resend_n3 = models.BooleanField(default=False, blank=True, help_text='Требуется отправка в N3?')
    need_resend_l2 = models.BooleanField(default=False, blank=True, help_text='Требуется отправка в L2.Core?')
    need_resend_crie = models.BooleanField(default=False, blank=True, help_text='Требуется отправка в CRIE')
    core_id = models.CharField(max_length=32, default=None, blank=True, null=True, db_index=True, help_text='Номер документа в L2.Core')
    amd_number = models.CharField(max_length=20, default=None, blank=True, null=True, db_index=True, help_text='Номер документа в АМД')
    error_amd = models.BooleanField(default=False, blank=True, help_text='Ошибка отправка в АМД?')
    amd_excluded = models.BooleanField(default=False, blank=True, help_text='Исключить из выгрузки в АМД?')
    amd_message = models.TextField(blank=True, null=True, default=None, help_text="Сообщение об ошибке АМД")
    purpose = models.CharField(max_length=64, null=True, blank=True, default=None, db_index=True, choices=PURPOSES, help_text="Цель направления")
    external_organization = models.ForeignKey(ExternalOrganization, default=None, blank=True, null=True, help_text='Внешняя организация', on_delete=models.SET_NULL)
    harmful_factor = models.CharField(max_length=255, blank=True, default='')
    workplace = models.CharField(max_length=255, blank=True, default='', db_index=True)
    hospital = models.ForeignKey(Hospitals, default=None, blank=True, null=True, on_delete=models.SET_NULL)
    id_in_hospital = models.CharField(max_length=20, default=None, blank=True, null=True, db_index=True, help_text='Номер документа во внешней организации')
    is_external = models.BooleanField(default=False, blank=True, null=True)
    rmis_case_number = models.CharField(max_length=20, default=None, blank=True, null=True, db_index=True, help_text='ID случая в РМИС')
    rmis_visit_number = models.CharField(max_length=20, default=None, blank=True, null=True, db_index=True, help_text='ID посещения в РМИС')
    qr_check_token = models.UUIDField(null=True, default=None, blank=True, unique=True, help_text='Токен для проверки результата по QR внешним сервисом')
    title_org_initiator = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='Организация направитель')
    ogrn_org_initiator = models.CharField(max_length=13, default=None, blank=True, null=True, help_text='ОГРН организации направитель')
    onkor_message_id = models.CharField(max_length=40, default=None, blank=True, null=True, help_text='Onkor message id', db_index=True)
    n3_odli_id = models.CharField(max_length=40, default=None, blank=True, null=True, help_text='ИД ОДЛИ', db_index=True)
    n3_iemk_ok = models.BooleanField(default=False, blank=True, null=True)
    ecp_ok = models.BooleanField(default=False, blank=True, null=True)
    vi_id = models.CharField(max_length=40, default=None, blank=True, null=True, help_text='ИД VI', db_index=True)
    eds_required_documents = ArrayField(models.CharField(max_length=3), verbose_name='Необходимые документы для ЭЦП', default=list, blank=True, db_index=True)
    eds_required_signature_types = ArrayField(models.CharField(max_length=32), verbose_name='Необходимые подписи для ЭЦП', default=list, blank=True, db_index=True)
    eds_total_signed = models.BooleanField(verbose_name='Результат полностью подписан', blank=True, default=False, db_index=True)
    eds_total_signed_at = models.DateTimeField(help_text='Дата и время полного подписания', db_index=True, blank=True, default=None, null=True)
    co_executor = models.ForeignKey(DoctorProfile, null=True, blank=True, related_name="doc_co_executor", db_index=True, help_text='Со-исполнитель', on_delete=models.SET_NULL)
    register_number = models.CharField(db_column='additional_number', max_length=24, blank=True, default='', help_text="Дополнительный номер при регистрации направления", db_index=True)
    register_number_year = models.SmallIntegerField(blank=True, default=None, null=True, help_text="Год при регистрации направления", db_index=True)
    planed_doctor_executor = models.ForeignKey(DoctorProfile, null=True, blank=True, related_name="planed_doctor", db_index=True, help_text='Планируемый врач', on_delete=models.SET_NULL)
    total_confirmed = models.BooleanField(verbose_name='Результат полностью подтверждён', blank=True, default=False, db_index=True)
    last_confirmed_at = models.DateTimeField(help_text='Дата и время последнего подтверждения', db_index=True, blank=True, default=None, null=True)
    emdr_id = models.CharField(max_length=40, default=None, blank=True, null=True, help_text='ИД РЭМД', db_index=True)
    email_with_results_sent = models.BooleanField(verbose_name='Результаты отправлены на почту', blank=True, default=False, db_index=True)
    celery_send_task_ids = ArrayField(models.CharField(max_length=64), default=list, blank=True, db_index=True)
    external_order = models.ForeignKey(RegisteredOrders, default=None, blank=True, null=True, db_index=True, on_delete=models.PROTECT, help_text='Внешний заказ')
    need_order_redirection = models.BooleanField(default=False, blank=True, help_text='Требуется проверка на перенаправление заказа')
    order_redirection_number = models.CharField(max_length=24, default=None, blank=True, null=True, db_index=True, help_text='Номер перенаправленного заказа')
    external_executor_hospital = models.ForeignKey(
        Hospitals, related_name='external_executor_hospital', default=None, blank=True, null=True, on_delete=models.PROTECT, help_text='Внешняя организация-исполнитель'
    )
    time_send_hl7 = models.DateTimeField(help_text='Дата и время отправки заказа', db_index=True, blank=True, default=None, null=True)
    price_name = models.ForeignKey(contracts.PriceName, default=None, blank=True, null=True, on_delete=models.PROTECT, help_text='Прайс для направления')
    cpp_upload_id = models.CharField(max_length=128, default=None, blank=True, null=True, db_index=True, help_text='Id-загрузки ЦПП')
    need_resend_cpp = models.BooleanField(default=False, blank=True, help_text='Требуется отправка в ЦПП')
    ecp_direction_number = models.CharField(max_length=64, default=None, blank=True, null=True, db_index=True, help_text='Id-направления ЕЦП')

    def sync_confirmed_fields(self, skip_post=False):
        has_confirmed_iss = Issledovaniya.objects.filter(napravleniye=self, time_confirmation__isnull=False).exists()
        no_unconfirmed_iss = not Issledovaniya.objects.filter(napravleniye=self, time_confirmation__isnull=True).exists()

        total_confirmed = has_confirmed_iss and no_unconfirmed_iss
        last_confirmed_at = None
        if has_confirmed_iss:
            last_confirmed_at = Issledovaniya.objects.filter(napravleniye=self, time_confirmation__isnull=False).order_by('time_confirmation').values_list('time_confirmation', flat=True)[0]

        updated = []

        if total_confirmed != self.total_confirmed:
            self.total_confirmed = total_confirmed
            updated.append('total_confirmed')

        if last_confirmed_at != self.last_confirmed_at:
            self.last_confirmed_at = last_confirmed_at
            updated.append('last_confirmed_at')
        if updated:
            self.save(update_fields=updated)

        if not skip_post:
            if self.is_all_confirm():
                self.post_confirmation()
            else:
                self.post_reset_confirmation()

    def get_eds_title(self):
        iss = Issledovaniya.objects.filter(napravleniye=self)

        for i in iss:
            research: directory.Researches = i.research
            if research.desc or research.is_extract:
                return research.title
        return 'Лабораторное исследование'

    def get_eds_generator(self):
        iss = Issledovaniya.objects.filter(napravleniye=self)
        gen_name = 'Laboratory_min'
        for i in iss:
            research: directory.Researches = i.research
            if research.is_paraclinic:
                gen_name = 'Instrumental'
            elif research.desc:
                gen_name = research.generator_name
            elif research.is_extract:
                gen_name = 'DischargeSummary_min'
        return gen_name

    def required_signatures(self, fast=False, need_save=False):
        if self.eds_total_signed or (fast and self.eds_required_documents and self.eds_required_signature_types):
            return {
                "docTypes": self.eds_required_documents,
                "signsRequired": self.eds_required_signature_types,
            }

        if SettingManager.l2('l2vi') or SettingManager.l2('cdator'):
            data = {
                "needCda": (
                    Issledovaniya.objects.filter(napravleniye=self, research__generator_name__isnull=False)
                    .exclude(research__generator_name="")
                    .exclude(research__podrazdeleniye__p_type=2)
                    .exists()
                    or Issledovaniya.objects.filter(napravleniye=self, research__generator_name__isnull=False, research__podrazdeleniye__p_type=2).exists(),
                ),
                "signsRequired": None,
            }
        else:
            data = get_required_signatures(self.get_eds_title())

        result = {
            "docTypes": ['PDF', 'CDA'] if data.get('needCda') else ['PDF'],
            "signsRequired": data.get('signsRequired') or ['Врач', 'Медицинская организация'],
        }

        if need_save:
            updated = []
            if any([x not in self.eds_required_documents for x in result['docTypes']]) or len(self.eds_required_documents) != len(result['docTypes']):
                self.eds_required_documents = result['docTypes']
                updated.append('eds_required_documents')

            if any([x not in self.eds_required_signature_types for x in result['signsRequired']]) or len(self.eds_required_signature_types) != len(result['signsRequired']):
                self.eds_required_signature_types = result['signsRequired']
                updated.append('eds_required_signature_types')

            if updated:
                self.save(update_fields=updated)

        return result

    def get_eds_total_signed(self, forced=False):
        if self.eds_total_signed and not forced:
            return True
        rs = self.required_signatures(fast=True, need_save=True)

        status = len(rs['docTypes']) > 0 and len(rs['signsRequired']) > 0

        for r in rs['docTypes']:
            dd: DirectionDocument = DirectionDocument.objects.filter(direction=self, is_archive=False, last_confirmed_at=self.last_time_confirm(), file_type=r.lower()).first()

            has_signatures = []
            empty_signatures = rs['signsRequired']
            if dd:
                for s in DocumentSign.objects.filter(document=dd):
                    has_signatures.append(s.sign_type)

                    empty_signatures = [x for x in empty_signatures if x != s.sign_type]
            if len(empty_signatures) != 0:
                status = False
                break

        if status != self.eds_total_signed:
            self.eds_total_signed = status
            if status:
                self.eds_total_signed_at = timezone.now()
            else:
                self.eds_total_signed_at = None
            self.save(update_fields=['eds_total_signed', 'eds_total_signed_at'])

        return status

    def get_doc_podrazdeleniye_title(self):
        if self.hospital and (self.is_external or not self.hospital.is_default):
            parts = [
                self.hospital_short_title,
            ]
        else:
            parts = []

        if self.doc and self.doc.podrazdeleniye:
            parts.append(self.doc.podrazdeleniye.title)

        return ', '.join(parts)

    def get_hospital(self):
        if self.doc and self.doc.hospital and not self.is_external:
            if self.hospital != self.doc.hospital:
                self.hospital = self.doc.hospital
                self.save(update_fields=['hospital'])
            return self.doc.hospital
        if not self.hospital:
            self.hospital = Hospitals.get_default_hospital()
            self.save(update_fields=['hospital'])
        return self.hospital

    def get_hospital_tfoms_id(self):
        hosp = self.get_hospital()
        if not hosp:
            return None
        return hosp.code_tfoms

    @property
    def hospital_title(self):
        hosp = self.get_hospital()
        if hosp:
            return hosp.title
        return SettingManager.get("org_title")

    def get_title_org_initiator(self):
        return (self.title_org_initiator or self.hospital_title or "").replace("\"", " ")

    @property
    def hospital_ogrn(self):
        hosp = self.get_hospital()
        if hosp:
            return hosp.ogrn
        return SettingManager.get("org_ogrn")

    @property
    def hospital_n3id(self):
        iss = Issledovaniya.objects.filter(napravleniye_id=self).first()
        if iss:
            return iss.doc_confirmation.hospital.n3_id
        return None

    @property
    def department_n3id(self):
        iss = Issledovaniya.objects.filter(napravleniye_id=self).first()
        if iss:
            return iss.doc_confirmation.podrazdeleniye.n3_id if iss.doc_confirmation.podrazdeleniye.n3_id else iss.doc_confirmation.hospital.n3_id
        return None

    @property
    def hospital_ecp_id(self):
        hosp = self.get_hospital()
        if hosp:
            return hosp.ecp_id
        return None

    def get_ogrn_org_initiator(self):
        return self.ogrn_org_initiator or self.hospital_ogrn or ""

    @property
    def hospital_short_title(self):
        hosp = self.get_hospital()
        if hosp:
            return hosp.safe_short_title
        return SettingManager.get("org_title")

    @property
    def hospital_address(self):
        hosp = self.get_hospital()
        if hosp:
            return hosp.safe_address
        return SettingManager.get("org_address")

    @property
    def hospital_phones(self):
        hosp = self.get_hospital()
        if hosp:
            return hosp.safe_phones
        return SettingManager.get("org_phones")

    @property
    def hospital_www(self):
        hosp = self.get_hospital()
        if hosp:
            return hosp.safe_www
        return SettingManager.get("org_www")

    @property
    def data_sozdaniya_local(self):
        return localtime(self.data_sozdaniya)

    @property
    def visit_date_local(self):
        return localtime(self.visit_date)

    @property
    def services(self) -> List[directory.Researches]:
        result = []
        for iss in self.issledovaniya_set.all().order_by('research__title'):
            result.append(iss.research)
        return result

    def __str__(self):
        return "%d для пациента %s (врач %s, выписал %s, %s, %s, %s, par: [%s])" % (
            self.pk,
            self.client.individual.fio(),
            "" if not self.doc else self.doc.get_fio(),
            self.doc_who_create,
            self.rmis_number,
            self.rmis_case_id,
            self.rmis_hosp_id,
            str(self.parent),
        )

    def get_instructions(self):
        r = []
        for i in Issledovaniya.objects.filter(napravleniye=self).exclude(research__instructions=""):
            r.append({"pk": i.research_id, "title": i.research.title, "text": i.research.instructions})
        return r

    def get_executors(self):
        executors = {}

        i: Issledovaniya
        for i in self.issledovaniya_set.all():
            if i.doc_confirmation_id not in executors:
                executors[i.doc_confirmation_id] = i.doc_confirmation_fio
            if i.executor_confirmation:
                executors[i.executor_confirmation_id] = i.executor_confirmation.get_fio()
        return executors

    @property
    def fin_title(self):
        return self.istochnik_f.title if self.istochnik_f else ''

    def set_polis(self):
        i = self.client.get_data_individual(empty=True)
        c = False
        if i['oms']['polis_num']:
            n = ('' if not i['oms']['polis_serial'] else i['oms']['polis_serial'] + ' ') + i['oms']['polis_num']
            if n != self.polis_n:
                c = True
                self.polis_n = n
        if i['oms']['polis_issued'] and self.polis_who_give != i['oms']['polis_issued']:
            self.polis_who_give = i['oms']['polis_issued']
            c = True
        if c:
            self.save()

    def fill_acsn(self):
        if not SettingManager.l2('fill_acsn'):
            return
        iss: Issledovaniya
        card = self.client
        individual = card.individual

        print('fill_acsn', str(self))  # noqa: T001

        for iss in self.issledovaniya_set.filter(acsn_id__isnull=True):
            if iss.research.is_paraclinic and iss.research.podrazdeleniye and iss.research.podrazdeleniye.can_has_pacs and iss.research.nsi_id:
                has_acsn = False
                data_to_log = {}
                try:
                    add_task_resp = add_task_request(
                        self.hospital_n3id,
                        {
                            **card.get_data_individual(full_empty=True, only_json_serializable=True),
                            "family": individual.family,
                            "name": individual.name,
                            "patronymic": individual.patronymic,
                            "birthday": individual.birthday.strftime("%Y-%m-%d"),
                            "docs": card.get_n3_documents(),
                            "sex": individual.sex,
                            "card": {
                                "base": {"pk": card.base_id, "title": card.base.title, "short_title": card.base.short_title},
                                "pk": card.pk,
                                "number": card.number,
                                "n3Id": card.n3_id,
                                "numberWithType": card.number_with_type(),
                            },
                        },
                        self.pk,
                        self.istochnik_f.get_n3_code() if self.istochnik_f else '6',
                        iss.research.nsi_id,
                        self.diagnos,
                        self.doc.uploading_data,
                    )

                    acsn = None
                    n3_odii_task = None
                    n3_odii_service_request = None
                    n3_odii_patient = None

                    for entry in add_task_resp.get('entry', []):
                        t = entry.get('resource', {}).get('resourceType')
                        u = entry.get('fullUrl')
                        if not u:
                            continue
                        if '/' in u:
                            u = u.split('/')[1]
                        else:
                            u = u.split(':')[2]
                        if t == 'Task':
                            n3_odii_task = u
                            for idt in entry['resource'].get('identifier', []):
                                for cd in idt.get('type', {}).get('coding', []):
                                    if cd.get('code') == 'ACSN':
                                        acsn = idt.get('value')
                                        break
                                if acsn:
                                    break
                        elif t == 'ServiceRequest':
                            n3_odii_service_request = u
                        elif t == 'Patient':
                            n3_odii_patient = u

                    data_to_log = {
                        'acsn': acsn,
                        'n3_odii_task': n3_odii_task,
                        'n3_odii_service_request': n3_odii_service_request,
                        'n3_odii_patient': n3_odii_patient,
                    }

                    if acsn and n3_odii_task and n3_odii_service_request and n3_odii_patient:
                        iss.acsn_id = str(acsn)
                        iss.n3_odii_task = str(n3_odii_task)
                        iss.n3_odii_service_request = str(n3_odii_service_request)
                        iss.n3_odii_patient = str(n3_odii_patient)
                        iss.save(update_fields=['acsn_id', 'n3_odii_task', 'n3_odii_service_request', 'n3_odii_patient'])
                        has_acsn = True
                    else:
                        logger.error(add_task_resp)

                    logger.error(f"ACSN REQUEST: {data_to_log}")
                except Exception as e:
                    logger.error(e)

                if has_acsn:
                    slog.Log.log(key=self.pk, type=60016, body=data_to_log)
                else:
                    slog.Log.log(key=self.pk, type=60017, body=data_to_log)

    def send_task_result(self):
        if not SettingManager.l2('fill_acsn'):
            return
        pdf_content = None

        if self.is_all_confirm():
            try:
                from results.views import result_print

                request_tuple = collections.namedtuple('HttpRequest', ('GET', 'user', 'plain_response'))
                req = {
                    'GET': {
                        "pk": f'[{self.pk}]',
                        "split": '1',
                        "leftnone": '0',
                        "inline": '1',
                        "protocol_plain_text": '1',
                    },
                    'user': self.doc.user,
                    'plain_response': True,
                }
                pdf_content = base64.b64encode(result_print(request_tuple(**req))).decode('utf-8')
            except Exception as e:
                logger.error(e)

        print('send_task_result', str(self))  # noqa: T001

        iss: Issledovaniya
        for iss in self.issledovaniya_set.filter(acsn_id__isnull=False):
            if not iss.research.is_paraclinic:
                print(str(iss), '!is_paraclinic')  # noqa: T001
                continue
            if not iss.research.podrazdeleniye:
                print(str(iss), '!iss.research.podrazdeleniye')  # noqa: T001
                continue
            if not iss.research.podrazdeleniye.can_has_pacs:
                print(str(iss), '!iss.research.podrazdeleniye.can_has_pacs')  # noqa: T001
                continue
            if not iss.research.nsi_id:
                print(str(iss), '!iss.research.nsi_id')  # noqa: T001
                continue

            has_image = bool(iss.study_instance_uid_tag)
            has_protocol = bool(pdf_content)

            if not has_image and not has_protocol:
                print(str(iss), '{has_image=} {has_protocol=}')  # noqa: T001
                continue

            try:
                add_task_result_resp = add_task_result(
                    self.hospital_n3id,
                    iss.n3_odii_patient,
                    iss.n3_odii_task,
                    iss.n3_odii_service_request,
                    iss.study_instance_uid_tag,
                    iss.acsn_id,
                    self.pk,
                    iss.research.nsi_id,
                    iss.research.odii_type or ('' if not iss.research.podrazdeleniye else iss.research.podrazdeleniye.odii_type),
                    iss.doc_confirmation.uploading_data if iss.doc_confirmation else self.doc.uploading_data,
                    iss.time_confirmation_local.isoformat() if iss.time_confirmation else timezone.now().isoformat(),
                    pdf_content,
                )

                task_resp = None

                for entry in add_task_result_resp.get('entry', []):
                    t = entry.get('resource', {}).get('resourceType')
                    u = entry.get('fullUrl')
                    if not u:
                        continue
                    if '/' in u:
                        u = u.split('/')[1]
                    else:
                        u = u.split(':')[2]
                    if t == 'Task' and entry.get('response', {}).get('location'):
                        task_resp = entry.get('response', {}).get('location').split('/')[1]
                t = None
                if task_resp:
                    print('send_task_result: OK')  # noqa: T001
                    iss.n3_odii_uploaded_task_id = task_resp
                    iss.save(update_fields=['n3_odii_uploaded_task_id'])
                    if has_image and has_protocol:
                        t = 60012
                    elif has_image:
                        t = 60014
                    elif has_protocol:
                        t = 60018
                else:
                    print(add_task_result_resp)  # noqa: T001
                    if has_image and has_protocol:
                        t = 60013
                    elif has_image:
                        t = 60015
                    elif has_protocol:
                        t = 60019
                    print('send_task_result: FAIL')  # noqa: T001
                slog.Log.log(key=self.pk, type=t, body=add_task_result_resp)
            except Exception as e:
                logger.error(e)

    @staticmethod
    def gen_napravleniye(
        client_id: int,
        doc: DoctorProfile,
        istochnik_f: IstochnikiFinansirovaniya,
        diagnos: str,
        historynum: str,
        doc_current: DoctorProfile,
        ofname_id: Union[int, None],
        ofname: DoctorProfile,
        issledovaniya: Union[list, None] = None,
        save: bool = True,
        for_rmis: bool = False,
        rmis_data: Union[dict, None] = None,
        parent_id=None,
        parent_auto_gen_id=None,
        parent_slave_hosp_id=None,
        parent_case_id=None,
        rmis_slot=None,
        direction_purpose="NONE",
        external_organization="NONE",
        price_category=-1,
        hospital=-1,
        external_order=None,
        price_name_id=None,
        slot_fact_id=None,
        id_in_hospital=None,
    ) -> 'Napravleniya':
        """
        Генерация направления
        :param client_id:
        :param doc:
        :param istochnik_f:
        :param diagnos:
        :param historynum:
        :param doc_current:
        :param ofname_id:
        :param ofname:
        :param issledovaniya:
        :param save:
        :param for_rmis:
        :param rmis_data:
        :param parent_id:
        :param parent_auto_gen_id:
        :return: Созданное направление
        """
        if rmis_data is None:
            rmis_data = {}
        if issledovaniya is None:
            pass
        client = Clients.Card.objects.get(pk=client_id)
        if price_name_id is None and istochnik_f and istochnik_f.title.lower() in ["договор"]:
            current_hospital = doc.hospital_id
            if hospital:
                current_hospital = hospital
            price_name_obj = contracts.PriceName.get_hospital_price_by_date(current_hospital, current_time(only_date=True), current_time(only_date=True), True)
            price_name_id = price_name_obj.pk

        dir = Napravleniya(
            client=client,
            doc=doc if not for_rmis else None,
            istochnik_f=istochnik_f,
            data_sozdaniya=timezone.now(),
            diagnos=diagnos,
            cancel=False,
            parent_id=parent_id,
            parent_auto_gen_id=parent_auto_gen_id,
            parent_slave_hosp_id=parent_slave_hosp_id,
            parent_case_id=parent_case_id,
            rmis_slot_id=rmis_slot,
            hospital=doc.hospital or Hospitals.get_default_hospital(),
            external_order=external_order,
            price_name_id=price_name_id,
            id_in_hospital=id_in_hospital,
        )
        dir.additional_num = client.number_poliklinika
        dir.harmful_factor = dir.client.harmful_factor
        dir.workplace = client.work_place_db.title if client.work_place_db else client.work_place
        if for_rmis:
            dir.rmis_number = rmis_data.get("rmis_number")
            dir.imported_from_rmis = True
            dir.imported_org = RMISOrgs.objects.filter(rmis_id=rmis_data.get("imported_org", -1)).first()
            dir.doc = None
            dir.doc_who_create = doc_current
        else:
            if historynum != "":
                dir.history_num = historynum
            if ofname_id > -1 and ofname:
                dir.doc = ofname
                dir.doc_who_create = doc_current
        if direction_purpose != "NONE":
            dir.purpose = direction_purpose
        if external_organization != "NONE":
            dir.external_organization_id = int(external_organization)
        if price_category is not None and price_category > -1:
            dir.price_category_id = price_category
        if hospital > 0:
            dir.hospital_id = hospital
            dir.is_external = True
        if save:
            dir.save()
        dir.set_polis()
        if slot_fact_id:
            from doctor_schedule.models import SlotFact

            f = SlotFact.objects.get(pk=slot_fact_id)
            f.direction = dir
            f.save(update_fields=['direction'])
        return dir

    @staticmethod
    def set_of_name(dir: 'Napravleniya', doc_current: DoctorProfile, ofname_id: int, ofname: DoctorProfile):
        """
        Проверка на выписывание направления от имени другого врача и установка этого имени в направление, если необходимо
        :rtype: Null
        :param dir: направление
        :param doc_current: текущий врач, выписавший направление
        :param ofname_id: id врача, от которого выписывается направление
        :param ofname: объект с профилем врача, от которого выписывается направление
        :return: Null
        """
        if ofname_id > -1 and ofname:
            dir.doc = ofname
            dir.doc_who_create = doc_current
            dir.save()

    @staticmethod
    def check_and_change_special_field(res_data, global_data):
        laboratory_previous_results, diagnostic_previous_results, doc_referral_previous_results = None, None, None
        if global_data.get('groups', None):
            groups_data = global_data.get('groups')
            for i in groups_data:
                if i.get('fields', None):
                    fields = i.get('fields', None)
                    for f in fields:
                        status = False
                        if f.get('field_type', None):
                            if f['field_type'] == 24:
                                laboratory_previous_results = f.get('value', None)
                                status = True
                            elif f['field_type'] == 25:
                                diagnostic_previous_results = f.get('value', None)
                                status = True
                            elif f['field_type'] == 26:
                                doc_referral_previous_results = f.get('value', None)
                                status = True
                        if not status:
                            res_data['groups'][0]['fields'].append(f)

        groups_data = res_data.get('groups')
        for i in groups_data:
            if i.get('fields', None):
                fields = i.get('fields', None)
                for f in fields:
                    if f.get('field_type', None):
                        if f['field_type'] == 24:
                            f['value'] = laboratory_previous_results
                        elif f['field_type'] == 25:
                            f['value'] = diagnostic_previous_results
                        elif f['field_type'] == 26:
                            f['value'] = doc_referral_previous_results

        return res_data

    @staticmethod
    def monitoring_is_created_later(
        research,
        type_period,
        period_param_hour,
        period_param_day,
        week_date_start_end,
        period_param_month,
        period_param_quarter,
        period_param_halfyear,
        period_param_year,
        current_hospital,
    ):
        monitoring_exists = None
        if type_period == 'PERIOD_HOUR':
            monitoring_exists = MonitoringResult.objects.filter(
                research=research,
                hospital=current_hospital,
                type_period=type_period,
                period_param_hour=period_param_hour,
                period_param_day=period_param_day,
                period_param_month=period_param_month,
                period_param_year=period_param_year,
            ).first()
        elif type_period == 'PERIOD_DAY':
            monitoring_exists = MonitoringResult.objects.filter(
                research=research,
                hospital=current_hospital,
                type_period=type_period,
                period_param_day=period_param_day,
                period_param_month=period_param_month,
                period_param_year=period_param_year,
            ).first()
        elif type_period == 'PERIOD_WEEK':
            monitoring_exists = MonitoringResult.objects.filter(
                research=research,
                hospital=current_hospital,
                type_period=type_period,
                period_param_week_description=week_date_start_end[0],
                period_param_week_date_start=week_date_start_end[1],
                period_param_week_date_end=week_date_start_end[2],
                period_param_year=period_param_year,
            ).first()
        elif type_period == 'PERIOD_MONTH':
            monitoring_exists = MonitoringResult.objects.filter(
                research=research, hospital=current_hospital, type_period=type_period, period_param_month=period_param_month, period_param_year=period_param_year
            ).first()
        elif type_period == 'PERIOD_QURTER':
            monitoring_exists = MonitoringResult.objects.filter(
                research=research, hospital=current_hospital, period_param_quarter=period_param_quarter, period_param_year=period_param_year
            ).first()
        elif type_period == 'PERIOD_HALFYEAR':
            monitoring_exists = MonitoringResult.objects.filter(
                research=research, hospital=current_hospital, period_param_halfyear=period_param_halfyear, period_param_year=period_param_year
            ).first()
        elif type_period == 'PERIOD_YEAR':
            monitoring_exists = MonitoringResult.objects.filter(research=research, hospital=current_hospital, period_param_year=period_param_year).first()
        return monitoring_exists

    @staticmethod
    def monitoring_week_correct(period_param_week_day_start, period_param_week_date_start):
        week_days = {"Понедельник": 0, "Вторник": 1, "Среда": 2, "Четверг": 3, "Пятница": 4, "Суббота": 5, "Воскресенье": 6}
        short_week_days = {0: "пн", 1: "вт", 2: "ср", 3: "чт", 4: "пт", 5: "сб", 6: "вc"}
        start_day = datetime.datetime.strptime(period_param_week_date_start, '%Y-%m-%d').date()
        if week_days.get(period_param_week_day_start) != start_day.weekday():
            return False
        else:
            end_date = start_day + relativedelta(days=+6)
            return (f"{short_week_days[start_day.weekday()]}-{short_week_days[end_date.weekday()]}", start_day, end_date)

    @staticmethod
    def gen_napravleniya_by_issledovaniya(
        client_id,
        diagnos,
        finsource,
        history_num,
        ofname_id,
        doc_current,
        researches,
        comments,
        for_rmis=None,
        rmis_data=None,
        vich_code='',
        count=1,
        discount=0,
        parent_iss=None,
        parent_slave_hosp=None,
        rmis_slot=None,
        counts=None,
        localizations=None,
        service_locations=None,
        visited=None,
        parent_auto_gen=None,
        direction_purpose="NONE",
        external_organization="NONE",
        direction_form_params=None,
        current_global_direction_params=None,
        hospital_department_override=-1,
        hospital_override=-1,
        price_category=-1,
        external_order: Optional[RegisteredOrders] = None,
        services_by_additional_order_num=None,
        price_name=None,
        case_id=-2,
        case_by_direction=False,
        plan_start_date=None,
        slot_fact_id=None,
        id_in_hospital=None,
    ):
        result = {"r": False, "list_id": [], "list_stationar_id": [], "messageLimit": ""}
        if case_id > -1 and case_by_direction:
            iss = Napravleniya.objects.get(pk=case_id).issledovaniya_set.all().first()
            if iss:
                case_id = iss.pk
            else:
                result["message"] = "Ошибка привязки к случаю"
                return result
        if not Clients.Card.objects.filter(pk=client_id).exists():
            result["message"] = "Карта в базе не зарегистрирована, попробуйте выполнить поиск заново"
            return result
        pk_reseerches = []
        issledovaniye_case_id = None
        for v in researches.values():
            pk_reseerches.extend(v)
        card = Clients.Card.objects.get(pk=client_id)
        control_anketa_dispanserization = SettingManager.get("control_anketa_dispanserization", default='false', default_type='b')

        if (finsource and isinstance(finsource, str) and not finsource.isdigit()) or not finsource:
            f_obj: Optional[IstochnikiFinansirovaniya] = (
                IstochnikiFinansirovaniya.objects.filter(base=card.base, title="ОМС", hide=False).first()
                or IstochnikiFinansirovaniya.objects.filter(base=card.base, hide=False).order_by('-order_weight').first()
            )
            if not f_obj:
                finsource = None
            else:
                finsource = f_obj.pk
        finsource = IstochnikiFinansirovaniya.objects.filter(pk=finsource).first()

        if not doc_current.not_control_anketa:
            if control_anketa_dispanserization and finsource and "омс" in finsource.title.lower() and doc_current.pk not in EXCLUDE_DOCTOR_PROFILE_PKS_ANKETA_NEED:
                d1, d2 = start_end_year()
                disp_data = dispensarization_research(card.individual.sex, card.individual.age_for_year(), card.pk, d1, d2)
                if len(disp_data) > 0:
                    dispanserization_service = DISPANSERIZATION_SERVICE_PK.get("pkServiceStart", [])
                    direction_is_anketa = False
                    for d_pk in dispanserization_service:
                        if d_pk == pk_reseerches[0]:
                            direction_is_anketa = True
                    if (
                        not Issledovaniya.objects.filter(time_confirmation__range=(d1, d2), research_id__in=dispanserization_service, napravleniye__client=card).exists()
                        and not direction_is_anketa
                    ):
                        result["message"] = "Диспансеризация не начата (АНКЕТА не заполнена)"
                        return result

        limit_researches_by_period = None
        month_reserches_limit_data, day_reserches_limit_data = None, None
        if doc_current.district_group and doc_current.district_group.pk:
            limit_researches = check_limit_assign_researches(doc_current.district_group.pk)
            limit_researches_by_period = {i.research_id: {"count": i.limit_count, "period": i.type_period_limit} for i in limit_researches}
            doctors_pks = tuple(DoctorProfile.objects.values_list('pk', flat=True).filter(district_group=doc_current.district_group))

            daysnmonth = calendar.monthrange(int(current_year()), int(current_month()))[1]

            start_date = f"{current_year()}-{current_month()}-01 00:00:00"
            end_date = f"{current_year()}-{current_month()}-{daysnmonth} 23:59:59"
            month_reserches_limit = get_count_researches_by_doc(doctors_pks, start_date, end_date)
            month_reserches_limit_data = {i.research_id: i.count for i in month_reserches_limit}

            day = normalize_dots_date(strdate(current_time(only_date=True)))
            day_reserches_limit = get_count_researches_by_doc(doctors_pks, f"{day} 00:00:00", f"{day} 23:59:59")
            day_reserches_limit_data = {i.research_id: i.count for i in day_reserches_limit}

        if not visited:
            visited = []
        if counts is None:
            counts = {}

        if localizations is None:
            localizations = {}

        if service_locations is None:
            service_locations = {}

        if rmis_data is None:
            rmis_data = {}
        current_hospital = doc_current.hospital or Hospitals.get_default_hospital()

        childrens = {}
        researches_grouped_by_lab = []  # Лист с выбранными исследованиями по лабораториям
        lab_podrazdeleniye_pk = list(Podrazdeleniya.objects.values_list('pk', flat=True).filter(p_type=2))
        if current_global_direction_params and not current_global_direction_params.get("title", False):
            current_global_direction_params = None

        i = 0

        ofname_id = ofname_id or -1
        ofname = None
        auto_print_direction_research = []
        control_actual_research_period = SettingManager.get("control_actual_research_period", default='false', default_type='b')
        doctor_control_actual_research = False
        if client_id and researches:  # если client_id получен и исследования получены
            if ofname_id > -1:
                ofname = umodels.DoctorProfile.objects.get(pk=ofname_id)
            if control_actual_research_period and not doc_current.has_group("Безлимитное назначение услуг"):
                doctor_control_actual_research = True

            no_attach = False
            conflict_list = []
            conflict_keys = []
            limit_research_to_assign = {}
            for v in researches:  # нормализация исследований
                researches_grouped_by_lab.append({v: researches[v]})
                for vv in researches[v]:
                    research_tmp = directory.Researches.objects.get(pk=vv)
                    if finsource and finsource.title.lower() != "платно" and limit_researches_by_period and limit_researches_by_period.get(vv, None):
                        template_research_assign = limit_researches_by_period.get(vv)
                        if template_research_assign["period"] == 1:
                            if month_reserches_limit_data.get(vv, None) and month_reserches_limit_data[vv] >= template_research_assign["count"]:
                                limit_research_to_assign[vv] = f'{research_tmp.title}-Не более {template_research_assign["count"]} в месяц'
                        if template_research_assign["period"] == 0:
                            if day_reserches_limit_data.get(vv, None) and day_reserches_limit_data[vv] >= template_research_assign["count"]:
                                limit_research_to_assign[vv] = f'{research_tmp.title}- Не более {template_research_assign["count"]} в день'

                    if vv == PERINATAL_DEATH_RESEARCH_PK:
                        client_days_age = card.individual.age(days_monthes_years=True)
                        if client_days_age[0] > 11 and client_days_age[1] == 0 and client_days_age[2] == 0 or client_days_age[1] > 0 or client_days_age[2] > 0:
                            result["message"] = "Св-во о перинатальной смерти оформляется до 7 дней"
                            return result

                    if research_tmp.no_attach and research_tmp.no_attach > 0:
                        if research_tmp.no_attach not in conflict_keys:
                            conflict_keys.append(research_tmp.no_attach)
                            if not no_attach:
                                conflict_list = [research_tmp.title]
                        else:
                            no_attach = True
                            conflict_list.append(research_tmp.title)
                i += 1
            res = []
            only_lab_researches = []
            dir_group_onlylab = ''
            for v in researches_grouped_by_lab:  # цикл перевода листа в словарь
                for key in v.keys():
                    res += v[key]
                    if int(key) in lab_podrazdeleniye_pk:
                        only_lab_researches += v[key]
                    # {5:[0,2,5,7],6:[8]}
            if only_lab_researches or external_organization != "NONE":
                dir_group_onlylab = -9999999
            if not no_attach:
                directions_for_researches = {}  # Словарь для временной записи направлений.
                # Исследования привязываются к направлению по группе

                # получить прайс
                work_place_link = card.work_place_db
                price_obj = IstochnikiFinansirovaniya.get_price_modifier(finsource, work_place_link)
                if AUTO_PRINT_RESEARCH_DIRECTION:
                    auto_print_direction_research = AUTO_PRINT_RESEARCH_DIRECTION.get("researches")
                    repeat_research = list(set(res) & set(auto_print_direction_research))
                    auto_print_direction_research = list(set(auto_print_direction_research) - set(repeat_research))
                for v in res:
                    research = directory.Researches.objects.get(pk=v)
                    research_coast = None
                    filter = {
                        "napravleniye__client__id": client_id,
                        "research__pk": v,
                    }
                    last_iss = Issledovaniya.objects.filter(**filter, time_confirmation__isnull=False).order_by("-time_confirmation").first()
                    if doctor_control_actual_research and research.actual_period_result > 0 and last_iss:
                        delta = current_time() - last_iss.time_confirmation
                        if delta.days <= research.actual_period_result:
                            result["messageLimit"] = f" {result.get('messageLimit', '')} \n Срок действия {research.title} - {research.actual_period_result} дн."
                            continue
                    if hospital_department_override == -1 and research.is_hospital:
                        if research.podrazdeleniye is None:
                            result["message"] = "Не указано отделение"
                            return result
                    # пользователю добавлять данные услуги в направления(не будут добавлены)
                    if research in doc_current.restricted_to_direct.all():
                        continue
                    if limit_research_to_assign.get(v):
                        result["messageLimit"] = f"{result.get('messageLimit', '')} \n {limit_research_to_assign[v]}"
                        continue

                    if external_order:
                        dir_group = external_order.order_number
                        research_data_params = None
                    else:
                        dir_group = -1
                        if research.direction and external_organization == "NONE":
                            dir_group = research.direction_id

                        if v in only_lab_researches and external_organization != "NONE":
                            dir_group = dir_group_onlylab

                        if research.plan_external_performing_organization:
                            dir_group = research.plan_external_performing_organization_id + 900000

                        research_data_params = direction_form_params.get(str(v), None) if direction_form_params else None
                        if research_data_params:
                            dir_group = -1
                    period_param_hour, period_param_day, period_param_month = None, None, None
                    period_param_quarter, period_param_halfyear, period_param_year, type_period = None, None, None, None
                    period_param_week_date_start, period_param_week_day_start, week_date_start_end = None, None, None
                    if research.is_monitoring:
                        for i in research_data_params['groups'][0]['fields']:
                            if i['title'] == "Час":
                                period_param_hour = i['value']
                            if i['title'] == "День":
                                date = i['value'].split('-')
                                period_param_day = date[2]
                                period_param_month = date[1]
                                period_param_year = date[0]
                            if i['title'] == "С":
                                period_param_week_day_start = i['value']
                            if i['title'] == "Дата отсчета":
                                period_param_week_date_start = i['value']
                            if i['title'] == "Месяц":
                                period_param_month = i['value']
                            if i['title'] == "Квартал":
                                period_param_quarter = i['value']
                            if i['title'] == "Полугодие":
                                period_param_halfyear = i['value']
                            if i['title'] == "Год":
                                period_param_year = i['value']
                        type_period = research.type_period

                        if type_period == "PERIOD_WEEK":
                            week_date_start_end = Napravleniya.monitoring_week_correct(period_param_week_day_start, period_param_week_date_start)
                            if not week_date_start_end:
                                result["message"] = "Ошибка в параметрах недели"
                                return result

                        if Napravleniya.monitoring_is_created_later(
                            research,
                            type_period,
                            period_param_hour,
                            period_param_day,
                            week_date_start_end,
                            period_param_month,
                            period_param_quarter,
                            period_param_halfyear,
                            period_param_year,
                            current_hospital,
                        ):
                            result["message"] = "Данный мониторинг уже создан"
                            return result

                    if case_id > -2:
                        if case_id == -1:
                            napravleniye_case = Napravleniya.gen_napravleniye(
                                client_id,
                                doc_current if not for_rmis else None,
                                finsource,
                                diagnos,
                                history_num,
                                doc_current,
                                ofname_id,
                                ofname,
                                for_rmis=for_rmis,
                                rmis_data=rmis_data,
                                parent_id=parent_iss,
                                parent_auto_gen_id=parent_auto_gen,
                                parent_slave_hosp_id=parent_slave_hosp,
                                rmis_slot=rmis_slot,
                                direction_purpose=direction_purpose,
                                external_organization=external_organization,
                                price_category=price_category,
                                hospital=hospital_override,
                                external_order=external_order,
                                price_name_id=price_name,
                                slot_fact_id=slot_fact_id,
                                id_in_hospital=id_in_hospital,
                            )
                            research_case = directory.Researches.objects.filter(is_case=True, hide=False).first()
                            issledovaniye_case = Issledovaniya(napravleniye=napravleniye_case, research=research_case, deferred=False)
                            issledovaniye_case.save()
                            issledovaniye_case_id = issledovaniye_case.pk
                        elif case_id > 0:
                            issledovaniye_case_id = case_id

                    if (dir_group > -1 and dir_group not in directions_for_researches.keys()) or (dir_group == dir_group_onlylab and dir_group not in directions_for_researches.keys()):
                        directions_for_researches[dir_group] = Napravleniya.gen_napravleniye(
                            client_id,
                            doc_current if not for_rmis else None,
                            finsource,
                            diagnos,
                            history_num,
                            doc_current,
                            ofname_id,
                            ofname,
                            for_rmis=for_rmis,
                            rmis_data=rmis_data,
                            parent_id=parent_iss,
                            parent_auto_gen_id=parent_auto_gen,
                            parent_slave_hosp_id=parent_slave_hosp,
                            parent_case_id=issledovaniye_case_id,
                            rmis_slot=rmis_slot,
                            direction_purpose=direction_purpose,
                            external_organization=external_organization,
                            price_category=price_category,
                            hospital=hospital_override,
                            external_order=external_order,
                            price_name_id=price_name,
                            slot_fact_id=slot_fact_id,
                            id_in_hospital=id_in_hospital,
                        )
                        npk = directions_for_researches[dir_group].pk
                        result["list_id"].append(npk)
                        if research.is_hospital:
                            result["list_stationar_id"].append(npk)
                        if current_global_direction_params:
                            DirectionParamsResult.save_direction_params(directions_for_researches[dir_group], current_global_direction_params)
                    if dir_group == -1:
                        dir_group = "id" + str(research.pk)
                        directions_for_researches[dir_group] = Napravleniya.gen_napravleniye(
                            client_id,
                            doc_current if not for_rmis else None,
                            finsource,
                            diagnos,
                            history_num,
                            doc_current,
                            ofname_id,
                            ofname,
                            for_rmis=for_rmis,
                            rmis_data=rmis_data,
                            parent_id=parent_iss,
                            parent_auto_gen_id=parent_auto_gen,
                            parent_slave_hosp_id=parent_slave_hosp,
                            parent_case_id=issledovaniye_case_id,
                            rmis_slot=rmis_slot,
                            direction_purpose=direction_purpose,
                            external_organization=external_organization,
                            price_category=price_category,
                            hospital=hospital_override,
                            external_order=external_order,
                            price_name_id=price_name,
                            slot_fact_id=slot_fact_id,
                            id_in_hospital=id_in_hospital,
                        )
                        npk = directions_for_researches[dir_group].pk
                        result["list_id"].append(npk)
                        if research.is_hospital:
                            result["list_stationar_id"].append(npk)

                        if not research_data_params and current_global_direction_params:
                            DirectionParamsResult.save_direction_params(directions_for_researches[dir_group], current_global_direction_params)

                        if research_data_params and not current_global_direction_params:
                            DirectionParamsResult.save_direction_params(directions_for_researches[dir_group], research_data_params)
                            research_data_params = None

                        if research_data_params and current_global_direction_params:
                            all_params_result = Napravleniya.check_and_change_special_field(research_data_params, current_global_direction_params)
                            DirectionParamsResult.save_direction_params(directions_for_researches[dir_group], all_params_result)

                    # получить по прайсу и услуге: текущую цену
                    research_coast = contracts.PriceCoast.get_coast_from_price(research.pk, price_obj)

                    discount_end = discount
                    if research.prior_discount:
                        discount_end = research.def_discount

                    research_discount = discount_end * -1
                    research_howmany = int(counts.get(str(research.pk), 1))

                    if research_howmany == 1:
                        research_howmany = count
                    ext_additional_num = None
                    if services_by_additional_order_num:
                        external_additional_order_number = services_by_additional_order_num[research.pk]
                        ext_additional_num = ExternalAdditionalOrder.objects.filter(external_add_order=external_additional_order_number).first()
                        if not ext_additional_num:
                            ext_additional_num = ExternalAdditionalOrder.objects.create(external_add_order=external_additional_order_number)
                            ext_additional_num.save()

                    issledovaniye = Issledovaniya(
                        napravleniye=directions_for_researches[dir_group],
                        research=research,
                        coast=research_coast,
                        discount=research_discount,
                        how_many=research_howmany,
                        deferred=False,
                        external_add_order=ext_additional_num,
                    )

                    if not directions_for_researches[dir_group].need_order_redirection and research.plan_external_performing_organization:
                        directions_for_researches[dir_group].need_order_redirection = True
                        directions_for_researches[dir_group].external_executor_hospital = research.plan_external_performing_organization
                        directions_for_researches[dir_group].save(update_fields=["need_order_redirection", "external_executor_hospital"])
                    elif not directions_for_researches[dir_group].need_order_redirection and NEED_ORDER_DIRECTION_FOR_DEFAULT_HOSPITAL:
                        directions_for_researches[dir_group].need_order_redirection = True
                        directions_for_researches[dir_group].external_executor_hospital = Hospitals.objects.filter(is_default=True).first()
                        directions_for_researches[dir_group].save(update_fields=["need_order_redirection", "external_executor_hospital"])

                    loc = ""
                    if str(research.pk) in localizations:
                        localization = directory.Localization.objects.get(pk=localizations[str(research.pk)]["code"])
                        issledovaniye.localization = localization
                        loc = localization.barcode
                    if str(research.pk) in service_locations and service_locations[str(research.pk)]:
                        s = directory.ServiceLocation.objects.get(pk=service_locations[str(research.pk)]["code"])
                        issledovaniye.service_location = s
                    issledovaniye.comment = loc or (comments.get(str(research.pk), "") or "")[:40]
                    if hospital_department_override != -1 and research.is_hospital and Podrazdeleniya.objects.filter(pk=hospital_department_override).exists():
                        issledovaniye.hospital_department_override_id = hospital_department_override
                    elif hospital_department_override == -1 and research.is_hospital and Podrazdeleniya.objects.filter(pk=research.podrazdeleniye.pk).exists():
                        issledovaniye.hospital_department_override_id = research.podrazdeleniye.pk
                    issledovaniye.save()

                    if research.is_monitoring:
                        monitoring = MonitoringResult(napravleniye=directions_for_researches[dir_group], research=research, issledovaniye=issledovaniye)
                        monitoring.type_period = research.type_period
                        monitoring.hospital = current_hospital
                        monitoring.period_param_hour = period_param_hour
                        monitoring.period_param_day = period_param_day
                        if type_period == 'PERIOD_WEEK':
                            monitoring.period_param_week_description = week_date_start_end[0]
                            monitoring.period_param_week_date_start = week_date_start_end[1]
                            monitoring.period_param_week_date_end = week_date_start_end[2]
                            period_param_year = period_param_week_date_start.split('-')[0]
                            monitoring.period_date = week_date_start_end[1]
                        monitoring.period_param_month = period_param_month
                        monitoring.period_param_quarter = period_param_quarter
                        monitoring.period_param_halfyear = period_param_halfyear
                        monitoring.period_param_year = period_param_year
                        monitoring.type_period = research.type_period

                        if type_period == "PERIOD_HOUR" or type_period == "PERIOD_DAY":
                            monitoring.period_date = datetime.date(int(period_param_year), int(period_param_month), int(period_param_day))
                        if type_period == "PERIOD_MONTH":
                            last_day_month = calendar.monthrange(int(period_param_year), int(period_param_month))[1]
                            monitoring.period_date = datetime.date(int(period_param_year), int(period_param_month), int(last_day_month))
                        monitoring.save()

                    if issledovaniye.pk not in childrens:
                        childrens[issledovaniye.pk] = {}

                    for raa in research.auto_add_hidden.all():
                        if raa.pk in visited:
                            continue
                        visited.append(raa.pk)
                        if raa.reversed_type not in childrens[issledovaniye.pk]:
                            childrens[issledovaniye.pk][raa.reversed_type] = []
                        childrens[issledovaniye.pk][raa.reversed_type].append(raa.pk)

                    FrequencyOfUseResearches.inc(research, doc_current)

                tube: Optional[TubesRegistration] = None

                if external_order:
                    research = directory.Researches.objects.get(pk=res[0])
                    tube = TubesRegistration.make_external_tube(external_order.order_number, research)

                v: Napravleniya
                for k, v in directions_for_researches.items():
                    if Issledovaniya.objects.filter(napravleniye=v, research__need_vich_code=True).exists():
                        v.vich_code = vich_code
                        v.save()

                    if tube:
                        for iss in Issledovaniya.objects.filter(napravleniye=v):
                            iss.tubes.add(tube)

                result["r"] = True
                slog.Log(
                    key=json.dumps(result["list_id"]),
                    user=doc_current,
                    type=21,
                    body=json.dumps(
                        {
                            "researches": researches,
                            "client_num": card.number,
                            "client_id": client_id,
                            "diagnos": diagnos,
                            "finsource": "" if not finsource else finsource.title + " " + finsource.base.title,
                            "history_num": history_num,
                            "ofname": str(ofname),
                            "for_rmis": for_rmis,
                            "rmis_data": rmis_data,
                            "comments": comments,
                            "count": count,
                            "discount": discount,
                            "external_order": external_order.order_number if external_order else None,
                        }
                    ),
                ).save()

            else:
                result["r"] = False
                result["message"] = "Следующие исследования не могут быть назначены вместе: " + ", ".join(conflict_list)
        for iss_parent_pk in childrens:
            if not childrens[iss_parent_pk]:
                continue
            res_children = Napravleniya.gen_napravleniya_by_issledovaniya(
                client_id,
                diagnos,
                finsource.pk if finsource else None,
                history_num,
                ofname_id,
                doc_current,
                childrens[iss_parent_pk],
                comments,
                for_rmis=for_rmis,
                rmis_data=rmis_data,
                vich_code=vich_code,
                count=count,
                discount=discount,
                parent_iss=iss_parent_pk,
                rmis_slot=rmis_slot,
                counts=counts,
                localizations=localizations,
                service_locations=service_locations,
                visited=visited,
            )
            if not res_children["r"]:
                return res_children
            result['list_id'].extend(res_children['list_id'])
        if finsource and finsource.title.lower() == "платно":
            from forms.forms_func import create_contract

            sorted_direction = sort_direction_by_file_name_contract(tuple(result['list_id']), '1')
            result_sorted = {}
            for i in sorted_direction:
                if not result_sorted.get(i.file_name_contract):
                    result_sorted[i.file_name_contract] = [i.napravleniye_id]
                else:
                    result_sorted[i.file_name_contract].append(i.napravleniye_id)
            for k, v in result_sorted.items():
                create_contract(v, client_id)
        if auto_print_direction_research:
            month_ago = AUTO_PRINT_RESEARCH_DIRECTION.get("month_ago")
            check_result = check_confirm_patient_research(client_id, tuple(auto_print_direction_research), month_ago)
            check_result = [ch.research_id for ch in check_result]
            check_result_research = list(set(auto_print_direction_research) - set(check_result))
            check_direction = check_create_direction_patient_by_research(client_id, tuple(check_result_research), month_ago)
            for ch_dir in check_direction:
                check_result_research.remove(ch_dir.research_id)
                result["list_id"].append(ch_dir.direction_id)
            for research_dir in check_result_research:
                new_direction = Napravleniya.gen_napravleniye(
                    client_id,
                    doc_current if not for_rmis else None,
                    finsource,
                    diagnos,
                    history_num,
                    doc_current,
                    ofname_id,
                    ofname,
                    for_rmis=for_rmis,
                    rmis_data=rmis_data,
                    parent_id=parent_iss,
                    parent_auto_gen_id=parent_auto_gen,
                    parent_slave_hosp_id=parent_slave_hosp,
                    rmis_slot=rmis_slot,
                    direction_purpose=direction_purpose,
                    external_organization=external_organization,
                    price_category=price_category,
                    hospital=hospital_override,
                    slot_fact_id=slot_fact_id,
                    id_in_hospital=id_in_hospital,
                )
                result["list_id"].append(new_direction.pk)
                Issledovaniya(napravleniye=new_direction, research_id=research_dir, deferred=False).save()

        return result

    def has_save(self):
        """
        Есть ли подтверждение у одного или более исследований в направлении
        :return: True, если есть подтверждение у одного или более
        """
        return any([x.time_save is not None for x in Issledovaniya.objects.filter(napravleniye=self)])

    def has_confirm(self):
        """
        Есть ли подтверждение у одного или более исследований в направлении
        :return: True, если есть подтверждение у одного или более
        """
        return any([x.time_confirmation is not None for x in Issledovaniya.objects.filter(napravleniye=self)])

    def is_all_confirm(self):
        """
        Есть ли подтверждение у всех исследований в направлении
        :return: True, если всё подтверждено
        """
        return all([x.time_confirmation is not None for x in Issledovaniya.objects.filter(napravleniye=self)])

    def post_confirmation(self):
        if SettingManager.l2("send_patients_email_results") and self.is_all_confirm() and self.client.send_to_email and self.client.email:
            rt = SettingManager.get("lab_reset_confirm_time_min") * 60 + 1
            task_id = str(uuid.uuid4())
            send_result.apply_async(args=(self.pk,), countdown=rt, task_id=task_id)
            self.celery_send_task_ids = (self.celery_send_task_ids or []) + [task_id]
            self.save(update_fields=['celery_send_task_ids'])
            slog.Log.log(key=self.pk, type=180000, body={"task_id": task_id})

        if self.external_order:
            totally_confirmed_all_directions_in_order = True

            for direction in Napravleniya.objects.filter(external_order=self.external_order).exclude(pk=self.pk):
                if not direction.is_all_confirm():
                    totally_confirmed_all_directions_in_order = False
                    break

            if self.external_order.totally_completed != totally_confirmed_all_directions_in_order:
                self.external_order.totally_completed = totally_confirmed_all_directions_in_order
                self.external_order.save()

        from results_feed.models import ResultFeed

        ResultFeed.insert_feed_by_direction(self)

    def post_reset_confirmation(self):
        if self.celery_send_task_ids:
            task_ids = self.celery_send_task_ids
            celeryapp.control.revoke(task_ids, terminate=True)
            self.celery_send_task_ids = []
            self.save(update_fields=['celery_send_task_ids'])
            slog.Log.log(key=self.pk, type=180003, body={"task_ids": task_ids})
        if self.external_order and self.external_order.totally_completed:
            self.external_order.totally_completed = False
            self.external_order.need_check_for_results_redirection = False
            self.external_order.save()

        from results_feed.models import ResultFeed
        ResultFeed.remove_feed_by_direction(self)

    def last_time_confirm(self):
        return Issledovaniya.objects.filter(napravleniye=self).order_by('-time_confirmation').values_list('time_confirmation', flat=True).first()

    def last_doc_confirm(self):
        iss = Issledovaniya.objects.filter(napravleniye=self).order_by('-time_confirmation').first()

        return str(iss.doc_confirmation) if iss else None

    def is_has_deff(self):
        """
        Есть ли отложенные исследования
        :return: True, если подтверждены не все и есть одно или более отложенное исследование
        """
        return not self.is_all_confirm() and any([x.deferred for x in Issledovaniya.objects.filter(napravleniye=self)])

    def research(self):
        if Issledovaniya.objects.filter(napravleniye=self).exists():
            return Issledovaniya.objects.filter(napravleniye=self)[0].research
        return None

    def department(self):
        research = self.research()
        if research:
            return research.podrazdeleniye
        return None

    def rmis_direction_type(self) -> str:
        dep = self.department()
        if dep:
            return dep.rmis_direction_type
        from rmis_integration.client import Settings

        research: directory.Researches = self.research()
        if research:
            k = None
            if research.is_doc_refferal:
                k = Settings.get("dtype_is_doc_refferal", default="Направление на консультацию")
            elif research.is_paraclinic:
                k = Settings.get("dtype_is_paraclinic", default="Направление на инструментальную диагностику")
            if k:
                return k

        return Settings.get("direction_type_title", default="Направление в лабораторию")

    def rmis_department_title(self) -> str:
        if self.is_external:
            return "КДЛ"
        dep = self.department()
        if dep:
            return dep.rmis_department_title
        from rmis_integration.client import Settings

        return Settings.get("depname")

    def rmis_referral_title(self) -> str:
        if self.is_external:
            return "КДЛ"
        return None if not self.doc.podrazdeleniye else self.doc.podrazdeleniye.rmis_department_title

    def get_attr(self):
        napr_data = {}
        ind_data = self.client.get_data_individual()
        napr_data['client_fio'] = ind_data['fio']
        napr_data['client_bd'] = ind_data['born']
        napr_data['card_num'] = ind_data['card_num']
        napr_data['number_poliklinika'] = ind_data['number_poliklinika']
        napr_data['polis_n'] = self.polis_n if self.polis_n else ''
        napr_data['polis_who_give'] = self.polis_who_give if self.polis_who_give else ''
        napr_data['istochnik_f'] = self.fin_title.lower()

        return napr_data

    @property
    def amd_status(self):
        if self.is_all_confirm():
            has_amd = SettingManager.l2_modules().get("l2_amd", False)

            if has_amd:
                if self.need_resend_amd:
                    return "planned"
                elif self.amd_excluded:
                    return "excluded"
                if self.error_amd:
                    return "error"
                elif self.amd_number:
                    return "ok"
                else:
                    return "need"
        return "not_need"

    class Meta:
        verbose_name = 'Направление'
        verbose_name_plural = 'Направления'


class AdditionNapravleniya(models.Model):
    """
    Направления для добавления исполнителем услуги
    """

    target_direction = models.ForeignKey(Napravleniya, related_name='main_of_doctor', null=True, help_text='Направление врача', db_index=True, on_delete=models.CASCADE)
    addition_direction = models.ForeignKey(Napravleniya, related_name='additional_direction', null=True, help_text='Направление от исполнителя', db_index=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.target_direction.pk

    class Meta:
        verbose_name = 'Направление-добавочное от исполнителя услуги'
        verbose_name_plural = 'Направления-добавочные от исполнителя услуги'


def get_direction_file_path(instance: 'DirectionDocument', filename):
    iss = Issledovaniya.objects.filter(napravleniye_id=instance.direction.pk).first()
    return os.path.join('directions', str(iss.doc_confirmation.hospital.code_tfoms), str(instance.direction.pk), filename)


class DirectionDocument(models.Model):
    PDF = 'pdf'
    CDA = 'cda'
    CPP = 'cpp'
    FILE_TYPES = (
        (PDF, PDF),
        (CDA, CDA),
        (CPP, CPP),
    )

    direction = models.ForeignKey(Napravleniya, on_delete=models.CASCADE, db_index=True, verbose_name="Направление")
    file_type = models.CharField(max_length=3, db_index=True, verbose_name="Тип файла")
    file = models.FileField(upload_to=get_direction_file_path, blank=True, null=True, default=None, verbose_name="Файл документа")
    is_archive = models.BooleanField(db_index=True, verbose_name="Архивный документ", blank=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время записи")
    last_confirmed_at = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Дата и время подтверждения протокола')

    def __str__(self) -> str:
        return f"{self.direction} — {self.file_type} – {self.last_confirmed_at}"

    class Meta:
        unique_together = ('direction', 'file_type', 'last_confirmed_at')
        verbose_name = 'Документ направления'
        verbose_name_plural = 'Документы направлений'


class SignatureCertificateDetails(models.Model):
    """
    Детали сертификата подписи
    """

    thumbprint = models.CharField(max_length=44, verbose_name='Отпечаток сертификата', db_index=True, unique=True)
    owner = models.CharField(max_length=256, verbose_name='Владелец сертификата')
    valid_from = models.DateTimeField(verbose_name='Дата и время начала действия сертификата')
    valid_to = models.DateTimeField(verbose_name='Дата и время окончания действия сертификата')
    details_original = models.TextField(verbose_name='Исходные данные владельца сертификата')

    def __str__(self) -> str:
        return f"{self.thumbprint} — {self.owner}"

    @staticmethod
    def parse_details(details: Union[dict, str]) -> Optional[dict]:
        if isinstance(details, str):
            try:
                parsed_details = json.loads(details)
                if not isinstance(parsed_details, dict):
                    parsed_details = None
            except:
                parsed_details = None
        elif isinstance(details, dict):
            parsed_details = details
        else:
            parsed_details = None

        if not parsed_details or not parsed_details.get('subjectName') or not parsed_details.get('validFrom') or not parsed_details.get('validTo'):
            return None

        try:
            sn = parsed_details["subjectName"]
            name_parts = ["", ""]
            sn = sn.split(",")
            for s in sn:
                if s.strip().startswith("SN="):
                    name_parts[0] = s.strip()[3:]
                elif s.strip().startswith("G="):
                    name_parts[1] = s.strip()[2:]
            name = " ".join(name_parts).strip()
        except:
            name = None

        try:
            valid_from = datetime.datetime.strptime(parsed_details['validFrom'], '%Y-%m-%dT%H:%M:%S.%fZ')
            valid_to = datetime.datetime.strptime(parsed_details['validTo'], '%Y-%m-%dT%H:%M:%S.%fZ')
        except:
            valid_from = None
            valid_to = None

        if not name or not valid_from or not valid_to:
            return None

        return {
            "owner": name,
            "valid_from": valid_from,
            "valid_to": valid_to,
        }

    @staticmethod
    def get_or_update(thumbprint: str, details: str) -> Optional['SignatureCertificateDetails']:
        cert_details = SignatureCertificateDetails.objects.filter(thumbprint=thumbprint).first()
        if cert_details:
            if cert_details.details_original != details:
                parsed_details = SignatureCertificateDetails.parse_details(details)
                if not parsed_details:
                    return None

                cert_details.details_original = details
                cert_details.owner = parsed_details["owner"]
                cert_details.valid_from = parsed_details["valid_from"]
                cert_details.valid_to = parsed_details["valid_to"]

                cert_details.save()
            return cert_details

        parsed_details = SignatureCertificateDetails.parse_details(details)
        if not parsed_details:
            return None

        cert_details = SignatureCertificateDetails(
            thumbprint=thumbprint,
            owner=parsed_details["owner"],
            valid_from=parsed_details["valid_from"],
            valid_to=parsed_details["valid_to"],
            details_original=details,
        )
        cert_details.save()
        return cert_details

    class Meta:
        verbose_name = 'Детали сертификата подписи'
        verbose_name_plural = 'Детали сертификатов подписи'


class DocumentSign(models.Model):
    document = models.ForeignKey(DirectionDocument, on_delete=models.CASCADE, db_index=True, verbose_name="Документ")
    executor = models.ForeignKey(DoctorProfile, db_index=True, verbose_name='Исполнитель подписи', on_delete=models.CASCADE)
    signed_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время подписи")
    sign_type = models.CharField(max_length=32, db_index=True, verbose_name='Тип подписи')
    sign_value = models.TextField(verbose_name="Значение подписи")
    sign_certificate = models.ForeignKey(SignatureCertificateDetails, on_delete=models.CASCADE, verbose_name="Сертификат подписи", blank=True, null=True, default=None)

    def __str__(self) -> str:
        return f"{self.document} — {self.sign_type} – {self.executor}"

    class Meta:
        unique_together = ('document', 'executor', 'sign_type')
        verbose_name = 'Подпись документа направления'
        verbose_name_plural = 'Подписи документов направлений'


class PersonContract(models.Model):
    """
    Каждый раз при генерации нового контракта для физлица создается просто запись
    """

    num_contract = models.CharField(max_length=25, null=False, db_index=True, help_text='Номер договора')
    protect_code = models.CharField(max_length=32, null=False, db_index=True, help_text="Контрольная сумма контракта")
    dir_list = models.CharField(max_length=512, null=False, db_index=True, help_text="Направления для контракта")
    sum_contract = models.CharField(max_length=255, null=False, db_index=True, help_text="Итоговая сумма контракта")
    patient_data = models.CharField(max_length=255, null=False, db_index=True, help_text="Фамилия инициалы Заказчика-Пациента")
    patient_card = models.ForeignKey(Clients.Card, related_name='patient_card', null=True, help_text='Карта пациента', db_index=True, on_delete=models.SET_NULL)
    payer_card = models.ForeignKey(Clients.Card, related_name='payer_card', null=True, default=None, blank=True, help_text='Карта плательщика', db_index=False, on_delete=models.SET_NULL)
    agent_card = models.ForeignKey(Clients.Card, related_name='agent_card', null=True, default=None, blank=True, help_text='Карта Представителя', db_index=False, on_delete=models.SET_NULL)
    create_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время создания")
    cancel = models.BooleanField(default=False, blank=True, help_text='Отмена контракта')

    class Meta:
        unique_together = ("num_contract", "protect_code")
        verbose_name = 'Договор физ.лица'
        verbose_name_plural = 'Договоры физ.лиц'

    @staticmethod
    def person_contract_save(n_contract, p_code, d_list, s_contract, p_data, p_card, p_payer=None, p_agent=None):
        """
        Запись в базу сведений о контракте
        """
        pers_contract = PersonContract(
            num_contract=n_contract, protect_code=p_code, dir_list=d_list, sum_contract=s_contract, patient_data=p_data, patient_card=p_card, payer_card=p_payer, agent_card=p_agent
        )
        pers_contract.save()


class ExternalAdditionalOrder(models.Model):
    external_add_order = models.CharField(max_length=255, db_index=True, blank=True, null=True, default=None, help_text='Внешний номер для услуги')

    def __str__(self):
        return f"{self.external_add_order}"

    class Meta:
        verbose_name = 'Внешний лабораторный номер заказа'
        verbose_name_plural = 'Внешние лабораторные номера заказов'


class Issledovaniya(models.Model):
    """
    Направления на исследования
    """

    napravleniye = models.ForeignKey(Napravleniya, null=True, help_text='Направление', db_index=True, on_delete=models.CASCADE)
    research = models.ForeignKey(directory.Researches, null=True, blank=True, help_text='Вид исследования из справочника', db_index=True, on_delete=models.CASCADE)
    tubes = models.ManyToManyField(TubesRegistration, help_text='Ёмкости, необходимые для исследования', db_index=True)
    doc_save = models.ForeignKey(
        DoctorProfile, null=True, blank=True, related_name="doc_save", db_index=True, help_text='Профиль пользователя, сохранившего результат', on_delete=models.SET_NULL
    )
    time_save = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время сохранения результата')
    doc_confirmation = models.ForeignKey(
        DoctorProfile, null=True, blank=True, related_name="doc_confirmation", db_index=True, help_text='Профиль автора результата', on_delete=models.SET_NULL
    )
    doc_confirmation_string = models.CharField(max_length=64, null=True, blank=True, default=None)
    time_confirmation = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время подтверждения результата')
    executor_confirmation = models.ForeignKey(
        DoctorProfile, null=True, blank=True, related_name="executor_confirmation", db_index=True, help_text='Профиль оператора, заполнившего результат', on_delete=models.SET_NULL
    )
    deferred = models.BooleanField(default=False, blank=True, help_text='Флаг, отложено ли исследование', db_index=True)
    comment = models.CharField(max_length=255, default="", blank=True, help_text='Комментарий (отображается на ёмкости)')
    lab_comment = models.TextField(default="", null=True, blank=True, help_text='Комментарий, оставленный лабораторией')
    api_app = models.ForeignKey(Application, null=True, blank=True, default=None, help_text='Приложение API, через которое результаты были сохранены', on_delete=models.SET_NULL)
    coast = models.DecimalField(max_digits=10, null=True, blank=True, default=None, decimal_places=2)
    discount = models.SmallIntegerField(default=0, help_text='Скидка назначена оператором')
    how_many = models.PositiveSmallIntegerField(default=1, help_text='Кол-во услуг назначено оператором')
    def_uet = models.DecimalField(max_digits=6, null=True, help_text="Нагрузка врача(лаборанта) подтвердившего результат", blank=True, default=None, decimal_places=3)
    co_executor = models.ForeignKey(DoctorProfile, related_name="co_executor", help_text="Со-исполнитель", default=None, null=True, blank=True, on_delete=models.SET_NULL)
    co_executor_uet = models.DecimalField(max_digits=6, null=True, blank=True, default=None, decimal_places=3)
    co_executor2 = models.ForeignKey(DoctorProfile, related_name="co_executor2", help_text="Со-исполнитель2", default=None, null=True, blank=True, on_delete=models.SET_NULL)
    co_executor2_uet = models.DecimalField(max_digits=6, null=True, blank=True, default=None, decimal_places=3)
    legal_authenticator = models.ForeignKey(
        DoctorProfile, related_name="legal_authenticator", help_text="Подпись организации", default=None, null=True, blank=True, on_delete=models.SET_NULL
    )
    purpose = models.ForeignKey(VisitPurpose, default=None, blank=True, null=True, on_delete=models.SET_NULL, help_text="Цель посещения")
    fin_source = models.ForeignKey(IstochnikiFinansirovaniya, default=None, blank=True, null=True, on_delete=models.SET_NULL, help_text="Перезаписать источник финансирования из направления")
    price_category = models.ForeignKey('contracts.PriceCategory', default=None, blank=True, null=True, help_text='Перезаписать категорию прайса из направления', on_delete=models.SET_NULL)
    first_time = models.BooleanField(default=False, help_text="Впервые")
    result_reception = models.ForeignKey(ResultOfTreatment, default=None, blank=True, null=True, on_delete=models.SET_NULL, help_text="Результат обращения")
    outcome_illness = models.ForeignKey(Outcomes, default=None, blank=True, null=True, on_delete=models.SET_NULL, help_text="Исход")
    place = models.ForeignKey(Place, default=None, blank=True, null=True, on_delete=models.SET_NULL, help_text="Условие оказание помощи")
    diagnos = models.CharField(blank=True, help_text="Заключительный Диагноз приема", default="", max_length=255)
    maybe_onco = models.BooleanField(default=False, help_text="Подозрение на онко")
    creator = models.ForeignKey(
        DoctorProfile,
        null=True,
        blank=True,
        default=None,
        related_name="doc_add_research",
        db_index=True,
        help_text='Профиль пользователя, добавившего услуги к созданному направлению',
        on_delete=models.SET_NULL,
    )
    parent = models.ForeignKey('self', related_name='parent_issledovaniye', help_text="Исследование основание", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    medical_examination = models.DateField(blank=True, null=True, default=None, help_text="Дата осмотра")
    localization = models.ForeignKey(directory.Localization, blank=True, null=True, default=None, help_text="Локализация", on_delete=models.SET_NULL)
    service_location = models.ForeignKey(directory.ServiceLocation, blank=True, null=True, default=None, help_text="Место оказания услуги", on_delete=models.SET_NULL)
    link_file = models.CharField(max_length=255, blank=True, null=True, default=None, help_text="Ссылка на файл")
    study_instance_uid = models.CharField(max_length=64, blank=True, null=True, default=None, help_text="uuid снимка - экземпляр")
    study_instance_uid_tag = models.CharField(max_length=64, blank=True, null=True, default=None, help_text="study instance_uid tag")
    acsn_id = models.CharField(max_length=55, blank=True, null=True, default=None, help_text="N3-ОДИИ уникальный идентификатор заявки")
    n3_odii_task = models.CharField(max_length=55, blank=True, null=True, default=None, help_text="N3-ОДИИ идентификатор Task заявки")
    n3_odii_service_request = models.CharField(max_length=55, blank=True, null=True, default=None, help_text="N3-ОДИИ идентификатор ServiceRequest заявки")
    n3_odii_patient = models.CharField(max_length=55, blank=True, null=True, default=None, help_text="N3-ОДИИ идентификатор пациента заявки")
    n3_odii_uploaded_task_id = models.CharField(max_length=55, blank=True, null=True, default=None, help_text="N3-ОДИИ идентификатор Task результата")
    ecp_evn_id = models.CharField(max_length=55, blank=True, null=True, default=None, help_text="ECP Evn_id")
    gen_direction_with_research_after_confirm = models.ForeignKey(
        directory.Researches, related_name='research_after_confirm', null=True, blank=True, help_text='Авто назначаемое при подтверждении', on_delete=models.SET_NULL
    )
    aggregate_lab = JSONField(null=True, blank=True, default=None, help_text='ID направлений лаборатории, привязанных к стационарному случаю')
    aggregate_desc = JSONField(null=True, blank=True, default=None, help_text='ID направлений описательных, привязанных к стационарному случаю')
    microbiology_conclusion = models.TextField(default=None, null=True, blank=True, help_text='Заключение по микробиологии')
    hospital_department_override = models.ForeignKey(Podrazdeleniya, blank=True, null=True, default=None, help_text="Отделение стационара", on_delete=models.SET_NULL)
    doc_add_additional = models.ForeignKey(
        DoctorProfile, null=True, blank=True, related_name="doc_add_additional", db_index=True, help_text='Профиль-добавил исполнитель дополнительные услуги', on_delete=models.SET_NULL
    )
    external_add_order = models.ForeignKey(ExternalAdditionalOrder, db_index=True, blank=True, null=True, default=None, help_text="Внешний заказ", on_delete=models.SET_NULL)
    plan_start_date = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Планируемое время начала услуги')
    billing = models.ForeignKey(contracts.BillingRegister, db_index=True, blank=True, null=True, default=None, help_text="Принадлежит счету", on_delete=models.SET_NULL)

    @staticmethod
    def save_billing(billing_id, iss_ids):
        iss = Issledovaniya.objects.filter(pk__in=iss_ids)
        for i in iss:
            i.billing_id = billing_id
            i.save()
        return True

    @staticmethod
    def cancel_billing(billing_id):
        iss = Issledovaniya.objects.filter(billing_id=billing_id)
        for i in iss:
            i.billing_id = None
            i.save()
        return True


    @property
    def time_save_local(self):
        return localtime(self.time_save)

    @property
    def time_confirmation_local(self):
        return localtime(self.time_confirmation)

    def get_stat_diagnosis(self):
        pass

    @property
    def hospital_department_replaced_title(self):
        if not self.research or not self.research.is_hospital:
            return None
        if self.hospital_department_override:
            return self.hospital_department_override.get_title()
        return None

    @property
    def doc_confirmation_fio(self):
        if self.doc_confirmation_string:
            return self.doc_confirmation_string
        if self.doc_confirmation:
            return self.doc_confirmation.get_fio()
        return ''

    @property
    def doc_confirmation_full_fio(self):
        if self.doc_confirmation:
            return self.doc_confirmation.get_fio()
        return ''

    @property
    def doc_position(self):
        if self.doc_confirmation:
            return self.doc_confirmation.position.title
        return ''

    def gen_after_confirm(self, user: User):
        if not self.time_confirmation or not self.gen_direction_with_research_after_confirm:
            return
        Napravleniya.gen_napravleniya_by_issledovaniya(
            self.napravleniye.client_id,
            "",
            self.napravleniye.parent.napravleniye.istochnik_f_id if self.napravleniye.parent else self.napravleniye.istochnik_f_id,
            "",
            None,
            user.doctorprofile,
            {-1: [self.gen_direction_with_research_after_confirm_id]},
            {},
            False,
            {},
            vich_code="",
            count=1,
            discount=0,
            parent_iss=self.napravleniye.parent_id or self.pk,
            parent_auto_gen=None,
        )

    def __str__(self):
        return f"{self.pk} - {self.napravleniye}"

    def is_get_material(self):
        """
        Осуществлен ли забор всего материала для исследования
        :return: True, если весь материал взят
        """
        return self.tubes.filter().exists() and all([x.doc_get is not None for x in self.tubes.filter()])

    @property
    def material_date(self):
        dt = self.time_confirmation
        if self.tubes.filter(time_get__isnull=False).exists():
            t = self.tubes.filter(time_get__isnull=False)[0]
            dt = t.time_get
        return strfdatetime(dt, '%Y-%m-%d')

    def get_visit_date(self, force=False):
        if not self.time_confirmation and not force:
            return ""
        if not self.napravleniye.visit_date or not self.napravleniye.visit_who_mark:
            self.napravleniye.visit_date = timezone.now()
            self.napravleniye.visit_who_mark = self.doc_confirmation
            self.napravleniye.save()
        return strdate(self.napravleniye.visit_date)

    def get_medical_examination(self):
        if not self.medical_examination and self.research.pk not in RESEARCHES_EXCLUDE_AUTO_MEDICAL_EXAMINATION:
            if self.napravleniye.visit_date or self.time_confirmation:
                self.medical_examination = (self.napravleniye.visit_date or self.time_confirmation).date()
            else:
                self.medical_examination = current_time(only_date=True)
            self.save(update_fields=['medical_examination'])
        return self.medical_examination

    def is_receive_material(self):
        """
        Осуществлен ли прием материала лабораторией
        :return: True, если весь материал принят
        """
        return self.is_get_material() and all([x.doc_recive is not None for x in self.tubes.filter()])

    def get_analyzer(self):
        return "" if not self.api_app else self.api_app.name

    def allow_reset_confirm(self, user: User):
        from api.stationar.stationar_func import forbidden_edit_dir

        if not self.time_confirmation:
            return False
        if user.is_superuser:
            return True
        groups = [str(x) for x in user.groups.all()]
        if self.research.can_transfer:
            return "Сброс подтверждения переводного эпикриза" in groups
        if self.research.is_extract:
            return "Сброс подтверждения выписки" in groups
        if forbidden_edit_dir(self.napravleniye_id):
            return False
        if self.napravleniye and self.napravleniye.eds_total_signed:
            return "Сброс подтверждений результатов" in groups
        ctp = int(0 if not self.time_confirmation else int(time.mktime(timezone.localtime(self.time_confirmation).timetuple())))
        ctime = int(time.time())
        current_doc_confirmation = self.doc_confirmation
        executor_confirmation = self.executor_confirmation
        rt = SettingManager.get("lab_reset_confirm_time_min") * 60
        return (
            ctime - ctp < rt and (current_doc_confirmation == user.doctorprofile or (executor_confirmation is not None and executor_confirmation == user.doctorprofile))
        ) or "Сброс подтверждений результатов" in groups

    class Meta:
        verbose_name = 'Назначение на исследование'
        verbose_name_plural = 'Назначения на исследования'


class NapravleniyaHL7LinkFiles(models.Model):
    HL7_ORIG_ORDER = 'HL7_ORIG_ORDER'
    HL7_FINISH_ORDER = 'HL7_FINISH_ORDER'
    HL7_ORIG_RESULT = 'HL7_ORIG_RESULT'
    FILE_TYPES = (
        (HL7_ORIG_ORDER, HL7_ORIG_ORDER),
        (HL7_FINISH_ORDER, HL7_FINISH_ORDER),
        (HL7_ORIG_RESULT, HL7_ORIG_RESULT),
    )

    napravleniye = models.ForeignKey(Napravleniya, on_delete=models.CASCADE, db_index=True, verbose_name="Направления")
    file_type = models.CharField(max_length=30, db_index=True, verbose_name="Тип файла")
    upload_file = models.FileField(blank=True, null=True, default=None, max_length=255, verbose_name="Файл документа")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время записи")

    def __str__(self) -> str:
        return f"{self.napravleniye} — {self.file_type} – {self.created_at}"

    def create_hl7_file_path(napravleniye_id, filename):
        if not os.path.exists(os.path.join(MEDIA_ROOT, 'hl7_files', str(napravleniye_id))):
            os.makedirs(os.path.join(MEDIA_ROOT, 'hl7_files', str(napravleniye_id)))
        return os.path.join(MEDIA_ROOT, 'hl7_files', str(napravleniye_id), filename)

    class Meta:
        verbose_name = 'HL7-файл'
        verbose_name_plural = 'HL7-файлы'


def get_file_path(instance: 'IssledovaniyaFiles', filename):
    return os.path.join('issledovaniya_files', str(instance.issledovaniye.pk), str(uuid.uuid4()), filename)


class IssledovaniyaFiles(models.Model):
    issledovaniye = models.ForeignKey(Issledovaniya, db_index=True, on_delete=models.CASCADE)
    uploaded_file = models.FileField(upload_to=get_file_path, blank=True, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    who_add_files = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="who_add_files", help_text='Создатель направления', on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Файлы на исследование'
        verbose_name_plural = 'Файлы на исследования'


class IssledovaniyaResultLaborant(models.Model):
    napravleniye = models.ForeignKey(Napravleniya, null=True, help_text='Направление', db_index=True, on_delete=models.CASCADE)
    issledovaniye = models.ForeignKey(Issledovaniya, db_index=True, help_text='Исследование, для которого сохранен результат', on_delete=models.CASCADE)
    field = models.ForeignKey(directory.ParaclinicInputField, db_index=True, help_text='Поле результата', on_delete=models.CASCADE)
    field_type = models.SmallIntegerField(default=None, blank=True, choices=directory.ParaclinicInputField.TYPES, null=True)
    value = models.TextField()
    operator_save = models.ForeignKey(DoctorProfile, null=True, blank=True, related_name="operator_save", db_index=True, help_text='оператор(лаборант) результата', on_delete=models.SET_NULL)
    time_save = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время подтверждения результата')

    @staticmethod
    def save_result_operator(iss, field, field_type, value, operator):
        if not IssledovaniyaResultLaborant.objects.filter(issledovaniye=iss, field=field).exists():
            f_result = IssledovaniyaResultLaborant(issledovaniye=iss, field=field, value="")
        else:
            f_result = IssledovaniyaResultLaborant.objects.filter(issledovaniye=iss, field=field)[0]
        f_result.value = value
        f_result.field_type = field_type
        if field_type in [27, 28, 29, 32, 33, 34, 35]:
            try:
                val = json.loads(value)
            except:
                val = {}
            f_result.value_json = val
        f_result.operator_save = operator
        f_result.napravleniye = iss.napravleniye
        f_result.time_save = timezone.now()
        f_result.save()

    class Meta:
        verbose_name = 'Лаборант-Оператор заполнил результат'
        verbose_name_plural = 'Лаборант-Оператор заполнил результаты'


class MonitoringResult(models.Model):
    PERIOD_HOUR = 'PERIOD_HOUR'
    PERIOD_DAY = 'PERIOD_DAY'
    PERIOD_WEEK = 'PERIOD_WEEK'
    PERIOD_MONTH = 'PERIOD_MONTH'
    PERIOD_QURTER = 'PERIOD_QURTER'
    PERIOD_HALFYEAR = 'PERIOD_HALFYEAR'
    PERIOD_YEAR = 'PERIOD_YEAR'

    PERIOD_TYPES = (
        (PERIOD_HOUR, 'Час'),
        (PERIOD_DAY, 'День'),
        (PERIOD_WEEK, 'Неделя'),
        (PERIOD_MONTH, 'Месяц'),
        (PERIOD_QURTER, 'Квартал'),
        (PERIOD_HALFYEAR, 'Полгода'),
        (PERIOD_YEAR, 'Год'),
    )

    napravleniye = models.ForeignKey(Napravleniya, null=True, help_text='Направление', db_index=True, on_delete=models.CASCADE)
    research = models.ForeignKey(directory.Researches, null=True, blank=True, help_text='Вид мониторинга/исследования из справочника', db_index=True, on_delete=models.CASCADE)
    issledovaniye = models.ForeignKey(Issledovaniya, db_index=True, help_text='Заказ на мониторинг, для которого сохранен результат', on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospitals, default=None, blank=True, null=True, db_index=True, on_delete=models.SET_NULL)
    group_id = models.IntegerField(default=None, blank=True, null=True, db_index=True, help_text='Группа результата')
    group_order = models.IntegerField(default=None, blank=True, null=True)
    field_id = models.IntegerField(default=None, blank=True, null=True, db_index=True, help_text='Поле результата')
    field_order = models.IntegerField(default=None, blank=True, null=True)
    field_type = models.SmallIntegerField(default=None, blank=True, choices=directory.ParaclinicInputField.TYPES, null=True)
    value_aggregate = models.DecimalField(max_digits=12, decimal_places=2, default=None, blank=True, null=True)
    value_text = models.TextField(default='', blank=True)
    type_period = models.CharField(max_length=20, db_index=True, choices=PERIOD_TYPES, help_text="Тип периода")
    period_param_hour = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    period_param_day = models.PositiveSmallIntegerField(default=None, blank=True, null=True, db_index=True)
    period_param_week_description = models.CharField(max_length=5, blank=True, null=True, default=None, help_text="Описание недельного периода")
    period_param_week_date_start = models.DateField(blank=True, null=True, default=None, help_text="Дата начала недельного периода")
    period_param_week_date_end = models.DateField(blank=True, null=True, default=None, help_text="Дата окончания недельного периода")
    period_param_month = models.PositiveSmallIntegerField(default=None, blank=True, null=True, db_index=True)
    period_param_quarter = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    period_param_halfyear = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    period_param_year = models.PositiveSmallIntegerField(default=None, blank=True, null=True, db_index=True)
    period_date = models.DateField(blank=True, null=True, default=None, help_text="Фактическая дата для периодов")

    class Meta:
        verbose_name = 'Мониторинг результаты'
        verbose_name_plural = 'Мониторинг результаты'


class MonitoringStatus(models.Model):
    STATUS_PREPARED = 'PREPARED'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'

    STATUS_TYPES = (
        (STATUS_PREPARED, 'Подготовлен'),
        (STATUS_APPROVED, 'Утвержден'),
        (STATUS_REJECTED, 'Отклонен'),
    )

    napravleniye = models.ForeignKey(Napravleniya, null=True, help_text='Направление', db_index=True, on_delete=models.CASCADE)
    type_status = models.CharField(max_length=20, db_index=True, choices=STATUS_TYPES, help_text="Cтатус мониторинга")
    time_change_status = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время изменения статуса')
    comment = models.CharField(max_length=255, default="", blank=True, help_text='Комментарий в случае отклонения')
    who_change_status = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True, help_text='Профиль пользователя изменившего статус', on_delete=models.SET_NULL)


class Dashboard(models.Model):
    title = models.CharField(max_length=255, default="", help_text='Название дашборда', db_index=True)
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие дашборда', db_index=True)
    order = models.SmallIntegerField(default=-99, blank=True, null=True)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = 'Дашборд'
        verbose_name_plural = 'Дашборды'


class DashboardCharts(models.Model):
    COLUMN = 'COLUMN'
    BAR = 'BAR'
    PIE = 'PIE'
    LINE = 'LINE'
    TABLE = 'TABLE'

    DEFAULT_TYPE = (
        (COLUMN, 'Столбцы'),
        (BAR, 'Полоса'),
        (PIE, 'Пирог-куски'),
        (LINE, 'Линейная диаграмма'),
        (TABLE, 'Таблица'),
    )

    title = models.CharField(max_length=255, default="", help_text='Название дашборда', db_index=True)
    dashboard = models.ForeignKey(Dashboard, null=True, help_text='Дашборд', db_index=True, on_delete=models.CASCADE)
    order = models.SmallIntegerField(default=-99, blank=True, null=True)
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие графика', db_index=True)
    hospitals_group = models.ForeignKey(HospitalsGroup, default=None, blank=True, null=True, db_index=True, help_text="Группа больниц", on_delete=models.CASCADE)
    is_full_width = models.BooleanField(default=False, blank=True, help_text='На всю ширину страницы')
    default_type = models.CharField(max_length=20, db_index=True, choices=DEFAULT_TYPE, default=COLUMN, help_text="Тип графика по умолчанию")

    def __str__(self):
        return f"{self.title} - Дашборд: {self.dashboard.title}"

    class Meta:
        verbose_name = 'Дашборд-Графики'
        verbose_name_plural = 'Дашборд-Графики'


class DashboardChartFields(models.Model):
    charts = models.ForeignKey(DashboardCharts, null=True, help_text='График', db_index=True, on_delete=models.CASCADE)
    field = models.ForeignKey(directory.ParaclinicInputField, null=True, help_text='Поле', db_index=True, on_delete=models.CASCADE)
    title_for_field = models.CharField(max_length=255, default="", help_text='Переопределение название поля в графике', db_index=True)
    order = models.SmallIntegerField(default=-99, blank=True, null=True)
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие поля', db_index=True)

    def __str__(self):
        return f"{self.field.title} - {self.charts.title}"

    class Meta:
        verbose_name = 'Дашборд-Поле для графика'
        verbose_name_plural = 'Дашборд-Поля для графика'


class MonitoringSumFieldByDay(models.Model):
    field = models.ForeignKey(directory.ParaclinicInputField, null=True, help_text='Поле', db_index=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default="", help_text='Заголовок данных', db_index=True)
    order = models.SmallIntegerField(default=None, blank=True, null=True)

    def __str__(self):
        return f"{self.field.title}"

    class Meta:
        verbose_name = 'Поле сумма за день'
        verbose_name_plural = 'Поля сумм за день'


class MonitoringSumFieldTotal(models.Model):
    field = models.ForeignKey(directory.ParaclinicInputField, null=True, help_text='Поле', db_index=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default="", help_text='Заголовок данных', db_index=True)
    date_start = models.DateField(blank=True, null=True, default=None, help_text="Дата начала отсчета")

    def __str__(self):
        return f"{self.field.title}"

    class Meta:
        verbose_name = 'Поле сумма за период от даты'
        verbose_name_plural = 'Поля сумм за период от даты'


class MethodsOfTaking(models.Model):
    drug_prescription = models.CharField(max_length=128, db_index=True)
    method_of_taking = models.CharField(max_length=128, db_index=True)
    count = models.IntegerField()

    @staticmethod
    def inc(dp, method):
        objs = MethodsOfTaking.objects.filter(drug_prescription=dp, method_of_taking=method)
        if not objs.exists():
            MethodsOfTaking(drug_prescription=dp, method_of_taking=method, count=1).save()
        else:
            obj = objs[0]
            obj.count += 1
            obj.save()

    @staticmethod
    def dec(dp, method):
        objs = MethodsOfTaking.objects.filter(drug_prescription=dp, method_of_taking=method)
        if objs.exists():
            obj = objs[0]
            obj.count -= 1
            obj.save()


class Recipe(models.Model):
    issledovaniye = models.ForeignKey(Issledovaniya, db_index=True, help_text='Направление на исследование, для которого сохранен рецепт', on_delete=models.CASCADE)
    drug_prescription = models.CharField(max_length=128, db_index=True)
    method_of_taking = models.CharField(max_length=128)
    comment = models.CharField(max_length=128)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class TypeJob(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    hide = models.BooleanField(help_text="Скрыть тип", default=False)
    value = models.DecimalField(max_digits=5, decimal_places=2, help_text="Ценность работы (в УЕТ или минутах-зависит от названия работы)")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Тип работы'
        verbose_name_plural = 'Типы работ'


class EmployeeJob(models.Model):
    type_job = models.ForeignKey(TypeJob, db_index=True, help_text='Тип косвенных работ', on_delete=models.CASCADE)
    count = models.SmallIntegerField(default=0, help_text="Количество данного типа", blank=True)
    doc_execute = models.ForeignKey(
        DoctorProfile, null=True, blank=True, related_name="doc_execute", db_index=True, help_text='Профиль пользователя, выполневший работы', on_delete=models.SET_NULL
    )
    date_job = models.DateField(default=date.today, help_text="Дата работ", blank=True, null=True, db_index=True)
    time_save = models.DateTimeField(default=timezone.now, null=True, blank=True, help_text='Время сохранения/корректировки')
    canceled_at = models.DateTimeField(default=None, null=True, blank=True, help_text='Время отмены')
    who_do_cancel = models.ForeignKey(
        DoctorProfile, null=True, blank=True, related_name="who_do_cancel", db_index=True, help_text='Профиль пользователя, выполневший отмену', on_delete=models.SET_NULL
    )

    @property
    def time_save_local(self):
        return localtime(self.time_save)

    class Meta:
        verbose_name = 'Нагрузка сотрудника'
        verbose_name_plural = 'Учет нагрзки'


class ParaclinicResult(models.Model):
    issledovaniye = models.ForeignKey(Issledovaniya, db_index=True, help_text='Направление на исследование, для которого сохранен результат', on_delete=models.CASCADE)
    field = models.ForeignKey(directory.ParaclinicInputField, db_index=True, help_text='Поле результата', on_delete=models.CASCADE)
    field_type = models.SmallIntegerField(default=None, blank=True, choices=directory.ParaclinicInputField.TYPES, null=True)
    value = models.TextField()
    value_json = JSONField(default=dict, blank=True)

    def get_field_type(self, default_field_type=None, is_confirmed_strict=None):
        return (
            self.field_type
            if (is_confirmed_strict is None and self.issledovaniye.time_confirmation and self.field_type) or (is_confirmed_strict and self.field_type) is not None
            else default_field_type or self.field.field_type
        )

    class JsonParser:
        PARSERS = {
            29: 'address',
            28: 'code_title',
            32: 'code_title',
            33: 'code_title',
            34: 'code_title',
            35: 'doctorprofile',
        }

        @staticmethod
        def get_value_as_json(field: Union['ParaclinicResult', 'DirectionParamsResult']):
            result = field.value_json
            if not result:
                try:
                    return json.loads(field.value)
                except:
                    pass
            return result

        @staticmethod
        def get_value_json_field(field: Union['ParaclinicResult', 'DirectionParamsResult'], prop: str, cached_json_value=None):
            json_result = cached_json_value or ParaclinicResult.JsonParser.get_value_as_json(field)
            if json_result and isinstance(json_result, dict):
                return json_result.get(prop) or ''

            return ''

        @staticmethod
        def get_value_json_fields(field: Union['ParaclinicResult', 'DirectionParamsResult'], props: List[str]):
            json_result = ParaclinicResult.JsonParser.get_value_as_json(field)
            return [ParaclinicResult.JsonParser.get_value_json_field(field, prop, cached_json_value=json_result) for prop in props]

        @staticmethod
        def from_json_to_string_value(field: Union['ParaclinicResult', 'DirectionParamsResult']):
            t = field.get_field_type()

            if t in ParaclinicResult.JsonParser.PARSERS:
                func = f"{ParaclinicResult.JsonParser.PARSERS[t]}_parser"
                if hasattr(ParaclinicResult.JsonParser, func):
                    return getattr(ParaclinicResult.JsonParser, func)(field)

            return field.value

        @staticmethod
        def from_static_json_to_string_value(value: str, t: int):
            if t in ParaclinicResult.JsonParser.PARSERS:
                func = f"{ParaclinicResult.JsonParser.PARSERS[t]}_parser"
                if hasattr(ParaclinicResult.JsonParser, func):
                    return getattr(ParaclinicResult.JsonParser, func)(ParaclinicResult(field_type=t, value=value, field=directory.ParaclinicInputField.objects.all()[0]))

            return value

        @staticmethod
        def address_parser(field: Union['ParaclinicResult', 'DirectionParamsResult']):
            return ParaclinicResult.JsonParser.get_value_json_field(field, 'address')

        @staticmethod
        def code_title_parser(field: Union['ParaclinicResult', 'DirectionParamsResult']):
            return ' – '.join(ParaclinicResult.JsonParser.get_value_json_fields(field, ('code', 'title')))

        @staticmethod
        def doctorprofile_parser(field: Union['ParaclinicResult', 'DirectionParamsResult']):
            return ParaclinicResult.JsonParser.get_value_json_field(field, 'fio')

    @property
    def string_value(self):
        return ParaclinicResult.JsonParser.from_json_to_string_value(self)

    @staticmethod
    def anesthesia_value_get(iss_pk=-1, field_pk=-1):
        if iss_pk > 0:
            paraclinic_result_obj = ParaclinicResult.objects.filter(issledovaniye__pk=iss_pk, field__pk=field_pk).first()
            if paraclinic_result_obj:
                return paraclinic_result_obj.value
        else:
            return ""

    @staticmethod
    def anesthesia_value_save(iss_pk=-1, field_pk=-1, value_anesthesia=None, action='add'):
        if value_anesthesia is None:
            value_anesthesia = {}
        previus_result = ParaclinicResult.anesthesia_value_get(iss_pk, field_pk)
        if previus_result:
            try:
                previus_result = json.loads(previus_result.replace("'", '"'))
            except:
                previus_result = None
        else:
            previus_result = {'patient_params': [], 'potent_drugs': [], 'narcotic_drugs': [], 'times': []}

        if not isinstance(previus_result, dict):
            previus_result = {'patient_params': [], 'potent_drugs': [], 'narcotic_drugs': [], 'times': []}

        temp_times = previus_result['times']
        current_time = value_anesthesia.get('time')
        if current_time not in temp_times and action == 'add':
            temp_times.append(current_time)
        elif action == 'del':
            temp_times.remove(current_time)
        temp_times = sorted(temp_times)
        previus_result['times'] = temp_times

        def made_anesthesia_structure(type):
            for k, v in value_anesthesia.get(type).items():
                if action == 'add':
                    if k not in previus_result[type]:
                        previus_result[type].append(k)
                    if previus_result.get(k):
                        temp_attr = previus_result[k]
                        temp_attr[current_time] = v
                        previus_result[k] = temp_attr
                    else:
                        previus_result[k] = {current_time: v}

                elif action == 'del':
                    if previus_result.get(k):
                        temp_attr = previus_result[k]
                        if current_time in temp_attr:
                            del temp_attr[current_time]
                            previus_result[k] = temp_attr

        made_anesthesia_structure('patient_params')
        made_anesthesia_structure('potent_drugs')
        made_anesthesia_structure('narcotic_drugs')

        paraclinic_result_obj = None
        if iss_pk > 0:
            iss_obj = Issledovaniya.objects.get(pk=iss_pk)
            field_obj = directory.ParaclinicInputField.objects.get(pk=field_pk)
            paraclinic_result_obj = ParaclinicResult.objects.filter(issledovaniye=iss_obj, field=field_obj).first()
            if paraclinic_result_obj:
                paraclinic_result_obj.value = previus_result
                paraclinic_result_obj.field_type = 21
            else:
                paraclinic_result_obj = ParaclinicResult(issledovaniye=iss_obj, field=field_obj, field_type=21, value=previus_result)
            paraclinic_result_obj.save()

        return paraclinic_result_obj


class DirectionParamsResult(models.Model):
    napravleniye = models.ForeignKey(Napravleniya, null=True, help_text='Направление для которого сохранены дополнительные параметры', db_index=True, on_delete=models.CASCADE)
    title = models.CharField(default='', max_length=400, help_text='Название поля ввода')
    field = models.ForeignKey(directory.ParaclinicInputField, db_index=True, help_text='Поле результата', on_delete=models.CASCADE)
    field_type = models.SmallIntegerField(default=None, blank=True, choices=directory.ParaclinicInputField.TYPES, null=True)
    value = models.TextField()
    order = models.SmallIntegerField(default=None, blank=True, null=True)

    def get_field_type(self):
        return self.field_type if self.field_type is not None else self.field.field_type

    @property
    def string_value(self):
        return ParaclinicResult.JsonParser.from_json_to_string_value(self)

    @property
    def string_value_normalized(self):
        result = self.string_value
        parts = result.split('-')
        if self.get_field_type() == 1 and len(parts) == 3:
            result = f'{parts[2]}.{parts[1]}.{parts[0]}'
        return result

    @staticmethod
    def save_direction_params(direction_obj, data):
        if data.get('groups', None):
            groups_data = data.get('groups')
            for i in groups_data:
                if i.get('fields', None):
                    fields = i.get('fields', None)
                    for f in fields:
                        field_obj, field_type = None, None
                        value, title = '', ''
                        order = -1
                        for k, v in f.items():
                            if k == 'pk':
                                field_obj = directory.ParaclinicInputField.objects.get(pk=v)
                            if k == 'order':
                                order = v
                            if k == 'value':
                                value = v
                            if k == 'field_type':
                                field_type = v
                            if k == 'title':
                                title = v
                        if value:
                            direction_params_obj = DirectionParamsResult(napravleniye=direction_obj, title=title, field=field_obj, field_type=field_type, value=value, order=order)
                            direction_params_obj.save()


class ParaclinicResultMultidimensionalTable(models.Model):
    paraclinic_record = models.ForeignKey(ParaclinicResult, db_index=True, help_text='Поле результата', on_delete=models.CASCADE)
    napravleniye = models.ForeignKey(Napravleniya, null=True, help_text='Направление для которого сохранение', db_index=True, on_delete=models.CASCADE)
    issledovaniye = models.ForeignKey(Issledovaniya, db_index=True, help_text='Исследование, для которого сохранен результат', on_delete=models.CASCADE)
    fieldpk_directory = models.IntegerField(default=None, blank=True, null=True, help_text="Сущности")
    directory_model = models.CharField(max_length=255, default=None, blank=True, null=True, help_text="Название-ссылка на справочник(модель)")
    fieldpk_directory_second = models.IntegerField(default=None, blank=True, null=True, help_text="Связанная сущность")
    directory_model_second = models.CharField(max_length=255, default=None, blank=True, null=True, help_text="Название-ссылка на справочник(модель) связанной сущности")
    fieldpk_attribute = models.IntegerField(default=None, blank=True, null=True, help_text="Атрибут")
    directory_model_attribute = models.CharField(max_length=255, default=None, blank=True, null=True, help_text="Название-ссылка на атрибут")
    date_param = models.DateField(default=None, blank=True, null=True, db_index=True, help_text="Если связанная сущность дата")
    value = models.TextField(default=None, blank=True, null=True, help_text="Результат-текст")


class MicrobiologyResultCulture(models.Model):
    issledovaniye = models.ForeignKey(
        Issledovaniya, db_index=True, help_text='Направление на исследование, для которого сохранен результат', on_delete=models.CASCADE, related_name='culture_results'
    )
    culture = models.ForeignKey(directory.Culture, help_text="Культура", on_delete=models.PROTECT)
    koe = models.CharField(max_length=16, help_text='КОЕ')
    comments = models.TextField(default='')

    def __str__(self):
        return f"{self.issledovaniye} — {self.culture}"

    class Meta:
        verbose_name = 'Результат-культура'
        verbose_name_plural = 'Результат-культуры'


class MicrobiologyResultCultureAntibiotic(models.Model):
    SENSITIVITIES = (
        ('S', 'S'),
        ('R', 'R'),
        ('I', 'I'),
    )

    result_culture = models.ForeignKey(MicrobiologyResultCulture, help_text="Результат-культура", on_delete=models.CASCADE, related_name='culture_antibiotic')
    antibiotic = models.ForeignKey(directory.Antibiotic, help_text="Антибиотик", on_delete=models.PROTECT)
    antibiotic_amount = models.CharField(max_length=30, help_text='Дозировка антибиотика', default='', blank=True)
    sensitivity = models.CharField(max_length=1, choices=SENSITIVITIES, help_text="Чувствительность")
    dia = models.CharField(max_length=64, help_text='Диаметр')

    class Meta:
        verbose_name = 'Результат-культура-антибиотик'
        verbose_name_plural = 'Результат-культура-антибиотики'


class MicrobiologyResultPhenotype(models.Model):
    result_culture = models.ForeignKey(MicrobiologyResultCulture, help_text="Результат-культура", on_delete=models.CASCADE, related_name='culture_phenotip')
    phenotype = models.ForeignKey(directory.Phenotype, help_text="Фенотип", on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'Результат-культура-фенотип'
        verbose_name_plural = 'Результат-культура-фенотипы'


class RmisServices(models.Model):
    napravleniye = models.ForeignKey(Napravleniya, help_text='Направление', db_index=True, on_delete=models.CASCADE)
    code = models.TextField(help_text='Код выгруженной услуги', db_index=True)
    rmis_id = models.CharField(max_length=15, default="", blank=True, help_text='ID выгруженной услуги в РМИС')

    def __str__(self):
        return "%s %s" % (self.napravleniye, self.code)

    class Meta:
        verbose_name = 'Выгруженная в РМИС услуга для направления'
        verbose_name_plural = 'Выгруженные в РМИС услуги для направлений'


class Result(models.Model):
    """
    Результат исследований
    """

    issledovaniye = models.ForeignKey(Issledovaniya, db_index=True, help_text='Направление на исследование, для которого сохранен результат', on_delete=models.CASCADE)
    fraction = models.ForeignKey(directory.Fractions, help_text='Фракция из исследования', db_index=True, on_delete=models.CASCADE)
    value = models.TextField(null=True, blank=True, help_text='Значение')
    comment = models.TextField(null=True, blank=True, help_text='Комментарий к значению')
    iteration = models.IntegerField(default=1, null=True, help_text='Итерация')
    is_normal = models.CharField(max_length=255, default="", null=True, blank=True, help_text="Это норма?")
    selected_reference = models.IntegerField(default=-2, blank=True, help_text="Выбранный референс")
    ref_sign = models.CharField(max_length=3, default="", null=True, blank=True, help_text="Направление отклонения от нормы")
    ref_m = JSONField(default=None, blank=True, null=True, help_text="Референсы М")
    ref_f = JSONField(default=None, blank=True, null=True, help_text="Референсы Ж")
    units = models.CharField(max_length=255, default=None, blank=True, null=True, help_text="Единицы измерения")
    ref_title = models.CharField(max_length=255, default=None, blank=True, null=True, help_text="Референсы Название")
    ref_about = models.TextField(default=None, blank=True, null=True, help_text="Референсы Описание")

    def __str__(self):
        return "%s | %s | %s" % (self.pk, self.fraction, self.ref_m is not None and self.ref_f is not None)

    def get_units(self, needsave=True):
        if not self.units:
            u = self.fraction.get_unit_str()
            if u:
                self.units = u
                if needsave:
                    self.save()
        return self.units or ""

    def get_ref(self, as_str=False, full=False, fromsave=False, re_save=False, needsave=True):
        if (not self.ref_title and not fromsave) or re_save:
            self.ref_title = "Default" if self.fraction.default_ref is None else self.fraction.default_ref.title
            self.save()
            if not self.ref_m or re_save:
                self.ref_m = self.fraction.ref_m if self.fraction.default_ref is None else self.fraction.default_ref.ref_m
                if needsave:
                    self.save()

            if not self.ref_f or re_save:
                self.ref_f = self.fraction.ref_f if self.fraction.default_ref is None else self.fraction.default_ref.ref_f
                if needsave:
                    self.save()

            if not self.ref_about or re_save:
                self.ref_about = "" if self.fraction.default_ref is None else self.fraction.default_ref.about
                if needsave:
                    self.save()

        if full:
            return {"title": self.ref_title, "about": self.ref_about, "m": self.ref_m, "f": self.ref_f}

        ref = self.ref_f if self.issledovaniye.napravleniye.client.individual.sex.lower() != "м" else self.ref_m

        if isinstance(ref, str):
            ref = json.loads(ref)
        if not ref:
            ref = {}

        if not as_str:
            return ref
        else:
            return json.dumps(ref)

    def save(self, *args, **kw):
        norm, ref_sign = self.calc_normal(True)
        self.is_normal = norm
        self.ref_sign = ref_sign
        super(Result, self).save(*args, **kw)

    def get_is_norm(self, recalc=False, with_ref=False):
        if self.is_normal == "" or recalc:
            norm, ref_sign = self.calc_normal()
            if self.is_normal != norm or self.ref_sign != ref_sign:
                self.is_normal = norm
                self.ref_sign = ref_sign
                self.save(update_fields=['is_normal', 'ref_sign'])
        else:
            norm = self.is_normal
            ref_sign = self.ref_sign
        if with_ref:
            return norm, ref_sign, self.calc_normal(only_ref=True, fromsave=True, raw_ref=True, single=True)
        return norm, ref_sign

    def calc_normal(self, fromsave=False, only_ref=False, raw_ref=True, single=False):
        value = self.value
        ref = self.get_ref(fromsave=fromsave)
        age = self.issledovaniye.napravleniye.client.individual.age(iss=self.issledovaniye, days_monthes_years=True)

        ref_processor = RefProcessor(ref, age)

        if only_ref:
            return ref_processor.get_active_ref(raw_ref=raw_ref, single=single)

        return ref_processor.calc(value)

    def get_is_norm_old(self, recalc=False):
        if self.is_normal == "" or recalc:
            norm = self.calc_normal_old()
            if self.is_normal != norm:
                self.save()
        else:
            norm = self.is_normal
        return norm

    def calc_normal_old(self, fromsave=False, only_ref=False, raw_ref=True):
        import operator
        from functools import reduce

        trues = {True: ["полож.", "положительно", "да", "положительный", "обнаружено"], False: ["отриц.", "отрицательно", "нет", "1/0", "отрицательный", "не обнаружено"]}
        signs = {">": [">", "&gt;", "более", "старше"], "<": ["<", "&lt;", "до", "младше", "менее"]}

        value = self.value
        days, monthes, years = self.issledovaniye.napravleniye.client.individual.age(iss=self.issledovaniye, days_monthes_years=True)

        ref = self.get_ref(fromsave=fromsave)

        def isnum(r):
            return r.replace(".", "", 1).replace(",", "", 1).isdigit()

        def replace_pow(v):
            v = str(v).replace(" ", "")
            for j in range(1, 9):
                for i in range(0, 12):
                    v = v.replace("%s*10<sup>%s</sup>" % (j, i), str(j * (10**i)))
            for i in range(0, 12):
                v = v.replace("10<sup>%s</sup>" % str(i), str(10**i))
            return v

        def val_normalize(v):
            if v == float("inf"):
                return v
            v = replace_pow(v)
            '''
            if any([x in v for x in signs["<"]]):
                pass
            elif any([x in v for x in signs[">"]]):
                pass'''

            import re

            tmp = re.findall("\d+,\d+", v)
            for t in tmp:
                v = v.replace(t, t.replace(",", "."))
            tmp = re.findall("\d+\.\d+", v)
            if len(tmp) == 0:
                tmp = re.findall('\d+', v)
                if len(tmp) == 0:
                    return False
            return tmp[-1]

        def rigths(r):
            if r == "все" or r == "":
                return 0, 200

            if "старше" in r.lower():
                r = r.replace("старше", "").strip()
                if r.isdigit():
                    return int(r), 200

            if "после" in r.lower():
                r = r.replace("после", "").strip()
                if r.isdigit():
                    return int(r), 200

            if "младше" in r.lower():
                r = r.replace("младше", "").strip()
                if r.isdigit():
                    return 0, int(r)

            if "до" in r.lower():
                r = r.replace("до", "").strip()
                if r.isdigit():
                    return 0, int(r)

            spl = r.split("-")
            if len(spl) == 2 and spl[0].isdigit() and spl[1].isdigit():
                return int(spl[0]), int(spl[1])
            return False

        def rigths_v(r):
            r = replace_pow(r.replace(" ", ""))
            if r == "":
                return -float("inf"), float("inf")
            if "един" in r.lower():
                r = "0-2"
            if "отсутств" in r.lower():
                r = "0-0"
            trues_vars = [x for x in trues.values()]
            trues_vars = reduce(operator.add, trues_vars)
            if any([x in r for x in trues_vars]):
                return r in trues[True]
            spl = r.split("-")
            if len(spl) == 2:
                x = spl[0]
                y = spl[1]
                if isnum(x) and isnum(y):
                    x = val_normalize(x)
                    y = val_normalize(y)
                    return float(x) - 0.00001, float(y) + 0.00001
            signs_vars = [x for x in signs.values()]
            signs_vars = reduce(operator.add, signs_vars)
            if any([x in r for x in signs_vars]):
                val_r = val_normalize(r)
                if not val_r:
                    val_r = "0.0"
                if any([x in r for x in signs["<"]]):
                    return -float("inf"), float(val_r) - 0.00001
                elif any([x in r for x in signs[">"]]):
                    return float(val_r) + 0.00001, float("inf")
            return r.lower().strip()

        def test_value(right, value):
            import re

            if isinstance(right, bool):
                return value.lower() in trues[right]
            if right == "":
                return True
            value = value.replace("''", "\"")
            if isinstance(right, tuple) and len(right) == 2:
                if isinstance(right[0], float) and isinstance(right[1], float):
                    if "един" in value.lower():
                        value = "1"
                    if "отсутств" in value.lower():
                        value = "0"
                    if "сплошь" in value.lower() or "++" in value or "+ +" in value or "++++" in value or "+" == value.strip() or "оксал ед" in value:
                        value = float("inf")
                    elif any([x in replace_pow(value) for x in signs["<"]]):
                        value = val_normalize(value)
                        if value and not isinstance(value, bool):
                            value = str(float(value) - 0.1)
                    elif any([x in replace_pow(value) for x in signs[">"]]):
                        value = val_normalize(value)
                        if value and not isinstance(value, bool):
                            value = str(float(value) + 0.1)
                    if isinstance(value, str) and re.match(r"(\d)\'(\d{1,2})\"", value.replace(" ", "")):
                        m = re.search(r"(\d)\'(\d{1,2})\"", value.replace(" ", ""))
                        min = int(m.group(1))
                        sec = int(m.group(2))
                        value = "{0:.2f}".format(min + sec / 60)
                    else:
                        value = val_normalize(value)
                    if not isinstance(right, bool):
                        return right[0] <= float(value) <= right[1]
            if isinstance(right, str):
                value = value.replace(".", "").lower().strip()
                return value in right
            return False

        def has_days(s: str):
            return any([x in s for x in ["дней", "день", "дн.", "дня"]])

        def has_monthes(s: str):
            return any([x in s for x in ["месяцев", "месяц", "мес.", "м.", "месяца"]])

        def not_days_and_m(s: str):
            return not has_days(s) and not has_monthes(s)

        def has_years(s: str):
            return any([x in s for x in ["лет", "год", "л.", "года"]] + [not has_days(s) and not has_monthes(s)])

        def clc(r, val, age, only_ref):
            result = "normal"
            active_ref = {}
            if val.strip() != "":
                for k in r.keys():
                    tmp_result = "normal"
                    kk = re.sub("[^0-9\-]", "", k)
                    rigth = rigths(k.strip().lower())
                    rigthkk = rigths(kk)

                    if years == 0 and rigthkk and not has_years(k):
                        print(days, monthes, years, k)  # noqa: T001
                        if monthes == 0:
                            if has_days(k):
                                rigth = rigthkk
                                age = days
                            else:
                                rigth = [-1, -1]
                        else:
                            if has_monthes(k):
                                rigth = rigthkk
                                age = monthes
                            else:
                                rigth = [-1, -1]
                    elif not not_days_and_m(k):
                        rigth = [-1, -1]

                    if not rigth:
                        tmp_result = "maybe"
                    elif rigth[0] <= age <= rigth[1]:
                        if not only_ref:
                            rigth_v = rigths_v(r[k].strip().lower())
                            pattern = re.compile(r"^([a-zA-Zа-яА-Я]|\s|:|,|\^|@|\\|\||/|\+|-|\(|\)|\[|\]|{|}|#|№|!|~|\.)+$")
                            if pattern.match(r[k]):
                                if self.compare(r[k], val):
                                    tmp_result = "normal"
                                else:
                                    tmp_result = "not_normal"
                            elif rigth_v == "":
                                tmp_result = "maybe"
                            else:
                                test_v = test_value(rigth_v, val)
                                if not test_v:
                                    tmp_result = "not_normal"
                        else:
                            if raw_ref:
                                active_ref = {"k": k, "r": r[k]}
                            else:
                                active_ref = rigths_v(r[k].strip().lower())
                    if result not in ["maybe", "not_normal"] or tmp_result == "maybe":
                        result = tmp_result
            if only_ref:
                return active_ref
            return result

        calc = clc(ref, value, years, only_ref)
        return calc

    class Meta:
        verbose_name = 'Результат исследования'
        verbose_name_plural = 'Результаты исследований'

    @staticmethod
    def NFD(text):
        return unicodedata.normalize('NFD', text)

    def canonical_caseless(self, text):
        return self.NFD(self.NFD(text).casefold())

    def compare(self, a: str, b: str):
        a = a.strip()
        b = b.strip()

        return self.canonical_caseless(a) == self.canonical_caseless(b)


class DirectionToUserWatch(models.Model):
    direction = models.ForeignKey(Napravleniya, on_delete=models.CASCADE)
    doc = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE)


class DirectionsHistory(models.Model):
    direction = models.ForeignKey(Napravleniya, on_delete=models.CASCADE)
    old_card = models.ForeignKey(Clients.Card, related_name='old_card', help_text="Старая карта", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    new_card = models.ForeignKey(Clients.Card, related_name='new_card', help_text="Новая карта", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    old_fio_born = models.CharField(max_length=200, blank=True, help_text="ФИО д.р старой карты")
    new_fio_born = models.CharField(max_length=200, blank=True, help_text="ФИО д.р новой карты")
    date_change = models.DateTimeField(default=timezone.now, help_text='Время изменения владельца направления')
    who_change = models.ForeignKey(DoctorProfile, db_index=True, null=True, help_text='Кто изменил принадлежность направлений', on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'История принадлежности направления'
        verbose_name_plural = 'Принадлежности направления'

    @staticmethod
    def move_directions(old_card_number, new_card_number, user):
        old_card = Clients.Card.objects.filter(number=old_card_number, base__internal_type=True)[0]
        old_fio_born = old_card.get_fio_w_card()
        new_card = Clients.Card.objects.filter(number=new_card_number, base__internal_type=True)[0]
        new_fio_born = new_card.get_fio_w_card()
        with transaction.atomic():
            directions = Napravleniya.objects.select_for_update().filter(client=old_card)
            for dir in directions:
                dir.client = new_card
                dir.save()
                dir_history = DirectionsHistory(direction=dir, old_card=old_card, new_card=new_card, old_fio_born=old_fio_born, new_fio_born=new_fio_born, who_change=user)
                dir_history.save()

        return directions


class GeneratorValuesAreOver(Exception):
    pass


class GeneratorOverlap(Exception):
    pass


class NumberGenerator(models.Model):
    DEATH_FORM_NUMBER = 'deathFormNumber'
    PERINATAL_DEATH_FORM_NUMBER = 'deathPerinatalNumber'
    TUBE_NUMBER = 'tubeNumber'
    EXTERNAL_ORDER_NUMBER = 'externalOrderNumber'

    KEYS = (
        (DEATH_FORM_NUMBER, 'Номер свидетельства о смерти'),
        (PERINATAL_DEATH_FORM_NUMBER, 'Номер свидетельства о перинатальной смерти'),
        (TUBE_NUMBER, 'Номер ёмкости биоматериала'),
        (EXTERNAL_ORDER_NUMBER, 'Номер внешнего заказ для отправки'),
    )

    hospital = models.ForeignKey(Hospitals, on_delete=models.CASCADE, db_index=True, verbose_name='Больница')
    key = models.CharField(choices=KEYS, max_length=128, db_index=True, verbose_name='Тип диапазона')
    year = models.IntegerField(verbose_name='Год', db_index=True)
    is_active = models.BooleanField(verbose_name='Активность диапазона', db_index=True)
    start = models.PositiveBigIntegerField(verbose_name='Начало диапазона')
    end = models.PositiveBigIntegerField(verbose_name='Конец диапазона', null=True, blank=True, default=None)
    last = models.PositiveBigIntegerField(verbose_name='Последнее значение диапазона', null=True, blank=True)
    free_numbers = ArrayField(models.PositiveBigIntegerField(verbose_name='Свободные номера'), default=list, blank=True)
    prepend_length = models.PositiveSmallIntegerField(verbose_name='Длина номера', help_text='Если номер короче, впереди будет добавлено недостающее кол-во "0"')

    def __str__(self):
        return f"{self.hospital} {self.key} {self.year} {self.is_active} {self.start} — {self.end} ({self.last})"

    def get_min_last_value(self):
        has_overlap = False
        min_last_value = self.last if self.last else (self.start - 1)
        has_free_number = False
        if self.free_numbers:
            min_last_orig = min_last_value
            min_last_value = min(min_last_value, *self.free_numbers)
            has_free_number = min_last_orig != min_last_value
        if self.key == NumberGenerator.TUBE_NUMBER and self.end is None and not has_free_number:
            includes_generators = (
                NumberGenerator.objects.exclude(pk=self.pk)
                .exclude(end__isnull=True)
                .filter(key=NumberGenerator.TUBE_NUMBER, start__lte=min_last_value + 1, end__gte=min_last_value + 1)
                .order_by('end')
            )
            for gen in includes_generators:
                min_last_orig = min_last_value
                min_last_value = max(min_last_value + 1, gen.end + 1)
                if min_last_orig + 1 != min_last_value:
                    has_overlap = True
        return min_last_value, has_overlap

    def get_next_value(self):
        min_last_value, has_overlap = self.get_min_last_value()
        if not self.last or self.last == min_last_value:
            next_value = min_last_value + 1
            if (self.end is not None or (not self.hospital.is_default)) and next_value > self.end:
                raise GeneratorValuesAreOver('Значения генератора закончились')
            self.last = next_value
        else:
            next_value = min_last_value
            if has_overlap:
                self.last = next_value
        self.free_numbers = [x for x in self.free_numbers if x != next_value]
        self.save(update_fields=['last', 'free_numbers'])

        if self.key == NumberGenerator.TUBE_NUMBER and TubesRegistration.objects.filter(number=next_value).exists():
            return self.get_next_value()

        return next_value

    def get_prepended_next_value(self):
        next_value = self.get_next_value()
        next_value = str(next_value).zfill(self.prepend_length)
        return next_value

    @staticmethod
    def check_value_for_organization(organization: Hospitals, value: int):
        generator = NumberGenerator.objects.filter(
            key=NumberGenerator.TUBE_NUMBER,
            hospital=organization,
            is_active=True,
            start__lte=value,
            end__gte=value,
        ).first()

        if not generator:
            return not organization.strict_tube_numbers

        return generator.start <= value <= generator.end and not TubesRegistration.objects.filter(number=value).exists()

    class Meta:
        verbose_name = 'Диапазон номеров'
        verbose_name_plural = 'Диапазоны номеров'
